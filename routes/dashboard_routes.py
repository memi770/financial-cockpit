from flask import Blueprint, render_template, session, redirect, request
from db import get_db
from utils.scope import get_account_scope
from services.dashboard_service import build_dashboard

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    user_id = session["user_id"]
    shared_id = get_account_scope(db, user_id)

    filters = {
        "transaction_type": request.args.get("transaction_type"),
        "start_date": request.args.get("start_date"),
        "end_date": request.args.get("end_date"),
        "created_by": request.args.get("created_by"),
    }

    data = build_dashboard(user_id, shared_id, filters)

    totals = data["totals"]
    balance = totals["balance"]

    if balance > 0:
        balance_color = "text-success"
        balance_icon = "bi-arrow-up-circle-fill"
    elif balance < 0:
        balance_color = "text-danger"
        balance_icon = "bi-arrow-down-circle-fill"
    else:
        balance_color = "text-secondary"
        balance_icon = "bi-dash-circle-fill"

    # Static data (לא עסקי)
    users = db.execute("SELECT user_id, username FROM users").fetchall()
    expense_types = db.execute("SELECT * FROM expense_types ORDER BY id").fetchall()
    income_types = db.execute("SELECT * FROM income_types ORDER BY name").fetchall()

    shared_users = []
    if shared_id:
        shared_users = db.execute(
            "SELECT user_id, username FROM users WHERE shared_account_id = ?",
            (shared_id,)
        ).fetchall()

    return render_template(
        "dashboard.html",
        transactions=data["transactions"],
        filters=filters,
        balance=balance,
        total_income=totals["total_income"],
        total_amount=totals["total_expense"],
        total_count=totals["expense_count"],
        income_count=totals["income_count"],
        balance_color=balance_color,
        balance_icon=balance_icon,
        expense_types=expense_types,
        income_types=income_types,
        users=users,
        shared_id=shared_id,
        shared_users=shared_users,
        cashflow=data["cashflow"],
    )