# app/admin/routes.py
from flask import Blueprint, render_template, session, redirect, url_for, request
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
    # Solo permite acceso a SysAdmin
    guard = require_sysadmin()
    if guard:
        return guard

    user_id = session.get("user_id")

    # # --- Inicializar nombre por defecto ---
    # admin_name = "Administrador"

    # # --- Obtener nombre del usuario desde tabla users ---
    # if user_id:
    #     try:
    #         resp_user = (
    #             supabase
    #             .table("users")
    #             .select("username")
    #             .eq("username_id", user_id)
    #             .single()
    #             .execute()
    #         )
    #         if resp_user.data:
    #             admin_name = resp_user.data.get("username", admin_name)

    #         # Guardar también en sesión para usarlo en toda la app
    #         session["username"] = admin_name

    #     except Exception as e:
    #         print("Error obteniendo usuario:", e)

    # ─────────────────────────────────────
    # MÉTRICAS PRINCIPALES
    # ─────────────────────────────────────

    resp_tickets = supabase.table("ticket").select("*", count="exact").execute()
    total_tickets = resp_tickets.count or 0

    resp_users = supabase.table("users").select("username_id", count="exact").execute()
    total_users = resp_users.count or 0

    resp_collab = (
        supabase.table("users")
        .select("username_id", count="exact")
        .eq("role", "admin_tech")
        .execute()
    )
    total_collaborators = resp_collab.count or 0

    resp_companies = (
        supabase.table("company")
        .select("company_id", count="exact")
        .execute()
    )
    total_companies = resp_companies.count or 0

    # ─────────────────────────────────────
    # TICKETS RECIENTES
    # ─────────────────────────────────────
    resp_recent = (
        supabase
        .table("ticket")
        .select("ticket_id, title, status, priority_id, category_id, created_at")
        .order("created_at", desc=True)
        .limit(5)
        .execute()
    )

    raw_tickets = resp_recent.data or []
    recent_tickets = []

    for row in raw_tickets:
        category_id = row.get("category_id")
        category_name = "Sin categoría"

        if category_id:
            try:
                resp_cat = (
                    supabase
                    .table("category")
                    .select("name")
                    .eq("category_id", category_id)
                    .single()
                    .execute()
                )
                if resp_cat.data:
                    category_name = resp_cat.data["name"]
            except:
                pass

        status = row.get("status") or "open"
        status_color = {
            "open": "primary",
            "closed": "success",
            "pending": "warning",
        }.get(status, "secondary")

        priority_id = row.get("priority_id")
        priority, priority_color = {
            1: ("Baja", "success"),
            2: ("Media", "warning"),
            3: ("Alta", "danger"),
        }.get(priority_id, ("N/D", "secondary"))

        recent_tickets.append({
            "id": row["ticket_id"],
            "title": row.get("title", "Sin título"),
            "status": status,
            "status_color": status_color,
            "priority": priority,
            "priority_color": priority_color,
            "category_name": category_name,
            "created_at": row.get("created_at"),
        })

    return render_template(
        "admin/homeAdmin.html",
        total_tickets=total_tickets,
        total_users=total_users,
        total_collaborators=total_collaborators,
        total_companies=total_companies,
        recent_tickets=recent_tickets,
        # admin_name=admin_name, 
        active_page="admin_home",
    )


@admin_bp.route("/admin/tickets")
def admin_tickets():
    guard = require_sysadmin()
    if guard:
        return guard

    # ─────────────────────────────────────
    # Parámetros de paginación y búsqueda
    # ─────────────────────────────────────
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "", type=str).strip()
    per_page = 10

    start = (page - 1) * per_page
    end = start + per_page - 1

    # ─────────────────────────────────────
    # Query base con joins lógicos
    # ─────────────────────────────────────
    query = (
        supabase
        .table("ticket")
        .select("""
            ticket_id,
            title,
            description,
            status,
            created_at,
            created_by_company_user_id,
            priority:priority_id (
                priority_id,
                code
            ),
            category:category_id (
                category_id,
                name
            ),
            company:id_company (
                company_id,
                commercialName,
                name
            )
        """, count="exact")
        .order("created_at", desc=True)
    )

    # Filtro de búsqueda (título o descripción)
    if q:
        pattern = f"%{q}%"
        query = query.or_(
            f"title.ilike.{pattern},description.ilike.{pattern}"
        )

    resp = query.range(start, end).execute()

    tickets = resp.data or []
    total_tickets = resp.count or 0
    total_pages = (total_tickets + per_page - 1) // per_page  # ceil entero

    return render_template(
        "admin/ticketsList.html",
        tickets=tickets,
        total_tickets=total_tickets,
        page=page,
        total_pages=total_pages,
        q=q,
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
