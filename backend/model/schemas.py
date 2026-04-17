"""
schemas.py
──────────────────────────────────────────────────────────────────────────────
Marshmallow schemas for every SQLAlchemy model in models.py.

Install:  pip install marshmallow

Usage:
    from schemas import (
        ProfileSchema, LoginSchema, MatchSchema, ReviewSchema, ...
    )

    # Serialise ORM object → JSON dict
    profile_schema = ProfileSchema()
    data = profile_schema.dump(profile_obj)

    # Deserialise + validate JSON body → dict  (raises ValidationError on fail)
    login_schema = LoginSchema()
    validated = login_schema.load(request.get_json())

Schema naming convention
    XxxSchema          – full output schema  (used for GET responses)
    XxxCreateSchema    – validated input for POST  (create)
    XxxUpdateSchema    – validated input for PUT/PATCH  (update, all fields optional)
    XxxNestedSchema    – lightweight read-only view used inside parent schemas
"""

from marshmallow import (
    Schema, fields, validate, validates, validates_schema,
    ValidationError, pre_load, post_load, EXCLUDE
)


# ─────────────────────────────────────────────────────────────────────────────
# SPORT
# ─────────────────────────────────────────────────────────────────────────────

class SportSchema(Schema):
    """Full output for a sport row."""
    sport_id    = fields.Int(dump_only=True)
    name        = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(allow_none=True)
    created_at  = fields.DateTime(dump_only=True)


class SportNestedSchema(Schema):
    """Lightweight sport — embedded inside league / team / player responses."""
    sport_id = fields.Int(dump_only=True)
    name     = fields.Str(dump_only=True)


# ─────────────────────────────────────────────────────────────────────────────
# LEAGUE
# ─────────────────────────────────────────────────────────────────────────────

class LeagueSchema(Schema):
    """Full output for a league row."""
    league_id       = fields.Int(dump_only=True)
    sport_id        = fields.Int(load_only=True)
    sport           = fields.Nested(SportNestedSchema, dump_only=True)
    name            = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    country         = fields.Str(allow_none=True)
    season          = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    external_api_id = fields.Str(allow_none=True, dump_only=True)
    created_at      = fields.DateTime(dump_only=True)


class LeagueCreateSchema(Schema):
    """Validated input for POST /admin/leagues."""
    sport_id = fields.Int(required=True)
    name     = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    country  = fields.Str(load_default=None)
    season   = fields.Str(required=True, validate=validate.Length(min=1, max=20))


class LeagueUpdateSchema(Schema):
    """Validated input for PUT /admin/leagues/:id — all fields optional."""
    name    = fields.Str(validate=validate.Length(min=1, max=150))
    country = fields.Str(allow_none=True)
    season  = fields.Str(validate=validate.Length(min=1, max=20))


class LeagueNestedSchema(Schema):
    """Lightweight league — embedded inside match responses."""
    league_id = fields.Int(dump_only=True)
    name      = fields.Str(dump_only=True)
    season    = fields.Str(dump_only=True)


# ─────────────────────────────────────────────────────────────────────────────
# TEAM
# ─────────────────────────────────────────────────────────────────────────────

class TeamSchema(Schema):
    """Full output for a team row."""
    team_id         = fields.Int(dump_only=True)
    sport_id        = fields.Int(load_only=True)
    sport           = fields.Nested(SportNestedSchema, dump_only=True)
    name            = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    country         = fields.Str(allow_none=True)
    founded_year    = fields.Int(allow_none=True,
                                 validate=validate.Range(min=1800, max=2100))
    home_ground     = fields.Str(allow_none=True)
    logo_url        = fields.Url(allow_none=True)
    external_api_id = fields.Str(allow_none=True, dump_only=True)
    created_at      = fields.DateTime(dump_only=True)


