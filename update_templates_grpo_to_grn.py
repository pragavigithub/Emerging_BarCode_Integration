#!/usr/bin/env python3
"""
Update all template files to change GRPO to GRN terminology
"""

import os
import glob

def update_template_file(file_path):
    """Update a single template file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Replace all GRPO references with GRN
        replacements = [
            ('GRPO', 'GRN'),
            ('Goods Receipt PO', 'Goods Received Note (GRN)'),
            ('Goods Receipt against Purchase Orders', 'Goods Received Note (GRN)'),
            ('createGRPOModal', 'createGRNModal'),
            ('Create GRPO', 'Create GRN'),
            ('grpo_detail', 'grn_detail'),
            ('grpo_id', 'grn_id'),
            ('grpo.html', 'grn.html'),
            ('GRPO Documents', 'GRN Documents'),
            ('GRPO ID', 'GRN ID'),
            ('No GRPO Documents', 'No GRN Documents'),
            ('first GRPO document', 'first GRN document'),
            ('GRPO created', 'GRN created'),
            ('GRPO Module', 'GRN Module'),
            ('grpo/create', 'grn/create'),
            ('grpo/detail', 'grn/detail'),
        ]
        
        for old, new in replacements:
            content = content.replace(old, new)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def update_all_templates():
    """Update all template files"""
    
    print("📝 Updating template files...")
    
    # Find all HTML templates
    template_files = []
    
    # Check templates/ directory
    if os.path.exists('templates'):
        template_files.extend(glob.glob('templates/**/*.html', recursive=True))
    
    # Check modules/ directory for templates
    if os.path.exists('modules'):
        template_files.extend(glob.glob('modules/**/templates/**/*.html', recursive=True))
        template_files.extend(glob.glob('modules/**/*.html', recursive=True))
    
    updated_count = 0
    
    for file_path in template_files:
        if update_template_file(file_path):
            print(f"✅ Updated {file_path}")
            updated_count += 1
        else:
            print(f"➡️ No changes needed in {file_path}")
    
    print(f"\n📊 Updated {updated_count} template files")
    return updated_count > 0

def rename_template_files():
    """Rename template files from grpo to grn"""
    
    print("📝 Renaming template files...")
    
    files_to_rename = [
        ('templates/grpo.html', 'templates/grn.html'),
        ('templates/grpo_detail.html', 'templates/grn_detail.html'),
        ('templates/create_grpo.html', 'templates/create_grn.html'),
        ('modules/grpo/templates/grpo.html', 'modules/grpo/templates/grn.html'),
        ('modules/grpo/templates/grpo_detail.html', 'modules/grpo/templates/grn_detail.html'),
        ('modules/grpo/templates/create_grpo.html', 'modules/grpo/templates/create_grn.html'),
    ]
    
    renamed_count = 0
    
    for old_path, new_path in files_to_rename:
        if os.path.exists(old_path):
            try:
                os.rename(old_path, new_path)
                print(f"✅ Renamed {old_path} to {new_path}")
                renamed_count += 1
            except Exception as e:
                print(f"❌ Error renaming {old_path}: {e}")
        else:
            print(f"➡️ File not found: {old_path}")
    
    print(f"\n📊 Renamed {renamed_count} template files")
    return renamed_count > 0

if __name__ == "__main__":
    print("=" * 60)
    print("   Update Templates GRPO to GRN")
    print("=" * 60)
    print()
    
    # Update template content
    if update_all_templates():
        print("✅ Template content updated")
    else:
        print("ℹ️ No template content changes needed")
    
    # Rename template files
    if rename_template_files():
        print("✅ Template files renamed")
    else:
        print("ℹ️ No template files to rename")
    
    print("\n🎉 Template updates completed!")
    print("📌 Templates now use GRN (Goods Received Note) terminology")