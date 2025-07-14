#!/usr/bin/env python3
"""
Initialize Local Database
Creates the database tables and adds missing columns for local development.
"""
import os
import sys
import sqlite3
from pathlib import Path

# Set environment to use SQLite for local development
os.environ['DATABASE_URL'] = 'sqlite:///instance/database.db'

def create_database_tables():
    """Create database tables using Flask app"""
    try:
        # Import and initialize the Flask app
        from app import app, db
        
        with app.app_context():
            # Import all models to ensure they're registered
            import models
            import models_extensions
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Add missing columns if they don't exist
            from sqlalchemy import text
            
            try:
                # Try to add notes column if it doesn't exist
                db.session.execute(text("ALTER TABLE grpo_documents ADD COLUMN notes TEXT"))
                db.session.commit()
                print("✅ Added 'notes' column to grpo_documents")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✓ 'notes' column already exists")
                else:
                    print(f"Note: {e}")
            
            try:
                # Try to add serial_number column if it doesn't exist
                db.session.execute(text("ALTER TABLE grpo_items ADD COLUMN serial_number VARCHAR(50)"))
                db.session.commit()
                print("✅ Added 'serial_number' column to grpo_items")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✓ 'serial_number' column already exists")
                else:
                    print(f"Note: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def create_default_user():
    """Create default admin user if none exists"""
    try:
        from app import app, db
        from models import User
        from werkzeug.security import generate_password_hash
        
        with app.app_context():
            # Check if admin user exists
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                # Create default admin user
                admin_user = User(
                    username='admin',
                    email='admin@wms.local',
                    password_hash=generate_password_hash('admin123'),
                    role='admin',
                    branch='MAIN'
                )
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Created default admin user (admin/admin123)")
            else:
                print("✓ Admin user already exists")
                
    except Exception as e:
        print(f"❌ Error creating default user: {e}")

def main():
    """Main function"""
    print("🔧 Local Database Initialization")
    print("=" * 50)
    
    # Ensure instance directory exists
    os.makedirs('instance', exist_ok=True)
    
    if create_database_tables():
        create_default_user()
        print("\n✅ Local database initialization completed!")
        print("You can now run your WMS application locally.")
        print("\nDefault login:")
        print("Username: admin")
        print("Password: admin123")
    else:
        print("\n❌ Database initialization failed!")

if __name__ == "__main__":
    main()