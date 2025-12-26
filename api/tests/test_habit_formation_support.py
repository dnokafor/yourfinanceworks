"""
Property-based tests for habit formation support system.

Feature: gamified-finance-habits
Property 25: Progressive Habit Difficulty
Property 26: Habit Strength Tracking
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import asyncio

from core.models.models_per_tenant import Base
from core.models.gamification import (
    UserGamificationProfile,
    UserStreak,
    HabitType,
    DataRetentionPolicy
)
from core.services.habit_formation_support import (
    HabitFormationSupport,
    HabitDifficulty,
    HabitStrengthLevel
)


def create_db_session():
    """Create a fresh in-memory SQLite database session"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def create_test_profile(db_session, user_id: int) -> UserGamificationProfile:
    """Helper to create a test gamification profile"""
    profile = UserGamificationProfile(
        user_id=user_id,
        module_enabled=True,
        level=1,
        total_experience_points=0,
        current_level_progress=0.0,
        financial_health_score=0.0,
        preferences={},
        statistics={},
        data_retention_policy=DataRetentionPolicy.PRESERVE
    )
    db_session.add(profile)
    db_session.commit()
    return profile


def create_test_streak(
    db_session,
    profile_id: int,
    habit_type: HabitType,
    current_length: int = 0,
    longest_length: int = 0,
    times_broken: int = 0,
    is_active: bool = True,
    last_activity_date: datetime = None
) -> UserStreak:
    """Helper to create a test streak"""
    if last_activity_date is None:
        last_activity_date = datetime.now(timezone.utc)
    
    streak = UserStreak(
        profile_id=profile_id,
        habit_type=habit_type,
        current_length=current_length,
        longest_length=longest_length,
        is_active=is_active,
        times_broken=times_broken,
        last_activity_date=last_activity_date,
        streak_start_date=last_activity_date if current_length > 0 else None
    )
    db_session.add(streak)
    db_session.commit()
    return streak


