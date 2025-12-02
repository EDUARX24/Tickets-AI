# app/admin/routes.py
from flask import Blueprint, render_template, session, redirect, url_for
from app import supabase

admin_bp = Blueprint("admin", __name__)

#endóint for sysAdmin dashboard
@admin_bp.route("/admin")
def home_admin():
    if session.get("role") != "sysAdmin":
        return redirect(url_for("main.index"))

    # Total de usuarios
    resp_users = (
        supabase
        .table("users")
        .select("username_id", count="exact")
        .execute()
    )
    total_users = resp_users.count or 0

    # Total de colaboradores (rol admin_tech)
    resp_collab = (
        supabase
        .table("users")
        .select("username_id", count="exact")
        .eq("role", "admin_tech")
        .execute()
    )
    total_collaborators = resp_collab.count or 0

    # Total de compañías (opcional)
    resp_companies = (
        supabase
        .table("company")
        .select("company_id", count="exact")
        .execute()
    )
    total_companies = resp_companies.count or 0

    return render_template(
        "admin/homeAdmin.html",
        total_users=total_users,
        total_collaborators=total_collaborators,
        total_companies=total_companies, active_page="admin_home"
    )


# Tech dashboard
@admin_bp.route("/admin/tech-dashboard")
def tech_dashboard():
    # opcional: proteger ruta solo para tech admins
    if session.get("role") != "admin_tech":
        return redirect(url_for("main.index"))

    return render_template("admin/techDashboard.html", active_page="tech_dashboard")

#endpoint para crear categorias