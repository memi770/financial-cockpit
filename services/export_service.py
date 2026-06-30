import io
import csv
import pandas as pd
from flask import make_response

from db import get_db
from repositories.transaction_repository import get_transactions
from utils.scope import resolve_scope

from repositories.transaction_repository import get_transactions
from utils.scope import resolve_scope

def export_csv_service(request, user_id):

    db = get_db()
    cursor = db.cursor()

    # קבלת shared_id כמו בדשבורד
    row = db.execute(
        "SELECT shared_account_id FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()

    shared_id = row["shared_account_id"] if row else None

    transactions = get_transactions(user_id, shared_id)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "תאריך",
        "קטגוריה",
        "תיאור",
        "סכום",
        "הוזן על ידי",
        "סוג עסקה",
        "אופי"
    ])

    for t in transactions:
        writer.writerow([
            t["date"],
            t["category"],
            t["description"],
            t["amount"],
            t["created_by"],
            t["transaction_type"],
            t["nature"]
        ])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=transactions.csv"
    response.headers["Content-type"] = "text/csv; charset=utf-8"

    return response

def export_excel_service(request, user_id):

    db = get_db()

    row = db.execute(
        "SELECT shared_account_id FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()

    shared_id = row["shared_account_id"] if row else None

    transactions = get_transactions(user_id, shared_id)

    df = pd.DataFrame(transactions)

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:

        df.to_excel(writer, sheet_name='Transactions', index=False)

        workbook = writer.book
        worksheet = writer.sheets['Transactions']

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9EAD3',
            'border': 1,
            'align': 'center'
        })

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 20)

        money_format = workbook.add_format({
            'num_format': '#,##0.00 ₪',
            'align': 'center'
        })

        for row_num, row in enumerate(df.itertuples(index=False), start=1):
            worksheet.write(row_num, 0, row.date)
            worksheet.write(row_num, 1, row.category)
            worksheet.write(row_num, 2, row.description)
            worksheet.write(row_num, 3, row.amount, money_format)
            worksheet.write(row_num, 4, row.created_by)
            worksheet.write(row_num, 5, row.transaction_type)
            worksheet.write(row_num, 6, row.nature)

    output.seek(0)

    response = make_response(output.read())
    response.headers["Content-Disposition"] = "attachment; filename=transactions.xlsx"
    response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return response