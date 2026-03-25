#!/usr/bin/env python3
"""
Seed the database with sample data for development and demo purposes.

Usage:
    docker compose exec api python scripts/seed_data.py
"""

import asyncio
import sys
import os
from datetime import date, datetime

# Add the app to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import async_session, engine
from app.models.base import Base
from app.models.document import Document
from app.models.change_history import ChangeHistory
from app.models.discourse import DiscourseItem, DiscourseSummary, CoMention
from app.models.glossary import GlossaryTerm


SAMPLE_DOCUMENTS = [
    {
        "id": "EFTA-2025-001247",
        "release_slug": "epstein-files",
        "title": "Email correspondence between J. Epstein and G. Maxwell regarding travel arrangements",
        "category": "Emails",
        "status": "available",
        "page_count": 12,
        "date_released": date(2025, 12, 19),
        "source_url": "https://www.justice.gov/epstein/documents/efta-2025-001247",
        "ai_summary": "Email chain (June 2003) discussing private flight logistics between New York and Palm Beach. References 'the house' (identified as Epstein's Palm Beach residence) and 'the pilot' (likely Larry Visoski). Mentions upcoming dinner with unnamed 'professor' and arrangements for 'young assistants' — a phrase flagged in multiple other documents as a potential euphemism.",
        "entities": ["Jeffrey Epstein", "Ghislaine Maxwell", "Larry Visoski"],
        "jargon_terms": ["the house", "the pilot", "young assistants"],
        "discourse_score": 87,
        "mention_count": 2340,
    },
    {
        "id": "EFTA-2025-003891",
        "release_slug": "epstein-files",
        "title": "FBI Interview notes — Witness 14 testimony regarding recruitment patterns",
        "category": "FBI Records",
        "status": "available",
        "page_count": 34,
        "date_released": date(2026, 1, 30),
        "source_url": "https://www.justice.gov/epstein/documents/efta-2025-003891",
        "ai_summary": "Detailed FBI interview notes from 2006 with a witness describing recruitment methods at a Palm Beach high school. Witness describes being approached by an older student who offered 'massage work' for a wealthy man. Contains references to 'the scheduler' (believed to be Sarah Kellen) and a network of recruiters operating through schools and shopping malls.",
        "entities": ["Sarah Kellen", "FBI Agent Rodriguez", "Witness 14"],
        "jargon_terms": ["massage work", "the scheduler", "modeling opportunity"],
        "discourse_score": 94,
        "mention_count": 5120,
    },
    {
        "id": "EFTA-2025-007823",
        "release_slug": "epstein-files",
        "title": "Flight log entries — Aircraft N908JE, January-March 2002",
        "category": "Flight Records",
        "status": "removed",
        "page_count": 8,
        "date_released": date(2025, 12, 19),
        "date_removed": date(2026, 2, 10),
        "source_url": "https://www.justice.gov/epstein/documents/efta-2025-007823",
        "ai_summary": "Partial flight manifest for Epstein's Boeing 727 (tail number N908JE, known publicly as 'the Lolita Express'). Covers 14 flights between Teterboro, NJ and various destinations. Passenger lists include initials and partial names. Document removed by DOJ on Feb 10, 2026; preserved copy available via ArchiveBox.",
        "entities": ["Jeffrey Epstein", "Multiple unnamed passengers"],
        "jargon_terms": ["N908JE", "the island"],
        "discourse_score": 99,
        "mention_count": 12800,
    },
    {
        "id": "EFTA-2026-012001",
        "release_slug": "epstein-files",
        "title": "Ghislaine Maxwell deposition transcript — sealed portions (partial)",
        "category": "Legal Documents",
        "status": "available",
        "page_count": 156,
        "date_released": date(2026, 2, 28),
        "source_url": "https://www.justice.gov/epstein/documents/efta-2026-012001",
        "ai_summary": "Previously sealed portions of Ghislaine Maxwell's civil deposition from Giuffre v. Maxwell. Contains testimony about the organizational structure of Epstein's network, property management across multiple residences, and Maxwell's self-described role as 'head of household.' References 'the black book' (Epstein's contact directory) and 'the schedule' (daily appointment system).",
        "entities": ["Ghislaine Maxwell", "Virginia Giuffre", "Attorney Sigrid McCawley"],
        "jargon_terms": ["head of household", "the black book", "the island"],
        "discourse_score": 96,
        "mention_count": 8900,
    },
    {
        "id": "EFTA-2025-002156",
        "release_slug": "epstein-files",
        "title": "Property records and financial transfers — Zorro Ranch, NM",
        "category": "Financial Records",
        "status": "available",
        "page_count": 22,
        "date_released": date(2025, 12, 19),
        "source_url": "https://www.justice.gov/epstein/documents/efta-2025-002156",
        "ai_summary": "Documentation of property transactions for Epstein's Zorro Ranch in Stanley, New Mexico. Includes LLC structures ('Zorro Trust'), transfer documents, and correspondence about ranch operations. References to 'scientific research' and 'educational programs' that investigators flagged as potential fronts.",
        "entities": ["Zorro Trust LLC", "NM Land Commissioner"],
        "jargon_terms": ["Zorro Trust", "scientific research"],
        "discourse_score": 62,
        "mention_count": 890,
    },
    {
        "id": "EFTA-2026-015443",
        "release_slug": "epstein-files",
        "title": "Blanche-Maxwell recorded conversation transcript — Session 3",
        "category": "Transcripts",
        "status": "available",
        "page_count": 48,
        "date_released": date(2026, 3, 10),
        "source_url": "https://www.justice.gov/epstein/documents/efta-2026-015443",
        "ai_summary": "Third session of recorded conversations between Deputy AG Todd Blanche and Ghislaine Maxwell. Discussion covers Maxwell's knowledge of financial arrangements and offshore accounts. Maxwell references 'the foundation' and names individuals described as 'benefactors.'",
        "entities": ["Todd Blanche", "Ghislaine Maxwell"],
        "jargon_terms": ["the foundation", "benefactors"],
        "discourse_score": 91,
        "mention_count": 6200,
    },
]

