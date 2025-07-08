"""
MS SQL Server Database Setup Script for WMS Application
Run this script to create the database and all required tables for your local environment.
"""

import os
import pyodbc
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

def get_connection_params():
    """Get connection parameters from environment or user input"""
    server = os.environ.get('MSSQL_SERVER') or input("Enter SQL Server name (default: localhost): ") or "localhost"
    database = os.environ.get('MSSQL_DATABASE') or input("Enter database name (default: WMS_DB): ") or "WMS_DB"
    username = os.environ.get('MSSQL_USERNAME') or input("Enter username: ")
    password = os.environ.get('MSSQL_PASSWORD') or input("Enter password: ")
    
    return server, database, username, password

def create_database(server, username, password, database_name):
    """Create the database if it doesn't exist"""
    try:
        # Connect to master database to create new database
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE=master;UID={username};PWD={password};TrustServerCertificate=yes"
        conn = pyodbc.connect(conn_str)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT name FROM sys.databases WHERE name = ?", database_name)
        if cursor.fetchone():
            logging.info(f"Database {database_name} already exists")
        else:
            # Create database
            cursor.execute(f"CREATE DATABASE {database_name}")
            logging.info(f"Database {database_name} created successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logging.error(f"Error creating database: {e}")
        return False

def create_tables(server, database, username, password):
    """Create all required tables"""
    try:
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users')
            CREATE TABLE users (
                id INT IDENTITY(1,1) PRIMARY KEY,
                username NVARCHAR(80) UNIQUE NOT NULL,
                email NVARCHAR(120) UNIQUE NOT NULL,
                password_hash NVARCHAR(256) NOT NULL,
                first_name NVARCHAR(80) NOT NULL,
                last_name NVARCHAR(80) NOT NULL,
                role NVARCHAR(20) NOT NULL DEFAULT 'user',
                branch_id NVARCHAR(10) NULL,
                branch_name NVARCHAR(100) NULL,
                default_branch_id NVARCHAR(10) NULL,
                is_active BIT DEFAULT 1,
                must_change_password BIT DEFAULT 0,
                last_login DATETIME2 NULL,
                permissions NTEXT NULL,
                created_at DATETIME2 DEFAULT GETDATE(),
                updated_at DATETIME2 DEFAULT GETDATE()
            )
        """)
        
        # Branches table
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'branches')
            CREATE TABLE branches (
                id NVARCHAR(10) PRIMARY KEY,
                name NVARCHAR(100) NOT NULL,
                address NTEXT NULL,
                phone NVARCHAR(20) NULL,
                email NVARCHAR(100) NULL,
                manager_name NVARCHAR(100) NULL,
                is_active BIT DEFAULT 1,
                is_default BIT DEFAULT 0,
                created_at DATETIME2 DEFAULT GETDATE(),
                updated_at DATETIME2 DEFAULT GETDATE()
            )
        """)
        
        # GRPO Documents table
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'grpo_documents')
            CREATE TABLE grpo_documents (
                id INT IDENTITY(1,1) PRIMARY KEY,
                po_number NVARCHAR(20) NOT NULL,
                sap_document_number NVARCHAR(20) NULL,
                supplier_code NVARCHAR(50) NULL,
                supplier_name NVARCHAR(200) NULL,
                po_date DATETIME2 NULL,
                po_total FLOAT NULL,
                status NVARCHAR(20) DEFAULT 'draft',
                user_id INT NOT NULL,
                qc_user_id INT NULL,
                qc_notes NTEXT NULL,
                draft_or_post NVARCHAR(10) DEFAULT 'draft',
                created_at DATETIME2 DEFAULT GETDATE(),
                updated_at DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (qc_user_id) REFERENCES users(id)
            )
        """)
        
        # GRPO Items table
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'grpo_items')
            CREATE TABLE grpo_items (
                id INT IDENTITY(1,1) PRIMARY KEY,
                grpo_document_id INT NOT NULL,
                po_line_number INT NULL,
                item_code NVARCHAR(50) NOT NULL,
                item_name NVARCHAR(200) NOT NULL,
                po_quantity FLOAT NULL,
                open_quantity FLOAT NULL,
                received_quantity FLOAT NOT NULL,
                unit_of_measure NVARCHAR(10) NOT NULL,
                unit_price FLOAT NULL,
                bin_location NVARCHAR(20) NOT NULL,
                batch_number NVARCHAR(50) NULL,
                expiration_date DATETIME2 NULL,
                supplier_barcode NVARCHAR(100) NULL,
                generated_barcode NVARCHAR(100) NULL,
                barcode_printed BIT DEFAULT 0,
                qc_status NVARCHAR(20) DEFAULT 'pending',
                qc_notes NTEXT NULL,
                created_at DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (grpo_document_id) REFERENCES grpo_documents(id)
            )
        """)
        
        # Additional tables for complete functionality
        tables_to_create = [
            """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'inventory_transfers')
            CREATE TABLE inventory_transfers (
                id INT IDENTITY(1,1) PRIMARY KEY,
                transfer_request_number NVARCHAR(20) NOT NULL,
                sap_document_number NVARCHAR(20) NULL,
                status NVARCHAR(20) DEFAULT 'draft',
                user_id INT NOT NULL,
                created_at DATETIME2 DEFAULT GETDATE(),
                updated_at DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """,
            """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'inventory_transfer_items')
            CREATE TABLE inventory_transfer_items (
                id INT IDENTITY(1,1) PRIMARY KEY,
                inventory_transfer_id INT NOT NULL,
                item_code NVARCHAR(50) NOT NULL,
                item_name NVARCHAR(200) NOT NULL,
                quantity FLOAT NOT NULL,
                unit_of_measure NVARCHAR(10) NOT NULL,
                from_bin NVARCHAR(20) NOT NULL,
                to_bin NVARCHAR(20) NOT NULL,
                batch_number NVARCHAR(50) NULL,
                created_at DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (inventory_transfer_id) REFERENCES inventory_transfers(id)
            )
            """,
            """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'pick_lists')
            CREATE TABLE pick_lists (
                id INT IDENTITY(1,1) PRIMARY KEY,
                sales_order_number NVARCHAR(20) NOT NULL,
                pick_list_number NVARCHAR(20) NOT NULL,
                status NVARCHAR(20) DEFAULT 'pending',
                user_id INT NOT NULL,
                approver_id INT NULL,
                created_at DATETIME2 DEFAULT GETDATE(),
                updated_at DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (approver_id) REFERENCES users(id)
            )
            """,
            """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'pick_list_items')
            CREATE TABLE pick_list_items (
                id INT IDENTITY(1,1) PRIMARY KEY,
                pick_list_id INT NOT NULL,
                item_code NVARCHAR(50) NOT NULL,
                item_name NVARCHAR(200) NOT NULL,
                quantity FLOAT NOT NULL,
                picked_quantity FLOAT DEFAULT 0,
                unit_of_measure NVARCHAR(10) NOT NULL,
                bin_location NVARCHAR(20) NOT NULL,
                batch_number NVARCHAR(50) NULL,
                created_at DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (pick_list_id) REFERENCES pick_lists(id)
            )
            """,
            """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'inventory_counts')
            CREATE TABLE inventory_counts (
                id INT IDENTITY(1,1) PRIMARY KEY,
                count_number NVARCHAR(20) NOT NULL,
                warehouse_code NVARCHAR(10) NOT NULL,
                bin_location NVARCHAR(20) NOT NULL,
                status NVARCHAR(20) DEFAULT 'assigned',
                user_id INT NOT NULL,
                created_at DATETIME2 DEFAULT GETDATE(),
                updated_at DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """,
            """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'inventory_count_items')
            CREATE TABLE inventory_count_items (
                id INT IDENTITY(1,1) PRIMARY KEY,
                inventory_count_id INT NOT NULL,
                item_code NVARCHAR(50) NOT NULL,
                item_name NVARCHAR(200) NOT NULL,
                system_quantity FLOAT NOT NULL,
                counted_quantity FLOAT NOT NULL,
                variance FLOAT NOT NULL,
                unit_of_measure NVARCHAR(10) NOT NULL,
                batch_number NVARCHAR(50) NULL,
                created_at DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (inventory_count_id) REFERENCES inventory_counts(id)
            )
            """,
            """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'barcode_labels')
            CREATE TABLE barcode_labels (
                id INT IDENTITY(1,1) PRIMARY KEY,
                item_code NVARCHAR(50) NOT NULL,
                barcode NVARCHAR(100) NOT NULL,
                label_format NVARCHAR(20) NOT NULL,
                print_count INT DEFAULT 0,
                created_at DATETIME2 DEFAULT GETDATE(),
                last_printed DATETIME2 NULL
            )
            """,
            """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'user_sessions')
            CREATE TABLE user_sessions (
                id INT IDENTITY(1,1) PRIMARY KEY,
                user_id INT NOT NULL,
                session_token NVARCHAR(256) NOT NULL,
                branch_id NVARCHAR(10) NULL,
                login_time DATETIME2 DEFAULT GETDATE(),
                logout_time DATETIME2 NULL,
                ip_address NVARCHAR(45) NULL,
                user_agent NTEXT NULL,
                is_active BIT DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """,
            """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'password_reset_tokens')
            CREATE TABLE password_reset_tokens (
                id INT IDENTITY(1,1) PRIMARY KEY,
                user_id INT NOT NULL,
                token NVARCHAR(256) UNIQUE NOT NULL,
                expires_at DATETIME2 NOT NULL,
                used BIT DEFAULT 0,
                created_by INT NULL,
                created_at DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
            """
        ]
        
        for table_sql in tables_to_create:
            cursor.execute(table_sql)
        
        # Insert default data
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM branches WHERE id = 'HQ001')
            INSERT INTO branches (id, name, is_default, is_active) 
            VALUES ('HQ001', 'Head Office', 1, 1)
        """)
        
        # Check if admin user exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            # Create default admin user (you'll need to hash the password properly in your app)
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, first_name, last_name, role, default_branch_id)
                VALUES ('admin', 'admin@company.com', '$2b$12$LQv3c1yqBTVHbr/j2J2U2eLYF4.h1OJpWnMdJcCQPmZQyEHfLQjHa', 'System', 'Administrator', 'admin', 'HQ001')
            """)
            logging.info("Default admin user created (username: admin, password: admin123)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logging.info("All tables created successfully!")
        return True
        
    except Exception as e:
        logging.error(f"Error creating tables: {e}")
        return False

def create_env_file():
    """Create a .env file with the configuration"""
    server, database, username, password = get_connection_params()
    
    env_content = f"""# Database Configuration for MS SQL Server
MSSQL_SERVER={server}
MSSQL_DATABASE={database}
MSSQL_USERNAME={username}
MSSQL_PASSWORD={password}

# Session Secret (change this in production)
SESSION_SECRET=your-secret-key-change-in-production

# SAP B1 Configuration (update these for your environment)
SAP_B1_SERVER=https://your-sap-server:50000
SAP_B1_USERNAME=your_sap_username
SAP_B1_PASSWORD=your_sap_password
SAP_B1_COMPANY_DB=your_company_database
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    logging.info(".env file created successfully")
    return server, database, username, password

def main():
    """Main setup function"""
    print("=== WMS Database Setup for MS SQL Server ===")
    print()
    
    try:
        # Get connection parameters
        server, database, username, password = create_env_file()
        
        # Create database
        if create_database(server, username, password, database):
            # Create tables
            if create_tables(server, database, username, password):
                print()
                print("✅ Database setup completed successfully!")
                print()
                print("Next steps:")
                print("1. Run: python main.py")
                print("2. Login with username: admin, password: admin123")
                print("3. Create additional users and configure permissions")
                print()
            else:
                print("❌ Failed to create tables")
        else:
            print("❌ Failed to create database")
            
    except Exception as e:
        logging.error(f"Setup failed: {e}")
        print(f"❌ Setup failed: {e}")

if __name__ == "__main__":
    main()