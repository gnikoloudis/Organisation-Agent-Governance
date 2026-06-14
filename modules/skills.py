import streamlit as st
from services.skills import create_skill, update_skill, delete_skill, get_skills
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
    if st.session_state.get("skills_uploader") is not None:
        try:
            content = st.session_state.skills_uploader.read().decode("utf-8")
            name, desc, tags, body = parse_frontmatter(content)
            
            if name: st.session_state.skills_name = name
            if desc: st.session_state.skills_desc = desc
            if tags: st.session_state.skills_tags = tags
            st.session_state.skills_text_content = body
        except Exception as e:
            st.error(f"Could not read file: {e}")

def render():
    if st.session_state.get("skills_clear_form"):
        for key in ["skills_name", "skills_text_content", "skills_bookmark", "skills_desc", "skills_ref", "skills_tags", "skills_create_url"]:
            if key in st.session_state:
                st.session_state[key] = ""
        st.session_state.skills_clear_form = False

    tab_view, tab_create = st.tabs(["📁 View & Edit Skills", "➕ Add to Skills"])

    # --- TAB: CREATE NEW SKILL ---
    with tab_create:
        st.subheader("Create New Skill Asset")
        
        name = st.text_input("Asset Name", placeholder="e.g., python_data_analyzer", key="skills_name")
        storage_type = st.selectbox("Storage Type", ["Markdown Text", "Real File Upload", "Web Bookmark"], key="skills_storage")
        
        content = ""
        uploaded_file_bytes = None
        uploaded_file_name = None

        if storage_type == "Real File Upload":
            uploaded_file = st.file_uploader("Choose Markdown or Text File", type=["md", "txt", "py", "csv"], key="skills_uploader", on_change=load_file_content)
            if uploaded_file is not None:
                uploaded_file_bytes = uploaded_file.read()
                uploaded_file_name = uploaded_file.name

        if storage_type in ["Markdown Text", "Real File Upload"]:
            if storage_type == "Markdown Text":
                col_url, col_btn = st.columns([4, 1])
                with col_url:
                    st.text_input("🌐 Load from Remote URL (Optional)", placeholder="https://raw.githubusercontent.com/.../prompt.md", key="skills_create_url")
                with col_btn:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    st.button("⬇️ Fetch Text", key="skills_fetch_btn", on_click=perform_fetch, args=("skills_create_url", "skills_name", "skills_desc", "skills_tags", "skills_text_content"))
                
                fetch_err = st.session_state.get("error_skills_create_url")
                if fetch_err: st.error(fetch_err)

            if "skills_text_content" not in st.session_state:
                st.session_state.skills_text_content = ""
            content = st.text_area("Markdown Code / Text Editor", key="skills_text_content", height=250, placeholder="# Write your agent instructions here...")

        elif storage_type == "Web Bookmark":
            content = st.text_input("Bookmark URL", placeholder="https://example.com/docs", key="skills_bookmark")
            st.info("📌 **Note:** Web Bookmarks cannot be exported directly to the Coding tool workspace.")
            
        description = st.text_area("Asset Description", key="skills_desc")
        
        reference_url = ""
        if storage_type in ["Markdown Text", "Real File Upload"]:
            reference_url = st.text_input("🔗 Reference Bookmark (Optional)", placeholder="https://...", key="skills_ref")
            
        tags = st.text_input("Category Tags (comma-separated)", key="skills_tags")
        
        if st.button("Save Skill Asset", type="primary"):
            try:
                create_skill(
                    name=name,
                    storage_type=storage_type,
                    content=content if storage_type != "Web Bookmark" else content.strip(),
                    file_blob=uploaded_file_bytes,
                    file_name=uploaded_file_name,
                    description=description,
                    tags=tags,
                    reference_url=reference_url
                )
                st.session_state.skills_clear_form = True
                st.success("✅ Successfully saved your Skill asset!")
                st.rerun()
            except (AssetValidationError, AssetFetchError) as e:
                st.error(f"❌ {e}")

    # --- TAB: VIEW & MANAGE SKILLS ---
    with tab_view:
        st.subheader("Active Assets under Skills")
        try:
            items = get_skills()
        except Exception as e:
            st.error(f"Error loading skills: {e}")
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
                        if st.button("🗑️ Delete", key=f"del_Skills_{item['id']}"):
                            try:
                                delete_skill(item['id'])
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
                        st.download_button("⬇️ Download File", data=item['file_blob'], file_name=item['file_name'], key=f"dl_Skills_{item['id']}")

                    with st.expander("✏️ Edit Asset Details"):
                        name_key = f"edit_name_skills_{item['id']}"
                        desc_key = f"edit_desc_skills_{item['id']}"
                        text_key = f"edit_content_skills_{item['id']}"
                        url_key = f"edit_remote_url_skills_{item['id']}"
                        tags_key = f"edit_tags_skills_{item['id']}"
                        
                        if name_key not in st.session_state: st.session_state[name_key] = item['name']
                        if desc_key not in st.session_state: st.session_state[desc_key] = item['description']
                        if text_key not in st.session_state: st.session_state[text_key] = item['content'] or ""
                        if tags_key not in st.session_state: st.session_state[tags_key] = item['tags']
                        
                        new_name = st.text_input("Asset Name", key=name_key)
                        new_desc = st.text_area("Description", key=desc_key)
                        
                        new_ref = ""
                        if item['type'] in ["Markdown Text", "Real File Upload"]:
                            new_ref = st.text_input("🔗 Append New Reference (Optional)", placeholder="https://...", key=f"edit_ref_skills_{item['id']}")
                            
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
                                st.button("⬇️ Fetch & Replace", key=f"edit_fetch_skills_{item['id']}", on_click=perform_fetch, args=(url_key, name_key, desc_key, tags_key, text_key))
                            
                            fetch_err = st.session_state.get(f"error_{url_key}")
                            if fetch_err: st.error(fetch_err)

                            # Consistent Text Editor UI
                            new_content = st.text_area("Markdown Code / Text Editor", height=200, key=text_key)
                            
                            # Real File Upload Replacement Logic
                            if item['type'] == "Real File Upload":
                                st.markdown(f"📄 **Current File:** `{item.get('file_name', 'Unknown File')}`")
                                new_uploaded_file = st.file_uploader("Upload New File to Replace (Leave empty to keep current file)", key=f"edit_file_skills_{item['id']}")
                                
                                if new_uploaded_file is not None:
                                    new_file_bytes = new_uploaded_file.read()
                                    new_file_name = new_uploaded_file.name

                        elif item['type'] == "Web Bookmark":
                            new_content = st.text_input("URL", value=item['content'], key=f"edit_url_skills_{item['id']}")
                            
                        if st.button("💾 Save Changes", key=f"save_edit_skills_{item['id']}", type="secondary"):
                            try:
                                update_skill(
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