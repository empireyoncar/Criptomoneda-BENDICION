"""Repository for P2P user reputation and profile operations."""

from __future__ import annotations

from typing import Any

from p2p_db import run_query


def get_user_reputation(user_id: str) -> dict[str, Any]:
    """Get complete reputation profile for a user including stats and recent comments."""
    stats_rows = run_query(
        """
        SELECT
            %s AS user_id,
            COALESCE(profile.bio, '') AS bio,
            COALESCE(order_stats.total_orders, 0) AS total_orders,
            COALESCE(order_stats.completed_orders, 0) AS completed_orders,
            COALESCE(order_stats.cancelled_orders, 0) AS cancelled_orders,
            COALESCE(order_stats.completion_rate, 0) AS completion_rate,
            COALESCE(rating_stats.total_ratings, 0) AS total_ratings,
            COALESCE(rating_stats.average_score, 0) AS average_score,
            COALESCE(rating_stats.positive_comments, 0) AS positive_comments,
            COALESCE(rating_stats.negative_comments, 0) AS negative_comments
        FROM (SELECT 1) AS anchor
        LEFT JOIN LATERAL (
            SELECT bio
            FROM p2p_user_profiles
            WHERE user_id = %s
        ) AS profile ON TRUE
        LEFT JOIN LATERAL (
            SELECT
                COUNT(*)::INT AS total_orders,
                COUNT(*) FILTER (WHERE status IN ('released', 'completed'))::INT AS completed_orders,
                COUNT(*) FILTER (WHERE status IN ('cancelled', 'refunded'))::INT AS cancelled_orders,
                COALESCE(
                    ROUND(
                        (
                            COUNT(*) FILTER (WHERE status IN ('released', 'completed'))::numeric
                            / NULLIF(COUNT(*)::numeric, 0)
                        ) * 100,
                        0
                    ),
                    0
                )::INT AS completion_rate
            FROM p2p_orders
            WHERE buyer_id = %s OR seller_id = %s
        ) AS order_stats ON TRUE
        LEFT JOIN LATERAL (
            SELECT
                COUNT(*)::INT AS total_ratings,
                COALESCE(ROUND(AVG(score)::numeric, 2), 0) AS average_score,
                COUNT(*) FILTER (WHERE score >= 4 AND comment <> '')::INT AS positive_comments,
                COUNT(*) FILTER (WHERE score <= 2 AND comment <> '')::INT AS negative_comments
            FROM p2p_ratings
            WHERE to_user_id = %s
        ) AS rating_stats ON TRUE
        """,
        (user_id, user_id, user_id, user_id, user_id),
    )
    comments = run_query(
        """
        SELECT from_user_id, score, comment, created_at
        FROM p2p_ratings
        WHERE to_user_id = %s AND comment <> ''
        ORDER BY created_at DESC
        LIMIT 50
        """,
        (user_id,),
    )
    result = stats_rows[0] if stats_rows else {
        "user_id": user_id,
        "bio": "",
        "total_orders": 0,
        "completed_orders": 0,
        "cancelled_orders": 0,
        "completion_rate": 0,
        "total_ratings": 0,
        "average_score": 0,
        "positive_comments": 0,
        "negative_comments": 0,
    }
    result["comments"] = comments
    return result


def upsert_user_profile(user_id: str, bio: str) -> dict[str, Any]:
    """Create or update user profile bio."""
    rows = run_query(
        """
        INSERT INTO p2p_user_profiles (user_id, bio, updated_at)
        VALUES (%s, %s, NOW())
        ON CONFLICT (user_id) DO UPDATE
        SET bio = EXCLUDED.bio,
                updated_at = NOW()
        RETURNING user_id, bio, updated_at
        """,
        (user_id, bio),
    )
    return rows[0]
