import streamlit as st
from database.db_manager import save_customization, get_customizations, delete_customization

def render():
    tab_view, tab_create = st.tabs(["📁 View Workflows", "➕ Add to Workflows"])

    # --- TAB: CREATE NEW WORKFLOW ---
    with tab_create:
        st.subheader("Create New Workflow Asset")
        
        with st.form("create_form_Workflows", clear_on_submit=True):
            name = st.text_input("Asset Name", placeholder="e.g., data_pipeline_v1")
            
            # We only use Web Bookmarks now
            st.info("ℹ️ Workflows currently use Web Bookmarks to manage complex external configurations.")
            content = st.text_input("Bookmark URL", placeholder="https://example.com/docs")
            
            st.info("📌 **Note:** Web Bookmarks cannot be exported directly to the Coding tool workspace. They will be pushed as human-readable `.toml` files to GitHub.")
                
            description = st.text_area("Asset Description")
            tags = st.text_input("Category Tags (comma-separated)")
            
            if st.form_submit_button("Save Asset"):
                if not name:
                    st.error("Please supply a valid item name.")
                elif not content:
                    st.error("Please supply a valid URL for the bookmark.")
                else:
                    # Hardcoding "Web Bookmark" and sending None for file data
                    save_customization(
                        category="Workflows", 
                        name=name, 
                        type_val="Web Bookmark", 
                        content=content, 
                        file_blob=None, 
                        file_name=None, 
                        description=description, 
                        tags=tags
                    )
                    st.success("Successfully saved your Workflows asset!")
                    st.rerun()

    # --- TAB: VIEW & MANAGE WORKFLOWS ---
    with tab_view:
        st.subheader("Active Assets under Workflows")
        items = get_customizations(category="Workflows")
        
        if not items:
            st.info("No records found in this category yet.")
        else:
            for item in items:
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"### **{item['name']}** `[{item['type']}]`")
                        if item['tags']:
                            st.markdown(" ".join([f"`{t.strip()}`" for t in item['tags'].split(",") if t.strip()]))
                    with col2:
                        if st.button("🗑️ Delete", key=f"del_Workflows_{item['id']}"):
                            delete_customization(item['id'])
                            st.rerun()
                    
                    st.markdown(f"**Description:** {item['description']}")
                    
                    # Simplified display: We only render links now
                    if item['type'] == "Web Bookmark":
                        st.markdown(f"🔗 **Bookmark Link:** [{item['content']}]({item['content']})")
                    else:
                        # Fallback just in case you have older non-bookmark records still in the database
                        st.warning("⚠️ This asset is an older type that is no longer supported in the Workflows UI.")