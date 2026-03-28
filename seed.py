"""
Script para popular o banco com dados demonstrativos.
Execute: python seed.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from database import get_db

app = create_app()

def seed():
    with app.app_context():
        db = get_db(app)

        # Talhões
        talhoes = [
            ('Talhão A1', 45.5,  'Setor Norte',  'Latossolo Vermelho'),
            ('Talhão A2', 38.0,  'Setor Norte',  'Latossolo Vermelho'),
            ('Talhão B1', 52.3,  'Setor Sul',    'Latossolo Vermelho-Amarelo'),
            ('Talhão C1', 30.0,  'Setor Leste',  'Argissolo'),
        ]
        for nome, area, loc, solo in talhoes:
            db.execute("INSERT INTO talhoes (nome, area_ha, localizacao, tipo_solo) VALUES (?,?,?,?)",
                       (nome, area, loc, solo))

        # Análises de Solo
        analises = [
            (1, '2024-03-10', '2023/24', '0-20 cm', 5.2, 8.5, 0.18, 3.2, 0.9, 0.3, 5.8, 10.4, 42.3, 55, 2.8),
            (2, '2024-03-10', '2023/24', '0-20 cm', 5.8, 14.2, 0.28, 4.1, 1.2, 0.1, 4.2, 10.0, 55.0, 42, 3.1),
            (3, '2024-03-12', '2023/24', '0-20 cm', 4.9, 5.1, 0.12, 2.8, 0.8, 0.6, 7.2, 11.4, 32.5, 48, 2.3),
            (4, '2024-03-12', '2023/24', '0-20 cm', 6.1, 22.0, 0.35, 5.5, 1.8, 0.0, 3.5, 11.5, 63.5, 35, 3.8),
        ]
        for t_id, data, safra, prof, ph, p, k, ca, mg, al, hal, ctc, v, argila, mo in analises:
            db.execute("""
                INSERT INTO analises_solo
                (talhao_id,data_coleta,safra,profundidade,ph,fosforo,potassio,calcio,magnesio,aluminio,h_al,ctc,saturacao_bases,teor_argila,materia_organica)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (t_id, data, safra, prof, ph, p, k, ca, mg, al, hal, ctc, v, argila, mo))

        # Plantios
        plantios = [
            (1, '2023/24', '2023-10-15', 'DKB 390 PRO3', 65000, 45.5, 'colhido'),
            (2, '2023/24', '2023-10-17', 'P3862 H',      62000, 38.0, 'colhido'),
            (3, '2023/24', '2023-10-20', 'AG 8088 PRO3', 68000, 52.3, 'colhido'),
            (1, '2024/25', '2024-10-10', 'DKB 390 PRO3', 65000, 45.5, 'plantado'),
            (2, '2024/25', '2024-10-12', 'P3862 H',      62000, 38.0, 'vegetativo'),
        ]
        for t_id, safra, data, hibrido, pop, area, status in plantios:
            db.execute("""
                INSERT INTO plantios (talhao_id,safra,data_plantio,hibrido,populacao,area_plantada,status)
                VALUES (?,?,?,?,?,?,?)
            """, (t_id, safra, data, hibrido, pop, area, status))

        # Colheitas (plantios 1, 2, 3)
        colheitas = [
            (1, '2024-03-05', 227500, 14.0, 224900.0, 4944.0,  82.4, 68.0),
            (2, '2024-03-08', 175400, 13.5, 174218.0, 4584.7,  120.1, 68.0),
            (3, '2024-03-10', 293880, 15.2, 289200.0, 5530.4,  92.2, 68.0),
        ]
        for p_id, data, prod_tot, umid, prod_cor, kgha, scha, preco in colheitas:
            receita = prod_cor / 60 * preco
            db.execute("""
                INSERT INTO colheitas
                (plantio_id,data_colheita,producao_total,umidade_colheita,producao_corrigida,produtividade_kgha,produtividade_scha,preco_saca,receita_bruta)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (p_id, data, prod_tot, umid, prod_cor, kgha, scha, preco, round(receita,2)))

        # Recomendações
        db.execute("""
            INSERT INTO recomendacoes_adubacao
            (talhao_id,analise_solo_id,safra,meta_produtividade,n_recomendado,p2o5_recomendado,k2o_recomendado,necessidade_calcario,fertilizante_base,dose_base,fertilizante_cobertura,dose_cobertura,custo_estimado)
            VALUES (1,1,'2024/25',10,160,80,60,1.97,'04-14-08',571,'Ureia (45% N)',267,0)
        """)

        # Custos
        custos_data = [
            (1,'Sementes',     'DKB 390 PRO3 — 2 sacos',       1800, '2023-10-10'),
            (1,'Fertilizantes','04-14-08 — 2.600 kg',          3380, '2023-10-15'),
            (1,'Fertilizantes','Ureia cobertura — 1.210 kg',   1452, '2023-11-20'),
            (1,'Defensivos',   'Herbicida pré-emergente',        620, '2023-10-16'),
            (1,'Defensivos',   'Fungicida V8',                  1100, '2023-12-10'),
            (1,'Combustível',  'Diesel plantio + tratos',       1200, '2023-10-20'),
            (1,'Colheita',     'Colheita mecânica terceirizada',2275, '2024-03-05'),
            (2,'Sementes',     'P3862 H — 2 sacos',            1650, '2023-10-12'),
            (2,'Fertilizantes','04-14-08 — 2.200 kg',          2860, '2023-10-17'),
            (2,'Colheita',     'Colheita mecânica',             1900, '2024-03-08'),
            (3,'Sementes',     'AG 8088 PRO3 — 3 sacos',       2100, '2023-10-18'),
            (3,'Fertilizantes','04-14-08 — 3.000 kg',          3900, '2023-10-20'),
            (3,'Colheita',     'Colheita mecânica',             2615, '2024-03-10'),
        ]
        for p_id, cat, desc, val, data in custos_data:
            db.execute("INSERT INTO custos (plantio_id,categoria,descricao,valor,data_custo) VALUES (?,?,?,?,?)",
                       (p_id, cat, desc, val, data))

        # Estoque
        estoque = [
            ('04-14-08',              'Base',     2500,  1.30),
            ('Ureia (45% N)',         'Cobertura',800,   1.40),
            ('KCl (60% K₂O)',         'Base',     350,   1.80),
            ('Superfosfato Triplo',   'Base',     200,   2.10),
        ]
        for prod, tipo, qtd, preco in estoque:
            db.execute("INSERT INTO estoque_fertilizantes (produto,tipo,quantidade_kg,preco_kg) VALUES (?,?,?,?)",
                       (prod, tipo, qtd, preco))

        db.commit()
        print("✅  Dados de demonstração inseridos com sucesso!")
        print("   Talhões: 4 | Análises: 4 | Plantios: 5 | Colheitas: 3 | Recomendações: 1")

if __name__ == '__main__':
    seed()
