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

# Configure database - handle MSSQL, PostgreSQL, and SQLite
mssql_server = os.environ.get("MSSQL_SERVER")
mssql_database = os.environ.get("MSSQL_DATABASE")
mssql_username = os.environ.get("MSSQL_USERNAME")
mssql_password = os.environ.get("MSSQL_PASSWORD")
database_url = os.environ.get("DATABASE_URL")

if mssql_server and mssql_database and mssql_username and mssql_password:
    # MSSQL Server connection with enhanced error handling
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
        
        mssql_connected = False
        for config in connection_configs:
            try:
                logging.info(f"Trying MSSQL connection: {config['description']}")
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
                
                # Test the connection
                from sqlalchemy import create_engine, text
                test_engine = create_engine(config['url'])
                with test_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    logging.info(f"✅ MSSQL connection successful: {mssql_server}/{mssql_database}")
                    mssql_connected = True
                    break
                    
            except Exception as e:
                logging.warning(f"❌ MSSQL connection failed with {config['description']}: {e}")
                continue
        
        if not mssql_connected:
            logging.error(f"❌ All MSSQL connection attempts failed for {mssql_server}/{mssql_database}")
            logging.info("Falling back to available database...")
            raise Exception("MSSQL connection failed")
            
    except Exception as e:
        logging.error(f"MSSQL connection error: {e}")
        logging.info("Falling back to available database...")
        # Fall through to next database option
        
elif database_url:
    # Replit environment with PostgreSQL
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20
    }
    logging.info("Using PostgreSQL database")
else:
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
