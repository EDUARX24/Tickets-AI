# app/auth/routes.py
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from werkzeug.security import (
    generate_password_hash, check_password_hash
)
from app import supabase

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # rol por defecto
        role = "admin_cliente"

        # validar campos vacíos
        if not username or not email or not password:
            # cambiar el flash por la de sweetalert 
            data = {
                'icon': 'error',
                'title': 'Error',
                'text': 'Falto llenar un campo',
                'redirect': url_for('auth.register')
            }
            return render_template("notification.html", data=data)

        if supabase is None:
            data = {
                'icon': 'error',
                'title': 'Error',
                'text': 'Error interno con Supabase',
                'redirect': url_for('auth.register')
            }
            return render_template("notification.html", data=data)
        # Verificar usuario existente (puedes ajustar columnas)
        existing_user = (
            supabase.table("users")
            .select("*")
            .or_(f"username.eq.{username},email.eq.{email}")
            .execute()
        )

        if existing_user.data:
            data = {
            'icon': 'error',
            'title': 'Usuario o email ya existe',
            'text': 'Elige otro usuario o email',
            'redirect': url_for('auth.register')  
            }
            return render_template("notification.html", data=data)

        # Crear usuario
        hashed_password = generate_password_hash(password)
        new_user = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "role": role,
        }

        supabase.table("users").insert(new_user).execute()
        data = {
                'icon': 'success',
                'title': 'Cuenta Registrada',
                'text': '¡Cuenta creada correctamente! Inicia sesión.',
                'redirect': url_for('auth.login')
            }
        return render_template("notification.html", data=data)
    return render_template("auth/register.html",active_page="register")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # validar campos vacíos
        if not email or not password:
            data = {
                'icon': 'error',
                'title': 'Error de Autenticación',
                'text': 'Debe ingresar correo y contraseña.',
                'redirect': url_for('auth.login')
            }
            return render_template("notification.html", data=data)

        # Verificar supabase
        if supabase is None:
            data = {
                'icon': 'error',
                'title': 'Error',
                'text': 'Error interno con Supabase',
                'redirect': url_for('auth.login')
            }
            return render_template("notification.html", data=data)

        # Fetch user
        user_response = (
            supabase.table("users")
            .select("*")
            .eq("email", email)
            .execute()
        )
        user = user_response.data[0] if user_response.data else None

        # Validar credenciales
        if user and check_password_hash(user["password"], password):

            # guardar datos en sesión
            session["user_id"] = user.get("username_id") or user.get("id")
            session["email"] = user["email"]
            session["role"] = user["role"]
             # ⭐ NUEVO: guardar el nombre de usuario para la navbar
            session["username"] = user.get("username") or user["email"]

            print(f"User role: {session['role']}")

            # ─────────────────────────────────────────────
            # SweetAlert: LOGIN EXITOSO
            # ─────────────────────────────────────────────
            success_data = {
                'icon': 'success',
                'title': '¡Bienvenido!',
                'text': 'Inicio de sesión exitoso.',
            }

            # ─────────────────────────────────────────────
            # ROL: sysAdmin  
            # ─────────────────────────────────────────────
            if user["role"] == "sysAdmin":
                success_data['redirect'] = url_for("admin.home_admin")
                return render_template("notification.html", data=success_data)

            # ─────────────────────────────────────────────
            # ROL: admin_cliente  
            # ─────────────────────────────────────────────
            elif user["role"] == "admin_cliente":
                user_id = session["user_id"]

                company_resp = (
                    supabase.table("company")
                    .select("company_id")
                    .eq("id_username", user_id)
                    .execute()
                )

                if company_resp.data:
                    company_id = company_resp.data[0]["company_id"]
                    session["company_id"] = company_id

                    success_data['redirect'] = url_for("client_admin.home_client_admin")
                    return render_template("notification.html", data=success_data)

                else:
                    data = {
                        'icon': 'info',
                        'title': 'Registrar Compañía',
                        'text': 'Debes registrar la compañía para continuar.',
                        'redirect': url_for('client_admin.create_company')
                    }
                    return render_template("notification.html", data=data)
            # ─────────────────────────────────────────────
            # ROL: sysAdmin  
            # ─────────────────────────────────────────────
            elif user["role"] == "admin_tech":
                success_data['redirect'] = url_for("admin.tech_dashboard")
                return render_template("notification.html", data=success_data)
            # ─────────────────────────────────────────────
            # Otros roles  
            # ─────────────────────────────────────────────
            else:
                success_data['redirect'] = url_for("main.index")
                return render_template("notification.html", data=success_data)

        # Credenciales incorrectas
        data = {
            'icon': 'error',
            'title': 'Error de Autenticación',
            'text': 'Usuario o contraseña incorrectos.',
            'redirect': url_for('auth.login')
        }
        return render_template("notification.html", data=data)

    return render_template("auth/login.html", active_page="login")



#ENDPoint for logout
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada", "success")
    return redirect(url_for("auth.login"))
