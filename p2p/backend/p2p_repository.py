"""Facade layer for P2P repository access.

This module re-exports all data access functions from domain-specific
repository modules, maintaining backward compatibility while allowing
code organization by domain entity.

All database operations are delegated to:
  - repository.ofertas_repo
  - repository.ordenes_repo
  - repository.disputas_repo
  - repository.timeout_repo
  - repository.calificaciones_repo
  - repository.reputacion_repo
  - repository.chat_repo

Single database connection managed by p2p_db module.
"""

# Offer operations
from repository.ofertas_repo import (
    cancel_offer,
    create_offer,
    get_offer,
    list_active_offers,
    take_offer,
)

# Order operations
from repository.ordenes_repo import (
    add_escrow_event,
    get_order,
    get_order_detail,
    list_user_orders,
    update_order_status,
)

# Dispute operations
from repository.disputas_repo import (
    create_dispute,
    get_dispute_detail,
    list_disputes,
    resolve_dispute,
)

# Timeout voting operations
from repository.timeout_repo import (
    get_timeout_votes,
    upsert_timeout_vote,
)

# Rating operations
from repository.calificaciones_repo import (
    add_rating,
    count_order_ratings,
    get_order_rating_by_user,
)

# Reputation and profile operations
from repository.reputacion_repo import (
    get_user_reputation,
    upsert_user_profile,
)

# Chat operations
from repository.chat_repo import (
    add_chat_message,
    get_chat_messages,
)

# Public API: all functions available as before
__all__ = [
    # Offers
    "get_offer",
    "create_offer",
    "list_active_offers",
    "take_offer",
    "cancel_offer",
    # Orders
    "get_order",
    "get_order_detail",
    "list_user_orders",
    "update_order_status",
    "add_escrow_event",
    # Disputes
    "create_dispute",
    "resolve_dispute",
    "list_disputes",
    "get_dispute_detail",
    # Timeouts
    "upsert_timeout_vote",
    "get_timeout_votes",
    # Ratings
    "add_rating",
    "get_order_rating_by_user",
    "count_order_ratings",
    # Reputation
    "get_user_reputation",
    "upsert_user_profile",
    # Chat
    "add_chat_message",
    "get_chat_messages",
]
