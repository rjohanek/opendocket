"""
LLM-based Discourse Summarizer

Generates per-document summaries of public discourse, with source citations.
Uses the Anthropic Claude API for summarization.
"""

import logging
from typing import Optional
from datetime import datetime

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def generate_discourse_summary(
    doc_id: str,
    doc_title: str,
    discourse_items: list[dict],
) -> Optional[str]:
    """
    Generate a sourced summary of public discourse about a specific document.

    Args:
        doc_id: The document reference number
        doc_title: The document title
        discourse_items: List of discourse item dicts with platform, title, text, etc.

    Returns:
        A summary string with inline source citations, or None if generation fails.
    """
    if not settings.anthropic_api_key:
        logger.info("Anthropic API not configured — skipping summarization")
        return None

    if not discourse_items:
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        # Build context from discourse items
        source_context = _build_source_context(discourse_items)

        prompt = f"""You are summarizing public discourse about a specific government document.

Document: {doc_id} — "{doc_title}"

Below are mentions of this document from news articles, social media posts, legal filings,
and forum discussions. Summarize the key themes, claims, and controversies in the public
discourse about this document.

REQUIREMENTS:
1. Every factual claim in your summary MUST cite its source by [Platform — Source Name]
2. Focus on what is UNIQUE about the discourse on THIS specific document
3. Note any disputes, controversies, or conflicting interpretations
4. If the document is discussed in connection with other documents, mention which ones
5. Note if the document has been removed/modified and what the public response was
6. Keep the summary to 2-4 paragraphs
7. Write in a neutral, informative tone

Source material:
{source_context}"""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    except ImportError:
        logger.warning("anthropic package not installed — skipping summarization")
        return None
    except Exception as e:
        logger.error(f"Discourse summarization failed for {doc_id}: {e}")
        return None


def _build_source_context(items: list[dict], max_items: int = 30) -> str:
    """Build a formatted context string from discourse items for the LLM prompt."""
    # Sort by engagement score (most impactful first) and take top N
    sorted_items = sorted(items, key=lambda x: x.get("engagement_score", 0), reverse=True)
    top_items = sorted_items[:max_items]

    lines = []
    for item in top_items:
        date_str = ""
        if item.get("date"):
            try:
                date_str = f" ({item['date'][:10]})"
            except (TypeError, IndexError):
                pass

        engagement = ""
        if item.get("engagement_score"):
            engagement = f" [engagement: {item['engagement_score']}]"

        source_label = f"[{item.get('platform', 'Unknown')} — {item.get('source_name', 'Unknown')}]"
        title = item.get("title", "Untitled")
        text = item.get("text_excerpt", "")[:300]

        lines.append(f"{source_label}{date_str}{engagement}")
        lines.append(f"  Title: {title}")
        if text:
            lines.append(f"  Excerpt: {text}")
        lines.append("")

    return "\n".join(lines)


async def generate_co_mention_analysis(
    doc_pairs: list[tuple[str, str, int]],
) -> Optional[str]:
    """
    Generate an analysis of why certain documents are frequently discussed together.

    Args:
        doc_pairs: List of (doc_id_1, doc_id_2, co_mention_count) tuples
    """
    if not settings.anthropic_api_key or not doc_pairs:
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        pairs_text = "\n".join(
            f"- {d1} and {d2}: co-mentioned {count} times"
            for d1, d2, count in doc_pairs[:20]
        )

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": f"""These government document pairs are frequently discussed together online.
Briefly explain the likely connections between the most co-mentioned pairs:

{pairs_text}

Keep your response to 1-2 paragraphs. Focus on why these specific combinations appear together in public discourse."""}],
        )

        return response.content[0].text

    except Exception as e:
        logger.error(f"Co-mention analysis failed: {e}")
        return None
