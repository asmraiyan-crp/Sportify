"""
schemas.py  —  Pydantic v2
──────────────────────────────────────────────────────────────────────────────
All request/response schemas for Sportify.
Mirrors every SQLAlchemy model in models.py exactly.

Install:
    pip install pydantic[email] pydantic-settings

Pydantic v2 conventions used here:
    • BaseModel                – base for all schemas
    • model_config             – replaces inner class Config
    • model_validator          – replaces @root_validator
    • field_validator          – replaces @validator
    • ConfigDict(from_attributes=True) – replaces orm_mode = True
      Allows  MySchema.model_validate(orm_obj)  to work directly.
    • Literal                  – replaces Regex/OneOf for strict choices

Naming convention:
    XxxOut        – serialise ORM → JSON  (response body)
    XxxCreate     – validate JSON → dict  (POST body)
    XxxUpdate     – validate JSON → dict  (PUT/PATCH body, all fields Optional)
    XxxNested     – lightweight read-only, embedded inside parent Out schemas
    XxxFilter     – query-string parameters for list endpoints
"""

from __future__ import annotations

from datetime import datetime, date, timezone
from typing import Any, Dict, List, Optional, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


# ─── Shared config ────────────────────────────────────────────────────────────

class _Base(BaseModel):
    """All schemas inherit this so orm_mode is always on."""
    model_config = ConfigDict(from_attributes=True)


# ══════════════════════════════════════════════════════════════════════════════
# SPORT
# ══════════════════════════════════════════════════════════════════════════════

