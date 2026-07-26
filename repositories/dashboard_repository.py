from db import get_db
from utils.scope import resolve_scope


def get_transactions(user_id, shared_id, filters):
    db = get_db()
    condition, params = resolve_scope(user_id, shared_id,"combined_transactions_view")

    query = f"""
        SELECT
            combined_transactions_view.*,
            users.username AS created_by_name
        FROM combined_transactions_view
        LEFT JOIN users
            ON users.user_id = combined_transactions_view.created_by
        WHERE {condition}
    """

    # תאריכים
    if filters.get("start_date"):
        query += " AND date >= ?"
        params += (filters["start_date"],)

    if filters.get("end_date"):
        query += " AND date <= ?"
        params += (filters["end_date"],)

    # סוג תנועה
    if filters.get("transaction_type"):
        query += " AND transaction_type = ?"
        params += (filters["transaction_type"],)

    # מי יצר
    if filters.get("created_by"):
        query += " AND created_by = ?"
        params += (filters["created_by"],)
        
    # קבועה / משתנה
    if filters.get("nature"):
        query += " AND nature = ?"
        params += (filters["nature"],)    

    query += " ORDER BY date DESC"

    return db.execute(query, params).fetchall()


def get_totals(user_id, shared_id, filters):
    db = get_db()
    condition, params = resolve_scope(user_id, shared_id,"combined_transactions_view")

    query = f"""
        SELECT transaction_type,
               SUM(amount) as total,
               COUNT(*) as count
        FROM combined_transactions_view
        WHERE {condition}
    """

    if filters.get("start_date"):
        query += " AND date >= ?"
        params += (filters["start_date"],)

    if filters.get("end_date"):
        query += " AND date <= ?"
        params += (filters["end_date"],)
        
    if filters.get("nature"):
        query += " AND nature = ?"
        params += (filters["nature"],)    

    query += " GROUP BY transaction_type"

    rows = db.execute(query, params).fetchall()

    total_income = 0
    total_expense = 0
    income_count = 0
    expense_count = 0

    for row in rows:
        if row["transaction_type"] == "income":
            total_income = row["total"] or 0
            income_count = row["count"] or 0
        else:
            total_expense = row["total"] or 0
            expense_count = row["count"] or 0

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "income_count": income_count,
        "expense_count": expense_count,
        "balance": total_income - total_expense
    }


def get_monthly_cashflow(user_id, shared_id):
    db = get_db()
    condition, params = resolve_scope(user_id, shared_id,"combined_transactions_view")

    query = f"""
        SELECT substr(date,1,7) as month,
               transaction_type,
               SUM(amount) as total
        FROM combined_transactions_view
        WHERE {condition}
        GROUP BY month, transaction_type
        ORDER BY month
    """

    rows = db.execute(query, params).fetchall()

    data = {}
    for row in rows:
        month = row["month"]
        if month not in data:
            data[month] = {"month": month, "expenses": 0, "incomes": 0}

        if row["transaction_type"] == "income":
            data[month]["incomes"] = row["total"] or 0
        else:
            data[month]["expenses"] = row["total"] or 0

    return list(data.values())