import os
from core.exceptions import AssetValidationError

def export_assets(selected_items, base_path):
    """Writes selected assets to the user-defined base path. Returns list of exported file paths."""
    base_path = base_path.strip() if base_path else ""
    if not base_path:
        raise AssetValidationError("Please specify a target directory.")
        
    exported_paths = []
    for item in selected_items:
        if item['type'] == "Web Bookmark":
            continue
            
        # Sanitize names
        safe_category = item['category'].lower().replace(" ", "_")
        safe_name = item['name'].replace(' ', '_').lower()
        
        # Path: base_path/{category}/{name}/
        target_dir = os.path.join(base_path, safe_category, safe_name)
        os.makedirs(target_dir, exist_ok=True)
        
        extension = ".json" if item['category'] == "MCP Services" else ".md"
        file_path = os.path.join(target_dir, f"{safe_name}{extension}")
        
        content = item['file_blob'] if item['file_blob'] else item['content']
        
        try:
            if isinstance(content, bytes):
                with open(file_path, 'wb') as f:
                    f.write(content)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(content))
            exported_paths.append(os.path.abspath(file_path))
        except Exception as e:
            raise AssetValidationError(f"Error writing {item['name']} to {base_path}: {e}")
            
    return exported_paths
