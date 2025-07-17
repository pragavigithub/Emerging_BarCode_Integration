# MySQL Database Migration Guide

## Overview
This guide helps you migrate your WMS application from SQLite to MySQL for better performance and enterprise-level features.

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)
```bash
# Run the MySQL setup script
python setup_mysql_local.py

# Run the migration
python migrate_inventory_transfers.py
```

### Option 2: Manual Setup

#### Step 1: Install MySQL Python Packages
```bash
pip install pymysql mysql-connector-python
```

#### Step 2: Create MySQL Database
```sql
-- Login to MySQL as root
mysql -u root -p

-- Create database
CREATE DATABASE warehouse_wms;

-- Create user (optional)
CREATE USER 'wms_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON warehouse_wms.* TO 'wms_user'@'localhost';
FLUSH PRIVILEGES;
```

#### Step 3: Configure Environment Variables
Create or update your `.env` file:
```bash
# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=wms_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=warehouse_wms

# Flask Session Secret
SESSION_SECRET=your-secret-key-here

# SAP B1 Configuration (optional)
SAP_B1_SERVER=https://your-sap-server:50000
SAP_B1_USERNAME=your-sap-username
SAP_B1_PASSWORD=your-sap-password
SAP_B1_COMPANY_DB=your-company-database
```

#### Step 4: Run Migration
```bash
python migrate_inventory_transfers.py
```

## 📊 Database Priority System

The application automatically detects and uses databases in this order:

1. **MySQL** - If `MYSQL_*` environment variables are set
2. **PostgreSQL** - If `DATABASE_URL` is set (Replit environment)
3. **SQLite** - Fallback for local development

## 🔄 Migration Features

### What the Migration Does:
- Detects your current database type (MySQL/PostgreSQL/SQLite)
- Adds missing QC approval columns to `inventory_transfers` table
- Adds QC workflow columns to `inventory_transfer_items` table
- Creates tables if they don't exist
- Handles different SQL syntax for each database type

### Added Columns:
**inventory_transfers table:**
- `qc_approver_id` (INT/INTEGER)
- `qc_approved_at` (DATETIME/TIMESTAMP)
- `qc_notes` (TEXT)
- `from_warehouse` (VARCHAR(20))
- `to_warehouse` (VARCHAR(20))

**inventory_transfer_items table:**
- `qc_status` (VARCHAR(20) DEFAULT 'pending')
- `qc_notes` (TEXT)

## 🛠️ Troubleshooting

### MySQL Connection Issues
```bash
# Check MySQL service status
sudo systemctl status mysql

# Start MySQL service
sudo systemctl start mysql

# Connect to MySQL
mysql -u root -p
```

### Permission Issues
```sql
-- Grant all privileges to user
GRANT ALL PRIVILEGES ON warehouse_wms.* TO 'wms_user'@'localhost';
FLUSH PRIVILEGES;
```

### Port Issues
```bash
# Check if MySQL is running on port 3306
netstat -an | grep 3306

# Or check MySQL configuration
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

## 🔧 Fix Scripts Available

### For Database Schema Issues:
1. **migrate_inventory_transfers.py** - Complete migration with table creation
2. **fix_inventory_transfer_schema.py** - Quick column addition fix
3. **run_database_fix.bat** - Interactive fix menu (Windows)

### For MySQL Setup:
1. **setup_mysql_local.py** - Interactive MySQL configuration
2. **install_mysql_local.py** - Package installation and basic setup

## 🎯 Benefits of MySQL Migration

### Performance Benefits:
- Better concurrent access handling
- Improved query performance for large datasets
- Professional database engine with optimization features

### Enterprise Features:
- Better backup and recovery options
- User management and permissions
- Replication and high availability support
- Better integration with enterprise tools

### Development Benefits:
- More compatible with production environments
- Better debugging and monitoring tools
- Support for stored procedures and functions
- More robust transaction handling

## 📋 Post-Migration Verification

After migration, verify the setup:

1. **Check Database Connection:**
   ```bash
   python -c "from migrate_inventory_transfers import get_database_connection; print(get_database_connection())"
   ```

2. **Verify Tables:**
   ```sql
   USE warehouse_wms;
   SHOW TABLES;
   DESCRIBE inventory_transfers;
   DESCRIBE inventory_transfer_items;
   ```

3. **Test Application:**
   ```bash
   python app.py
   # Access inventory transfer module
   # Create a test transfer
   # Submit for QC approval
   ```

## 🆘 Support

If you encounter issues:
1. Check MySQL service is running
2. Verify database credentials
3. Run the migration script again
4. Check application logs for detailed error messages

The migration scripts are designed to be safe and can be run multiple times without issues.