import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fazenda-milho-secret-2024')
    DATABASE = os.path.join(os.path.dirname(__file__), 'fazenda_milho.db')
    DEBUG = True
