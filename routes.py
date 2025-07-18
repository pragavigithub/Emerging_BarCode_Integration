from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import logging
import json

from app import app, db, login_manager
from models import User, GRPODocument, GRPOItem, InventoryTransfer, InventoryTransferItem, PickList, PickListItem, InventoryCount, InventoryCountItem, BarcodeLabel
from sap_integration import SAPIntegration

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        branch_id = request.form.get('branch_id', '').strip()
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            if user.is_active:
                # Update branch - use provided branch, default branch, or 'HQ001'
                if branch_id:
                    user.branch_id = branch_id
                elif user.default_branch_id:
                    user.branch_id = user.default_branch_id
                elif not user.branch_id:
                    user.branch_id = 'HQ001'  # Default to head office
                
                # Update last login
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                login_user(user)
                
                # Check if password change is required
                if user.must_change_password:
                    flash('You must change your password before continuing.', 'warning')
                    return redirect(url_for('change_password'))
                
                flash('Logged in successfully!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Account is deactivated. Please contact administrator.', 'error')
        else:
            flash('Invalid username or password.', 'error')
    
    # Get available branches for login form
    branches = db.session.execute(db.text("SELECT id, name FROM branches WHERE is_active = TRUE ORDER BY name")).fetchall()
    return render_template('login.html', branches=branches)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Get dashboard statistics
        grpo_count = GRPODocument.query.filter_by(user_id=current_user.id).count()
        transfer_count = InventoryTransfer.query.filter_by(user_id=current_user.id).count()
        pick_list_count = PickList.query.filter_by(user_id=current_user.id).count()
        count_tasks = InventoryCount.query.filter_by(user_id=current_user.id).count()
        
        stats = {
            'grpo_count': grpo_count,
            'transfer_count': transfer_count,
            'pick_list_count': pick_list_count,
            'count_tasks': count_tasks
        }
    except Exception as e:
        logging.error(f"Database error in dashboard: {e}")
        # Handle database schema mismatch gracefully
        stats = {
            'grpo_count': 0,
            'transfer_count': 0,
            'pick_list_count': 0,
            'count_tasks': 0
        }
        flash('Database needs to be updated. Please run: python migrate_database.py', 'warning')
    
    return render_template('dashboard.html', stats=stats)

@app.route('/grpo')
@login_required
def grpo():
    try:
        documents = GRPODocument.query.filter_by(user_id=current_user.id).order_by(GRPODocument.created_at.desc()).all()
    except Exception as e:
        logging.error(f"Database error in grpo: {e}")
        documents = []
        flash('Database needs to be updated. Please run: python migrate_database.py', 'warning')
    return render_template('grpo.html', documents=documents)

@app.route('/grpo/create', methods=['POST'])
@login_required
def create_grpo():
    po_number = request.form['po_number']
    
    # BUSINESS LOGIC CHANGE: Allow multiple GRPOs per PO
    # Each PO should create a NEW GRPO every time (user requirement)
    # Skip the existing GRPO check to allow multiple GRPOs per PO
    
    # Check if PO exists in SAP
    sap = SAPIntegration()
    po_data = sap.get_purchase_order(po_number)
    
    if not po_data:
        flash('Purchase Order not found in SAP B1.', 'error')
        return redirect(url_for('grpo'))
    
    # Check if PO has open lines
    document_lines = po_data.get('DocumentLines', [])
    has_open_lines = False
    
    logging.info(f"Validating PO {po_number}: Found {len(document_lines)} line items")
    
    for line in document_lines:
        line_status = line.get('LineStatus', '')
        # Check both possible field names for open quantity
        open_quantity = line.get('RemainingOpenQuantity', line.get('OpenQuantity', 0))
        quantity = line.get('Quantity', 0)
        item_code = line.get('ItemCode', 'Unknown')
        
        logging.info(f"Line {line.get('LineNum', '?')} - Item: {item_code}, Status: '{line_status}', OpenQty: {open_quantity}, Qty: {quantity}")
        
        # Check if line is open (not closed) and has open quantity
        # Also handle cases where LineStatus might be missing (offline mode)
        # In offline mode, assume lines are open if they have positive open quantity
        is_line_open = (line_status == 'bost_Open' or 
                       (line_status == '' and open_quantity > 0) or
                       (line_status == '' and quantity > 0))
        
        if is_line_open and open_quantity > 0:
            has_open_lines = True
            logging.info(f"Found open line: {item_code} with open quantity {open_quantity}")
            break
    
    if not has_open_lines:
        if document_lines:
            flash('Purchase Order has no open lines available for receipt. All lines are either closed or fully received.', 'error')
        else:
            flash('Purchase Order has no line items.', 'error')
        return redirect(url_for('grpo'))
    
    # Parse SAP date safely (handles both ISO format and simple date format)
    po_date = datetime.utcnow()
    if po_data.get('DocDate'):
        date_str = po_data.get('DocDate')
        try:
            # Try ISO format first (SAP B1 format: 2025-01-08T00:00:00Z)
            if 'T' in date_str:
                po_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                # Simple date format
                po_date = datetime.strptime(date_str, '%Y-%m-%d')
        except (ValueError, TypeError) as e:
            logging.warning(f"Could not parse PO date '{date_str}': {e}")
            po_date = datetime.utcnow()

    # Create GRPO document with PO details
    grpo_doc = GRPODocument(
        po_number=po_number,
        supplier_code=po_data.get('CardCode'),
        supplier_name=po_data.get('CardName'),
        po_date=po_date,
        po_total=po_data.get('DocTotal', 0),
        user_id=current_user.id,
        draft_or_post=request.form.get('draft_or_post', 'draft')
    )
    db.session.add(grpo_doc)
    db.session.commit()
    
    flash(f'GRPO created successfully for PO {po_number}!', 'success')
    return redirect(url_for('grpo_detail', grpo_id=grpo_doc.id))

@app.route('/grpo/<int:grpo_id>')
@login_required
def grpo_detail(grpo_id):
    try:
        grpo_doc = GRPODocument.query.get_or_404(grpo_id)
        
        # Get PO items from SAP
        sap = SAPIntegration()
        po_items = sap.get_purchase_order_items(grpo_doc.po_number)
    except Exception as e:
        logging.error(f"Database error in grpo_detail: {e}")
        flash('Database needs to be updated. Please run: python reset_database.py', 'error')
        return redirect(url_for('grpo'))
    
    return render_template('grpo_detail.html', grpo_doc=grpo_doc, po_items=po_items)

