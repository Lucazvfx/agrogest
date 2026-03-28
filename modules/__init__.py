from flask import Blueprint
# The calculadora_adubacao module contains the calculation engine (no routes needed)
# Routes are in adubacao.py
calc_bp = Blueprint('calculadora', __name__)
