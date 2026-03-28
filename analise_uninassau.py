"""
Script para importar análise de solo do PDF "Analise de Solo - Área Experimental - Uninassau.pdf"
e gerar recomendações de adubação.

Execute: python importar_analise_uninassau.py
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from database import get_db

# Dados extraídos do laudo (PDF)
DADOS_ANALISE = {
    "talhao_nome": "25140",                     # Identificador do talhão no laudo
    "data_coleta": "2025-12-12",                # Data de entrega do laudo (última data)
    "safra": "2025/26",                         # Safra de referência
    "profundidade": "0-20 cm",                  # Profundidade padrão
    "ph": 6.2,
    "fosforo": 1.0,                             # mg/dm³ (P Mehlich)
    "potassio": 27.7,                           # mg/dm³ (K Mehlich)
    "calcio": 1.7,                              # cmolc/dm³
    "magnesio": 0.5,                            # cmolc/dm³
    "aluminio": 0.0,                            # cmolc/dm³
    "h_al": 4.1,                                # cmolc/dm³ (H+Al)
    "ctc": 6.4,                                 # cmolc/dm³ (CTC pH 7,0)
    "saturacao_bases": 35,                      # % V
    "teor_argila": 61,                          # % (convertido de 610 g/kg)
    "materia_organica": 18,                     # g/dm³
    # Outros valores (não obrigatórios)
    "zinco": 2.1,
    "cobre": 1.4,
    "ferro": 40,
    "manganes": 4.2,
    "boro": 0.17,
    "enxofre": 13.1,
}

# Meta de produtividade para a recomendação (exemplo: 10 t/ha)
META_PRODUTIVIDADE = 10  # toneladas por hectare


def criar_talhao_se_nao_existe(db, nome):
    """Verifica se o talhão existe; se não, cria um com dados padrão."""
    row = db.execute("SELECT id FROM talhoes WHERE nome = ?", (nome,)).fetchone()
    if row:
        talhao_id = row[0]
        print(f"Talhão '{nome}' já existe (ID {talhao_id}).")
        return talhao_id
    else:
        # Dados padrão (ajuste conforme necessário)
        area = 0.0
        localizacao = "Área Experimental Uninassau"
        tipo_solo = "Latossolo Vermelho-Amarelo"
        db.execute(
            "INSERT INTO talhoes (nome, area_ha, localizacao, tipo_solo) VALUES (?,?,?,?)",
            (nome, area, localizacao, tipo_solo)
        )
        talhao_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        print(f"Talhão '{nome}' criado com ID {talhao_id}.")
        return talhao_id


def inserir_analise(db, talhao_id, dados):
    """Insere os dados da análise de solo na tabela analises_solo."""
    sql = """
        INSERT INTO analises_solo
        (talhao_id, data_coleta, safra, profundidade, ph, fosforo, potassio,
         calcio, magnesio, aluminio, h_al, ctc, saturacao_bases, teor_argila,
         materia_organica)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    db.execute(sql, (
        talhao_id,
        dados["data_coleta"],
        dados["safra"],
        dados["profundidade"],
        dados["ph"],
        dados["fosforo"],
        dados["potassio"],
        dados["calcio"],
        dados["magnesio"],
        dados["aluminio"],
        dados["h_al"],
        dados["ctc"],
        dados["saturacao_bases"],
        dados["teor_argila"],
        dados["materia_organica"]
    ))
    analise_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    print(f"Análise de solo inserida com ID {analise_id}.")
    return analise_id


def recomendar_adubacao(dados, meta_produtividade):
    """
    Gera recomendações de adubação e calagem com base nos parâmetros do solo.
    Retorna um dicionário com as recomendações.
    """
    # 1. Necessidade de calagem (método saturação por bases)
    v_atual = dados["saturacao_bases"]           # %
    v_desejada = 70 if dados["teor_argila"] > 20 else 60  # recomendação comum
    if v_atual < v_desejada:
        # PRNT = 100% (calcário padrão)
        nc = (v_desejada - v_atual) * dados["ctc"] / 100
        necessidade_calcario = round(nc, 2)  # t/ha
    else:
        necessidade_calcario = 0.0

    # 2. Fósforo (P2O5) - baseado no teor de P e na meta produtividade
    p_atual = dados["fosforo"]  # mg/dm³
    # Tabela simplificada: se P < 10 -> aplicar 120 kg/ha P2O5; se P < 20 -> 80; senão 40
    if p_atual < 10:
        p2o5_recomendado = 120
    elif p_atual < 20:
        p2o5_recomendado = 80
    else:
        p2o5_recomendado = 40

    # 3. Potássio (K2O) - baseado no teor de K e na CTC
    k_atual = dados["potassio"]  # mg/dm³
    # Converter K mg/dm³ para cmolc/dm³ (1 cmolc = 391 mg)
    k_cmol = k_atual / 391
    # Tabela simplificada
    if k_cmol < 0.15:
        k2o_recomendado = 120
    elif k_cmol < 0.25:
        k2o_recomendado = 80
    else:
        k2o_recomendado = 40

    # 4. Nitrogênio (N) - baseado na matéria orgânica e meta produtividade
    # N recomendado (kg/ha) = (meta em t/ha) * 20 - (MO_g_dm3 * 2)  (fórmula empírica)
    n_recomendado = max(0, int(meta_produtividade * 20 - dados["materia_organica"] * 2))

    # 5. Escolha de fertilizantes (exemplo)
    fertilizante_base = "04-14-08"
    # Para atender P2O5 e K2O com 04-14-08:
    # 100 kg de 04-14-08 fornecem 14 kg P2O5 e 8 kg K2O
    dose_base = max(p2o5_recomendado, k2o_recomendado) * 100 / 14  # ajustado pelo P2O5
    dose_base = int(round(dose_base / 50) * 50)  # arredonda para múltiplo de 50

    # Cobertura: ureia (45% N)
    dose_cobertura = int(n_recomendado * 100 / 45)

    return {
        "n_recomendado": n_recomendado,
        "p2o5_recomendado": p2o5_recomendado,
        "k2o_recomendado": k2o_recomendado,
        "necessidade_calcario": necessidade_calcario,
        "fertilizante_base": fertilizante_base,
        "dose_base": dose_base,
        "fertilizante_cobertura": "Ureia (45% N)",
        "dose_cobertura": dose_cobertura,
        "custo_estimado": 0  # pode ser calculado posteriormente
    }