@app.route('/grpo/<int:grpo_id>/add_item', methods=['POST'])
@login_required
def add_grpo_item(grpo_id):
    try:
        grpo_doc = GRPODocument.query.get_or_404(grpo_id)
    except Exception as e:
        logging.error(f"Database error in add_grpo_item: {e}")
        flash('Database needs to be updated. Please run: python reset_database.py', 'error')
        return redirect(url_for('grpo'))
    
    item_code = request.form['item_code']
    quantity = float(request.form['quantity'])
    warehouse_code = request.form['warehouse_code']
    bin_location = request.form.get('bin_location') or f"{warehouse_code}-BIN-01"
    batch_number = request.form.get('batch_number')
    serial_number = request.form.get('serial_number')
    
    # Get PO line item details if available
    sap = SAPIntegration()
    po_items = sap.get_purchase_order_items(grpo_doc.po_number)
    
    # Find matching PO line item
    po_line_item = None
    for po_item in po_items:
        if po_item.get('ItemCode') == item_code:
            po_line_item = po_item
            break
    
    # Generate barcode if not provided
    generated_barcode = None
    if not request.form.get('barcode'):
        import secrets
        random_suffix = secrets.token_hex(4).upper()
        generated_barcode = f"WMS-{item_code}-{random_suffix}"
    
    # Create GRPO item with enhanced details
    grpo_item = GRPOItem(
        grpo_document_id=grpo_doc.id,
        po_line_number=po_line_item.get('LineNum') if po_line_item else None,
        item_code=item_code,
        item_name=request.form['item_name'],
        po_quantity=po_line_item.get('Quantity') if po_line_item else quantity,
        open_quantity=po_line_item.get('OpenQuantity') if po_line_item else quantity,
        received_quantity=quantity,
        unit_of_measure=po_line_item.get('UoMCode') or po_line_item.get('UoMEntry') or request.form.get('unit_of_measure', 'EA'),
        unit_price=po_line_item.get('Price') if po_line_item else 0,
        bin_location=bin_location,
        batch_number=batch_number,
        serial_number=serial_number,
        expiration_date=datetime.strptime(request.form['expiration_date'], '%Y-%m-%d') if request.form.get('expiration_date') else None,
        supplier_barcode=request.form.get('barcode'),
        generated_barcode=generated_barcode
    )
    db.session.add(grpo_item)
    db.session.commit()
    
    flash('Item added to GRPO successfully!', 'success')
    return redirect(url_for('grpo_detail', grpo_id=grpo_id))

@app.route('/grpo/<int:grpo_id>/submit', methods=['POST'])
@login_required
def submit_grpo(grpo_id):
    grpo_doc = GRPODocument.query.get_or_404(grpo_id)
    
    # Update status to submitted for QC approval
    grpo_doc.status = 'submitted'
    db.session.commit()
    
    flash('GRPO submitted for QC approval!', 'success')
    return redirect(url_for('grpo_detail', grpo_id=grpo_id))

@app.route('/grpo/<int:grpo_id>/approve', methods=['POST'])
@login_required
def approve_grpo(grpo_id):
    grpo_doc = GRPODocument.query.get_or_404(grpo_id)
    
    # Check if user has QC role
    if current_user.role not in ['qc', 'manager', 'admin']:
        flash('You do not have permission to approve GRPO documents.', 'error')
        return redirect(url_for('grpo_detail', grpo_id=grpo_id))
    
    # Get draft or post preference from form
    grpo_doc.draft_or_post = request.form.get('draft_or_post', 'draft')
    grpo_doc.qc_user_id = current_user.id
    grpo_doc.qc_notes = request.form.get('qc_notes', '')
    
    # Update all items QC status first
    for item in grpo_doc.items:
        item.qc_status = 'approved'
    
    # If user selected 'post', submit to SAP B1
    if grpo_doc.draft_or_post == 'post':
        logging.info("=" * 100)
        logging.info("🚀 POSTING GRPO TO SAP B1 - PURCHASE DELIVERY NOTE CREATION")
        logging.info("=" * 100)
        logging.info(f"📋 GRPO ID: {grpo_doc.id}")
        logging.info(f"📄 PO Number: {grpo_doc.po_number}")
        logging.info(f"👤 User: {current_user.username}")
        logging.info(f"🏢 Branch: {current_user.branch_id}")
        
        sap = SAPIntegration()
        result = sap.post_grpo_to_sap(grpo_doc)
        
        if result.get('success'):
            grpo_doc.status = 'posted'
            grpo_doc.sap_document_number = result.get('sap_document_number')
            logging.info("=" * 100)
            logging.info("✅ SUCCESS: GRPO POSTED TO SAP B1")
            logging.info(f"📄 SAP Document Number: {result.get('sap_document_number')}")
            logging.info("=" * 100)
            flash(f'GRPO approved and posted to SAP B1 successfully! SAP Document Number: {result.get("sap_document_number")}', 'success')
        else:
            grpo_doc.status = 'approved'  # Keep as approved even if SAP posting fails
            logging.error("=" * 100)
            logging.error("❌ FAILED: GRPO POSTING TO SAP B1 FAILED")
            logging.error(f"🚫 Error: {result.get('error')}")
            logging.error("=" * 100)
            flash(f'GRPO approved but failed to post to SAP B1: {result.get("error")}', 'warning')
    else:
        grpo_doc.status = 'approved'
        flash('GRPO approved successfully (saved as draft)', 'success')
    
    db.session.commit()
    return redirect(url_for('grpo_detail', grpo_id=grpo_id))

@app.route('/grpo/<int:grpo_id>/reject', methods=['POST'])
@login_required
def reject_grpo(grpo_id):
    grpo_doc = GRPODocument.query.get_or_404(grpo_id)
    
    # Check if user has QC role
    if current_user.role not in ['qc', 'manager', 'admin']:
        flash('You do not have permission to reject GRPO documents.', 'error')
        return redirect(url_for('grpo_detail', grpo_id=grpo_id))
    
    grpo_doc.status = 'rejected'
    grpo_doc.qc_user_id = current_user.id
    grpo_doc.qc_notes = request.form.get('qc_notes', '')
    db.session.commit()
    
    # Update all items QC status
    for item in grpo_doc.items:
        item.qc_status = 'rejected'
        item.qc_notes = request.form.get('qc_notes', '')
    db.session.commit()
    
    flash('GRPO rejected!', 'warning')
    return redirect(url_for('grpo_detail', grpo_id=grpo_id))

