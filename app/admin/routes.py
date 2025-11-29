# app/admin/routes.py
from flask import Blueprint, render_template, session, redirect, url_for

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin")
def home_admin():
    # opcional: proteger ruta solo para admins
    if session.get("role") != "admin_cliente":
        return redirect(url_for("main.index"))

    return render_template("admin/homeAdmin.html")
