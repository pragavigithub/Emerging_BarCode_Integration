#!/usr/bin/env python3
"""
Direct MySQL Database Migration Script
This script connects directly to MySQL and adds the missing columns
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Main migration function for MySQL"""
    try:
        # Import PyMySQL
        import pymysql
        
        # MySQL connection parameters
        connection_params = {
            'host': os.environ.get('MYSQL_HOST', 'localhost'),
            'port': int(os.environ.get('MYSQL_PORT', 3306)),
            'user': os.environ.get('MYSQL_USER', 'root'),
            'password': os.environ.get('MYSQL_PASSWORD', ''),
            'database': os.environ.get('MYSQL_DATABASE', 'wms_db'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
        
        logging.info("Connecting to MySQL database...")
        connection = pymysql.connect(**connection_params)
        
        with connection.cursor() as cursor:
            # Check if notes column exists
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'grpo_documents' 
                AND COLUMN_NAME = 'notes'
            """, (connection_params['database'],))
            
            result = cursor.fetchone()
            
            if result['count'] == 0:
                logging.info("Adding 'notes' column to grpo_documents table...")
                cursor.execute("ALTER TABLE grpo_documents ADD COLUMN notes TEXT NULL")
                connection.commit()
                logging.info("✓ Successfully added 'notes' column")
            else:
                logging.info("✓ 'notes' column already exists")
            
            # Check and add other missing columns
            missing_columns = [
                ('grpo_documents', 'qc_notes', 'TEXT'),
                ('grpo_documents', 'draft_or_post', "VARCHAR(10) DEFAULT 'draft'"),
                ('grpo_items', 'generated_barcode', 'VARCHAR(100)'),
                ('grpo_items', 'barcode_printed', 'BOOLEAN DEFAULT FALSE'),
                ('grpo_items', 'qc_status', "VARCHAR(20) DEFAULT 'pending'"),
                ('grpo_items', 'qc_notes', 'TEXT'),
                ('users', 'branch_id', 'VARCHAR(10)'),
                ('users', 'branch_name', 'VARCHAR(100)'),
                ('users', 'default_branch_id', 'VARCHAR(10)'),
                ('users', 'must_change_password', 'BOOLEAN DEFAULT FALSE'),
                ('users', 'last_login', 'DATETIME'),
                ('users', 'permissions', 'TEXT'),
            ]
            
            for table_name, column_name, column_type in missing_columns:
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = %s 
                    AND TABLE_NAME = %s 
                    AND COLUMN_NAME = %s
                """, (connection_params['database'], table_name, column_name))
                
                result = cursor.fetchone()
                
                if result['count'] == 0:
                    logging.info(f"Adding '{column_name}' column to {table_name} table...")
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                    cursor.execute(sql)
                    connection.commit()
                    logging.info(f"✓ Successfully added '{column_name}' column")
                else:
                    logging.info(f"✓ '{column_name}' column already exists in {table_name}")
            
            # Create barcode_labels table if it doesn't exist
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'barcode_labels'
            """, (connection_params['database'],))
            
            result = cursor.fetchone()
            
            if result['count'] == 0:
                logging.info("Creating barcode_labels table...")
                cursor.execute("""
                    CREATE TABLE barcode_labels (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        item_code VARCHAR(50) NOT NULL,
                        barcode VARCHAR(100) NOT NULL,
                        label_format VARCHAR(20) NOT NULL,
                        print_count INT DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_printed DATETIME NULL
                    )
                """)
                connection.commit()
                logging.info("✓ Successfully created barcode_labels table")
            else:
                logging.info("✓ barcode_labels table already exists")
            
            # Create branches table if it doesn't exist
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'branches'
            """, (connection_params['database'],))
            
            result = cursor.fetchone()
            
            if result['count'] == 0:
                logging.info("Creating branches table...")
                cursor.execute("""
                    CREATE TABLE branches (
                        id VARCHAR(10) PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        address TEXT,
                        phone VARCHAR(20),
                        email VARCHAR(100),
                        manager_name VARCHAR(100),
                        is_default BOOLEAN DEFAULT FALSE,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert default branch
                cursor.execute("""
                    INSERT INTO branches (id, name, is_default, is_active) 
                    VALUES ('HQ001', 'Head Office', TRUE, TRUE)
                """)
                connection.commit()
                logging.info("✓ Successfully created branches table with default branch")
            else:
                logging.info("✓ branches table already exists")
        
        logging.info("=" * 60)
        logging.info("✓ MySQL DATABASE MIGRATION COMPLETED SUCCESSFULLY!")
        logging.info("=" * 60)
        logging.info("You can now run your application without database errors.")
        
    except ImportError:
        logging.error("PyMySQL is not installed. Please install it with: pip install pymysql")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Migration failed: {e}")
        sys.exit(1)
    finally:
        if 'connection' in locals():
            connection.close()
            logging.info("Database connection closed.")

if __name__ == "__main__":
    main()