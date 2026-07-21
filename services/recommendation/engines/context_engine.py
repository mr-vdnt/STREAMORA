
from datetime import datetime

class ContextEngine:
    def __init__(self):
        pass
        
    def get_current_context(self) -> dict:
        now = datetime.now()
        hour = now.hour
        day = now.weekday()
        
        is_weekend = day >= 5
        time_of_day = "morning"
        if 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 22:
            time_of_day = "evening"
        elif hour >= 22 or hour < 4:
            time_of_day = "night"
            
        # Stub holiday check
        is_holiday = False
        holiday_name = None
        
        return {
            "time_of_day": time_of_day,
            "is_weekend": is_weekend,
            "is_holiday": is_holiday,
            "holiday_name": holiday_name
        }
        
    def reorder_shelves(self, shelves: list, context: dict) -> list:
        # Boost specific shelves based on context
        boosted = []
        regular = []
        
        for shelf in shelves:
            title = shelf.get("title", "").lower()
            if context.get("is_weekend") and ("family" in title or "comedy" in title):
                boosted.append(shelf)
            elif context.get("time_of_day") == "evening" and ("action" in title or "thriller" in title):
                boosted.append(shelf)
            else:
                regular.append(shelf)
                
        return boosted + regular