class TestProgressiveHabitDifficulty:
    """Tests for progressive difficulty adaptation - Property 25"""

    @given(
        user_id=st.integers(min_value=1, max_value=10000),
        longest_streak=st.integers(min_value=0, max_value=400)
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_difficulty_increases_with_streak_length(
        self,
        user_id,
        longest_streak
    ):
        """Property 25: Difficulty should match streak length"""
        db_session = create_db_session()
        try:
            habit_formation_service = HabitFormationSupport(db_session)
            profile = create_test_profile(db_session, user_id)
            create_test_streak(
                db_session,
                profile.id,
                HabitType.DAILY_EXPENSE_TRACKING,
                current_length=0,
                longest_length=longest_streak,
                is_active=False
            )

            difficulty = asyncio.run(
                habit_formation_service.get_habit_difficulty(
                    user_id,
                    HabitType.DAILY_EXPENSE_TRACKING
                )
            )

            if longest_streak >= 365:
                assert difficulty == HabitDifficulty.EXPERT
            elif longest_streak >= 90:
                assert difficulty == HabitDifficulty.ADVANCED
            elif longest_streak >= 30:
                assert difficulty == HabitDifficulty.INTERMEDIATE
            elif longest_streak >= 7:
                assert difficulty == HabitDifficulty.NOVICE
            else:
                assert difficulty == HabitDifficulty.BEGINNER
        finally:
            db_session.close()

    @given(
        habit_type=st.sampled_from([
            HabitType.DAILY_EXPENSE_TRACKING,
            HabitType.WEEKLY_BUDGET_REVIEW,
            HabitType.INVOICE_FOLLOW_UP,
            HabitType.RECEIPT_DOCUMENTATION
        ]),
        difficulty=st.sampled_from([
            HabitDifficulty.BEGINNER,
            HabitDifficulty.NOVICE,
            HabitDifficulty.INTERMEDIATE,
            HabitDifficulty.ADVANCED,
            HabitDifficulty.EXPERT
        ])
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_educational_content_provided(
        self,
        habit_type,
        difficulty
    ):
        """Property 25: Educational content should be available for all difficulties"""
        db_session = create_db_session()
        try:
            habit_formation_service = HabitFormationSupport(db_session)
            content = asyncio.run(
                habit_formation_service.get_educational_content(habit_type, difficulty)
            )

            assert "tips" in content
            assert "target_frequency" in content
            assert "success_criteria" in content
            assert isinstance(content["tips"], list)
            assert len(content["tips"]) > 0
        finally:
            db_session.close()


class TestHabitStrengthTracking:
    """Tests for habit strength calculation - Property 26"""

    @given(
        user_id=st.integers(min_value=1, max_value=10000),
        current_streak=st.integers(min_value=0, max_value=100),
        longest_streak=st.integers(min_value=0, max_value=100),
        times_broken=st.integers(min_value=0, max_value=10)
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_habit_strength_score_is_valid_range(
        self,
        user_id,
        current_streak,
        longest_streak,
        times_broken
    ):
        """Property 26: Habit strength score should be between 0 and 100"""
        if longest_streak < current_streak:
            longest_streak = current_streak

        db_session = create_db_session()
        try:
            habit_formation_service = HabitFormationSupport(db_session)
            profile = create_test_profile(db_session, user_id)
            create_test_streak(
                db_session,
                profile.id,
                HabitType.DAILY_EXPENSE_TRACKING,
                current_length=current_streak,
                longest_length=longest_streak,
                times_broken=times_broken,
                is_active=current_streak > 0
            )

            strength_score = asyncio.run(
                habit_formation_service.calculate_habit_strength(
                    user_id,
                    HabitType.DAILY_EXPENSE_TRACKING
                )
            )

            assert 0.0 <= strength_score.overall_score <= 100.0
        finally:
            db_session.close()

    @given(
        user_id=st.integers(min_value=1, max_value=10000),
        current_streak=st.integers(min_value=0, max_value=100),
        longest_streak=st.integers(min_value=0, max_value=100),
        times_broken=st.integers(min_value=0, max_value=10)
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_habit_strength_level_matches_score(
        self,
        user_id,
        current_streak,
        longest_streak,
        times_broken
    ):
        """Property 26: Strength level should match score"""
        if longest_streak < current_streak:
            longest_streak = current_streak

        db_session = create_db_session()
        try:
            habit_formation_service = HabitFormationSupport(db_session)
            profile = create_test_profile(db_session, user_id)
            create_test_streak(
                db_session,
                profile.id,
                HabitType.DAILY_EXPENSE_TRACKING,
                current_length=current_streak,
                longest_length=longest_streak,
                times_broken=times_broken,
                is_active=current_streak > 0
            )

            strength_score = asyncio.run(
                habit_formation_service.calculate_habit_strength(
                    user_id,
                    HabitType.DAILY_EXPENSE_TRACKING
                )
            )

            score = strength_score.overall_score
            level = strength_score.strength_level

            if score < 20:
                assert level == HabitStrengthLevel.FRAGILE
            elif score < 40:
                assert level == HabitStrengthLevel.WEAK
            elif score < 60:
                assert level == HabitStrengthLevel.MODERATE
            elif score < 80:
                assert level == HabitStrengthLevel.STRONG
            else:
                assert level == HabitStrengthLevel.UNBREAKABLE
        finally:
            db_session.close()

    @given(
        user_id=st.integers(min_value=1, max_value=10000),
        current_streak=st.integers(min_value=1, max_value=100),
        longest_streak=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_consistency_percentage_is_valid(
        self,
        user_id,
        current_streak,
        longest_streak
    ):
        """Property 26: Consistency percentage should be between 0 and 100"""
        if longest_streak < current_streak:
            longest_streak = current_streak

        db_session = create_db_session()
        try:
            habit_formation_service = HabitFormationSupport(db_session)
            profile = create_test_profile(db_session, user_id)
            create_test_streak(
                db_session,
                profile.id,
                HabitType.DAILY_EXPENSE_TRACKING,
                current_length=current_streak,
                longest_length=longest_streak,
                is_active=True
            )

            strength_score = asyncio.run(
                habit_formation_service.calculate_habit_strength(
                    user_id,
                    HabitType.DAILY_EXPENSE_TRACKING
                )
            )

            assert 0.0 <= strength_score.consistency_percentage <= 100.0
        finally:
            db_session.close()
