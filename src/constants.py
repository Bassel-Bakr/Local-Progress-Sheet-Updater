import os
import pathlib
import sys

# determine if application is a script file or frozen exe
if getattr(sys, "frozen", False):
    ROOT_DIR = pathlib.Path(sys.executable).parent.parent.absolute()
elif __file__:
    ROOT_DIR = pathlib.Path(__file__).parent.parent.absolute()

LOG_FILE_PATH = os.path.join(ROOT_DIR, "logging.conf")
SPREADSHEET_TOKEN_FILE_PATH = os.path.join(ROOT_DIR, "token.pickle")
SPREADSHEET_CREDENTIALS_FILE_PATH = os.path.join(ROOT_DIR, "credentials.json")

CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
LOGGING_CONFIG_PATH = os.path.join(ROOT_DIR, "logging.conf")
