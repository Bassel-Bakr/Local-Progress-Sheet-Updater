import csv
from datetime import datetime
import logging
import os
import googleapiclient.discovery
import urllib.request

from aim_trainers.aim_trainer import AimTrainer
from conf import Config
from errors import handle_error
from scenario import Scenario
from sheets import cells_from_sheet_ranges, read_sheet_range


class Kovaaks(AimTrainer):
    def __init__(
        self,
        config: Config,
        sheet_api: googleapiclient.discovery.Resource,
    ):
        AimTrainer.__init__(self, sheet_api=sheet_api)
        self.config = config
        self.sheet_api = sheet_api
        self.blacklist = self.init_version_blacklist()
        self.stats = list(sorted(os.listdir(config.stats_path)))
        self.scenarios = self.init_scenario_data()

    def process_files(self):
        AimTrainer.process_files(self)

        self.update()

    def init_scenario_data(self):
        AimTrainer.init_scenario_data(self)

        hs_cells_iter = cells_from_sheet_ranges(self.config.highscore_ranges)
        if self.config.calculate_averages:
            avg_cells_iter = cells_from_sheet_ranges(self.config.average_ranges)

        scens = {}

        i = 0
        for r in self.config.scenario_name_ranges:
            for s in read_sheet_range(self.sheet_api, self.config.sheet_id_kovaaks, r):
                if s not in scens:
                    scens[s] = Scenario()

                scens[s].hs_cells.append(next(hs_cells_iter))
                if self.config.calculate_averages:
                    try:
                        scens[s].avg_cells.append(next(avg_cells_iter))
                    except AttributeError:
                        handle_error("averages")
                scens[s].ids.append(i)
                i += 1

        highscores = []
        for r in self.config.highscore_ranges:
            highscores += map(
                lambda x: float(x),
                read_sheet_range(self.sheet_api, self.config.sheet_id_kovaaks, r),
            )

        if self.config.calculate_averages:
            averages = []
            for r in self.config.average_ranges:
                averages += map(
                    lambda x: float(x),
                    read_sheet_range(self.sheet_api, self.config.sheet_id_kovaaks, r),
                )

        if len(highscores) < len(scens):  # Require highscore cells but not averages
            handle_error("range_size")

        for s in scens:
            scens[s].hs = min([highscores[i] for i in scens[s].ids])
            if self.config.calculate_averages:
                scens[s].avg = min([averages[i] for i in scens[s].ids])

        return scens

    def update(self):
        AimTrainer.update(self)

        new_stats = os.listdir(self.config.stats_path)
        files = list(sorted([f for f in new_stats if f not in self.stats]))

        new_hs = set()
        new_avgs = set()

        # Process new runs to populate new_hs and new_avgs
        for f in files:
            s = f[0 : f.find(" - Challenge - ")].lower()
            if s in self.scenarios:
                if s in self.blacklist.keys():
                    date = f[f.find(" - Challenge - ") + 15 :]
                    date = date[: date.find("-")]
                    playdate = datetime.strptime(date, "%Y.%m.%d").date()
                    if playdate <= self.blacklist[s]:
                        continue
                score = self.read_score_from_file(f"{self.config.stats_path}/{f}")
                if score > self.scenarios[s].hs:
                    self.scenarios[s].hs = score
                    new_hs.add(s)

                if self.config.calculate_averages:
                    self.scenarios[s].recent_scores.append(
                        score
                    )  # Will be last N runs if files are fed chronologically
                    if (
                        len(self.scenarios[s].recent_scores)
                        > self.config.num_of_runs_to_average
                    ):
                        self.scenarios[s].recent_scores.pop(0)

        if self.config.calculate_averages:
            for s in self.scenarios:
                runs = self.scenarios[s].recent_scores
                if (
                    runs
                ):  # If the scenario was never played this would result in a div by zero error
                    new_avg = round(sum(runs) / len(runs), 1)
                if runs and new_avg != self.scenarios[s].avg:
                    self.scenarios[s].avg = new_avg
                    new_avgs.add(s)

        self.create_output(
            new_hs, new_avgs, self.scenarios, self.config.sheet_id_kovaaks
        )

        self.stats = new_stats

    def read_score_from_file(self, file_path: str) -> float:
        with open(file_path, newline="") as csvfile:
            for row in csv.reader(csvfile):
                if row and row[0] == "Score:":
                    return round(float(row[1]), 1)
        return 0.0

    def init_version_blacklist(self) -> dict:
        logging.debug("Initializing version blacklist...")

        url = "https://docs.google.com/spreadsheets/d/1uvXfx-wDsyPg5gM79NDTszFk-t6SL42seL-8dwDTJxw/gviz/tq?tqx=out:csv&sheet=Update_Dates"
        response = urllib.request.urlopen(url)
        lines = [l.decode("utf-8") for l in response.readlines()]
        blacklist = dict()
        for line in lines[1:]:
            splits = line.split('","')
            name = splits[0].replace('"', "")
            date = datetime.strptime(
                splits[1].replace('"', "").replace("\n", ""), "%d.%m.%Y"
            ).date()
            blacklist[name.lower()] = date

        return blacklist
