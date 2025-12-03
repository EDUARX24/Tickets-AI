# app/admin/routes.py
from flask import Blueprint, render_template, session, redirect, url_for
from app import supabase

admin_bp = Blueprint("admin", __name__)

def require_sysadmin():
    """
    Pequeño helper para proteger rutas del SysAdmin.
    Si no es sysAdmin, lo redirige al inicio.
    """
    if session.get("role") != "sysAdmin":
        return redirect(url_for("main.index"))
    return None

# ============================
# Dashboard SysAdmin
# ============================
@admin_bp.route("/admin")
def home_admin():
    guard = require_sysadmin()
    if guard:
        return guard

    # Total de tickets (ajusta el nombre de la tabla si es distinto)
    # Total de tickets  (tabla: ticket)
    resp_tickets = (
    supabase
    .table("ticket")              # 👈 nombre correcto de la tabla
    .select("*", count="exact")   # * para no depender del nombre de la columna
    .execute()
    )
    total_tickets = resp_tickets.count or 0

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

    # Total de compañías
    resp_companies = (
        supabase
        .table("company")
        .select("company_id", count="exact")
        .execute()
    )
    total_companies = resp_companies.count or 0

    return render_template(
        "admin/homeAdmin.html",
        total_tickets=total_tickets,
        total_users=total_users,
        total_collaborators=total_collaborators,
        total_companies=total_companies,
        active_page="admin_home",   # este lo usas en el sidebar
    )

@admin_bp.route("/admin/tickets")
def admin_tickets():
    guard = require_sysadmin()
    if guard:
        return guard

    # Traer todos los tickets (ajusta nombres de columnas según tu tabla)
    resp = (
        supabase
        .table("ticket")   # 👈 aquí también en singular
        .select("*")
        .execute()
    )
    tickets = resp.data or []

    return render_template(
        "admin/ticketsList.html",
        tickets=tickets,
        active_page="admin_tickets",
    )

@admin_bp.route("/admin/users")
def admin_users():
    guard = require_sysadmin()
    if guard:
        return guard

    try:
        resp = (
            supabase
            .table("users")
            .select("username_id, username, email, role, created_at")
            .order("created_at", desc=True)
            .execute()
        )
        users = resp.data or []
    except Exception as e:
        print("Error obteniendo usuarios:", e)
        users = []

    total_users = len(users)

    return render_template(
        "admin/usersList.html",
        users=users,
        total_users=total_users,
        active_page="admin_users",
    )


@admin_bp.route("/admin/companies")
def admin_companies():
    guard = require_sysadmin()
    if guard:
        return guard

    resp = (
        supabase
        .table("company")
        .select("*")
        .execute()
    )
    companies = resp.data or []

    return render_template(
        "admin/companiesList.html",
        companies=companies,
        active_page="admin_companies",
    )

@admin_bp.route("/admin/tech-dashboard")
def tech_dashboard():
    if session.get("role") != "admin_tech":
        return redirect(url_for("main.index"))

    return render_template("admin/techDashboard.html", active_page="tech_dashboard")
