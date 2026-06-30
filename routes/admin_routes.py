from flask import Blueprint, redirect, session, flash, render_template
from db import get_db
from datetime import datetime


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def _is_admin():
    return 'user_id' in session and session.get('is_admin')

def _get_admin_stats(cursor):

    cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin=1")
    admin_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT shared_account_id FROM users WHERE shared_account_id IS NOT NULL
            UNION
            SELECT user_id FROM users WHERE shared_account_id IS NULL
        )
    """)
    total_accounts = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(login_count) FROM users")
    total_logins = cursor.fetchone()[0] or 0

    return dict(
        admin_count=admin_count,
        total_accounts=total_accounts,
        total_logins=total_logins
    )


def _get_all_accounts(cursor):

    shared = cursor.execute("""
        SELECT 
            sa.id AS account_id,
            sa.name AS account_name,
            GROUP_CONCAT(u.username, '<br>') AS usernames,
            GROUP_CONCAT(u.email, '<br>') AS emails,
            GROUP_CONCAT(u.user_id, ',') AS members,
            SUM(u.login_count) AS total_logins,
            MAX(u.last_login) AS last_login,
            MIN(u.created_at) AS created_at,
            1 AS is_shared,
            MAX(u.is_admin) AS has_admin,
            COUNT(u.user_id) AS member_count
        FROM shared_accounts sa
        JOIN users u ON sa.id = u.shared_account_id
        GROUP BY sa.id
    """).fetchall()

    personal = cursor.execute("""
        SELECT 
            u.user_id AS account_id,
            u.username AS account_name,
            u.username AS usernames,
            u.email AS emails,
            CAST(u.user_id AS TEXT) AS members,
            u.login_count AS total_logins,
            u.last_login AS last_login,
            u.created_at AS created_at,
            0 AS is_shared,
            u.is_admin AS has_admin,
            1 AS member_count
        FROM users u
        WHERE u.shared_account_id IS NULL
    """).fetchall()

    return [dict(r) for r in shared] + [dict(r) for r in personal]

def _process_accounts(accounts):

    for acc in accounts:
        for field in ["created_at", "last_login"]:
            if acc.get(field):
                try:
                    dt = datetime.strptime(acc[field], "%Y-%m-%d %H:%M:%S")
                    acc[field] = dt.strftime("%d/%m/%Y %H:%M")
                except:
                    pass

    accounts.sort(
        key=lambda a: (
            -a["has_admin"],
            -a["is_shared"],
            a["account_name"].lower()
        )
    )

    return accounts


@admin_bp.route('/')
def admin_panel():

    if not _is_admin():
        return redirect('/')

    db = get_db()
    cursor = db.cursor()

    try:
        stats = _get_admin_stats(cursor)
        accounts = _get_all_accounts(cursor)
        accounts = _process_accounts(accounts)

    finally:
        db.close()

    return render_template(
        'admin.html',
        accounts=accounts,
        total_accounts=stats["total_accounts"],
        total_logins=stats["total_logins"],
        admin_count=stats["admin_count"]
    )


def _toggle_admin_logic(cursor, target_id, current_admin_id):

    row = cursor.execute(
        "SELECT is_admin FROM users WHERE user_id=?",
        (target_id,)
    ).fetchone()

    if not row:
        return dict(msg="⚠️ המשתמש לא נמצא.", category="warning")

    if target_id == current_admin_id:
        return dict(msg="🚫 לא ניתן לשנות את עצמך.", category="danger")

    is_admin = row['is_admin']

    if is_admin:
        count = cursor.execute(
            "SELECT COUNT(*) FROM users WHERE is_admin=1"
        ).fetchone()[0]

        if count <= 1:
            return dict(msg="🚫 מנהל אחרון.", category="danger")

        cursor.execute(
            "UPDATE users SET is_admin=0 WHERE user_id=?",
            (target_id,)
        )
        return dict(msg="⚙️ הוסר ניהול.", category="info")

    cursor.execute(
        "UPDATE users SET is_admin=1 WHERE user_id=?",
        (target_id,)
    )
    return dict(msg="✅ נוסף כמנהל.", category="success")


@admin_bp.route('/toggle_admin/<int:user_id>', methods=['POST'])
def toggle_admin(user_id):

    if not _is_admin():
        return redirect('/')

    db = get_db()
    cursor = db.cursor()

    try:
        result = _toggle_admin_logic(cursor, user_id, session['user_id'])
        db.commit()
        flash(result["msg"], result["category"])

    finally:
        db.close()

    return redirect('/admin')


def _delete_user_logic(cursor, target_id, current_admin_id):

    row = cursor.execute(
        "SELECT is_admin, shared_account_id FROM users WHERE user_id=?",
        (target_id,)
    ).fetchone()

    if not row:
        return dict(msg="⚠️ לא נמצא.", category="warning")

    if target_id == current_admin_id:
        return dict(msg="🚫 לא ניתן למחוק את עצמך.", category="danger")

    if row['is_admin']:
        count = cursor.execute(
            "SELECT COUNT(*) FROM users WHERE is_admin=1"
        ).fetchone()[0]

        if count <= 1:
            return dict(msg="🚫 מנהל אחרון.", category="danger")

    cursor.execute("DELETE FROM expenses WHERE user_id=?", (target_id,))
    cursor.execute("DELETE FROM users WHERE user_id=?", (target_id,))

    if row['shared_account_id']:
        remaining = cursor.execute(
            "SELECT COUNT(*) FROM users WHERE shared_account_id=?",
            (row['shared_account_id'],)
        ).fetchone()[0]

        if remaining == 0:
            cursor.execute(
                "DELETE FROM shared_accounts WHERE id=?",
                (row['shared_account_id'],)
            )

    return dict(msg="🗑️ המשתמש נמחק.", category="danger")


@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):

    if not _is_admin():
        return redirect('/')

    db = get_db()
    cursor = db.cursor()

    try:
        result = _delete_user_logic(
            cursor,
            user_id,
            session['user_id']
        )

        db.commit()
        flash(result["msg"], result["category"])

    finally:
        db.close()

    return redirect('/admin')
