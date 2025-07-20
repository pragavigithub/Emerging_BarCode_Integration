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

# Configure database with multiple database support
# Priority: MySQL > PostgreSQL > SQLite (fallback)
database_url = None
db_type = "unknown"

# Check for MySQL configuration
mysql_host = os.environ.get("MYSQL_HOST")
mysql_user = os.environ.get("MYSQL_USER")
mysql_password = os.environ.get("MYSQL_PASSWORD")
mysql_database = os.environ.get("MYSQL_DATABASE")

if mysql_host and mysql_user and mysql_password and mysql_database:
    # MySQL configuration with proper URL encoding
    from urllib.parse import quote_plus
    encoded_password = quote_plus(mysql_password)
    database_url = f"mysql+pymysql://{mysql_user}:{encoded_password}@{mysql_host}/{mysql_database}"
    db_type = "mysql"
    logging.info("✅ Using MySQL database")
elif os.environ.get("DATABASE_URL"):
    # PostgreSQL configuration (Replit environment)
    database_url = os.environ.get("DATABASE_URL")
    db_type = "postgresql"
    logging.info("✅ Using PostgreSQL database for Replit deployment")

if database_url:
    # Production database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20
    }
    logging.info(f"Database URL configured: {database_url.replace(encoded_password, '***') if 'encoded_password' in locals() else database_url}")
else:
    # Local development fallback - create SQLite database with proper path handling
    import tempfile
    
    db_type = "sqlite"
    logging.info("⚠️  MySQL/PostgreSQL not configured, falling back to SQLite")
    
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
        logging.info(f"📁 Using SQLite database for local development: {db_path}")
        
    except (OSError, PermissionError) as e:
        # Fallback to temp directory
        logging.warning(f"Cannot create database in instance directory: {e}")
        temp_dir = tempfile.gettempdir()
        db_path = os.path.join(temp_dir, "wms.db")
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
        logging.info(f"📁 Using SQLite database in temp directory: {db_path}")
        
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }

# Store database type for use in other modules
app.config["DB_TYPE"] = db_type

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
    
    # Add missing columns for local SQLite development
    if not database_url:  # Only for local SQLite
        try:
            from sqlalchemy import text
            
            # Check if we're using SQLite and add missing columns
            if 'sqlite' in str(db.engine.url):
                logging.info("🔧 Checking for missing columns in SQLite database...")
                
                # Try to add notes column to grpo_documents if it doesn't exist
                try:
                    db.session.execute(text("ALTER TABLE grpo_documents ADD COLUMN notes TEXT"))
                    db.session.commit()
                    logging.info("✅ Added 'notes' column to grpo_documents")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        logging.info("✓ 'notes' column already exists")
                    else:
                        logging.debug(f"Notes column: {e}")
                
                # Try to add serial_number column to grpo_items if it doesn't exist
                try:
                    db.session.execute(text("ALTER TABLE grpo_items ADD COLUMN serial_number VARCHAR(50)"))
                    db.session.commit()
                    logging.info("✅ Added 'serial_number' column to grpo_items")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        logging.info("✓ 'serial_number' column already exists")
                    else:
                        logging.debug(f"Serial number column: {e}")
                        
                logging.info("✅ SQLite schema migration completed")
                
        except Exception as e:
            logging.warning(f"Schema migration warning: {e}")

    # Create default branch (with error handling for MySQL)
    try:
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
    except Exception as e:
        logging.warning(f"Could not create/query default branch: {e}")
        logging.info("Please run fix_mysql_database.py to fix database schema")
        # Continue with application startup

    # Create default admin user (with error handling for MySQL)
    try:
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
    except Exception as e:
        logging.warning(f"Could not create/query admin user: {e}")
        logging.info("Please run quick_mysql_fix.py to fix database schema")
        # Continue with application startup

# Import routes to register them
import routes
