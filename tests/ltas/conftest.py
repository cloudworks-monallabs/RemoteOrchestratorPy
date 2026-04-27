import pytest
import os

@pytest.fixture(autouse=True)
def cleanup_doit_db():
    """
    Ensures a clean state by removing pydoit's tracking database 
    before and after every test execution.
    """
    # The default pydoit DB name is '.doit.db'
    # Note: Depending on the backend, it might be '.doit.db.dat' or '.doit.db.dir'
    db_files = [".doit.db", ".doit.db.dat", ".doit.db.dir", ".doit.db.bak"]
    
    def remove_files():
        for f in db_files:
            if os.path.exists(f):
                os.remove(f)

    # Setup: Run before the test starts
    remove_files()
    print("cleanup_doit_db: remove files ")
    yield  # The test runs here
    
    # Teardown: Run after the test finishes
    remove_files()
