"""Workspace construction helpers."""

from src.domain.entities import Workspace


def create_workspace():
    """Create an empty in-memory representation of a law firm."""

    return Workspace(
        statistics={
            "clients": 0,
            "cases": 0,
            "organizations": 0,
            "persons": 0,
            "documents": 0,
        }
    )
