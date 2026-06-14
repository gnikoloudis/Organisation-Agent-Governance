class AssetValidationError(Exception):
    """Raised when validation (like JSON schema validation or field requirements) fails."""
    pass

class AssetFetchError(Exception):
    """Raised when fetching content from a remote URL fails."""
    pass

class AssetNotFoundError(Exception):
    """Raised when a requested asset is not found in the database."""
    pass
