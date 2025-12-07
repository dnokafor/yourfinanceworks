"""
Property-based tests for AttributionService.

Feature: user-attribution-tracking, Property 7: Graceful handling of missing attribution
Validates: Requirements 7.1, 7.2, 7.3, 7.4

These tests verify that the attribution service handles missing or incomplete
user data gracefully without errors, which is essential for backward compatibility
with legacy records.
"""
import pytest
from hypothesis import given, strategies as st, settings
from core.services.attribution_service import AttributionService
from core.models.models import User


# Custom strategies for generating test data
@st.composite
def user_with_full_name(draw):
    """Generate a User object with first and last name"""
    user = User()
    user.id = draw(st.integers(min_value=1, max_value=100000))
    user.first_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))))
    user.last_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))))
    user.email = draw(st.emails())
    return user


@st.composite
def user_with_first_name_only(draw):
    """Generate a User object with only first name"""
    user = User()
    user.id = draw(st.integers(min_value=1, max_value=100000))
    user.first_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))))
    user.last_name = None
    user.email = draw(st.emails())
    return user


@st.composite
def user_with_last_name_only(draw):
    """Generate a User object with only last name"""
    user = User()
    user.id = draw(st.integers(min_value=1, max_value=100000))
    user.first_name = None
    user.last_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))))
    user.email = draw(st.emails())
    return user


@st.composite
def user_with_email_only(draw):
    """Generate a User object with only email"""
    user = User()
    user.id = draw(st.integers(min_value=1, max_value=100000))
    user.first_name = None
    user.last_name = None
    user.email = draw(st.emails())
    return user


@st.composite
def user_with_empty_strings(draw):
    """Generate a User object with empty string names"""
    user = User()
    user.id = draw(st.integers(min_value=1, max_value=100000))
    user.first_name = ""
    user.last_name = ""
    user.email = draw(st.emails())
    return user


@st.composite
def user_with_whitespace_names(draw):
    """Generate a User object with whitespace-only names"""
    user = User()
    user.id = draw(st.integers(min_value=1, max_value=100000))
    user.first_name = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Zs',))))
    user.last_name = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Zs',))))
    user.email = draw(st.emails())
    return user


