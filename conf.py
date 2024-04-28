import json
import os
import pathlib
import sys
import logging
from typing import List

# determine if application is a script file or frozen exe
if getattr(sys, "frozen", False):
    PROJECT_DIR = pathlib.Path(sys.executable).parent.absolute()
elif __file__:
    PROJECT_DIR = pathlib.Path(__file__).parent.absolute()
LOG_FILE_PATH = os.path.join(PROJECT_DIR, "logging.conf")
SPREADSHEET_TOKEN_FILE_PATH = os.path.join(PROJECT_DIR, "token.pickle")
SPREADSHEET_CREDENTIALS_FILE_PATH = os.path.join(PROJECT_DIR, "credentials.json")


class Config:
    def __init__(self):
        config_file = "config.json"
        if not os.path.isfile(config_file):
            logging.error("Failed to find config file: %s", config_file)
            sys.exit(1)

        self.config = json.load(open(config_file, "r"))

    def save(self):
        with open("config.json", "w") as outfile:
            json.dump(self.config, outfile, indent=4)

    def dump(self):
        logging.debug(json.dumps(self.config, indent=2))

    @property
    def stats_path(self) -> str:
        return self.config["stats_path"]

    @stats_path.setter
    def stats_path(self, value):
        self.config["stats_path"] = value

    @property
    def aimlab_db_path(self) -> str:
        return self.config["aimlab_db_path"]

    @aimlab_db_path.setter
    def aimlab_db_path(self, value):
        self.config["aimlab_db_path"] = value

    @property
    def sheet_id_kovaaks(self) -> str:
        return self.config["sheet_id_kovaaks"]

    @sheet_id_kovaaks.setter
    def sheet_id_kovaaks(self, value):
        self.config["sheet_id_kovaaks"] = value

    @property
    def sheet_id_aimlab(self) -> str:
        return self.config["sheet_id_aimlab"]

    @sheet_id_aimlab.setter
    def sheet_id_aimlab(self, value):
        self.config["sheet_id_aimlab"] = value

    @property
    def scenario_name_ranges(self) -> List[str]:
        return self.config["scenario_name_ranges"]

    @scenario_name_ranges.setter
    def scenario_name_ranges(self, value):
        self.config["scenario_name_ranges"] = value

    @property
    def highscore_ranges(self) -> List[str]:
        return self.config["highscore_ranges"]

    @highscore_ranges.setter
    def highscore_ranges(self, value):
        self.config["highscore_ranges"] = value

    @property
    def average_ranges(self) -> List[str]:
        return self.config["average_ranges"]

    @average_ranges.setter
    def average_ranges(self, value):
        self.config["average_ranges"] = value

    @property
    def aimlab_name_ranges(self) -> List[str]:
        return self.config["aimlab_name_ranges"]

    @aimlab_name_ranges.setter
    def aimlab_name_ranges(self, value):
        self.config["aimlab_name_ranges"] = value

    @property
    def aimlab_score_ranges(self) -> List[str]:
        return self.config["aimlab_score_ranges"]

    @aimlab_score_ranges.setter
    def aimlab_score_ranges(self, value):
        self.config["aimlab_score_ranges"] = value

    @property
    def aimlab_average_ranges(self) -> List[str]:
        return self.config["aimlab_average_ranges"]

    @aimlab_average_ranges.setter
    def aimlab_average_ranges(self, value):
        self.config["aimlab_average_ranges"] = value

    @property
    def aimlab_average_ranges(self) -> List[str]:
        return self.config["aimlab_average_ranges"]

    @aimlab_average_ranges.setter
    def aimlab_average_ranges(self, value):
        self.config["aimlab_average_ranges"] = value

    @property
    def run_mode(self) -> str:
        return self.config["run_mode"]

    @run_mode.setter
    def run_mode(self, value):
        self.config["run_mode"] = value

    @property
    def game(self) -> str:
        return self.config["game"]

    @game.setter
    def game(self, value):
        self.config["game"] = value

    @property
    def calculate_averages(self) -> bool:
        return self.config["calculate_averages"]

    @calculate_averages.setter
    def calculate_averages(self, value):
        self.config["calculate_averages"] = value

    @property
    def num_of_runs_to_average(self) -> int:
        return int(self.config["num_of_runs_to_average"])

    @num_of_runs_to_average.setter
    def num_of_runs_to_average(self, value):
        self.config["num_of_runs_to_average"] = value

    @property
    def polling_interval(self) -> int:
        return int(self.config["polling_interval"])

    @polling_interval.setter
    def polling_interval(self, value):
        self.config["polling_interval"] = value

    @property
    def open_config(self) -> bool:
        return self.config["open_config"]

    @open_config.setter
    def open_config(self, value):
        self.config["open_config"] = value
