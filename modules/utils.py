import re

def sanitize_filename(name: str) -> str:
    """
    Sanitizes a string to be used as a filename.
    Removes invalid characters and replaces spaces/hyphens with underscores.
    """
    if not name:
        return "untitled"
    # Remove characters that are not alphanumeric, underscore, hyphen, or space
    name = re.sub(r'[^\w\s-]', '', name).strip()
    # Replace multiple spaces/hyphens with a single underscore
    name = re.sub(r'[-\s]+', '_', name)
    return name

def add_http_if_missing(url: str) -> str:
    """Adds http:// if the URL doesn't have a scheme."""
    if not url:
        return ""
    if not url.startswith(('http://', 'https://')):
        return 'http://' + url
    return url