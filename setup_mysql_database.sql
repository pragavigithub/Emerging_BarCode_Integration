-- MySQL Database Setup for WMS
-- Run this script in MySQL to create the database and user

-- Create database
CREATE DATABASE IF NOT EXISTS wms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (optional - you can use root)
CREATE USER IF NOT EXISTS 'wms_user'@'localhost' IDENTIFIED BY 'wms_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON wms_db.* TO 'wms_user'@'localhost';

-- Grant permissions to root as well
GRANT ALL PRIVILEGES ON wms_db.* TO 'root'@'localhost';

-- Flush privileges
FLUSH PRIVILEGES;

-- Use the database
USE wms_db;

-- Verify setup
SELECT 'Database setup complete!' as status;
SHOW DATABASES LIKE 'wms_db';
