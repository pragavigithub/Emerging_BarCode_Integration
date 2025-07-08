#!/usr/bin/env python3
"""
Local Development Setup Script for WMS Application
This script sets up the WMS application for local development.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")

def install_dependencies():
    """Install required Python packages"""
    print("Installing required packages...")
    
    packages = [
        "flask",
        "flask-sqlalchemy", 
        "flask-login",
        "werkzeug",
        "sqlalchemy",
        "psycopg2-binary",
        "requests",
        "gunicorn"
    ]
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package}")
            return False
    
    return True

def create_directories():
    """Create necessary directories"""
    directories = ["instance", "static", "templates", "logs"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")

def create_env_file():
    """Create a .env file with default settings"""
    env_content = """# Local Development Environment Variables
# Database Configuration (leave empty to use SQLite)
DATABASE_URL=

# Flask Configuration
SESSION_SECRET=your-secret-key-change-in-production
FLASK_ENV=development
FLASK_DEBUG=True

# SAP B1 Configuration (optional for local development)
SAP_B1_SERVER=https://your-sap-server:50000
SAP_B1_USERNAME=your-username
SAP_B1_PASSWORD=your-password
SAP_B1_COMPANY_DB=your-company-db
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✓ Created .env file with default settings")
    else:
        print("✓ .env file already exists")

def test_database_connection():
    """Test if the database connection works"""
    try:
        # Import the app to trigger database creation
        from app import app, db
        
        with app.app_context():
            # Test database connection
            db.create_all()
            print("✓ Database connection successful")
            return True
            
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def main():
    """Main setup function"""
    print("=== WMS Local Development Setup ===")
    print()
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    if not install_dependencies():
        print("Setup failed during package installation")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Create .env file
    create_env_file()
    
    # Test database connection
    if not test_database_connection():
        print("Setup completed but database connection test failed")
        print("This might be normal if SAP B1 server is not accessible")
    
    print()
    print("=== Setup Complete ===")
    print("To run the application:")
    print("1. python main.py")
    print("2. Open http://localhost:5000 in your browser")
    print("3. Login with username: admin, password: admin123")
    print()
    print("Note: The application will use SQLite for local development")

if __name__ == "__main__":
    main()