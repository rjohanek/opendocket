"""
Document Matcher

The intelligence that maps unstructured discourse mentions back to
specific document IDs. This is the critical novel component — people
don't always reference documents by their official ID. They might
say "the flight logs," "that FBI interview," or "document 7823."

Matching strategies (in order of confidence):
1. Exact reference number match (highest confidence)
2. Partial ID / Bates number match
3. Entity + category co-occurrence (medium confidence)
4. LLM-assisted matching for ambiguous references (used sparingly)
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional

from app.services.discourse.collectors import DiscourseHit

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    doc_id: str
    confidence: float     # 0.0 to 1.0
    match_reason: str
    matched_text: str = ""


class DocumentMatcher:
    """Maps unstructured text mentions to specific document IDs."""

    def __init__(self, document_index: list[dict], id_pattern: str = ""):
        """
        Args:
            document_index: List of dicts with at minimum 'id', 'title',
                           'entities', 'category' keys.
            id_pattern: Regex pattern for document IDs in this release.
        """
        self.documents = {doc["id"]: doc for doc in document_index}
        self.id_pattern = id_pattern

        # Build reverse lookup indices for faster matching
        self._entity_index = self._build_entity_index()
        self._title_keywords = self._build_title_keywords()

    def match(self, text: str) -> list[MatchResult]:
        """
        Match a text against the document index.
        Returns list of (doc_id, confidence, reason) sorted by confidence desc.
        """
        if not text:
            return []

        matches = []
        text_lower = text.lower()

        # Strategy 1: Exact document ID match (confidence: 1.0)
        matches.extend(self._exact_id_match(text))

        # Strategy 2: Partial ID / numeric reference match (confidence: 0.85)
        matches.extend(self._partial_id_match(text))

        # Strategy 3: Entity + category co-occurrence (confidence: 0.6-0.8)
        matches.extend(self._entity_category_match(text_lower))

        # Strategy 4: Title keyword overlap (confidence: 0.5-0.7)
        matches.extend(self._title_keyword_match(text_lower))

        # Deduplicate by doc_id, keeping highest confidence
        return self._deduplicate_matches(matches)

    def match_discourse_hit(self, hit: DiscourseHit) -> list[MatchResult]:
        """Match a DiscourseHit against the document index.
        Combines title and text for matching."""
        combined_text = f"{hit.title} {hit.text}"
        return self.match(combined_text)

    # ── Strategy implementations ──────────────────────────────────────

    def _exact_id_match(self, text: str) -> list[MatchResult]:
        """Find exact document ID references in text."""
        matches = []
        for doc_id in self.documents:
            if doc_id in text:
                matches.append(MatchResult(
                    doc_id=doc_id,
                    confidence=1.0,
                    match_reason="exact_id_match",
                    matched_text=doc_id,
                ))

        # Also match via the configured pattern
        if self.id_pattern:
            for m in re.finditer(self.id_pattern, text):
                found_id = m.group(0)
                if found_id in self.documents and found_id not in {r.doc_id for r in matches}:
                    matches.append(MatchResult(
                        doc_id=found_id,
                        confidence=1.0,
                        match_reason="pattern_id_match",
                        matched_text=found_id,
                    ))

        return matches

    def _partial_id_match(self, text: str) -> list[MatchResult]:
        """Find partial numeric references that could match document IDs."""
        matches = []

        # Look for standalone numbers that match the numeric portion of IDs
        numbers = re.findall(r'\b(\d{4,7})\b', text)
        for num in numbers:
            for doc_id, doc in self.documents.items():
                if num in doc_id:
                    matches.append(MatchResult(
                        doc_id=doc_id,
                        confidence=0.85,
                        match_reason=f"partial_id_match: '{num}' in {doc_id}",
                        matched_text=num,
                    ))
                    break  # One match per number

        return matches

    def _entity_category_match(self, text_lower: str) -> list[MatchResult]:
        """Match based on co-occurrence of entities and document category."""
        matches = []

        for doc_id, doc in self.documents.items():
            entities = [e.lower() for e in (doc.get("entities") or [])]
            category = (doc.get("category") or "").lower()

            matching_entities = [e for e in entities if e in text_lower]
            category_match = category and category in text_lower

            if len(matching_entities) >= 2:
                confidence = 0.7 if category_match else 0.6
                matches.append(MatchResult(
                    doc_id=doc_id,
                    confidence=confidence,
                    match_reason=f"entity_match: {matching_entities}" + (
                        f" + category '{category}'" if category_match else ""
                    ),
                ))
            elif len(matching_entities) == 1 and category_match:
                matches.append(MatchResult(
                    doc_id=doc_id,
                    confidence=0.5,
                    match_reason=f"entity+category: {matching_entities[0]} + {category}",
                ))

        return matches

    def _title_keyword_match(self, text_lower: str) -> list[MatchResult]:
        """Match based on significant keyword overlap with document titles."""
        matches = []

        for doc_id, keywords in self._title_keywords.items():
            if not keywords:
                continue
            matching = [kw for kw in keywords if kw in text_lower]
            overlap_ratio = len(matching) / len(keywords) if keywords else 0

            if overlap_ratio >= 0.5 and len(matching) >= 2:
                confidence = min(0.7, 0.5 + overlap_ratio * 0.3)
                matches.append(MatchResult(
                    doc_id=doc_id,
                    confidence=confidence,
                    match_reason=f"title_keyword_match: {matching}",
                ))

        return matches

    # ── Index builders ────────────────────────────────────────────────

    def _build_entity_index(self) -> dict[str, list[str]]:
        """Build reverse index: entity_name → [doc_ids]."""
        index = {}
        for doc_id, doc in self.documents.items():
            for entity in (doc.get("entities") or []):
                entity_lower = entity.lower()
                if entity_lower not in index:
                    index[entity_lower] = []
                index[entity_lower].append(doc_id)
        return index

    def _build_title_keywords(self) -> dict[str, list[str]]:
        """Extract significant keywords from each document title."""
        stop_words = {
            "the", "a", "an", "and", "or", "of", "to", "in", "for", "on",
            "with", "at", "by", "from", "is", "was", "are", "were", "be",
            "been", "being", "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "shall",
            "that", "this", "these", "those", "it", "its", "not", "no",
            "re", "regarding", "between", "about", "into", "through",
        }
        index = {}
        for doc_id, doc in self.documents.items():
            title = (doc.get("title") or "").lower()
            words = re.findall(r'\b[a-z]{3,}\b', title)
            keywords = [w for w in words if w not in stop_words]
            index[doc_id] = keywords
        return index

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _deduplicate_matches(matches: list[MatchResult]) -> list[MatchResult]:
        """Keep only the highest-confidence match per document."""
        best = {}
        for m in matches:
            if m.doc_id not in best or m.confidence > best[m.doc_id].confidence:
                best[m.doc_id] = m
        return sorted(best.values(), key=lambda x: x.confidence, reverse=True)
