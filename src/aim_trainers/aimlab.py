from datetime import datetime
import logging
import urllib.request
import sqlite3
from typing import Tuple
import googleapiclient.discovery

from aim_trainers.aim_trainer import AimTrainer
from conf import Config
from errors import handle_error
from scenario import Scenario
from sheets import cells_from_sheet_ranges, read_sheet_range


class Aimlab(AimTrainer):
    def __init__(
        self,
        config: Config,
        sheet_api: googleapiclient.discovery.Resource,
    ):
        AimTrainer.__init__(self, sheet_api=sheet_api)
        self.config = config
        self.sheet_api = sheet_api

        cs_level_ids, blacklist = self.init_cs_level_ids_and_blacklist()
        self.blacklist = blacklist
        self.cs_level_ids = cs_level_ids
        self.scenarios = self.init_scenario_data()

    def process_files(self):
        AimTrainer.process_files(self)
        self.update()

    def init_scenario_data(self):
        AimTrainer.init_scenario_data(self)

        hs_cells_iter = cells_from_sheet_ranges(self.config.aimlab_score_ranges)
        avg_cells_iter = cells_from_sheet_ranges(self.config.aimlab_average_ranges)

        scens = {}

        i = 0
        for r in self.config.aimlab_name_ranges:
            for s in read_sheet_range(self.sheet_api, self.config.sheet_id_aimlab, r):
                if s not in scens:
                    scens[s] = Scenario()

                scens[s].hs_cells.append(next(hs_cells_iter))
                scens[s].avg_cells.append(next(avg_cells_iter))
                scens[s].ids.append(i)
                i += 1

        highscores = []
        for r in self.config.aimlab_score_ranges:
            highscores += map(
                lambda x: float(x),
                read_sheet_range(self.sheet_api, self.config.sheet_id_aimlab, r),
            )

        averages = []
        for r in self.config.aimlab_average_ranges:
            averages += map(
                lambda x: float(x),
                read_sheet_range(self.sheet_api, self.config.sheet_id_aimlab, r),
            )

        if len(highscores) < len(scens):  # Require highscore cells but not averages
            handle_error("range_size")

        for s in scens:
            scens[s].hs = min([highscores[i] for i in scens[s].ids])
            scens[s].avg = min([averages[i] for i in scens[s].ids])

        return scens

    def update(self):
        AimTrainer.update(self)

        new_hs = set()
        new_avgs = set()

        # Aimlab has its data in /AppData/LocalLow/statespace/aimlab_tb/Users/[USER_ID]/LocalDB/klutch.bytes

        db_path = f"{self.config.aimlab_db_path}/klutch.bytes"
        # Open db connection
        con = sqlite3.connect(db_path)
        cur = con.cursor()

        # Get scores from the database
        result = []
        for csid, name in self.cs_level_ids.items():
            cur.execute(
                f"""SELECT taskName, score
                FROM TaskData
                WHERE taskName = ? AND createDate > date(?)""",
                [csid, self.blacklist[name]],
            )
            temp = cur.fetchall()
            result.extend(temp)

        for s in result:
            name = self.cs_level_ids[s[0]]
            score = s[1]
            if score > self.scenarios[name].hs:
                self.scenarios[name].hs = score
                new_hs.add(name)

            if self.config.calculate_averages:
                self.scenarios[name].recent_scores.append(
                    score
                )  # Will be last N runs if files are fed chronologically
                if (
                    len(self.scenarios[name].recent_scores)
                    > self.config.num_of_runs_to_average
                ):
                    self.scenarios[name].recent_scores.pop(0)

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
            new_hs, new_avgs, self.scenarios, self.config.sheet_id_aimlab
        )

    def init_cs_level_ids_and_blacklist(self) -> Tuple[dict, dict]:
        logging.debug("Initializing CsLevelIds...")
        url = "https://docs.google.com/spreadsheets/d/1uvXfx-wDsyPg5gM79NDTszFk-t6SL42seL-8dwDTJxw/gviz/tq?tqx=out:csv&sheet=cslevelids"
        response = urllib.request.urlopen(url)
        lines = [l.decode("utf-8") for l in response.readlines()]
        cs_level_ids = dict()
        blacklist = dict()
        for line in lines[1:]:
            splits = line.split('","')
            name = splits[0].replace('"', "")
            cs_level_id = splits[1].replace('"', "")
            cs_level_ids[cs_level_id] = name.lower()
            date = datetime.strptime(
                splits[2].replace('"', "").replace("\n", ""), "%d.%m.%Y"
            ).date()
            blacklist[name.lower()] = date

        return cs_level_ids, blacklist
