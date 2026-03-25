"""
Discourse Collectors

Each collector pulls mentions from a specific platform and returns
standardized DiscourseHit objects. The pipeline runs all collectors
in parallel, then passes results through the Document Matcher.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import httpx
import feedparser

from app.core.config import get_settings
from app.core.release_config import ReleaseConfig

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class DiscourseHit:
    """Standardized representation of a discourse item from any platform."""
    platform: str           # Reddit, YouTube, News, Legal, Bluesky
    source_name: str        # subreddit, outlet, channel, etc.
    title: str
    url: str
    text: str = ""
    author: str = ""
    date: Optional[datetime] = None
    engagement_score: int = 0
    type: str = "social"    # social, news, legal
    raw_data: dict = field(default_factory=dict)


# ─── GDELT News Collector ─────────────────────────────────────────────────────

async def collect_news_gdelt(config: ReleaseConfig) -> list[DiscourseHit]:
    """
    Collect news articles from GDELT's DOC API.
    Free, no authentication required, covers global news in real-time.
    """
    hits = []

    for query in config.discourse.search_queries[:5]:  # Rate-limit friendly
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    "https://api.gdeltproject.org/api/v2/doc/doc",
                    params={
                        "query": query,
                        "mode": "artlist",
                        "maxrecords": 50,
                        "format": "json",
                        "timespan": "90d",
                        "sort": "DateDesc",
                    },
                )
                if response.status_code != 200:
                    continue

                data = response.json()
                for article in data.get("articles", []):
                    hits.append(DiscourseHit(
                        platform="News",
                        source_name=article.get("domain", ""),
                        title=article.get("title", ""),
                        url=article.get("url", ""),
                        text=article.get("title", ""),  # GDELT doesn't return full text
                        date=_parse_gdelt_date(article.get("seendate")),
                        engagement_score=int(article.get("socialimage", 0) != ""),
                        type="news",
                        raw_data=article,
                    ))
        except Exception as e:
            logger.warning(f"GDELT collection failed for query '{query}': {e}")

    return _deduplicate(hits)


# ─── RSS News Collector ───────────────────────────────────────────────────────

async def collect_news_rss(config: ReleaseConfig) -> list[DiscourseHit]:
    """Collect from configured RSS feeds (targeted high-value outlets)."""
    hits = []
    search_terms = [q.lower() for q in config.discourse.search_queries]

    for feed_url in config.discourse.news_outlets_rss:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title_lower = entry.get("title", "").lower()
                summary_lower = entry.get("summary", "").lower()

                # Only include entries matching our search terms
                if not any(term in title_lower or term in summary_lower for term in search_terms):
                    continue

                hits.append(DiscourseHit(
                    platform="News",
                    source_name=feed.feed.get("title", feed_url),
                    title=entry.get("title", ""),
                    url=entry.get("link", ""),
                    text=entry.get("summary", "")[:500],
                    date=_parse_rss_date(entry),
                    type="news",
                    raw_data=dict(entry),
                ))
        except Exception as e:
            logger.warning(f"RSS collection failed for {feed_url}: {e}")

    return hits


# ─── Reddit Collector ─────────────────────────────────────────────────────────

async def collect_reddit(config: ReleaseConfig) -> list[DiscourseHit]:
    """
    Collect Reddit posts and comments via PRAW (Python Reddit API Wrapper).
    Searches configured subreddits for release-related discussions.
    """
    if not settings.reddit_client_id:
        logger.info("Reddit not configured — skipping collection")
        return []

    hits = []
    try:
        import praw

        reddit = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
        )

        for subreddit_name in config.discourse.subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                for query in config.discourse.search_queries[:3]:
                    for post in subreddit.search(query, sort="relevance", time_filter="year", limit=25):
                        hits.append(DiscourseHit(
                            platform="Reddit",
                            source_name=f"r/{subreddit_name}",
                            title=post.title,
                            url=f"https://reddit.com{post.permalink}",
                            text=post.selftext[:500] if post.selftext else "",
                            author=str(post.author) if post.author else "[deleted]",
                            date=datetime.utcfromtimestamp(post.created_utc),
                            engagement_score=post.score,
                            type="social",
                            raw_data={
                                "score": post.score,
                                "num_comments": post.num_comments,
                                "upvote_ratio": post.upvote_ratio,
                            },
                        ))
            except Exception as e:
                logger.warning(f"Reddit collection failed for r/{subreddit_name}: {e}")

    except ImportError:
        logger.warning("PRAW not installed — skipping Reddit collection")
    except Exception as e:
        logger.warning(f"Reddit collection failed: {e}")

    return _deduplicate(hits)


# ─── YouTube Collector ────────────────────────────────────────────────────────

async def collect_youtube(config: ReleaseConfig) -> list[DiscourseHit]:
    """Collect YouTube videos via the YouTube Data API."""
    if not settings.youtube_api_key:
        logger.info("YouTube not configured — skipping collection")
        return []

    hits = []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            for query in config.discourse.search_queries[:3]:
                response = await client.get(
                    "https://www.googleapis.com/youtube/v3/search",
                    params={
                        "part": "snippet",
                        "q": query,
                        "type": "video",
                        "order": "relevance",
                        "maxResults": 20,
                        "key": settings.youtube_api_key,
                    },
                )
                if response.status_code != 200:
                    continue

                for item in response.json().get("items", []):
                    snippet = item.get("snippet", {})
                    video_id = item.get("id", {}).get("videoId", "")
                    hits.append(DiscourseHit(
                        platform="YouTube",
                        source_name=snippet.get("channelTitle", ""),
                        title=snippet.get("title", ""),
                        url=f"https://www.youtube.com/watch?v={video_id}",
                        text=snippet.get("description", "")[:500],
                        author=snippet.get("channelTitle", ""),
                        date=_parse_iso_date(snippet.get("publishedAt")),
                        type="social",
                        raw_data=item,
                    ))
    except Exception as e:
        logger.warning(f"YouTube collection failed: {e}")

    return _deduplicate(hits)


# ─── CourtListener / RECAP Legal Collector ────────────────────────────────────

async def collect_legal(config: ReleaseConfig) -> list[DiscourseHit]:
    """Collect legal documents from CourtListener's free API."""
    if not settings.courtlistener_api_key:
        logger.info("CourtListener not configured — skipping legal collection")
        return []

    hits = []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            for query in config.discourse.courtlistener_queries[:5]:
                response = await client.get(
                    "https://www.courtlistener.com/api/rest/v4/search/",
                    params={"q": query, "type": "r", "order_by": "dateFiled desc"},
                    headers={"Authorization": f"Token {settings.courtlistener_api_key}"},
                )
                if response.status_code != 200:
                    continue

                for result in response.json().get("results", []):
                    hits.append(DiscourseHit(
                        platform="Legal",
                        source_name=result.get("court", ""),
                        title=result.get("caseName", ""),
                        url=f"https://www.courtlistener.com{result.get('absolute_url', '')}",
                        text=result.get("snippet", "")[:500],
                        date=_parse_iso_date(result.get("dateFiled")),
                        type="legal",
                        raw_data=result,
                    ))
    except Exception as e:
        logger.warning(f"CourtListener collection failed: {e}")

    return hits


