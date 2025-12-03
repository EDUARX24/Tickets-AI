# app/admin/routes.py
from flask import Blueprint, app, render_template, session, redirect, url_for,request, flash
from app import supabase
from datetime import datetime
from werkzeug.security import (generate_password_hash, check_password_hash)
from math import ceil
import os
import requests

#blueprint para los clientes administradores
client_admin_bp = Blueprint("client_admin", __name__)

TICKETS_IA_API_URL = os.getenv("TICKETS_IA_API_URL", "http://localhost:8000")

# Mapeo nombre categoría (modelo) -> ID en tu tabla category
CATEGORY_NAME_TO_ID = {
    "Red y Conectividad": 1,
    "Software y Aplicaciones": 2,
    "Hardware": 3,
    "Impresoras y Escáneres": 4,
    "Accesos y Contraseñas": 5,
    "Archivos y Almacenamiento": 6,
    "CCTV y Seguridad": 7,
    "Telefonía": 8,
    "Soporte General": 9,
}

# Mapeo nombre prioridad (modelo) -> ID en tabla priority
PRIORITY_NAME_TO_ID = {
    "Baja": 1,
    "Media": 2,
    "Alta": 3,
    "Urgente": 4,
}

# Endpoint para crear una nueva compañía
@client_admin_bp.route("/company/create", methods=["GET", "POST"])
def create_company():
    # ─────────────────────────────────────────────
    # 1. Proteger la ruta: solo usuarios logueados
    #    y con rol admin_cliente
    # ─────────────────────────────────────────────
    if "user_id" not in session:
        data = {
            "icon": "warning",
            "title": "Sesión requerida",
            "text": "Debes iniciar sesión para registrar una compañía.",
            "redirect": url_for("auth.login"),
        }
        return render_template("notification.html", data=data)

    if session.get("role") != "admin_cliente":
        data = {
            "icon": "error",
            "title": "Acceso denegado",
            "text": "No tienes permisos para registrar una compañía.",
            "redirect": url_for("main.index"),
        }
        return render_template("notification.html", data=data)
    

    # ─────────────────────────────────────────────
    # 2. Método GET → solo mostrar el formulario
    # ─────────────────────────────────────────────
    if request.method == "GET":
        return render_template("clients/createCompany.html")

    # ─────────────────────────────────────────────
    # 3. Método POST → crear compañía en Supabase
    # ─────────────────────────────────────────────
    form = request.form
    user_id = session["user_id"]

    # Checkbox de estado (switch)
    status_value = True if form.get("status") == "on" else False

    payload = {
        "name":           form.get("name") or None,
        "commercialName": form.get("commercialName") or None,
        "businessName":   form.get("businessName") or None,
        "countryCode":    form.get("countryCode") or None,
        "countryNumber":  form.get("countryNumber") or None,
        "phoneNumber":    form.get("phoneNumber") or None,
        "countryCity":    form.get("countryCity") or None,
        "stateProvince":  form.get("stateProvince") or None,
        "addressPrimary": form.get("addressPrimary") or None,
        "webSite":        form.get("webSite") or None,
        "imageUrl":       form.get("imageUrl") or None,
        "status":         status_value,
        "id_username":    user_id,
        "created_at":     datetime.utcnow().isoformat(),
    }

    print("Creating company with payload:", payload)

    # Validación mínima: nombre legal obligatorio
    if not payload["name"]:
        data = {
            "icon": "error",
            "title": "Datos incompletos",
            "text": "El nombre legal de la compañía es obligatorio.",
            "redirect": url_for("client_admin.create_company"),
        }
        return render_template("notification.html", data=data)

    try:
        resp = (
            supabase
            .table("company")
            .insert(payload)
            .execute()
        )
    except Exception as e:
        print("Error al crear compañía en Supabase:", e)
        data = {
            "icon": "error",
            "title": "Error al guardar",
            "text": "Ocurrió un error al registrar la compañía. Inténtalo de nuevo.",
            "redirect": url_for("client_admin.create_company"),
        }
        return render_template("notification.html", data=data)

    # Si Supabase devolvió la fila creada
    if resp.data:
        company = resp.data[0]
        session["company_id"] = company.get("company_id")

        data = {
            "icon": "success",
            "title": "Compañía registrada",
            "text": "La compañía se registró correctamente.",
            "redirect": url_for("client_admin.home_client_admin"),
        }
        return render_template("notification.html", data=data)

    # Por si no regresara datos
    data = {
        "icon": "error",
        "title": "No se guardó la compañía",
        "text": "No se pudo guardar la compañía. Inténtalo nuevamente.",
        "redirect": url_for("client_admin.create_company"),
    }
    return render_template("notification.html", data=data)

