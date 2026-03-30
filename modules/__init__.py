from flask import Blueprint
from auth import auth_bp, login_required
from datetime import timedelta
# The calculadora_adubacao module contains the calculation engine (no routes needed)
# Routes are in adubacao.py
calc_bp = Blueprint('calculadora', __name__)
