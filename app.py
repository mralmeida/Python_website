from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    SubmitField,
    SelectField
)
from wtforms.validators import DataRequired, Email
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    flash
)
app = Flask(__name__)
app.config["SECRET_KEY"] = "something-secure"

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
@app.route("/")
def home():
    return redirect("/contacts")

class ContactForm(FlaskForm):
    name = StringField("Name",validators=[DataRequired()])
    email = StringField("Email",validators=[DataRequired(), Email()])
    company = SelectField("Company", coerce=int)
    role = SelectField("Role", coerce=int)
    department = SelectField("Department", coerce=int)
    comment = TextAreaField("Comment")
    submit = SubmitField("Save")
# ----- these are "helper functions"
def get_roles():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name
        FROM role
        ORDER BY name
    """)

    rows = cursor.fetchall()
    conn.close()

    return [(row[0], row[1]) for row in rows]


def get_companies():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name
        FROM company
        ORDER BY name
    """)

    rows = cursor.fetchall()
    conn.close()

    return [(row[0], row[1]) for row in rows]

def get_departments():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name
        FROM department 
        ORDER BY name
    """)

    rows = cursor.fetchall()
    conn.close()

    return [(row[0], row[1]) for row in rows]
#----- end of "helper functions"

@app.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()

    #--- loads all combo boxes
    form.company.choices = get_companies()
    form.role.choices = get_roles()
    form.department.choices = get_departments()
    # ----- combo boxes all loaded

    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        company_id = form.company.data
        role_id = form.role.data
        department_id = form.department.data
        comment = form.comment.data

        # Insert into SQLite
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contact (name, email, roleID, companyID, departmentID, obs)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, email, role_id, company_id, department_id , comment))
        conn.commit()
        conn.close()

        return render_template(
            "contact_result.html",
            name=name,
            email=email,
            role=role_id,
            company=company_id,
            department=department_id,
            comment=comment
        )

    return render_template("contact_form.html", form=form)

# def get_messages():
#     conn = sqlite3.connect("database.db")
#     cursor = conn.cursor()
#     cursor.execute("SELECT id, name, email, message FROM messages")
#     rows = cursor.fetchall()
#     conn.close()
#     return rows
#
#
# @app.route("/messages")
# def messages():
#     data = get_messages()
#     count = len(data)
#     return render_template("messages.html", messages=data, count=count)
# --------------------------------------------------------
def get_contacts():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    sql = """
    SELECT CTS.id, CTS.name, CTS.email, CTS.companyID, COMP.name, CTS.roleID, ROLE.name, CTS.departmentID, DEPT.name, CTS.obs 
    FROM contact CTS 
    INNER JOIN company COMP ON CTS.companyID = COMP.id 
    INNER JOIN role ROLE ON ROLE.id = CTS.roleID 
    INNER JOIN department DEPT ON DEPT.id = CTS.departmentID 
    ORDER BY CTS.name
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()
    return rows


@app.route("/contacts")
def contacts():
    data = get_contacts()
    count = len(data)
    return render_template("contacts.html", contacts=data, count=count)

# --------------------------------------------------------
# --to delete all selected records
# ---- For now, let us disable this feature. We do not want to delete our records. I will figure out how to do that safely later.
# @app.route("/delete-messages", methods=["POST"])
# def delete_messages():
#     ids = request.form.getlist("delete_ids")
#
#     if ids:
#         conn = sqlite3.connect("database.db")
#         cursor = conn.cursor()
#
#         for message_id in ids:
#             cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
#
#         conn.commit()
#         conn.close()
#
#     return redirect("/messages")

# ---------------------------------------------------------
#---to insert data onto messages table
import csv
import sqlite3
from flask import render_template, request

REQUIRED_COLUMNS = {"name", "email", "message"}


def read_csv_file(file):
    """
    Reads the uploaded CSV and returns a list of rows.
    """

    try:
        text = file.stream.read().decode("utf-8")
    except UnicodeDecodeError:
        return None, ["The file is not a valid UTF-8 CSV file."]

    reader = csv.DictReader(text.splitlines())

    if not reader.fieldnames:
        return None, ["The file does not contain a valid CSV header row."]

    rows = list(reader)

    return rows, []


