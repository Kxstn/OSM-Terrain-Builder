import os
from pathlib import Path
from dotenv import load_dotenv

"""Main Config File.

Config.py is used to store default values for most var inputs,
that can be made by the user. Also it contains the path to
the .evn file which should contain the OpenTopography API key.
"""

DEFAULT_TERRAIN_SIZE_CM = 15.0
DEFAULT_BASE_THICKNESS_MM = 3.0
DEFAULT_BUILDING_HEIGHT_MM = 3.0
DEFAULT_WATER_DEPTH_MM = 0.5
DEFAULT_OUTPUT_DIR = "output"

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

OPENTOPOGRAPHY_API_KEY = os.getenv("OPENTOPOGRAPHY_API_KEY")
API_URL = "https://portal.opentopography.org/API/globaldem"

if not OPENTOPOGRAPHY_API_KEY:
    raise RuntimeError(
        "OpenTopography API key not found. "
        "Check that your .env file is in the project root."
    )