import os
import json
from flask import Flask, session, render_template, url_for, request, redirect, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) # Supabase client initialized

load_dotenv()

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    return render_template("prueba.html")

# Endpoint Register
@app.route("/register", methods=["GET", "POST"])
def register():
    #crear cuenta usuario usando supabase
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # asignar role por defecto
        role = "admin_cliente"

        # Check if username or email already exists
        existing_user = supabase.table("users").select("*").or_(f"username.eq.{username},email.eq.{email}").execute()
        if existing_user.data:
            flash("Username or email already exists", "danger")
            return redirect(url_for("register"))
        
        # validar campos vacios
        if not username or not email or not password:
            flash("Please fill out all fields", "danger")
            return redirect(url_for("register"))

        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = {"username": username,"email": email,"password": hashed_password, "role": role}
        supabase.table("users").insert(new_user).execute()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("login"))
        
    # Render register template
    return render_template("auth/register.html")

#endpoint login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # validar campos vacios
        if not email or not password:
            flash("Please fill out all fields", "danger")
            return redirect(url_for("login"))

        # Fetch user from database
        user_response = supabase.table("users").select("*").eq("email", email).execute()
        user = user_response.data[0] if user_response.data else None

        # Validar credenciales
        if user and check_password_hash(user["password"], password):
            # Guardar datos en sesión
            session["user_id"] = user["username_id"]   # <- nombre real de la columna
            session["email"] = user["email"]
            session["role"] = user["role"]

            flash("Logged in successfully!", "success")

            # Redirigir según rol
            if user["role"] == "admin_cliente":   # o 'admin', según tus valores
                return redirect(url_for("home_admin"))
            else:
                return redirect(url_for("index"))

        # Si llegó aquí, las credenciales son inválidas
        flash("Invalid email or password", "danger")
        return redirect(url_for("login"))

    # Render login template
    return render_template("auth/login.html")

#endpoint home admin
@app.route("/admin")
def home_admin():
    return render_template("admin/homeAdmin.html")

@app.route("/logout")
def logout():
    session.clear()
    return render_template("auth/login.html")

if __name__ == "__main__":
    app.run(debug=True)