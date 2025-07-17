#!/usr/bin/env python3
"""
Complete Database Migration Script for WMS Application
This script handles database setup and schema migration for all supported databases.
Supports: SQLite, MySQL, PostgreSQL, SQL Server
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError, ProgrammingError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self):
        self.engine = None
        self.db_type = None
        self.connection = None
        
    def detect_and_connect(self):
        """Detect database configuration and establish connection"""
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
            logger.info("Environment variables loaded from .env file")
        except ImportError:
            logger.info("Using system environment variables")
        
        # Try PostgreSQL first (Replit production)
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            try:
                self.engine = create_engine(database_url)
                self.connection = self.engine.connect()
                self.db_type = 'postgresql'
                logger.info("✅ Connected to PostgreSQL database")
                return True
            except Exception as e:
                logger.error(f"PostgreSQL connection failed: {e}")
        
        # Try MySQL
        mysql_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'user': os.getenv('MYSQL_USER'),
            'password': os.getenv('MYSQL_PASSWORD'),
            'database': os.getenv('MYSQL_DATABASE')
        }
        
        if all(mysql_config.values()):
            try:
                from urllib.parse import quote_plus
                encoded_password = quote_plus(mysql_config['password'])
                mysql_url = f"mysql+pymysql://{mysql_config['user']}:{encoded_password}@{mysql_config['host']}/{mysql_config['database']}"
                self.engine = create_engine(mysql_url)
                self.connection = self.engine.connect()
                self.db_type = 'mysql'
                logger.info("✅ Connected to MySQL database")
                return True
            except Exception as e:
                logger.error(f"MySQL connection failed: {e}")
        
        # Try SQL Server
        mssql_config = {
            'server': os.getenv('MSSQL_SERVER'),
            'user': os.getenv('MSSQL_USER'),
            'password': os.getenv('MSSQL_PASSWORD'),
            'database': os.getenv('MSSQL_DATABASE'),
            'driver': os.getenv('MSSQL_DRIVER', 'ODBC Driver 17 for SQL Server')
        }
        
        if mssql_config['server'] and mssql_config['user'] and mssql_config['password'] and mssql_config['database']:
            try:
                from urllib.parse import quote_plus
                encoded_password = quote_plus(mssql_config['password'])
                encoded_driver = quote_plus(mssql_config['driver'])
                mssql_url = f"mssql+pyodbc://{mssql_config['user']}:{encoded_password}@{mssql_config['server']}/{mssql_config['database']}?driver={encoded_driver}"
                self.engine = create_engine(mssql_url)
                self.connection = self.engine.connect()
                self.db_type = 'mssql'
                logger.info("✅ Connected to SQL Server database")
                return True
            except Exception as e:
                logger.error(f"SQL Server connection failed: {e}")
        
        # Fallback to SQLite
        try:
            instance_dir = os.path.join(os.getcwd(), "instance")
            os.makedirs(instance_dir, exist_ok=True)
            db_path = os.path.join(instance_dir, "wms.db")
            sqlite_url = f"sqlite:///{db_path}"
            self.engine = create_engine(sqlite_url)
            self.connection = self.engine.connect()
            self.db_type = 'sqlite'
            logger.info(f"✅ Connected to SQLite database: {db_path}")
            return True
        except Exception as e:
            logger.error(f"SQLite connection failed: {e}")
            return False
    
    def check_table_exists(self, table_name):
        """Check if table exists"""
        try:
            inspector = inspect(self.engine)
            return table_name in inspector.get_table_names()
        except Exception as e:
            logger.error(f"Error checking table {table_name}: {e}")
            return False
    
    def check_column_exists(self, table_name, column_name):
        """Check if column exists in table"""
        try:
            inspector = inspect(self.engine)
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            return column_name in columns
        except Exception as e:
            logger.debug(f"Error checking column {column_name} in {table_name}: {e}")
            return False
    
    def add_column_if_not_exists(self, table_name, column_name, column_definition):
        """Add column if it doesn't exist"""
        if self.check_column_exists(table_name, column_name):
            logger.info(f"✓ Column {column_name} already exists in {table_name}")
            return True
        
        try:
            if self.db_type == 'mysql':
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
            elif self.db_type == 'postgresql':
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
            elif self.db_type == 'mssql':
                sql = f"ALTER TABLE {table_name} ADD {column_name} {column_definition}"
            else:  # SQLite
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
            
            self.connection.execute(text(sql))
            self.connection.commit()
            logger.info(f"✅ Added column {column_name} to {table_name}")
            return True
        except Exception as e:
            logger.error(f"Error adding column {column_name} to {table_name}: {e}")
            return False
    
    def create_table_if_not_exists(self, table_name, create_sql):
        """Create table if it doesn't exist"""
        if self.check_table_exists(table_name):
            logger.info(f"✓ Table {table_name} already exists")
            return True
        
        try:
            self.connection.execute(text(create_sql))
            self.connection.commit()
            logger.info(f"✅ Created table {table_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating table {table_name}: {e}")
            return False
    
    def get_create_table_sql(self, table_name):
        """Get database-specific CREATE TABLE SQL"""
        
        # Common column type mappings
        if self.db_type == 'mysql':
            integer_type = "INT"
            string_type = "VARCHAR"
            text_type = "TEXT"
            datetime_type = "DATETIME"
            boolean_type = "BOOLEAN"
            float_type = "FLOAT"
        elif self.db_type == 'postgresql':
            integer_type = "INTEGER"
            string_type = "VARCHAR"
            text_type = "TEXT"
            datetime_type = "TIMESTAMP"
            boolean_type = "BOOLEAN"
            float_type = "REAL"
        elif self.db_type == 'mssql':
            integer_type = "INT"
            string_type = "NVARCHAR"
            text_type = "NTEXT"
            datetime_type = "DATETIME2"
            boolean_type = "BIT"
            float_type = "FLOAT"
        else:  # SQLite
            integer_type = "INTEGER"
            string_type = "VARCHAR"
            text_type = "TEXT"
            datetime_type = "DATETIME"
            boolean_type = "BOOLEAN"
            float_type = "REAL"
        
        # Table creation SQL templates
        tables = {
            'inventory_transfers': f"""
                CREATE TABLE inventory_transfers (
                    id {integer_type} PRIMARY KEY {'AUTO_INCREMENT' if self.db_type == 'mysql' else ''},
                    transfer_request_number {string_type}(20) NOT NULL,
                    sap_document_number {string_type}(20),
                    status {string_type}(20) DEFAULT 'draft',
                    user_id {integer_type} NOT NULL,
                    qc_approver_id {integer_type},
                    qc_approved_at {datetime_type},
                    qc_notes {text_type},
                    from_warehouse {string_type}(20),
                    to_warehouse {string_type}(20),
                    created_at {datetime_type} DEFAULT {'NOW()' if self.db_type == 'mysql' else 'CURRENT_TIMESTAMP'},
                    updated_at {datetime_type} DEFAULT {'NOW()' if self.db_type == 'mysql' else 'CURRENT_TIMESTAMP'}
                )
            """,
            'inventory_transfer_items': f"""
                CREATE TABLE inventory_transfer_items (
                    id {integer_type} PRIMARY KEY {'AUTO_INCREMENT' if self.db_type == 'mysql' else ''},
                    inventory_transfer_id {integer_type} NOT NULL,
                    item_code {string_type}(50) NOT NULL,
                    item_name {string_type}(200) NOT NULL,
                    quantity {float_type} NOT NULL,
                    unit_of_measure {string_type}(10) NOT NULL,
                    from_bin {string_type}(20) NOT NULL,
                    to_bin {string_type}(20) NOT NULL,
                    batch_number {string_type}(50),
                    qc_status {string_type}(20) DEFAULT 'pending',
                    qc_notes {text_type},
                    created_at {datetime_type} DEFAULT {'NOW()' if self.db_type == 'mysql' else 'CURRENT_TIMESTAMP'}
                )
            """
        }
        
        return tables.get(table_name, "")
    
    def migrate_inventory_transfers(self):
        """Migrate inventory_transfers table and add missing columns"""
        logger.info("🔧 Migrating inventory_transfers table...")
        
        # Create table if it doesn't exist
        create_sql = self.get_create_table_sql('inventory_transfers')
        if create_sql:
            self.create_table_if_not_exists('inventory_transfers', create_sql)
        
        # Add missing columns
        columns_to_add = [
            ('qc_approver_id', 'INTEGER'),
            ('qc_approved_at', 'DATETIME'),
            ('qc_notes', 'TEXT'),
            ('from_warehouse', 'VARCHAR(20)'),
            ('to_warehouse', 'VARCHAR(20)')
        ]
        
        for column_name, column_type in columns_to_add:
            self.add_column_if_not_exists('inventory_transfers', column_name, column_type)
    
    def migrate_inventory_transfer_items(self):
        """Migrate inventory_transfer_items table and add missing columns"""
        logger.info("🔧 Migrating inventory_transfer_items table...")
        
        # Create table if it doesn't exist
        create_sql = self.get_create_table_sql('inventory_transfer_items')
        if create_sql:
            self.create_table_if_not_exists('inventory_transfer_items', create_sql)
        
        # Add missing columns
        columns_to_add = [
            ('qc_status', 'VARCHAR(20) DEFAULT "pending"'),
            ('qc_notes', 'TEXT')
        ]
        
        for column_name, column_type in columns_to_add:
            self.add_column_if_not_exists('inventory_transfer_items', column_name, column_type)
    
    def run_migration(self):
        """Run complete database migration"""
        logger.info("🚀 Starting database migration...")
        
        if not self.detect_and_connect():
            logger.error("❌ Failed to connect to any database")
            return False
        
        try:
            # Migrate tables
            self.migrate_inventory_transfers()
            self.migrate_inventory_transfer_items()
            
            logger.info("✅ Database migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
        finally:
            if self.connection:
                self.connection.close()

def main():
    """Main migration function"""
    migrator = DatabaseMigrator()
    success = migrator.run_migration()
    
    if success:
        logger.info("🎉 Migration completed successfully!")
        print("\n" + "="*60)
        print("✅ DATABASE MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("Your database schema has been updated.")
        print("You can now restart your application.")
        print("="*60)
        return 0
    else:
        logger.error("❌ Migration failed!")
        print("\n" + "="*60)
        print("❌ DATABASE MIGRATION FAILED!")
        print("="*60)
        print("Please check the error messages above and fix any issues.")
        print("="*60)
        return 1

if __name__ == "__main__":
    exit(main())