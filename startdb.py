import sqlite3

conn = sqlite3.connect("userdata.db")
cur = conn.cursor()

cur.execute("CREATE TABLE users(name PRIMARY KEY, plays, correct)")