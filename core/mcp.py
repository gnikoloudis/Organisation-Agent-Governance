import json
from jsonschema import validate, ValidationError
from database.db_manager import save_customization, get_customizations, delete_customization, update_customization, get_customization_by_id
from core.exceptions import AssetValidationError, AssetNotFoundError

CATEGORY_NAME = "MCP Services"

MCP_SCHEMA = {
    "type": "object",
    "properties": {
        "mcpServers": {
            "type": "object",
            "patternProperties": {
                "^.*$": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"},
                        "args": {"type": "array", "items": {"type": "string"}},
                        "env": {"type": "object"}
                    },
                    "required": ["command"]
                }
            }
        }
    },
    "required": ["mcpServers"]
}

def validate_mcp_config(content):
    """Validates that content is a valid JSON string and matches the MCP schema."""
    if not content or not content.strip():
        raise AssetValidationError("MCP configuration cannot be empty.")
    try:
        parsed_json = json.loads(content)
        validate(instance=parsed_json, schema=MCP_SCHEMA)
    except json.JSONDecodeError as e:
        raise AssetValidationError(f"JSON Syntax Error at Line {e.lineno}, Column {e.colno}: {e.msg}")
    except ValidationError as e:
        path = " -> ".join([str(p) for p in e.path]) if e.path else "Root Object"
        raise AssetValidationError(f"MCP Schema Error in '{path}': {e.message}")

def get_mcps():
    """Retrieves all MCP service assets."""
    return get_customizations(category=CATEGORY_NAME)

def get_mcp_by_id(item_id):
    """Retrieves a single MCP service asset by ID."""
    item = get_customization_by_id(item_id)
    if not item or item["category"] != CATEGORY_NAME:
        raise AssetNotFoundError(f"MCP service asset with ID {item_id} not found.")
    return item

def create_mcp(name, storage_type, content, file_blob, file_name, description, tags, reference_url=""):
    """Creates a new MCP service asset, validating its configuration if it's a JSON type."""
    name = name.strip() if name else ""
    if not name:
        raise AssetValidationError("Please supply a valid item name.")
        
    if storage_type == "Web Bookmark":
        if not content or not content.strip():
            raise AssetValidationError("Please supply a valid URL for the bookmark.")
    else:
        validate_mcp_config(content)
        
    final_desc = description.strip() if description else ""
    if reference_url and reference_url.strip():
        ref = reference_url.strip()
        final_desc += f"\n\n🔗 **Reference Bookmark:** [{ref}]({ref})"
        
    new_id = save_customization(
        category=CATEGORY_NAME,
        name=name,
        type_val=storage_type,
        content=content,
        file_blob=file_blob,
        file_name=file_name,
        description=final_desc.strip(),
        tags=tags.lower().strip() if tags else ""
    )
    return new_id

def update_mcp(item_id, name, storage_type, content, description, tags, reference_url="", file_blob=None, file_name=None):
    """Updates an existing MCP service asset."""
    item = get_mcp_by_id(item_id)
    
    name = name.strip() if name else item["name"]
    content = content if content is not None else item["content"]
    description = description.strip() if description is not None else item["description"]
    tags = tags if tags is not None else item["tags"]
    
    if storage_type != "Web Bookmark" and content is not None:
        validate_mcp_config(content)
        
    final_desc = description
    if reference_url and reference_url.strip():
        ref = reference_url.strip()
        final_desc += f"\n\n🔗 **Reference Bookmark:** [{ref}]({ref})"
        
    update_customization(
        item_id=item_id,
        name=name,
        content=content,
        description=final_desc.strip(),
        tags=tags.lower().strip() if tags else "",
        file_blob=file_blob,
        file_name=file_name
    )
    return item_id

def delete_mcp(item_id):
    """Deletes an MCP service asset by ID."""
    get_mcp_by_id(item_id) # Ensure it exists and belongs to this category
    delete_customization(item_id)
