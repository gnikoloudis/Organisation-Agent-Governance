import streamlit as st
import json
from core.mcp import create_mcp, update_mcp, delete_mcp, get_mcps
from core.utils import fetch_remote_content
from core.exceptions import AssetValidationError, AssetNotFoundError

def perform_mcp_fetch(url_key, content_key):
    """Callback: Fetches pure JSON securely using core utilities."""
    url = st.session_state.get(url_key, "").strip()
    if not url:
        st.session_state[f"error_{url_key}"] = "Please enter a URL first."
        return
    try:
        fetched_data = fetch_remote_content(url)
        json.loads(fetched_data) # Force validate JSON
        if content_key: st.session_state[content_key] = fetched_data
        st.session_state[f"error_{url_key}"] = None
    except json.JSONDecodeError:
        st.session_state[f"error_{url_key}"] = "❌ The fetched URL does not contain a valid JSON payload."
    except Exception as e:
        st.session_state[f"error_{url_key}"] = f"❌ Failed to fetch URL: {e}"

def load_file_content():
    """Callback: Safely reads uploaded JSON file."""
    if st.session_state.get("mcp_uploader") is not None:
        try:
            content = st.session_state.mcp_uploader.read().decode("utf-8")
            st.session_state.mcp_text_content = content
        except Exception as e:
            st.error(f"Could not read file: {e}")

