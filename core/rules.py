from database.db_manager import save_customization, get_customizations, delete_customization, update_customization, get_customization_by_id
from core.exceptions import AssetValidationError, AssetNotFoundError
from core.utils import parse_frontmatter

CATEGORY_NAME = "Rules"

def get_rules():
    """Retrieves all rule assets."""
    return get_customizations(category=CATEGORY_NAME)

def get_rule_by_id(item_id):
    """Retrieves a single rule asset by ID."""
    item = get_customization_by_id(item_id)
    if not item or item["category"] != CATEGORY_NAME:
        raise AssetNotFoundError(f"Rule asset with ID {item_id} not found.")
    return item

def create_rule(name, storage_type, content, file_blob, file_name, description, tags, reference_url=""):
    """Creates a new rule asset, validating inputs and resolving frontmatter."""
    name = name.strip() if name else ""
    if not name:
        raise AssetValidationError("Please supply a valid item name.")
        
    if storage_type == "Web Bookmark":
        if not content or not content.strip():
            raise AssetValidationError("Please supply a valid URL for the bookmark.")
    else:
        if not content or not content.strip():
            raise AssetValidationError("Please provide the text content.")
            
    # Parse frontmatter from content if applicable
    parsed_name, parsed_desc, parsed_tags, _ = parse_frontmatter(content)
    
    final_name = parsed_name if parsed_name else name
    final_desc = parsed_desc if parsed_desc else (description.strip() if description else "")
    final_tags = parsed_tags if parsed_tags else (tags.lower().strip() if tags else "")
    
    if reference_url and reference_url.strip():
        ref = reference_url.strip()
        final_desc += f"\n\n🔗 **Reference Bookmark:** [{ref}]({ref})"
        
    new_id = save_customization(
        category=CATEGORY_NAME,
        name=final_name,
        type_val=storage_type,
        content=content,
        file_blob=file_blob,
        file_name=file_name,
        description=final_desc.strip(),
        tags=final_tags
    )
    return new_id

def update_rule(item_id, name, content, description, tags, reference_url="", file_blob=None, file_name=None):
    """Updates an existing rule asset."""
    # Ensure it exists
    item = get_rule_by_id(item_id)
    
    name = name.strip() if name else item["name"]
    content = content if content is not None else item["content"]
    description = description.strip() if description is not None else item["description"]
    tags = tags if tags is not None else item["tags"]
    
    # Parse frontmatter from new/updated content
    parsed_name, parsed_desc, parsed_tags, _ = parse_frontmatter(content)
    
    # Check if the parsed tag exists and do not duplicate them in new tags
    new_tags = tags.lower().strip() if tags else ""
    if parsed_tags:
        for tag in parsed_tags.split(","):
            tag_clean = tag.strip().lower()
            if tag_clean and tag_clean not in new_tags:
                new_tags = f"{new_tags},{tag_clean}" if new_tags else tag_clean
                
    final_name = parsed_name if parsed_name else name
    final_desc = parsed_desc if parsed_desc else description
    
    if reference_url and reference_url.strip():
        ref = reference_url.strip()
        final_desc += f"\n\n🔗 **Reference Bookmark:** [{ref}]({ref})"
        
    update_customization(
        item_id=item_id,
        name=final_name,
        content=content,
        description=final_desc.strip(),
        tags=new_tags,
        file_blob=file_blob,
        file_name=file_name
    )
    return item_id

def delete_rule(item_id):
    """Deletes a rule asset by ID."""
    get_rule_by_id(item_id) # Ensure it exists and belongs to this category
    delete_customization(item_id)