def inserir_recomendacao(db, talhao_id, analise_id, recomendacao):
    """Insere a recomendação na tabela recomendacoes_adubacao."""
    sql = """
        INSERT INTO recomendacoes_adubacao
        (talhao_id, analise_solo_id, safra, meta_produtividade,
         n_recomendado, p2o5_recomendado, k2o_recomendado,
         necessidade_calcario, fertilizante_base, dose_base,
         fertilizante_cobertura, dose_cobertura, custo_estimado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    db.execute(sql, (
        talhao_id,
        analise_id,
        DADOS_ANALISE["safra"],
        META_PRODUTIVIDADE,
        recomendacao["n_recomendado"],
        recomendacao["p2o5_recomendado"],
        recomendacao["k2o_recomendado"],
        recomendacao["necessidade_calcario"],
        recomendacao["fertilizante_base"],
        recomendacao["dose_base"],
        recomendacao["fertilizante_cobertura"],
        recomendacao["dose_cobertura"],
        recomendacao["custo_estimado"]
    ))
    rec_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    print(f"Recomendação de adubação inserida com ID {rec_id}.")
    return rec_id


def main():
    app = create_app()
    with app.app_context():
        db = get_db(app)

        # 1. Criar ou obter talhão
        talhao_id = criar_talhao_se_nao_existe(db, DADOS_ANALISE["talhao_nome"])

        # 2. Inserir análise de solo
        analise_id = inserir_analise(db, talhao_id, DADOS_ANALISE)

        # 3. Gerar recomendação
        recomendacao = recomendar_adubacao(DADOS_ANALISE, META_PRODUTIVIDADE)

        # 4. Inserir recomendação no banco
        inserir_recomendacao(db, talhao_id, analise_id, recomendacao)

        # 5. Commit e relatório final
        db.commit()

        print("\n" + "=" * 60)
        print("RESUMO DA ANÁLISE E RECOMENDAÇÃO")
        print("=" * 60)
        print(f"Talhão: {DADOS_ANALISE['talhao_nome']}")
        print(f"Data da coleta: {DADOS_ANALISE['data_coleta']}")
        print(f"pH: {DADOS_ANALISE['ph']}")
        print(f"P (mg/dm³): {DADOS_ANALISE['fosforo']}")
        print(f"K (mg/dm³): {DADOS_ANALISE['potassio']}")
        print(f"Matéria Orgânica (g/dm³): {DADOS_ANALISE['materia_organica']}")
        print(f"CTC (cmolc/dm³): {DADOS_ANALISE['ctc']}")
        print(f"V%: {DADOS_ANALISE['saturacao_bases']}%")
        print(f"Argila: {DADOS_ANALISE['teor_argila']}%")
        print("\nRecomendações:")
        print(f"  - Calcário: {recomendacao['necessidade_calcario']:.2f} t/ha")
        print(f"  - N (kg/ha): {recomendacao['n_recomendado']}")
        print(f"  - P₂O₅ (kg/ha): {recomendacao['p2o5_recomendado']}")
        print(f"  - K₂O (kg/ha): {recomendacao['k2o_recomendado']}")
        print(f"  - Fertilizante base: {recomendacao['dose_base']} kg/ha de {recomendacao['fertilizante_base']}")
        print(f"  - Cobertura: {recomendacao['dose_cobertura']} kg/ha de {recomendacao['fertilizante_cobertura']}")
        print("=" * 60)
        print("✅ Dados importados e recomendações geradas com sucesso!")


if __name__ == "__main__":
    main()