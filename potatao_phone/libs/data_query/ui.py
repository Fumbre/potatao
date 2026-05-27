def get_view(db, parent_id):
    """
    Fetches all child UI items belonging to a specific parent menu ID.
    """
    db.row_type = "dict"

    
    return db.execute(
        "SELECT * FROM potatao_ui WHERE parent_id=? ORDER BY order_num ASC", 
        parent_id
    ).fetchall()