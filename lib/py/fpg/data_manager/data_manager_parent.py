"""
Super class for the data handler
"""
from typing import Any


class DataHandlerSuper:
    def __init__(
            self: Any,
            fpg_connector: Any = None,
            database: Any = None
    ) -> None:
        self.fpg_connector = fpg_connector
        self.database = database
        self.current_time = None
        self.current_price = None
