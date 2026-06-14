import streamlit as st
import json
import urllib.request
import urllib.error
from jsonschema import validate, ValidationError
from database.db_manager import save_customization, get_customizations, delete_customization, update_customization

MCP_SCHEMA = {
    "type": "object",
    "properties": {"mcpServers": {"type": "object", "patternProperties": {"^.*$": {"type": "object", "properties": {"command": {"type": "string"}, "args": {"type": "array", "items": {"type": "string"}}, "env": {"type": "object"}}, "required": ["command"]}}}},
    "required": ["mcpServers"]
}

def perform_mcp_fetch(url_key, content_key):
    """Callback: Fetches pure JSON securely."""
    url = st.session_state.get(url_key, "").strip()
    if not url:
        st.session_state[f"error_{url_key}"] = "Please enter a URL first."
        return
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            fetched_data = response.read().decode("utf-8")
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
            # FIX: Restricted back to pure json
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
            clean_tags = tags.lower().strip() if tags else ""
            final_desc = description.strip()
            if reference_url.strip(): final_desc += f"\n\n🔗 **Reference Bookmark:** [{reference_url.strip()}]({reference_url.strip()})"
            final_desc = final_desc.strip()
            
            if not name: st.error("Please supply a valid item name.")
            elif storage_type == "Web Bookmark" and not content: st.error("Please supply a valid URL for the bookmark.")
            elif storage_type in ["JSON Config", "Real File Upload"]:
                if not content.strip(): st.error("Please provide the JSON configuration.")
                else:
                    try:
                        parsed_json = json.loads(content)
                        validate(instance=parsed_json, schema=MCP_SCHEMA)
                        save_customization("MCP Services", name, storage_type, content, uploaded_file_bytes, uploaded_file_name, final_desc, clean_tags)
                        st.session_state.mcp_clear_form = True
                        st.success("✅ Successfully validated and saved your MCP Service asset!")
                        st.rerun()
                    except json.JSONDecodeError as e: st.error(f"❌ **JSON Syntax Error** at **Line {e.lineno}**, Column {e.colno}:\n`{e.msg}`")
                    except ValidationError as e:
                        path = " -> ".join([str(p) for p in e.path]) if e.path else "Root Object"
                        st.error(f"❌ **MCP Schema Error:**\n* **Location:** `{path}`\n* **Issue:** {e.message}")
            else:
                save_customization("MCP Services", name, storage_type, content, uploaded_file_bytes, uploaded_file_name, final_desc, clean_tags)
                st.session_state.mcp_clear_form = True
                st.success("✅ Successfully saved your MCP Service asset!")
                st.rerun()

    with tab_view:
        st.subheader("Active Assets under MCP Services")
        items = get_customizations(category="MCP Services")
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
                            delete_customization(item['id'])
                            st.rerun()
                    
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

                        elif item['type'] == "Web Bookmark":
                            new_content = st.text_input("URL", value=item['content'], key=f"edit_url_{item['id']}")
                            
                        if st.button("💾 Save Changes", key=f"save_edit_{item['id']}", type="secondary"):
                            clean_new_tags = new_tags.lower().strip() if new_tags else ""
                            final_edit_desc = new_desc.strip()
                            if new_ref.strip(): final_edit_desc += f"\n\n🔗 **Reference Bookmark:** [{new_ref.strip()}]({new_ref.strip()})"
                            
                            if item['type'] in ["JSON Config", "Real File Upload"]:
                                try:
                                    parsed_json = json.loads(new_content)
                                    validate(instance=parsed_json, schema=MCP_SCHEMA)
                                    update_customization(item['id'], new_name, new_content, final_edit_desc.strip(), clean_new_tags)
                                    st.success("✅ Asset updated successfully!")
                                    st.rerun()
                                except json.JSONDecodeError as e: st.error(f"❌ **Syntax Error:** Line {e.lineno}")
                                except ValidationError as e: st.error(f"❌ **Schema Error:** {e.message}")
                            else:
                                update_customization(item['id'], new_name, new_content, final_edit_desc.strip(), clean_new_tags)
                                st.success("✅ Asset updated successfully!")
                                st.rerun()