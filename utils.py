import logging
import sys
from threading import Timer
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from conf import Config


def debounce(wait):
    """Decorator that will postpone a functions
    execution until after wait seconds
    have elapsed since the last time it was invoked.
    https://gist.github.com/walkermatt/2871026"""

    def decorator(fn):
        def debounced(*args, **kwargs):
            def call_it():
                fn(*args, **kwargs)

            try:
                debounced.t.cancel()
            except AttributeError:
                pass
            debounced.t = Timer(wait, call_it)
            debounced.t.start()

        return debounced

    return decorator


def handle_exception(exc_type, exc_value, exc_traceback):
    """
    Function that replaces sys.excepthook to also log uncaught exceptions, see:
    https://stackoverflow.com/questions/6234405/logging-uncaught-exceptions-in-python/16993115#16993115
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.critical(
        "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
    )


class LambdaDispatchEventHandler(FileSystemEventHandler):
    def __init__(self, config: Config, func):
        self.func = func

    def on_any_event(self, event):
        if event.is_directory:
            return None
        elif event.event_type == "modified":
            if self.config.game == "Kovaaks" or event.src_path.endswith("klutch.bytes"):
                self.func()
