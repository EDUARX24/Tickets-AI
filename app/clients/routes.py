# app/admin/routes.py
from flask import Blueprint, render_template, session, redirect, url_for

#blueprint para los clientes administradores
client_admin_bp = Blueprint("client_admin", __name__)
@client_admin_bp.route("/client-admin")
def home_client_admin():
    # opcional: proteger ruta solo para clientes administradores
    if session.get("role") != "admin_cliente":
        return redirect(url_for("main.index"))

    return render_template("client_admin/homeClientAdmin.html")