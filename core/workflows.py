from database.db_manager import save_customization, get_customizations, delete_customization, update_customization, get_customization_by_id
from core.exceptions import AssetValidationError, AssetNotFoundError

CATEGORY_NAME = "Workflows"

def get_workflows():
    """Retrieves all workflow assets."""
    return get_customizations(category=CATEGORY_NAME)

def get_workflow_by_id(item_id):
    """Retrieves a single workflow asset by ID."""
    item = get_customization_by_id(item_id)
    if not item or item["category"] != CATEGORY_NAME:
        raise AssetNotFoundError(f"Workflow asset with ID {item_id} not found.")
    return item

def create_workflow(name, content, description, tags):
    """Creates a new workflow bookmark asset."""
    name = name.strip() if name else ""
    if not name:
        raise AssetValidationError("Please supply a valid item name.")
    if not content or not content.strip():
        raise AssetValidationError("Please supply a valid URL for the bookmark.")
        
    new_id = save_customization(
        category=CATEGORY_NAME,
        name=name,
        type_val="Web Bookmark",
        content=content,
        file_blob=None,
        file_name=None,
        description=description.strip() if description else "",
        tags=tags.strip() if tags else ""
    )
    return new_id

def update_workflow(item_id, name, content, description, tags):
    """Updates an existing workflow bookmark asset."""
    item = get_workflow_by_id(item_id)
    
    name = name.strip() if name else item["name"]
    content = content.strip() if content else item["content"]
    description = description.strip() if description is not None else item["description"]
    tags = tags.strip() if tags is not None else item["tags"]
    
    if not name:
        raise AssetValidationError("Please supply a valid item name.")
    if not content:
        raise AssetValidationError("Please supply a valid URL for the bookmark.")
        
    update_customization(
        item_id=item_id,
        name=name,
        content=content,
        description=description,
        tags=tags,
        file_blob=None,
        file_name=None
    )
    return item_id

def delete_workflow(item_id):
    """Deletes a workflow asset by ID."""
    get_workflow_by_id(item_id) # Ensure it exists and belongs to this category
    delete_customization(item_id)
