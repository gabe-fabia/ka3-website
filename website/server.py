from flask import Flask, render_template, Blueprint
from flask_login import login_required, current_user

ALLOWED_EXTENSIONS = {"csv"}

app = Blueprint("app", __name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", name=current_user.name)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/home")
def home():
    return render_template("index.html")


@app.route("/documentation")
def documentation():
    return render_template("documentation.html")
