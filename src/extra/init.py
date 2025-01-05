import sqlite3
import os, sys

dir = os.path.join(os.path.dirname(sys.path[0]), "src", "extra")
__DBNAME__ = os.path.join(dir, "austalk.db")
__SQL__ = os.path.join(dir, "austalk.sql")

def initdb():
    # Initialise Database
    print __DBNAME__
    db = sqlite3.connect(__DBNAME__)
    cur = db.cursor()

    # The following does not seem to work
    # cur.executescript(open(__SQL__).read())

    # Execute each statement in the SQL file
    for stmt in open(__SQL__).read().split(";"):
        stmt = stmt.strip()
        if len(stmt):
            #print "Executed:", stmt
            cur.execute(stmt)

    # Commit changes
    db.commit()

if __name__=='__main__':
    initdb()
