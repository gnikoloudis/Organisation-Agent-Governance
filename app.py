import streamlit as st
from database.db_manager import init_db
from modules import skills, rules, workflows, mcp, exporter # Add exporter

# Import our new isolated modules
from modules import skills, rules, workflows,mcp

# Set page configurations
st.set_page_config(page_title="Agent Customization Hub", layout="wide")

# Initialize database
init_db()

st.title("🤖 Agent Customization Hub")
st.caption("Keep your agent configurations clean, modular, and deployable.")

# Dictionary mapping sidebar names to their respective modules
CATEGORIES = {
    "Skills": skills,
    "Rules": rules,
    "Workflows": workflows,
    "MCP Services": mcp,
    "Exporter": exporter # Add to menu
}
# Sidebar Navigation
selected_category = st.sidebar.radio("Select Workspace", list(CATEGORIES.keys()))

# Execute the render function of the selected module
selected_module = CATEGORIES[selected_category]
selected_module.render()