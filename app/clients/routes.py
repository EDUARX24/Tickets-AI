# app/admin/routes.py
from flask import Blueprint, app, render_template, session, redirect, url_for,request, flash
from app import supabase
from datetime import datetime
from werkzeug.security import (
    generate_password_hash, check_password_hash
)

#blueprint para los clientes administradores
client_admin_bp = Blueprint("client_admin", __name__)

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

#endpoint de bienvenida para admin_cliente
@client_admin_bp.route("/client_admin/home")
def home_client_admin():
    # ─────────────────────────────────────────────
    # Proteger la ruta: solo usuarios logueados
    # y con rol admin_cliente
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
    # Obtener información de la compañía y del admin
    # ─────────────────────────────────────────────
    company_name = "Sin compañía asociada"
    admin_name = "Administrador"

    user_id = session.get("user_id")
    company_id = session.get("company_id")

    # --- Obtener nombre del admin desde users ---
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

    # --- Obtener nombre de la compañía ---
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


    return render_template(
        "clients/homeClients.html",
        company_name=company_name,
        admin_name=admin_name,
        active_page="client_dashboard",
    )


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

@client_admin_bp.route("/client_admin/tickets/manual", methods=["GET"])
def create_ticket_manual():
    # Validaciones básicas de sesión/rol
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") not in ["admin_cliente", "admin_op"]:
        return redirect(url_for("main.index"))

    # Obtener categorías desde Supabase
    try:
        resp_cat = supabase.table("category").select("*").execute()
        categories = resp_cat.data or []
    except:
        categories = []

    # Obtener prioridades desde Supabase
    try:
        resp_pri = supabase.table("priority").select("*").order("sort_order").execute()
        priorities = resp_pri.data or []
    except:
        priorities = []

    return render_template(
        "clients/createTicketManual.html",
        categories=categories,
        priorities=priorities,
        active_page="create_ticket_manual"
    )

@client_admin_bp.route("/client_admin/tickets/ia", methods=["GET"])
def create_ticket_ai():
    # Proteger la ruta (mismo criterio que el ticket manual)
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") not in ["admin_cliente", "admin_op"]:
        return redirect(url_for("main.index"))

    return render_template(
        "clients/createTicketAI.html",
        active_page="create_ticket_ai"
    )



