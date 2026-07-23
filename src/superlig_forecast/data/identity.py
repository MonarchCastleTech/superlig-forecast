"""Conservative canonical identity resolution."""

import re
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ClubAlias:
    """A reviewed source-to-canonical club mapping."""

    source: str
    source_id: str
    observed_name: str
    canonical_id: str


def normalized_name(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold())
    ascii_text = "".join(char for char in folded if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", ascii_text).strip()


class IdentityResolver:
    """Resolves exact source IDs and reviewed aliases without fuzzy guesses."""

    def __init__(self, aliases: list[ClubAlias]) -> None:
        self._by_source = {(item.source, item.source_id): item.canonical_id for item in aliases}

    def resolve_club(self, source: str, source_id: str, name: str, valid_at: date) -> str:
        del valid_at
        reviewed = self._by_source.get((source, source_id))
        if reviewed is not None:
            return reviewed
        stable = uuid.uuid5(uuid.NAMESPACE_URL, f"{source}:{source_id}:{normalized_name(name)}")
        return f"club:{stable}"
