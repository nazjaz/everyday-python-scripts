"""Unit tests for password generator."""

import pytest

from src.main import PasswordGenerator


class TestPasswordGenerator:
    """Test cases for PasswordGenerator class."""

    @pytest.fixture
    def sample_config(self):
        """Create sample configuration."""
        return {
            "defaults": {
                "length": 16,
                "min_length": 4,
                "max_length": 128,
                "character_sets": {
                    "lowercase": True,
                    "uppercase": True,
                    "digits": True,
                    "symbols": True,
                    "exclude_similar": True,
                    "exclude_ambiguous": False,
                },
            },
            "characters": {
                "lowercase": "abcdefghijklmnopqrstuvwxyz",
                "uppercase": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                "digits": "0123456789",
                "symbols": "!@#$%^&*()_+-=[]{}|;:,.<>?",
                "similar_chars": "0OIl1",
                "ambiguous_chars": "{}[]()/\\'\"`~,;:.<>",
            },
            "security": {
                "use_secure_random": True,
                "min_entropy_bits": 40,
            },
        }

    @pytest.fixture
    def generator(self, sample_config):
        """Create PasswordGenerator instance."""
        return PasswordGenerator(sample_config)

    def test_get_character_set_default(self, generator):
        """Test default character set."""
        char_set = generator.get_character_set()
        assert len(char_set) > 0
        assert any(c.islower() for c in char_set)
        assert any(c.isupper() for c in char_set)
        assert any(c.isdigit() for c in char_set)
        assert any(not c.isalnum() for c in char_set)

    def test_get_character_set_lowercase_only(self, generator):
        """Test lowercase-only character set."""
        char_set = generator.get_character_set(
            lowercase=True,
            uppercase=False,
            digits=False,
            symbols=False,
        )
        assert all(c.islower() for c in char_set)
        assert len(char_set) > 0

    def test_get_character_set_uppercase_only(self, generator):
        """Test uppercase-only character set."""
        char_set = generator.get_character_set(
            lowercase=False,
            uppercase=True,
            digits=False,
            symbols=False,
        )
        assert all(c.isupper() for c in char_set)
        assert len(char_set) > 0

    def test_get_character_set_digits_only(self, generator):
        """Test digits-only character set."""
        char_set = generator.get_character_set(
            lowercase=False,
            uppercase=False,
            digits=True,
            symbols=False,
        )
        assert all(c.isdigit() for c in char_set)
        assert len(char_set) > 0

    def test_get_character_set_no_selection(self, generator):
        """Test that no character sets raises ValueError."""
        with pytest.raises(ValueError, match="At least one character set"):
            generator.get_character_set(
                lowercase=False,
                uppercase=False,
                digits=False,
                symbols=False,
            )

    def test_get_character_set_exclude_similar(self, generator):
        """Test excluding similar characters."""
        char_set_with = generator.get_character_set(exclude_similar=False)
        char_set_without = generator.get_character_set(exclude_similar=True)

        # Similar characters should be excluded
        similar_chars = "0OIl1"
        for char in similar_chars:
            if char in char_set_with:
                assert char not in char_set_without

    def test_get_character_set_exclude_ambiguous(self, generator):
        """Test excluding ambiguous characters."""
        char_set_with = generator.get_character_set(exclude_ambiguous=False)
        char_set_without = generator.get_character_set(exclude_ambiguous=True)

        # Ambiguous characters should be excluded
        ambiguous_chars = "{}[]()/\\'\"`~,;:.<>"
        for char in ambiguous_chars:
            if char in char_set_with:
                assert char not in char_set_without

    def test_generate_password_valid_length(self, generator):
        """Test password generation with valid length."""
        password = generator.generate_password(length=16)
        assert len(password) == 16
        assert isinstance(password, str)

    def test_generate_password_min_length(self, generator):
        """Test password generation with minimum length."""
        password = generator.generate_password(length=4)
        assert len(password) == 4

    def test_generate_password_max_length(self, generator):
        """Test password generation with maximum length."""
        password = generator.generate_password(length=128)
        assert len(password) == 128

    def test_generate_password_too_short(self, generator):
        """Test that too short password raises ValueError."""
        with pytest.raises(ValueError, match="Password length must be"):
            generator.generate_password(length=3)

    def test_generate_password_too_long(self, generator):
        """Test that too long password raises ValueError."""
        with pytest.raises(ValueError, match="Password length must be"):
            generator.generate_password(length=200)

    def test_generate_password_custom_character_sets(self, generator):
        """Test password generation with custom character sets."""
        password = generator.generate_password(
            length=20, lowercase=True, uppercase=False, digits=False, symbols=False
        )
        assert len(password) == 20
        assert all(c.islower() for c in password)

    def test_generate_password_different_lengths(self, generator):
        """Test password generation with different lengths."""
        for length in [8, 16, 32, 64]:
            password = generator.generate_password(length=length)
            assert len(password) == length

    def test_generate_password_uniqueness(self, generator):
        """Test that generated passwords are likely unique."""
        passwords = [generator.generate_password(length=16) for _ in range(10)]
        # All passwords should be different (very high probability)
        assert len(set(passwords)) == len(passwords)

    def test_calculate_entropy(self, generator):
        """Test entropy calculation."""
        password = "test123"
        char_set_size = 62  # 26 lowercase + 26 uppercase + 10 digits
        entropy = generator.calculate_entropy(password, char_set_size)

        assert entropy > 0
        assert isinstance(entropy, float)

    def test_calculate_entropy_zero_length(self, generator):
        """Test entropy calculation for empty password."""
        entropy = generator.calculate_entropy("", 62)
        assert entropy == 0.0

    def test_calculate_entropy_zero_charset(self, generator):
        """Test entropy calculation for zero character set."""
        entropy = generator.calculate_entropy("test", 0)
        assert entropy == 0.0

    def test_generate_password_all_options(self, generator):
        """Test password generation with all options enabled."""
        password = generator.generate_password(
            length=20,
            lowercase=True,
            uppercase=True,
            digits=True,
            symbols=True,
            exclude_similar=True,
            exclude_ambiguous=False,
        )
        assert len(password) == 20
        assert len(password) > 0
