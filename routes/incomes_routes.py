from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3

from db import get_db
from utils.scope import get_account_scope
from repositories.income_repository import (
    get_all_incomes,
    get_income_by_id,
    insert_income,
    update_income,
    delete_income as delete_income_repo,
    get_income_types_for_user,
    add_income_type
)

incomes_bp = Blueprint("incomes", __name__, url_prefix="/incomes")


@incomes_bp.before_request
def require_login():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

# ----------- Add ------------

@incomes_bp.route("/add", methods=["POST"])
def add_income():
    db = get_db()
    shared_id = get_account_scope(db, session["user_id"])

    insert_income(
        user_id=session["user_id"],
        shared_id=shared_id,
        amount=request.form["amount"],
        type_id=request.form.get("type_id"),
        description=request.form.get("description", ""),
        date=request.form["date"],
        income_nature=request.form.get("income_nature", "משתנה")
    )

    flash("הכנסה נוספה בהצלחה", "success")
    return redirect(url_for("dashboard.index"))


# ----------- Edit ------------

@incomes_bp.route("/edit/<int:income_id>", methods=["GET", "POST"])
def edit_income(income_id):

    db = get_db()
    user_id=session["user_id"]
    shared_id = get_account_scope(db, user_id)

    income = get_income_by_id(income_id, user_id, shared_id)

    if not income:
        flash("❌ ההכנסה לא נמצאה", "danger")
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":

        update_income(
            income_id=income_id,
            user_id=user_id,
            shared_id=shared_id,
            amount=request.form["amount"],
            description=request.form.get("description", ""),
            date=request.form["date"],
            type_id=request.form.get("type_id"),
            income_nature=request.form.get("income_nature", "משתנה")
        )

        flash("✅ ההכנסה עודכנה", "success")
        return redirect(url_for("dashboard.index"))

    types = get_income_types_for_user(session["user_id"])

    return render_template(
        "edit_income.html",
        income=income,
        income_types=types
    )


# ----------- Delete ------------

@incomes_bp.route("/delete/<int:income_id>", methods=["POST"])
def delete_income(income_id):
    db = get_db()
    shared_id = get_account_scope(db, session["user_id"])

    delete_income_repo(income_id, session["user_id"], shared_id)

    flash("הכנסה נמחקה", "info")
    return redirect(url_for("dashboard.index"))


# ----------- Add Type ------------

@incomes_bp.route("/add_type", methods=["POST"])
def add_type():

    try:
        add_income_type(request.form["name"])
    except sqlite3.IntegrityError:
        pass

    return redirect(request.referrer or url_for("dashboard.index"))


