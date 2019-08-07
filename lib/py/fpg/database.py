"""
Module to create and handle database
"""
import json
import sqlite3
from typing import Any
from lib.py.fpg.constants import (
    Constants
)
from lib.py.fpg.utils import (
    get_epoch_from_datetime
)


class Database:
    def __init__(
            self
    ) -> None:
        self.coins_tables = {}
        self.connection = None
        self.strategy_objects_table = None
        self.trading_history_table = None
        self.crsr = None
        self.trade_history_columns = [
            'trade_id',
            'trade_time',
            'amount',
            'price',
            'trade_type',
            'enter_exit',
            'leverage',
            'asset',
            'strategy_id',
            'strategy_name',
            'portfolio_balance'
        ]

    def connect(
            self: Any,
            query: bool = False
    ) -> None:
        """
        Connects to the database
        :return: None
        """
        self.connection = sqlite3.connect(f"{Constants.database_link}")
        if query:
            self.connection.row_factory = sqlite3.Row
        self.crsr = self.connection.cursor()

    def execute(
            self: Any,
            command,
            values: tuple = None
    ) -> None:
        """

        :param command:
        :param values:
        :return:
        """
        if values is None:
            self.crsr.execute(command)
        else:
            self.crsr.execute(command, values)
        self.connection.commit()

    def close_connection(
            self: Any
    ) -> None:
        """

        :return:
        """
        self.connection.close()

    def initialize_database(
            self: Any,
            name: str = 'strategy_objects'
    ) -> None:
        """
        Will either create (if not exists) or find
        a table for the strategy objects
        :return: None changes default values
        """
        self.connect()
        self.strategy_objects_table = name
        strategy_table_command = f"""
        CREATE TABLE IF NOT EXISTS {self.strategy_objects_table} (
        strategy_id INTEGER PRIMARY KEY,
        strategy_name VARCHAR(50),
        pair VARCHAR(10),
        creation_time REAL,
        strategy_position VARCHAR,
        amount REAL,
        is_expired INTEGER,
        live_position VARCHAR,
        days_passed INTEGER,
        is_leverage VARCHAR,
        additional_user_settings VARCHAR);
        """
        self.execute(command=strategy_table_command)
        self.trading_history_table = "trading_history_" + name
        trading_table_command = f"""
        CREATE TABLE IF NOT EXISTS {self.trading_history_table} (
        trade_id INTEGER PRIMARY KEY,
        trade_time REAL,
        amount REAL,
        price REAL,
        trade_type VARCHAR,
        enter_exit VARCHAR,
        leverage INT,
        asset VARCHAR,
        strategy_id INT,
        strategy_name VARCHAR,
        portfolio_balance VARCHAR);
        """
        self.execute(command=trading_table_command)
        self.close_connection()

    def initialize_coin_db(
            self,
            pair
    ) -> None:
        """
        :param pair: Pair traded
        :return: will either create a table for
                 for the pair or will find an old one
                 created
        """
        db_pair = pair.replace("/", "_")
        coin_table_command = f"""
        CREATE TABLE IF NOT EXISTS {db_pair} (
        unix_time REAL PRIMARY KEY,
        price REAL);
        """
        self.execute(
            command=coin_table_command
        )
        return db_pair

    def insert_coin_data(
            self: Any,
            pair: str,
            price: float,
            date: Any
    ) -> None:
        """
        Will find the database corresponding to the
        pair and will store the data if the same data
        does not exist
        :param pair: str -> pair traded
        :param price: float - > current price
        :param date: epoch since fetch
        :return:
        """
        self.connect()
        try:
            db_pair = self.coins_tables[pair]
        except KeyError:
            db_pair = self.initialize_coin_db(pair)
            self.coins_tables[pair] = db_pair
        values_to_insert = (get_epoch_from_datetime(date), price)
        update_command = f"""
        INSERT OR REPLACE INTO {db_pair} (unix_time, price) VALUES (
        ?,
        ?
        );
        """
        self.execute(
            command=update_command,
            values=values_to_insert
        )
        self.close_connection()

    def insert_new_strategy(
            self: Any,
            strategy_object
    ) -> None:
        """
        Will write new strategy objects to the table
        :param strategy_object:
        :return: None
        """
        self.connect()
        values_to_insert = (
            strategy_object.strategy_id,
            strategy_object.strategy_name,
            strategy_object.pair,
            get_epoch_from_datetime(strategy_object.creation_time),
            strategy_object.strategy_position,
            strategy_object.amount,
            strategy_object.is_expired,
            strategy_object.live_position,
            strategy_object.days_passed,
            strategy_object.is_leverage,
            json.dumps(strategy_object.create_dictionary_for_db())
        )
        strategy_command = f"""
        INSERT INTO {self.strategy_objects_table} VALUES (
        ?,?,?,?,?,?,?,?,?,?,?)
        """
        self.execute(
            command=strategy_command,
            values=values_to_insert
        )
        self.close_connection()

    def update_strategy(
            self: Any,
            strategy_object: Any
    ) -> None:
        """
        Will receieve strategy object and will
        update its entry in the database based on
        id, name and pair
        :param strategy_object:
        :return: None -> updates db
        """
        self.connect()
        values_to_insert = (
            strategy_object.strategy_position,  # 1
            strategy_object.amount,  # 2
            strategy_object.is_expired,  # 3
            strategy_object.live_position,  # 4
            strategy_object.days_passed,  # 5
            strategy_object.is_leverage,  # 6
            json.dumps(strategy_object.create_dictionary_for_db()),  # 7
            strategy_object.strategy_id,  # 8
            strategy_object.pair,  # 9
            strategy_object.strategy_name  # 10
        )
        update_command = f"""
        UPDATE {self.strategy_objects_table} SET
        strategy_position = ?,
        amount = ?,
        is_expired = ?,
        live_position = ?,
        days_passed = ?,
        is_leverage = ?,
        additional_user_settings = ?
        WHERE (strategy_id = ? AND pair = ? AND strategy_name = ?)
        """
        self.execute(
            command=update_command,
            values=values_to_insert
        )
        self.close_connection()

    def restore_last_objects(
            self
    ) -> list:
        """
        Will query the DB and will return
        all rows were objects were not expired
        :return: list of not expired objects
        """
        self.connect(query=True)
        command = f"""
        SELECT * FROM {self.strategy_objects_table}
        WHERE is_expired = 0
        """
        self.execute(
            command=command
        )
        live_strategies = self.crsr.fetchall()
        self.close_connection()
        if live_strategies:
            return live_strategies
        else:
            return None

    def set_object_to_expired(
            self: Any,
            strategy_id: int
    ) -> None:
        """
        Will update the strategy id passed
        to expired
        :param strategy_id: int -> id of the strategy object
        :return: None -> updates the db
        """
        self.connect()
        values_to_insert = (True, strategy_id)
        update_command = f"""
        UPDATE {self.strategy_objects_table}
        SET is_expired = ?
        WHERE strategy_id = ?
        """
        self.execute(
            command=update_command,
            values=values_to_insert
        )
        self.close_connection()

    def retrieve_all_objects(
            self: Any
    ):
        """
        Will query the database and return
        all objects in the session
        :return:
        """
        self.connect(query=True)
        command = f"""
                SELECT * FROM {self.strategy_objects_table}
                """
        self.execute(
            command=command
        )
        strategies = self.crsr.fetchall()
        self.close_connection()
        return strategies

    def save_trade(
            self: Any,
            action,
            portfolio_amount
    ) -> None:
        self.connect()
        values_to_insert = (
            action['trade_id'],
            action['trade_time'],
            action['amount'],
            action['price'],
            action['type'],
            action['action'],
            action['leverage'],
            action['pair'].split('/')[0],
            action['strategy_id'],
            action['strategy_name'],
            json.dumps(portfolio_amount)
        )
        trade_command = f"""
                INSERT INTO {self.trading_history_table} VALUES (
                ?,?,?,?,?,?,?,?,?,?,?)
                """
        self.execute(
            command=trade_command,
            values=values_to_insert
        )

    def retrieve_all_trades(
            self: Any
    ):
        """
        Will query the database and return
        all objects in the session
        :return:
        """
        self.connect(query=True)
        command = f"""
                SELECT * FROM {self.trading_history_table}
                """
        self.execute(
            command=command
        )
        trades = self.crsr.fetchall()
        self.close_connection()
        return trades

