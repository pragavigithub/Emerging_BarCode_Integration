#!/usr/bin/env python3
"""
Local installation script for WMS Application
Run this script to set up the WMS application on your local machine
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ Successfully installed {package}")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install {package}: {e}")
        return False
    return True

def create_env_file():
    """Create a .env file with default settings"""
    env_content = """# WMS Application Environment Variables
SESSION_SECRET=dev-secret-key-change-in-production
DATABASE_URL=sqlite:///wms.db
SAP_B1_SERVER=https://your-sap-server:50000
SAP_B1_USERNAME=your-sap-username
SAP_B1_PASSWORD=your-sap-password
SAP_B1_COMPANY_DB=your-company-database
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✓ Created .env file with default settings")
    else:
        print("✓ .env file already exists")

def main():
    """Main installation process"""
    print("WMS Application Local Setup")
    print("=" * 30)
    
    # Required packages
    packages = [
        "Flask==3.0.0",
        "Flask-SQLAlchemy==3.1.1", 
        "Flask-Login==0.6.3",
        "Werkzeug==3.0.1",
        "Jinja2==3.1.2",
        "SQLAlchemy==2.0.23",
        "email-validator==2.1.0",
        "requests==2.31.0",
        "gunicorn==21.2.0",
        "psycopg2-binary==2.9.9",
        "PyJWT==2.8.0"
    ]
    
    print("Installing required packages...")
    failed_packages = []
    
    for package in packages:
        if not install_package(package):
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n✗ Failed to install: {', '.join(failed_packages)}")
        print("Please install these packages manually.")
    else:
        print("\n✓ All packages installed successfully!")
    
    # Create environment file
    create_env_file()
    
    print("\nSetup complete!")
    print("\nTo run the application:")
    print("1. Update the .env file with your actual SAP B1 credentials")
    print("2. Run: python main.py")
    print("3. Open your browser to: http://localhost:5000")
    print("4. Login with: admin / admin123")

if __name__ == "__main__":
    main()