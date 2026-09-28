from flask import Flask, jsonify
from auth import require_admin
from utils.csv_tools import to_csv
from db import all_users

app = Flask(__name__)


@app.get("/admin/export")
@require_admin
def export_users():
    return to_csv(all_users()), 200, {"Content-Type": "text/csv"}
