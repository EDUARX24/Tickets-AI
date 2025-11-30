# app/admin/routes.py
from flask import Blueprint, render_template, session, redirect, url_for,request, flash
from app import supabase
from datetime import datetime


#blueprint para los clientes administradores
client_admin_bp = Blueprint("client_admin", __name__)
@client_admin_bp.route("/client-admin")
def home_client_admin():
    return render_template("clients/homeClients.html") 

@client_admin_bp.route("/company/create", methods=["GET", "POST"])
def create_company():
    # ─────────────────────────────────────────────
    # 1. Proteger la ruta: solo usuarios logueados
    #    y con rol admin_cliente
    # ─────────────────────────────────────────────
    if "user_id" not in session:
        flash("Debes iniciar sesión para continuar.", "warning")
        return redirect(url_for("auth.login"))

    if session.get("role") != "admin_cliente":
        flash("No tienes permisos para registrar una compañía.", "danger")
        return redirect(url_for("main.index"))

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
        "id_username":    user_id,                             # FK hacia users.username_id
        "created_at":     datetime.utcnow().isoformat(),       # opcional si la tabla no lo autogenera
    }
    #print de todo el payload en una línea para debug
    print("Creating company with payload:", payload)

    # Validación mínima: nombre legal obligatorio
    if not payload["name"]:
        flash("El nombre legal de la compañía es obligatorio.", "danger")
        return redirect(url_for("client_admin.create_company"))

    try:
        resp = (
            supabase
            .table("company")
            .insert(payload)
            .execute()
        )
    except Exception as e:
        print("Error al crear compañía en Supabase:", e)
        flash("Ocurrió un error al registrar la compañía. Inténtalo de nuevo.", "danger")
        return redirect(url_for("client_admin.create_company"))

    # Si Supabase devolvió la fila creada
    if resp.data:
        company = resp.data[0]
        # guarda el company_id en la sesión
        session["company_id"] = company.get("company_id")
        flash("Compañía registrada correctamente.", "success")
        return redirect(url_for("client_admin.home_client_admin"))

    # Por si no regresara datos
    flash("No se pudo guardar la compañía. Inténtalo nuevamente.", "danger")
    return redirect(url_for("client_admin.create_company"))