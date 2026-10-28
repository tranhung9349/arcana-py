"""Versioned analysis snapshots; casting records are never rewritten or re-sampled."""
import json

from .liuyao_analysis import digest


class LiuYaoAnalysisStore:
    def __init__(self, store):
        self.store = store
        with store.connect() as connection:
            connection.execute('''CREATE TABLE IF NOT EXISTS coin_analyses (
                session_id TEXT NOT NULL, cache_key TEXT NOT NULL, response TEXT NOT NULL,
                PRIMARY KEY(session_id, cache_key))''')
            connection.execute('''CREATE TABLE IF NOT EXISTS coin_analysis_latest (
                session_id TEXT PRIMARY KEY, cache_key TEXT NOT NULL)''')

    def execute(self, session, context, interpreter):
        session_id = str(session['request_id'])
        key = digest({'context': context.model_dump(mode='json'), 'rules': interpreter.rules_sha256,
                      'snapshot': digest(session)})
        with self.store.connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            row = connection.execute('SELECT response FROM coin_analyses WHERE session_id=? AND cache_key=?', (session_id, key)).fetchone()
            if row:
                result = json.loads(row[0])
            else:
                result = interpreter.analyze(session, context)
                connection.execute('INSERT INTO coin_analyses VALUES (?, ?, ?)', (session_id, key, json.dumps(result, ensure_ascii=False)))
            connection.execute('INSERT OR REPLACE INTO coin_analysis_latest VALUES (?, ?)', (session_id, key))
            return result

    def latest(self, session_id):
        with self.store.connect() as connection:
            row = connection.execute('''SELECT a.response FROM coin_analysis_latest l
                JOIN coin_analyses a ON a.session_id=l.session_id AND a.cache_key=l.cache_key
                WHERE l.session_id=?''', (str(session_id),)).fetchone()
        return json.loads(row[0]) if row else None
