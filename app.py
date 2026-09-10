from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask import Flask, render_template, request, redirect
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
    return "Hello Mr. Xups — your Python website is running, now with SQLite database!"

class ContactForm(FlaskForm):
    name = StringField("Your name", validators=[DataRequired()])
    email = StringField("Email address", validators=[DataRequired()])
    message = StringField("Message", validators=[DataRequired()])
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

@app.route("/import-csv", methods=["GET", "POST"])
def import_csv():
    #import pdb; pdb.set_trace()  # debugger stops here

    if request.method == "POST":

        file = request.files["csvfile"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        csv_reader = csv.DictReader(file.stream.read().decode("utf-8").splitlines())

        for row in csv_reader:
            cursor.execute("""
                INSERT INTO messages (name, email, message)
                VALUES (?, ?, ?)
            """, (
                row["name"],
                row["email"],
                row["message"]
            ))

        conn.commit()
        conn.close()

        return "CSV imported successfully!"

    return render_template("import_csv.html")
#-----
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
