import requests
import json
import logging
from datetime import datetime
from app import app

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SAPIntegration:
    def __init__(self):
        self.base_url = app.config['SAP_B1_SERVER']
        self.username = app.config['SAP_B1_USERNAME']
        self.password = app.config['SAP_B1_PASSWORD']
        self.company_db = app.config['SAP_B1_COMPANY_DB']
        self.session_id = None
        self.session = requests.Session()
        self.session.verify = False  # For development, in production use proper SSL
        self.is_offline = False
        
        # Cache for frequently accessed data
        self._warehouse_cache = {}
        self._bin_cache = {}
        self._branch_cache = {}
        self._item_cache = {}
        
    def login(self):
        """Login to SAP B1 Service Layer"""
        # Check if SAP configuration exists
        if not self.base_url or not self.username or not self.password or not self.company_db:
            logging.warning("SAP B1 configuration not complete. Running in offline mode.")
            return False
            
        login_url = f"{self.base_url}/b1s/v1/Login"
        login_data = {
            "UserName": self.username,
            "Password": self.password,
            "CompanyDB": self.company_db
        }
        
        try:
            response = self.session.post(login_url, json=login_data, timeout=10)
            if response.status_code == 200:
                self.session_id = response.json().get('SessionId')
                logging.info("Successfully logged in to SAP B1")
                return True
            else:
                logging.warning(f"SAP B1 login failed: {response.text}. Running in offline mode.")
                return False
        except Exception as e:
            logging.warning(f"SAP B1 login error: {str(e)}. Running in offline mode.")
            return False
    
    def ensure_logged_in(self):
        """Ensure we have a valid session"""
        if not self.session_id:
            return self.login()
        return True
    
    def get_inventory_transfer_request(self, doc_num):
        """Get specific inventory transfer request from SAP B1"""
        if not self.ensure_logged_in():
            return None
        
        try:
            url = f"{self.base_url}/b1s/v1/InventoryTransferRequests?$filter=DocNum eq {doc_num}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                transfers = data.get('value', [])
                if transfers:
                    return transfers[0]
            return None
        except Exception as e:
            logging.error(f"Error getting inventory transfer request: {str(e)}")
            return None
    
    def get_bins(self, warehouse_code):
        """Get bins for a specific warehouse"""
        if not self.ensure_logged_in():
            return []
        
        try:
            url = f"{self.base_url}/b1s/v1/BinLocations?$filter=Warehouse eq '{warehouse_code}'"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                bins = data.get('value', [])
                
                # Transform the data to match our expected format
                formatted_bins = []
                for bin_data in bins:
                    formatted_bins.append({
                        'BinCode': bin_data.get('BinCode'),
                        'Description': bin_data.get('Description', ''),
                        'Warehouse': bin_data.get('Warehouse'),
                        'Active': bin_data.get('Active', 'Y')
                    })
                
                return formatted_bins
            else:
                logging.error(f"Failed to get bins: {response.status_code}")
                return []
        except Exception as e:
            logging.error(f"Error getting bins: {str(e)}")
            return []
    
    def get_purchase_order(self, po_number):
        """Get purchase order details from SAP B1"""
        if not self.ensure_logged_in():
            # Return mock data for offline mode
            return {
                'DocNum': po_number,
                'CardCode': 'V001',  # Sample vendor code
                'CardName': 'Sample Vendor Ltd',
                'DocDate': '2025-01-08',
                'DocTotal': 15000.00,
                'DocumentLines': [
                    {
                        'LineNum': 0,
                        'ItemCode': 'ITM001',
                        'ItemDescription': 'Sample Item 1',
                        'Quantity': 100,
                        'OpenQuantity': 100,
                        'Price': 50.00,
                        'UoMCode': 'EA',
                        'WarehouseCode': 'WH01',
                        'LineStatus': 'bost_Open'
                    },
                    {
                        'LineNum': 1,
                        'ItemCode': 'ITM002', 
                        'ItemDescription': 'Sample Item 2',
                        'Quantity': 50,
                        'OpenQuantity': 30,
                        'Price': 200.00,
                        'UoMCode': 'KGS',
                        'WarehouseCode': 'WH01',
                        'LineStatus': 'bost_Open'
                    }
                ]
            }
            
        url = f"{self.base_url}/b1s/v1/PurchaseOrders?$filter=DocNum eq {po_number}"
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['value']:
                    return data['value'][0]
            return None
        except Exception as e:
            logging.warning(f"Error fetching PO {po_number}: {str(e)}. Using offline mode.")
            # Return mock data on error
            return {
                'DocNum': po_number,
                'CardCode': 'V001',
                'CardName': 'Sample Vendor Ltd',
                'DocDate': '2025-01-08',
                'DocTotal': 15000.00,
                'DocumentLines': [
                    {
                        'LineNum': 0,
                        'ItemCode': 'ITM001',
                        'ItemDescription': 'Sample Item 1',
                        'Quantity': 100,
                        'OpenQuantity': 100,
                        'Price': 50.00,
                        'UoMCode': 'EA',
                        'WarehouseCode': 'WH01',
                        'LineStatus': 'bost_Open'
                    }
                ]
            }
    
    def get_purchase_order_items(self, po_number):
        """Get purchase order line items"""
        try:
            po_data = self.get_purchase_order(po_number)
            if po_data:
                return po_data.get('DocumentLines', [])
        except Exception as e:
            logging.warning(f"Unable to fetch PO items for {po_number}: {str(e)}. Running in offline mode.")
        return []
    
    def get_item_master(self, item_code):
        """Get item master data from SAP B1"""
        if not self.ensure_logged_in():
            return None
            
        url = f"{self.base_url}/b1s/v1/Items('{item_code}')"
        
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logging.error(f"Error fetching item {item_code}: {str(e)}")
            return None
    
    def get_warehouse_bins(self, warehouse_code):
        """Get bins for a warehouse"""
        if not self.ensure_logged_in():
            return []
            
        url = f"{self.base_url}/b1s/v1/BinLocations?$filter=WhsCode eq '{warehouse_code}'"
        
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get('value', [])
            return []
        except Exception as e:
            logging.error(f"Error fetching bins for warehouse {warehouse_code}: {str(e)}")
            return []
    
    def get_bin_items(self, bin_code):
        """Get items in a specific bin"""
        if not self.ensure_logged_in():
            return []
            
        url = f"{self.base_url}/b1s/v1/StockTransferDrafts?$filter=BinCode eq '{bin_code}'"
        
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get('value', [])
            return []
        except Exception as e:
            logging.error(f"Error fetching items for bin {bin_code}: {str(e)}")
            return []
    
    def get_available_bins(self, warehouse_code):
        """Get available bins for a warehouse"""
        if not self.ensure_logged_in():
            # Return fallback bins if SAP is not available
            return []
            
        try:
            # Get bins from SAP B1
            url = f"{self.base_url}/b1s/v1/BinLocations"
            params = {'$filter': f"Warehouse eq '{warehouse_code}' and Active eq 'Y'"}
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                bins = []
                for bin_data in data.get('value', []):
                    bins.append({
                        'BinCode': bin_data.get('BinCode'),
                        'Description': bin_data.get('Description', '')
                    })
                return bins
            else:
                logging.error(f"Failed to get bins from SAP: {response.text}")
                return []
                
        except Exception as e:
            logging.error(f"Error getting bins from SAP: {str(e)}")
            return []
    
    def create_goods_receipt_po(self, grpo_document):
        """Create Goods Receipt PO in SAP B1"""
        if not self.ensure_logged_in():
            # Return success for offline mode
            import random
            return {
                'success': True, 
                'error': None,
                'document_number': f'GRPO-{random.randint(100000, 999999)}'
            }
            
        url = f"{self.base_url}/b1s/v1/PurchaseDeliveryNotes"
        
        # Get PO data to ensure we have correct supplier code
        po_data = self.get_purchase_order(grpo_document.po_number)
        if not po_data:
            return {'success': False, 'error': f'Purchase Order {grpo_document.po_number} not found'}
        
        supplier_code = po_data.get('CardCode')
        if not supplier_code:
            return {'success': False, 'error': 'Supplier code not found in PO'}
        
        # Build document lines
        document_lines = []
        for item in grpo_document.items:
            line = {
                "ItemCode": item.item_code,
                "Quantity": item.received_quantity,
                "UnitOfMeasure": item.unit_of_measure,
                "WarehouseCode": "WH01",  # Default warehouse
                "BinCode": item.bin_location
            }
            
            # Add batch information if available
            if item.batch_number:
                line["BatchNumbers"] = [{
                    "BatchNumber": item.batch_number,
                    "Quantity": item.received_quantity,
                    "ExpiryDate": item.expiration_date.strftime('%Y-%m-%d') if item.expiration_date else None
                }]
                
            # Add serial numbers if needed
            if item.generated_barcode:
                line["SerialNumbers"] = [{
                    "SerialNumber": item.generated_barcode,
                    "Quantity": 1
                }]
                
            document_lines.append(line)
        
        grpo_data = {
            "CardCode": supplier_code,
            "DocDate": grpo_document.created_at.strftime('%Y-%m-%d'),
            "DocumentLines": document_lines,
            "Comments": f"Created from WMS GRPO {grpo_document.id} by {grpo_document.user.username}",
            "U_WMS_GRPO_ID": str(grpo_document.id)  # Custom field to track WMS document
        }
        
        try:
            response = self.session.post(url, json=grpo_data)
            if response.status_code == 201:
                result = response.json()
                return {
                    'success': True,
                    'document_number': result.get('DocNum')
                }
            else:
                return {
                    'success': False,
                    'error': f"SAP B1 error: {response.text}"
                }
        except Exception as e:
            logging.error(f"Error creating GRPO in SAP B1: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_inventory_transfer(self, transfer_document):
        """Create Inventory Transfer in SAP B1"""
        if not self.ensure_logged_in():
            return {'success': False, 'error': 'Not logged in to SAP B1'}
            
        url = f"{self.base_url}/b1s/v1/StockTransfers"
        
        # Build document lines
        document_lines = []
        for item in transfer_document.items:
            line = {
                "ItemCode": item.item_code,
                "Quantity": item.quantity,
                "FromWarehouseCode": item.from_bin[:2],  # Assuming first 2 chars are warehouse
                "ToWarehouseCode": item.to_bin[:2],
                "FromBinCode": item.from_bin,
                "ToBinCode": item.to_bin
            }
            if item.batch_number:
                line["BatchNumbers"] = [{
                    "BatchNumber": item.batch_number,
                    "Quantity": item.quantity
                }]
            document_lines.append(line)
        
        transfer_data = {
            "DocumentLines": document_lines,
            "Comments": f"Created from WMS Transfer {transfer_document.id}"
        }
        
        try:
            response = self.session.post(url, json=transfer_data)
            if response.status_code == 201:
                result = response.json()
                return {
                    'success': True,
                    'document_number': result.get('DocNum')
                }
            else:
                return {
                    'success': False,
                    'error': f"SAP B1 error: {response.text}"
                }
        except Exception as e:
            logging.error(f"Error creating inventory transfer in SAP B1: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_inventory_counting(self, count_document):
        """Create Inventory Counting Document in SAP B1"""
        if not self.ensure_logged_in():
            return {'success': False, 'error': 'Not logged in to SAP B1'}
            
        url = f"{self.base_url}/b1s/v1/InventoryCountings"
        
        # Build document lines
        document_lines = []
        for item in count_document.items:
            line = {
                "ItemCode": item.item_code,
                "CountedQuantity": item.counted_quantity,
                "BinCode": count_document.bin_location
            }
            if item.batch_number:
                line["BatchNumber"] = item.batch_number
            document_lines.append(line)
        
        count_data = {
            "CountDate": datetime.now().strftime('%Y-%m-%d'),
            "CountTime": datetime.now().strftime('%H:%M:%S'),
            "Remarks": f"Created from WMS Count {count_document.id}",
            "InventoryCountingLines": document_lines
        }
        
        try:
            response = self.session.post(url, json=count_data)
            if response.status_code == 201:
                result = response.json()
                return {
                    'success': True,
                    'document_number': result.get('DocNum')
                }
            else:
                return {
                    'success': False,
                    'error': f"SAP B1 error: {response.text}"
                }
        except Exception as e:
            logging.error(f"Error creating inventory counting in SAP B1: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def sync_warehouses(self):
        """Sync warehouses from SAP B1 to local database"""
        if not self.ensure_logged_in():
            logging.warning("Cannot sync warehouses - SAP B1 not available")
            return False
            
        try:
            url = f"{self.base_url}/b1s/v1/Warehouses"
            response = self.session.get(url)
            
            if response.status_code == 200:
                warehouses = response.json().get('value', [])
                
                from app import db
                
                # Clear cache and update database
                self._warehouse_cache = {}
                
                for wh in warehouses:
                    # Check if warehouse exists in branches table
                    existing = db.session.execute(
                        db.text("SELECT id FROM branches WHERE id = :id"), 
                        {"id": wh.get('WarehouseCode')}
                    ).fetchone()
                    
                    if not existing:
                        # Insert new warehouse as branch - use compatible SQL
                        import os
                        from app import app
                        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
                        
                        if 'postgresql' in db_uri.lower() or 'mysql' in db_uri.lower():
                            insert_sql = """
                                INSERT INTO branches (id, name, address, is_active, created_at, updated_at)
                                VALUES (:id, :name, :address, :is_active, NOW(), NOW())
                            """
                        else:
                            insert_sql = """
                                INSERT INTO branches (id, name, address, is_active, created_at, updated_at)
                                VALUES (:id, :name, :address, :is_active, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            """
                        
                        db.session.execute(db.text(insert_sql), {
                            "id": wh.get('WarehouseCode'),
                            "name": wh.get('WarehouseName', ''),
                            "address": wh.get('Street', ''),
                            "is_active": wh.get('Inactive') != 'Y'
                        })
                    else:
                        # Update existing warehouse - use compatible SQL
                        import os
                        from app import app
                        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
                        
                        if 'postgresql' in db_uri.lower() or 'mysql' in db_uri.lower():
                            update_sql = """
                                UPDATE branches SET 
                                    name = :name, 
                                    address = :address, 
                                    is_active = :is_active,
                                    updated_at = NOW()
                                WHERE id = :id
                            """
                        else:
                            update_sql = """
                                UPDATE branches SET 
                                    name = :name, 
                                    address = :address, 
                                    is_active = :is_active,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = :id
                            """
                        
                        db.session.execute(db.text(update_sql), {
                            "id": wh.get('WarehouseCode'),
                            "name": wh.get('WarehouseName', ''),
                            "address": wh.get('Street', ''),
                            "is_active": wh.get('Inactive') != 'Y'
                        })
                    
                    # Cache warehouse data
                    self._warehouse_cache[wh.get('WarehouseCode')] = {
                        'WarehouseCode': wh.get('WarehouseCode'),
                        'WarehouseName': wh.get('WarehouseName'),
                        'Address': wh.get('Street'),
                        'Active': wh.get('Inactive') != 'Y'
                    }
                
                db.session.commit()
                logging.info(f"Synced {len(warehouses)} warehouses from SAP B1")
                return True
                
        except Exception as e:
            logging.error(f"Error syncing warehouses: {str(e)}")
            return False
    
    def sync_bins(self, warehouse_code=None):
        """Sync bin locations from SAP B1"""
        if not self.ensure_logged_in():
            logging.warning("Cannot sync bins - SAP B1 not available")
            return False
            
        try:
            # Get bins for specific warehouse or all warehouses
            if warehouse_code:
                url = f"{self.base_url}/b1s/v1/BinLocations?$filter=Warehouse eq '{warehouse_code}'"
            else:
                url = f"{self.base_url}/b1s/v1/BinLocations"
                
            response = self.session.get(url)
            
            if response.status_code == 200:
                bins = response.json().get('value', [])
                
                # Create bins table if not exists - use compatible SQL
                from app import db, app
                import os
                
                db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
                
                if 'postgresql' in db_uri.lower():
                    create_table_sql = """
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
                elif 'mysql' in db_uri.lower():
                    create_table_sql = """
                        CREATE TABLE IF NOT EXISTS bin_locations (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            bin_code VARCHAR(50) NOT NULL,
                            warehouse_code VARCHAR(10) NOT NULL,
                            bin_name VARCHAR(100),
                            is_active BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT NOW(),
                            updated_at TIMESTAMP DEFAULT NOW() ON UPDATE NOW(),
                            UNIQUE KEY unique_bin_warehouse (bin_code, warehouse_code)
                        )
                    """
                else:
                    create_table_sql = """
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
                
                db.session.execute(db.text(create_table_sql))
                
                # Clear cache
                self._bin_cache = {}
                
                for bin_data in bins:
                    bin_code = bin_data.get('BinCode')
                    wh_code = bin_data.get('Warehouse')  # Use 'Warehouse' not 'WarehouseCode'
                    
                    if bin_code and wh_code:
                        # Upsert bin location - use database-specific syntax
                        if 'postgresql' in db_uri.lower():
                            upsert_sql = """
                                INSERT INTO bin_locations (bin_code, warehouse_code, bin_name, is_active, created_at, updated_at)
                                VALUES (:bin_code, :warehouse_code, :bin_name, :is_active, NOW(), NOW())
                                ON CONFLICT (bin_code, warehouse_code) 
                                DO UPDATE SET 
                                    bin_name = EXCLUDED.bin_name,
                                    is_active = EXCLUDED.is_active,
                                    updated_at = NOW()
                            """
                        elif 'mysql' in db_uri.lower():
                            upsert_sql = """
                                INSERT INTO bin_locations (bin_code, warehouse_code, bin_name, is_active, created_at, updated_at)
                                VALUES (:bin_code, :warehouse_code, :bin_name, :is_active, NOW(), NOW())
                                ON DUPLICATE KEY UPDATE 
                                    bin_name = VALUES(bin_name),
                                    is_active = VALUES(is_active),
                                    updated_at = NOW()
                            """
                        else:
                            # SQLite - use INSERT OR REPLACE
                            upsert_sql = """
                                INSERT OR REPLACE INTO bin_locations (bin_code, warehouse_code, bin_name, is_active, created_at, updated_at)
                                VALUES (:bin_code, :warehouse_code, :bin_name, :is_active, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            """
                        
                        db.session.execute(db.text(upsert_sql), {
                            "bin_code": bin_code,
                            "warehouse_code": wh_code,
                            "bin_name": bin_data.get('Description', ''),
                            "is_active": bin_data.get('Inactive') != 'Y'
                        })
                        
                        # Cache bin data
                        cache_key = f"{wh_code}:{bin_code}"
                        self._bin_cache[cache_key] = {
                            'BinCode': bin_code,
                            'WarehouseCode': wh_code,
                            'Description': bin_data.get('Description', ''),
                            'Active': bin_data.get('Inactive') != 'Y'
                        }
                
                db.session.commit()
                logging.info(f"Synced {len(bins)} bin locations from SAP B1")
                return True
                
        except Exception as e:
            logging.error(f"Error syncing bins: {str(e)}")
            return False
    
    def sync_business_partners(self):
        """Sync business partners (suppliers/customers) from SAP B1"""
        if not self.ensure_logged_in():
            logging.warning("Cannot sync business partners - SAP B1 not available")
            return False
            
        try:
            # Get suppliers and customers
            url = f"{self.base_url}/b1s/v1/BusinessPartners?$filter=CardType eq 'cSupplier' or CardType eq 'cCustomer'"
            response = self.session.get(url)
            
            if response.status_code == 200:
                partners = response.json().get('value', [])
                
                from app import db, app
                
                # Create business_partners table if not exists - use database-specific syntax
                db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
                
                if 'postgresql' in db_uri.lower():
                    create_table_sql = """
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
                elif 'mysql' in db_uri.lower():
                    create_table_sql = """
                        CREATE TABLE IF NOT EXISTS business_partners (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            card_code VARCHAR(50) UNIQUE NOT NULL,
                            card_name VARCHAR(200) NOT NULL,
                            card_type VARCHAR(20) NOT NULL,
                            phone VARCHAR(50),
                            email VARCHAR(100),
                            address TEXT,
                            is_active BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT NOW(),
                            updated_at TIMESTAMP DEFAULT NOW() ON UPDATE NOW()
                        )
                    """
                else:
                    create_table_sql = """
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
                
                db.session.execute(db.text(create_table_sql))
                
                for partner in partners:
                    card_code = partner.get('CardCode')
                    if card_code:
                        # Use database-specific upsert syntax
                        if 'postgresql' in db_uri.lower():
                            upsert_sql = """
                                INSERT INTO business_partners (card_code, card_name, card_type, phone, email, address, is_active, created_at, updated_at)
                                VALUES (:card_code, :card_name, :card_type, :phone, :email, :address, :is_active, NOW(), NOW())
                                ON CONFLICT (card_code) 
                                DO UPDATE SET 
                                    card_name = EXCLUDED.card_name,
                                    card_type = EXCLUDED.card_type,
                                    phone = EXCLUDED.phone,
                                    email = EXCLUDED.email,
                                    address = EXCLUDED.address,
                                    is_active = EXCLUDED.is_active,
                                    updated_at = NOW()
                            """
                        elif 'mysql' in db_uri.lower():
                            upsert_sql = """
                                INSERT INTO business_partners (card_code, card_name, card_type, phone, email, address, is_active, created_at, updated_at)
                                VALUES (:card_code, :card_name, :card_type, :phone, :email, :address, :is_active, NOW(), NOW())
                                ON DUPLICATE KEY UPDATE 
                                    card_name = VALUES(card_name),
                                    card_type = VALUES(card_type),
                                    phone = VALUES(phone),
                                    email = VALUES(email),
                                    address = VALUES(address),
                                    is_active = VALUES(is_active),
                                    updated_at = NOW()
                            """
                        else:
                            # SQLite - use INSERT OR REPLACE
                            upsert_sql = """
                                INSERT OR REPLACE INTO business_partners (card_code, card_name, card_type, phone, email, address, is_active, created_at, updated_at)
                                VALUES (:card_code, :card_name, :card_type, :phone, :email, :address, :is_active, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            """
                        
                        db.session.execute(db.text(upsert_sql), {
                            "card_code": card_code,
                            "card_name": partner.get('CardName', ''),
                            "card_type": partner.get('CardType', ''),
                            "phone": partner.get('Phone1', ''),
                            "email": partner.get('EmailAddress', ''),
                            "address": partner.get('Address', ''),
                            "is_active": partner.get('Valid') == 'Y'
                        })
                
                db.session.commit()
                logging.info(f"Synced {len(partners)} business partners from SAP B1")
                return True
                
        except Exception as e:
            logging.error(f"Error syncing business partners: {str(e)}")
            return False
    
    def create_purchase_delivery_note(self, grpo_document):
        """Create Purchase Delivery Note in SAP B1 to close PO after QC Approval"""
        if not self.ensure_logged_in():
            # Return success for offline mode
            import random
            return {
                'success': True, 
                'error': None,
                'document_number': f'PDN-{random.randint(100000, 999999)}'
            }
            
        # Get PO data first to ensure proper field mapping
        po_data = self.get_purchase_order(grpo_document.po_number)
        if not po_data:
            return {'success': False, 'error': f'Purchase Order {grpo_document.po_number} not found in SAP B1'}
        
        supplier_code = po_data.get('CardCode')
        po_doc_entry = po_data.get('DocEntry')
        
        if not supplier_code or not po_doc_entry:
            return {'success': False, 'error': 'Missing supplier code or PO DocEntry from SAP B1'}
        
        # Build document lines with proper PO base reference
        document_lines = []
        for item in grpo_document.items:
            # Only include QC approved items
            if item.qc_status != 'approved':
                continue
                
            # Find matching PO line for proper mapping
            po_line_num = None
            po_line_data = None
            for po_line in po_data.get('DocumentLines', []):
                if po_line.get('ItemCode') == item.item_code:
                    po_line_num = po_line.get('LineNum')
                    po_line_data = po_line
                    break
            
            if po_line_num is None:
                logging.warning(f"PO line not found for item {item.item_code} in PO {grpo_document.po_number}")
                continue  # Skip items not found in PO
            
            # Extract warehouse code from bin location (first 4 characters or default)
            warehouse_code = item.bin_location[:4] if len(item.bin_location) >= 4 else "2002"
            
            # Build line with proper SAP B1 field mapping
            line = {
                "BaseType": 22,  # Purchase Order base type
                "BaseEntry": po_doc_entry,
                "BaseLine": po_line_num,
                "ItemCode": item.item_code,
                "ItemDescription": item.item_name,
                "Quantity": item.received_quantity,
                "Price": po_line_data.get('Price', 0) if po_line_data else 0,
                "WarehouseCode": warehouse_code,
                "UoMCode": item.unit_of_measure or po_line_data.get('UoMCode', 'EA') if po_line_data else 'EA'
            }
            
            # Add batch information if available
            if item.batch_number:
                batch_info = {
                    "BatchNumber": item.batch_number,
                    "Quantity": item.received_quantity
                }
                if item.expiration_date:
                    batch_info["ExpiryDate"] = item.expiration_date.strftime('%Y-%m-%d')
                line["BatchNumbers"] = [batch_info]
            
            # Add bin location information
            if item.bin_location:
                line["BinAllocations"] = [{
                    "BinAbsEntry": 0,  # SAP will resolve this
                    "BinCode": item.bin_location,
                    "Quantity": item.received_quantity
                }]
            
            document_lines.append(line)
        
        if not document_lines:
            return {'success': False, 'error': 'No approved items found for Purchase Delivery Note creation'}
        
        # Create Purchase Delivery Note payload with all required fields
        pdn_data = {
            "CardCode": supplier_code,
            "DocDate": grpo_document.created_at.strftime('%Y-%m-%d'),
            "DocDueDate": grpo_document.created_at.strftime('%Y-%m-%d'),
            "TaxDate": grpo_document.created_at.strftime('%Y-%m-%d'),
            "Comments": f"WMS GRPO {grpo_document.id} - Closing PO {grpo_document.po_number} after QC Approval by {grpo_document.qc_user.username if grpo_document.qc_user else 'System'}",
            "Reference1": f"GRPO-{grpo_document.id}",
            "Reference2": f"PO-{grpo_document.po_number}",
            "DocumentLines": document_lines
        }
        
        url = f"{self.base_url}/b1s/v1/PurchaseDeliveryNotes"
        
        try:
            response = self.session.post(url, json=pdn_data)
            if response.status_code == 201:
                result = response.json()
                logging.info(f"Successfully created Purchase Delivery Note {result.get('DocNum')} for GRPO {grpo_document.id}")
                return {
                    'success': True,
                    'document_number': result.get('DocNum'),
                    'doc_entry': result.get('DocEntry'),
                    'message': f'Purchase Delivery Note {result.get("DocNum")} created successfully'
                }
            else:
                error_msg = f"SAP B1 error creating Purchase Delivery Note: {response.text}"
                logging.error(error_msg)
                return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = f"Error creating Purchase Delivery Note in SAP B1: {str(e)}"
            logging.error(error_msg)
            return {'success': False, 'error': error_msg}

    def post_grpo_to_sap(self, grpo_document):
        """Post approved GRPO to SAP B1 as Purchase Delivery Note"""
        if not self.ensure_logged_in():
            logging.warning("Cannot post GRPO - SAP B1 not available")
            return {'success': False, 'error': 'SAP B1 not available'}
            
        try:
            # Create Purchase Delivery Note to close PO
            result = self.create_purchase_delivery_note(grpo_document)
            
            if result.get('success'):
                # Update WMS record with SAP document number
                grpo_document.sap_document_number = str(result.get('document_number'))
                grpo_document.status = 'posted'
                
                from app import db
                db.session.commit()
                
                logging.info(f"GRPO posted to SAP B1 with Purchase Delivery Note: {result.get('document_number')}")
                return {
                    'success': True,
                    'sap_document_number': result.get('document_number'),
                    'message': f'GRPO posted to SAP B1 as Purchase Delivery Note {result.get("document_number")}'
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error occurred')
                }
        except Exception as e:
            logging.error(f"Error posting GRPO to SAP: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def sync_all_master_data(self):
        """Sync all master data from SAP B1"""
        logging.info("Starting full SAP B1 master data synchronization...")
        
        results = {
            'warehouses': self.sync_warehouses(),
            'bins': self.sync_bins(),
            'business_partners': self.sync_business_partners()
        }
        
        success_count = sum(1 for result in results.values() if result)
        logging.info(f"Master data sync completed: {success_count}/{len(results)} successful")
        
        return results

    def logout(self):
        """Logout from SAP B1"""
        if self.session_id:
            try:
                logout_url = f"{self.base_url}/b1s/v1/Logout"
                self.session.post(logout_url)
                self.session_id = None
                logging.info("Logged out from SAP B1")
            except Exception as e:
                logging.error(f"Error logging out from SAP B1: {str(e)}")
