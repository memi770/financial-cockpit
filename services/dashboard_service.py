from repositories.dashboard_repository import (
    get_transactions,
    get_totals,
    get_monthly_cashflow
)


def build_dashboard(user_id, shared_id, filters):
    transactions = get_transactions(user_id, shared_id, filters)
    totals = get_totals(user_id, shared_id, filters)
    cashflow = get_monthly_cashflow(user_id, shared_id)

    return {
        "transactions": transactions,
        "totals": totals,
        "cashflow": cashflow
    }