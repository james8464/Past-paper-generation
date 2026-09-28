"""Local reference retrieval: scope first, text ranking second, no fallback."""

import json
import re
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlparse

from Backend.Core.education_context import EducationContext

CATEGORIES = frozenset(
    {
        "programme",
        "assessment_rules",
        "official_paper",
        "official_correction",
        "academic_resource",
        "teacher_correction",
    }
)


class EvidenceGap(ValueError):
    """No eligible source supports a requested reference query."""


@dataclass(frozen=True)
class SourceDocument:
    id: str
    context: EducationContext
    curriculum_version: str
    category: str
    authority: str
    url: str
    retrieved_at: str
    sha256: str
    session: int
    centre: str
    rights: str
    split: str

    def __post_init__(self):
        if not isinstance(self.context, EducationContext):
            raise ValueError("Source context is required")
        for name in ("id", "curriculum_version", "authority", "centre"):
            if (
                not isinstance(getattr(self, name), str)
                or not getattr(self, name).strip()
            ):
                raise ValueError(f"Missing source {name}")
        if self.category not in CATEGORIES:
            raise ValueError("Unknown source category")
        if self.rights not in {"reference-only", "redistribution-cleared"}:
            raise ValueError("Source rights require review before indexing")
        if self.split not in {"reference", "holdout"}:
            raise ValueError("Unknown corpus split")
        if not re.fullmatch(r"[a-f0-9]{64}", self.sha256):
            raise ValueError("Invalid source hash")
        if urlparse(self.url).scheme != "https" or not urlparse(self.url).hostname:
            raise ValueError("Source requires an HTTPS provenance URL")
        if datetime.fromisoformat(self.retrieved_at).tzinfo is None:
            raise ValueError("Retrieval date requires a timezone")
        if type(self.session) is not int or not 1900 <= self.session <= 2200:
            raise ValueError("Invalid source session")


@dataclass(frozen=True)
class ReferenceHit:
    source_id: str
    source_sha256: str
    page: int
    text: str
    url: str
    category: str


class ReferenceIndex:
    def __init__(self, path: Path):
        self.connection = sqlite3.connect(path)
        self.connection.execute("PRAGMA foreign_keys=ON")
        version = self.connection.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1):
            self.connection.close()
            raise ValueError("Unsupported reference index version")
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY, scope TEXT NOT NULL, curriculum TEXT NOT NULL,
                category TEXT NOT NULL, split TEXT NOT NULL, metadata TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id),
                page INTEGER NOT NULL, text TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS source_scope ON sources(scope, curriculum, category, split);
            PRAGMA user_version=1;
        """)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.connection.close()

    @staticmethod
    def _json(value):
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )

    def add(
        self, source: SourceDocument, content: str | bytes, pages: list[tuple[int, str]]
    ):
        raw = content.encode("utf-8") if isinstance(content, str) else content
        if sha256(raw).hexdigest() != source.sha256:
            raise ValueError("Source content hash mismatch")
        if not pages or any(
            type(page) is not int or page < 1 or not text.strip()
            for page, text in pages
        ):
            raise ValueError("Non-empty numbered source pages are required")
        if len({page for page, _ in pages}) != len(pages):
            raise ValueError("Duplicate source page")
        metadata = self._json(asdict(source))
        previous = self.connection.execute(
            "SELECT metadata FROM sources WHERE id=?", (source.id,)
        ).fetchone()
        if previous:
            stored = self.connection.execute(
                "SELECT page,text FROM chunks WHERE source_id=? ORDER BY page",
                (source.id,),
            ).fetchall()
            if previous[0] != metadata or stored != sorted(pages):
                raise ValueError(
                    "Source identity already exists with different content or metadata"
                )
            return
        with self.connection:
            self.connection.execute(
                "INSERT INTO sources VALUES (?,?,?,?,?,?)",
                (
                    source.id,
                    self._json(source.context.to_dict()),
                    source.curriculum_version,
                    source.category,
                    source.split,
                    metadata,
                ),
            )
            self.connection.executemany(
                "INSERT INTO chunks(source_id,page,text) VALUES (?,?,?)",
                [(source.id, page, text) for page, text in pages],
            )

    def retrieve(
        self,
        context: EducationContext,
        curriculum: str,
        query: str,
        *,
        categories: tuple[str, ...],
        limit: int = 4,
    ) -> list[ReferenceHit]:
        if not isinstance(context, EducationContext) or not curriculum.strip():
            raise ValueError("Complete reference scope is required")
        if not categories or set(categories) - CATEGORIES or not 1 <= limit <= 20:
            raise ValueError("Invalid reference categories or limit")
        tokens = sorted(set(re.findall(r"[^\W_]+", query.casefold())))
        if not tokens:
            raise EvidenceGap("La recherche ne contient aucun terme exploitable.")
        # FTS is deliberately populated ONLY with eligible chunks. A global FTS
        # query followed by filtering can rank/leak unrelated curriculum content.
        eligible = self.connection.execute(
            f"SELECT c.id,c.page,c.text,s.metadata FROM chunks c JOIN sources s ON s.id=c.source_id WHERE s.scope=? AND s.curriculum=? AND s.split='reference' AND s.category IN ({','.join('?' for _ in categories)})",
            (self._json(context.to_dict()), curriculum, *categories),
        ).fetchall()
        with sqlite3.connect(":memory:") as ranking:
            ranking.execute("CREATE VIRTUAL TABLE ranked USING fts5(text)")
            ranking.executemany(
                "INSERT INTO ranked(rowid,text) VALUES (?,?)",
                [(row[0], row[2]) for row in eligible],
            )
            matches = ranking.execute(
                "SELECT rowid FROM ranked WHERE ranked MATCH ? ORDER BY bm25(ranked),rowid LIMIT ?",
                (" OR ".join(f'"{token}"' for token in tokens), limit),
            ).fetchall()
        by_id = {row[0]: row for row in eligible}
        hits = []
        for (row_id,) in matches:
            _, page, text, metadata = by_id[row_id]
            source = json.loads(metadata)
            hits.append(
                ReferenceHit(
                    source["id"],
                    source["sha256"],
                    page,
                    text,
                    source["url"],
                    source["category"],
                )
            )
        if not hits:
            raise EvidenceGap(
                "Aucune référence compatible : ajoutez des sources vérifiées pour ce programme."
            )
        return hits