@app.route('/grpo/<int:grpo_id>/item/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_grpo_item(grpo_id, item_id):
    grpo_doc = GRPODocument.query.get_or_404(grpo_id)
    grpo_item = GRPOItem.query.get_or_404(item_id)
    
    # Check if user has permission to edit
    if grpo_doc.user_id != current_user.id and current_user.role not in ['manager', 'admin']:
        flash('You do not have permission to edit this item.', 'error')
        return redirect(url_for('grpo_detail', grpo_id=grpo_id))
    
    # Check if GRPO is still editable
    if grpo_doc.status not in ['draft', 'rejected']:
        flash('Cannot edit items in approved or posted GRPO.', 'error')
        return redirect(url_for('grpo_detail', grpo_id=grpo_id))
    
    if request.method == 'POST':
        # Update only the received quantity
        new_quantity = float(request.form.get('received_quantity', grpo_item.received_quantity))
        grpo_item.received_quantity = new_quantity
        
        # Update any other allowed fields
        if request.form.get('bin_location'):
            grpo_item.bin_location = request.form.get('bin_location')
        if request.form.get('batch_number'):
            grpo_item.batch_number = request.form.get('batch_number')
        if request.form.get('expiration_date'):
            grpo_item.expiration_date = datetime.strptime(request.form.get('expiration_date'), '%Y-%m-%d')
        
        db.session.commit()
        flash('Item updated successfully!', 'success')
        return redirect(url_for('grpo_detail', grpo_id=grpo_id))
    
    return render_template('edit_grpo_item.html', grpo_doc=grpo_doc, grpo_item=grpo_item)

@app.route('/grpo/item/<int:item_id>/update_field', methods=['POST'])
@login_required
def update_grpo_item_field(item_id):
    """Update a single field of a GRPO item via AJAX"""
    grpo_item = GRPOItem.query.get_or_404(item_id)
    grpo_doc = grpo_item.grpo_document
    
    # Check permissions
    if grpo_doc.user_id != current_user.id and current_user.role not in ['manager', 'admin']:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    # Check if editable
    if grpo_doc.status not in ['draft', 'rejected']:
        return jsonify({'success': False, 'error': 'Cannot edit approved or posted GRPO'}), 400
    
    try:
        field_name = request.json.get('field_name')
        field_value = request.json.get('field_value')
        
        if field_name == 'received_quantity':
            grpo_item.received_quantity = float(field_value) if field_value else 0
        elif field_name == 'batch_number':
            grpo_item.batch_number = field_value if field_value else None
        elif field_name == 'expiration_date':
            if field_value:
                grpo_item.expiration_date = datetime.strptime(field_value, '%Y-%m-%d')
            else:
                grpo_item.expiration_date = None
        elif field_name == 'generated_barcode':
            grpo_item.generated_barcode = field_value if field_value else None
        else:
            return jsonify({'success': False, 'error': 'Invalid field name'}), 400
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Field updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating GRPO item field: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/inventory_transfer')
@login_required
def inventory_transfer():
    transfers = InventoryTransfer.query.filter_by(user_id=current_user.id).order_by(InventoryTransfer.created_at.desc()).all()
    return render_template('inventory_transfer.html', transfers=transfers)

@app.route('/inventory_transfer/create', methods=['POST'])
@login_required
def create_inventory_transfer():
    transfer_request_number = request.form['transfer_request_number'].strip()
    
    if not transfer_request_number:
        flash('Please enter a transfer request number', 'error')
        return redirect(url_for('inventory_transfer'))
    
    # Check if transfer already exists
    existing_transfer = InventoryTransfer.query.filter_by(
        transfer_request_number=transfer_request_number,
        user_id=current_user.id
    ).first()
    
    if existing_transfer:
        flash(f'Transfer request {transfer_request_number} already exists for your account', 'warning')
        return redirect(url_for('inventory_transfer_detail', transfer_id=existing_transfer.id))
    
    # Validate transfer request with SAP B1
    sap = SAPIntegration()
    logging.info(f"🔍 Validating transfer request: {transfer_request_number}")
    transfer_data = sap.get_inventory_transfer_request(transfer_request_number)
    
    if not transfer_data:
        logging.error(f"❌ Transfer request {transfer_request_number} not found in SAP B1")
        flash(f'Transfer request {transfer_request_number} not found in SAP B1. Please verify the number and try again.', 'error')
        return redirect(url_for('inventory_transfer'))
    
    # Check document status - only allow open transfer requests
    doc_status = transfer_data.get('DocumentStatus', transfer_data.get('DocStatus', ''))
    if doc_status.lower() not in ['open', 'bost_open', 'o']:
        logging.error(f"❌ Transfer request {transfer_request_number} is not open. Status: {doc_status}")
        flash(f'Transfer request {transfer_request_number} is closed or not available for processing. Status: {doc_status}', 'error')
        return redirect(url_for('inventory_transfer'))
    
    # Check if there are any open line items
    stock_transfer_lines = transfer_data.get('StockTransferLines', [])
    open_lines = [line for line in stock_transfer_lines if line.get('LineStatus', '').lower() in ['open', 'bost_open', 'o'] or not line.get('LineStatus')]
    
    if not open_lines:
        logging.error(f"❌ Transfer request {transfer_request_number} has no open line items")
        flash(f'Transfer request {transfer_request_number} has no open line items available for processing.', 'error')
        return redirect(url_for('inventory_transfer'))
    
    # Extract warehouse information
    from_warehouse = transfer_data.get('FromWarehouse', '')
    to_warehouse = transfer_data.get('ToWarehouse', '')
    
    # Log transfer data for debugging
    logging.info(f"✅ Transfer request found: {transfer_data.get('DocNum')} - From: {from_warehouse} - To: {to_warehouse} - Open Lines: {len(open_lines)}")
    
    # Create inventory transfer with warehouse information
    transfer = InventoryTransfer(
        transfer_request_number=transfer_request_number,
        user_id=current_user.id,
        from_warehouse=from_warehouse,
        to_warehouse=to_warehouse,
        status='draft'
    )
    db.session.add(transfer)
    db.session.commit()
    
    flash(f'Inventory transfer {transfer_request_number} created successfully! From: {from_warehouse} → To: {to_warehouse} ({len(open_lines)} open lines)', 'success')
    return redirect(url_for('inventory_transfer_detail', transfer_id=transfer.id))

@app.route('/inventory_transfer/<int:transfer_id>', methods=['GET', 'POST'])
@login_required
def inventory_transfer_detail(transfer_id):
    transfer = InventoryTransfer.query.get_or_404(transfer_id)
    
    # Get available items from SAP transfer request (only open lines)
    available_items = []
    sap = SAPIntegration()
    
    if transfer.transfer_request_number:
        transfer_data = sap.get_inventory_transfer_request(transfer.transfer_request_number)
        if transfer_data and 'StockTransferLines' in transfer_data:
            # Filter only open line items
            all_lines = transfer_data['StockTransferLines']
            available_items = [line for line in all_lines if line.get('LineStatus', '').lower() in ['open', 'bost_open', 'o'] or not line.get('LineStatus')]
            logging.info(f"Found {len(available_items)} open items out of {len(all_lines)} total for transfer request {transfer.transfer_request_number}")
    
    # Handle adding items to transfer
    if request.method == 'POST':
        try:
            item_code = request.form['item_code']
            item_name = request.form['item_name']
            quantity = float(request.form['quantity'])
            unit_of_measure = request.form['unit_of_measure']
            from_warehouse_code = request.form['from_warehouse_code']
            to_warehouse_code = request.form['to_warehouse_code']
            from_bin = request.form['from_bin']
            to_bin = request.form['to_bin']
            batch_number = request.form.get('batch_number', '')
            
            # Get item details from SAP B1 to ensure correct UOM
            sap = SAPIntegration()
            item_details = sap.get_item_details(item_code)
            if item_details:
                actual_uom = item_details.get('InventoryUoM', unit_of_measure)
                logging.info(f"🔍 Item {item_code} UOM from SAP: {actual_uom}")
            else:
                actual_uom = unit_of_measure
                logging.warning(f"⚠️ Could not get UOM from SAP for item {item_code}, using form value: {unit_of_measure}")
            
            # Create new transfer item
            transfer_item = InventoryTransferItem(
                inventory_transfer_id=transfer.id,
                item_code=item_code,
                item_name=item_name,
                quantity=quantity,
                unit_of_measure=actual_uom,
                from_bin=from_bin,
                to_bin=to_bin,
                batch_number=batch_number if batch_number else None
            )
            
            db.session.add(transfer_item)
            db.session.commit()
            
            flash(f'Item {item_code} added to transfer successfully!', 'success')
            return redirect(url_for('inventory_transfer_detail', transfer_id=transfer_id))
            
        except Exception as e:
            logging.error(f"Error adding item to transfer: {str(e)}")
            flash(f'Error adding item: {str(e)}', 'error')
            return redirect(url_for('inventory_transfer_detail', transfer_id=transfer_id))
    
    return render_template('inventory_transfer_detail.html', transfer=transfer, available_items=available_items)

@app.route('/api/validate_transfer_request/<transfer_request_number>')
@login_required
def validate_transfer_request_api(transfer_request_number):
    """API endpoint to validate transfer request number"""
    try:
        sap = SAPIntegration()
        transfer_data = sap.get_inventory_transfer_request(transfer_request_number)
        
        if transfer_data:
            return jsonify({
                'success': True,
                'data': {
                    'DocNum': transfer_data.get('DocNum'),
                    'FromWarehouse': transfer_data.get('FromWarehouse'),
                    'ToWarehouse': transfer_data.get('ToWarehouse'),
                    'DocumentStatus': transfer_data.get('DocumentStatus', transfer_data.get('DocStatus')),
                    'LineCount': len(transfer_data.get('StockTransferLines', []))
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Transfer request {transfer_request_number} not found'
            })
    
    except Exception as e:
        logging.error(f"Error validating transfer request: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/inventory_transfer/<int:transfer_id>/submit', methods=['POST'])
@login_required
def submit_transfer(transfer_id):
    """Submit inventory transfer for QC approval"""
    try:
        transfer = InventoryTransfer.query.get_or_404(transfer_id)
        
        # Check if user owns this transfer
        if transfer.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Check if transfer has items
        if not transfer.items:
            return jsonify({'success': False, 'error': 'Cannot submit transfer without items'}), 400
        
        # Check if already submitted
        if transfer.status != 'draft':
            return jsonify({'success': False, 'error': 'Transfer already submitted'}), 400
        
        # Update transfer status to submitted for QC approval
        transfer.status = 'submitted'
        transfer.updated_at = datetime.utcnow()
        db.session.commit()
        
        logging.info(f"✅ Inventory Transfer {transfer_id} submitted for QC approval")
        return jsonify({
            'success': True, 
            'message': 'Transfer submitted for QC approval successfully',
            'status': 'submitted'
        })
        
    except Exception as e:
        logging.error(f"Error submitting transfer: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/inventory_transfer/<int:transfer_id>/qc_approve', methods=['POST'])
@login_required
def qc_approve_transfer(transfer_id):
    """QC approve inventory transfer and post to SAP B1"""
    try:
        transfer = InventoryTransfer.query.get_or_404(transfer_id)
        
        # Check if user has QC permissions
        if not current_user.has_permission('qc_dashboard') and current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'error': 'Access denied - QC permissions required'}), 403
        
        # Check if transfer is in submitted status
        if transfer.status != 'submitted':
            return jsonify({'success': False, 'error': 'Transfer must be submitted for QC approval'}), 400
        
        # Get QC notes from request
        qc_notes = request.json.get('qc_notes', '') if request.is_json else request.form.get('qc_notes', '')
        
        # Mark individual items as approved
        for item in transfer.items:
            item.qc_status = 'approved'
            
        # Submit to SAP B1
        sap = SAPIntegration()
        result = sap.create_inventory_transfer(transfer)
        
        if result.get('success'):
            # Update transfer status and SAP document number
            transfer.status = 'qc_approved'
            transfer.qc_approver_id = current_user.id
            transfer.qc_approved_at = datetime.utcnow()
            transfer.qc_notes = qc_notes
            transfer.sap_document_number = result.get('document_number')
            db.session.commit()
            
            logging.info(f"✅ Inventory Transfer {transfer_id} QC approved and posted to SAP B1 as document {result.get('document_number')}")
            return jsonify({
                'success': True, 
                'message': f'Transfer QC approved and posted to SAP B1 as document {result.get("document_number")}',
                'sap_document_number': result.get('document_number')
            })
        else:
            logging.error(f"❌ Failed to post transfer {transfer_id} to SAP B1: {result.get('error')}")
            return jsonify({'success': False, 'error': result.get('error')}), 500
        
    except Exception as e:
        logging.error(f"Error QC approving transfer: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/inventory_transfer/<int:transfer_id>/qc_reject', methods=['POST'])
@login_required
def qc_reject_transfer(transfer_id):
    """QC reject inventory transfer"""
    try:
        transfer = InventoryTransfer.query.get_or_404(transfer_id)
        
        # Check if user has QC permissions
        if not current_user.has_permission('qc_dashboard') and current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'error': 'Access denied - QC permissions required'}), 403
        
        # Check if transfer is in submitted status
        if transfer.status != 'submitted':
            return jsonify({'success': False, 'error': 'Transfer must be submitted for QC approval'}), 400
        
        # Get QC notes from request
        qc_notes = request.json.get('qc_notes', '') if request.is_json else request.form.get('qc_notes', '')
        
        # Mark individual items as rejected
        for item in transfer.items:
            item.qc_status = 'rejected'
            
        # Update transfer status
        transfer.status = 'rejected'
        transfer.qc_approver_id = current_user.id
        transfer.qc_approved_at = datetime.utcnow()
        transfer.qc_notes = qc_notes
        db.session.commit()
        
        logging.info(f"❌ Inventory Transfer {transfer_id} rejected by QC")
        return jsonify({
            'success': True, 
            'message': 'Transfer rejected by QC',
            'status': 'rejected'
        })
        
    except Exception as e:
        logging.error(f"Error rejecting transfer: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/inventory_transfer/<int:transfer_id>/reopen', methods=['POST'])
@login_required
def reopen_transfer(transfer_id):
    """Reopen a rejected inventory transfer"""
    try:
        transfer = InventoryTransfer.query.get_or_404(transfer_id)
        
        # Check if user owns the transfer or has admin permissions
        if transfer.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'error': 'Access denied - You can only reopen your own transfers'}), 403
        
        # Check if transfer is rejected
        if transfer.status != 'rejected':
            return jsonify({'success': False, 'error': 'Only rejected transfers can be reopened'}), 400
        
        # Reset transfer to draft status
        transfer.status = 'draft'
        transfer.qc_approver_id = None
        transfer.qc_approved_at = None
        transfer.qc_notes = None
        transfer.updated_at = datetime.utcnow()
        
        # Reset all items to pending
        for item in transfer.items:
            item.qc_status = 'pending'
            
        db.session.commit()
        
        logging.info(f"🔄 Inventory Transfer {transfer_id} reopened and reset to draft status")
        return jsonify({
            'success': True, 
            'message': 'Transfer reopened successfully. You can now edit and resubmit it.',
            'status': 'draft'
        })
        
    except Exception as e:
        logging.error(f"Error reopening transfer: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/qc_dashboard')
@login_required
def qc_dashboard():
    """QC Dashboard for approving transfers and GRPOs"""
    # Check QC permissions
    if not current_user.has_permission('qc_dashboard') and current_user.role not in ['admin', 'manager']:
        flash('Access denied - QC permissions required', 'error')
        return redirect(url_for('dashboard'))
    
    # Get pending transfers for QC approval
    pending_transfers = InventoryTransfer.query.filter_by(status='submitted').order_by(InventoryTransfer.created_at.desc()).all()
    
    # Get pending GRPOs for QC approval
    pending_grpos = GRPODocument.query.filter_by(status='submitted').order_by(GRPODocument.created_at.desc()).all()
    
    return render_template('qc_dashboard.html', 
                         pending_transfers=pending_transfers,
                         pending_grpos=pending_grpos)

@app.route('/pick_list')
@login_required
def pick_list():
    pick_lists = PickList.query.filter_by(user_id=current_user.id).order_by(PickList.created_at.desc()).all()
    return render_template('pick_list.html', pick_lists=pick_lists)

@app.route('/pick_list/<int:pick_list_id>')
@login_required
def pick_list_detail(pick_list_id):
    pick_list = PickList.query.get_or_404(pick_list_id)
    return render_template('pick_list_detail.html', pick_list=pick_list)

@app.route('/create_pick_list', methods=['POST'])
@login_required
def create_pick_list():
    sales_order_number = request.form.get('sales_order_number')
    pick_list_number = request.form.get('pick_list_number')
    
    if not sales_order_number or not pick_list_number:
        flash('Sales order number and pick list number are required', 'error')
        return redirect(url_for('pick_list'))
    
    # Create new pick list
    pick_list = PickList(
        sales_order_number=sales_order_number,
        pick_list_number=pick_list_number,
        user_id=current_user.id,
        status='pending'
    )
    
    db.session.add(pick_list)
    db.session.commit()
    
    flash('Pick list created successfully', 'success')
    return redirect(url_for('pick_list_detail', pick_list_id=pick_list.id))

@app.route('/pick_list/<int:pick_list_id>/approve', methods=['POST'])
@login_required
def approve_pick_list(pick_list_id):
    pick_list = PickList.query.get_or_404(pick_list_id)
    
    if current_user.role in ['admin', 'manager']:
        pick_list.status = 'approved'
        pick_list.approver_id = current_user.id
        db.session.commit()
        flash('Pick list approved successfully!', 'success')
    else:
        flash('You do not have permission to approve pick lists.', 'error')
    
    return redirect(url_for('pick_list_detail', pick_list_id=pick_list_id))

@app.route('/pick_list/<int:pick_list_id>/reject', methods=['POST'])
@login_required
def reject_pick_list(pick_list_id):
    pick_list = PickList.query.get_or_404(pick_list_id)
    
    if current_user.role in ['admin', 'manager']:
        pick_list.status = 'rejected'
        pick_list.approver_id = current_user.id
        db.session.commit()
        return jsonify({'success': True, 'message': 'Pick list rejected successfully'})
    else:
        return jsonify({'success': False, 'message': 'You do not have permission to reject pick lists'}), 403

@app.route('/inventory_counting')
@login_required
def inventory_counting():
    counts = InventoryCount.query.filter_by(user_id=current_user.id).order_by(InventoryCount.created_at.desc()).all()
    return render_template('inventory_counting.html', counts=counts)

@app.route('/inventory_counting/<int:count_id>')
@login_required
def inventory_counting_detail(count_id):
    count = InventoryCount.query.get_or_404(count_id)
    return render_template('inventory_counting_detail.html', count=count)

@app.route('/create_count_task', methods=['POST'])
@login_required
def create_count_task():
    count_number = request.form.get('count_number')
    warehouse_code = request.form.get('warehouse_code')
    bin_location = request.form.get('bin_location')
    
    if not count_number or not warehouse_code or not bin_location:
        flash('All fields are required', 'error')
        return redirect(url_for('inventory_counting'))
    
    # Create new count task
    count = InventoryCount(
        count_number=count_number,
        warehouse_code=warehouse_code,
        bin_location=bin_location,
        user_id=current_user.id,
        status='assigned'
    )
    
    db.session.add(count)
    db.session.commit()
    
    flash('Count task created successfully', 'success')
    return redirect(url_for('inventory_counting'))

@app.route('/inventory_counting/<int:count_id>/start', methods=['POST'])
@login_required
def start_count_task(count_id):
    count = InventoryCount.query.get_or_404(count_id)
    
    if count.user_id != current_user.id:
        flash('You can only start your own count tasks', 'error')
        return redirect(url_for('inventory_counting'))
    
    count.status = 'in_progress'
    db.session.commit()
    
    flash('Count task started', 'success')
    return redirect(url_for('inventory_counting_detail', count_id=count_id))

@app.route('/inventory_counting/<int:count_id>/complete', methods=['POST'])
@login_required
def complete_count_task(count_id):
    count = InventoryCount.query.get_or_404(count_id)
    
    if count.user_id != current_user.id:
        flash('You can only complete your own count tasks', 'error')
        return redirect(url_for('inventory_counting'))
    
    count.status = 'completed'
    db.session.commit()
    
    flash('Count task completed successfully', 'success')
    return redirect(url_for('inventory_counting'))

@app.route('/api/pending_approvals')
@login_required
def get_pending_approvals():
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    pending_pick_lists = PickList.query.filter_by(status='pending').all()
    
    data = []
    for pick_list in pending_pick_lists:
        data.append({
            'id': pick_list.id,
            'pick_list_number': pick_list.pick_list_number,
            'sales_order_number': pick_list.sales_order_number,
            'user_name': f"{pick_list.user.first_name} {pick_list.user.last_name}",
            'created_at': pick_list.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify({'pending_approvals': data})

@app.route('/bin_scanning')
@login_required
def bin_scanning():
    return render_template('bin_scanning.html')

@app.route('/api/scan_bin', methods=['POST'])
@login_required
def scan_bin():
    bin_code = request.json['bin_code']
    
    # Get items from SAP B1
    sap = SAPIntegration()
    items = sap.get_bin_items(bin_code)
    
    return jsonify({'items': items})

@app.route('/label_printing')
@login_required
def label_printing():
    return render_template('label_printing.html')

@app.route('/api/print_label', methods=['POST'])
@login_required
def print_label():
    data = request.get_json()
    if not data or 'item_code' not in data:
        return jsonify({'error': 'item_code is required'}), 400
    
    item_code = data['item_code']
    label_format = data.get('label_format', 'standard')
    
    # Generate barcode with proper WMS format
    import secrets
    random_suffix = secrets.token_hex(4).upper()
    barcode = f"WMS-{item_code}-{random_suffix}"
    
    # Save to database
    label = BarcodeLabel(
        item_code=item_code,
        barcode=barcode,
        label_format=label_format,
        print_count=1,
        last_printed=datetime.utcnow()
    )
    db.session.add(label)
    db.session.commit()
    
    return jsonify({'success': True, 'barcode': barcode})

@app.route('/barcode_reprint')
@login_required
def barcode_reprint():
    labels = BarcodeLabel.query.order_by(BarcodeLabel.last_printed.desc()).all()
    return render_template('barcode_reprint.html', labels=labels)

@app.route('/api/reprint_label', methods=['POST'])
@login_required
def reprint_label():
    label_id = request.json['label_id']
    
    label = BarcodeLabel.query.get_or_404(label_id)
    label.print_count += 1
    label.last_printed = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True, 'barcode': label.barcode})

@app.route('/api/generate_barcode', methods=['POST'])
@login_required
def generate_barcode_api():
    """Generate new barcode for item"""
    data = request.get_json()
    if not data or 'item_code' not in data:
        return jsonify({'error': 'item_code is required'}), 400
    
    item_code = data['item_code']
    
    # Generate barcode with proper WMS format
    import secrets
    random_suffix = secrets.token_hex(4).upper()
    barcode = f"WMS-{item_code}-{random_suffix}"
    
    return jsonify({'success': True, 'barcode': barcode})

# Duplicate route removed - using existing update_grpo_item_field function

@app.route('/user_management')
@login_required
def user_management():
    if not current_user.has_permission('user_management'):
        flash('Access denied. You do not have permission to manage users.', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    branches = db.session.execute(db.text("SELECT id, name FROM branches WHERE is_active = TRUE ORDER BY name")).fetchall()
    return render_template('user_management.html', users=users, branches=branches)

@app.route('/user_management/create', methods=['POST'])
@login_required
def create_user():
    if not current_user.has_permission('user_management'):
        flash('You do not have permission to create users.', 'error')
        return redirect(url_for('dashboard'))
    
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    role = request.form['role']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    default_branch_id = request.form.get('default_branch_id')
    must_change_password = 'must_change_password' in request.form
    
    # Check if user exists
    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'error')
        return redirect(url_for('user_management'))
    
    if User.query.filter_by(email=email).first():
        flash('Email already exists.', 'error')
        return redirect(url_for('user_management'))
    
    # Create user
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        first_name=first_name,
        last_name=last_name,
        role=role,
        default_branch_id=default_branch_id if default_branch_id else None,
        must_change_password=must_change_password
    )
    
    # Set custom permissions if provided
    permissions = {}
    for screen in ['dashboard', 'grpo', 'inventory_transfer', 'pick_list', 'inventory_counting', 
                   'bin_scanning', 'label_printing', 'user_management', 'qc_dashboard']:
        permissions[screen] = screen in request.form
    
    user.set_permissions(permissions)
    
    db.session.add(user)
    db.session.commit()
    
    flash(f'User {username} created successfully!', 'success')
    return redirect(url_for('user_management'))

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.has_permission('user_management'):
        flash('Access denied. You do not have permission to edit users.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.email = request.form['email']
        user.role = request.form['role']
        user.default_branch_id = request.form.get('default_branch_id') or None
        user.is_active = 'is_active' in request.form
        user.must_change_password = 'must_change_password' in request.form
        
        # Update permissions
        permissions = {}
        for screen in ['dashboard', 'grpo', 'inventory_transfer', 'pick_list', 'inventory_counting', 
                       'bin_scanning', 'label_printing', 'user_management', 'qc_dashboard']:
            permissions[screen] = screen in request.form
        
        user.set_permissions(permissions)
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash(f'User {user.username} updated successfully!', 'success')
        return redirect(url_for('user_management'))
    
    branches = db.session.execute(db.text("SELECT id, name FROM branches WHERE is_active = TRUE ORDER BY name")).fetchall()
    return render_template('edit_user.html', user=user, branches=branches)

@app.route('/reset_password/<int:user_id>', methods=['POST'])
@login_required
def reset_password(user_id):
    if not current_user.has_permission('user_management'):
        flash('Access denied. You do not have permission to reset passwords.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    new_password = request.form['new_password']
    
    user.password_hash = generate_password_hash(new_password)
    user.must_change_password = True  # Force user to change password on next login
    user.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'Password reset for user {user.username}. They must change it on next login.', 'success')
    return redirect(url_for('user_management'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Current password is incorrect.', 'error')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('change_password.html')
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('change_password.html')
        
        current_user.password_hash = generate_password_hash(new_password)
        current_user.must_change_password = False
        current_user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('change_password.html')

@app.route('/branch_management')
@login_required
def branch_management():
    if current_user.role != 'admin':
        flash('Access denied. Only administrators can manage branches.', 'error')
        return redirect(url_for('dashboard'))
    
    branches = db.session.execute(db.text("SELECT * FROM branches ORDER BY name")).fetchall()
    return render_template('branch_management.html', branches=branches)

@app.route('/create_branch', methods=['POST'])
@login_required
def create_branch():
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    branch_id = request.form['branch_id'].upper()
    name = request.form['name']
    address = request.form.get('address', '')
    phone = request.form.get('phone', '')
    email = request.form.get('email', '')
    manager_name = request.form.get('manager_name', '')
    is_default = 'is_default' in request.form
    
    # Check if branch exists
    existing = db.session.execute(db.text("SELECT id FROM branches WHERE id = :id"), {"id": branch_id}).fetchone()
    if existing:
        flash('Branch ID already exists.', 'error')
        return redirect(url_for('branch_management'))
    
    # If this is the new default, remove default from others
    if is_default:
        db.session.execute(db.text("UPDATE branches SET is_default = FALSE"))
    
    # Insert new branch
    db.session.execute(db.text("""
        INSERT INTO branches (id, name, address, phone, email, manager_name, is_default, is_active)
        VALUES (:id, :name, :address, :phone, :email, :manager_name, :is_default, TRUE)
    """), {
        "id": branch_id,
        "name": name, 
        "address": address,
        "phone": phone,
        "email": email,
        "manager_name": manager_name,
        "is_default": is_default
    })
    
    db.session.commit()
    flash(f'Branch {name} created successfully!', 'success')
    return redirect(url_for('branch_management'))

# API endpoints for barcode scanning
@app.route('/api/validate_po', methods=['POST'])
@login_required
def validate_po():
    po_number = request.json['po_number']
    
    sap = SAPIntegration()
    po_data = sap.get_purchase_order(po_number)
    
    if po_data:
        return jsonify({'valid': True, 'po_data': po_data})
    else:
        return jsonify({'valid': False, 'error': 'Purchase Order not found'})

@app.route('/api/validate_item', methods=['POST'])
@login_required
def validate_item():
    item_code = request.json['item_code']
    
    sap = SAPIntegration()
    item_data = sap.get_item_master(item_code)
    
    if item_data:
        return jsonify({'valid': True, 'item_data': item_data})
    else:
        return jsonify({'valid': False, 'error': 'Item not found'})

@app.route('/api/get_bins', methods=['GET'])
@login_required
def get_bins():
    warehouse = request.args.get('warehouse')
    
    sap = SAPIntegration()
    bins = sap.get_warehouse_bins(warehouse)
    
    return jsonify({'bins': bins})

# Enhanced GRPO API routes

@app.route('/api/scan_po', methods=['POST'])
@login_required
def scan_po():
    """API endpoint for PO barcode scanning"""
    po_number = request.json.get('po_number')
    
    sap = SAPIntegration()
    po_data = sap.get_purchase_order(po_number)
    
    if po_data:
        return jsonify({
            'success': True,
            'po_data': {
                'po_number': po_data.get('DocNum'),
                'supplier_code': po_data.get('CardCode'),
                'supplier_name': po_data.get('CardName'),
                'po_date': po_data.get('DocDate'),
                'total': po_data.get('DocTotal'),
                'items': po_data.get('DocumentLines', [])
            }
        })
    else:
        return jsonify({'success': False, 'error': 'PO not found'})

@app.route('/api/scan_barcode', methods=['POST'])
@login_required  
def scan_barcode():
    """API endpoint for supplier barcode scanning"""
    barcode = request.json.get('barcode')
    
    # This would integrate with a barcode lookup service or database
    # For now, return mock data
    return jsonify({
        'success': True,
        'item_data': {
            'item_code': 'ITM001',
            'batch_number': 'BTH2025001',
            'expiration_date': '2025-12-31',
            'serial_number': barcode
        }
    })

# Duplicate generate_barcode_api route removed to prevent conflicts

@app.route('/api/print_barcode', methods=['POST'])
@login_required
def print_barcode_api():
    """Print barcode and mark as printed"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        barcode = data.get('barcode')
        item_id = data.get('item_id')
        
        if not barcode:
            return jsonify({'error': 'barcode is required'}), 400
        
        # Update GRPO item print status if item_id provided
        if item_id:
            grpo_item = GRPOItem.query.get(item_id)
            if grpo_item and grpo_item.generated_barcode == barcode:
                grpo_item.barcode_printed = True
                db.session.commit()
        
        # Update barcode label print count
        label = BarcodeLabel.query.filter_by(barcode=barcode).first()
        if label:
            label.print_count += 1
            label.last_printed = datetime.utcnow()
            db.session.commit()
        
        # In a real system, this would send to a label printer
        # For now, we'll return success with barcode data
        return jsonify({
            'success': True,
            'message': f'Printing barcode: {barcode}',
            'barcode': barcode
        })
        
    except Exception as e:
        logging.error(f"Error printing barcode: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/post_grpo_to_sap/<int:grpo_id>', methods=['POST'])
@login_required
def post_grpo_to_sap_manual(grpo_id):
    """Manually post approved GRPO to SAP B1"""
    try:
        # Get GRPO document
        grpo_doc = GRPODocument.query.get_or_404(grpo_id)
        
        # Check if user has permission to post
        if current_user.role not in ['admin', 'manager']:
            flash('Access denied. Only managers and admins can post to SAP B1.', 'error')
            return redirect(url_for('grpo_detail', grpo_id=grpo_id))
        
        # Check if GRPO is approved
        if grpo_doc.status != 'approved':
            flash('GRPO must be approved before posting to SAP B1.', 'error')
            return redirect(url_for('grpo_detail', grpo_id=grpo_id))
        
        # Check if already posted
        if grpo_doc.sap_document_number:
            flash(f'GRPO already posted to SAP B1 as document {grpo_doc.sap_document_number}.', 'warning')
            return redirect(url_for('grpo_detail', grpo_id=grpo_id))
        
        # Post to SAP B1
        logging.info("=" * 100)
        logging.info("🔄 MANUAL POSTING GRPO TO SAP B1")
        logging.info("=" * 100)
        logging.info(f"📋 GRPO ID: {grpo_doc.id}")
        logging.info(f"📄 PO Number: {grpo_doc.po_number}")
        logging.info(f"👤 Manual Post User: {current_user.username}")
        
        sap = SAPIntegration()
        result = sap.post_grpo_to_sap(grpo_doc)
        
        if result.get('success'):
            logging.info("=" * 100)
            logging.info("✅ SUCCESS: MANUAL GRPO POSTED TO SAP B1")
            logging.info(f"📄 SAP Document Number: {result.get('sap_document_number')}")
            logging.info("=" * 100)
            flash(f'GRPO successfully posted to SAP B1 as Purchase Delivery Note {result.get("sap_document_number")}.', 'success')
        else:
            logging.error("=" * 100)
            logging.error("❌ FAILED: MANUAL GRPO POSTING TO SAP B1 FAILED")
            logging.error(f"🚫 Error: {result.get('error')}")
            logging.error("=" * 100)
            flash(f'Error posting GRPO to SAP B1: {result.get("error")}', 'error')
        
        return redirect(url_for('grpo_detail', grpo_id=grpo_id))
        
    except Exception as e:
        logging.error(f"Error in post_grpo_to_sap_manual: {str(e)}")
        flash(f'Error posting GRPO to SAP B1: {str(e)}', 'error')
        return redirect(url_for('grpo_detail', grpo_id=grpo_id))

@app.route('/api/validate_transfer_request', methods=['POST'])
@login_required
def validate_transfer_request():
    """Validate transfer request number from SAP B1"""
    data = request.get_json()
    request_number = data.get('request_number')
    
    if not request_number:
        return jsonify({'valid': False, 'error': 'Transfer request number is required'})
    
    try:
        # Check SAP B1 for the transfer request
        sap = SAPIntegration()
        transfer_data = sap.get_inventory_transfer_request(request_number)
        
        if transfer_data:
            items_count = len(transfer_data.get('StockTransferLines', []))
            return jsonify({
                'valid': True,
                'transfer_data': transfer_data,
                'items_count': items_count,
                'from_warehouse': transfer_data.get('FromWarehouse', ''),
                'to_warehouse': transfer_data.get('ToWarehouse', ''),
                'status': transfer_data.get('DocStatus', '')
            })
        else:
            return jsonify({'valid': False, 'error': 'Transfer request not found in SAP B1'})
    except Exception as e:
        logging.error(f"Error validating transfer request: {str(e)}")
        return jsonify({'valid': False, 'error': f'Error validating transfer request: {str(e)}'})

@app.route('/inventory_transfer/<int:transfer_id>/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_transfer_item(transfer_id, item_id):
    """Delete an item from inventory transfer"""
    try:
        transfer = InventoryTransfer.query.get_or_404(transfer_id)
        
        # Check if user owns this transfer
        if transfer.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
            
        # Check if transfer is still in draft status
        if transfer.status != 'draft':
            return jsonify({'success': False, 'error': 'Cannot delete items from submitted transfer'}), 400
        
        # Find and delete the item
        item = InventoryTransferItem.query.filter_by(
            id=item_id, 
            inventory_transfer_id=transfer_id
        ).first()
        
        if not item:
            return jsonify({'success': False, 'error': 'Item not found'}), 404
            
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Item deleted successfully'})
        
    except Exception as e:
        logging.error(f"Error deleting transfer item: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/inventory_transfer/<int:transfer_id>/item/<int:item_id>/edit', methods=['POST'])
@login_required
def edit_transfer_item(transfer_id, item_id):
    """Edit an item in inventory transfer"""
    try:
        transfer = InventoryTransfer.query.get_or_404(transfer_id)
        
        # Check if user owns this transfer
        if transfer.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
            
        # Check if transfer is still in draft status
        if transfer.status != 'draft':
            return jsonify({'success': False, 'error': 'Cannot edit items in submitted transfer'}), 400
        
        # Find the item
        item = InventoryTransferItem.query.filter_by(
            id=item_id, 
            inventory_transfer_id=transfer_id
        ).first()
        
        if not item:
            return jsonify({'success': False, 'error': 'Item not found'}), 404
        
        # Update item fields
        data = request.get_json()
        item.quantity = float(data.get('quantity', item.quantity))
        item.from_bin = data.get('from_bin', item.from_bin)
        item.to_bin = data.get('to_bin', item.to_bin)
        item.batch_number = data.get('batch_number', item.batch_number) or None
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Item updated successfully'})
        
    except Exception as e:
        logging.error(f"Error editing transfer item: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bins', methods=['GET'])
@login_required
def get_bins_api():
    """API endpoint to get available bins from SAP B1"""
    warehouse_code = request.args.get('warehouse_code')
    
    if not warehouse_code:
        return jsonify({'error': 'warehouse_code parameter is required'}), 400
    
    try:
        # Get bins from SAP B1 if available
        from sap_integration import SAPIntegration
        sap_integration = SAPIntegration()
        bins = sap_integration.get_bins(warehouse_code)
        
        # If SAP is not available, return fallback bins
        if not bins:
            bins = [
                {'BinCode': f'{warehouse_code}-A1-01', 'Description': 'Aisle A, Level 1, Position 1'},
                {'BinCode': f'{warehouse_code}-A1-02', 'Description': 'Aisle A, Level 1, Position 2'},
                {'BinCode': f'{warehouse_code}-A2-01', 'Description': 'Aisle A, Level 2, Position 1'},
                {'BinCode': f'{warehouse_code}-B1-01', 'Description': 'Aisle B, Level 1, Position 1'},
                {'BinCode': f'{warehouse_code}-B1-02', 'Description': 'Aisle B, Level 1, Position 2'},
            ]
        
        return jsonify({'bins': bins})
        
    except Exception as e:
        logging.error(f"Error fetching bins: {str(e)}")
        # Return fallback bins for error cases
        fallback_bins = [
            {'BinCode': f'{warehouse_code}-A1-01', 'Description': 'Aisle A, Level 1, Position 1'},
            {'BinCode': f'{warehouse_code}-A1-02', 'Description': 'Aisle A, Level 1, Position 2'},
            {'BinCode': f'{warehouse_code}-A2-01', 'Description': 'Aisle A, Level 2, Position 1'},
            {'BinCode': f'{warehouse_code}-B1-01', 'Description': 'Aisle B, Level 1, Position 1'},
            {'BinCode': f'{warehouse_code}-B1-02', 'Description': 'Aisle B, Level 1, Position 2'},
        ]
        return jsonify({'bins': fallback_bins})

@app.route('/sync-sap-data', methods=['POST'])
@login_required
def sync_sap_data():
    """Sync master data from SAP B1"""
    if current_user.role not in ['admin', 'manager']:
        flash('You do not have permission to sync SAP data', 'error')
        return redirect(url_for('dashboard'))
    
    from sap_integration import SAPIntegration
    sap_integration = SAPIntegration()
    results = sap_integration.sync_all_master_data()
    
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    if success_count == total_count:
        flash(f'SAP master data synchronized successfully! ({success_count}/{total_count} completed)', 'success')
    elif success_count > 0:
        flash(f'SAP master data partially synchronized ({success_count}/{total_count} completed)', 'warning')
    else:
        flash('Failed to synchronize SAP master data. Check SAP connection.', 'error')
    
    return redirect(url_for('dashboard'))

# Duplicate route removed - using the one defined earlier

# Default admin user is created in app.py during initialization

@app.route('/api/grpo/<int:grpo_id>/preview_json')
@login_required
def preview_grpo_json(grpo_id):
    """Preview the JSON that will be posted to SAP B1"""
    try:
        grpo_doc = GRPODocument.query.get_or_404(grpo_id)
        
        # Generate the same JSON that would be posted to SAP B1
        sap = SAPIntegration()
        
        # Get PO data
        po_data = sap.get_purchase_order(grpo_doc.po_number)
        if not po_data:
            return jsonify({'success': False, 'error': 'PO data not found'})
        
        # Build the Purchase Delivery Note JSON structure using PO dates
        card_code = po_data.get('CardCode')
        po_doc_entry = po_data.get('DocEntry')
        
        # Use PO dates in correct format (YYYY-MM-DD, not with time)
        doc_date = po_data.get('DocDate', '2024-02-24')
        doc_due_date = po_data.get('DocDueDate', '2024-03-05')
        
        # Ensure dates are in YYYY-MM-DD format (remove time if present)
        if 'T' in doc_date:
            doc_date = doc_date.split('T')[0]
        if 'T' in doc_due_date:
            doc_due_date = doc_due_date.split('T')[0]
        
        # Generate external reference
        external_ref = sap.generate_external_reference_number(grpo_doc)
        
        # Get BusinessPlaceID from PO DocumentLines instead of bin location
        first_warehouse_code = None
        if grpo_doc.items:
            for item in grpo_doc.items:
                if item.qc_status == 'approved':
                    # Find matching PO line to get proper warehouse code
                    for po_line in po_data.get('DocumentLines', []):
                        if po_line.get('ItemCode') == item.item_code:
                            first_warehouse_code = po_line.get('WarehouseCode') or po_line.get('WhsCode')
                            if first_warehouse_code:
                                break
                    if first_warehouse_code:
                        break
        
        business_place_id = sap.get_warehouse_business_place_id(first_warehouse_code) if first_warehouse_code else 5
        
        # Build document lines
        document_lines = []
        line_number = 0
        
        for item in grpo_doc.items:
            if item.qc_status != 'approved':
                continue
                
            # Find matching PO line
            po_line_num = None
            for po_line in po_data.get('DocumentLines', []):
                if po_line.get('ItemCode') == item.item_code:
                    po_line_num = po_line.get('LineNum')
                    break
            
            if po_line_num is None:
                continue
            
            # Get exact warehouse code from PO line instead of bin location
            po_warehouse_code = None
            for po_line in po_data.get('DocumentLines', []):
                if po_line.get('ItemCode') == item.item_code:
                    po_warehouse_code = po_line.get('WarehouseCode') or po_line.get('WhsCode')
                    break
            
            # Use PO warehouse code, or fallback to extracted from bin location
            warehouse_code = po_warehouse_code or (item.bin_location.split('-')[0] if '-' in item.bin_location else item.bin_location[:4])
            
            # Build line
            line = {
                "BaseType": 22,
                "BaseEntry": po_doc_entry,
                "BaseLine": po_line_num,
                "ItemCode": item.item_code,
                "Quantity": item.received_quantity,
                "WarehouseCode": warehouse_code
            }
            
            # Add batch information if available
            if item.batch_number:
                # Format expiry date properly
                expiry_date = doc_date + "T00:00:00Z"  # Default to PO date
                if item.expiration_date:
                    if hasattr(item.expiration_date, 'strftime'):
                        expiry_date = item.expiration_date.strftime('%Y-%m-%dT%H:%M:%SZ')
                    else:
                        # If it's a string, ensure proper format
                        expiry_date = str(item.expiration_date)
                        if 'T' not in expiry_date:
                            expiry_date += "T00:00:00Z"
                
                batch_info = {
                    "BatchNumber": item.batch_number,
                    "Quantity": item.received_quantity,
                    "BaseLineNumber": line_number,
                    "ManufacturerSerialNumber": getattr(item, 'manufacturer_serial', None) or "MFG-SN-001",
                    "InternalSerialNumber": getattr(item, 'internal_serial', None) or "INT-SN-001",
                    "ExpiryDate": expiry_date
                }
                line["BatchNumbers"] = [batch_info]
            
            document_lines.append(line)
            line_number += 1
        
        # Build complete JSON structure
        pdn_data = {
            "CardCode": card_code,
            "DocDate": doc_date,
            "DocDueDate": doc_due_date,
            "Comments": grpo_doc.notes or "Auto-created from PO after QC",
            "NumAtCard": external_ref,
            "BPL_IDAssignedToInvoice": business_place_id,
            "DocumentLines": document_lines
        }
        
        # Log the complete JSON structure for debugging
        logging.info(f"🔍 JSON Preview Generated for GRPO {grpo_id}:")
        logging.info(f"📊 PO Number: {grpo_doc.po_number}")
        logging.info(f"📋 Total Lines: {len(document_lines)}")
        logging.info("=" * 80)
        logging.info("🏗️ COMPLETE JSON STRUCTURE TO BE POSTED TO SAP B1:")
        logging.info("=" * 80)
        print(json.dumps(pdn_data, indent=2, default=str))
        logging.info("=" * 80)
        logging.info("📤 END OF JSON STRUCTURE")
        logging.info("=" * 80)
        
        return jsonify({
            'success': True,
            'json_data': pdn_data,
            'grpo_id': grpo_id,
            'po_number': grpo_doc.po_number,
            'total_lines': len(document_lines)
        })
        
    except Exception as e:
        logging.error(f"❌ Error generating JSON preview: {str(e)}")
        import traceback
        logging.error(f"🔍 Full traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)})
