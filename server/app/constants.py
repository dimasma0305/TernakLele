import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().absolute().parent
RESOURCES_DIR = BASE_DIR / 'resources'

CONFIG_PATH = BASE_DIR / 'config.py'
SCHEMA_PATH = RESOURCES_DIR / 'schema.sql'

SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', '/app/data/farm.db')
