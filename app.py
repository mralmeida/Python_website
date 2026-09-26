from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email
from flask import Flask, render_template, request, redirect, flash

import sqlite3

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
    return redirect("/messages")

class ContactForm(FlaskForm):
    name = StringField(
        "Your name",
        validators=[DataRequired(message="Name is required.")]
    )

    email = StringField(
        "Email address",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Please enter a valid email address.")
        ]
    )

    message = TextAreaField(
        "Message",
        validators=[DataRequired(message="Message is required.")]
    )

    submit = SubmitField("Send")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()

    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        message = form.message.data

        # Insert into SQLite
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (name, email, message)
            VALUES (?, ?, ?)
        """, (name, email, message))
        conn.commit()
        conn.close()

        return render_template(
            "contact_result.html",
            name=name,
            email=email,
            message=message
        )

    return render_template("contact_form.html", form=form)

def get_messages():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, message FROM messages")
    rows = cursor.fetchall()
    conn.close()
    return rows


@app.route("/messages")
def messages():
    data = get_messages()
    count = len(data)
    return render_template("messages.html", messages=data, count=count)

# --------------------------------------------------------
# --to delete all selected records
@app.route("/delete-messages", methods=["POST"])
def delete_messages():
    ids = request.form.getlist("delete_ids")

    if ids:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        for message_id in ids:
            cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))

        conn.commit()
        conn.close()

    return redirect("/messages")

# ---------------------------------------------------------
#---to insert data onto messages table
import csv
import sqlite3
from flask import Flask, render_template, request
from wtforms.validators import Email
REQUIRED_COLUMNS = {"name", "email", "message"}
from wtforms.validators import Email

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

        if not row.get("message", "").strip():
            errors.append(
                f"Row {row_number}: Message cannot be empty."
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

# @app.route("/import-csv", methods=["GET", "POST"])
#
# def import_csv():
#     if request.method == "POST":
#         file = request.files["csvfile"]
#
#         if not file or file.filename == '':
#             flash('Please select a CSV file before uploading.')
#             return redirect(request.url)
#
#         conn = sqlite3.connect("database.db")
#         cursor = conn.cursor()
#
#         csv_reader = csv.DictReader(
#             file.stream.read().decode("utf-8").splitlines()
#         )
#
#         for row in csv_reader:
#             cursor.execute("""
#                 INSERT INTO messages (name, email, message)
#                 VALUES (?, ?, ?)
#             """, (
#                 row["name"],
#                 row["email"],
#                 row["message"]
#             ))
#
#         conn.commit()
#         conn.close()
#
#         return render_template("import_success.html")
#     # Handles GET requests
#     return render_template("import_csv.html")
#-----
from flask import send_from_directory

# ---------------------------------------------------------------------
# --- To edit the selected record
@app.route("/edit/<int:message_id>", methods=["GET", "POST"])
def edit_message(message_id):

    form = ContactForm()

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "GET":

        cursor.execute("""
            SELECT name, email, message
            FROM messages
            WHERE id = ?
        """, (message_id,))

        record = cursor.fetchone()

        if record:
            form.name.data = record[0]
            form.email.data = record[1]
            form.message.data = record[2]

    if form.validate_on_submit():

        cursor.execute("""
            UPDATE messages
            SET name = ?, email = ?, message = ?
            WHERE id = ?
        """, (
            form.name.data,
            form.email.data,
            form.message.data,
            message_id
        ))

        conn.commit()
        conn.close()
        form.submit.label.text = "Save Changes"
        return redirect("/messages")

    conn.close()

    return render_template(
        "contact_form.html",
        form=form,
        edit_mode=True
    )

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
