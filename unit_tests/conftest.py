import pytest
from pathlib import Path

@pytest.fixture
def load_fixture():
    """
    A pytest fixture that loads a file from the 'fixtures' directory.

    This makes it easy for any test to get the content of a reST file
    by simply calling this fixture with the filename.

    Args:
        filename (str): The name of the file in the tests/fixtures/ directory.

    Returns:
        str: The content of the file.
    """
    def _load_file(filename):
        # Construct the full path to the fixture file
        # __file__ is the path to the current file (conftest.py)
        # .parent gives the directory (tests/)
        # .joinpath() combines paths intelligently
        fixture_path = Path(__file__).parent.joinpath("fixtures", filename)
        
        if not fixture_path.exists():
            raise FileNotFoundError(f"Fixture file not found at: {fixture_path}")
            
        with open(fixture_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    return _load_file
