from flask import Flask
from wtforms.validators import DataRequired

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello Mr. Xups — your Python website is running!"

app.run(debug=True)

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
        return render_template("contact_result.html",
                               name=name,
                               email=email,
                               message=message)
    return render_template("contact_form.html", form=form)
