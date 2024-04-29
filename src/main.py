import logging
import logging.config
import os
import sys
import time

from watchdog.observers import Observer

from aim_trainers.aimlab import Aimlab
from aim_trainers.kovaaks import Kovaaks
from constants import LOGGING_CONFIG_PATH
from errors import handle_error
from gui import Gui
from sheets import (
    create_service,
)
from conf import Config
from utils import handle_exception, LambdaDispatchEventHandler


sheet_api = create_service()


def main():
    logging.config.fileConfig(LOGGING_CONFIG_PATH)
    sys.excepthook = handle_exception

    config = Config()

    gui = Gui(config)
    gui.main()

    try:
        config.dump()
    except Exception:
        handle_error("no_credentials")

    logging.debug("Creating service...")

    aimlab: Aimlab
    kovaaks: Kovaaks

    if config.game == "Aimlab":
        logging.debug("Game: Aimlab")

        aimlab = Aimlab(config, sheet_api)
        aimlab.update()

    # Kovaaks has its data in the stats folder
    elif config.game == "Kovaaks":
        logging.debug("Game: Kovaaks")

        kovaaks = Kovaaks(config, sheet_api)
        kovaaks.update()

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
                config, lambda: aimlab.process_files()
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
                aimlab.process_files()
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
