"""
sync.py  —  Flask Blueprint
──────────────────────────────────────────────────────────────────────────────
API routes for Scheduler & Sync resources.

All endpoints require admin role.

Admin-only endpoints:
    GET  /api/v1/admin/sync-logs          – paginated list of sync_log rows
    GET  /api/v1/admin/sync-logs/<id>     – single sync log detail
    POST /api/v1/admin/sync/trigger       – manually trigger a sync job
──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Thread

from flask import Blueprint, g, jsonify, request
from pydantic import ValidationError
from sqlalchemy import desc

from core.auth import require_auth, require_role
from database import SessionLocal
from model.model import SyncLog
from model.schemas import (
    ErrorOut,
    MessageOut,
    PaginationMeta,
    SyncLogOut,
    SyncTrigger,
)

sync_bp = Blueprint("sync", __name__)


# ─── DB helper ────────────────────────────────────────────────────────────────

def get_db():
    return SessionLocal()


# ══════════════════════════════════════════════════════════════════════════════
# SYNC JOB RUNNER
# Runs in a background thread when manually triggered.
# Replace each job block with your real sync logic (e.g. call external API,
# upsert matches, update standings, etc.)
# ══════════════════════════════════════════════════════════════════════════════

def run_sync_job(sync_type: str, log_id: int):
    """
    Background worker that executes the sync job and updates the sync_log row.
    Each sync_type block should contain your real API fetch + DB upsert logic.
    """
    db = get_db()
    try:
        log = db.query(SyncLog).filter(SyncLog.log_id == log_id).first()
        if not log:
            return

        records_fetched  = 0
        records_upserted = 0

        # ── swap these blocks with real sync logic ────────────────────────────
        if sync_type == "live":
            # TODO: fetch live match data from external API
            # Example:
            #   matches = fetch_live_matches_from_api()
            #   records_fetched = len(matches)
            #   records_upserted = upsert_matches(db, matches)
            records_fetched  = 0
            records_upserted = 0

        elif sync_type == "fixtures":
            # TODO: fetch upcoming fixtures from external API
            records_fetched  = 0
            records_upserted = 0

        elif sync_type == "standings":
            # TODO: fetch standings from external API
            records_fetched  = 0
            records_upserted = 0

        elif sync_type == "player_stats":
            # TODO: fetch player stats from external API
            records_fetched  = 0
            records_upserted = 0
        # ─────────────────────────────────────────────────────────────────────

        # Mark as success
        log.status           = "success"
        log.finished_at      = datetime.now(tz=timezone.utc)
        log.records_fetched  = records_fetched
        log.records_upserted = records_upserted
        db.commit()

    except Exception as err:
        # Mark as failed with error message
        try:
            log = db.query(SyncLog).filter(SyncLog.log_id == log_id).first()
            if log:
                log.status        = "failed"
                log.finished_at   = datetime.now(tz=timezone.utc)
                log.error_message = str(err)
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/admin/sync-logs
# ══════════════════════════════════════════════════════════════════════════════

@sync_bp.route("/sync-logs", methods=["GET"])
@require_auth
@require_role(["admin"])
def list_sync_logs():
    """
    Paginated list of sync_log rows. Shows scheduler run history.

    Query params:
        ?page=<int>   default 1
        ?limit=<int>  default 20, max 100

    Response 200:
        { "data": [SyncLogOut, …], "meta": PaginationMeta }
    """
    db = get_db()
    try:
        try:
            page  = max(1, int(request.args.get("page",  1)))
            limit = min(100, max(1, int(request.args.get("limit", 20))))
        except (ValueError, TypeError):
            return jsonify(
                ErrorOut(error="Invalid query parameter", code="BAD_QUERY").model_dump()
            ), 400

        total = db.query(SyncLog).count()

        logs = (
            db.query(SyncLog)
            .order_by(desc(SyncLog.started_at))
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        data = [SyncLogOut.model_validate(log).model_dump(mode="json") for log in logs]

        total_pages = max(1, (total + limit - 1) // limit)
        meta = PaginationMeta(
            page=page, limit=limit, total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ).model_dump()

        return jsonify({"data": data, "meta": meta}), 200

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/admin/sync-logs/<id>
# ══════════════════════════════════════════════════════════════════════════════

@sync_bp.route("/sync-logs/<int:log_id>", methods=["GET"])
@require_auth
@require_role(["admin"])
def get_sync_log(log_id: int):
    """
    Single sync log detail including error_message if failed.

    Response 200: SyncLogOut
    Response 404: ErrorOut
    """
    db = get_db()
    try:
        log = db.query(SyncLog).filter(SyncLog.log_id == log_id).first()

        if log is None:
            return jsonify(
                ErrorOut(error=f"Sync log {log_id} not found", code="NOT_FOUND").model_dump()
            ), 404

        return jsonify(SyncLogOut.model_validate(log).model_dump(mode="json")), 200

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/admin/sync/trigger
# ══════════════════════════════════════════════════════════════════════════════

@sync_bp.route("/sync/trigger", methods=["POST"])
@require_auth
@require_role(["admin"])
def trigger_sync():
    """
    Manually trigger a sync job.

    Request body:
        {
            "sync_type": "live" | "fixtures" | "standings" | "player_stats"
        }

    Response 202: { "message": "...", "log_id": <int> }
        Job starts in background. Poll GET /sync-logs/<log_id> to track status.

    Response 400: ErrorOut  (validation error)
    Response 409: ErrorOut  (same sync_type already running)
    """
    db = get_db()
    try:
        try:
            payload = SyncTrigger.model_validate(request.get_json(force=True) or {})
        except ValidationError as exc:
            return jsonify(
                ErrorOut(error="Validation error", code="VALIDATION_ERROR",
                         details=exc.errors()).model_dump()
            ), 400

        # Check if same sync_type is already running
        already_running = (
            db.query(SyncLog)
            .filter(
                SyncLog.sync_type == payload.sync_type,
                SyncLog.status    == "running",
            )
            .first()
        )
        if already_running:
            return jsonify(
                ErrorOut(
                    error=f"A '{payload.sync_type}' sync job is already running. "
                          f"Check log_id {already_running.log_id} for status.",
                    code="SYNC_ALREADY_RUNNING"
                ).model_dump()
            ), 409

        # Create sync log entry with status=running
        log = SyncLog(
            sync_type  = payload.sync_type,
            started_at = datetime.now(tz=timezone.utc),
            status     = "running",
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        log_id = log.log_id

        # Run job in background thread so response returns immediately
        thread = Thread(target=run_sync_job, args=(payload.sync_type, log_id), daemon=True)
        thread.start()

        return jsonify({
            "message": f"Sync job '{payload.sync_type}' started successfully.",
            "log_id":  log_id,
            "status":  "running",
            "hint":    f"Poll GET /api/v1/admin/sync-logs/{log_id} to track progress."
        }), 202

    except Exception as err:
        db.rollback()
        return jsonify(ErrorOut(error=str(err)).model_dump()), 500

    finally:
        db.close()