import usqlite

def get_view(db, parent_id, sql_path: str = None):
    """
    Fetches all child UI items belonging to a specific parent menu ID.
    """
    if sql_path:
        db = usqlite.connect("/sd/potatao.db")
       

    db.row_type = "dict"

    result = db.execute(
        "SELECT id, parent_id,name, function_name, record_method FROM potatao_ui WHERE parent_id=? ORDER BY order_num ASC", 
        parent_id
    ).fetchall()

    db.close()

    return result
