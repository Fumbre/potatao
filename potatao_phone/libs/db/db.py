def db_exist(db) -> bool:
    try:
        # check if our main table exists
        cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='potatao_ui'")
        row = cursor.fetchone()
        return row is not None
    except:
        return False
    
def db_create(db):
    # Create the table
    db.execute("""
        CREATE TABLE IF NOT EXISTS potatao_ui (
            id            INTEGER PRIMARY KEY,
            parent_id     INTEGER,
            name          TEXT,
            order_num     INTEGER,
            function_name TEXT
        );
    """)


    # Define default dataset
    default_items = [
        (1, 0, 'WiFi mess',  0, 'link'),
        (2, 0, 'NRF mess',   1, 'link'),
        (3, 0, 'SD Card',    2, 'get_sdcard_data'),
        (4, 0, 'Settings',   3, 'link'),
        (5, 0, 'Extra',      4, 'link'),
        (6, 4, 'Volume',     1, 'volume_state'),
        (7, 4, 'Nickname',   2, 'change_nickname'),
        (8, 4, 'Back',       3, 'pop_back'),
        (9, 2, 'receive  NRF',       0, 'receive_nrf'),
        (10, 2, 'send to NRF',       1, 'send_nrf'),
    ]

    # Dynamic SQL string construction for usqlite
    # We loop through items and format them properly into SQL-safe VALUE strings.
    insert_statements = ""
    for item in default_items:
        # item[2] (name) and item[4] (function_name) are strings, so they need single quotes ''
        insert_statements += f"INSERT INTO potatao_ui VALUES ({item[0]}, {item[1]}, '{item[2]}', {item[3]}, '{item[4]}');"

    # Wrap everything inside a single transaction string
    transaction_sql = f"BEGIN TRANSACTION;{insert_statements}COMMIT;"
    
    db.executemany(transaction_sql)

    print("Database ready!")


