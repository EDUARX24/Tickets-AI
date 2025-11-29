# app/__init__.py
import os
from flask import Flask
from flask_session import Session
from dotenv import load_dotenv
from supabase import create_client, Client
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

session_ext = Session()
supabase: Client | None = None
db = None


def create_app():
    global supabase, db

    load_dotenv()

    # 👇 OJO: ya NO ponemos template_folder="../templates"
    app = Flask(__name__)  # por defecto usa app/templates y app/static

    # Config básica
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"
    session_ext.init_app(app)

    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # DB (si la usas)
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        engine = create_engine(db_url)
        db = scoped_session(sessionmaker(bind=engine))
        app.extensions["sqlalchemy_db"] = db

    # Blueprints
    from .main.routes import main_bp
    from .auth.routes import auth_bp
    from .admin.routes import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    return app
