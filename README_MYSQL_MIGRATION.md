# MySQL Database Migration Guide for WMS Application

## Overview
This guide provides instructions for migrating the WMS application database schema when using MySQL as the primary database.

## Prerequisites
- MySQL 5.7 or higher installed
- Python with PyMySQL package installed
- Proper MySQL environment variables configured

## Environment Variables for MySQL
Set the following environment variables for MySQL connection:

```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=wms_db
```

## Migration Scripts

### 1. Primary Migration Script
```bash
python migrate_database_mysql.py
```

This script automatically:
- Detects the database type (MySQL, PostgreSQL, or SQLite)
- Adds missing columns to existing tables
- Creates missing tables if they don't exist
- Handles database-specific SQL syntax differences

### 2. Database-Specific Features

#### MySQL Syntax Handled:
- `AUTO_INCREMENT` for primary keys
- `DATETIME` for timestamp columns
- `BOOLEAN` data types
- `CURRENT_TIMESTAMP` default values
- `VARCHAR` length specifications

#### PostgreSQL Compatibility:
- `SERIAL` for auto-increment
- `TIMESTAMP` for datetime
- Different boolean syntax

#### SQLite Fallback:
- `INTEGER PRIMARY KEY AUTOINCREMENT`
- Simplified data types

## Common Migration Scenarios

### Adding New Columns
The script automatically checks for and adds these columns if missing:

#### grpo_documents table:
- `notes` (TEXT) - General notes/comments
- `qc_notes` (TEXT) - QC approval notes
- `draft_or_post` (VARCHAR(10)) - Draft or post status

#### grpo_items table:
- `generated_barcode` (VARCHAR(100)) - WMS generated barcode
- `barcode_printed` (BOOLEAN) - Print status flag
- `qc_status` (VARCHAR(20)) - QC approval status
- `qc_notes` (TEXT) - QC item notes

#### users table:
- `branch_id` (VARCHAR(10)) - Current branch
- `branch_name` (VARCHAR(100)) - Branch display name
- `default_branch_id` (VARCHAR(10)) - Default branch
- `must_change_password` (BOOLEAN) - Password change flag
- `last_login` (DATETIME) - Last login timestamp
- `permissions` (TEXT) - User permissions JSON

### Creating Missing Tables

#### barcode_labels table:
```sql
CREATE TABLE barcode_labels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_code VARCHAR(50) NOT NULL,
    barcode VARCHAR(100) NOT NULL,
    label_format VARCHAR(20) NOT NULL,
    print_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_printed DATETIME NULL
);
```

#### branches table:
```sql
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
);
```

## Manual MySQL Commands

### Check Current Schema
```sql
-- Check if a column exists
SELECT COUNT(*) 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME = 'grpo_documents' 
AND COLUMN_NAME = 'notes';

-- List all tables
SHOW TABLES;

-- Describe table structure
DESCRIBE grpo_documents;
```

### Add Missing Column Manually
```sql
-- Add notes column to grpo_documents
ALTER TABLE grpo_documents ADD COLUMN notes TEXT NULL;

-- Add barcode columns to grpo_items
ALTER TABLE grpo_items ADD COLUMN generated_barcode VARCHAR(100) NULL;
ALTER TABLE grpo_items ADD COLUMN barcode_printed BOOLEAN DEFAULT FALSE;
```

## Troubleshooting

### Connection Issues
1. Verify MySQL service is running:
   ```bash
   sudo systemctl status mysql
   ```

2. Test connection:
   ```bash
   mysql -h localhost -u root -p
   ```

3. Check environment variables:
   ```bash
   echo $MYSQL_HOST
   echo $MYSQL_USER
   echo $MYSQL_DATABASE
   ```

### Permission Errors
1. Grant proper permissions:
   ```sql
   GRANT ALL PRIVILEGES ON wms_db.* TO 'your_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

2. Create database if it doesn't exist:
   ```sql
   CREATE DATABASE wms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

### Migration Failures
1. Check MySQL error log:
   ```bash
   sudo tail -f /var/log/mysql/error.log
   ```

2. Rollback and retry:
   ```sql
   ROLLBACK;
   ```

3. Manual column addition if script fails:
   ```sql
   -- Check what columns exist
   SHOW COLUMNS FROM grpo_documents;
   
   -- Add missing columns one by one
   ALTER TABLE grpo_documents ADD COLUMN notes TEXT;
   ```

## Validation

### Verify Migration Success
```sql
-- Check all expected columns exist
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME = 'grpo_documents';

-- Verify data integrity
SELECT COUNT(*) FROM grpo_documents;
SELECT COUNT(*) FROM grpo_items;
SELECT COUNT(*) FROM users;
```

### Test Application
1. Start the application:
   ```bash
   python main.py
   ```

2. Check for database errors in logs
3. Test GRPO creation and editing functionality
4. Verify barcode generation works

## Best Practices

1. **Always backup before migration:**
   ```bash
   mysqldump -u root -p wms_db > wms_backup_$(date +%Y%m%d).sql
   ```

2. **Test migrations on development environment first**

3. **Monitor application logs during migration:**
   ```bash
   tail -f application.log
   ```

4. **Use transactions for complex migrations:**
   ```sql
   START TRANSACTION;
   -- Migration commands here
   COMMIT;  -- or ROLLBACK; if issues
   ```

## Support

If you encounter issues:
1. Check the application logs for database errors
2. Verify all environment variables are set correctly
3. Ensure MySQL user has proper permissions
4. Test database connection manually
5. Run the migration script with verbose logging

For additional help, check the main application logs and ensure all dependencies are installed:
```bash
pip install PyMySQL mysql-connector-python
```