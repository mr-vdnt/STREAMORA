from __future__ import annotations
import random
from typing import List, Dict, Any

class ExplorationBandit:
    """
    Epsilon-Greedy Exploration & Serendipity Engine.
    Blends (1 - epsilon)% exploited high-confidence recommendations with epsilon% novel content.
    """

    def __init__(self, epsilon: float = 0.15):
        self.epsilon = epsilon

    def blend_exploitation_exploration(
        self, 
        exploited_candidates: List[Dict[str, Any]], 
        exploration_candidates: List[Dict[str, Any]], 
        total_limit: int = 10
    ) -> List[Dict[str, Any]]:
        num_explore = max(1, int(total_limit * self.epsilon))
        num_exploit = total_limit - num_explore

        selected = list(exploited_candidates[:num_exploit])
        selected_ids = {item.get("id") or item.get("content_id") for item in selected}

        # Select unique exploration items
        explored_added = 0
        for item in exploration_candidates:
            item_id = item.get("id") or item.get("content_id")
            if item_id not in selected_ids:
                selected.append(item)
                selected_ids.add(item_id)
                explored_added += 1
                if explored_added >= num_explore:
                    break

        return selected[:total_limit]
