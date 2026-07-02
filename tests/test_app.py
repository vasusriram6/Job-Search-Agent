import sys
import os
from streamlit.testing.v1 import AppTest

def test_app_streamlit():
    # Changing working directory first to avoid relative import related errors

    # Get the current script directory
    test_dir = os.path.dirname(os.path.abspath(__file__))

    # Root folder of this script's directory
    project_root = os.path.dirname(test_dir)

    app_dir = os.path.join(project_root, "src")

    # Add project root to sys.path
    if app_dir not in sys.path:
        sys.path.append(app_dir)

    at = AppTest.from_file("app.py").run(timeout=30)
    assert not at.exception

    print("App testing passed")