import os
import streamlit as st
from database.db_manager import get_customizations
from core.exporter import export_assets
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

    # Multiselect with category prefix
    selected_names = st.multiselect(
        "Select assets to export:", 
        options=[i['name'] for i in exportable],
        format_func=lambda name: next(f"[{i['category']}] {i['name']}" for i in exportable if i['name'] == name)
    )

    if st.button("Run Export"):
        if not base_path.strip():
            st.error("Please specify a target directory.")
        else:
            items_to_export = [i for i in exportable if i['name'] in selected_names]
            try:
                exported_paths = export_assets(items_to_export, base_path)
                st.success(f"Successfully exported {len(exported_paths)} assets to: {os.path.abspath(base_path)}")
            except AssetValidationError as e:
                st.error(f"❌ {e}")