def render():
    if st.session_state.get("mcp_clear_form"):
        for key in ["mcp_name", "mcp_text_content", "mcp_bookmark", "mcp_desc", "mcp_ref", "mcp_tags", "mcp_create_url"]:
            if key in st.session_state:
                st.session_state[key] = ""
        st.session_state.mcp_clear_form = False

    tab_view, tab_create = st.tabs(["📁 View & Edit MCP Services", "➕ Add to MCP Services"])

    with tab_create:
        st.subheader("Create New MCP Service Asset")
        name = st.text_input("Asset Name", placeholder="e.g., file_system_mcp", key="mcp_name")
        storage_type = st.selectbox("Storage Type", ["JSON Config", "Real File Upload", "Web Bookmark"], key="mcp_storage")
        
        content = ""
        uploaded_file_bytes = None
        uploaded_file_name = None

        if storage_type == "Real File Upload":
            uploaded_file = st.file_uploader("Choose JSON File", type=["json"], key="mcp_uploader", on_change=load_file_content)
            if uploaded_file is not None:
                uploaded_file_bytes = uploaded_file.read()
                uploaded_file_name = uploaded_file.name

        if storage_type in ["JSON Config", "Real File Upload"]:
            if storage_type == "JSON Config":
                col_url, col_btn = st.columns([4, 1])
                with col_url:
                    st.text_input("🌐 Load from Remote URL (Optional)", placeholder="https://raw.githubusercontent.com/.../config.json", key="mcp_create_url")
                with col_btn:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    st.button("⬇️ Fetch JSON", key="mcp_fetch_btn", on_click=perform_mcp_fetch, args=("mcp_create_url", "mcp_text_content"))
                
                fetch_err = st.session_state.get("error_mcp_create_url")
                if fetch_err: st.error(fetch_err)

            if "mcp_text_content" not in st.session_state:
                st.session_state.mcp_text_content = ""
            content = st.text_area("JSON Configuration Editor", key="mcp_text_content", height=250, placeholder='{\n  "mcpServers": { ... }\n}')

        elif storage_type == "Web Bookmark":
            content = st.text_input("Bookmark URL", placeholder="https://example.com/docs", key="mcp_bookmark")
            st.info("📌 **Note:** Web Bookmarks cannot be exported directly to the Coding tool workspace.")
            
        description = st.text_area("Asset Description", key="mcp_desc")
        
        reference_url = ""
        if storage_type in ["JSON Config", "Real File Upload"]:
            reference_url = st.text_input("🔗 Reference Bookmark (Optional)", placeholder="https://...", key="mcp_ref")
            
        tags = st.text_input("Category Tags (comma-separated)", key="mcp_tags")
        
        if st.button("Save MCP Asset", type="primary"):
            try:
                create_mcp(
                    name=name,
                    storage_type=storage_type,
                    content=content if storage_type != "Web Bookmark" else content.strip(),
                    file_blob=uploaded_file_bytes,
                    file_name=uploaded_file_name,
                    description=description,
                    tags=tags,
                    reference_url=reference_url
                )
                st.session_state.mcp_clear_form = True
                st.success("✅ Successfully validated and saved your MCP Service asset!")
                st.rerun()
            except AssetValidationError as e:
                st.error(f"❌ {e}")

    with tab_view:
        st.subheader("Active Assets under MCP Services")
        try:
            items = get_mcps()
        except Exception as e:
            st.error(f"Error loading MCP services: {e}")
            items = []
            
        if not items:
            st.info("No records found in this category yet.")
        else:
            for item in items:
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"### **{item['name']}** `[{item['type']}]`")
                        if item['tags']: st.markdown(" ".join([f"`{t.strip().lower()}`" for t in item['tags'].split(",") if t.strip()]))
                    with col2:
                        if st.button("🗑️ Delete", key=f"del_MCP_{item['id']}"):
                            try:
                                delete_mcp(item['id'])
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ {e}")
                    
                    st.markdown(f"**Description:** \n{item['description']}")
                    if item['type'] in ["JSON Config", "Real File Upload"] and item['content']:
                        with st.expander("⚙️ Preview JSON Tree"):
                            try: st.json(json.loads(item['content']))
                            except: st.code(item['content'], language="json")
                    elif item['type'] == "Web Bookmark":
                        display_text = item['description'] if item['description'] else item['name']
                        st.markdown(f"🔗 **Bookmark Link:** <a href='{item['content']}' target='_blank'>{display_text}</a>", unsafe_allow_html=True)

                    with st.expander("✏️ Edit Asset Details"):
                        name_key = f"edit_name_{item['id']}"
                        desc_key = f"edit_desc_{item['id']}"
                        text_key = f"edit_content_{item['id']}"
                        url_key = f"edit_remote_url_{item['id']}"
                        
                        if name_key not in st.session_state: st.session_state[name_key] = item['name']
                        if desc_key not in st.session_state: st.session_state[desc_key] = item['description']
                        if text_key not in st.session_state: st.session_state[text_key] = item['content'] or ""

                        new_name = st.text_input("Asset Name", key=name_key)
                        new_desc = st.text_area("Description", key=desc_key)
                        
                        new_ref = ""
                        if item['type'] in ["JSON Config", "Real File Upload"]:
                            new_ref = st.text_input("🔗 Append New Reference (Optional)", placeholder="https://...", key=f"edit_ref_{item['id']}")
                            
                        new_tags = st.text_input("Tags", value=item['tags'], key=f"edit_tags_{item['id']}")
                        new_content = item['content']
                        
                        new_file_bytes = None
                        new_file_name = None
                        
                        if item['type'] in ["JSON Config", "Real File Upload"]:
                            col_edit_url, col_edit_btn = st.columns([4, 1])
                            with col_edit_url:
                                st.text_input("🌐 Replace from Remote URL", placeholder="https://raw.githubusercontent.com/.../config.json", key=url_key)
                            with col_edit_btn:
                                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                                st.button("⬇️ Fetch & Replace", key=f"edit_fetch_{item['id']}", on_click=perform_mcp_fetch, args=(url_key, text_key))
                            
                            fetch_err = st.session_state.get(f"error_{url_key}")
                            if fetch_err: st.error(fetch_err)

                            new_content = st.text_area("JSON Configuration", height=200, key=text_key)

                            if item['type'] == "Real File Upload":
                                st.markdown(f"📄 **Current File:** `{item.get('file_name', 'Unknown File')}`")
                                new_uploaded_file = st.file_uploader("Upload New File to Replace (Leave empty to keep current file)", key=f"edit_file_mcp_{item['id']}")
                                
                                if new_uploaded_file is not None:
                                    new_file_bytes = new_uploaded_file.read()
                                    new_file_name = new_uploaded_file.name

                        elif item['type'] == "Web Bookmark":
                            new_content = st.text_input("URL", value=item['content'], key=f"edit_url_{item['id']}")
                            
                        if st.button("💾 Save Changes", key=f"save_edit_{item['id']}", type="secondary"):
                            try:
                                update_mcp(
                                    item_id=item['id'],
                                    name=new_name,
                                    storage_type=item['type'],
                                    content=new_content,
                                    description=new_desc,
                                    tags=new_tags,
                                    reference_url=new_ref,
                                    file_blob=new_file_bytes,
                                    file_name=new_file_name
                                )
                                st.success("✅ Asset updated successfully!")
                                st.rerun()
                            except (AssetValidationError, AssetNotFoundError) as e:
                                st.error(f"❌ {e}")