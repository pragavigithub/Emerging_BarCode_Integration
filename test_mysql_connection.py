#!/usr/bin/env python3
import pymysql
import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_pymysql():
    try:
        connection = pymysql.connect(
            host=os.environ.get('MYSQL_HOST', 'localhost'),
            port=int(os.environ.get('MYSQL_PORT', 3306)),
            user=os.environ.get('MYSQL_USERNAME', 'root'),
            password=os.environ.get('MYSQL_PASSWORD', ''),
            database=os.environ.get('MYSQL_DATABASE', 'wms_db'),
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            result = cursor.fetchone()
            print(f"SUCCESS: PyMySQL connection - MySQL version: {result[0]}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"FAILED: PyMySQL connection - {e}")
        return False

def test_mysql_connector():
    try:
        connection = mysql.connector.connect(
            host=os.environ.get('MYSQL_HOST', 'localhost'),
            port=int(os.environ.get('MYSQL_PORT', 3306)),
            user=os.environ.get('MYSQL_USERNAME', 'root'),
            password=os.environ.get('MYSQL_PASSWORD', ''),
            database=os.environ.get('MYSQL_DATABASE', 'wms_db'),
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        result = cursor.fetchone()
        print(f"SUCCESS: MySQL Connector - MySQL version: {result[0]}")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"FAILED: MySQL Connector - {e}")
        return False

def main():
    print("Testing MySQL Connection...")
    print("")
    
    # Test both connectors
    pymysql_ok = test_pymysql()
    connector_ok = test_mysql_connector()
    
    if pymysql_ok or connector_ok:
        print("")
        print("MySQL connection successful! You can now run:")
        print("python main.py")
    else:
        print("")
        print("MySQL connection failed. Please check:")
        print("1. MySQL server is running")
        print("2. Database 'wms_db' exists")
        print("3. Username and password are correct")
        print("4. Host and port are accessible")

if __name__ == "__main__":
    main()
