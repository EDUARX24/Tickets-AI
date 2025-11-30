# app/main/routes.py
from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    # antes era tu @app.route("/") en application.py
    return render_template("main/index.html",active_page="dashboard")
