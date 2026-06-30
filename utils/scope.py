

def resolve_scope(user_id, shared_id, table_alias=None):
    """
    מחזיר תנאי WHERE ופרמטרים לפי scope.
    תומך גם ב-alias (למשל e.user_id)
    """

    prefix = f"{table_alias}." if table_alias else ""

    if shared_id:
        return f"{prefix}shared_account_id = ?", (shared_id,)
    else:
        return f"{prefix}user_id = ?", (user_id,)

def get_account_scope(db, user_id):
    row = db.execute(
        "SELECT shared_account_id FROM users WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    return row["shared_account_id"] if row and row["shared_account_id"] else None