class TeamCreateSchema(Schema):
    """Validated input for POST /admin/teams."""
    sport_id     = fields.Int(required=True)
    name         = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    country      = fields.Str(load_default=None)
    founded_year = fields.Int(load_default=None,
                              validate=validate.Range(min=1800, max=2100))
    home_ground  = fields.Str(load_default=None)
    logo_url     = fields.Url(load_default=None)


class TeamUpdateSchema(Schema):
    """Validated input for PUT /admin/teams/:id."""
    name         = fields.Str(validate=validate.Length(min=1, max=150))
    country      = fields.Str(allow_none=True)
    founded_year = fields.Int(allow_none=True,
                              validate=validate.Range(min=1800, max=2100))
    home_ground  = fields.Str(allow_none=True)
    logo_url     = fields.Url(allow_none=True)


class TeamNestedSchema(Schema):
    """Lightweight team — embedded inside match and player responses."""
    team_id  = fields.Int(dump_only=True)
    name     = fields.Str(dump_only=True)
    logo_url = fields.Str(dump_only=True, allow_none=True)
    country  = fields.Str(dump_only=True, allow_none=True)


# ─────────────────────────────────────────────────────────────────────────────
# PROFILE  (manual auth — password stored as bcrypt hash)
# ─────────────────────────────────────────────────────────────────────────────

class ProfileSchema(Schema):
    """Full output for a profiles row — NEVER include password_hash."""
    id           = fields.UUID(dump_only=True)
    email        = fields.Email(dump_only=True)
    display_name = fields.Str(dump_only=True, allow_none=True)
    role         = fields.Str(dump_only=True,
                              validate=validate.OneOf(["fan", "team_manager", "admin"]))
    team_managed = fields.Int(dump_only=True, allow_none=True)
    is_active    = fields.Bool(dump_only=True)
    created_at   = fields.DateTime(dump_only=True)
    updated_at   = fields.DateTime(dump_only=True)


class ProfileNestedSchema(Schema):
    """Author info embedded inside review / comment responses."""
    id           = fields.UUID(dump_only=True)
    display_name = fields.Str(dump_only=True, allow_none=True)
    role         = fields.Str(dump_only=True)


# ── Auth input schemas ────────────────────────────────────────────────────────

class RegisterSchema(Schema):
    """Validated input for POST /auth/register."""
    email        = fields.Email(required=True)
    password     = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(min=8, max=128),
    )
    display_name = fields.Str(
        load_default=None,
        validate=validate.Length(min=1, max=100),
    )

    @validates("password")
    def validate_password_strength(self, value):
        if not any(c.isupper() for c in value):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in value):
            raise ValidationError("Password must contain at least one digit.")


class LoginSchema(Schema):
    """Validated input for POST /auth/login."""
    email    = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True,
                          validate=validate.Length(min=1))


class PasswordResetRequestSchema(Schema):
    """Validated input for POST /auth/password-reset (request email)."""
    email = fields.Email(required=True)


class PasswordResetConfirmSchema(Schema):
    """Validated input for POST /auth/password-reset/confirm."""
    token        = fields.Str(required=True)
    new_password = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(min=8, max=128),
    )

    @validates("new_password")
    def validate_strength(self, value):
        if not any(c.isupper() for c in value):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in value):
            raise ValidationError("Password must contain at least one digit.")


class ProfileUpdateSchema(Schema):
    """Validated input for PUT /users/me."""
    display_name = fields.Str(validate=validate.Length(min=1, max=100))


class AdminRoleUpdateSchema(Schema):
    """Validated input for PUT /admin/users/:id/role."""
    role         = fields.Str(
        required=True,
        validate=validate.OneOf(["fan", "team_manager", "admin"]),
    )
    team_managed = fields.Int(load_default=None, allow_none=True)

    @validates_schema
    def validate_team_managed(self, data, **kwargs):
        if data.get("role") == "team_manager" and data.get("team_managed") is None:
            raise ValidationError(
                "team_managed is required when role is team_manager.",
                field_name="team_managed",
            )
        if data.get("role") != "team_manager":
            data["team_managed"] = None  # clear it when downgrading


