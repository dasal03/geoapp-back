from os import environ
from dotenv import load_dotenv
import pymysql
from sqlalchemy.dialects import mysql
from sqlalchemy.exc import SQLAlchemyError
from DataBase.Layer import Layer
from collections.abc import Iterable
from typing import Tuple

pymysql.install_as_MySQLdb()
load_dotenv()

# Enviroment variables
DB_HOST = environ.get("DB_HOST", "localhost")
DB_PORT = environ.get("DB_PORT", 3306)
DB_USER = environ.get("DB_USER", "root")
DB_PASSWORD = environ.get("DB_PASSWORD", "")
DB_NAME = environ.get("DB_NAME")
DB_ENGINE = environ.get("DB_ENGINE", "mysql")


class DataBase:
    """Class base for Database session using pymysql library."""

    def __init__(self, **kwargs: dict):
        """Constructor defined for the instance of class."""
        self._conn = None
        self._username = DB_USER
        self._password = DB_PASSWORD
        self._host = DB_HOST
        self._port = int(DB_PORT)
        self._dbname = DB_NAME
        self._engine = DB_ENGINE

    @property
    def db_name(self):
        """Property db_name."""
        return self._dbname

    def connect(self) -> None:
        """Method for connect to database."""
        connect = False
        try:
            # Fix decimal cast
            conversions = pymysql.converters.conversions.copy()
            conversions[pymysql.converters.FIELD_TYPE.DECIMAL] = float
            conversions[pymysql.converters.FIELD_TYPE.NEWDECIMAL] = float

            connect = pymysql.connect(
                host=self._host,
                port=self._port,
                user=self._username,
                passwd=self._password,
                db=self._dbname,
                cursorclass=pymysql.cursors.DictCursor,
                charset="utf8mb4",
                conv=conversions,
            )

        except pymysql.Error as e:
            print("Error: connect pymysql %d: %s" %
                  (e.args[0], e.args[1]))
            raise SQLAlchemyError(e)

        return connect

    @classmethod
    def compile_sql(
        cls, statement: str, data: Iterable
    ) -> Tuple[str, Iterable]:
        """Staticmethod Compile statemens sqlalchemy to queries for pymysql."""
        if statement is not str:
            compiled = statement.compile(
                dialect=mysql.dialect(),
                compile_kwargs={"render_postcompile": True}
            )
            data = tuple(compiled.params.values())
            return str(compiled), data
        else:
            return statement, data

    def execute(self, sql: str) -> None:
        """Method for execute queries in pymysql."""
        self._conn = self.connect()
        with self._conn:
            with self._conn.cursor() as cursor:
                try:
                    cursor.execute(sql)
                except pymysql.Error as e:
                    print("Error: execute pymysql %d: %s" %
                          (e.args[0], e.args[1]))
                    raise SQLAlchemyError(e)

    def query(self, stmt: str, **kwargs: dict) -> Layer:
        self._conn = self.connect()
        result = self._query(stmt, **kwargs)
        return Layer(result)

    def _query(
        self,
        stmt: str,
        data: Iterable = (),
        one: bool = False,
        size: int = 0,
    ) -> dict:
        """Method for execute select statements."""
        resp = None
        sql, data = self.compile_sql(stmt, data)

        with self._conn:
            with self._conn.cursor() as cursor:
                try:
                    cursor.execute(sql, data)
                    if one:
                        resp = cursor.fetchone()
                    elif size:
                        resp = cursor.fetchmany(size)
                    else:
                        resp = cursor.fetchall()
                except pymysql.Error as e:
                    print("Error: query pymysql %d: %s" %
                          (e.args[0], e.args[1]))
                    raise SQLAlchemyError(e)
        # print(f'!query output: {resp}')
        return resp

    def add(self, stmt: str, data: Iterable = (), many: bool = False) -> int:
        """Method for execute insert statements."""
        result_id = 0
        sql, data = self.compile_sql(stmt, data)
        self._conn = self.connect()

        with self._conn:
            with self._conn.cursor() as cursor:
                try:
                    cursor.execute(sql, data)
                    result_id = cursor.rowcount if many else cursor.lastrowid
                    self._conn.commit()
                except pymysql.Error as e:
                    print("Error: insert pymysql %d: %s" %
                          (e.args[0], e.args[1]))
                    raise SQLAlchemyError(e)
        return result_id

    def update(self, stmt: str, data: Iterable = ()) -> int:
        """Method for execute update statements."""
        row_count = 0
        sql, data = self.compile_sql(stmt, data)
        self._conn = self.connect()

        with self._conn:
            with self._conn.cursor() as cursor:
                try:
                    cursor.execute(sql, data)
                    self._conn.commit()
                    row_count = cursor.rowcount
                except pymysql.Error as e:
                    print("Error: update pymysql %d: %s" %
                          (e.args[0], e.args[1]))
                    raise SQLAlchemyError(e)
        return row_count

    def delete(self, stmt: str, data: Iterable = ()) -> int:
        """Method for execute delete statements."""
        row_count = 0
        sql, data = self.compile_sql(stmt, data)
        self._conn = self.connect()

        with self._conn:
            with self._conn.cursor() as cursor:
                try:
                    cursor.execute(sql, data)
                    self._conn.commit()
                    row_count = cursor.rowcount
                except pymysql.Error as e:
                    print("Error: delete pymysql %d: %s" %
                          (e.args[0], e.args[1]))
                    raise SQLAlchemyError(e)
        return row_count


db = DataBase()
db.connect()