class TestAttributionServiceProperties:
    """Property-based tests for AttributionService"""
    
    @settings(max_examples=100)
    @given(user=user_with_full_name())
    def test_property_7a_get_display_name_never_returns_none(self, user):
        """
        Feature: user-attribution-tracking, Property 7: Graceful handling of missing attribution
        
        For any user object (including None), get_display_name should always return
        a string, never None or raise an exception.
        """
        result = AttributionService.get_display_name(user)
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_property_7b_get_display_name_handles_none_gracefully(self):
        """
        Feature: user-attribution-tracking, Property 7: Graceful handling of missing attribution
        
        When user is None, get_display_name should return "Unknown" without errors.
        This is critical for legacy records.
        """
        result = AttributionService.get_display_name(None)
        assert result == "Unknown"
        assert isinstance(result, str)
    
    @settings(max_examples=100)
    @given(user=st.one_of(
        user_with_full_name(),
        user_with_first_name_only(),
        user_with_last_name_only(),
        user_with_email_only(),
        user_with_empty_strings(),
        user_with_whitespace_names()
    ))
    def test_property_7c_get_display_name_always_returns_valid_string(self, user):
        """
        Feature: user-attribution-tracking, Property 7: Graceful handling of missing attribution
        
        For any user object with any combination of name fields, get_display_name
        should return a non-empty string without raising exceptions.
        """
        result = AttributionService.get_display_name(user)
        assert isinstance(result, str)
        assert len(result) > 0
        # Should never return just whitespace
        assert result.strip() != ""
    
    @settings(max_examples=100)
    @given(user=user_with_full_name())
    def test_property_7d_format_user_info_returns_dict_with_required_keys(self, user):
        """
        Feature: user-attribution-tracking, Property 7: Graceful handling of missing attribution
        
        For any valid user, format_user_info should return a dictionary with
        user_id, username, and email keys.
        """
        result = AttributionService.format_user_info(user)
        assert isinstance(result, dict)
        assert "user_id" in result
        assert "username" in result
        assert "email" in result
    
    @settings(max_examples=100)
    @given(user=user_with_full_name())
    def test_property_7e_format_user_info_preserves_user_id(self, user):
        """
        Feature: user-attribution-tracking, Property 7: Graceful handling of missing attribution
        
        For any user, format_user_info should preserve the user's ID exactly.
        """
        result = AttributionService.format_user_info(user)
        assert result["user_id"] == user.id
    
    @settings(max_examples=100)
    @given(user=st.one_of(
        user_with_full_name(),
        user_with_first_name_only(),
        user_with_last_name_only(),
        user_with_email_only()
    ))
    def test_property_7f_format_user_info_username_never_empty_when_data_exists(self, user):
        """
        Feature: user-attribution-tracking, Property 7: Graceful handling of missing attribution
        
        For any user with at least one name field or email, format_user_info
        should return a non-None username.
        """
        result = AttributionService.format_user_info(user)
        # If user has any identifying information, username should not be None
        if user.first_name or user.last_name or user.email:
            assert result["username"] is not None
            assert len(result["username"]) > 0
    
    @settings(max_examples=100)
    @given(user=user_with_full_name())
    def test_property_7g_get_user_from_context_returns_valid_id(self, user):
        """
        Feature: user-attribution-tracking, Property 7: Graceful handling of missing attribution
        
        For any valid user, get_user_from_context should return a positive integer ID.
        """
        result = AttributionService.get_user_from_context(user)
        assert isinstance(result, int)
        assert result > 0
        assert result == user.id
    
    def test_property_7h_get_user_from_context_rejects_none(self):
        """
        Feature: user-attribution-tracking, Property 7: Graceful handling of missing attribution
        
        When user is None, get_user_from_context should raise ValueError
        (authentication is required for creating records).
        """
        with pytest.raises(ValueError, match="User context is required"):
            AttributionService.get_user_from_context(None)
    
    @settings(max_examples=100)
    @given(user=user_with_full_name())
    def test_property_7i_display_name_contains_identifiable_info(self, user):
        """
        Feature: user-attribution-tracking, Property 7: Graceful handling of missing attribution
        
        For any user with name or email, get_display_name should return a string
        that contains some part of their identifying information.
        """
        result = AttributionService.get_display_name(user)
        
        # Result should contain at least part of the user's identity
        has_first_name = user.first_name and user.first_name.strip() and user.first_name.strip() in result
        has_last_name = user.last_name and user.last_name.strip() and user.last_name.strip() in result
        has_email = user.email and user.email in result
        
        # At least one should be true (or it's "Unknown")
        assert has_first_name or has_last_name or has_email or result == "Unknown"
    
    @settings(max_examples=100)
    @given(user=user_with_email_only())
    def test_property_7j_email_fallback_works(self, user):
        """
        Feature: user-attribution-tracking, Property 7: Graceful handling of missing attribution
        
        For any user with only email (no names), both get_display_name and
        format_user_info should use email as the identifier.
        """
        display_name = AttributionService.get_display_name(user)
        user_info = AttributionService.format_user_info(user)
        
        # When no names are available, email should be used
        assert display_name == user.email
        assert user_info["username"] == user.email
    
    @settings(max_examples=100)
    @given(user=user_with_empty_strings())
    def test_property_7k_empty_strings_treated_as_missing(self, user):
        """
        Feature: user-attribution-tracking, Property 7: Graceful handling of missing attribution
        
        For any user with empty string names, the service should treat them
        as missing and fall back to email.
        """
        display_name = AttributionService.get_display_name(user)
        
        # Empty strings should be treated as missing, so should fall back to email
        assert display_name == user.email or display_name == "Unknown"
    
    @settings(max_examples=100)
    @given(user=user_with_whitespace_names())
    def test_property_7l_whitespace_names_handled_gracefully(self, user):
        """
        Feature: user-attribution-tracking, Property 7: Graceful handling of missing attribution
        
        For any user with whitespace-only names, the service should handle
        gracefully and fall back to email.
        """
        display_name = AttributionService.get_display_name(user)
        user_info = AttributionService.format_user_info(user)
        
        # Should not return just whitespace
        assert display_name.strip() != ""
        # Should fall back to email when names are just whitespace
        assert display_name == user.email or display_name == "Unknown"
