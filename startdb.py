import sqlite3

conn = sqlite3.connect("userdata.db")
cur = conn.cursor()

""" NFL DB """
cur.execute("CREATE TABLE IF NOT EXISTS users(name PRIMARY KEY, plays, correct, currstreak, maxstreak)")
cur.execute("CREATE TABLE IF NOT EXISTS faceusers(name PRIMARY KEY, plays, correct, currstreak, maxstreak)")
cur.execute("CREATE TABLE IF NOT EXISTS mashusers(name PRIMARY KEY, plays, correct, currstreak, maxstreak)")

""" NBA DB """
cur.execute("CREATE TABLE IF NOT EXISTS hoopusers(name PRIMARY KEY, plays, correct, currstreak, maxstreak)")