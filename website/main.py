from flask import Flask, render_template, Blueprint
from flask_login import login_required, current_user

ALLOWED_EXTENSIONS = {"csv"}

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/profile")
@login_required
def profile():
    return render_template("profile.html", name=current_user.name)


@main.route("/about")
def about():
    return render_template("about.html")


@main.route("/home")
def home():
    return render_template("index.html")


@main.route("/documentation")
def documentation():
    return render_template("documentation.html")
