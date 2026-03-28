from flask import Flask
from config import Config
from database import init_db
from modules.talhoes import talhoes_bp
from modules.plantio import plantio_bp
from modules.adubacao import adubacao_bp
from modules.defensivos import defensivos_bp
from modules.custos import custos_bp
from modules.colheita import colheita_bp
from modules.dashboard import dashboard_bp
from modules.relatorios import relatorios_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    init_db(app)

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(talhoes_bp, url_prefix='/talhoes')
    app.register_blueprint(plantio_bp, url_prefix='/plantio')
    app.register_blueprint(adubacao_bp, url_prefix='/adubacao')
    app.register_blueprint(defensivos_bp, url_prefix='/defensivos')
    app.register_blueprint(custos_bp, url_prefix='/custos')
    app.register_blueprint(colheita_bp, url_prefix='/colheita')
    app.register_blueprint(relatorios_bp, url_prefix='/relatorios')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