# Endpoint home del admin de clientes
@client_admin_bp.route("/client_admin/home")
def home_client_admin():
    # ─────────────────────────────────────────────
    # Proteger la ruta
    # ─────────────────────────────────────────────
    if "user_id" not in session:
        data = {
            "icon": "warning",
            "title": "Sesión requerida",
            "text": "Debes iniciar sesión para acceder a esta página.",
            "redirect": url_for("auth.login"),
        }
        return render_template("notification.html", data=data)

    if session.get("role") != "admin_cliente":
        data = {
            "icon": "error",
            "title": "Acceso denegado",
            "text": "No tienes permisos para acceder a esta página.",
            "redirect": url_for("main.index"),
        }
        return render_template("notification.html", data=data)

    # ─────────────────────────────────────────────
    # Info de compañía y admin
    # ─────────────────────────────────────────────
    company_name = "Sin compañía asociada"
    admin_name = "Administrador"

    user_id = session.get("user_id")
    company_id = session.get("company_id")

    # --- Nombre del admin (tabla users) ---
    if user_id:
        try:
            resp_user = (
                supabase
                .table("users")
                .select("username")
                .eq("username_id", user_id)
                .single()
                .execute()
            )
            if resp_user.data:
                admin_name = resp_user.data.get("username", admin_name)
        except Exception as e:
            print("Error obteniendo usuario:", e)

    # --- Nombre de la compañía ---
    if company_id:
        try:
            resp_company = (
                supabase
                .table("company")
                .select("company_id, name, commercialName")
                .eq("company_id", company_id)
                .single()
                .execute()
            )
            company = resp_company.data
            if company:
                company_name = (
                    company.get("commercialName")
                    or company.get("name")
                    or company_name
                )
        except Exception as e:
            print("Error obteniendo compañía:", e)

    # ─────────────────────────────────────────────
    # Métricas de tickets
    # ─────────────────────────────────────────────
    open_tickets = 0
    resolved_tickets = 0
    overdue_tickets = 0
    month_tickets = 0
    total_tickets = 0

    if company_id:
        try:
            # Total de tickets de la empresa
            resp_total = (
                supabase
                .table("ticket")
                .select("ticket_id", count="exact")
                .eq("id_company", company_id)
                .execute()
            )
            total_tickets = resp_total.count or 0

            # Tickets abiertos (solo status = 'open'; ajusta si quieres incluir in_progress/on_hold)
            resp_open = (
                supabase
                .table("ticket")
                .select("ticket_id", count="exact")
                .eq("id_company", company_id)
                .eq("status", "open")
                .execute()
            )
            open_tickets = resp_open.count or 0

            # Tickets resueltos (resolved + closed)
            resp_resolved = (
                supabase
                .table("ticket")
                .select("ticket_id", count="exact")
                .eq("id_company", company_id)
                .in_("status", ["resolved", "closed"])
                .execute()
            )
            resolved_tickets = resp_resolved.count or 0

            # Tickets fuera de SLA:
            # ejemplo: response_due_at vencida y ticket no cerrado/cancelado
            now_iso = datetime.utcnow().isoformat()

            resp_overdue = (
                supabase
                .table("ticket")
                .select("ticket_id", count="exact")
                .eq("id_company", company_id)
                .not_.in_("status", ["resolved", "closed", "cancelled"])
                .lt("response_due_at", now_iso)
                .execute()
            )
            overdue_tickets = resp_overdue.count or 0

            # Tickets creados este mes
            now = datetime.utcnow()
            start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            start_month_iso = start_month.isoformat()

            resp_month = (
                supabase
                .table("ticket")
                .select("ticket_id", count="exact")
                .eq("id_company", company_id)
                .gte("created_at", start_month_iso)
                .execute()
            )
            month_tickets = resp_month.count or 0

        except Exception as e:
            print("Error obteniendo métricas de tickets:", e)

    return render_template(
        "clients/homeClients.html",
        company_name=company_name,
        admin_name=admin_name,
        active_page="client_dashboard",
        open_tickets=open_tickets,
        resolved_tickets=resolved_tickets,
        overdue_tickets=overdue_tickets,
        month_tickets=month_tickets,
        total_tickets=total_tickets,
    )