SAMPLE_CHANGES = [
    {"doc_id": "EFTA-2025-001247", "action": "added", "timestamp": datetime(2025, 12, 19), "note": "Initial DOJ release (Batch 1)", "detected_by": "changedetection.io"},
    {"doc_id": "EFTA-2025-001247", "action": "removed", "timestamp": datetime(2026, 1, 15), "note": "Removed by DOJ citing 'victim privacy review'", "detected_by": "changedetection.io"},
    {"doc_id": "EFTA-2025-001247", "action": "restored", "timestamp": datetime(2026, 1, 30), "note": "Re-added in Batch 3 release with additional redactions", "detected_by": "changedetection.io"},
    {"doc_id": "EFTA-2025-003891", "action": "added", "timestamp": datetime(2026, 1, 30), "note": "Released in Batch 3", "detected_by": "changedetection.io"},
    {"doc_id": "EFTA-2025-007823", "action": "added", "timestamp": datetime(2025, 12, 19), "note": "Initial DOJ release (Batch 1)", "detected_by": "changedetection.io"},
    {"doc_id": "EFTA-2025-007823", "action": "removed", "timestamp": datetime(2026, 2, 10), "note": "Removed by DOJ — no public explanation provided", "detected_by": "changedetection.io"},
    {"doc_id": "EFTA-2026-012001", "action": "added", "timestamp": datetime(2026, 2, 28), "note": "Released in Batch 5 (sealed materials)", "detected_by": "changedetection.io"},
    {"doc_id": "EFTA-2025-002156", "action": "added", "timestamp": datetime(2025, 12, 19), "note": "Initial DOJ release (Batch 1)", "detected_by": "changedetection.io"},
    {"doc_id": "EFTA-2026-015443", "action": "added", "timestamp": datetime(2026, 3, 10), "note": "Released in Batch 7", "detected_by": "changedetection.io"},
]

