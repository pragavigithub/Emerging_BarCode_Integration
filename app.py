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

# Configure database - use PostgreSQL in Replit environment
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
logging.info("Using PostgreSQL database")
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