#endpont para ver los tickets de la compañia
@client_admin_bp.route("/client_admin/tickets")
def company_tickets():
    # Proteger la ruta
    if "user_id" not in session:
        data = {
            "icon": "warning",
            "title": "Sesión requerida",
            "text": "Debes iniciar sesión para acceder a esta página.",
            "redirect": url_for("auth.login"),
        }
        return render_template("notification.html", data=data)

    if session.get("role") != "admin_cliente":
        data = {
            "icon": "error",
            "title": "Acceso denegado",
            "text": "No tienes permisos para acceder a esta página.",
            "redirect": url_for("main.index"),
        }
        return render_template("notification.html", data=data)
      # ─────────────────────────────────────────────
    # Info de compañía y admin
    # ─────────────────────────────────────────────
    company_name = "Sin compañía asociada"
    admin_name = "Administrador"

    user_id = session.get("user_id")
    company_id = session.get("company_id")

    # --- Nombre del admin (tabla users) ---
    if user_id:
        try:
            resp_user = (
                supabase
                .table("users")
                .select("username")
                .eq("username_id", user_id)
                .single()
                .execute()
            )
            if resp_user.data:
                admin_name = resp_user.data.get("username", admin_name)
        except Exception as e:
            print("Error obteniendo usuario:", e)

    # --- Nombre de la compañía ---
    if company_id:
        try:
            resp_company = (
                supabase
                .table("company")
                .select("company_id, name, commercialName")
                .eq("company_id", company_id)
                .single()
                .execute()
            )
            company = resp_company.data
            if company:
                company_name = (
                    company.get("commercialName")
                    or company.get("name")
                    or company_name
                )
        except Exception as e:
            print("Error obteniendo compañía:", e)

      # ─────────────────────────────────────────────
    # Obtener tickets de la compañía
    # ─────────────────────────────────────────────
    page = request.args.get("page", 1, type=int)
    per_page = 10  # tickets por página

    tickets = []
    total_tickets = 0
    total_pages = 1

    if company_id:
        try:
            # calcular rango para Supabase (inclusive)
            start = (page - 1) * per_page
            end = start + per_page - 1

            resp_tickets = (
                supabase
                .table("ticket")
                .select("ticket_id, title, status, created_at", count="exact")
                .eq("id_company", company_id)
                .order("created_at", desc=True)
                .range(start, end)
                .execute()
            )

            tickets = resp_tickets.data or []
            total_tickets = resp_tickets.count or 0
            total_pages = max(ceil(total_tickets / per_page), 1)

        except Exception as e:
            print("Error obteniendo tickets de la compañía:", e)

    return render_template(
        "clients/tickets-company.html",
        active_page="company_tickets",
        company_name=company_name,
        admin_name=admin_name,
        tickets=tickets,
        page=page,
        total_pages=total_pages,
        total_tickets=total_tickets,
        per_page=per_page,
    )

