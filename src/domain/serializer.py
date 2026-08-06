"""Pure serialization helpers for the domain persistence boundary."""

import json
from datetime import datetime

from src.domain.candidates import LearningCandidate


def datetime_to_text(value):
    return value.isoformat() if value is not None else None


def text_to_datetime(value):
    return datetime.fromisoformat(value) if value else None


def metadata_to_text(metadata):
    return json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True)


def text_to_metadata(value):
    return json.loads(value) if value else {}


def candidate_to_record(candidate):
    return (
        candidate.id,
        candidate.entity_type,
        candidate.canonical_name,
        candidate.source,
        candidate.confidence,
        metadata_to_text(candidate.metadata),
        int(candidate.requires_confirmation),
        candidate.reason,
        candidate.status,
        datetime_to_text(candidate.created_at),
        datetime_to_text(candidate.updated_at),
    )


def candidate_from_row(row):
    return LearningCandidate(
        id=row["id"],
        entity_type=row["entity_type"],
        canonical_name=row["canonical_name"],
        source=row["source"],
        confidence=row["confidence"],
        metadata=text_to_metadata(row["metadata"]),
        requires_confirmation=bool(row["requires_confirmation"]),
        reason=row["reason"],
        status=row["status"],
        created_at=text_to_datetime(row["created_at"]),
        updated_at=text_to_datetime(row["updated_at"]),
    )
