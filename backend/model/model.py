import json
from datetime import datetime, date
from typing import Any, Dict, Optional, List
from uuid import uuid4

from sqlalchemy import (
	Column, BigInteger, Integer, SmallInteger, String, Text, Boolean, Date,
	DateTime, ForeignKey, UniqueConstraint, CheckConstraint, JSON,
	create_engine, func, event
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class Sport(Base):
	"""Sports like Football, Cricket, Wrestling."""
	__tablename__ = 'sport'

	sport_id = Column(BigInteger, primary_key=True, autoincrement=True)
	name = Column(String, nullable=False, unique=True)
	description = Column(Text)
	created_at = Column(DateTime(timezone=True), server_default=func.now())

	leagues = relationship("League", back_populates="sport", cascade="all, delete-orphan")
	teams = relationship("Team", back_populates="sport", cascade="all, delete-orphan")
	players = relationship("Player", back_populates="sport", cascade="all, delete-orphan")


class League(Base):
	"""Leagues within a sport (e.g., Premier League, IPL)."""
	__tablename__ = 'league'
	__table_args__ = (UniqueConstraint('name', 'season', name='uq_league_name_season'),)

	league_id = Column(BigInteger, primary_key=True, autoincrement=True)
	sport_id = Column(BigInteger, ForeignKey('sport.sport_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
	name = Column(String, nullable=False)
	country = Column(String)
	season = Column(String, nullable=False)
	external_api_id = Column(String)
	created_at = Column(DateTime(timezone=True), server_default=func.now())

	sport = relationship("Sport", back_populates="leagues")
	teams = relationship("Team", secondary="team_league", back_populates="leagues")
	matches = relationship("GameMatch", back_populates="league", cascade="all, delete-orphan")


class Team(Base):
	"""Teams competing in leagues and sports."""
	__tablename__ = 'team'

	team_id = Column(BigInteger, primary_key=True, autoincrement=True)
	sport_id = Column(BigInteger, ForeignKey('sport.sport_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
	name = Column(String, nullable=False)
	country = Column(String)
	founded_year = Column(Integer)
	home_ground = Column(String)
	logo_url = Column(String)
	external_api_id = Column(String)
	created_at = Column(DateTime(timezone=True), server_default=func.now())

	sport = relationship("Sport", back_populates="teams")
	leagues = relationship("League", secondary="team_league", back_populates="teams")
	players = relationship("Player", back_populates="team", cascade="all, delete-orphan")
	home_matches = relationship("GameMatch", foreign_keys="GameMatch.home_team_id", back_populates="home_team")
	away_matches = relationship("GameMatch", foreign_keys="GameMatch.away_team_id", back_populates="away_team")
	followers = relationship("UserFollowTeam", back_populates="team", cascade="all, delete-orphan")


class TeamLeague(Base):
	"""Junction table: Teams participating in Leagues."""
	__tablename__ = 'team_league'

	team_id = Column(BigInteger, ForeignKey('team.team_id', ondelete='CASCADE'), primary_key=True)
	league_id = Column(BigInteger, ForeignKey('league.league_id', ondelete='CASCADE'), primary_key=True)


class Profile(Base):
	"""User profiles with UUID primary key and manual authentication."""
	__tablename__ = 'profiles'
	__table_args__ = (
		CheckConstraint("role IN ('admin','team_manager','fan')", name='ck_profile_role'),
	)

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
	email = Column(String, nullable=False, unique=True)
	password_hash = Column(String, nullable=True)  # Bcrypt hashed password
	display_name = Column(String)
	role = Column(String, nullable=False, default='fan')
	team_managed = Column(BigInteger, ForeignKey('team.team_id', ondelete='SET NULL'))
	is_active = Column(Boolean, nullable=False, default=True)
	created_at = Column(DateTime(timezone=True), server_default=func.now())
	updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

	reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
	comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
	player_ratings = relationship("PlayerRating", back_populates="user", cascade="all, delete-orphan")
	highlights = relationship("Highlight", back_populates="user", foreign_keys="Highlight.added_by")
	events_created = relationship("FanEvent", back_populates="creator")
	event_registrations = relationship("EventRegistration", back_populates="user", cascade="all, delete-orphan")
	followed_teams = relationship("UserFollowTeam", back_populates="user", cascade="all, delete-orphan")
	followed_players = relationship("UserFollowPlayer", back_populates="user", cascade="all, delete-orphan")


class Player(Base):
	"""Players in teams."""
	__tablename__ = 'player'
	__table_args__ = (
		CheckConstraint("injury_status IN ('fit','injured','doubtful')", name='ck_player_injury_status'),
	)

	player_id = Column(BigInteger, primary_key=True, autoincrement=True)
	team_id = Column(BigInteger, ForeignKey('team.team_id', ondelete='SET NULL'))
	sport_id = Column(BigInteger, ForeignKey('sport.sport_id', ondelete='RESTRICT'), nullable=False)
	name = Column(String, nullable=False)
	nationality = Column(String)
	date_of_birth = Column(Date)
	position_role = Column(String)
	jersey_number = Column(SmallInteger)
	profile_image_url = Column(String)
	injury_status = Column(String, nullable=False, default='fit')
	injury_updated_at = Column(DateTime(timezone=True))
	external_api_id = Column(String)
	created_at = Column(DateTime(timezone=True), server_default=func.now())

	team = relationship("Team", back_populates="players")
	sport = relationship("Sport", back_populates="players")
	match_stats = relationship("PlayerMatchStat", back_populates="player", cascade="all, delete-orphan")
	ratings = relationship("PlayerRating", back_populates="player", cascade="all, delete-orphan")
	followers = relationship("UserFollowPlayer", back_populates="player", cascade="all, delete-orphan")


class GameMatch(Base):
	"""Matches/games between teams."""
	__tablename__ = 'game_match'
	__table_args__ = (
		CheckConstraint("status IN ('scheduled','live','finished','postponed','cancelled')", name='ck_match_status'),
		CheckConstraint("home_team_id <> away_team_id", name='ck_match_different_teams'),
	)

	match_id = Column(BigInteger, primary_key=True, autoincrement=True)
	league_id = Column(BigInteger, ForeignKey('league.league_id'), nullable=False)
	home_team_id = Column(BigInteger, ForeignKey('team.team_id'), nullable=False)
	away_team_id = Column(BigInteger, ForeignKey('team.team_id'), nullable=False)
	match_datetime = Column(DateTime(timezone=True), nullable=False)
	venue = Column(String)
	status = Column(String, nullable=False, default='scheduled')
	home_score = Column(SmallInteger, default=0)
	away_score = Column(SmallInteger, default=0)
	elapsed_time = Column(SmallInteger)
	extra_data = Column(JSON)
	external_api_id = Column(String)
	created_at = Column(DateTime(timezone=True), server_default=func.now())
	updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

	league = relationship("League", back_populates="matches")
	home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
	away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
	player_stats = relationship("PlayerMatchStat", back_populates="match", cascade="all, delete-orphan")
	reviews = relationship("Review", back_populates="match", cascade="all, delete-orphan")
	player_ratings = relationship("PlayerRating", back_populates="match", cascade="all, delete-orphan")
	highlights = relationship("Highlight", back_populates="match", cascade="all, delete-orphan")


class PlayerMatchStat(Base):
	"""Statistics for a player in a specific match."""
	__tablename__ = 'player_match_stat'
	__table_args__ = (UniqueConstraint('player_id', 'match_id', name='uq_player_match'),)

	stat_id = Column(BigInteger, primary_key=True, autoincrement=True)
	player_id = Column(BigInteger, ForeignKey('player.player_id', ondelete='CASCADE'), nullable=False)
	match_id = Column(BigInteger, ForeignKey('game_match.match_id', ondelete='CASCADE'), nullable=False)
	minutes_played = Column(SmallInteger, default=0)
	goals = Column(SmallInteger, default=0)
	assists = Column(SmallInteger, default=0)
	yellow_cards = Column(SmallInteger, default=0)
	red_cards = Column(SmallInteger, default=0)
	runs_scored = Column(SmallInteger, default=0)
	wickets = Column(SmallInteger, default=0)
	extra_stats = Column(JSON)

	player = relationship("Player", back_populates="match_stats")
	match = relationship("GameMatch", back_populates="player_stats")


class Review(Base):
	"""Match reviews by users."""
	__tablename__ = 'review'
	__table_args__ = (
		UniqueConstraint('user_id', 'match_id', name='uq_review_user_match'),
		CheckConstraint("rating BETWEEN 1 AND 5", name='ck_review_rating'),
	)

	review_id = Column(BigInteger, primary_key=True, autoincrement=True)
	match_id = Column(BigInteger, ForeignKey('game_match.match_id', ondelete='CASCADE'), nullable=False)
	user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
	rating = Column(SmallInteger, nullable=False)
	body = Column(Text)
	is_hidden = Column(Boolean, default=False)
	created_at = Column(DateTime(timezone=True), server_default=func.now())

	match = relationship("GameMatch", back_populates="reviews")
	user = relationship("Profile", back_populates="reviews")


class Comment(Base):
	"""Comments on matches or players."""
	__tablename__ = 'comment'
	__table_args__ = (
		CheckConstraint("entity_type IN ('match','player')", name='ck_comment_entity_type'),
	)

	comment_id = Column(BigInteger, primary_key=True, autoincrement=True)
	user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
	entity_type = Column(String, nullable=False)
	entity_id = Column(BigInteger, nullable=False)
	parent_id = Column(BigInteger, ForeignKey('comment.comment_id', ondelete='CASCADE'))
	body = Column(Text, nullable=False)
	is_hidden = Column(Boolean, default=False)
	created_at = Column(DateTime(timezone=True), server_default=func.now())
	edited_at = Column(DateTime(timezone=True))

	user = relationship("Profile", back_populates="comments")
	replies = relationship("Comment", remote_side=[comment_id], cascade="all, delete-orphan", single_parent=True)


class PlayerRating(Base):
	"""Ratings for a player in a specific match by users."""
	__tablename__ = 'player_rating'
	__table_args__ = (
		UniqueConstraint('player_id', 'match_id', 'user_id', name='uq_player_rating_user_match'),
		CheckConstraint("rating BETWEEN 1 AND 5", name='ck_player_rating_value'),
	)

	rating_id = Column(BigInteger, primary_key=True, autoincrement=True)
	player_id = Column(BigInteger, ForeignKey('player.player_id', ondelete='CASCADE'), nullable=False)
	match_id = Column(BigInteger, ForeignKey('game_match.match_id', ondelete='CASCADE'), nullable=False)
	user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
	rating = Column(SmallInteger, nullable=False)
	created_at = Column(DateTime(timezone=True), server_default=func.now())

	player = relationship("Player", back_populates="ratings")
	match = relationship("GameMatch", back_populates="player_ratings")
	user = relationship("Profile", back_populates="player_ratings")


class Highlight(Base):
	"""Video highlights for matches."""
	__tablename__ = 'highlight'

	highlight_id = Column(BigInteger, primary_key=True, autoincrement=True)
	match_id = Column(BigInteger, ForeignKey('game_match.match_id', ondelete='CASCADE'), nullable=False)
	title = Column(String, nullable=False)
	video_url = Column(String, nullable=False)
	added_by = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='SET NULL'))
	created_at = Column(DateTime(timezone=True), server_default=func.now())

	match = relationship("GameMatch", back_populates="highlights")
	user = relationship("Profile", back_populates="highlights", foreign_keys=[added_by])


class FanEvent(Base):
	"""Community events for fans."""
	__tablename__ = 'fan_event'

	event_id = Column(BigInteger, primary_key=True, autoincrement=True)
	title = Column(String, nullable=False)
	description = Column(Text)
	event_date = Column(DateTime(timezone=True), nullable=False)
	location = Column(String)
	capacity = Column(SmallInteger, nullable=False, default=100)
	created_by = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='SET NULL'))
	created_at = Column(DateTime(timezone=True), server_default=func.now())

	registrations = relationship("EventRegistration", back_populates="event", cascade="all, delete-orphan")
	creator = relationship("Profile", back_populates="events_created", foreign_keys=[created_by])


class EventRegistration(Base):
	"""User registrations for fan events."""
	__tablename__ = 'event_registration'
	__table_args__ = (UniqueConstraint('event_id', 'user_id', name='uq_event_registration_user'),)

	registration_id = Column(BigInteger, primary_key=True, autoincrement=True)
	event_id = Column(BigInteger, ForeignKey('fan_event.event_id', ondelete='CASCADE'), nullable=False)
	user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
	registered_at = Column(DateTime(timezone=True), server_default=func.now())

	event = relationship("FanEvent", back_populates="registrations")
	user = relationship("Profile", back_populates="event_registrations")


class UserFollowTeam(Base):
	"""Users following teams."""
	__tablename__ = 'user_follow_team'

	user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), primary_key=True)
	team_id = Column(BigInteger, ForeignKey('team.team_id', ondelete='CASCADE'), primary_key=True)
	followed_at = Column(DateTime(timezone=True), server_default=func.now())

	user = relationship("Profile", back_populates="followed_teams")
	team = relationship("Team", back_populates="followers")


class UserFollowPlayer(Base):
	"""Users following players."""
	__tablename__ = 'user_follow_player'

	user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), primary_key=True)
	player_id = Column(BigInteger, ForeignKey('player.player_id', ondelete='CASCADE'), primary_key=True)
	followed_at = Column(DateTime(timezone=True), server_default=func.now())

	user = relationship("Profile", back_populates="followed_players")
	player = relationship("Player", back_populates="followers")


class SyncLog(Base):
	"""Logs for external API sync operations."""
	__tablename__ = 'sync_log'
	__table_args__ = (
		CheckConstraint("status IN ('running','success','failed')", name='ck_sync_status'),
	)

	log_id = Column(BigInteger, primary_key=True, autoincrement=True)
	sync_type = Column(String, nullable=False)
	started_at = Column(DateTime(timezone=True), nullable=False)
	finished_at = Column(DateTime(timezone=True))
	records_fetched = Column(Integer, default=0)
	records_upserted = Column(Integer, default=0)
	status = Column(String, default='running')
	error_message = Column(Text)
