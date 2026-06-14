import streamlit as st
from database.db_manager import save_customization, get_customizations, delete_customization

def render_category_ui(category_name):
    """Generates the standard workspace UI for a given category."""
    tab_view, tab_create = st.tabs([f"📁 View {category_name}", f"➕ Add to {category_name}"])

    # --- TAB: CREATE NEW CUSTOMIZATION ---
    with tab_create:
        st.subheader(f"Create New {category_name[:-1] if category_name.endswith('s') else category_name} Asset")
        
        with st.form(f"create_form_{category_name}", clear_on_submit=True):
            name = st.text_input("Asset Name", placeholder="e.g., specific_task_handler")
            storage_type = st.selectbox("Storage Type", ["Markdown Text", "Real File Upload", "Web Bookmark"])
            
            content = ""
            uploaded_file_bytes = None
            uploaded_file_name = None
            
            if storage_type == "Markdown Text":
                content = st.text_area("Markdown Code / Text Editor", height=250)
            elif storage_type == "Real File Upload":
                uploaded_file = st.file_uploader("Choose File")
                if uploaded_file is not None:
                    uploaded_file_bytes = uploaded_file.read()
                    uploaded_file_name = uploaded_file.name
            elif storage_type == "Web Bookmark":
                content = st.text_input("Bookmark URL", placeholder="https://example.com/docs")
                st.info("📌 **Note:** Web Bookmarks cannot be exported directly to the Coding tool workspace. They will be pushed as human-readable `.toml` files to GitHub.")
                
            description = st.text_area("Asset Description")
            tags = st.text_input("Category Tags (comma-separated)")
            
            submit_btn = st.form_submit_button("Save Asset")
            
            if submit_btn:
                if not name:
                    st.error("Please supply a valid item name.")
                elif storage_type == "Web Bookmark" and not content:
                    st.error("Please supply a valid URL for the bookmark.")
                else:
                    save_customization(
                        category=category_name, name=name, type_val=storage_type,
                        content=content, file_blob=uploaded_file_bytes, 
                        file_name=uploaded_file_name, description=description, tags=tags
                    )
                    st.success(f"Successfully saved your {category_name} asset!")
                    st.rerun()

    # --- TAB: VIEW & MANAGE WORKSPACE ---
    with tab_view:
        st.subheader(f"Active Assets under {category_name}")
        items = get_customizations(category=category_name)
        
        if not items:
            st.info("No records found in this category yet.")
        else:
            for item in items:
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"### **{item['name']}** `[{item['type']}]`")
                        if item['tags']:
                            tags_list = [t.strip() for t in item['tags'].split(",") if t.strip()]
                            st.markdown(" ".join([f"`{t}`" for t in tags_list]))
                    with col2:
                        if st.button("🗑️ Delete", key=f"del_{category_name}_{item['id']}"):
                            delete_customization(item['id'])
                            st.rerun()
                    
                    st.markdown(f"**Description:** {item['description']}")
                    
                    if item['type'] == "Markdown Text" and item['content']:
                        with st.expander("📝 Preview Markdown Content"):
                            st.markdown(item['content'])
                    elif item['type'] == "Web Bookmark":
                        st.markdown(f"🔗 **Bookmark Link:** [{item['content']}]({item['content']})")
                    elif item['type'] == "Real File Upload" and item['file_blob']:
                        st.download_button("⬇️ Download File", data=item['file_blob'], file_name=item['file_name'], key=f"dl_{category_name}_{item['id']}")