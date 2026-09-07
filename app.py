from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
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
        return render_template(
            "contact_result.html",
            name=form.name.data,
            email=form.email.data,
            message=form.message.data
        )
    return render_template("contact_form.html", form=form)

# ---------------------------------------------------------
# ✅ INSERT THIS PART HERE — your new messages table route
# ---------------------------------------------------------

def get_messages():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, message FROM messages")
    rows = cursor.fetchall()
    conn.close()
    return rows

@app.route("/messages")
def messages():
    data = get_messages()
    return render_template("messages.html", messages=data)

# ---------------------------------------------------------
#---to insert data onto messages table
import csv
import sqlite3
from flask import Flask, render_template, request

@app.route("/import-csv", methods=["GET", "POST"])
def import_csv():

    if request.method == "POST":

        file = request.files["csvfile"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        csv_reader = csv.DictReader(
            file.stream.read().decode("utf-8").splitlines()
        )

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

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
