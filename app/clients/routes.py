# app/admin/routes.py
from flask import Blueprint, render_template, session, redirect, url_for,request, flash
from app import supabase
from datetime import datetime

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

    return render_template("clients/homeClients.html")