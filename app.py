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
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-please-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database for Replit environment
# Priority: PostgreSQL (Replit) > SQLite (fallback) 
database_url = None
db_type = "unknown"

# Priority 1: PostgreSQL (for Replit environment)
if os.environ.get("DATABASE_URL"):
    database_url = os.environ.get("DATABASE_URL")
    db_type = "postgresql"
    logging.info("✅ Using PostgreSQL database for Replit deployment")

if not database_url:
    logging.info("🔧 No database configured - checking fallback options")

if database_url:
    # Production database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20
    }
    # Log database configuration (URL already masked by environment)
    logging.info(f"Database URL configured: {database_url[:50]}...")
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
login_manager.login_view = 'login'  # type: ignore
login_manager.login_message = 'Please log in to access this page.'

# SAP B1 Configuration
app.config['SAP_B1_SERVER'] = os.environ.get('SAP_B1_SERVER',
                                             'https://192.168.0.194:50000')
app.config['SAP_B1_USERNAME'] = os.environ.get('SAP_B1_USERNAME', 'manager')
app.config['SAP_B1_PASSWORD'] = os.environ.get('SAP_B1_PASSWORD', '1422')
app.config['SAP_B1_COMPANY_DB'] = os.environ.get('SAP_B1_COMPANY_DB',
                                                 'EINV-TESTDB-LIVE-HUST')

with app.app_context():
    # Import models to create tables
    import models
    import models_extensions
    # Import api_batch_management later to avoid circular imports
# import api_batch_management
    db.create_all()
    logging.info("Database tables created")
    
    # Database schema verification and migrations
    try:
        from sqlalchemy import text, inspect
        
        # Get database dialect
        dialect = db.engine.dialect.name
        logging.info(f"🔧 Database dialect: {dialect}")
        
        # Check if we're using SQLite and add missing columns
        if dialect == 'sqlite':
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
        else:
            logging.info("✓ Using PostgreSQL - schema managed by SQLAlchemy")
            
    except Exception as e:
        logging.warning(f"Schema migration warning: {e}")

    # Create default branch (with error handling for MySQL)
    try:
        from models_extensions import Branch
        default_branch = Branch.query.filter_by(id='BR001').first()
        if not default_branch:
            default_branch = Branch()
            default_branch.id = 'BR001'
            default_branch.name = 'Main Branch'
            default_branch.address = 'Main Office'
            default_branch.is_active = True
            default_branch.is_default = True
            db.session.add(default_branch)
            db.session.commit()
            logging.info("Default branch created")
    except Exception as e:
        logging.warning(f"Could not create/query default branch: {e}")
        # Continue with application startup

    # Create default admin user (with error handling for MySQL)
    try:
        from werkzeug.security import generate_password_hash
        from models import User
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User()
            admin.username = 'admin'
            admin.email = 'admin@company.com'
            admin.password_hash = generate_password_hash('admin123')
            admin.first_name = 'System'
            admin.last_name = 'Administrator'
            admin.role = 'admin'
            admin.branch_id = 'BR001'
            admin.default_branch_id = 'BR001'
            db.session.add(admin)
            db.session.commit()
            logging.info("Default admin user created")
    except Exception as e:
        logging.warning(f"Could not create/query admin user: {e}")
        # Continue with application startup

# Import routes to register them
import routes
