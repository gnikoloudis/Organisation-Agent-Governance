import os
from core.exceptions import AssetValidationError

def export_assets(selected_items, base_path):
    """Writes selected assets to the user-defined base path. Returns list of exported file paths."""
    base_path = base_path.strip() if base_path else ""
    if not base_path:
        raise AssetValidationError("Please specify a target directory.")
        
    selected_ids = {item['id'] for item in selected_items}
    child_ids_to_skip = set()
    
    from database.db_manager import get_relations
    for item in selected_items:
        if item['category'] in ["Skills", "Rules"]:
            relations = get_relations(item['id'])
            for rel in relations:
                child_id = rel.get('child_id')
                if child_id in selected_ids:
                    child_ids_to_skip.add(child_id)
        
    exported_paths = []
    for item in selected_items:
        if item['id'] in child_ids_to_skip:
            continue
            
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
        content = content or ""
        
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
            
        # Export relations if item is a Skill or Rule
        if item['category'] in ["Skills", "Rules"]:
            from database.db_manager import get_relations
            relations = get_relations(item['id'])
            for rel in relations:
                rel_type = rel['relation_type']
                plural_type = f"{rel_type}s" if not rel_type.endswith("s") else rel_type
                
                rel_dir = os.path.join(target_dir, plural_type)
                os.makedirs(rel_dir, exist_ok=True)
                
                rel_alias = rel['relation_alias']
                rel_file_path = os.path.join(rel_dir, rel_alias)
                
                rel_content = rel['file_blob'] if rel['file_blob'] else rel['content']
                rel_content = rel_content or ""
                
                if rel['type'] == "Web Bookmark" and rel_content:
                    rel_content = f"[Bookmark Link]({rel_content})\n\nDescription: {rel['description'] or ''}"
                    
                try:
                    if isinstance(rel_content, bytes):
                        with open(rel_file_path, 'wb') as f:
                            f.write(rel_content)
                    else:
                        with open(rel_file_path, 'w', encoding='utf-8') as f:
                            f.write(str(rel_content))
                    exported_paths.append(os.path.abspath(rel_file_path))
                except Exception as e:
                    raise AssetValidationError(f"Error writing relation {rel_alias} to {rel_dir}: {e}")
            
    return exported_paths
