#!/usr/bin/env python3
"""
Update all GRPO references to GRN in routes.py file
This script will systematically replace all GRPO terminology with GRN
"""

import re

def update_routes_file():
    """Update routes.py to change GRPO to GRN"""
    
    try:
        with open('routes.py', 'r') as f:
            content = f.read()
        
        print("📝 Updating routes.py - GRPO to GRN references...")
        
        # Replace all GRPO references with GRN
        replacements = [
            ('GRPODocument', 'GRNDocument'),
            ('GRPOItem', 'GRNItem'),
            ('grpo_document', 'grn_document'),
            ('grpo_doc', 'grn_doc'),
            ('grpo_id', 'grn_id'),
            ('grpo_count', 'grn_count'),
            ('user_grpo_count', 'user_grn_count'),
            ('grpo_documents', 'grn_documents'),
            ('grpo_items', 'grn_items'),
            ('create_grpo', 'create_grn'),
            ('grpo_detail', 'grn_detail'),
            ('grpo_list', 'grn_list'),
            ("'grpo'", "'grn'"),
            ('"grpo"', '"grn"'),
            ('GRPO', 'GRN'),
            ('grpo', 'grn'),
            ('Goods Receipt against Purchase Orders', 'Goods Received Note (GRN)'),
            ('Goods Receipt PO', 'Goods Received Note (GRN)'),
            ('Purchase Delivery Note', 'Goods Received Note'),
        ]
        
        for old, new in replacements:
            content = content.replace(old, new)
        
        # Update specific route names
        content = re.sub(r"@app\.route\('/grpo'", "@app.route('/grn'", content)
        content = re.sub(r"@app\.route\('/grpo/", "@app.route('/grn/", content)
        content = re.sub(r"url_for\('grpo'", "url_for('grn'", content)
        content = re.sub(r"url_for\('grpo_", "url_for('grn_", content)
        
        # Update comments and logging messages
        content = re.sub(r'GRPO', 'GRN', content)
        content = re.sub(r'grpo', 'grn', content)
        
        with open('routes.py', 'w') as f:
            f.write(content)
        
        print("✅ routes.py updated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error updating routes.py: {e}")
        return False

def update_permission_references():
    """Update permission name from grpo to grn in models.py"""
    
    try:
        with open('models.py', 'r') as f:
            content = f.read()
        
        print("📝 Updating models.py - permission references...")
        
        # Update permission references
        content = content.replace("'grpo': False", "'grn': False")
        content = content.replace("'grpo': True", "'grn': True")
        content = content.replace("'grpo'", "'grn'")
        content = content.replace('"grpo"', '"grn"')
        
        with open('models.py', 'w') as f:
            f.write(content)
        
        print("✅ models.py permission references updated")
        return True
        
    except Exception as e:
        print(f"❌ Error updating models.py: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("   Update GRPO to GRN in Application Files")
    print("=" * 60)
    print()
    
    if update_routes_file():
        print("✅ Routes file updated")
    else:
        print("❌ Routes file update failed")
        exit(1)
    
    if update_permission_references():
        print("✅ Permission references updated")
    else:
        print("❌ Permission references update failed")
    
    print("\n🎉 Application files updated from GRPO to GRN!")
    print("📌 Please restart your Flask application.")