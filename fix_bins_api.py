"""
Fix for Bins API endpoint - Add missing route
"""
from flask import request, jsonify
from flask_login import login_required
import logging
from app import app, db
from sap_integration import SAPIntegration

@app.route('/api/bins', methods=['GET'])
@login_required
def get_bins_api():
    """API endpoint to get available bins from SAP B1"""
    warehouse_code = request.args.get('warehouse_code')
    
    if not warehouse_code:
        return jsonify({'error': 'warehouse_code parameter is required'}), 400
    
    try:
        # First try to get from local database
        bins = db.session.execute(db.text("""
            SELECT bin_code, bin_name 
            FROM bin_locations 
            WHERE warehouse_code = :warehouse_code AND is_active = TRUE
            ORDER BY bin_code
        """), {"warehouse_code": warehouse_code}).fetchall()
        
        if bins:
            bin_list = [{'BinCode': bin[0], 'Description': bin[1]} for bin in bins]
            return jsonify({'bins': bin_list})
        
        # If no local data, try SAP B1
        sap = SAPIntegration()
        bins = sap.get_bins(warehouse_code)
        
        if bins:
            return jsonify({'bins': bins})
        else:
            return jsonify({'error': 'Unable to fetch bins from SAP B1'}), 500
            
    except Exception as e:
        logging.error(f"Error fetching bins: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/generate_barcode', methods=['POST'])
@login_required
def generate_barcode_api():
    """Generate new barcode for item"""
    data = request.get_json()
    item_code = data.get('item_code')
    
    if not item_code:
        return jsonify({'error': 'Item code is required'}), 400
    
    # Generate unique barcode with proper WMS format
    import secrets
    random_suffix = secrets.token_hex(4).upper()
    barcode = f"WMS-{item_code}-{random_suffix}"
    
    return jsonify({'barcode': barcode})

print("Bins API and Barcode Generation API routes added successfully!")