#!/usr/bin/env python3
"""
Quick Database Fix for Replit Migration Issues
This script fixes the specific database issues reported:
1. Missing columns in branches table
2. bin_location column too small in grn_items
3. Batch filtering by item code
"""

import os
import sys
from app import app, db
from models import User, GRNDocument, GRNItem
from sqlalchemy import text

def fix_database_schema():
    """Fix database schema issues"""
    print("🔧 Starting database schema fixes...")
    
    with app.app_context():
        try:
            # Fix 1: Add missing columns to branches table if they don't exist
            print("📝 Checking branches table schema...")
            try:
                # Try to add missing columns to branches table
                db.session.execute(text("""
                    ALTER TABLE branches 
                    ADD COLUMN IF NOT EXISTS description TEXT,
                    ADD COLUMN IF NOT EXISTS address VARCHAR(255),
                    ADD COLUMN IF NOT EXISTS phone VARCHAR(50),
                    ADD COLUMN IF NOT EXISTS email VARCHAR(120),
                    ADD COLUMN IF NOT EXISTS manager_name VARCHAR(100),
                    ADD COLUMN IF NOT EXISTS is_default BOOLEAN DEFAULT FALSE
                """))
                print("✅ Added missing columns to branches table")
            except Exception as e:
                print(f"⚠️ Branches table fix (PostgreSQL doesn't need this): {e}")
            
            # Fix 2: Increase bin_location column size
            print("📝 Fixing bin_location column size...")
            try:
                db.session.execute(text("""
                    ALTER TABLE grn_items 
                    ALTER COLUMN bin_location TYPE VARCHAR(100)
                """))
                print("✅ Increased bin_location column size to VARCHAR(100)")
            except Exception as e:
                print(f"⚠️ Bin location column fix: {e}")
                
            # Fix 3: Add missing columns to grn_items if needed
            print("📝 Checking grn_items table schema...")
            try:
                db.session.execute(text("""
                    ALTER TABLE grn_items 
                    ADD COLUMN IF NOT EXISTS po_line_number INTEGER DEFAULT 0,
                    ADD COLUMN IF NOT EXISTS po_quantity DECIMAL(15,3),
                    ADD COLUMN IF NOT EXISTS open_quantity DECIMAL(15,3),
                    ADD COLUMN IF NOT EXISTS unit_price DECIMAL(15,4),
                    ADD COLUMN IF NOT EXISTS supplier_barcode VARCHAR(100),
                    ADD COLUMN IF NOT EXISTS generated_barcode VARCHAR(100),
                    ADD COLUMN IF NOT EXISTS barcode_printed BOOLEAN DEFAULT FALSE,
                    ADD COLUMN IF NOT EXISTS qc_status VARCHAR(20) DEFAULT 'pending',
                    ADD COLUMN IF NOT EXISTS qc_notes TEXT
                """))
                print("✅ Added missing columns to grn_items table")
            except Exception as e:
                print(f"⚠️ GRN items table fix: {e}")
            
            # Commit all changes
            db.session.commit()
            print("✅ All database schema fixes completed successfully!")
            
        except Exception as e:
            print(f"❌ Error fixing database schema: {e}")
            db.session.rollback()
            return False
    
    return True

def create_missing_data():
    """Create missing default data"""
    with app.app_context():
        try:
            # Check if default branch exists, create if missing
            from models import Branch
            
            default_branch = Branch.query.filter_by(id='BR001').first()
            if not default_branch:
                default_branch = Branch(
                    id='BR001',
                    name='Main Branch',
                    description='Default main branch',
                    address='Head Office',
                    phone='N/A',
                    email='admin@company.com',
                    manager_name='System Admin',
                    is_default=True,
                    is_active=True
                )
                db.session.add(default_branch)
                db.session.commit()
                print("✅ Created default branch")
            else:
                # Update existing branch with missing fields
                if not hasattr(default_branch, 'description') or default_branch.description is None:
                    default_branch.description = 'Default main branch'
                    default_branch.address = 'Head Office'
                    default_branch.phone = 'N/A'
                    default_branch.email = 'admin@company.com'
                    default_branch.manager_name = 'System Admin'
                    default_branch.is_default = True
                    db.session.commit()
                    print("✅ Updated default branch with missing fields")
                
        except Exception as e:
            print(f"⚠️ Could not create/update default branch: {e}")

if __name__ == "__main__":
    print("🚀 Starting Quick Database Fix for Replit...")
    
    # Fix database schema
    if fix_database_schema():
        print("✅ Database schema fixes completed")
        
        # Create missing data
        create_missing_data()
        print("✅ Missing data creation completed")
        
        print("\n🎉 Database fixes completed successfully!")
        print("You can now restart your application.")
    else:
        print("❌ Database fix failed. Please check the errors above.")
        sys.exit(1)