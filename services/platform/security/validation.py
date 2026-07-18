class ValidationError(Exception):
    pass

def validate_query(query: str, max_length: int = 250):
    if not query:
        raise ValidationError("Query cannot be empty.")
        
    if len(query) > max_length:
        raise ValidationError(f"Query exceeds maximum length of {max_length} characters.")
        
    # Basic sanitization (e.g., reject excessive special characters if needed)
    # For now just strip whitespace
    return query.strip()