# endpoint ver tickets por id
@client_admin_bp.route("/client_admin/tickets/<int:ticket_id>")
def view_ticket(ticket_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "admin_cliente":
        return redirect(url_for("main.index"))

    company_id = session.get("company_id")

    try:
        resp = (
            supabase
            .table("ticket")
            .select("*")
            .eq("ticket_id", ticket_id)
            .eq("id_company", company_id)  # seguridad: que sea de su empresa
            .single()
            .execute()
        )
        ticket = resp.data
    except Exception as e:
        print("Error obteniendo detalle de ticket:", e)
        ticket = None

    if not ticket:
        data = {
            "icon": "error",
            "title": "Ticket no encontrado",
            "text": "El ticket no existe o no pertenece a tu empresa.",
            "redirect": url_for("client_admin.company_tickets"),
        }
        return render_template("notification.html", data=data)

    return render_template("clients/ticket-detail.html", ticket=ticket)


#endpoint para crear usuarios de compañia
@client_admin_bp.route("/client_admin/users", methods=["GET", "POST"])
def create_company_user():
    if "company_id" not in session:
        flash("No tienes una compañía asociada.", "danger")
        return redirect(url_for("auth.login"))

    company_id = session["company_id"]

    # GET → mostrar formulario
    if request.method == "GET":
        return render_template("clients/createCompanyUser.html")

    # POST → procesar formulario
    form = request.form

    if not form.get("email") or not form.get("password") or not form.get("username_company"):
        # sweetalert puede usarse aquí también
        data = {
            "icon": "error",
            "title": "Datos incompletos",
            "text": "Correo, usuario interno y contraseña son obligatorios.",
            "redirect": url_for("client_admin.create_company_user"),
        }
        return render_template("notification.html", data=data)

    payload = {
        "email": form.get("email"),
        "password": generate_password_hash(form.get("password")),
        "role": form.get("role"),
        "is_activate": True if form.get("is_activate") == "on" else False,
        "imageSelfieUrl": form.get("imageSelfieUrl") or None,
        "phoneNumber": form.get("phoneNumber") or None,
        "username_company": form.get("username_company"),
        "Id_company": company_id,# ✅ NOMBRE REAL DE LA COLUMNA
        "created_at": datetime.utcnow().isoformat()
    }

    print("Creating company user payload:", payload)

    try:
        resp = supabase.table("company_users").insert(payload).execute()
        if resp.data:
            data = {
                "icon": "success",
                "title": "Colaborador registrado",
                "text": "El colaborador se registró correctamente.",
                "redirect": url_for("client_admin.create_company_user"),
            }
            return render_template("notification.html", data=data)

        data = {
            "icon": "error",
            "title": "No se pudo registrar el colaborador",
            "text": "Inténtalo nuevamente.",
            "redirect": url_for("client_admin.create_company_user"),
        }
        return render_template("notification.html", data=data)

    except Exception as e:
        print("Error al crear usuario:", e)
        data = {
            "icon": "error",
            "title": "Error",
            "text": "Error al registrar colaborador.",
            "redirect": url_for("client_admin.create_company_user"),
        }
        return render_template("notification.html", data=data)
    
#EndPoint para probar supabase
@client_admin_bp.route("/client_admin/test-supabase")
def test_supabase():
    data = {"name": "Prueba desde Flask", "is_active": True}
    resp = supabase.table("category").insert(data).execute()
    print(resp)
    return "OK"
    
# ============================
# Nuevo ticket (pantalla para elegir modo)
# ============================
@client_admin_bp.route("/client_admin/tickets/new" , methods=["GET"])
def choose_create_ticket():
    # Proteger la ruta (ajusta el rol según tu diseño)
    if "user_id" not in session:
        data = {
            "icon": "warning",
            "title": "Sesión requerida",
            "text": "Debes iniciar sesión para acceder a esta página.",
            "redirect": url_for("auth.login"),
        }
        return render_template("notification.html", data=data)

    # Aquí podrías permitir tanto admin_cliente como admin_op si quieres:
    if session.get("role") not in ["admin_cliente", "admin_op"]:
        data = {
            "icon": "error",
            "title": "Acceso denegado",
            "text": "No tienes permisos para acceder a esta página.",
            "redirect": url_for("main.index"),
        }
        return render_template("notification.html", data=data)

    # Renderizar la vista de selección de tipo de ticket
    return render_template(
       "clients/CreateTicket.html",
        active_page="op_new_ticket"
    )

@client_admin_bp.route("/client_admin/tickets/manual", methods=["GET", "POST"])
def create_ticket_manual():
    # 1. Validar sesión y rol
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") not in ["admin_cliente", "admin_op"]:
        return redirect(url_for("main.index"))

    # ─────────────────────────────
    # 2. Si es GET → mostrar formulario
    # ─────────────────────────────
    if request.method == "GET":
        try:
            resp_cat = supabase.table("category").select("*").order("sort_order").execute()
            categories = resp_cat.data or []
        except Exception:
            categories = []

        try:
            resp_pri = supabase.table("priority").select("*").order("sort_order").execute()
            priorities = resp_pri.data or []
        except Exception:
            priorities = []

        return render_template(
            "clients/createTicketManual.html",
            categories=categories,
            priorities=priorities,
            active_page="create_ticket_manual",
        )

    # ─────────────────────────────
    # 3. Si es POST → crear ticket
    # ─────────────────────────────
    form = request.form

    title = (form.get("title") or "").strip()
    description = (form.get("description") or "").strip()
    category_id = form.get("category_id")
    priority_id = form.get("priority_id")

    # Validación rápida
    if not title or not description or not category_id or not priority_id:
        # sweetalert puede usarse aquí también
        data = {
            "icon": "error",
            "title": "Datos incompletos",
            "text": "Todos los campos marcados con * son obligatorios.",
            "redirect": url_for("client_admin.create_ticket_manual"),
        }
        return render_template("notification.html", data=data)

    # Conversión a int (la tabla ticket usa int8)
    try:
        category_id = int(category_id)
        priority_id = int(priority_id)
    except ValueError:
        data = {
            "icon": "error",
            "title": "Error de validación",
            "text": "Categoría o prioridad no válida.",
            "redirect": url_for("client_admin.create_ticket_manual"),
        }
        return render_template("notification.html", data=data)

    # Datos de sesión
    company_id = session.get("company_id")          # la empresa del admin_cliente
    # created_by = session.get("user_id")             # quien crea el ticket
    
    # si luego tienes company_user_id, puedes usarlo aquí

    payload = {
        "id_company": company_id,
        # "created_by_company_user_id": created_by,   # ajusta al nombre real de tu columna
        "assigned_to_staff_user_id": None,          # sin asignar por ahora
        "title": title,
        "description": description,
        "category_id": category_id,
        "priority_id": priority_id,
        "status": "open",                           # ENUM ticket_status
        "created_at": datetime.utcnow().isoformat()
    }

    try:
        resp = supabase.table("ticket").insert(payload).execute()
    except Exception as e:
        print("Error al crear ticket:", e)
        data = {
            "icon": "error",
            "title": "Error al registrar ticket",
            "text": "Ocurrió un error al registrar el ticket.",
            "redirect": url_for("client_admin.create_ticket_manual"),
        }
        return render_template("notification.html", data=data)

    # Si todo fue bien
    if resp.data:
        data = {
            "icon": "success",
            "title": "Ticket registrado",
            "text": "El ticket se registró correctamente.",
            "redirect": url_for("client_admin.home_client_admin"),
        }
        return render_template("notification.html", data=data)

    data = {
        "icon": "error",
        "title": "Error",
        "text": "No se pudo registrar el ticket. Intenta nuevamente.",
        "redirect": url_for("client_admin.create_ticket_manual"),
    }
    return render_template("notification.html", data=data)

@client_admin_bp.route("/client_admin/tickets/ia", methods=["GET", "POST"])
def create_ticket_ai():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") not in ["admin_cliente", "admin_op"]:
        return redirect(url_for("main.index"))

    # GET = mostrar formulario
    if request.method == "GET":
        return render_template("clients/createTicketAI.html", active_page="create_ticket_ai")

    # POST = recibir datos del formulario
    title = request.form.get("ia_title", "").strip()
    description = request.form.get("ia_description", "").strip()

    if not title or not description:
        # mostrar error con sweetalert
        data = {
            "icon": "error",
            "title": "Datos incompletos",   
            "text": "Debes ingresar tanto título como descripción.",
            "redirect": url_for("client_admin.create_ticket_ai"),
        }
        return render_template("notification.html", data=data)

    # --- Llamar a la API IA ---
    try:
        resp = requests.post(
            f"{TICKETS_IA_API_URL}/api/predict-ticket",
            json={
                "title": title,
                "description": description,
            }
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print("API Error:", e)
        # mostrar error con sweetalert
        data = {
            "icon": "error",
            "title": "Error de IA",
            "text": "Hubo un error al comunicarse con el servicio de IA. Inténtalo más tarde.",
            "redirect": url_for("client_admin.create_ticket_ai"),
        }
        return render_template("notification.html", data=data)

    # Procesar respuesta
    cat_name = data["category_name"]
    prior_name = data["priority_name"]
    priority_value = data["priority_value"]

    # Aquí mapeas a IDs reales
    category_id = CATEGORY_NAME_TO_ID.get(cat_name)
    priority_id = PRIORITY_NAME_TO_ID.get(prior_name)

    # Crear ticket en Supabase
    try:
        payload = {
            "id_company": session.get("company_id"),
            "created_by_company_user_id": session.get("company_user_id"),
            "title": title,
            "description": description,
            "category_id": category_id,
            "priority_id": priority_id,
            "status": "open"
        }

        supabase.table("ticket").insert(payload).execute()

    except Exception as e:
        print("Error Supabase:", e)
        # mostrar error con sweetalert
        data = {
            "icon": "error",
            "title": "Error al guardar ticket",
            "text": "Ocurrió un error al guardar el ticket generado por IA.",
            "redirect": url_for("client_admin.create_ticket_ai"),
        }
        return render_template("notification.html", data=data)
    
    # Si todo bien
    data = {
        "icon": "success",
        "title": "Ticket creado",
        "text": "El ticket fue creado correctamente usando IA.",
        "redirect": url_for("client_admin.company_tickets"),
    }
    return render_template("notification.html", data=data)

