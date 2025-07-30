"""
SAP Integration extensions for missing methods
"""
import logging
from datetime import datetime


def get_bin_locations(sap_instance, warehouse_code):
    """Get bin locations for a specific warehouse"""
    if not sap_instance.ensure_logged_in():
        # Return mock data for offline mode
        return [
            {
                'BinCode': f'{warehouse_code}-SYSTEM-BIN-LOCATION',
                'AbsEntry': 1390,
                'Description': 'System Bin Location',
                'Warehouse': warehouse_code
            }
        ]

    try:
        # Get bin locations using SAP B1 API pattern from user
        url = f"{sap_instance.base_url}/b1s/v1/BinLocations?$filter=Warehouse eq '{warehouse_code}'"
        response = sap_instance.session.get(url)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('value', [])
        else:
            logging.warning(f"Error fetching bin locations: {response.text}")
            return []
            
    except Exception as e:
        logging.error(f"Error fetching bin locations: {str(e)}")
        return []


def get_batch_details(sap_instance, item_code):
    """Get batch details for a specific item code"""
    if not sap_instance.ensure_logged_in():
        # Return mock data for offline mode
        return [
            {
                'Batch': '20220729',
                'ItemCode': item_code,
                'ItemDescription': 'Sample Item Description',
                'Status': 'bdsStatus_Released',
                'ExpirationDate': '2025-07-29T00:00:00Z',
                'SystemNumber': 1
            }
        ]

    try:
        # Get batch details using SAP B1 API pattern from user
        url = f"{sap_instance.base_url}/b1s/v1/BatchNumberDetails?$filter=ItemCode eq '{item_code}'"
        response = sap_instance.session.get(url)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('value', [])
        else:
            logging.warning(f"Error fetching batch details: {response.text}")
            return []
            
    except Exception as e:
        logging.error(f"Error fetching batch details: {str(e)}")
        return []


def post_grn_to_sap(sap_instance, grn_doc):
    """Post GRN (Goods Received Note) to SAP B1 as Purchase Delivery Note"""
    if not sap_instance.ensure_logged_in():
        # Return mock success for offline mode
        logging.warning("SAP B1 not available, simulating successful GRN posting")
        return {
            'success': True,
            'sap_document_number': f'PD-MOCK-{grn_doc.id}',
            'message': 'Mock posting successful (offline mode)'
        }

    try:
        # Get PO details first
        po_data = sap_instance.get_purchase_order(grn_doc.po_number)
        if not po_data:
            return {
                'success': False,
                'error': f'Purchase Order {grn_doc.po_number} not found in SAP B1'
            }

        # Build Purchase Delivery Note JSON
        delivery_note = {
            'CardCode': po_data.get('CardCode'),
            'DocDate': datetime.now().strftime('%Y-%m-%d'),
            'DocDueDate': po_data.get('DocDueDate', datetime.now().strftime('%Y-%m-%d')),
            'Comments': f'GRN {grn_doc.grn_number} - Generated from WMS',
            'NumAtCard': grn_doc.po_number,
            'DocumentLines': []
        }

        # Add document lines from approved GRN items
        for item in grn_doc.items:
            if item.qc_status == 'approved' and item.received_quantity > 0:
                # Find corresponding PO line
                po_line = None
                for po_doc_line in po_data.get('DocumentLines', []):
                    if po_doc_line.get('ItemCode') == item.item_code:
                        po_line = po_doc_line
                        break
                
                if po_line:
                    doc_line = {
                        'ItemCode': item.item_code,
                        'Quantity': float(item.received_quantity),
                        'UnitPrice': po_line.get('UnitPrice', 0),
                        'WarehouseCode': item.warehouse_code,
                        'BaseType': 22,  # Purchase Order
                        'BaseEntry': po_data.get('DocEntry'),
                        'BaseLine': po_line.get('LineNum')
                    }
                    
                    # Add batch information if available
                    if item.batch_number:
                        doc_line['BatchNumbers'] = [{
                            'BatchNumber': item.batch_number,
                            'Quantity': float(item.received_quantity),
                            'ExpiryDate': item.expiration_date.strftime('%Y-%m-%dT00:00:00Z') if item.expiration_date else None
                        }]
                    
                    delivery_note['DocumentLines'].append(doc_line)

        if not delivery_note['DocumentLines']:
            return {
                'success': False,
                'error': 'No approved items found to post to SAP B1'
            }

        # Post to SAP B1
        url = f"{sap_instance.base_url}/b1s/v1/PurchaseDeliveryNotes"
        response = sap_instance.session.post(url, json=delivery_note)
        
        if response.status_code == 201:
            result_data = response.json()
            doc_entry = result_data.get('DocEntry')
            doc_num = result_data.get('DocNum')
            
            logging.info(f"✅ Successfully posted GRN to SAP B1 as Purchase Delivery Note {doc_num}")
            
            return {
                'success': True,
                'sap_document_number': doc_num,
                'sap_doc_entry': doc_entry,
                'message': f'Successfully posted to SAP B1 as Purchase Delivery Note {doc_num}'
            }
        else:
            error_msg = f"SAP B1 API Error: {response.status_code} - {response.text}"
            logging.error(f"❌ Failed to post GRN to SAP B1: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
            
    except Exception as e:
        error_msg = f"Error posting GRN to SAP B1: {str(e)}"
        logging.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }