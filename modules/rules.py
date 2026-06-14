import streamlit as st
import os
from services.rules import create_rule, update_rule, delete_rule, get_rules, get_rule_relations, add_rule_relation, remove_rule_relation
from services.skills import get_skills
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
            from database.db_manager import get_relations, get_customizations
            all_customizations = get_customizations()
            child_ids = set()
            for custom_item in all_customizations:
                if custom_item['category'] in ["Skills", "Rules"]:
                    rels = get_relations(custom_item['id'])
                    for r in rels:
                        child_ids.add(r['child_id'])
            root_items = [i for i in items if i['id'] not in child_ids]
        except Exception as e:
            st.error(f"Error loading rules: {e}")
            root_items = []
        
        if not root_items:
            st.info("No records found in this category yet.")
        else:
            for item in root_items:
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

                    # --- RELATIONSHIPS EXPANDER ---
                    with st.expander("🔗 Related References, Resources Assets & Tools"):
                        try:
                            relations = get_rule_relations(item['id'])
                        except Exception as e:
                            st.error(f"Error loading relations: {e}")
                            relations = []
                            
                        if relations:
                            st.markdown("##### **Current Relations**")
                            for rel in relations:
                                child_asset = rel["child_asset"]
                                with st.container(border=True):
                                    col_c1, col_c2 = st.columns([4, 1])
                                    with col_c1:
                                        st.markdown(f"###### ↳ 🔗 **{child_asset['name']}** `[{child_asset['type']}]`")
                                        st.caption(f"Alias: `{rel['relation_alias']}` | Type: `{rel['relation_type'].capitalize()}`")
                                        if child_asset['tags']:
                                            st.markdown(" ".join([f"`{t.strip().lower()}`" for t in child_asset['tags'].split(",") if t.strip()]))
                                    with col_c2:
                                        if st.button("🗑️ Delete Link", key=f"del_link_Rules_{item['id']}_{child_asset['id']}_{rel['relation_type']}_{rel['relation_alias']}"):
                                            try:
                                                remove_rule_relation(item['id'], child_asset['id'], rel['relation_type'], rel['relation_alias'])
                                                st.success("Relation removed!")
                                                st.rerun()
                                            except Exception as err:
                                                st.error(f"Error: {err}")
                                                
                                    st.markdown(f"**Description:** \n{child_asset['description']}")
                                    
                                    # Preview and Download
                                    if child_asset['type'] in ["Markdown Text", "Real File Upload"] and child_asset['content']:
                                        with st.expander("📝 Preview Content"):
                                            st.markdown(child_asset['content'])
                                    elif child_asset['type'] == "Web Bookmark":
                                        display_text = child_asset['description'] if child_asset['description'] else child_asset['name']
                                        st.markdown(f"🔗 **Bookmark Link:** <a href='{child_asset['content']}' target='_blank'>{display_text}</a>", unsafe_allow_html=True)
                                        
                                    if child_asset['type'] == "Real File Upload" and child_asset.get('file_blob'):
                                        st.download_button(
                                            "⬇️ Download File", 
                                            data=child_asset['file_blob'], 
                                            file_name=child_asset['file_name'] or rel['relation_alias'], 
                                            key=f"dl_rel_Rules_{item['id']}_{child_asset['id']}_{rel['relation_type']}_{rel['relation_alias']}"
                                        )
                                        
                                    # Edit relation details
                                    with st.expander("✏️ Edit Relation Details"):
                                        c_name_key = f"edit_name_rel_Rules_{item['id']}_{child_asset['id']}_{rel['relation_type']}_{rel['relation_alias']}"
                                        c_desc_key = f"edit_desc_rel_Rules_{item['id']}_{child_asset['id']}_{rel['relation_type']}_{rel['relation_alias']}"
                                        c_text_key = f"edit_content_rel_Rules_{item['id']}_{child_asset['id']}_{rel['relation_type']}_{rel['relation_alias']}"
                                        c_tags_key = f"edit_tags_rel_Rules_{item['id']}_{child_asset['id']}_{rel['relation_type']}_{rel['relation_alias']}"
                                        
                                        c_type_key = f"edit_type_rel_Rules_{item['id']}_{child_asset['id']}_{rel['relation_type']}_{rel['relation_alias']}"
                                        c_alias_key = f"edit_alias_rel_Rules_{item['id']}_{child_asset['id']}_{rel['relation_type']}_{rel['relation_alias']}"
                                        
                                        if c_name_key not in st.session_state: st.session_state[c_name_key] = child_asset['name']
                                        if c_desc_key not in st.session_state: st.session_state[c_desc_key] = child_asset['description']
                                        if c_text_key not in st.session_state: st.session_state[c_text_key] = child_asset['content'] or ""
                                        if c_tags_key not in st.session_state: st.session_state[c_tags_key] = child_asset['tags']
                                        
                                        if c_type_key not in st.session_state: st.session_state[c_type_key] = rel['relation_type']
                                        if c_alias_key not in st.session_state: st.session_state[c_alias_key] = rel['relation_alias']
                                        
                                        # Relationship Metadata Section
                                        c_new_type = st.selectbox(
                                            "Relationship Type", 
                                            options=["reference", "asset", "tool", "resources"], 
                                            key=c_type_key
                                        )
                                        c_new_alias = st.text_input("Relation Filename / Alias", key=c_alias_key)
                                        
                                        st.divider()
                                        st.markdown("**Asset Details**")
                                        
                                        c_new_name = st.text_input("Asset Name", key=c_name_key)
                                        c_new_desc = st.text_area("Description", key=c_desc_key)
                                        c_new_tags = st.text_input("Tags", key=c_tags_key)
                                        c_new_content = child_asset['content']
                                        
                                        c_new_file_bytes = None
                                        c_new_file_name = None
                                        
                                        if child_asset['type'] in ["Markdown Text", "Real File Upload"]:
                                            c_new_content = st.text_area("Markdown Code / Text Editor", height=150, key=c_text_key)
                                            if child_asset['type'] == "Real File Upload":
                                                st.markdown(f"📄 **Current File:** `{child_asset.get('file_name', 'Unknown File')}`")
                                                c_new_file = st.file_uploader("Upload New File to Replace", key=f"edit_file_rel_Rules_{item['id']}_{child_asset['id']}_{rel['relation_type']}_{rel['relation_alias']}")
                                                if c_new_file is not None:
                                                    c_new_file_bytes = c_new_file.read()
                                                    c_new_file_name = c_new_file.name
                                        elif child_asset['type'] == "Web Bookmark":
                                            c_new_content = st.text_input("URL", value=child_asset['content'], key=f"edit_url_rel_Rules_{item['id']}_{child_asset['id']}_{rel['relation_type']}_{rel['relation_alias']}")
                                            
                                        if st.button("💾 Save Changes", key=f"save_edit_rel_Rules_{item['id']}_{child_asset['id']}_{rel['relation_type']}_{rel['relation_alias']}", type="secondary"):
                                            try:
                                                from services.skills import update_skill
                                                if child_asset['category'] == "Skills":
                                                    update_skill(
                                                        item_id=child_asset['id'],
                                                        name=c_new_name,
                                                        content=c_new_content,
                                                        description=c_new_desc,
                                                        tags=c_new_tags,
                                                        file_blob=c_new_file_bytes,
                                                        file_name=c_new_file_name
                                                    )
                                                else:
                                                    update_rule(
                                                        item_id=child_asset['id'],
                                                        name=c_new_name,
                                                        content=c_new_content,
                                                        description=c_new_desc,
                                                        tags=c_new_tags,
                                                        file_blob=c_new_file_bytes,
                                                        file_name=c_new_file_name
                                                    )
                                                
                                                from services.rules import update_rule_relation
                                                update_rule_relation(
                                                    rule_id=item['id'],
                                                    child_id=child_asset['id'],
                                                    old_type=rel['relation_type'],
                                                    old_alias=rel['relation_alias'],
                                                    new_type=c_new_type,
                                                    new_alias=c_new_alias
                                                )
                                                st.success("✅ Relation and Asset updated successfully!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"❌ {e}")
                        else:
                            st.info("No relations linked to this Rule yet.")
                            
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
                                    key=f"cand_select_Rules_{item['id']}"
                                )
                                selected_candidate = next(c for c in candidates if c['name'] == selected_candidate_name)
                                
                                rel_type = st.selectbox("Relation Type", ["reference", "asset", "tool","resources"], key=f"cand_type_Rules_{item['id']}")
                                
                                # Default alias based on child file_name or sanitized name
                                default_alias = selected_candidate.get("file_name") or f"{selected_candidate['name'].replace(' ', '_').lower()}.md"
                                rel_alias = st.text_input("Relation Filename / Alias", value=default_alias, key=f"cand_alias_Rules_{item['id']}")
                                
                                if st.button("Link Existing Item", key=f"btn_link_Rules_{item['id']}", type="primary"):
                                    try:
                                        add_rule_relation(item['id'], selected_candidate['id'], rel_type, rel_alias)
                                        st.success("Successfully linked item!")
                                        st.rerun()
                                    except Exception as err:
                                        st.error(f"Error: {err}")
                                        
                        with tab_link_url:
                            import_url = st.text_input("🌐 Enter URL to import", placeholder="https://...", key=f"import_url_Rules_{item['id']}")
                            
                            # Fields to capture child metadata
                            child_name = st.text_input("Asset Name", key=f"import_name_Rules_{item['id']}")
                            child_type = st.selectbox("Storage Type", ["Markdown Text", "Real File Upload"], key=f"import_storage_Rules_{item['id']}")
                            child_desc = st.text_area("Asset Description", key=f"import_desc_Rules_{item['id']}")
                            child_tags = st.text_input("Category Tags (comma-separated)", key=f"import_tags_Rules_{item['id']}")
                            
                            # Relation fields
                            import_rel_type = st.selectbox("Relation Type", ["reference", "asset", "tool","resources"], key=f"import_type_Rules_{item['id']}")
                            import_rel_alias = st.text_input("Relation Filename / Alias", key=f"import_alias_Rules_{item['id']}")
                            
                            # Button to fetch
                            st.button(
                                "Fetch & Pre-fill URL Content", 
                                key=f"btn_fetch_url_Rules_{item['id']}", 
                                on_click=perform_relation_fetch, 
                                args=(
                                    f"import_url_Rules_{item['id']}",
                                    f"import_name_Rules_{item['id']}",
                                    f"import_storage_Rules_{item['id']}",
                                    f"import_desc_Rules_{item['id']}",
                                    f"import_tags_Rules_{item['id']}",
                                    f"import_alias_Rules_{item['id']}",
                                    f"fetched_content_Rules_{item['id']}",
                                    f"error_fetch_Rules_{item['id']}"
                                )
                            )
                            
                            error_err = st.session_state.get(f"error_fetch_Rules_{item['id']}")
                            if error_err:
                                st.error(error_err)
                                        
                            fetched_content = st.session_state.get(f"fetched_content_Rules_{item['id']}")
                            if fetched_content:
                                with st.expander("📄 View Fetched Content Preview"):
                                    st.code(fetched_content[:1000] + ("\n... [truncated]" if len(fetched_content) > 1000 else ""))
                                    
                                if st.button("Save & Link Imported Item", key=f"btn_save_imported_Rules_{item['id']}", type="primary"):
                                    try:
                                        # Child category matches parent category: Rules
                                        child_category = "Rules"
                                        
                                        # Create the customization first
                                        if child_type == "Real File Upload":
                                            file_blob = fetched_content.encode("utf-8")
                                            file_name = import_rel_alias or f"{child_name}.txt"
                                            child_new_id = create_rule(child_name, child_type, fetched_content, file_blob, file_name, child_desc, child_tags)
                                        else:
                                            child_new_id = create_rule(child_name, child_type, fetched_content, None, None, child_desc, child_tags)
                                                
                                        # Establish relationship
                                        add_rule_relation(item['id'], child_new_id, import_rel_type, import_rel_alias)
                                        
                                        # Clear fetched state
                                        st.session_state[f"fetched_content_Rules_{item['id']}"] = None
                                        st.success("✅ Successfully imported, saved and linked the remote asset!")
                                        st.rerun()
                                    except Exception as err:
                                        st.error(f"Error saving imported item: {err}")

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