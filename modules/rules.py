import streamlit as st
from services.rules import create_rule, update_rule, delete_rule, get_rules
from core.utils import fetch_remote_content, parse_frontmatter
from core.exceptions import AssetValidationError, AssetNotFoundError, AssetFetchError

def perform_fetch(url_key, name_key, desc_key, tags_key, content_key):
    """Callback: Fetches markdown from a remote URL and parses it using core utilities."""
    url = st.session_state.get(url_key, "").strip()
    if not url:
        st.session_state[f"error_{url_key}"] = "Please enter a URL first."
        return
    try:
        fetched_data = fetch_remote_content(url)
        fetch_name, fetch_desc, fetch_tags, fetch_body = parse_frontmatter(fetched_data)
        
        if fetch_name and name_key: st.session_state[name_key] = fetch_name
        if fetch_desc and desc_key: st.session_state[desc_key] = fetch_desc
        if fetch_tags and tags_key: st.session_state[tags_key] = fetch_tags
        if content_key: st.session_state[content_key] = fetch_body
        st.session_state[f"error_{url_key}"] = None
    except Exception as e:
        st.session_state[f"error_{url_key}"] = f"❌ Failed to fetch URL: {e}"

def load_file_content():
    """Callback: Safely reads uploaded text file into the form and parses frontmatter."""
    if st.session_state.get("rules_uploader") is not None:
        try:
            content = st.session_state.rules_uploader.read().decode("utf-8")
            name, desc, tags, body = parse_frontmatter(content)
            
            if name: st.session_state.rules_name = name
            if desc: st.session_state.rules_desc = desc
            if tags: st.session_state.rules_tags = tags
            st.session_state.rules_text_content = body
        except Exception as e:
            st.error(f"Could not read file: {e}")

