import sqlite3
from flask import g

def get_db(app=None):
    from flask import current_app
    if app:
        db = sqlite3.connect(app.config['DATABASE'], detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = sqlite3.Row
        return db
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app):
    with app.app_context():
        db = get_db(app)
        db.executescript(SCHEMA)
        db.commit()
    app.teardown_appcontext(close_db)

SCHEMA = """
CREATE TABLE IF NOT EXISTS talhoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    area_ha REAL NOT NULL,
    localizacao TEXT,
    tipo_solo TEXT,
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analises_solo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    talhao_id INTEGER NOT NULL,
    data_coleta DATE NOT NULL,
    safra TEXT,
    profundidade TEXT DEFAULT '0-20 cm',
    ph REAL,
    fosforo REAL,
    potassio REAL,
    calcio REAL,
    magnesio REAL,
    aluminio REAL,
    h_al REAL,
    ctc REAL,
    saturacao_bases REAL,
    teor_argila REAL,
    materia_organica REAL,
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (talhao_id) REFERENCES talhoes(id)
);

CREATE TABLE IF NOT EXISTS recomendacoes_adubacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    talhao_id INTEGER NOT NULL,
    analise_solo_id INTEGER,
    safra TEXT NOT NULL,
    meta_produtividade REAL,
    n_recomendado REAL,
    p2o5_recomendado REAL,
    k2o_recomendado REAL,
    necessidade_calcario REAL,
    fertilizante_base TEXT,
    dose_base REAL,
    fertilizante_cobertura TEXT,
    dose_cobertura REAL,
    custo_estimado REAL,
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (talhao_id) REFERENCES talhoes(id),
    FOREIGN KEY (analise_solo_id) REFERENCES analises_solo(id)
);

CREATE TABLE IF NOT EXISTS plantios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    talhao_id INTEGER NOT NULL,
    safra TEXT NOT NULL,
    data_plantio DATE,
    hibrido TEXT,
    populacao INTEGER,
    area_plantada REAL,
    status TEXT DEFAULT 'planejado',
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (talhao_id) REFERENCES talhoes(id)
);

CREATE TABLE IF NOT EXISTS aplicacoes_adubacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plantio_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    data_aplicacao DATE,
    fertilizante TEXT NOT NULL,
    dose_kgha REAL NOT NULL,
    area_ha REAL NOT NULL,
    custo_kg REAL,
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plantio_id) REFERENCES plantios(id)
);

CREATE TABLE IF NOT EXISTS aplicacoes_defensivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plantio_id INTEGER NOT NULL,
    data_aplicacao DATE,
    produto TEXT NOT NULL,
    tipo TEXT,
    dose_lha REAL,
    area_ha REAL,
    custo_litro REAL,
    estagio_cultura TEXT,
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plantio_id) REFERENCES plantios(id)
);

CREATE TABLE IF NOT EXISTS custos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plantio_id INTEGER NOT NULL,
    categoria TEXT NOT NULL,
    descricao TEXT NOT NULL,
    valor REAL NOT NULL,
    data_custo DATE,
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plantio_id) REFERENCES plantios(id)
);

CREATE TABLE IF NOT EXISTS colheitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plantio_id INTEGER NOT NULL,
    data_colheita DATE,
    producao_total REAL,
    umidade_colheita REAL,
    producao_corrigida REAL,
    produtividade_kgha REAL,
    produtividade_scha REAL,
    preco_saca REAL,
    receita_bruta REAL,
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plantio_id) REFERENCES plantios(id)
);

CREATE TABLE IF NOT EXISTS estoque_fertilizantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto TEXT NOT NULL,
    tipo TEXT,
    quantidade_kg REAL DEFAULT 0,
    preco_kg REAL,
    fornecedor TEXT,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""