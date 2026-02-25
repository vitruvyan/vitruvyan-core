"""
Vitruvyan INTAKE — Reddit Intake Agent

Media Scope: Reddit posts and comments (via PRAW)
Constraints: NO semantic inference, NO relevance judgment

Compliance: ACCORDO-FONDATIVO-INTAKE-V1.1

Key Principles:
- Extract text literally (descriptive, not interpretative)
- Preserve raw reference + hash
- Emit Evidence Pack + event
- NO domain-specific logic
"""

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from infrastructure.edge.oculus_prime.core.guardrails import IntakeGuardrails

try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False

logger = logging.getLogger(__name__)


class RedditIntakeAgent:
    """
    Pre-epistemic Reddit acquisition agent.

    Responsibilities:
    - Fetch posts/comments from subreddits via PRAW
    - Generate normalized_text (descriptive-literal only)
    - Create immutable Evidence Pack per post
    - Emit oculus_prime.evidence.created event

    DOES NOT:
    - Interpret content semantically (no sentiment scoring)
    - Evaluate relevance or importance
    - Apply domain-specific rules
    - Call Codex directly
    """

    AGENT_ID = "reddit-intake-v1"
    AGENT_VERSION = "1.0.0"
    DEFAULT_POST_LIMIT = 25
    MAX_COMMENT_DEPTH = 3
    MAX_COMMENTS_PER_POST = 10

    def __init__(
        self,
        event_emitter,
        postgres_agent=None,
        client_id: str = "",
        client_secret: str = "",
        user_agent: str = "vitruvyan:oculus_prime:v1.0",
    ):
        """
        Args:
            event_emitter: IntakeEventEmitter instance
            postgres_agent: PostgresAgent for Evidence Pack persistence
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: Reddit API user agent string
        """
        self.event_emitter = event_emitter
        self.postgres_agent = postgres_agent
        self._reddit: Optional[Any] = None
        self._client_id = client_id
        self._client_secret = client_secret
        self._user_agent = user_agent

        if not PRAW_AVAILABLE:
            logger.warning("praw not installed — RedditIntakeAgent will be non-functional")

    @property
    def reddit(self):
        """Lazy-load Reddit client (read-only mode)."""
        if self._reddit is None and PRAW_AVAILABLE:
            self._reddit = praw.Reddit(
                client_id=self._client_id,
                client_secret=self._client_secret,
                user_agent=self._user_agent,
            )
        return self._reddit

    # =========================================================================
    # Public API
    # =========================================================================

    def ingest_subreddit(
        self,
        subreddit_name: str,
        sort: str = "hot",
        limit: int = DEFAULT_POST_LIMIT,
        time_filter: str = "week",
        include_comments: bool = True,
        correlation_id: Optional[str] = None,
    ) -> List[str]:
        """
        Ingest posts from a subreddit.

        Args:
            subreddit_name: Name of subreddit (without r/)
            sort: Sort method: hot, new, top, rising
            limit: Max posts to fetch
            time_filter: Time filter for 'top': hour, day, week, month, year, all
            include_comments: Whether to fetch top-level comments
            correlation_id: Distributed tracing ID

        Returns:
            List of evidence_ids created

        Raises:
            RuntimeError: If praw is not available
            ValueError: If subreddit is inaccessible
        """
        if not PRAW_AVAILABLE or not self.reddit:
            raise RuntimeError("praw not available — install with: pip install praw>=7.0.0")

        subreddit = self.reddit.subreddit(subreddit_name)
        posts = self._fetch_posts(subreddit, sort=sort, limit=limit, time_filter=time_filter)

        evidence_ids: List[str] = []
        for post in posts:
            try:
                eid = self._ingest_post(
                    post,
                    subreddit_name=subreddit_name,
                    include_comments=include_comments,
                    correlation_id=correlation_id,
                )
                evidence_ids.append(eid)
            except Exception as e:
                logger.error("Failed to ingest post %s: %s", getattr(post, "id", "?"), e)

        logger.info(
            "Reddit intake complete: subreddit=r/%s sort=%s posts=%d evidence=%d",
            subreddit_name, sort, len(posts), len(evidence_ids),
        )
        return evidence_ids

    def ingest_post_by_url(
        self,
        url: str,
        include_comments: bool = True,
        correlation_id: Optional[str] = None,
    ) -> str:
        """Ingest a single Reddit post by URL."""
        if not PRAW_AVAILABLE or not self.reddit:
            raise RuntimeError("praw not available")

        submission = self.reddit.submission(url=url)
        return self._ingest_post(
            submission,
            subreddit_name=str(submission.subreddit),
            include_comments=include_comments,
            correlation_id=correlation_id,
        )

    # =========================================================================
    # Internals
    # =========================================================================

    def _fetch_posts(self, subreddit, sort: str, limit: int, time_filter: str) -> list:
        """Fetch posts with the specified sort order."""
        sort_map = {
            "hot": subreddit.hot,
            "new": subreddit.new,
            "rising": subreddit.rising,
            "top": lambda limit: subreddit.top(time_filter=time_filter, limit=limit),
        }
        fetcher = sort_map.get(sort, subreddit.hot)
        return list(fetcher(limit=limit))

    def _ingest_post(
        self,
        post,
        subreddit_name: str,
        include_comments: bool,
        correlation_id: Optional[str],
    ) -> str:
        """Create Evidence Pack from a single Reddit submission."""
        evidence_id = self._generate_evidence_id()
        post_text = self._extract_post_text(post)
        source_hash = self._compute_hash(post_text)

        # Gather top-level comments
        comments_text = ""
        comments_raw: List[Dict[str, Any]] = []
        if include_comments:
            post.comments.replace_more(limit=0)
            for comment in post.comments[:self.MAX_COMMENTS_PER_POST]:
                comments_raw.append({
                    "author": str(getattr(comment, "author", "[deleted]")),
                    "body": comment.body[:2000],
                    "score": comment.score,
                    "created_utc": datetime.fromtimestamp(
                        comment.created_utc, tz=timezone.utc
                    ).isoformat(),
                })
                comments_text += f"\n---\nComment by {getattr(comment, 'author', '[deleted]')}: {comment.body[:2000]}"

        # Build normalized text (literal, no interpretation)
        normalized_text = (
            f"Title: {post.title}\n"
            f"Author: {str(getattr(post, 'author', '[deleted]'))}\n"
            f"Subreddit: r/{subreddit_name}\n"
            f"Score: {post.score} | Comments: {post.num_comments}\n"
            f"---\n{post.selftext[:8000] if post.is_self else f'[Link: {post.url}]'}"
        )
        if comments_text:
            normalized_text += f"\n\n=== Top Comments ===\n{comments_text[:4000]}"

        # Build raw data payload
        raw_data = {
            "post_id": post.id,
            "title": post.title,
            "author": str(getattr(post, "author", "[deleted]")),
            "selftext": post.selftext[:8000] if post.is_self else "",
            "url": post.url,
            "permalink": f"https://reddit.com{post.permalink}",
            "subreddit": subreddit_name,
            "score": post.score,
            "upvote_ratio": post.upvote_ratio,
            "num_comments": post.num_comments,
            "created_utc": datetime.fromtimestamp(
                post.created_utc, tz=timezone.utc
            ).isoformat(),
            "is_self": post.is_self,
            "link_flair_text": post.link_flair_text,
            "comments": comments_raw,
        }

        evidence_pack = {
            "evidence_id": evidence_id,
            "chunk_id": "CHK-0",
            "schema_version": "1.0.0",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "source_ref": {
                "source_type": "document",
                "source_uri": f"reddit://r/{subreddit_name}/comments/{post.id}",
                "source_hash": source_hash,
                "mime_type": "text/plain",
                "byte_size": len(normalized_text.encode("utf-8")),
            },
            "normalized_text": normalized_text,
            "technical_metadata": {
                "extraction_method": "praw",
                "extraction_version": self.AGENT_VERSION,
                "language_detected": None,
                "confidence_score": 1.0,
                "chunk_position": {
                    "start_offset": 0,
                    "end_offset": len(normalized_text),
                    "total_chunks": 1,
                },
                "reddit_metadata": raw_data,
            },
            "integrity": {
                "evidence_hash": self._compute_evidence_hash(
                    evidence_id, "CHK-0", normalized_text, source_hash
                ),
                "immutable": True,
            },
            "sampling_policy_ref": None,
            "tags": ["reddit", f"subreddit:{subreddit_name}"],
        }

        # Guardrails
        IntakeGuardrails.validate_no_semantics(normalized_text, "document")
        IntakeGuardrails.validate_source_hash_required(evidence_pack["source_ref"])

        # Persist
        evidence_pack_ref = self._persist_evidence_pack(evidence_pack)

        # Emit event
        self.event_emitter.emit_evidence_created(
            evidence_id=evidence_id,
            chunk_id="CHK-0",
            source_type="document",
            source_uri=f"reddit://r/{subreddit_name}/comments/{post.id}",
            evidence_pack_ref=evidence_pack_ref,
            source_hash=source_hash,
            intake_agent_id=self.AGENT_ID,
            intake_agent_version=self.AGENT_VERSION,
            byte_size=len(normalized_text.encode("utf-8")),
            language_detected=None,
            correlation_id=correlation_id,
        )

        return evidence_id

    # =========================================================================
    # Helpers
    # =========================================================================

    def _extract_post_text(self, post) -> str:
        """Extract searchable text from post."""
        parts = [post.title]
        if post.is_self and post.selftext:
            parts.append(post.selftext[:8000])
        return "\n".join(parts)

    @staticmethod
    def _generate_evidence_id() -> str:
        return f"EVD-{str(uuid.uuid4()).upper()}"

    @staticmethod
    def _compute_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _compute_evidence_hash(
        evidence_id: str, chunk_id: str, text: str, source_hash: str
    ) -> str:
        composite = f"{evidence_id}{chunk_id}{text[:500]}{source_hash}"
        return hashlib.sha256(composite.encode("utf-8")).hexdigest()

    def _persist_evidence_pack(self, pack: Dict[str, Any]) -> str:
        """Persist Evidence Pack to PostgreSQL (append-only)."""
        ref = f"evidence_packs/{pack['evidence_id']}"
        if self.postgres_agent:
            try:
                self.postgres_agent.execute(
                    """INSERT INTO oculus_evidence_packs (evidence_id, chunk_id, pack_json, created_at)
                       VALUES (%s, %s, %s, NOW())
                       ON CONFLICT (evidence_id, chunk_id) DO NOTHING""",
                    (pack["evidence_id"], pack["chunk_id"], json.dumps(pack)),
                )
            except Exception as e:
                logger.warning("Evidence pack persistence failed: %s", e)
        return ref
