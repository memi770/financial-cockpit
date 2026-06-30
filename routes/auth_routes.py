from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from utils.scope import get_account_scope
from db import get_db

auth_bp = Blueprint("auth", __name__)

# ------------------- Login -------------------

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():

    if session.get('user_id'):
            return redirect('/dashboard')


    if request.method == 'POST':
        db = get_db()
        username = request.form['username']
        password = request.form['password']

        user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and check_password_hash(user['password'], password):
            # עדכונים
            db.execute("""
                UPDATE users
                SET last_login = datetime('now'),
                    login_count = COALESCE(login_count, 0) + 1
                WHERE user_id = ?
            """, (user['user_id'],))
            db.execute("""
                UPDATE expenses
                SET created_by = user_id
                WHERE created_by IS NULL AND user_id = ?
            """, (user['user_id'],))
            db.commit()

            # שמירת סשן
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            session['admin_view'] = bool(user['is_admin'])

            flash(f"ברוך הבא, {user['username']}!", "success")
            return redirect(
                url_for('admin.admin_panel')
                if session['admin_view']
                else url_for('dashboard.index')
            )

        flash("שם משתמש או סיסמה שגויים.", "danger")
        return redirect(url_for('auth.login'))

    return render_template('login.html')


# ------------------- Logout -------------------
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


# ------------------- Register -------------------

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        db = get_db()

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        is_shared = request.form.get('is_shared') == 'on'
        partner_username = request.form.get('partner_username')
        partner_password = request.form.get('partner_password')
        shared_name = request.form.get('shared_name')

        # --- password check ---
        if password != confirm_password:
            flash("❌ הסיסמאות אינן תואמות", "danger")
            return redirect(url_for('auth.register'))

        # --- unique user check ---
        exists = db.execute(
            "SELECT 1 FROM users WHERE username=? OR email=?",
            (username, email)
        ).fetchone()

        if exists:
            flash("⚠️ שם משתמש או אימייל כבר קיימים", "warning")
            return redirect(url_for('auth.register'))

        shared_account_id = None

        try:
            # ==========================
            # Shared account logic
            # ==========================
            if is_shared:

                if is_shared and not (partner_username and partner_password) and not shared_name:
                    flash("❌ צריך לבחור שותף או ליצור חשבון משותף חדש", "danger")
                    return redirect(url_for("auth.register"))


                # join via partner
                if partner_username and partner_password:
                    partner = db.execute(
                        "SELECT * FROM users WHERE username=?",
                        (partner_username,)
                    ).fetchone()

                    if not partner or not check_password_hash(partner['password'], partner_password):
                        flash("❌ אימות השותף נכשל", "danger")
                        return redirect(url_for('auth.register'))

                    if partner['shared_account_id']:
                        shared_account_id = partner['shared_account_id']
                    else:
                        auto_name = f"חשבון משותף של {partner_username} ו-{username}"
                        cursor = db.execute(
                            "INSERT INTO shared_accounts(name) VALUES (?)",
                            (auto_name,)
                        )
                        shared_account_id = cursor.lastrowid

                        db.execute(
                            "UPDATE users SET shared_account_id=? WHERE user_id=?",
                            (shared_account_id, partner['user_id'])
                        )

                # create new shared account
                elif shared_name:
                    exists_shared = db.execute(
                        "SELECT 1 FROM shared_accounts WHERE name=?",
                        (shared_name,)
                    ).fetchone()

                    if exists_shared:
                        flash("⚠️ שם החשבון המשותף כבר קיים", "warning")
                        return redirect(url_for('auth.register'))

                    cursor = db.execute(
                        "INSERT INTO shared_accounts(name) VALUES (?)",
                        (shared_name,)
                    )
                    shared_account_id = cursor.lastrowid

            # ==========================
            # create user
            # ==========================
            db.execute("""
                INSERT INTO users (username, email, password, is_admin, shared_account_id)
                VALUES (?, ?, ?, 0, ?)
            """, (
                username,
                email,
                generate_password_hash(password),
                shared_account_id
            ))

            db.commit()
            flash("✅ ההרשמה בוצעה בהצלחה! אפשר להתחבר", "success")
            return redirect(url_for('auth.login'))

        except Exception:
            db.rollback()
            raise

    return render_template('register.html')


# ----------- merge_options -------------

