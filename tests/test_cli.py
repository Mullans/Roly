"""Tests for the rollie CLI."""

from io import StringIO
from unittest.mock import patch

from rollie.cli import main


def test_main_prints_hello_world():
    """Test that main() prints 'Hello world'."""
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        main()
        assert mock_stdout.getvalue().strip() == "Hello world"
