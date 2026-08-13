"""
Franchise & Canonical Universe Engine for Streamora KIP.

Maps relationships between content entities:
- Sequel / Prequel
- Shared Canonical Universe
- Thematic Twin
"""
from typing import Dict, List, Optional
from services.knowledge.dtos import KnowledgeRelationshipDTO


class FranchiseEngine:
    """Manages franchise boundaries and universe graph relationships."""

    UNIVERSE_CLUSTERS = {
        "mcu": ["Iron Man", "Avengers", "Thor", "Captain America", "Spider-Man", "Doctor Strange", "Guardians of the Galaxy"],
        "dc": ["Batman", "Superman", "Justice League", "Wonder Woman", "The Dark Knight"],
        "star_wars": ["Star Wars", "The Empire Strikes Back", "Return of the Jedi", "The Mandalorian"],
        "nolan_sci_fi": ["Inception", "Interstellar", "Tenet"]
    }

    def detect_relationships(self, source_content_id: int, source_title: str, catalog: List[Dict]) -> List[KnowledgeRelationshipDTO]:
        relationships: List[KnowledgeRelationshipDTO] = []
        source_title_lower = source_title.lower()

        for item in catalog:
            target_id = item["id"]
            if target_id == source_content_id:
                continue

            target_title = item["title"]
            target_title_lower = target_title.lower()

            # Check Universe Clusters
            for cluster_name, titles in self.UNIVERSE_CLUSTERS.items():
                in_source = any(t.lower() in source_title_lower for t in titles)
                in_target = any(t.lower() in target_title_lower for t in titles)

                if in_source and in_target:
                    rel_type = "shared_universe"
                    if (" 2" in target_title or " 3" in target_title or "returns" in target_title_lower) and source_title_lower in target_title_lower:
                        rel_type = "sequel"
                    
                    relationships.append(KnowledgeRelationshipDTO(
                        source_content_id=source_content_id,
                        target_content_id=target_id,
                        relationship_type=rel_type,
                        strength=0.95,
                        provenance=f"franchise_cluster:{cluster_name}"
                    ))

        return relationships