@auth_bp.route('/merge_options', methods=['GET', 'POST'])
def merge_options():
    # אם אין מידע על משתמש ממתין לאיחוד
    if 'pending_merge' not in session:
        return redirect(url_for('auth.profile'))

    db = get_db()
    partner_info = session['pending_merge']

    if request.method == 'POST':
        choice = request.form.get('choice')
        from_month = request.form.get('from_month')

        user_id = session['user_id']
        partner_id = partner_info['partner_id']

        # יצירת חשבון משותף חדש
        shared_name = f"חשבון משותף של {session['username']} ו-{partner_info['partner_username']}"
        cursor = db.execute(
            "INSERT INTO shared_accounts (name) VALUES (?)",
            (shared_name,)
        )
        shared_id = cursor.lastrowid

        # סינון לפי חודש (אם קיים)
        month_sql = ""
        params = []
        if from_month:
            month_sql = "AND substr(date, 1, 7) >= ?"
            params.append(from_month)

        # טיפול לפי בחירה
        if choice == "merge_both":
            db.execute(f"""
                UPDATE expenses
                SET shared_account_id=?
                WHERE user_id IN (?, ?) {month_sql}
            """, (shared_id, user_id, partner_id, *params))

        elif choice == "keep_current":
            db.execute(
                f"DELETE FROM expenses WHERE user_id=? {month_sql}",
                (partner_id, *params)
            )
            db.execute(f"""
                UPDATE expenses
                SET shared_account_id=?
                WHERE user_id=? {month_sql}
            """, (shared_id, user_id, *params))

        elif choice == "keep_partner":
            db.execute(
                f"DELETE FROM expenses WHERE user_id=? {month_sql}",
                (user_id, *params)
            )
            db.execute(f"""
                UPDATE expenses
                SET shared_account_id=?
                WHERE user_id=? {month_sql}
            """, (shared_id, partner_id, *params))

        elif choice == "new_empty":
            db.execute(
                f"DELETE FROM expenses WHERE user_id IN (?, ?) {month_sql}",
                (user_id, partner_id, *params)
            )

        # עדכון שני המשתמשים לחשבון המשותף
        db.execute(
            "UPDATE users SET shared_account_id=? WHERE user_id IN (?, ?)",
            (shared_id, user_id, partner_id)
        )

        db.commit()
        session.pop('pending_merge', None)

        flash("האיחוד בוצע בהצלחה ✅", "success")
        return redirect(url_for('auth.profile'))

    return render_template("merge_options.html", partner=partner_info)

# ------------- toggle_mode -----------
@auth_bp.route('/toggle_mode')
def toggle_mode():
    if not session.get("is_admin"):
        return redirect(url_for('dashboard.index'))

    session['admin_view'] = not session.get('admin_view', False)

    if session['admin_view']:
        return redirect(url_for('admin.admin_panel'))
    return redirect(url_for('dashboard.index'))

# ----------------- profile ---------------


def update_profile(db, user_id, form):
    username = form['username']
    email = form['email']
    new_password = form.get('new_password')

    existing = db.execute("""
        SELECT 1 FROM users
        WHERE (username=? OR email=?) AND user_id<>?
    """, (username, email, user_id)).fetchone()

    if existing:
        flash("שם המשתמש או האימייל כבר קיימים במערכת.", "danger")
        return False

    db.execute(
        "UPDATE users SET username=?, email=? WHERE user_id=?",
        (username, email, user_id)
    )

    if new_password:
        db.execute(
            "UPDATE users SET password=? WHERE user_id=?",
            (generate_password_hash(new_password), user_id)
        )

    session['username'] = username
    flash("✅ הפרופיל עודכן בהצלחה.", "success")
    return True


def add_new_partner(db, user_id, form):
    partner_username = form.get("partner_username")
    partner_email = form.get("partner_email")
    partner_password = form.get("partner_password")
    shared_name = form.get("shared_name")

    if not all([partner_username, partner_email, partner_password, shared_name]):
        flash("נא למלא את כל השדות", "warning")
        return False
    
    exists = db.execute(
        "SELECT 1 FROM users WHERE username=? OR email=?",
        (partner_username, partner_email)
    ).fetchone()

    if exists:
        flash("שם משתמש או אימייל כבר קיימים", "danger")
        return False


    cursor = db.execute("INSERT INTO shared_accounts(name) VALUES (?)", (shared_name,))
    shared_id = cursor.lastrowid

    db.execute("""
        INSERT INTO users (username, password, email, shared_account_id)
        VALUES (?, ?, ?, ?)
    """, (
        partner_username,
        generate_password_hash(partner_password),
        partner_email,
        shared_id
    ))

    db.execute(
        "UPDATE users SET shared_account_id=? WHERE user_id=?",
        (shared_id, user_id)
    )

    flash("נוצר חשבון משותף חדש", "success")
    return True
 

def leave_shared(db, user_id):
    db.execute(
        "UPDATE users SET shared_account_id=NULL WHERE user_id=?",
        (user_id,)
    )
    flash("נותקת מהחשבון המשותף", "info")
    return True


@auth_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()
    user_id = session["user_id"]

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_profile":
            update_profile(db, user_id, request.form)

        elif action == "add_new_partner":
            add_new_partner(db, user_id, request.form)

        elif action == "leave_shared":
            leave_shared(db, user_id)

        db.commit()

    user = db.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()

    if not user:
        session.clear()
        flash("הסשן לא תקף. נא להתחבר מחדש.", "warning")
        return redirect(url_for("auth.login"))

    shared_id = get_account_scope(db, user_id)

    partners = []
    shared_name = None
    if shared_id:
        shared_name = db.execute(
            "SELECT name FROM shared_accounts WHERE id=?",
            (shared_id,)
        ).fetchone()["name"]

        partners = db.execute("""
            SELECT username FROM users
            WHERE shared_account_id=? AND user_id<>?
        """, (shared_id, user_id)).fetchall()

    return render_template(
        "profile.html",
        user=dict(user),
        shared_name=shared_name,
        partners=partners
    )