# ─────────────────────────────────────────────────────────────────────────────
# PLAYER
# ─────────────────────────────────────────────────────────────────────────────

class PlayerSchema(Schema):
    """Full output for a player row."""
    player_id         = fields.Int(dump_only=True)
    team_id           = fields.Int(load_only=True, allow_none=True)
    team              = fields.Nested(TeamNestedSchema, dump_only=True, allow_none=True)
    sport_id          = fields.Int(load_only=True)
    sport             = fields.Nested(SportNestedSchema, dump_only=True)
    name              = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    nationality       = fields.Str(allow_none=True)
    date_of_birth     = fields.Date(allow_none=True)
    position_role     = fields.Str(allow_none=True)
    jersey_number     = fields.Int(allow_none=True,
                                   validate=validate.Range(min=1, max=999))
    profile_image_url = fields.Url(allow_none=True)
    injury_status     = fields.Str(dump_only=True,
                                   validate=validate.OneOf(["fit","injured","doubtful"]))
    injury_updated_at = fields.DateTime(dump_only=True, allow_none=True)
    external_api_id   = fields.Str(dump_only=True, allow_none=True)
    created_at        = fields.DateTime(dump_only=True)


class PlayerNestedSchema(Schema):
    """Lightweight player — embedded inside match stat responses."""
    player_id     = fields.Int(dump_only=True)
    name          = fields.Str(dump_only=True)
    position_role = fields.Str(dump_only=True, allow_none=True)
    injury_status = fields.Str(dump_only=True)


class InjuryUpdateSchema(Schema):
    """Validated input for PUT /players/:id/injury  (Manager/Admin only)."""
    injury_status = fields.Str(
        required=True,
        validate=validate.OneOf(["fit", "injured", "doubtful"]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# GAME MATCH
# ─────────────────────────────────────────────────────────────────────────────

class MatchSchema(Schema):
    """Full match output including nested team + league."""
    match_id        = fields.Int(dump_only=True)
    league          = fields.Nested(LeagueNestedSchema, dump_only=True)
    home_team       = fields.Nested(TeamNestedSchema,   dump_only=True)
    away_team       = fields.Nested(TeamNestedSchema,   dump_only=True)
    match_datetime  = fields.DateTime(dump_only=True)
    venue           = fields.Str(dump_only=True, allow_none=True)
    status          = fields.Str(dump_only=True,
                                 validate=validate.OneOf(
                                     ["scheduled","live","finished","postponed","cancelled"]))
    home_score      = fields.Int(dump_only=True)
    away_score      = fields.Int(dump_only=True)
    elapsed_time    = fields.Int(dump_only=True, allow_none=True)
    external_api_id = fields.Str(dump_only=True, allow_none=True)
    updated_at      = fields.DateTime(dump_only=True)


class MatchDetailSchema(MatchSchema):
    """Match detail — adds player stats and highlights."""
    player_stats = fields.List(
        fields.Nested(lambda: PlayerMatchStatSchema()),
        dump_only=True,
    )
    highlights = fields.List(
        fields.Nested(lambda: HighlightSchema()),
        dump_only=True,
    )


class MatchListFilterSchema(Schema):
    """Query-string filters for GET /matches."""
    sport      = fields.Str(load_default=None)
    league_id  = fields.Int(load_default=None)
    status     = fields.Str(load_default=None,
                             validate=validate.OneOf(
                                 ["scheduled","live","finished","postponed","cancelled"]))
    date_from  = fields.Date(load_default=None)
    date_to    = fields.Date(load_default=None)
    page       = fields.Int(load_default=1,  validate=validate.Range(min=1))
    limit      = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))

    @validates_schema
    def validate_date_range(self, data, **kwargs):
        if data.get("date_from") and data.get("date_to"):
            if data["date_from"] > data["date_to"]:
                raise ValidationError(
                    "date_from must be before or equal to date_to.",
                    field_name="date_from",
                )