def render():
    st.info("""
    💡 **Rules Syntax Tip:** You can reference other files using `@filename` in your markdown text.
    * **Relative path:** `@file.md` (Resolves relative to this rule)
    * **Absolute path:** `@/path/to/file.md` (Resolves to workspace root)
    """)
    st.divider()

    if st.session_state.get("rules_clear_form"):
        for key in ["rules_name", "rules_text_content", "rules_bookmark", "rules_desc", "rules_ref", "rules_tags", "rules_create_url"]:
            if key in st.session_state:
                st.session_state[key] = ""
        st.session_state.rules_clear_form = False

    tab_view, tab_create = st.tabs(["📁 View & Edit Rules", "➕ Add to Rules"])

    # --- TAB: CREATE NEW RULE ---
    with tab_create:
        st.subheader("Create New Rule Asset")
        
        name = st.text_input("Asset Name", placeholder="e.g., project_guidelines", key="rules_name")
        storage_type = st.selectbox("Storage Type", ["Markdown Text", "Real File Upload", "Web Bookmark"], key="rules_storage")
        
        content = ""
        uploaded_file_bytes = None
        uploaded_file_name = None

        if storage_type == "Real File Upload":
            uploaded_file = st.file_uploader("Choose Markdown or Text File", type=["md", "txt", "py", "csv"], key="rules_uploader", on_change=load_file_content)
            if uploaded_file is not None:
                uploaded_file_bytes = uploaded_file.read()
                uploaded_file_name = uploaded_file.name

        if storage_type in ["Markdown Text", "Real File Upload"]:
            if storage_type == "Markdown Text":
                col_url, col_btn = st.columns([4, 1])
                with col_url:
                    st.text_input("🌐 Load from Remote URL (Optional)", placeholder="https://raw.githubusercontent.com/.../rule.md", key="rules_create_url")
                with col_btn:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    st.button("⬇️ Fetch Text", key="rules_fetch_btn", on_click=perform_fetch, args=("rules_create_url", "rules_name", "rules_desc", "rules_tags", "rules_text_content"))
                
                fetch_err = st.session_state.get("error_rules_create_url")
                if fetch_err: st.error(fetch_err)

            if "rules_text_content" not in st.session_state:
                st.session_state.rules_text_content = ""
            content = st.text_area("Markdown Code / Text Editor", key="rules_text_content", height=250, placeholder="# Write your rule instructions here...")

        elif storage_type == "Web Bookmark":
            content = st.text_input("Bookmark URL", placeholder="https://example.com/docs", key="rules_bookmark")
            st.info("📌 **Note:** Web Bookmarks cannot be exported directly to the Coding tool workspace.")
            
        description = st.text_area("Asset Description", key="rules_desc")
        
        reference_url = ""
        if storage_type in ["Markdown Text", "Real File Upload"]:
            reference_url = st.text_input("🔗 Reference Bookmark (Optional)", placeholder="https://...", key="rules_ref")
            
        tags = st.text_input("Category Tags (comma-separated)", key="rules_tags")
        
        if st.button("Save Rule Asset", type="primary"):
            try:
                create_rule(
                    name=name,
                    storage_type=storage_type,
                    content=content if storage_type != "Web Bookmark" else content.strip(),
                    file_blob=uploaded_file_bytes,
                    file_name=uploaded_file_name,
                    description=description,
                    tags=tags,
                    reference_url=reference_url
                )
                st.session_state.rules_clear_form = True
                st.success("✅ Successfully saved your Rule asset!")
                st.rerun()
            except (AssetValidationError, AssetFetchError) as e:
                st.error(f"❌ {e}")

    # --- TAB: VIEW & MANAGE RULES ---
    with tab_view:
        st.subheader("Active Assets under Rules")
        try:
            items = get_rules()
        except Exception as e:
            st.error(f"Error loading rules: {e}")
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
                        if st.button("🗑️ Delete", key=f"del_Rules_{item['id']}"):
                            try:
                                delete_rule(item['id'])
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ {e}")
                    
                    st.markdown(f"**Description:** \n{item['description']}")
                    
                    if item['type'] in ["Markdown Text", "Real File Upload"] and item['content']:
                        with st.expander("📝 Preview Markdown Content"):
                            st.markdown(item['content'])
                    elif item['type'] == "Web Bookmark":
                        display_text = item['description'] if item['description'] else item['name']
                        st.markdown(f"🔗 **Bookmark Link:** <a href='{item['content']}' target='_blank'>{display_text}</a>", unsafe_allow_html=True)
                        
                    elif item['type'] == "Real File Upload" and item.get('file_blob'):
                        st.download_button("⬇️ Download File", data=item['file_blob'], file_name=item['file_name'], key=f"dl_Rules_{item['id']}")

                    with st.expander("✏️ Edit Asset Details"):
                        name_key = f"edit_name_rules_{item['id']}"
                        desc_key = f"edit_desc_rules_{item['id']}"
                        text_key = f"edit_content_rules_{item['id']}"
                        url_key = f"edit_remote_url_rules_{item['id']}"
                        tags_key = f"edit_tags_rules_{item['id']}"
                        
                        if name_key not in st.session_state: st.session_state[name_key] = item['name']
                        if desc_key not in st.session_state: st.session_state[desc_key] = item['description']
                        if text_key not in st.session_state: st.session_state[text_key] = item['content'] or ""
                        if tags_key not in st.session_state: st.session_state[tags_key] = item['tags']
                        
                        new_name = st.text_input("Asset Name", key=name_key)
                        new_desc = st.text_area("Description", key=desc_key)
                        
                        new_ref = ""
                        if item['type'] in ["Markdown Text", "Real File Upload"]:
                            new_ref = st.text_input("🔗 Append New Reference (Optional)", placeholder="https://...", key=f"edit_ref_rules_{item['id']}")
                            
                        new_tags = st.text_input("Tags", key=tags_key)
                        new_content = item['content']
                        
                        # Data placeholders for Real File Uploads
                        new_file_bytes = None
                        new_file_name = None
                        
                        if item['type'] in ["Markdown Text", "Real File Upload"]:
                            col_edit_url, col_edit_btn = st.columns([4, 1])
                            with col_edit_url:
                                st.text_input("🌐 Replace from Remote URL", placeholder="https://...", key=url_key)
                            with col_edit_btn:
                                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                                st.button("⬇️ Fetch & Replace", key=f"edit_fetch_rules_{item['id']}", on_click=perform_fetch, args=(url_key, name_key, desc_key, tags_key, text_key))
                            
                            fetch_err = st.session_state.get(f"error_{url_key}")
                            if fetch_err: st.error(fetch_err)

                            new_content = st.text_area("Markdown Code / Text Editor", height=200, key=text_key)
                            
                            if item['type'] == "Real File Upload":
                                st.markdown(f"📄 **Current File:** `{item.get('file_name', 'Unknown File')}`")
                                new_uploaded_file = st.file_uploader("Upload New File to Replace (Leave empty to keep current file)", key=f"edit_file_rules_{item['id']}")
                                
                                if new_uploaded_file is not None:
                                    new_file_bytes = new_uploaded_file.read()
                                    new_file_name = new_uploaded_file.name

                        elif item['type'] == "Web Bookmark":
                            new_content = st.text_input("URL", value=item['content'], key=f"edit_url_rules_{item['id']}")
                            
                        if st.button("💾 Save Changes", key=f"save_edit_rules_{item['id']}", type="secondary"):
                            try:
                                update_rule(
                                    item_id=item['id'],
                                    name=new_name,
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