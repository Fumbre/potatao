import sqlite3

db = sqlite3.connect(":memory:")

# create table
db.execute("""CREATE TABLE IF NOT EXISTS potatao_ui (
    id INTEGER PRIMARY KEY, parent_id INTEGER,
    name TEXT, order_num INTEGER, function_name TEXT
);""")
db.commit()

# check table exists
row = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='potatao_ui'").fetchone()
assert row is not None

# insert some items
db.execute("INSERT INTO potatao_ui VALUES (1, 0, 'WiFi', 0, 'link')")
db.execute("INSERT INTO potatao_ui VALUES (2, 0, 'NRF', 1, 'link')")
db.execute("INSERT INTO potatao_ui VALUES (3, 0, 'SD Card', 2, 'link')")
db.execute("INSERT INTO potatao_ui VALUES (4, 4, 'Volume', 0, 'volume_state')")
db.commit()

# check rows inserted
count = db.execute("SELECT COUNT(*) FROM potatao_ui").fetchone()
assert count[0] == 4

# check function name
vol = db.execute("SELECT function_name FROM potatao_ui WHERE name='Volume'").fetchone()
assert vol[0] == 'volume_state'

db.close()
print("db tests passed!")

