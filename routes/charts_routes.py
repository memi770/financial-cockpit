#charts_routes.py

from flask import Blueprint, session, render_template, request, jsonify

from db import get_db
from utils.scope import get_account_scope

charts_bp = Blueprint("charts", __name__)

@charts_bp.route("/charts")
def charts():
    db = get_db()
    user_id = session["user_id"]
    shared_id = get_account_scope(db, user_id)
    users = []

    if shared_id:
        transactions = db.execute("""
            SELECT * FROM combined_transactions_view
            WHERE shared_account_id=?
        """, (shared_id,)).fetchall()
        
        users = db.execute("""
            SELECT user_id, username
            FROM users
            WHERE shared_account_id = ?
            ORDER BY username
        """, (shared_id,)).fetchall()
        print([dict(u) for u in users])
    else:
        transactions = db.execute("""
            SELECT * FROM combined_transactions_view
            WHERE user_id=?
        """, (user_id,)).fetchall()
    transactions = [dict(row) for row in transactions]    

    return render_template(
        "charts.html",
        transactions=transactions,
        shared_id=shared_id,
        users=users
    )

# ===============================
# Chart Data
# ===============================

@charts_bp.route('/get_chart_data')
def get_chart_data():

    db = get_db()
    user_id = session["user_id"]
    shared_id = get_account_scope(db, user_id)

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    transaction_type = request.args.get("type") 
    print("TYPE FROM FRONT:", transaction_type)    
    nature = request.args.get("nature")
    created_by = request.args.get("created_by")


    query = """
        SELECT category, amount, transaction_type, date
        FROM combined_transactions_view
        WHERE 1=1
    """
    params = []

    # scope
    if shared_id:
        query += " AND shared_account_id=?"
        params.append(shared_id)
    else:
        query += " AND user_id=?"
        params.append(user_id)

    # date filters
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    if transaction_type:
        query += " AND transaction_type=?"
        params.append(transaction_type)

    if nature:
        query += " AND nature=?"
        params.append(nature)  
        
    if created_by:
        query += " AND created_by=?"
        params.append(created_by)     

    # DEBUG DB VALUES
    debug_rows = db.execute(
        "SELECT DISTINCT transaction_type FROM combined_transactions_view"
    ).fetchall()

    print("DB VALUES:", [r["transaction_type"] for r in debug_rows])    

    rows = db.execute(query, params).fetchall()
    

    return jsonify([
        {
            "category": r["category"],
            "amount": r["amount"],
            "type": r["transaction_type"],
            "date": r["date"]
        }
        for r in rows
    ])


@charts_bp.route('/get_cashflow_data')
def get_cashflow_data():

    db = get_db()
    user_id = session["user_id"]
    shared_id = get_account_scope(db, user_id)

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    created_by = request.args.get("created_by")

    query = """
        SELECT amount, transaction_type, date
        FROM combined_transactions_view
        WHERE 1=1
    """

    params = []

    # scope
    if shared_id:
        query += " AND shared_account_id=?"
        params.append(shared_id)
    else:
        query += " AND user_id=?"
        params.append(user_id)

    # dates
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    # created by
    if created_by:
        query += " AND created_by=?"
        params.append(created_by)

    rows = db.execute(query, params).fetchall()

    return jsonify([
        {
            "amount": r["amount"],
            "type": r["transaction_type"],
            "date": r["date"]
        }
        for r in rows
    ])



