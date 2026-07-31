from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from services.ingestion.dtos import NormalizedContentDTO, PersonDTO, SeasonDTO


@dataclass
class CreateContentCommand:
    """Command to create a new Content aggregate in the catalog."""

    normalized: NormalizedContentDTO
    source_connector: str
    raw_payload_id: Optional[int] = None
    job_id: Optional[int] = None


@dataclass
class UpdateContentCommand:
    """Command to update an existing Content aggregate."""

    content_id: int
    normalized: NormalizedContentDTO
    changed_fields: Dict[str, tuple] = field(default_factory=dict)  # {field: (old, new)}
    source_connector: str = ""
    raw_payload_id: Optional[int] = None
    job_id: Optional[int] = None


@dataclass
class MergeContentCommand:
    """Command to merge two Content entities (deduplication)."""

    primary_content_id: int
    duplicate_content_id: int
    merge_strategy: str = "freshness_wins"  # "freshness_wins", "completeness_wins", "manual"
    source_connector: str = ""


@dataclass
class DeleteContentCommand:
    """Command to soft-delete a Content entity."""

    content_id: int
    reason: str = ""
    actor: str = "ingestion_pipeline"
