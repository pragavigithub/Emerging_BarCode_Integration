-- Manual MySQL Database Fix Script
-- Run this directly in MySQL to add missing columns

-- Add missing columns to grpo_documents table
ALTER TABLE grpo_documents ADD COLUMN notes TEXT NULL;
ALTER TABLE grpo_documents ADD COLUMN qc_notes TEXT NULL;
ALTER TABLE grpo_documents ADD COLUMN draft_or_post VARCHAR(10) DEFAULT 'draft';

-- Add missing columns to grpo_items table
ALTER TABLE grpo_items ADD COLUMN generated_barcode VARCHAR(100) NULL;
ALTER TABLE grpo_items ADD COLUMN barcode_printed BOOLEAN DEFAULT FALSE;
ALTER TABLE grpo_items ADD COLUMN qc_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE grpo_items ADD COLUMN qc_notes TEXT NULL;

-- Add missing columns to users table
ALTER TABLE users ADD COLUMN branch_id VARCHAR(10) NULL;
ALTER TABLE users ADD COLUMN branch_name VARCHAR(100) NULL;
ALTER TABLE users ADD COLUMN default_branch_id VARCHAR(10) NULL;
ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN last_login DATETIME NULL;
ALTER TABLE users ADD COLUMN permissions TEXT NULL;

-- Create barcode_labels table
CREATE TABLE IF NOT EXISTS barcode_labels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_code VARCHAR(50) NOT NULL,
    barcode VARCHAR(100) NOT NULL,
    label_format VARCHAR(20) NOT NULL,
    print_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_printed DATETIME NULL
);

-- Create branches table
CREATE TABLE IF NOT EXISTS branches (
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

-- Insert default branch
INSERT IGNORE INTO branches (id, name, is_default, is_active) 
VALUES ('HQ001', 'Head Office', TRUE, TRUE);

-- Show results
SELECT 'Database migration completed successfully' as message;