"""
Fix SAP Data Sync Issues and Add Inventory Transfer Integration
"""
import os
import logging
from app import app, db
from sap_integration import SAPIntegration

def fix_database_schema():
    """Fix database schema to be compatible with both PostgreSQL and SQLite"""
    with app.app_context():
        try:
            # Check if we're using PostgreSQL or SQLite
            is_postgresql = 'postgresql' in os.environ.get('DATABASE_URL', '').lower()
            
            if is_postgresql:
                # PostgreSQL syntax
                create_bins_table = """
                    CREATE TABLE IF NOT EXISTS bin_locations (
                        id SERIAL PRIMARY KEY,
                        bin_code VARCHAR(50) NOT NULL,
                        warehouse_code VARCHAR(10) NOT NULL,
                        bin_name VARCHAR(100),
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(bin_code, warehouse_code)
                    )
                """
                
                create_business_partners_table = """
                    CREATE TABLE IF NOT EXISTS business_partners (
                        id SERIAL PRIMARY KEY,
                        card_code VARCHAR(50) UNIQUE NOT NULL,
                        card_name VARCHAR(200) NOT NULL,
                        card_type VARCHAR(20) NOT NULL,
                        phone VARCHAR(50),
                        email VARCHAR(100),
                        address TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """
                
                insert_warehouse_sql = """
                    INSERT INTO branches (id, name, address, is_active, created_at, updated_at)
                    VALUES (:id, :name, :address, :is_active, NOW(), NOW())
                """
                
            else:
                # SQLite syntax
                create_bins_table = """
                    CREATE TABLE IF NOT EXISTS bin_locations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        bin_code VARCHAR(50) NOT NULL,
                        warehouse_code VARCHAR(10) NOT NULL,
                        bin_name VARCHAR(100),
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(bin_code, warehouse_code)
                    )
                """
                
                create_business_partners_table = """
                    CREATE TABLE IF NOT EXISTS business_partners (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        card_code VARCHAR(50) UNIQUE NOT NULL,
                        card_name VARCHAR(200) NOT NULL,
                        card_type VARCHAR(20) NOT NULL,
                        phone VARCHAR(50),
                        email VARCHAR(100),
                        address TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                
                insert_warehouse_sql = """
                    INSERT INTO branches (id, name, address, is_active, created_at, updated_at)
                    VALUES (:id, :name, :address, :is_active, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            
            # Create tables
            db.session.execute(db.text(create_bins_table))
            db.session.execute(db.text(create_business_partners_table))
            db.session.commit()
            
            logging.info("Database schema fixed successfully")
            return True, insert_warehouse_sql
            
        except Exception as e:
            logging.error(f"Error fixing database schema: {str(e)}")
            return False, None

def sync_inventory_transfers():
    """Sync inventory transfer requests from SAP B1"""
    sap = SAPIntegration()
    
    if not sap.ensure_logged_in():
        logging.warning("Cannot sync inventory transfers - SAP B1 not available")
        return False
    
    try:
        # Get inventory transfer requests from SAP B1
        url = f"{sap.base_url}/b1s/v1/InventoryTransferRequests"
        response = sap.session.get(url)
        
        if response.status_code == 200:
            transfers = response.json().get('value', [])
            
            # Import necessary models
            from models import InventoryTransfer, InventoryTransferItem, User
            
            synced_count = 0
            for transfer in transfers:
                # Check if transfer already exists
                existing = InventoryTransfer.query.filter_by(
                    sap_document_number=str(transfer.get('DocEntry'))
                ).first()
                
                if not existing:
                    # Get or create a system user for SAP synced data
                    system_user = User.query.filter_by(username='system').first()
                    if not system_user:
                        continue  # Skip if no system user
                    
                    # Create new inventory transfer
                    new_transfer = InventoryTransfer(
                        transfer_request_number=f"TR-{transfer.get('DocEntry')}",
                        sap_document_number=str(transfer.get('DocEntry')),
                        status='approved' if transfer.get('DocStatus') == 'bost_Open' else 'draft',
                        user_id=system_user.id
                    )
                    
                    db.session.add(new_transfer)
                    db.session.flush()  # Get the ID
                    
                    # Add transfer items
                    for line in transfer.get('StockTransferLines', []):
                        transfer_item = InventoryTransferItem(
                            inventory_transfer_id=new_transfer.id,
                            item_code=line.get('ItemCode', ''),
                            item_name=line.get('ItemDescription', ''),
                            quantity=line.get('Quantity', 0),
                            unit_of_measure=line.get('UoMCode', 'EA'),
                            from_bin=line.get('FromWarehouseCode', ''),
                            to_bin=line.get('WarehouseCode', ''),
                            batch_number=line.get('BatchNumber', '')
                        )
                        db.session.add(transfer_item)
                    
                    synced_count += 1
            
            db.session.commit()
            logging.info(f"Synced {synced_count} inventory transfers from SAP B1")
            return True
            
        else:
            logging.error(f"Failed to get inventory transfers: {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"Error syncing inventory transfers: {str(e)}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== SAP Data Sync Fix ===")
    print("1. Fixing database schema...")
    success, insert_sql = fix_database_schema()
    if success:
        print("✓ Database schema fixed")
    else:
        print("✗ Database schema fix failed")
    
    print("2. Syncing inventory transfers...")
    if sync_inventory_transfers():
        print("✓ Inventory transfers synced")
    else:
        print("✗ Inventory transfer sync failed")
    
    print("=== Fix Complete ===")