# ─────────────────────────────────────────────────────────────────────────────
# PLAYER MATCH STAT
# ─────────────────────────────────────────────────────────────────────────────

class PlayerMatchStatSchema(Schema):
    """Stat row — embedded inside match detail or player stats list."""
    stat_id        = fields.Int(dump_only=True)
    player         = fields.Nested(PlayerNestedSchema, dump_only=True)
    match_id       = fields.Int(dump_only=True)
    minutes_played = fields.Int(dump_only=True)
    goals          = fields.Int(dump_only=True)
    assists        = fields.Int(dump_only=True)
    yellow_cards   = fields.Int(dump_only=True)
    red_cards      = fields.Int(dump_only=True)
    runs_scored    = fields.Int(dump_only=True)
    wickets        = fields.Int(dump_only=True)
    extra_stats    = fields.Dict(dump_only=True, allow_none=True)


# ─────────────────────────────────────────────────────────────────────────────
# REVIEW
# ─────────────────────────────────────────────────────────────────────────────

class ReviewSchema(Schema):
    """Full review output including nested author."""
    review_id  = fields.Int(dump_only=True)
    match_id   = fields.Int(dump_only=True)
    user       = fields.Nested(ProfileNestedSchema, dump_only=True)
    rating     = fields.Int(dump_only=True, validate=validate.Range(min=1, max=5))
    body       = fields.Str(dump_only=True, allow_none=True)
    is_hidden  = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class ReviewCreateSchema(Schema):
    """Validated input for POST /matches/:id/reviews."""
    rating = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=5, error="Rating must be between 1 and 5."),
    )
    body = fields.Str(
        load_default=None,
        validate=validate.Length(max=2000),
    )


class ReviewWithStatsSchema(Schema):
    """GET /matches/:id/reviews response — includes avg rating + list."""
    average_rating = fields.Float(dump_only=True, allow_none=True)
    total_reviews  = fields.Int(dump_only=True)
    reviews        = fields.List(fields.Nested(ReviewSchema), dump_only=True)


# ─────────────────────────────────────────────────────────────────────────────
# COMMENT
# ─────────────────────────────────────────────────────────────────────────────

class CommentSchema(Schema):
    """Full comment output — replies are loaded separately to avoid deep nesting."""
    comment_id  = fields.Int(dump_only=True)
    user        = fields.Nested(ProfileNestedSchema, dump_only=True)
    entity_type = fields.Str(dump_only=True)
    entity_id   = fields.Int(dump_only=True)
    parent_id   = fields.Int(dump_only=True, allow_none=True)
    body        = fields.Str(dump_only=True)
    is_hidden   = fields.Bool(dump_only=True)
    created_at  = fields.DateTime(dump_only=True)
    edited_at   = fields.DateTime(dump_only=True, allow_none=True)


class CommentCreateSchema(Schema):
    """Validated input for POST /comments."""
    entity_type = fields.Str(
        required=True,
        validate=validate.OneOf(["match", "player"],
                                error="entity_type must be 'match' or 'player'."),
    )
    entity_id = fields.Int(required=True, validate=validate.Range(min=1))
    body      = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=2000,
                                 error="Comment must be between 1 and 2000 characters."),
    )
    parent_id = fields.Int(load_default=None, allow_none=True)


class CommentUpdateSchema(Schema):
    """Validated input for PUT /comments/:id  (15-minute edit window enforced in Flask)."""
    body = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=2000),
    )


# ─────────────────────────────────────────────────────────────────────────────
# PLAYER RATING
# ─────────────────────────────────────────────────────────────────────────────

