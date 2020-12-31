import logging
import sqlite3
try:
    import cPickle as pickle
except ImportError:
    import pickle # noqa
from multiprocessing import Manager
from typing import Optional, List, Tuple

log = logging.getLogger('rich')


class SqlBackend:
    """\
    Manages persistent data
    """
    def __init__(self, db):
        self._lock = Manager().Lock()
        self._connection = sqlite3.connect(db, check_same_thread=False)

        self._cursor = self._connection.cursor()

        with self._lock:
            self._cursor.execute('create table if not exists data (\
                                 id integer primary key not null,\
                                 chatid integer not null,\
                                 query text not null,\
                                 data blob not null)')
            self._connection.commit()

    def save(self, chatid: int, query: str, data: Optional[List] = None) -> bool:
        if data is None:
            data = list()
        try:
            pickle_data = pickle.dumps(data, pickle.HIGHEST_PROTOCOL)
            with self._lock:
                self._cursor.execute('insert into data values (null,?,?,?)', (chatid, query, sqlite3.Binary(pickle_data)))
                self._connection.commit()
            return True
        except sqlite3.Error as sql_err:
            log.debug(sql_err)
        return False

    def set_data(self, entryid: int, data: List) -> bool:
        try:
            pickle_data = pickle.dumps(data, pickle.HIGHEST_PROTOCOL)
            with self._lock:
                self._cursor.execute('update data set data=? where id=?', (sqlite3.Binary(pickle_data), entryid,))
                self._connection.commit()
            return True
        except sqlite3.Error as sql_err:
            log.debug(sql_err)
        return False

    def load(self, chatid: Optional[int] = None) -> List[Tuple]:
        try:
            with self._lock:
                if chatid:
                    result = self._cursor.execute('select * from data where chatid=?', (chatid,))
                else:
                    result = self._cursor.execute('select * from data')
                return [(*res[:-1], pickle.loads(res[-1][0])) for res in result.fetchall()]
        except sqlite3.Error as sql_err:
            log.debug(sql_err)
        return list()

    def delete(self, chatid: int, query: Optional[str] = None) -> bool:
        try:
            with self._lock:
                if query:
                    self._cursor.execute('delete from data where chatid=? and query=?', (chatid, query,))
                else:
                    self._cursor.execute('delete from data where chatid=?', (chatid,))
                self._connection.commit()
            return True
        except sqlite3.Error as sql_err:
            log.debug(sql_err)
        return False
