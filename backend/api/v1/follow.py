"""
follow.py  —  Flask Blueprint
──────────────────────────────────────────────────────────────────────────────
Follow / Unfollow system for teams and players.

Routes (all require authentication):

    GET    /api/v1/users/me/following        – lists of teams + players followed
    POST   /api/v1/follow/team/<team_id>     – follow a team   (idempotent)
    DELETE /api/v1/follow/team/<team_id>     – unfollow a team
    POST   /api/v1/follow/player/<player_id> – follow a player (idempotent)
    DELETE /api/v1/follow/player/<player_id> – unfollow a player

Registration in app.py  (add these two lines):
    from api.v1.follow import me_bp, follow_bp
    app.register_blueprint(me_bp,     url_prefix="/api/v1/users")
    app.register_blueprint(follow_bp, url_prefix="/api/v1/follow")

Models used   : UserFollowTeam, UserFollowPlayer, Team, Player   (model.py)
Schemas used  : FollowingOut, FollowTeamOut, FollowPlayerOut,
                TeamNested, PlayerNested, MessageOut, ErrorOut   (schemas.py)
──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from functools import wraps
from uuid import UUID

from flask import Blueprint, jsonify, request, g
from sqlalchemy.orm import joinedload

from database import SessionLocal
from model.model import UserFollowTeam, UserFollowPlayer, Team, Player
from model.schemas import (
    FollowingOut,
    FollowTeamOut,
    FollowPlayerOut,
    MessageOut,
    ErrorOut,
)


# ══════════════════════════════════════════════════════════════════════════════
# Blueprints
# Two separate blueprints because their url_prefixes differ:
#   me_bp     → registered at /api/v1/users
#   follow_bp → registered at /api/v1/follow
# ══════════════════════════════════════════════════════════════════════════════

me_bp     = Blueprint("me",     __name__)
follow_bp = Blueprint("follow", __name__)


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def get_db():
    """Return a SQLAlchemy session."""
    return SessionLocal()


# ── Auth decorator ────────────────────────────────────────────────────────────
# IMPORTANT: Replace the body of require_auth with your real JWT verification.
# Your existing auth_bp likely already has this logic — extract it into a
# shared decorator (e.g. in auth/utils.py) and import it here instead.
#
# The decorator MUST:
#   1. Read the Authorization header  →  "Bearer <token>"
#   2. Verify the JWT and decode the payload
#   3. Store the user's UUID string in  g.current_user_id
#   4. Return 401 if the token is missing or invalid

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify(
                ErrorOut(error="Authorization header missing", code="UNAUTHORIZED").model_dump()
            ), 401

        token = auth_header.removeprefix("Bearer ").strip()

        # ── Swap this block with your real JWT decode once auth is ready ──
        try:
            UUID(token)                  # validates it looks like a UUID
            g.current_user_id = token    # treat the token itself as the user UUID
        except ValueError:
            return jsonify(
                ErrorOut(error="Invalid token", code="UNAUTHORIZED").model_dump()
            ), 401
        # ─────────────────────────────────────────────────────────────────

        return f(*args, **kwargs)
    return decorated
    # @wraps(f)
    # def decorated(*args, **kwargs):
    #     # ── STUB: remove the two lines below and add your real JWT logic ──────
    #     # For testing without auth, hard-code a UUID that exists in your DB:
    #     # g.current_user_id = "00000000-0000-0000-0000-000000000001"

    #     auth_header = request.headers.get("Authorization", "")
    #     if not auth_header.startswith("Bearer "):
    #         return jsonify(
    #             ErrorOut(error="Authorization header missing or malformed",
    #                      code="UNAUTHORIZED").model_dump()
    #         ), 401

    #     token = auth_header.removeprefix("Bearer ").strip()

    #     # ── Replace with your real JWT decode logic ───────────────────────────
    #     # Temporary: treat the raw token value as the user UUID (for smoke tests)
    #     # In production this MUST be replaced with actual JWT verification.
    #     try:
    #         UUID(token)           # validates it is a UUID
    #         g.current_user_id = token
    #     except ValueError:
    #         return jsonify(
    #             ErrorOut(error="Invalid token", code="UNAUTHORIZED").model_dump()
    #         ), 401
    #     # ─────────────────────────────────────────────────────────────────────

    #     return f(*args, **kwargs)
    # return decorated


def _current_uuid() -> UUID:
    """Return the authenticated user's UUID from g."""
    return UUID(g.current_user_id)


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/users/me/following
# ══════════════════════════════════════════════════════════════════════════════

@me_bp.route("/me/following", methods=["GET"])
@require_auth
def get_following():
    """
    GET /api/v1/users/me/following
    ──────────────────────────────
    Returns the full list of teams and players the authenticated user follows.

    Response 200: FollowingOut
        {
          "teams":   [ { user_id, team_id, team: { team_id, name, logo_url, country }, followed_at }, … ],
          "players": [ { user_id, player_id, player: { player_id, name, position_role, injury_status }, followed_at }, … ]
        }
    """
    db  = get_db()
    uid = _current_uuid()

    try:
        # ── followed teams ────────────────────────────────────────────────────
        team_follows = (
            db.query(UserFollowTeam)
            .options(joinedload(UserFollowTeam.team))
            .filter(UserFollowTeam.user_id == uid)
            .order_by(UserFollowTeam.followed_at.desc())
            .all()
        )

        # ── followed players ──────────────────────────────────────────────────
        player_follows = (
            db.query(UserFollowPlayer)
            .options(joinedload(UserFollowPlayer.player))
            .filter(UserFollowPlayer.user_id == uid)
            .order_by(UserFollowPlayer.followed_at.desc())
            .all()
        )

        response = FollowingOut(
            teams   = [FollowTeamOut.model_validate(f)   for f in team_follows],
            players = [FollowPlayerOut.model_validate(f) for f in player_follows],
        )

        return jsonify(response.model_dump(mode="json")), 200

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/follow/team/<team_id>
# ══════════════════════════════════════════════════════════════════════════════