class SportNested(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    sport_id: int
    name:     str


class SportOut(_Base):
    sport_id:    int
    name:        str
    description: Optional[str]  = None
    created_at:  Optional[datetime] = None


class SportCreate(BaseModel):
    name:        str   = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class SportUpdate(BaseModel):
    name:        Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


# ══════════════════════════════════════════════════════════════════════════════
# LEAGUE
# ══════════════════════════════════════════════════════════════════════════════

class LeagueNested(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    league_id: int
    name:      str
    season:    str


class LeagueOut(_Base):
    league_id:       int
    sport:           Optional[SportNested] = None
    name:            str
    country:         Optional[str]      = None
    season:          str
    external_api_id: Optional[str]      = None
    created_at:      Optional[datetime] = None


class LeagueCreate(BaseModel):
    sport_id: int   = Field(..., gt=0)
    name:     str   = Field(..., min_length=1, max_length=150)
    country:  Optional[str] = None
    season:   str   = Field(..., min_length=1, max_length=20)


class LeagueUpdate(BaseModel):
    name:    Optional[str] = Field(None, min_length=1, max_length=150)
    country: Optional[str] = None
    season:  Optional[str] = Field(None, min_length=1, max_length=20)


# ══════════════════════════════════════════════════════════════════════════════
# TEAM
# ══════════════════════════════════════════════════════════════════════════════

class TeamNested(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    team_id:  int
    name:     str
    logo_url: Optional[str] = None
    country:  Optional[str] = None


class TeamOut(_Base):
    team_id:         int
    sport:           Optional[SportNested] = None
    name:            str
    country:         Optional[str]      = None
    founded_year:    Optional[int]      = None
    home_ground:     Optional[str]      = None
    logo_url:        Optional[str]      = None
    external_api_id: Optional[str]      = None
    created_at:      Optional[datetime] = None


class TeamCreate(BaseModel):
    sport_id:     int  = Field(..., gt=0)
    name:         str  = Field(..., min_length=1, max_length=150)
    country:      Optional[str] = None
    founded_year: Optional[int] = Field(None, ge=1800, le=2100)
    home_ground:  Optional[str] = None
    logo_url:     Optional[str] = None


class TeamUpdate(BaseModel):
    name:         Optional[str] = Field(None, min_length=1, max_length=150)
    country:      Optional[str] = None
    founded_year: Optional[int] = Field(None, ge=1800, le=2100)
    home_ground:  Optional[str] = None
    logo_url:     Optional[str] = None


# ══════════════════════════════════════════════════════════════════════════════
# PROFILE  (manual auth — bcrypt password, no Supabase Auth)
# ══════════════════════════════════════════════════════════════════════════════

class ProfileNested(BaseModel):
    """Embedded inside review / comment responses — no sensitive fields."""
    model_config = ConfigDict(from_attributes=True)
    id:           UUID
    display_name: Optional[str] = None
    role:         str


class ProfileOut(_Base):
    """Safe profile response — password_hash is NEVER included."""
    id:           UUID
    email:        EmailStr
    display_name: Optional[str] = None
    role:         str
    team_managed: Optional[int] = None
    is_active:    bool
    created_at:   Optional[datetime] = None
    updated_at:   Optional[datetime] = None


# ── Auth input schemas ────────────────────────────────────────────────────────

class RegisterCreate(BaseModel):
    email:        EmailStr
    password:     str = Field(..., min_length=8, max_length=128)
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


class LoginCreate(BaseModel):
    email:    EmailStr
    password: str = Field(..., min_length=1)


class TokenOut(BaseModel):
    """Response body after successful login."""
    access_token:  str
    token_type:    str = "Bearer"
    expires_in:    int             # seconds until access token expires
    user:          ProfileOut


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token:        str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


class ProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)


class AdminRoleUpdate(BaseModel):
    role:         Literal["fan", "team_manager", "admin"]
    team_managed: Optional[int] = Field(None, gt=0)

    @model_validator(mode="after")
    def check_team_managed(self) -> "AdminRoleUpdate":
        if self.role == "team_manager" and self.team_managed is None:
            raise ValueError(
                "team_managed is required when role is team_manager."
            )
        if self.role != "team_manager":
            self.team_managed = None   # clear when downgrading role
        return self


# ══════════════════════════════════════════════════════════════════════════════
# PLAYER
# ══════════════════════════════════════════════════════════════════════════════

class PlayerNested(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    player_id:     int
    name:          str
    position_role: Optional[str] = None
    injury_status: str


class PlayerOut(_Base):
    player_id:         int
    team:              Optional[TeamNested]  = None
    sport:             Optional[SportNested] = None
    name:              str
    nationality:       Optional[str]      = None
    date_of_birth:     Optional[date]     = None
    position_role:     Optional[str]      = None
    jersey_number:     Optional[int]      = None
    profile_image_url: Optional[str]      = None
    injury_status:     str
    injury_updated_at: Optional[datetime] = None
    external_api_id:   Optional[str]      = None
    created_at:        Optional[datetime] = None


class InjuryUpdate(BaseModel):
    injury_status: Literal["fit", "injured", "doubtful"]


# ══════════════════════════════════════════════════════════════════════════════
# GAME MATCH
# ══════════════════════════════════════════════════════════════════════════════

class MatchOut(_Base):
    match_id:        int
    league:          Optional[LeagueNested] = None
    home_team:       Optional[TeamNested]   = None
    away_team:       Optional[TeamNested]   = None
    match_datetime:  Optional[datetime]     = None
    venue:           Optional[str]          = None
    status:          str
    home_score:      int = 0
    away_score:      int = 0
    elapsed_time:    Optional[int]          = None
    extra_data:      Optional[Dict[str, Any]] = None
    external_api_id: Optional[str]          = None
    created_at:      Optional[datetime]     = None
    updated_at:      Optional[datetime]     = None


class MatchDetailOut(MatchOut):
    """Extends MatchOut — adds player stats and highlights."""
    player_stats: List["PlayerMatchStatOut"] = []
    highlights:   List["HighlightOut"]       = []


class MatchListFilter(BaseModel):
    """Query-string parameters for GET /matches."""
    sport:     Optional[str] = None
    league_id: Optional[int] = Field(None, gt=0)
    status:    Optional[Literal["scheduled", "live", "finished", "postponed", "cancelled"]] = None
    date_from: Optional[date] = None
    date_to:   Optional[date] = None
    page:      int = Field(1,  ge=1)
    limit:     int = Field(20, ge=1, le=100)

    @model_validator(mode="after")
    def check_date_range(self) -> "MatchListFilter":
        if self.date_from and self.date_to:
            if self.date_from > self.date_to:
                raise ValueError("date_from must be before or equal to date_to.")
        return self


# ══════════════════════════════════════════════════════════════════════════════
# PLAYER MATCH STAT
# ══════════════════════════════════════════════════════════════════════════════

class PlayerMatchStatOut(_Base):
    stat_id:        int
    player:         Optional[PlayerNested]  = None
    match_id:       int
    minutes_played: int = 0
    goals:          int = 0
    assists:        int = 0
    yellow_cards:   int = 0
    red_cards:      int = 0
    runs_scored:    int = 0
    wickets:        int = 0
    extra_stats:    Optional[Dict[str, Any]] = None


# ══════════════════════════════════════════════════════════════════════════════
# REVIEW
# ══════════════════════════════════════════════════════════════════════════════

class ReviewOut(_Base):
    review_id:  int
    match_id:   int
    user:       Optional[ProfileNested] = None
    rating:     int
    body:       Optional[str]      = None
    is_hidden:  bool               = False
    created_at: Optional[datetime] = None


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5,
                        description="Star rating between 1 (worst) and 5 (best).")
    body:   Optional[str] = Field(None, max_length=2000)


class ReviewWithStats(BaseModel):
    """Response body for GET /matches/:id/reviews."""
    model_config = ConfigDict(from_attributes=True)
    average_rating: Optional[float] = None
    total_reviews:  int
    reviews:        List[ReviewOut]


# ══════════════════════════════════════════════════════════════════════════════
# COMMENT
# ══════════════════════════════════════════════════════════════════════════════

class CommentOut(_Base):
    comment_id:  int
    user:        Optional[ProfileNested] = None
    entity_type: str
    entity_id:   int
    parent_id:   Optional[int]      = None
    body:        str
    is_hidden:   bool               = False
    created_at:  Optional[datetime] = None
    edited_at:   Optional[datetime] = None


class CommentCreate(BaseModel):
    entity_type: Literal["match", "player"] = Field(..., description="'match' or 'player'")
    entity_id:   int = Field(..., gt=0)
    body:        str = Field(..., min_length=1, max_length=2000)
    parent_id:   Optional[int] = Field(None, gt=0)


class CommentUpdate(BaseModel):
    """15-minute edit window enforced in the Flask route — not here."""
    body: str = Field(..., min_length=1, max_length=2000)


# ══════════════════════════════════════════════════════════════════════════════
# PLAYER RATING
# ══════════════════════════════════════════════════════════════════════════════

class PlayerRatingOut(_Base):
    rating_id:  int
    player_id:  int
    match_id:   int
    user:       Optional[ProfileNested] = None
    rating:     int
    created_at: Optional[datetime] = None


class PlayerRatingCreate(BaseModel):
    player_id: int = Field(..., gt=0)
    match_id:  int = Field(..., gt=0)
    rating:    int = Field(..., ge=1, le=5)


class PlayerRatingAvg(BaseModel):
    """Summary for GET /players/:id/ratings."""
    model_config = ConfigDict(from_attributes=True)
    player_id:      int
    average_rating: Optional[float] = None
    total_ratings:  int


# ══════════════════════════════════════════════════════════════════════════════
# HIGHLIGHT
# ══════════════════════════════════════════════════════════════════════════════

class HighlightOut(_Base):
    highlight_id: int
    match_id:     int
    title:        str
    video_url:    str
    added_by:     Optional[UUID]     = None
    created_at:   Optional[datetime] = None


class HighlightCreate(BaseModel):
    match_id:  int = Field(..., gt=0)
    title:     str = Field(..., min_length=1, max_length=300)
    video_url: str = Field(..., min_length=10) 


# ══════════════════════════════════════════════════════════════════════════════
# FAN EVENT
# ══════════════════════════════════════════════════════════════════════════════

class FanEventOut(_Base):
    event_id:    int
    title:       str
    description: Optional[str]      = None
    event_date:  Optional[datetime] = None
    location:    Optional[str]      = None
    capacity:    int
    registered:  int = 0            # computed in Flask route via COUNT query
    spots_left:  int = 0            # computed: capacity - registered
    created_by:  Optional[UUID]     = None
    created_at:  Optional[datetime] = None


class FanEventCreate(BaseModel):
    title:       str      = Field(..., min_length=1, max_length=300)
    description: Optional[str] = Field(None, max_length=2000)
    event_date:  datetime
    location:    Optional[str] = Field(None, max_length=300)
    capacity:    int      = Field(100, ge=1, le=32767)

    @field_validator("event_date")
    @classmethod
    def must_be_future(cls, v: datetime) -> datetime:
        now = datetime.now(tz=timezone.utc)
        # Make v timezone-aware if it isn't
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v <= now:
            raise ValueError("event_date must be in the future.")
        return v


class FanEventUpdate(BaseModel):
    title:       Optional[str]      = Field(None, min_length=1, max_length=300)
    description: Optional[str]      = None
    event_date:  Optional[datetime] = None
    location:    Optional[str]      = None
    capacity:    Optional[int]      = Field(None, ge=1, le=32767)


# ══════════════════════════════════════════════════════════════════════════════
# EVENT REGISTRATION
# ══════════════════════════════════════════════════════════════════════════════

class EventRegistrationOut(_Base):
    registration_id: int
    event_id:        int
    user_id:         UUID
    registered_at:   Optional[datetime] = None


# ══════════════════════════════════════════════════════════════════════════════
# FOLLOW SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

class FollowTeamOut(_Base):
    user_id:     UUID
    team_id:     int
    team:        Optional[TeamNested]   = None
    followed_at: Optional[datetime]     = None


class FollowPlayerOut(_Base):
    user_id:     UUID
    player_id:   int
    player:      Optional[PlayerNested] = None
    followed_at: Optional[datetime]     = None


class FollowingOut(BaseModel):
    """Response body for GET /users/me/following."""
    model_config = ConfigDict(from_attributes=True)
    teams:   List[FollowTeamOut]   = []
    players: List[FollowPlayerOut] = []


# ══════════════════════════════════════════════════════════════════════════════
# STANDINGS  (computed — no ORM model, direct SQL function result)
# ══════════════════════════════════════════════════════════════════════════════

class StandingRow(BaseModel):
    """One row in the league table."""
    model_config = ConfigDict(from_attributes=True)
    pos:       int
    team_id:   int
    team_name: str
    logo_url:  Optional[str] = None
    played:    int
    won:       int
    drawn:     int
    lost:      int
    gf:        int
    ga:        int
    gd:        int   # computed: gf - ga
    pts:       int


class StandingsOut(BaseModel):
    """Response body for GET /leagues/:id/standings."""
    model_config = ConfigDict(from_attributes=True)
    league:     LeagueNested
    standings:  List[StandingRow]
    updated_at: Optional[datetime] = None


# ══════════════════════════════════════════════════════════════════════════════
# PERSONALISED FEED
# ══════════════════════════════════════════════════════════════════════════════

class FeedMatchOut(BaseModel):
    """Match shown in personalised feed — includes reason for showing."""
    model_config = ConfigDict(from_attributes=True)
    match_id:       int
    league:         Optional[LeagueNested] = None
    home_team:      Optional[TeamNested]   = None
    away_team:      Optional[TeamNested]   = None
    match_datetime: Optional[datetime]     = None
    status:         str
    home_score:     int = 0
    away_score:     int = 0
    elapsed_time:   Optional[int]          = None
    reason:         str                    # e.g. "Following Arsenal"


class FeedOut(BaseModel):
    """Response body for GET /users/me/feed."""
    model_config = ConfigDict(from_attributes=True)
    matches: List[FeedMatchOut] = []
    total:   int


# ══════════════════════════════════════════════════════════════════════════════
# SYNC LOG  (scheduler audit trail)
# ══════════════════════════════════════════════════════════════════════════════

class SyncLogOut(_Base):
    log_id:           int
    sync_type:        str
    started_at:       datetime
    finished_at:      Optional[datetime] = None
    records_fetched:  int = 0
    records_upserted: int = 0
    status:           str
    error_message:    Optional[str] = None


class SyncTrigger(BaseModel):
    """Input for POST /admin/sync/trigger."""
    sync_type: Literal["live", "fixtures", "standings", "player_stats"] = Field(
        ...,
        description="Which scheduler job to run manually.",
    )


# ══════════════════════════════════════════════════════════════════════════════
# GENERIC WRAPPERS
# ══════════════════════════════════════════════════════════════════════════════

class PaginationMeta(BaseModel):
    """Embedded in any paginated list response."""
    page:        int
    limit:       int
    total:       int
    total_pages: int
    has_next:    bool
    has_prev:    bool


class MessageOut(BaseModel):
    """Generic success message response."""
    message: str


class ErrorOut(BaseModel):
    """Standard error response body — all Flask error handlers return this."""
    error:   str
    code:    Optional[str] = None    # machine-readable code, e.g. "DUPLICATE_REVIEW"
    details: Optional[Dict[str, Any]] = None   # field-level validation errors


# ══════════════════════════════════════════════════════════════════════════════
# REBUILD forward refs  (required because some schemas reference each other)
# ══════════════════════════════════════════════════════════════════════════════

MatchDetailOut.model_rebuild()