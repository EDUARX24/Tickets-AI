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
            flash("Please fill out all fields", "danger")
            return redirect(url_for("auth.register"))

        if supabase is None:
            flash("Error interno con Supabase", "danger")
            return redirect(url_for("auth.register"))

        # Verificar usuario existente (puedes ajustar columnas)
        existing_user = (
            supabase.table("users")
            .select("*")
            .or_(f"username.eq.{username},email.eq.{email}")
            .execute()
        )

        if existing_user.data:
            flash("Username or email already exists", "danger")
            return redirect(url_for("auth.register"))

        # Crear usuario
        hashed_password = generate_password_hash(password)
        new_user = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "role": role,
        }

        supabase.table("users").insert(new_user).execute()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html",active_page="register")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # validar campos vacíos
        if not email or not password:
            flash("Please fill out all fields", "danger")
            return redirect(url_for("auth.login"))

        if supabase is None:
            flash("Error interno con Supabase", "danger")
            return redirect(url_for("auth.login"))

        # Fetch user
        user_response = (
            supabase.table("users")
            .select("*")
            .eq("email", email)
            .execute()
        )
        user = user_response.data[0] if user_response.data else None

        if user and check_password_hash(user["password"], password):
            # OJO: ajusta según tus columnas reales
            session["user_id"] = user.get("username_id") or user.get("id")
            session["email"] = user["email"]
            session["role"] = user["role"]

            flash("Logged in successfully!", "success")

            if user["role"] == "admin_cliente":
                return redirect(url_for("admin.home_admin"))
            else:
                return redirect(url_for("main.index"))

        flash("Invalid email or password", "danger")
        return redirect(url_for("auth.login"))

    return render_template("auth/login.html",active_page="login")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada", "success")
    return redirect(url_for("auth.login"))