SAMPLE_DISCOURSE = [
    {"doc_id": "EFTA-2025-007823", "platform": "Reddit", "source_name": "r/EpsteinFiles", "title": "Flight log analysis: decoded initials from EFTA-2025-007823", "url": "https://reddit.com/r/EpsteinFiles/example1", "text_excerpt": "I've been cross-referencing the passenger initials with known associates from the black book...", "engagement_score": 14200, "type": "social", "date": datetime(2026, 1, 2)},
    {"doc_id": "EFTA-2025-007823", "platform": "News", "source_name": "The Guardian", "title": "Epstein flight logs reveal patterns of travel to private island", "url": "https://theguardian.com/example", "text_excerpt": "Newly released flight logs show a pattern of trips...", "engagement_score": 500, "type": "news", "date": datetime(2026, 1, 5)},
    {"doc_id": "EFTA-2025-007823", "platform": "YouTube", "source_name": "Legal Eagle", "title": "Breaking Down the Epstein Flight Logs", "url": "https://youtube.com/example", "text_excerpt": "Today we're examining what these flight logs actually show from a legal perspective...", "engagement_score": 2100000, "type": "social", "date": datetime(2026, 1, 8)},
    {"doc_id": "EFTA-2025-007823", "platform": "News", "source_name": "CBS News", "title": "DOJ removes flight log documents without explanation", "url": "https://cbsnews.com/example", "text_excerpt": "The DOJ has removed several documents including flight logs...", "engagement_score": 800, "type": "news", "date": datetime(2026, 2, 11)},
    {"doc_id": "EFTA-2025-003891", "platform": "Reddit", "source_name": "r/TrueCrime", "title": "Witness 14 testimony reveals organized recruitment at schools", "url": "https://reddit.com/r/TrueCrime/example", "text_excerpt": "The FBI notes describe a systematic recruitment operation...", "engagement_score": 11300, "type": "social", "date": datetime(2026, 2, 2)},
    {"doc_id": "EFTA-2025-003891", "platform": "News", "source_name": "Miami Herald", "title": "FBI notes detail Epstein recruitment network at local schools", "url": "https://miamiherald.com/example", "text_excerpt": "New FBI interview notes released as part of the Epstein Files...", "engagement_score": 600, "type": "news", "date": datetime(2026, 2, 5)},
    {"doc_id": "EFTA-2026-012001", "platform": "News", "source_name": "New York Times", "title": "Maxwell deposition reveals organizational structure", "url": "https://nytimes.com/example", "text_excerpt": "The unsealed deposition provides unprecedented insight...", "engagement_score": 1200, "type": "news", "date": datetime(2026, 3, 3)},
    {"doc_id": "EFTA-2026-012001", "platform": "YouTube", "source_name": "Law & Crime", "title": "LIVE analysis: Maxwell deposition unsealed portions", "url": "https://youtube.com/example2", "text_excerpt": "We're going through the Maxwell deposition live...", "engagement_score": 3400000, "type": "social", "date": datetime(2026, 3, 1)},
    {"doc_id": "EFTA-2026-015443", "platform": "News", "source_name": "COURIER", "title": "Independent transcription differs from DOJ version", "url": "https://couriernewsroom.com/example", "text_excerpt": "Our independent transcription of the Blanche-Maxwell tapes reveals discrepancies...", "engagement_score": 900, "type": "news", "date": datetime(2026, 3, 12)},
    {"doc_id": "EFTA-2026-015443", "platform": "Reddit", "source_name": "r/EpsteinFiles", "title": "Side-by-side: DOJ vs COURIER transcription of Session 3", "url": "https://reddit.com/r/EpsteinFiles/example2", "text_excerpt": "I've compiled a side-by-side comparison of the two transcriptions...", "engagement_score": 15600, "type": "social", "date": datetime(2026, 3, 13)},
]


async def seed():
    print("Seeding database with sample data...")

    async with async_session() as db:
        # Documents
        for doc_data in SAMPLE_DOCUMENTS:
            existing = await db.get(Document, doc_data["id"])
            if not existing:
                db.add(Document(**doc_data))
        await db.commit()
        print(f"  Added {len(SAMPLE_DOCUMENTS)} documents")

        # Change history
        for ch_data in SAMPLE_CHANGES:
            db.add(ChangeHistory(**ch_data))
        await db.commit()
        print(f"  Added {len(SAMPLE_CHANGES)} change history entries")

        # Discourse items
        for disc_data in SAMPLE_DISCOURSE:
            db.add(DiscourseItem(**disc_data))
        await db.commit()
        print(f"  Added {len(SAMPLE_DISCOURSE)} discourse items")

        # Co-mentions
        co_mentions = [
            ("EFTA-2025-001247", "EFTA-2025-007823", 45),
            ("EFTA-2025-003891", "EFTA-2026-012001", 67),
            ("EFTA-2025-007823", "EFTA-2026-012001", 89),
            ("EFTA-2026-012001", "EFTA-2026-015443", 34),
        ]
        for id1, id2, count in co_mentions:
            db.add(CoMention(doc_id_1=id1, doc_id_2=id2, co_mention_count=count))
        await db.commit()
        print(f"  Added {len(co_mentions)} co-mention pairs")

        # Glossary terms (from the release config seed terms)
        import yaml
        with open("/app/configs/releases/epstein-files.yaml") as f:
            config = yaml.safe_load(f)

        seed_terms = config.get("glossary", {}).get("seed_terms", [])
        for seed in seed_terms:
            existing = await db.execute(
                select(GlossaryTerm).where(
                    GlossaryTerm.release_slug == "epstein-files",
                    GlossaryTerm.term == seed["term"],
                )
            )
            if not existing.scalar_one_or_none():
                db.add(GlossaryTerm(
                    release_slug="epstein-files",
                    term=seed["term"],
                    decoded_meaning=seed["meaning"],
                    confidence=seed.get("confidence", "confirmed"),
                    proposed_by="seed",
                    approved=True,
                ))
        await db.commit()
        print(f"  Added {len(seed_terms)} glossary terms")

    print("Seed complete!")


# Need this import for the glossary seeding query
from sqlalchemy import select

if __name__ == "__main__":
    asyncio.run(seed())
