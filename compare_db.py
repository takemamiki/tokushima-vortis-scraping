import sqlite3

conn = sqlite3.connect("data/vortis.db")
conn.row_factory = sqlite3.Row

for d in ["20261010", "20261017", "20261021"]:
    print("=====", d)
    for row in conn.execute("SELECT * FROM matches WHERE game_id LIKE ?", (d + "%",)):
        print(dict(row))
    for row in conn.execute("SELECT * FROM goals WHERE game_id LIKE ?", (d + "%",)):
        print(dict(row))

conn.close()