# ─── Bluesky Collector (AT Protocol) ─────────────────────────────────────────

async def collect_bluesky(config: ReleaseConfig) -> list[DiscourseHit]:
    """Collect posts from Bluesky via the AT Protocol (fully open, no auth for public data)."""
    hits = []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            for query in config.discourse.search_queries[:3]:
                response = await client.get(
                    "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts",
                    params={"q": query, "limit": 25},
                )
                if response.status_code != 200:
                    continue

                for post in response.json().get("posts", []):
                    record = post.get("record", {})
                    author = post.get("author", {})
                    hits.append(DiscourseHit(
                        platform="Bluesky",
                        source_name=author.get("handle", ""),
                        title=record.get("text", "")[:100],
                        url=f"https://bsky.app/profile/{author.get('handle', '')}/post/{post.get('uri', '').split('/')[-1]}",
                        text=record.get("text", "")[:500],
                        author=author.get("displayName", author.get("handle", "")),
                        date=_parse_iso_date(record.get("createdAt")),
                        engagement_score=post.get("likeCount", 0),
                        type="social",
                        raw_data=post,
                    ))
    except Exception as e:
        logger.warning(f"Bluesky collection failed: {e}")

    return hits


# ─── Aggregate All Collectors ─────────────────────────────────────────────────

async def collect_all(config: ReleaseConfig) -> list[DiscourseHit]:
    """Run all collectors and return combined results."""
    import asyncio

    results = await asyncio.gather(
        collect_news_gdelt(config),
        collect_news_rss(config),
        collect_reddit(config),
        collect_youtube(config),
        collect_legal(config),
        collect_bluesky(config),
        return_exceptions=True,
    )

    all_hits = []
    collector_names = ["GDELT", "RSS", "Reddit", "YouTube", "Legal", "Bluesky"]
    for name, result in zip(collector_names, results):
        if isinstance(result, Exception):
            logger.error(f"Collector {name} failed: {result}")
        else:
            logger.info(f"Collector {name}: {len(result)} hits")
            all_hits.extend(result)

    return all_hits


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _deduplicate(hits: list[DiscourseHit]) -> list[DiscourseHit]:
    """Remove duplicate hits by URL."""
    seen = set()
    unique = []
    for hit in hits:
        if hit.url not in seen:
            seen.add(hit.url)
            unique.append(hit)
    return unique


def _parse_gdelt_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str[:14], "%Y%m%dT%H%M%S")
    except (ValueError, TypeError):
        return None


def _parse_rss_date(entry) -> Optional[datetime]:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        from time import mktime
        return datetime.fromtimestamp(mktime(entry.published_parsed))
    return None


def _parse_iso_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
