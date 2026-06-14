import streamlit as st
import os
from services.skills import create_skill, update_skill, delete_skill, get_skills, get_skill_relations, add_skill_relation, remove_skill_relation
from services.rules import get_rules
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

def perform_relation_fetch(url_key, name_key, storage_key, desc_key, tags_key, alias_key, content_key, error_key):
    """Callback: Fetches remote content and pre-populates relation forms safely before widget instantiation."""
    url = st.session_state.get(url_key, "").strip()
    if not url:
        st.session_state[error_key] = "Please enter a URL first."
        return
    try:
        fetched_data = fetch_remote_content(url)
        st.session_state[content_key] = fetched_data
        
        url_path = url.split("?")[0]
        filename_from_url = os.path.basename(url_path)
        
        st.session_state[alias_key] = filename_from_url
        st.session_state[name_key] = filename_from_url.split(".")[0]
        
        if filename_from_url.endswith(".md"):
            st.session_state[storage_key] = "Markdown Text"
            fetch_name, fetch_desc, fetch_tags, _ = parse_frontmatter(fetched_data)
            if fetch_name: st.session_state[name_key] = fetch_name
            if fetch_desc: st.session_state[desc_key] = fetch_desc
            if fetch_tags: st.session_state[tags_key] = fetch_tags
        else:
            st.session_state[storage_key] = "Real File Upload"
            
        st.session_state[error_key] = None
    except Exception as e:
        st.session_state[error_key] = f"❌ Failed to fetch URL: {e}"

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

                    # --- RELATIONSHIPS EXPANDER ---
                    with st.expander("🔗 Related References, Assets & Tools"):
                        try:
                            relations = get_skill_relations(item['id'])
                        except Exception as e:
                            st.error(f"Error loading relations: {e}")
                            relations = []
                            
                        if relations:
                            st.markdown("##### **Current Relations**")
                            for rel in relations:
                                child_asset = rel["child_asset"]
                                col_r1, col_r2, col_r3 = st.columns([3, 2, 1])
                                with col_r1:
                                    st.markdown(f"**[{child_asset['category']}] {child_asset['name']}**")
                                    st.caption(f"Alias: `{rel['relation_alias']}` | Type: `{rel['relation_type']}`")
                                with col_r2:
                                    # Safe download or preview
                                    if child_asset.get("type") == "Real File Upload" and child_asset.get("file_blob"):
                                        st.download_button(
                                            "⬇️ Download File", 
                                            data=child_asset["file_blob"], 
                                            file_name=child_asset["file_name"] or rel['relation_alias'], 
                                            key=f"dl_rel_Skills_{item['id']}_{child_asset['id']}_{rel['relation_alias']}"
                                        )
                                with col_r3:
                                    if st.button("🗑️ Delete Link", key=f"del_link_Skills_{item['id']}_{child_asset['id']}_{rel['relation_alias']}"):
                                        try:
                                            remove_skill_relation(item['id'], child_asset['id'], rel['relation_type'], rel['relation_alias'])
                                            st.success("Relation removed!")
                                            st.rerun()
                                        except Exception as err:
                                            st.error(f"Error: {err}")
                        else:
                            st.info("No relations linked to this Skill yet.")
                            
                        st.markdown("---")
                        st.markdown("##### **Add a Relation**")
                        
                        # Tabs for existing vs import from URL
                        tab_link_existing, tab_link_url = st.tabs(["🔗 Link Existing Skill/Rule", "🌐 Import from Remote URL"])
                        
                        with tab_link_existing:
                            candidates = []
                            try:
                                candidates = [c for c in (get_skills() + get_rules()) if c['id'] != item['id']]
                            except Exception:
                                pass
                                
                            if not candidates:
                                st.info("No other Skills or Rules available to link.")
                            else:
                                selected_candidate_name = st.selectbox(
                                    "Select Skill/Rule to link",
                                    options=[c['name'] for c in candidates],
                                    key=f"cand_select_Skills_{item['id']}"
                                )
                                selected_candidate = next(c for c in candidates if c['name'] == selected_candidate_name)
                                
                                rel_type = st.selectbox("Relation Type", ["reference", "asset", "tool"], key=f"cand_type_Skills_{item['id']}")
                                
                                # Default alias based on child file_name or sanitized name
                                default_alias = selected_candidate.get("file_name") or f"{selected_candidate['name'].replace(' ', '_').lower()}.md"
                                rel_alias = st.text_input("Relation Filename / Alias", value=default_alias, key=f"cand_alias_Skills_{item['id']}")
                                
                                if st.button("Link Existing Item", key=f"btn_link_Skills_{item['id']}", type="primary"):
                                    try:
                                        add_skill_relation(item['id'], selected_candidate['id'], rel_type, rel_alias)
                                        st.success("Successfully linked item!")
                                        st.rerun()
                                    except Exception as err:
                                        st.error(f"Error: {err}")
                                        
                        with tab_link_url:
                            import_url = st.text_input("🌐 Enter URL to import", placeholder="https://...", key=f"import_url_Skills_{item['id']}")
                            
                            # Fields to capture child metadata
                            child_name = st.text_input("Asset Name", key=f"import_name_Skills_{item['id']}")
                            child_type = st.selectbox("Storage Type", ["Markdown Text", "Real File Upload"], key=f"import_storage_Skills_{item['id']}")
                            child_desc = st.text_area("Asset Description", key=f"import_desc_Skills_{item['id']}")
                            child_tags = st.text_input("Category Tags (comma-separated)", key=f"import_tags_Skills_{item['id']}")
                            
                            # Relation fields
                            import_rel_type = st.selectbox("Relation Type", ["reference", "asset", "tool"], key=f"import_type_Skills_{item['id']}")
                            import_rel_alias = st.text_input("Relation Filename / Alias", key=f"import_alias_Skills_{item['id']}")
                            
                            # Button to fetch
                            st.button(
                                "Fetch & Pre-fill URL Content", 
                                key=f"btn_fetch_url_Skills_{item['id']}", 
                                on_click=perform_relation_fetch, 
                                args=(
                                    f"import_url_Skills_{item['id']}",
                                    f"import_name_Skills_{item['id']}",
                                    f"import_storage_Skills_{item['id']}",
                                    f"import_desc_Skills_{item['id']}",
                                    f"import_tags_Skills_{item['id']}",
                                    f"import_alias_Skills_{item['id']}",
                                    f"fetched_content_Skills_{item['id']}",
                                    f"error_fetch_Skills_{item['id']}"
                                )
                            )
                            
                            error_err = st.session_state.get(f"error_fetch_Skills_{item['id']}")
                            if error_err:
                                st.error(error_err)
                                        
                            fetched_content = st.session_state.get(f"fetched_content_Skills_{item['id']}")
                            if fetched_content:
                                with st.expander("📄 View Fetched Content Preview"):
                                    st.code(fetched_content[:1000] + ("\n... [truncated]" if len(fetched_content) > 1000 else ""))
                                    
                                if st.button("Save & Link Imported Item", key=f"btn_save_imported_Skills_{item['id']}", type="primary"):
                                    try:
                                        # Child category matches parent category: Skills
                                        child_category = "Skills"
                                        
                                        # Create the customization first
                                        if child_type == "Real File Upload":
                                            file_blob = fetched_content.encode("utf-8")
                                            file_name = import_rel_alias or f"{child_name}.txt"
                                            child_new_id = create_skill(child_name, child_type, fetched_content, file_blob, file_name, child_desc, child_tags)
                                        else:
                                            child_new_id = create_skill(child_name, child_type, fetched_content, None, None, child_desc, child_tags)
                                                
                                        # Establish relationship
                                        add_skill_relation(item['id'], child_new_id, import_rel_type, import_rel_alias)
                                        
                                        # Clear fetched state
                                        st.session_state[f"fetched_content_Skills_{item['id']}"] = None
                                        st.success("✅ Successfully imported, saved and linked the remote asset!")
                                        st.rerun()
                                    except Exception as err:
                                        st.error(f"Error saving imported item: {err}")

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