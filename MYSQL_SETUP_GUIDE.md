# MySQL Database Setup Guide for WMS

## Issue Summary
The error you're experiencing is due to MySQL database schema mismatch. The application is trying to query a `branches` table with columns that don't exist in your local MySQL database.

## Quick Fix Steps

### 1. Install Required MySQL Dependencies
```bash
pip install mysql-connector-python pymysql
```

### 2. Update Your .env File
Edit your `.env` file and uncomment the MySQL configuration:

```env
# MySQL (Alternative for local development)
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=wms_db_dev
```

### 3. Run the MySQL Setup Script
```bash
python setup_mysql_local.py
```

This script will:
- Create the `wms_db_dev` database
- Create all required tables with proper schema
- Insert default data (branch, admin user)
- Update your .env file

### 4. Manual Database Setup (Alternative)

If the setup script doesn't work, you can manually create the database:

```sql
-- Connect to MySQL and run these commands
CREATE DATABASE IF NOT EXISTS wms_db_dev;
USE wms_db_dev;

-- Create branches table
CREATE TABLE branches (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),
    manager_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert default branch
INSERT INTO branches (id, name, address, is_active, is_default) 
VALUES ('BR001', 'Main Branch', 'Main Office', TRUE, TRUE);

-- Create users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256),
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    role VARCHAR(20) DEFAULT 'user',
    branch_id VARCHAR(10),
    default_branch_id VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## Common Issues and Solutions

### Issue 1: MySQL Connection Error
**Error**: `Can't connect to MySQL server on 'localhost'`

**Solution**:
1. Ensure MySQL is running: `sudo service mysql start` (Linux) or start MySQL from Services (Windows)
2. Check MySQL credentials in .env file
3. Test connection: `mysql -u root -p`

### Issue 2: Database Not Found
**Error**: `Unknown database 'wms_db_dev'`

**Solution**:
Run the setup script or manually create the database as shown above.

### Issue 3: Table Doesn't Exist
**Error**: `Table 'wms_db_dev.branches' doesn't exist`

**Solution**:
The Flask app will create tables automatically, but if it fails:
1. Run `python setup_mysql_local.py`
2. Or create tables manually using the SQL above

### Issue 4: GRPO Add Item Button Not Working

This is likely due to missing data in the database. After setting up MySQL:

1. Create a test GRPO document
2. Ensure Purchase Order items are loaded from SAP B1
3. Check browser console for JavaScript errors

## Testing Your Setup

After setup, test the application:

1. **Start the application**: `python main.py`
2. **Login**: username=`admin`, password=`admin123`
3. **Create GRPO**: Navigate to GRPO module
4. **Test Add Item**: Click Add buttons on Purchase Order items

## Database Connection Priority

The application tries databases in this order:
1. MySQL (if MYSQL_HOST is configured)
2. PostgreSQL (if DATABASE_URL is configured)
3. SQLite (fallback for development)

## Troubleshooting

### Check Database Connection
```python
# Test MySQL connection
import mysql.connector
try:
    connection = mysql.connector.connect(
        host='localhost',
        database='wms_db_dev',
        user='root',
        password='your_password'
    )
    print("✅ MySQL connection successful")
    connection.close()
except Exception as e:
    print(f"❌ MySQL connection failed: {e}")
```

### Check Tables
```sql
-- Show all tables
SHOW TABLES;

-- Check branches table structure
DESCRIBE branches;

-- Check if default data exists
SELECT * FROM branches;
SELECT * FROM users;
```

## Next Steps

After successful MySQL setup:
1. The GRPO Add Item buttons should work
2. Inventory Transfer edit functionality should show your actual data
3. All database operations will use MySQL instead of fallback data

## Support

If you continue to have issues:
1. Check the application logs
2. Verify MySQL service is running
3. Ensure .env file has correct credentials
4. Run the setup script with MySQL admin privileges