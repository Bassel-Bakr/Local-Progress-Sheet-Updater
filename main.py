import csv
import json
import logging
import logging.config
import os
import sqlite3
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from threading import Timer

import googleapiclient.discovery
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from aim_trainers.kovaaks import Kovaaks
from errors import handle_error
from gui import Gui
from scenario import Scenario
from sheets import (
    cells_from_sheet_ranges,
    create_service,
    read_sheet_range,
    write_to_cell,
)
from conf import Config
from utils import debounce, handle_exception, LambdaDispatchEventHandler


sheet_api = create_service()


def init_scenario_data_aimlab(
    config: Config, sheet_api: googleapiclient.discovery.Resource
) -> dict:
    hs_cells_iter = cells_from_sheet_ranges(config.aimlab_score_ranges)
    avg_cells_iter = cells_from_sheet_ranges(config.aimlab_average_ranges)

    scens = {}

    i = 0
    for r in config.aimlab_name_ranges:
        for s in read_sheet_range(sheet_api, config.sheet_id_aimlab, r):
            if s not in scens:
                scens[s] = Scenario()

            scens[s].hs_cells.append(next(hs_cells_iter))
            scens[s].avg_cells.append(next(avg_cells_iter))
            scens[s].ids.append(i)
            i += 1

    highscores = []
    for r in config.aimlab_score_ranges:
        highscores += map(
            lambda x: float(x),
            read_sheet_range(sheet_api, config.sheet_id_aimlab, r),
        )

    averages = []
    for r in config.aimlab_average_ranges:
        averages += map(
            lambda x: float(x),
            read_sheet_range(sheet_api, config.sheet_id_aimlab, r),
        )

    if len(highscores) < len(scens):  # Require highscore cells but not averages
        handle_error("range_size")

    for s in scens:
        scens[s].hs = min([highscores[i] for i in scens[s].ids])
        scens[s].avg = min([averages[i] for i in scens[s].ids])

    return scens


def update_aimlab(
    config: Config, scens: dict, cs_level_ids: dict, blacklist: dict
) -> None:
    new_hs = set()
    new_avgs = set()

    # Open db connection
    con = sqlite3.connect(config.aimlab_db_path)
    cur = con.cursor()

    # Get scores from the database
    result = []
    for csid, name in cs_level_ids.items():
        cur.execute(
            f"SELECT taskName, score FROM TaskData WHERE taskName = ? AND createDate > date(?)",
            [csid, blacklist[name]],
        )
        temp = cur.fetchall()
        result.extend(temp)

    for s in result:
        name = cs_level_ids[s[0]]
        score = s[1]
        if score > scens[name].hs:
            scens[name].hs = score
            new_hs.add(name)

        if config.calculate_averages:
            scens[name].recent_scores.append(
                score
            )  # Will be last N runs if files are fed chronologically
            if len(scens[name].recent_scores) > config.num_of_runs_to_average:
                scens[name].recent_scores.pop(0)

    if config.calculate_averages:
        for s in scens:
            runs = scens[s].recent_scores
            if (
                runs
            ):  # If the scenario was never played this would result in a div by zero error
                new_avg = round(sum(runs) / len(runs), 1)
            if runs and new_avg != scens[s].avg:
                scens[s].avg = new_avg
                new_avgs.add(s)

    create_output(
        new_hs, new_avgs, scens, config.sheet_id_aimlab
    )  # check averages here as well


def create_output(new_hs: dict, new_avgs: dict, scens: dict, sheet_id: str) -> None:
    # Pretty output and update progress sheet
    if not new_hs and not new_avgs:
        logging.info("Your progress sheet is up-to-date.")
        return

    if new_hs:
        logging.info(f'New Highscore{"s" if len(new_hs) > 1 else ""}')
        for s in new_hs:
            logging.info(f"{scens[s].hs:>10} - {s}")
            for cell in scens[s].hs_cells:
                write_to_cell(sheet_api, sheet_id, cell, scens[s].hs)

    if new_avgs:
        logging.info(f' New Average{"s" if len(new_hs) > 1 else ""}')
        for s in new_avgs:
            logging.info(f"{scens[s].avg:>10} - {s}")
            for cell in scens[s].avg_cells:
                write_to_cell(sheet_api, sheet_id, cell, scens[s].avg)


def init_version_blacklist() -> dict:
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


def init_cs_level_ids_and_blacklist() -> (dict, dict):
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


@debounce(5)
def process_files_aimlab():
    global config, sheet_api, scenarios, cs_level_ids, blacklist

    update_aimlab(config, scenarios, cs_level_ids, blacklist)


def main():
    logging.config.fileConfig("logging.conf")
    sys.excepthook = handle_exception

    config = Config()

    gui = Gui(config)
    gui.main()

    try:
        config.dump()
    except Exception:
        handle_error("no_credentials")

    logging.debug("Creating service...")

    kovaaks: Kovaaks

    # Aimlab has its data in /AppData/LocalLow/statespace/aimlab_tb/klutch.bytes
    if config.game == "Aimlab":
        logging.debug("Game: Aimlab")
        logging.debug("Initializing scenario data...")
        scenarios = init_scenario_data_aimlab(config, sheet_api)
        logging.debug("Initializing CsLevelIds...")
        cs_level_ids, blacklist = init_cs_level_ids_and_blacklist()
        update_aimlab(config, scenarios, cs_level_ids, blacklist)

    # Kovaaks has its data in the stats folder
    elif config.game == "Kovaaks":
        logging.debug("Game: Kovaaks")

        logging.debug("Initializing version blacklist...")
        blacklist = init_version_blacklist()

        stats = list(sorted(os.listdir(config.stats_path)))

        kovaaks = Kovaaks(config, sheet_api, blacklist, stats)
        kovaaks.update(stats)

    if config.run_mode == "once":
        logging.info("Finished Updating, program will close in 3 seconds...")
        time.sleep(3)
        sys.exit()
    elif config.run_mode == "watchdog":
        observer = Observer()
        if config.game == "Kovaaks":
            event_handler = LambdaDispatchEventHandler(
                config, lambda: kovaaks.process_files()
            )
            observer.schedule(event_handler, config.stats_path)
        elif config.game == "Aimlab":
            event_handler = LambdaDispatchEventHandler(
                config, lambda: process_files_aimlab()
            )
            observer.schedule(
                event_handler, os.path.join(config.aimlab_db_path, os.pardir)
            )
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    elif config.run_mode == "interval":
        while True:
            if config.game == "Kovaaks":
                kovaaks.process_files()
            elif config.game == "Aimlab":
                process_files_aimlab()
            try:
                time.sleep(max(config.polling_interval, 30))
            except KeyboardInterrupt:
                logging.debug("Received keyboard interrupt.")
                break
    else:
        logging.info(
            "Run mode is not supported. Supported types are 'once'/'watchdog'/'interval'."
        )

    logging.info("Program will close in 3 seconds...")
    time.sleep(3)
    sys.exit()


if __name__ == "__main__":
    main()
