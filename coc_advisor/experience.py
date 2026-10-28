"""Durable local episodes; the SQLite writer never runs in the control loop."""
import json
from contextlib import closing
from pathlib import Path
import queue
import sqlite3
import threading
import time
import uuid


class ExperienceStore:
    def __init__(self, root):
        root=Path(root); root.mkdir(parents=True,exist_ok=True)
        self.path=root/'experience.sqlite3'; self.queue=queue.Queue(maxsize=1024)
        self.error=None; self.contexts={}; self.closed=False
        with closing(sqlite3.connect(self.path)) as db:
            db.executescript('''PRAGMA journal_mode=WAL;
              CREATE TABLE IF NOT EXISTS episodes(id TEXT PRIMARY KEY, created REAL,
                context TEXT, prediction TEXT, result TEXT, status TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, battle_id TEXT,
                monotonic REAL, kind TEXT, payload TEXT);''')
        self.thread=threading.Thread(target=self._writer,daemon=True); self.thread.start()

    def _writer(self):
        with closing(sqlite3.connect(self.path)) as db:
            while True:
                item=self.queue.get()
                try:
                    if item is None: return
                    sql,args=item; db.execute(sql,args); db.commit()
                except Exception as exc: self.error=exc
                finally: self.queue.task_done()

    def _enqueue(self,sql,args):
        if self.closed: raise RuntimeError('Experience store closed.')
        if self.error: raise RuntimeError(f'Experience write failed: {self.error}')
        try: self.queue.put_nowait((sql,args))
        except queue.Full as exc: raise RuntimeError('Experience writer is behind; pause control.') from exc

    def begin_battle(self, context):
        context=json.loads(json.dumps(context,allow_nan=False)); b=uuid.uuid4().hex
        self.contexts[b]=context
        self._enqueue('INSERT INTO episodes VALUES(?,?,?,?,?,?)',
            (b,time.time(),json.dumps(context),None,None,'incomplete'))
        return b

    def append_event(self,battle_id,kind,payload):
        self._enqueue('INSERT INTO events(battle_id,monotonic,kind,payload) VALUES(?,?,?,?)',
                      (battle_id,time.monotonic(),kind,json.dumps(payload,allow_nan=False)))

    def update_context(self,battle_id,context):
        context=json.loads(json.dumps(context,allow_nan=False)); self.contexts[battle_id]=context
        self._enqueue('UPDATE episodes SET context=? WHERE id=? AND prediction IS NULL',
                      (json.dumps(context),battle_id))

    def record_prediction(self,battle_id,prediction):
        if prediction.get('predicted_at',0)<self.contexts[battle_id].get('observed_at',0):
            raise ValueError('Features were not available at prediction time.')
        self._enqueue('UPDATE episodes SET prediction=? WHERE id=? AND prediction IS NULL',
                      (json.dumps(prediction,allow_nan=False),battle_id))

    def finish_battle(self,battle_id,result_evidence):
        d=result_evidence.get('destruction'); stars=result_evidence.get('stars')
        valid=(type(d) in (int,float) and 0<=d<=100 and type(stars) is int and 0<=stars<=3
               and (d!=100 or stars==3) and (stars!=3 or d==100)
               and result_evidence.get('verified') is True and bool(result_evidence.get('evidence')))
        status='accepted' if valid else 'quarantined'
        self._enqueue("""UPDATE episodes SET status=CASE WHEN result IS NULL THEN ?
            WHEN json_extract(result,'$.destruction') IS ? AND json_extract(result,'$.stars') IS ?
             AND json_extract(result,'$.verified') IS ? THEN status ELSE 'quarantined' END,
            result=COALESCE(result,?) WHERE id=?""",
            (status,d,stars,int(result_evidence.get('verified') is True),json.dumps(result_evidence,allow_nan=False),battle_id))

    def flush(self):
        self.queue.join()
        if self.error: raise RuntimeError(f'Experience write failed: {self.error}')

    def episodes(self,status='accepted'):
        self.flush()
        with closing(sqlite3.connect(self.path)) as db:
            rows=db.execute('SELECT id,created,context,prediction,result,status FROM episodes WHERE status=? ORDER BY created,id',(status,)).fetchall()
        return [dict(id=r[0],created=r[1],context=json.loads(r[2]),
                     prediction=json.loads(r[3]) if r[3] else None,
                     result=json.loads(r[4]) if r[4] else None,status=r[5]) for r in rows]

    def close(self):
        if self.closed:return
        self.queue.join(); self.queue.put(None); self.thread.join(timeout=3); self.closed=True