@follow_bp.route("/team/<int:team_id>", methods=["POST"])
@require_auth
def follow_team(team_id: int):
    """
    POST /api/v1/follow/team/<team_id>
    ───────────────────────────────────
    Follow a team.  Idempotent — calling it again on an already-followed team
    returns 200 without creating a duplicate row.

    Response 200: MessageOut  (already following)
    Response 201: FollowTeamOut
    Response 404: ErrorOut  (team not found)
    """
    db  = get_db()
    uid = _current_uuid()

    try:
        # ── verify team exists ────────────────────────────────────────────────
        team = db.query(Team).filter(Team.team_id == team_id).first()
        if team is None:
            return jsonify(ErrorOut(error=f"Team {team_id} not found", code="NOT_FOUND").model_dump()), 404

        # ── idempotency check ─────────────────────────────────────────────────
        existing = (
            db.query(UserFollowTeam)
            .filter(UserFollowTeam.user_id == uid, UserFollowTeam.team_id == team_id)
            .first()
        )
        if existing:
            return jsonify(MessageOut(message=f"Already following team {team_id}.").model_dump()), 200

        # ── insert ────────────────────────────────────────────────────────────
        follow = UserFollowTeam(user_id=uid, team_id=team_id)
        db.add(follow)
        db.commit()
        db.refresh(follow)

        # reload with relationship for full response
        follow = (
            db.query(UserFollowTeam)
            .options(joinedload(UserFollowTeam.team))
            .filter(UserFollowTeam.user_id == uid, UserFollowTeam.team_id == team_id)
            .first()
        )

        return jsonify(FollowTeamOut.model_validate(follow).model_dump(mode="json")), 201

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# DELETE /api/v1/follow/team/<team_id>
# ══════════════════════════════════════════════════════════════════════════════

@follow_bp.route("/team/<int:team_id>", methods=["DELETE"])
@require_auth
def unfollow_team(team_id: int):
    """
    DELETE /api/v1/follow/team/<team_id>
    ──────────────────────────────────────
    Unfollow a team.

    Response 200: MessageOut
    Response 404: ErrorOut  (not currently following)
    """
    db  = get_db()
    uid = _current_uuid()

    try:
        follow = (
            db.query(UserFollowTeam)
            .filter(UserFollowTeam.user_id == uid, UserFollowTeam.team_id == team_id)
            .first()
        )

        if follow is None:
            return jsonify(
                ErrorOut(error=f"You are not following team {team_id}.", code="NOT_FOUND").model_dump()
            ), 404

        db.delete(follow)
        db.commit()

        return jsonify(MessageOut(message=f"Unfollowed team {team_id}.").model_dump()), 200

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/follow/player/<player_id>
# ══════════════════════════════════════════════════════════════════════════════

@follow_bp.route("/player/<int:player_id>", methods=["POST"])
@require_auth
def follow_player(player_id: int):
    """
    POST /api/v1/follow/player/<player_id>
    ────────────────────────────────────────
    Follow a player.  Idempotent.

    Response 200: MessageOut  (already following)
    Response 201: FollowPlayerOut
    Response 404: ErrorOut  (player not found)
    """
    db  = get_db()
    uid = _current_uuid()

    try:
        # ── verify player exists ──────────────────────────────────────────────
        player = db.query(Player).filter(Player.player_id == player_id).first()
        if player is None:
            return jsonify(ErrorOut(error=f"Player {player_id} not found", code="NOT_FOUND").model_dump()), 404

        # ── idempotency check ─────────────────────────────────────────────────
        existing = (
            db.query(UserFollowPlayer)
            .filter(UserFollowPlayer.user_id == uid, UserFollowPlayer.player_id == player_id)
            .first()
        )
        if existing:
            return jsonify(MessageOut(message=f"Already following player {player_id}.").model_dump()), 200

        # ── insert ────────────────────────────────────────────────────────────
        follow = UserFollowPlayer(user_id=uid, player_id=player_id)
        db.add(follow)
        db.commit()
        db.refresh(follow)

        # reload with relationship
        follow = (
            db.query(UserFollowPlayer)
            .options(joinedload(UserFollowPlayer.player))
            .filter(UserFollowPlayer.user_id == uid, UserFollowPlayer.player_id == player_id)
            .first()
        )

        return jsonify(FollowPlayerOut.model_validate(follow).model_dump(mode="json")), 201

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# DELETE /api/v1/follow/player/<player_id>
# ══════════════════════════════════════════════════════════════════════════════

@follow_bp.route("/player/<int:player_id>", methods=["DELETE"])
@require_auth
def unfollow_player(player_id: int):
    """
    DELETE /api/v1/follow/player/<player_id>
    ─────────────────────────────────────────
    Unfollow a player.

    Response 200: MessageOut
    Response 404: ErrorOut  (not currently following)
    """
    db  = get_db()
    uid = _current_uuid()

    try:
        follow = (
            db.query(UserFollowPlayer)
            .filter(UserFollowPlayer.user_id == uid, UserFollowPlayer.player_id == player_id)
            .first()
        )

        if follow is None:
            return jsonify(
                ErrorOut(error=f"You are not following player {player_id}.", code="NOT_FOUND").model_dump()
            ), 404

        db.delete(follow)
        db.commit()

        return jsonify(MessageOut(message=f"Unfollowed player {player_id}.").model_dump()), 200

    finally:
        db.close()