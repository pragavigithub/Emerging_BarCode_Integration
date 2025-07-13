#!/usr/bin/env python3
"""
Quick MySQL Schema Fix
This script adds the missing 'notes' column to fix the immediate error
"""

import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Quick fix for MySQL schema"""
    try:
        import pymysql
        
        # Get connection parameters from environment
        connection = pymysql.connect(
            host=os.environ.get('MYSQL_HOST', 'localhost'),
            port=int(os.environ.get('MYSQL_PORT', 3306)),
            user=os.environ.get('MYSQL_USER', 'root'),
            password=os.environ.get('MYSQL_PASSWORD', ''),
            database=os.environ.get('MYSQL_DATABASE', 'wms_db'),
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Add notes column if it doesn't exist
            try:
                cursor.execute("ALTER TABLE grpo_documents ADD COLUMN notes TEXT NULL")
                logging.info("✓ Added 'notes' column to grpo_documents")
            except pymysql.Error as e:
                if "Duplicate column name" in str(e):
                    logging.info("✓ 'notes' column already exists")
                else:
                    raise
            
            # Add other essential columns
            essential_columns = [
                ("grpo_documents", "qc_notes", "TEXT"),
                ("grpo_documents", "draft_or_post", "VARCHAR(10) DEFAULT 'draft'"),
                ("grpo_items", "generated_barcode", "VARCHAR(100)"),
                ("grpo_items", "barcode_printed", "BOOLEAN DEFAULT FALSE"),
                ("grpo_items", "qc_status", "VARCHAR(20) DEFAULT 'pending'"),
                ("grpo_items", "qc_notes", "TEXT"),
            ]
            
            for table, column, column_type in essential_columns:
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
                    logging.info(f"✓ Added '{column}' column to {table}")
                except pymysql.Error as e:
                    if "Duplicate column name" in str(e):
                        logging.info(f"✓ '{column}' column already exists in {table}")
                    else:
                        logging.warning(f"Could not add {column} to {table}: {e}")
            
            connection.commit()
            logging.info("✓ MySQL schema updated successfully!")
            
    except ImportError:
        logging.error("PyMySQL not installed. Run: pip install pymysql")
        return False
    except Exception as e:
        logging.error(f"Error: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()
    
    return True

if __name__ == "__main__":
    if main():
        print("✓ Schema fix completed. You can now run your application.")
    else:
        print("✗ Schema fix failed. Please check the error messages above.")