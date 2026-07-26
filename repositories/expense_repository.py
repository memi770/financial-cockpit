from db import get_db
from utils.scope import resolve_scope

# =========================================================
# Basic CRUD
# =========================================================

def get_expense_by_scope(expense_id, user_id, shared_id):
    db = get_db()

    condition, params = resolve_scope(user_id, shared_id)

    query = f"""
        SELECT *,
            expense_nature AS nature
        FROM expenses
        WHERE id=? AND {condition}
    """

    return db.execute(query, (expense_id, *params)).fetchone()

def insert_expense(user_id, shared_id, amount,
                   description, date, type_id, nature):

    db = get_db()

    db.execute("""
        INSERT INTO expenses
        (user_id, shared_account_id, created_by,
         amount, description, date, type_id, expense_nature)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        shared_id,
        user_id,
        amount,
        description,
        date,
        type_id,
        nature
    ))

    db.commit()


def update_expense(expense_id, user_id, shared_id,
                   amount, description, date, type_id, nature):

    db = get_db()

    condition, params = resolve_scope(user_id, shared_id)

    query = f"""
        UPDATE expenses
        SET amount=?,
            description=?,
            date=?,
            type_id=?,
            expense_nature=?
        WHERE id=? AND {condition}
    """

    db.execute(query, (
        amount,
        description,
        date,
        type_id,
        nature,
        expense_id,
        *params
    ))

    db.commit()

def delete_expense_by_scope(expense_id, user_id, shared_id):
    db = get_db()

    condition, params = resolve_scope(user_id, shared_id)

    query = f"""
        DELETE FROM expenses
        WHERE id=? AND {condition}
    """

    db.execute(query, (expense_id, *params))
    db.commit()


# =========================================================
# Categories
# =========================================================

def get_expense_types_for_user(user_id):
    db = get_db()

    return db.execute("""
        SELECT MIN(id) as id, name, MIN(color) as color
        FROM expense_types
        WHERE created_by IS NULL
           OR created_by = ?
        GROUP BY name              
        ORDER BY name
    """, (user_id,)).fetchall()


def add_expense_type(name, color, user_id):
    db = get_db()

    db.execute("""
        INSERT INTO expense_types (name, color, created_by)
        VALUES (?, ?, ?)
    """, (name, color, user_id))

    db.commit()


# =========================================================
# Reporting / Charts
# =========================================================

def get_expense_chart_data(user_id, shared_id,
                           start_date=None,
                           end_date=None,
                           category=None,
                           created_by=None,
                           nature=None):

    db = get_db()

    query = """
        SELECT e.amount, t.name AS category
        FROM expenses e
        WHERE 1=1
    """
    params = []

    # scope
    if shared_id:
        query += " AND e.shared_account_id=?"
        params.append(shared_id)
    else:
        query += " AND e.user_id=?"
        params.append(user_id)

    # filters
    if start_date:
        query += " AND e.date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND e.date <= ?"
        params.append(end_date)

    if category:
        query += " AND e.type_id=?"
        params.append(category)

    if created_by:
        query += " AND e.created_by=?"
        params.append(created_by)

    if nature:
        query += " AND e.expense_nature=?"
        params.append(nature)

    return db.execute(query, params).fetchall()


def get_monthly_summary(user_id, shared_id):
    db = get_db()

    query = """
        SELECT strftime('%Y-%m', e.date) AS month,
               t.name AS category,
               SUM(e.amount) AS total
        FROM expenses e
        WHERE 1=1
    """
    params = []

    if shared_id:
        query += " AND e.shared_account_id=?"
        params.append(shared_id)
    else:
        query += " AND e.user_id=?"
        params.append(user_id)

    query += " GROUP BY strftime('%Y-%m', e.date), t.name"

    return db.execute(query, params).fetchall()


def get_expenses_by_period(user_id, shared_id, year=None, month=None):
    db = get_db()

    query = """
        SELECT e.date,
               t.name AS category,
               e.amount
        FROM expenses e
        WHERE 1=1
    """
    params = []

    # scope
    if shared_id:
        query += " AND e.shared_account_id=?"
        params.append(shared_id)
    else:
        query += " AND e.user_id=?"
        params.append(user_id)

    # date filters
    if year and month:
        query += """
            AND strftime('%Y', e.date) = ?
            AND strftime('%m', e.date) = ?
        """
        params.extend([year, month])

    elif year:
        query += " AND strftime('%Y', e.date) = ?"
        params.append(year)

    elif month:
        query += " AND strftime('%m', e.date) = ?"
        params.append(month)

    query += " ORDER BY e.date"

    return db.execute(query, params).fetchall()