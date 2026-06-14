import os
import streamlit as st
from database.db_manager import get_customizations, get_relations
from services.exporter import export_assets
from core.exceptions import AssetValidationError

def render():
    st.subheader("🚀 Export to Development Workspace")
    
    # User Input for Directory
    base_path = st.text_input("Target Directory for .agent", value=".agent")
    
    items = get_customizations()
    exportable = [i for i in items if i['type'] != "Web Bookmark"]
    
    if not exportable:
        st.info("No exportable assets found.")
        return

    # Build relations and track children of exportable items
    relations_map = {}
    child_ids = set()
    exportable_ids = {i['id'] for i in exportable}
    
    for item in exportable:
        if item['category'] in ["Skills", "Rules"]:
            rels = get_relations(item['id'])
            relations_map[item['id']] = rels
            for rel in rels:
                if rel['child_id'] in exportable_ids:
                    child_ids.add(rel['child_id'])
                    
    root_items = [i for i in exportable if i['id'] not in child_ids]

    st.write("##### **Select Assets to Export:**")
    st.caption("Child assets are nested under their parents and will be automatically exported with them.")

    selected_items = []
    
    categories = ["Skills", "Rules", "Workflows", "MCP Services"]
    for cat in categories:
        cat_items = [i for i in root_items if i['category'] == cat]
        if not cat_items:
            continue
            
        st.markdown(f"**{cat}**")
        for item in cat_items:
            # Root Checkbox
            is_selected = st.checkbox(
                f"{item['name']}", 
                value=True, 
                key=f"export_item_{item['id']}"
            )
            if is_selected:
                selected_items.append(item)
                
            # Indented relations
            rels = relations_map.get(item['id'], [])
            if rels:
                for rel in rels:
                    st.markdown(
                        f"&nbsp;&nbsp;&nbsp;&nbsp;↳ 🔗 **{rel['relation_type'].capitalize()}**: `{rel['relation_alias']}` *({rel['name']})*"
                    )
        st.write("") # Category spacer

    if st.button("Run Export"):
        if not base_path.strip():
            st.error("Please specify a target directory.")
        elif not selected_items:
            st.error("Please select at least one asset to export.")
        else:
            try:
                exported_paths = export_assets(selected_items, base_path)
                st.success(f"Successfully exported {len(exported_paths)} assets to: {os.path.abspath(base_path)}")
            except AssetValidationError as e:
                st.error(f"❌ {e}")