class PlayerRatingSchema(Schema):
    """Output for a single player rating."""
    rating_id  = fields.Int(dump_only=True)
    player_id  = fields.Int(dump_only=True)
    match_id   = fields.Int(dump_only=True)
    user       = fields.Nested(ProfileNestedSchema, dump_only=True)
    rating     = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class PlayerRatingCreateSchema(Schema):
    """Validated input for POST /players/:id/rate."""
    match_id = fields.Int(required=True, validate=validate.Range(min=1))
    rating   = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=5, error="Rating must be between 1 and 5."),
    )


class PlayerRatingAvgSchema(Schema):
    """Average rating summary for GET /players/:id/ratings."""
    player_id      = fields.Int(dump_only=True)
    average_rating = fields.Float(dump_only=True, allow_none=True)
    total_ratings  = fields.Int(dump_only=True)


# ─────────────────────────────────────────────────────────────────────────────
# HIGHLIGHT
# ─────────────────────────────────────────────────────────────────────────────

class HighlightSchema(Schema):
    """Output for a video highlight."""
    highlight_id = fields.Int(dump_only=True)
    match_id     = fields.Int(dump_only=True)
    title        = fields.Str(dump_only=True)
    video_url    = fields.Url(dump_only=True)
    added_by     = fields.UUID(dump_only=True, allow_none=True)
    created_at   = fields.DateTime(dump_only=True)


class HighlightCreateSchema(Schema):
    """Validated input for POST /admin/highlights  (Admin only)."""
    match_id  = fields.Int(required=True, validate=validate.Range(min=1))
    title     = fields.Str(required=True, validate=validate.Length(min=1, max=300))
    video_url = fields.Url(required=True)


# ─────────────────────────────────────────────────────────────────────────────
# FAN EVENT
# ─────────────────────────────────────────────────────────────────────────────

class FanEventSchema(Schema):
    """Full fan event output including current registration count."""
    event_id      = fields.Int(dump_only=True)
    title         = fields.Str(dump_only=True)
    description   = fields.Str(dump_only=True, allow_none=True)
    event_date    = fields.DateTime(dump_only=True)
    location      = fields.Str(dump_only=True, allow_none=True)
    capacity      = fields.Int(dump_only=True)
    registered    = fields.Int(dump_only=True)   # computed field — set in Flask route
    spots_left    = fields.Int(dump_only=True)   # computed field — capacity - registered
    created_by    = fields.UUID(dump_only=True, allow_none=True)
    created_at    = fields.DateTime(dump_only=True)


class FanEventCreateSchema(Schema):
    """Validated input for POST /admin/events  (Admin only)."""
    title       = fields.Str(required=True, validate=validate.Length(min=1, max=300))
    description = fields.Str(load_default=None, validate=validate.Length(max=2000))
    event_date  = fields.DateTime(required=True)
    location    = fields.Str(load_default=None, validate=validate.Length(max=300))
    capacity    = fields.Int(
        load_default=100,
        validate=validate.Range(min=1, max=100_000),
    )

    @validates("event_date")
    def validate_future_date(self, value):
        from datetime import timezone
        now = __import__("datetime").datetime.now(tz=timezone.utc)
        if value <= now:
            raise ValidationError("event_date must be in the future.")


class FanEventUpdateSchema(Schema):
    """Validated input for PUT /admin/events/:id."""
    title       = fields.Str(validate=validate.Length(min=1, max=300))
    description = fields.Str(allow_none=True)
    event_date  = fields.DateTime()
    location    = fields.Str(allow_none=True)
    capacity    = fields.Int(validate=validate.Range(min=1, max=100_000))


# ─────────────────────────────────────────────────────────────────────────────
# EVENT REGISTRATION
# ─────────────────────────────────────────────────────────────────────────────

class EventRegistrationSchema(Schema):
    """Output confirming a fan event registration."""
    registration_id = fields.Int(dump_only=True)
    event_id        = fields.Int(dump_only=True)
    user_id         = fields.UUID(dump_only=True)
    registered_at   = fields.DateTime(dump_only=True)


# ─────────────────────────────────────────────────────────────────────────────
# FOLLOW SYSTEM
# ─────────────────────────────────────────────────────────────────────────────

