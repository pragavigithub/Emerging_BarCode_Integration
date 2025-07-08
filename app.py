import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)


class Base(DeclarativeBase):
    pass


# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get(
    "SESSION_SECRET") or "dev-secret-key-change-in-production"
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration with robust error handling
database_url = os.environ.get("DATABASE_URL")
mssql_server = os.environ.get("MSSQL_SERVER", "DESKTOP-PLFK2B5\\SQLEXPRESS")
mssql_database = os.environ.get("MSSQL_DATABASE", "WMS_DB")
mssql_username = os.environ.get("MSSQL_USERNAME", "sa")
mssql_password = os.environ.get("MSSQL_PASSWORD", "Ea@12345")

def configure_database():
    """Configure database with proper connection string handling"""
    if database_url:
        # Production/Replit environment with PostgreSQL
        logging.info("Using PostgreSQL database")
        return database_url
    
    elif mssql_server and mssql_username and mssql_password:
        try:
            # Local development with MS SQL Server
            from urllib.parse import quote_plus
            
            # URL encode problematic characters
            encoded_server = quote_plus(mssql_server)
            encoded_password = quote_plus(mssql_password)
            encoded_username = quote_plus(mssql_username)
            
            # Build connection string with proper encoding
            connection_string = (
                f"mssql+pyodbc://{encoded_username}:{encoded_password}@{encoded_server}/"
                f"{mssql_database}?driver=ODBC+Driver+17+for+SQL+Server&"
                f"TrustServerCertificate=yes&Encrypt=no"
            )
            
            logging.info(f"Using MS SQL Server database: {mssql_server}/{mssql_database}")
            return connection_string
            
        except Exception as e:
            logging.error(f"Error configuring MSSQL: {e}")
            logging.info("Falling back to SQLite due to MSSQL configuration error")
            return None
    else:
        logging.info("No database configuration found, using SQLite")
        return None

# Configure database
db_config = configure_database()
if db_config:
    app.config["SQLALCHEMY_DATABASE_URI"] = db_config
else:
    # Fallback to SQLite with proper directory creation
    os.makedirs("instance", exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///instance/wms.db"
    logging.info("Using SQLite database for local development")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# SAP B1 Configuration
app.config['SAP_B1_SERVER'] = os.environ.get('SAP_B1_SERVER',
                                             'https://192.168.1.5:50000')
app.config['SAP_B1_USERNAME'] = os.environ.get('SAP_B1_USERNAME', 'manager')
app.config['SAP_B1_PASSWORD'] = os.environ.get('SAP_B1_PASSWORD', 'Ea@12345')
app.config['SAP_B1_COMPANY_DB'] = os.environ.get('SAP_B1_COMPANY_DB',
                                                 'Test_Hutchinson')

with app.app_context():
    # Import models to create tables
    import models
    db.create_all()
    logging.info("Database tables created")

    # Create default admin user
    from werkzeug.security import generate_password_hash
    admin = models.User.query.filter_by(username='admin').first()
    if not admin:
        admin = models.User(username='admin',
                            email='admin@company.com',
                            password_hash=generate_password_hash('admin123'),
                            first_name='System',
                            last_name='Administrator',
                            role='admin')
        db.session.add(admin)
        db.session.commit()
        logging.info("Default admin user created")