def validate_csv_columns(fieldnames):
    """
    Validates that required columns exist.
    """

    errors = []

    missing_columns = REQUIRED_COLUMNS - set(fieldnames)

    if missing_columns:
        errors.append(
            f"Missing required columns: {', '.join(sorted(missing_columns))}"
        )

    return errors


def validate_email_address(email):
    """
    Basic email validation.
    """

    if not email:
        return False

    return "@" in email and "." in email


def validate_csv_rows(rows):
    """
    Validates row data.
    """

    errors = []

    for row_number, row in enumerate(rows, start=2):

        if not row.get("name", "").strip():
            errors.append(
                f"Row {row_number}: Name cannot be empty."
            )

        if not row.get("email", "").strip():
            errors.append(
                f"Row {row_number}: Email cannot be empty."
            )

        elif not validate_email_address(row["email"].strip()):
            errors.append(
                f"Row {row_number}: Invalid email address."
            )

        if not row.get("comment", "").strip():
            errors.append(
                f"Row {row_number}: Comment cannot be empty."
            )

    return errors


def validate_csv_file(file):
    """
    Runs all file validations.
    """

    rows, errors = read_csv_file(file)

    if errors:
        return None, errors

    if not rows:
        return None, ["The file contains no data rows."]

    column_errors = validate_csv_columns(rows[0].keys())

    if column_errors:
        return None, column_errors

    row_errors = validate_csv_rows(rows)

    if row_errors:
        return None, row_errors

    return rows, []


def insert_rows(rows):
    """
    Inserts rows in a single transaction.
    """

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    try:

        for row in rows:

            cursor.execute("""
                INSERT INTO messages (name, email, message)
                VALUES (?, ?, ?)
            """, (
                row["name"].strip(),
                row["email"].strip(),
                row["message"].strip()
            ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

@app.route("/import-csv", methods=["GET", "POST"])
def import_csv():

    if request.method == "POST":

        file = request.files.get("csvfile")

        if not file or file.filename == "":
            flash("Please select a CSV file before uploading.")
            return redirect(request.url)

        rows, errors = validate_csv_file(file)

        if errors:

            for error in errors:
                flash(error)

            return redirect(request.url)

        try:

            insert_rows(rows)

        except Exception as ex:

            flash(
                f"Database error. No records were imported. "
                f"Details: {str(ex)}"
            )

            return redirect(request.url)

        return render_template(
            "import_success.html",
            records_imported=len(rows)
        )

    return render_template("import_csv.html")


# ---------------------------------------------------------------------
# --- To edit the selected record
@app.route("/edit/<int:contact_id>", methods=["GET", "POST"])
def edit_message(contact_id):

    form = ContactForm()
    #----- populate all combo boxes and get them ready to be selected with the record info
    form.company.choices = get_companies()
    form.role.choices = get_roles()
    form.department.choices = get_departments()

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "GET":

        sql = """
            SELECT      CTS.id, CTS.name, CTS.email, CTS.companyID, COMP.name,  
                        CTS.roleID, ROLE.name, CTS.departmentID, DEPT.name, CTS.obs
            FROM        contact CTS
                INNER JOIN company COMP ON CTS.companyID = COMP.id
                INNER JOIN role ROLE ON ROLE.id = CTS.roleID
                INNER JOIN department DEPT ON DEPT.id = CTS.departmentID
            WHERE       CTS.id = ?
            ORDER BY    CTS.name
        """
        cursor.execute(sql, (contact_id,))
        record = cursor.fetchone()

        if record:
            form.name.data = record[1]
            form.email.data = record[2]
            form.company.data = record[3]
            form.role.data = record[5]
            form.department.data = record[7]
            form.comment.data = record[9]

    if form.validate_on_submit():

        cursor.execute("""
            UPDATE contact
            SET name = ?, email = ?, companyid = ?, roleid = ?, departmentid = ?, obs = ?
            WHERE id = ?
        """, (
            form.name.data,
            form.email.data,
            form.company.data,
            form.role.data,
            form.department.data,
            form.comment.data,
            contact_id
        ))

        conn.commit()
        conn.close()
        form.submit.label.text = "Save Changes"
        return redirect("/contacts")

    conn.close()

    return render_template(
        "contact_form.html",
        form=form,
        edit_mode=True
    )

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
