from flask import (
    Blueprint, request, session, redirect,
    jsonify, flash, render_template, url_for
)
from datetime import datetime
import random, sqlite3

from db import get_db
from utils.scope import get_account_scope
from repositories.expense_repository import (
    get_expense_by_scope,
    insert_expense,
    update_expense,
    delete_expense_by_scope,
    get_expense_types_for_user,
    add_expense_type,
    get_expense_chart_data,
    get_monthly_summary,
    get_expenses_by_period
)

expenses_bp = Blueprint("expenses", __name__, url_prefix="/expenses")


# ===============================
# Require Login
# ===============================

@expenses_bp.before_request
def require_login_for_expenses():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))





# ===============================
# Monthly Summary
# ===============================

@expenses_bp.route('/monthly_summary')
def monthly_summary():

    db = get_db()
    user_id = session["user_id"]
    shared_id = get_account_scope(db, user_id)

    rows = get_monthly_summary(user_id, shared_id)

    result = {}
    for r in rows:
        month = r["month"]
        category = r["category"] or "אחר"
        result.setdefault(month, {})[category] = r["total"]

    return jsonify(result)


# ===============================
# Add Expense
# ===============================

@expenses_bp.route('/add', methods=['POST'])
def add_expense():

    db = get_db()
    user_id = session["user_id"]
    shared_id = get_account_scope(db, user_id)

    amount = float(request.form["amount"])
    description = request.form.get("description", "")
    date = request.form["date"]
    type_id = request.form["category"]
    nature = request.form.get("nature", "משתנה")

    insert_expense(
        user_id,
        shared_id,
        amount,
        description,
        date,
        type_id,
        nature
    )

    flash("✅ ההוצאה נוספה בהצלחה", "success")
    return redirect(url_for("dashboard.index"))


# ===============================
# Edit Expense
# ===============================

@expenses_bp.route('/edit/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):

    db = get_db()
    user_id = session["user_id"]
    shared_id = get_account_scope(db, user_id)

    expense = get_expense_by_scope(expense_id, user_id, shared_id)

    if not expense:
        flash("❌ ההוצאה לא נמצאה", "danger")
        return redirect("/")

    if request.method == 'POST':

        update_expense(
            expense_id,
            user_id,
            shared_id,
            request.form["amount"],
            request.form.get("description", ""),
            request.form["date"],
            request.form["category"],
            request.form.get("nature", "משתנה")
        )

        flash("✅ ההוצאה עודכנה", "success")
        return redirect("/")

    types = get_expense_types_for_user(user_id)

    return render_template(
        "edit_expense.html",
        expense=expense,
        expense_types=types
    )


# ===============================
# Delete Expense
# ===============================

@expenses_bp.route('/delete/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):

    db = get_db()
    user_id = session["user_id"]
    shared_id = get_account_scope(db, user_id)

    delete_expense_by_scope(expense_id, user_id, shared_id)

    return redirect(_build_redirect_url())


def _build_redirect_url():

    year = request.args.get('year')
    month = request.args.get('month')

    if year and month:
        return f"/?year={year}&month={month}"

    return "/"


# ===============================
# Add Category
# ===============================

@expenses_bp.route('/add_type', methods=['POST'])
def add_type():

    user_id = session["user_id"]
    name = request.form["name"]

    # צבעים זמינים
    all_colors = [
        "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0",
        "#9966FF", "#FF9F40", "#00BFFF",
        "#8A2BE2", "#ADFF2F", "#FF69B4", "#FFD700"
    ]

    color = random.choice(all_colors)

    try:
        add_expense_type(name, color, user_id)
    except sqlite3.IntegrityError:
        pass

    return redirect(request.referrer or "/")


# ===============================
# API: Expenses by Month/Year
# ===============================

@expenses_bp.route('/api/expenses_by_month')
def expenses_by_month():

    db = get_db()
    user_id = session["user_id"]
    shared_id = get_account_scope(db, user_id)

    year = request.args.get("year")
    month = request.args.get("month")

    rows = get_expenses_by_period(
        user_id,
        shared_id,
        year,
        month
    )

    expenses = [dict(row) for row in rows]

    for e in expenses:
        date_obj = datetime.strptime(e["date"], "%Y-%m-%d")
        e["date_display"] = date_obj.strftime("%d/%m/%Y")
        e["date_iso"] = date_obj.strftime("%Y-%m-%d")

    return {"expenses": expenses}