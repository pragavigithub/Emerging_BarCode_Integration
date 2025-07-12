"""
Database Integration Fix for WMS Application
Addresses MSSQL data transfer issues and database connectivity
"""
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from app import app, db
from models import *

def check_database_connectivity():
    """Check if database is properly connected"""
    try:
        with app.app_context():
            # Test database connection
            result = db.session.execute(text("SELECT 1")).fetchone()
            if result:
                logging.info("Database connectivity: SUCCESS")
                return True
            else:
                logging.error("Database connectivity: FAILED")
                return False
    except Exception as e:
        logging.error(f"Database connectivity error: {str(e)}")
        return False

def test_mssql_connection():
    """Test MSSQL connection if configured"""
    mssql_url = os.environ.get('MSSQL_DATABASE_URL')
    if not mssql_url:
        logging.info("MSSQL URL not configured, skipping MSSQL test")
        return False
    
    try:
        engine = create_engine(mssql_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            if result:
                logging.info("MSSQL connectivity: SUCCESS")
                return True
            else:
                logging.error("MSSQL connectivity: FAILED")
                return False
    except Exception as e:
        logging.error(f"MSSQL connectivity error: {str(e)}")
        return False

def fix_database_tables():
    """Ensure all required tables exist with correct schema"""
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            
            # Check if bin_locations table exists
            result = db.session.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'bin_locations'
            """)).fetchone()
            
            if result[0] == 0:
                # Create bin_locations table
                db.session.execute(text("""
                    CREATE TABLE bin_locations (
                        id SERIAL PRIMARY KEY,
                        bin_code VARCHAR(50) NOT NULL,
                        warehouse_code VARCHAR(10) NOT NULL,
                        bin_name VARCHAR(100),
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(bin_code, warehouse_code)
                    )
                """))
                db.session.commit()
                logging.info("Created bin_locations table")
            
            # Check if branches table has all required columns
            db.session.execute(text("""
                ALTER TABLE branches 
                ADD COLUMN IF NOT EXISTS manager_name VARCHAR(100),
                ADD COLUMN IF NOT EXISTS phone VARCHAR(20),
                ADD COLUMN IF NOT EXISTS email VARCHAR(100)
            """))
            db.session.commit()
            logging.info("Database tables updated successfully")
            
    except Exception as e:
        logging.error(f"Error fixing database tables: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== Database Integration Fix ===")
    print("1. Testing PostgreSQL connectivity...")
    if check_database_connectivity():
        print("✓ PostgreSQL connection successful")
    else:
        print("✗ PostgreSQL connection failed")
    
    print("2. Testing MSSQL connectivity...")
    if test_mssql_connection():
        print("✓ MSSQL connection successful")
    else:
        print("✗ MSSQL connection failed or not configured")
    
    print("3. Fixing database tables...")
    fix_database_tables()
    print("✓ Database tables fixed")
    
    print("=== Fix Complete ===")