import re
from typing import Optional, Dict, Any

FORBIDDEN_VALUES = {
    "Unknown", "Unknown Director", "Unknown Writer", "N/A", "NA",
    "Not Available", "Undisclosed", "Standalone", "0", "$0",
    "null", "undefined", "None"
}

FORBIDDEN_PATTERNS = [
    r"\d+% Match",
    r"Highly correlated",
    r"Streamora AI",
    r"Recommended for you"
]

class MetadataSanitizer:
    @classmethod
    def sanitize_field(cls, value: Any, field_name: Optional[str] = None) -> Optional[str]:
        if value is None:
            return None
        val_str = str(value).strip()
        if val_str in FORBIDDEN_VALUES:
            return None
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, val_str, re.IGNORECASE):
                return None
        return val_str

    @classmethod
    def format_runtime(cls, minutes: int, content_type: str) -> str:
        if content_type.lower() == 'series':
            return f"{minutes} Seasons" if minutes > 1 else f"{minutes} Season"
        else:
            hours = minutes // 60
            remainder = minutes % 60
            if hours > 0:
                return f"{hours}h {remainder}m" if remainder > 0 else f"{hours}h"
            return f"{minutes}m"

    @classmethod
    def format_rating(cls, rating: float, source: str = 'internal') -> dict:
        if source.lower() == 'imdb':
            return {"rating": rating, "rating_source": "imdb", "display": f"IMDb {rating:.1f}/10"}
        return {"rating": rating, "rating_source": "internal", "display": f"Rating {rating:.1f}/10"}

    @classmethod
    def sanitize_dto(cls, dto: dict) -> dict:
        result = {}
        for k, v in dto.items():
            if isinstance(v, dict):
                result[k] = cls.sanitize_dto(v)
            elif isinstance(v, list):
                new_list = []
                for item in v:
                    if isinstance(item, dict):
                        new_list.append(cls.sanitize_dto(item))
                    elif isinstance(item, str):
                        sanitized = cls.sanitize_field(item, k)
                        if sanitized is not None:
                            new_list.append(sanitized)
                    else:
                        new_list.append(item)
                result[k] = new_list
            elif isinstance(v, str):
                result[k] = cls.sanitize_field(v, k)
            else:
                result[k] = v
        return result
