import urllib.request
import re
from core.exceptions import AssetFetchError

def parse_frontmatter(content):
    """Extracts name, description, and tags from YAML frontmatter, returning the full content intact."""
    if not content:
        return None, None, None, ""
        
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if match:
        frontmatter = match.group(1)
        
        # Match 'title:' or 'name:'
        name_match = re.search(r'^(?:title|name):\s*(.+)$', frontmatter, re.MULTILINE | re.IGNORECASE)
        name = name_match.group(1).strip() if name_match else None
        
        # Match 'category:' and map it to tags
        cat_match = re.search(r'^category:\s*(.+)$', frontmatter, re.MULTILINE | re.IGNORECASE)
        tags = cat_match.group(1).strip() if cat_match else None
        
        # Match 'description:', looking ahead for the next key to safely capture multi-line text
        desc_match = re.search(r'^description:\s*(.*?)(?=\n^[a-zA-Z0-9_-]+:|\Z)', frontmatter, re.MULTILINE | re.IGNORECASE | re.DOTALL)
        desc = None
        if desc_match:
            desc = re.sub(r'\s+', ' ', desc_match.group(1)).strip()
        
        return name, desc, tags, content 
    return None, None, None, content

def fetch_remote_content(url):
    """Fetches text content from a remote URL."""
    url = url.strip()
    if not url:
        raise AssetFetchError("URL cannot be empty.")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            return response.read().decode("utf-8")
    except Exception as e:
        raise AssetFetchError(f"Failed to fetch URL: {e}")
