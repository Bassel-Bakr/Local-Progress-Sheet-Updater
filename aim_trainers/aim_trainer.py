import logging
import googleapiclient.discovery

from abc import abstractmethod
from sheets import write_to_cell


class AimTrainer:
    sheet_api: googleapiclient.discovery.Resource

    def __init__(self, sheet_api: googleapiclient.discovery.Resource) -> None:
        self.sheet_api = sheet_api

    @abstractmethod
    def process_files(self):
        pass

    @abstractmethod
    def init_scenario_data(self):
        logging.debug("Initializing scenario data...")
        pass

    @abstractmethod
    def update(self, data: list[str]):
        pass

    def create_output(
        self, new_hs: dict, new_avgs: dict, scens: dict, sheet_id: str
    ) -> None:
        # Pretty output and update progress sheet
        if not new_hs and not new_avgs:
            logging.info("Your progress sheet is up-to-date.")
            return

        if new_hs:
            logging.info(f'New Highscore{"s" if len(new_hs) > 1 else ""}')
            for s in new_hs:
                logging.info(f"{scens[s].hs:>10} - {s}")
                for cell in scens[s].hs_cells:
                    write_to_cell(self.sheet_api, sheet_id, cell, scens[s].hs)

        if new_avgs:
            logging.info(f' New Average{"s" if len(new_hs) > 1 else ""}')
            for s in new_avgs:
                logging.info(f"{scens[s].avg:>10} - {s}")
                for cell in scens[s].avg_cells:
                    write_to_cell(self.sheet_api, sheet_id, cell, scens[s].avg)