class FollowTeamSchema(Schema):
    """Output for a user–team follow relationship."""
    user_id     = fields.UUID(dump_only=True)
    team_id     = fields.Int(dump_only=True)
    team        = fields.Nested(TeamNestedSchema, dump_only=True)
    followed_at = fields.DateTime(dump_only=True)


class FollowPlayerSchema(Schema):
    """Output for a user–player follow relationship."""
    user_id     = fields.UUID(dump_only=True)
    player_id   = fields.Int(dump_only=True)
    player      = fields.Nested(PlayerNestedSchema, dump_only=True)
    followed_at = fields.DateTime(dump_only=True)


class FollowingSchema(Schema):
    """Combined output for GET /users/me/following."""
    teams   = fields.List(fields.Nested(FollowTeamSchema),   dump_only=True)
    players = fields.List(fields.Nested(FollowPlayerSchema), dump_only=True)


# ─────────────────────────────────────────────────────────────────────────────
# STANDINGS  (computed — no ORM model, pure SQL function result)
# ─────────────────────────────────────────────────────────────────────────────

class StandingRowSchema(Schema):
    """Single row in a league standings table."""
    pos       = fields.Int(dump_only=True)
    team_id   = fields.Int(dump_only=True)
    team_name = fields.Str(dump_only=True)
    logo_url  = fields.Str(dump_only=True, allow_none=True)
    played    = fields.Int(dump_only=True)
    won       = fields.Int(dump_only=True)
    drawn     = fields.Int(dump_only=True)
    lost      = fields.Int(dump_only=True)
    gf        = fields.Int(dump_only=True)
    ga        = fields.Int(dump_only=True)
    gd        = fields.Int(dump_only=True)   # computed: gf - ga
    pts       = fields.Int(dump_only=True)


class StandingsSchema(Schema):
    """Full standings response for GET /leagues/:id/standings."""
    league     = fields.Nested(LeagueNestedSchema, dump_only=True)
    standings  = fields.List(fields.Nested(StandingRowSchema), dump_only=True)
    updated_at = fields.DateTime(dump_only=True, allow_none=True)


# ─────────────────────────────────────────────────────────────────────────────
# SYNC LOG  (scheduler audit trail)
# ─────────────────────────────────────────────────────────────────────────────

class SyncLogSchema(Schema):
    """Full sync log output for GET /admin/sync-logs."""
    log_id           = fields.Int(dump_only=True)
    sync_type        = fields.Str(dump_only=True)
    started_at       = fields.DateTime(dump_only=True)
    finished_at      = fields.DateTime(dump_only=True, allow_none=True)
    records_fetched  = fields.Int(dump_only=True)
    records_upserted = fields.Int(dump_only=True)
    status           = fields.Str(dump_only=True,
                                  validate=validate.OneOf(["running","success","failed"]))
    error_message    = fields.Str(dump_only=True, allow_none=True)


# ─────────────────────────────────────────────────────────────────────────────
# FEED  (personalised — no ORM model, composed from multiple tables)
# ─────────────────────────────────────────────────────────────────────────────

class FeedMatchSchema(Schema):
    """Match shown in personalised feed — same as MatchSchema but includes reason."""
    match_id       = fields.Int(dump_only=True)
    league         = fields.Nested(LeagueNestedSchema, dump_only=True)
    home_team      = fields.Nested(TeamNestedSchema,   dump_only=True)
    away_team      = fields.Nested(TeamNestedSchema,   dump_only=True)
    match_datetime = fields.DateTime(dump_only=True)
    status         = fields.Str(dump_only=True)
    home_score     = fields.Int(dump_only=True)
    away_score     = fields.Int(dump_only=True)
    elapsed_time   = fields.Int(dump_only=True, allow_none=True)
    reason         = fields.Str(dump_only=True)  # e.g. "Following Arsenal"


