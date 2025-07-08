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
        
    def login(self):
        """Login to SAP B1 Service Layer"""
        login_url = f"{self.base_url}/b1s/v1/Login"
        login_data = {
            "UserName": self.username,
            "Password": self.password,
            "CompanyDB": self.company_db
        }
        
        try:
            response = self.session.post(login_url, json=login_data)
            if response.status_code == 200:
                self.session_id = response.json().get('SessionId')
                logging.info("Successfully logged in to SAP B1")
                return True
            else:
                logging.error(f"SAP B1 login failed: {response.text}")
                return False
        except Exception as e:
            logging.error(f"SAP B1 login error: {str(e)}")
            return False
    
    def ensure_logged_in(self):
        """Ensure we have a valid session"""
        if not self.session_id:
            return self.login()
        return True
    
    def get_purchase_order(self, po_number):
        """Get purchase order details from SAP B1"""
        if not self.ensure_logged_in():
            return None
            
        url = f"{self.base_url}/b1s/v1/PurchaseOrders?$filter=DocNum eq {po_number}"
        
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                data = response.json()
                if data['value']:
                    return data['value'][0]
            return None
        except Exception as e:
            logging.error(f"Error fetching PO {po_number}: {str(e)}")
            return None
    
    def get_purchase_order_items(self, po_number):
        """Get purchase order line items"""
        po_data = self.get_purchase_order(po_number)
        if po_data:
            return po_data.get('DocumentLines', [])
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
    
    def create_goods_receipt_po(self, grpo_document):
        """Create Goods Receipt PO in SAP B1"""
        if not self.ensure_logged_in():
            return {'success': False, 'error': 'Not logged in to SAP B1'}
            
        url = f"{self.base_url}/b1s/v1/PurchaseDeliveryNotes"
        
        # Build document lines
        document_lines = []
        for item in grpo_document.items:
            line = {
                "ItemCode": item.item_code,
                "Quantity": item.quantity,
                "UnitOfMeasure": item.unit_of_measure,
                "BinCode": item.bin_location
            }
            if item.batch_number:
                line["BatchNumbers"] = [{
                    "BatchNumber": item.batch_number,
                    "Quantity": item.quantity
                }]
            document_lines.append(line)
        
        grpo_data = {
            "CardCode": "SUPPLIER001",  # This should come from PO
            "DocumentLines": document_lines,
            "Comments": f"Created from WMS GRPO {grpo_document.id}"
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
