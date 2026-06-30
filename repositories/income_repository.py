from db import get_db
from utils.scope import resolve_scope
import random


# =========================================================
# Basic CRUD
# =========================================================

def get_all_incomes(user_id, shared_id):
    db = get_db()

    condition, params = resolve_scope(user_id, shared_id)

    query = f"""
        SELECT *
        FROM incomes
        WHERE {condition}
        ORDER BY date DESC
    """

    return db.execute(query, params).fetchall()


def get_income_by_id(income_id, user_id, shared_id):
    db = get_db()

    condition, params = resolve_scope(user_id, shared_id)

    query = f"""
        SELECT *
        FROM incomes
        WHERE id=? AND {condition}
    """

    return db.execute(query, (income_id, *params)).fetchone()


def insert_income(user_id, shared_id,
                  amount, type_id, description, date, income_nature):

    db = get_db()

    db.execute("""
        INSERT INTO incomes
        (user_id, shared_account_id, created_by,
         amount, type_id, description, date, income_nature)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        shared_id,
        user_id,
        amount,
        type_id,
        description,
        date,
        income_nature
    ))

    db.commit()


def update_income(income_id, user_id, shared_id,
                  amount, description, date, type_id, income_nature):

    db = get_db()

    condition, params = resolve_scope(user_id, shared_id)

    query = f"""
        UPDATE incomes
        SET amount=?,
            description=?,
            date=?,
            type_id=?,
            income_nature=?
        WHERE id=? AND {condition}
    """

    db.execute(query, (
        amount,
        description,
        date,
        type_id,
        income_nature,
        income_id,
        *params
    ))

    db.commit()


def delete_income(income_id, user_id, shared_id):
    db = get_db()

    condition, params = resolve_scope(user_id, shared_id)

    query = f"""
        DELETE FROM incomes
        WHERE id=? AND {condition}
    """

    db.execute(query, (income_id, *params))
    db.commit()


# =========================================================
# Income Types (Categories)
# =========================================================

def get_income_types_for_user(user_id):
    db = get_db()

    return db.execute("""
        SELECT MIN(id) as id, name, MIN(color) as color
        FROM income_types
        WHERE created_by IS NULL
           OR created_by = ?
        GROUP BY name              
        ORDER BY name
    """, (user_id,)).fetchall()


def add_income_type(name, user_id):
    db = get_db()

    existing_colors = [
        row["color"]
        for row in db.execute(
            "SELECT color FROM income_types"
        ).fetchall()
    ]

    all_colors = [
        "#4CAF50", "#2196F3", "#9C27B0", "#FF9800", "#795548",
        "#00BCD4", "#8BC34A", "#E91E63", "#3F51B5", "#CDDC39"
    ]

    available_colors = [c for c in all_colors if c not in existing_colors]

    color = (
        random.choice(available_colors)
        if available_colors
        else random.choice(all_colors)
    )

    db.execute("""
        INSERT INTO income_types (name, color, created_by)
        VALUES (?, ?, ?)
    """, (name, color, user_id))

    db.commit()