

from db import get_db
from utils.scope import resolve_scope


def get_transactions(user_id, shared_id):
    db = get_db()
    condition, params = resolve_scope(user_id, shared_id)

    query = f"""
        SELECT *
        FROM combined_transactions_view
        WHERE {condition}
        ORDER BY date DESC
    """

    return db.execute(query, params).fetchall()


def get_totals(user_id, shared_id):
    db = get_db()
    condition, params = resolve_scope(user_id, shared_id)

    query = f"""
        SELECT transaction_type, SUM(amount) as total
        FROM combined_transactions_view
        WHERE {condition}
        GROUP BY transaction_type
    """

    return db.execute(query, params).fetchall()