from flask import Blueprint, session, redirect, request
from services.export_service import (
    export_csv_service,
    export_excel_service
)

export_bp = Blueprint('export', __name__)


@export_bp.route('/export_csv')
def export_csv():
    if 'user_id' not in session:
        return redirect('/login')

    return export_csv_service(request, session['user_id'])


@export_bp.route('/export_excel')
def export_excel():
    if 'user_id' not in session:
        return redirect('/login')

    return export_excel_service(request, session['user_id'])