from repositories.transaction_repository import get_transactions, get_totals


def fetch_dashboard_data(user_id, shared_id):
    transactions = get_transactions(user_id, shared_id)
    totals_rows = get_totals(user_id, shared_id)

    total_income = 0
    total_expense = 0

    for row in totals_rows:
        if row["transaction_type"] == "income":
            total_income = row["total"] or 0
        else:
            total_expense = row["total"] or 0

    return {
        "transactions": transactions,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense
    }