import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
    logging.info("Environment variables loaded from .env file")
except ImportError:
    logging.info("python-dotenv not installed, using system environment variables")
except Exception as e:
    logging.warning(f"Could not load .env file: {e}")

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

# Configure database - handle MSSQL, PostgreSQL, and SQLite
mssql_server = os.environ.get("MSSQL_SERVER")
mssql_database = os.environ.get("MSSQL_DATABASE")
mssql_username = os.environ.get("MSSQL_USERNAME")
mssql_password = os.environ.get("MSSQL_PASSWORD")
database_url = os.environ.get("DATABASE_URL")

# Database connection priority: MSSQL > PostgreSQL > SQLite
database_configured = False

# Try MSSQL first (only if all required variables are set and not empty)
if (mssql_server and mssql_server.strip() and 
    mssql_database and mssql_database.strip() and 
    mssql_username and mssql_username.strip() and 
    mssql_password and mssql_password.strip()):
    
    # Check if we're in a Windows environment (required for MSSQL)
    import platform
    if platform.system() == "Windows":
        from urllib.parse import quote_plus
        
        try:
            # Encode credentials for URL
            encoded_username = quote_plus(mssql_username)
            encoded_password = quote_plus(mssql_password)
            encoded_server = quote_plus(mssql_server)
            encoded_database = quote_plus(mssql_database)
            
            # Try multiple connection configurations
            connection_configs = [
                # Configuration 1: TCP/IP connection
                {
                    'url': f"mssql+pyodbc://{encoded_username}:{encoded_password}@{encoded_server}/{encoded_database}?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes",
                    'description': 'ODBC Driver 17 with TCP/IP'
                },
                # Configuration 2: Named Pipes disabled
                {
                    'url': f"mssql+pyodbc://{encoded_username}:{encoded_password}@{encoded_server}/{encoded_database}?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&Trusted_Connection=no",
                    'description': 'ODBC Driver 17 without Named Pipes'
                },
                # Configuration 3: SQL Server driver fallback
                {
                    'url': f"mssql+pyodbc://{encoded_username}:{encoded_password}@{encoded_server}/{encoded_database}?driver=SQL+Server&TrustServerCertificate=yes",
                    'description': 'SQL Server driver'
                }
            ]
            
            for config in connection_configs:
                try:
                    logging.info(f"Trying MSSQL connection: {config['description']}")
                    
                    # Test the connection first
                    from sqlalchemy import create_engine, text
                    test_engine = create_engine(config['url'], pool_timeout=5)
                    with test_engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                        # Connection successful, configure Flask
                        app.config["SQLALCHEMY_DATABASE_URI"] = config['url']
                        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
                            "pool_recycle": 300,
                            "pool_pre_ping": True,
                            "pool_size": 5,
                            "max_overflow": 10,
                            "pool_timeout": 10,
                            "connect_args": {
                                "timeout": 10,
                                "autocommit": False
                            }
                        }
                        logging.info(f"✅ MSSQL connection successful: {mssql_server}/{mssql_database}")
                        database_configured = True
                        break
                        
                except Exception as e:
                    logging.warning(f"❌ MSSQL connection failed with {config['description']}: {e}")
                    continue
            
            if not database_configured:
                logging.error(f"❌ All MSSQL connection attempts failed for {mssql_server}/{mssql_database}")
                logging.info("Falling back to next database option...")
                
        except Exception as e:
            logging.error(f"MSSQL connection error: {e}")
            logging.info("Falling back to next database option...")
    else:
        logging.info("MSSQL configuration detected but not supported on this platform (non-Windows)")
        logging.info("Falling back to next database option...")

# Try PostgreSQL if MSSQL failed or not configured
if not database_configured and database_url:
    # Replit environment with PostgreSQL
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20
    }
    logging.info("Using PostgreSQL database")
    database_configured = True

# Fall back to SQLite if no other database is configured
if not database_configured:
    # Local development - create SQLite database with proper path handling
    import tempfile
    
    # Try to create instance directory in current working directory
    try:
        instance_dir = os.path.join(os.getcwd(), "instance")
        os.makedirs(instance_dir, exist_ok=True)
        db_path = os.path.join(instance_dir, "wms.db")
        
        # Test if we can write to this location
        test_file = os.path.join(instance_dir, "test.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
        logging.info(f"Using SQLite database for local development: {db_path}")
        
    except (OSError, PermissionError) as e:
        # Fallback to temp directory
        logging.warning(f"Cannot create database in instance directory: {e}")
        temp_dir = tempfile.gettempdir()
        db_path = os.path.join(temp_dir, "wms.db")
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
        logging.info(f"Using SQLite database in temp directory: {db_path}")
        
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
    import models_extensions
    db.create_all()
    logging.info("Database tables created")

    # Create default branch
    default_branch = models_extensions.Branch.query.filter_by(id='BR001').first()
    if not default_branch:
        default_branch = models_extensions.Branch(
            id='BR001',
            name='Main Branch',
            address='Main Office',
            is_active=True,
            is_default=True
        )
        db.session.add(default_branch)
        db.session.commit()
        logging.info("Default branch created")

    # Create default admin user
    from werkzeug.security import generate_password_hash
    admin = models.User.query.filter_by(username='admin').first()
    if not admin:
        admin = models.User(username='admin',
                            email='admin@company.com',
                            password_hash=generate_password_hash('admin123'),
                            first_name='System',
                            last_name='Administrator',
                            role='admin',
                            branch_id='BR001',
                            default_branch_id='BR001')
        db.session.add(admin)
        db.session.commit()
        logging.info("Default admin user created")

# Import routes to register them
import routes
