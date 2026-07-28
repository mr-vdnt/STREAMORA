from datetime import datetime
import hashlib

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
            "holiday_name": holiday_name,
            "hour": hour
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

    def select_hero(self, heroes: list, context: dict) -> dict:
        if not heroes:
            return None
            
        # Context-aware hero selection. For evening/night, boost thriller/action.
        # For morning, boost comedy/family. 
        # Fallback to a deterministic rotation based on the hour to avoid the erratic 10s rotation.
        
        time_of_day = context.get("time_of_day", "morning")
        
        scored_heroes = []
        for h in heroes:
            score = 1.0
            genres = str(h.get("genres", "")).lower()
            if time_of_day in ["evening", "night"] and ("thriller" in genres or "action" in genres or "crime" in genres):
                score += 2.0
            if time_of_day == "morning" and ("comedy" in genres or "family" in genres):
                score += 2.0
            if context.get("is_weekend") and ("family" in genres or "animation" in genres):
                score += 1.5
                
            scored_heroes.append((h, score))
            
        # Sort by contextual score (desc) and then deterministically pick from the top contenders
        # based on the current hour.
        scored_heroes.sort(key=lambda x: x[1], reverse=True)
        top_candidates = [h for h, s in scored_heroes[:3]]
        
        hour = context.get("hour", 0)
        idx = hour % len(top_candidates)
        return top_candidates[idx]
