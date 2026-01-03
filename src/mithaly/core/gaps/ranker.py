"""Priority Ranker - Orders tasks/gaps based on criticality using heuristic or LLM."""
from typing import List, Dict, Any

class PriorityRanker:
    """Sorts and ranks analysis items."""
    
    def rank_gaps(self, gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort gaps by impact and urgency. 
        Simple heuristic: Critical > High > Medium > Low.
        """
        priority_map = {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3,
            "unknown": 4
        }
        
        def get_score(g):
            impact = g.get('impact', 'unknown').lower()
            return priority_map.get(impact, 4)

        # Sort stable
        return sorted(gaps, key=get_score)

    def select_top_tasks(self, gaps: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        sorted_gaps = self.rank_gaps(gaps)
        return sorted_gaps[:limit]