class FeedSchema(Schema):
    """Full feed response for GET /users/me/feed."""
    matches = fields.List(fields.Nested(FeedMatchSchema), dump_only=True)
    total   = fields.Int(dump_only=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGINATION WRAPPER  (generic — use in any list endpoint)
# ─────────────────────────────────────────────────────────────────────────────

class PaginationSchema(Schema):
    """Standard pagination envelope for any list response."""
    page       = fields.Int(dump_only=True)
    limit      = fields.Int(dump_only=True)
    total      = fields.Int(dump_only=True)
    total_pages= fields.Int(dump_only=True)
    has_next   = fields.Bool(dump_only=True)
    has_prev   = fields.Bool(dump_only=True)


# ─────────────────────────────────────────────────────────────────────────────
# CONVENIENCE: pre-instantiated singletons
# (import these directly instead of instantiating in each view)
# ─────────────────────────────────────────────────────────────────────────────

# Sports & Leagues
sport_schema          = SportSchema()
sports_schema         = SportSchema(many=True)
league_schema         = LeagueSchema()
leagues_schema        = LeagueSchema(many=True)
league_create_schema  = LeagueCreateSchema()
league_update_schema  = LeagueUpdateSchema()
standings_schema      = StandingsSchema()

# Teams & Players
team_schema           = TeamSchema()
teams_schema          = TeamSchema(many=True)
team_create_schema    = TeamCreateSchema()
team_update_schema    = TeamUpdateSchema()
player_schema         = PlayerSchema()
players_schema        = PlayerSchema(many=True)
injury_update_schema  = InjuryUpdateSchema()
player_rating_schema  = PlayerRatingSchema()
player_ratings_schema = PlayerRatingSchema(many=True)
player_rating_create_schema = PlayerRatingCreateSchema()
player_rating_avg_schema    = PlayerRatingAvgSchema()

# Auth & Profiles
register_schema             = RegisterSchema()
login_schema                = LoginSchema()
password_reset_req_schema   = PasswordResetRequestSchema()
password_reset_conf_schema  = PasswordResetConfirmSchema()
profile_schema              = ProfileSchema()
profiles_schema             = ProfileSchema(many=True)
profile_update_schema       = ProfileUpdateSchema()
admin_role_update_schema    = AdminRoleUpdateSchema()

# Matches
match_schema              = MatchSchema()
matches_schema            = MatchSchema(many=True)
match_detail_schema       = MatchDetailSchema()
match_list_filter_schema  = MatchListFilterSchema()
player_stat_schema        = PlayerMatchStatSchema()
player_stats_schema       = PlayerMatchStatSchema(many=True)

# Community
review_schema             = ReviewSchema()
reviews_schema            = ReviewSchema(many=True)
review_create_schema      = ReviewCreateSchema()
review_with_stats_schema  = ReviewWithStatsSchema()
comment_schema            = CommentSchema()
comments_schema           = CommentSchema(many=True)
comment_create_schema     = CommentCreateSchema()
comment_update_schema     = CommentUpdateSchema()
highlight_schema          = HighlightSchema()
highlights_schema         = HighlightSchema(many=True)
highlight_create_schema   = HighlightCreateSchema()

# Events
fan_event_schema          = FanEventSchema()
fan_events_schema         = FanEventSchema(many=True)
fan_event_create_schema   = FanEventCreateSchema()
fan_event_update_schema   = FanEventUpdateSchema()
event_registration_schema = EventRegistrationSchema()

# Social
follow_team_schema        = FollowTeamSchema()
follow_teams_schema       = FollowTeamSchema(many=True)
follow_player_schema      = FollowPlayerSchema()
follow_players_schema     = FollowPlayerSchema(many=True)
following_schema          = FollowingSchema()
feed_schema               = FeedSchema()

# Ops
sync_log_schema           = SyncLogSchema()
sync_logs_schema          = SyncLogSchema(many=True)
pagination_schema         = PaginationSchema()