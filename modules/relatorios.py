"""
Motor de Cálculo de Adubação para Milho
Baseado no Manual de Adubação e Calagem para o Cerrado — Embrapa
Capítulos 6 (P), 7 (K), 12 (Milho) — tabelas oficiais.
"""

# ══════════════════════════════════════════════════════════════════
#  TABELA 3 – INTERPRETAÇÃO DE FÓSFORO (Mehlich-1) – SEQUEIRO
#  Cap. 6, p. 154  |  limites superiores de cada classe (mg/dm³)
# ══════════════════════════════════════════════════════════════════
P_INTERP_SEQUEIRO = {
    15: (6.0,  12.0, 18.0, 25.0),
    35: (5.0,  10.0, 15.0, 20.0),
    60: (3.0,   5.0,  8.0, 12.0),
    999: (2.0,   3.0,  4.0,  6.0),
}

# TABELA 4 – IRRIGADO
P_INTERP_IRRIGADO = {
    15: (12.0, 18.0, 25.0, 40.0),
    35: (10.0, 15.0, 20.0, 35.0),
    60: (5.0,   8.0, 12.0, 18.0),
    999: (3.0,   4.0,  6.0,  9.0),
}

# TABELA 8 – CORRETIVA P₂O₅ (kg/ha)  |  Cap. 6, p. 158
P_CORRETIVA_SEQUEIRO = {
    15: (60,  30,  15),
    35: (100,  50,  25),
    60: (200, 100,  50),
    999: (280, 140,  70),
}
P_CORRETIVA_IRRIGADO = {
    15: (90,  45,  20),
    35: (150,  75,  38),
    60: (300, 150,  75),
    999: (420, 210, 105),
}

# TABELA 11 – MANUTENÇÃO P₂O₅ (kg/ha)  |  Cap. 6, p. 161
P_MANUTENCAO_SEQUEIRO = {'Adequado': (60, 100), 'Alto': (30, 50)}
P_MANUTENCAO_IRRIGADO = {'Adequado': (80, 120), 'Alto': (40, 60)}

# TABELA 5 – POTÁSSIO  |  Cap. 7, p. 181
K_INTERP_CTC_BAIXA = {
    15: ('Baixo',    50,  70),
    30: ('Médio',    25,  60),
    40: ('Adequado',  0,   0),
    9999: ('Alto',      0,   0),
}
K_INTERP_CTC_ALTA = {
    25: ('Baixo',   100,  80),
    50: ('Médio',    50,  60),
    80: ('Adequado',  0,   0),
    9999: ('Alto',      0,   0),
}

# NITROGÊNIO – Cap. 12 (Milho)
N_FAIXAS = [
    (6,  40,  80),
    (8,  40,  80),
    (10,  80, 120),
    (999, 120, 160),
]
N_BASE_KGHA = 20

# FERTILIZANTES COMERCIAIS
FERTILIZANTES_DISPONIVEIS = {
    '04-14-08': {'n': 0.04, 'p': 0.14, 'k': 0.08},
    '08-28-16': {'n': 0.08, 'p': 0.28, 'k': 0.16},
    '05-25-15': {'n': 0.05, 'p': 0.25, 'k': 0.15},
    '10-10-10': {'n': 0.10, 'p': 0.10, 'k': 0.10},
    '02-20-20': {'n': 0.02, 'p': 0.20, 'k': 0.20},
    '04-20-20': {'n': 0.04, 'p': 0.20, 'k': 0.20},
    '06-30-06': {'n': 0.06, 'p': 0.30, 'k': 0.06},
    '00-18-18': {'n': 0.00, 'p': 0.18, 'k': 0.18},
    'Superfosfato Simples (18% P2O5)': {'n': 0.00, 'p': 0.18, 'k': 0.00},
    'Superfosfato Triplo (46% P2O5)': {'n': 0.00, 'p': 0.46, 'k': 0.00},
    'KCl (60% K2O)': {'n': 0.00, 'p': 0.00, 'k': 0.60},
    'Ureia (45% N)': {'n': 0.45, 'p': 0.00, 'k': 0.00},
    'Sulfato de Amonio (20% N)': {'n': 0.20, 'p': 0.00, 'k': 0.00},
    'Nitrato de Amonio (32% N)': {'n': 0.32, 'p': 0.00, 'k': 0.00},
    'MAP (12-52-00)': {'n': 0.12, 'p': 0.52, 'k': 0.00},
    'DAP (18-46-00)': {'n': 0.18, 'p': 0.46, 'k': 0.00},
    'NitroMais (30% N)': {'n': 0.30, 'p': 0.00, 'k': 0.00},
}

COBERTURA_OPCOES = {
    'Ureia (45% N)': {'n': 0.45, 'p': 0.00, 'k': 0.00},
    'Sulfato de Amonio (20% N)': {'n': 0.20, 'p': 0.00, 'k': 0.00},
    'Nitrato de Amonio (32% N)': {'n': 0.32, 'p': 0.00, 'k': 0.00},
    'NitroMais (30% N)': {'n': 0.30, 'p': 0.00, 'k': 0.00},
}

# ========================= HELPERS =========================

def _lookup_argila(tabela, teor_argila):
    for k in sorted(tabela.keys()):
        if teor_argila <= k:
            return tabela[k]
    return tabela[max(tabela.keys())]

def _k_mgdm3(k_cmolc):
    return k_cmolc * 391.0

# ========================= PARCELAMENTO N =========================
def _parcelamento_n(n_cob, teor_argila):
    """Retorna lista de parcelamentos para N em cobertura."""
    if teor_argila > 15:
        if n_cob < 100:
            return [{'epoca': '1 aplicacao - V6-V8 (7-8 folhas)', 'dose': n_cob, 'pct': 100}]
        d1 = round(n_cob * 0.50); d2 = n_cob - d1
        return [{'epoca': '1a Cobertura (V4-V5)', 'dose': d1, 'pct': 50},
                {'epoca': '2a Cobertura (V6-V8)', 'dose': d2, 'pct': 50}]
    else:
        if n_cob < 100:
            d1 = round(n_cob * 0.50); d2 = n_cob - d1
            return [{'epoca': '1a Cobertura (V4-V5)', 'dose': d1, 'pct': 50},
                    {'epoca': '2a Cobertura (V6-V8)', 'dose': d2, 'pct': 50}]
        d1 = round(n_cob*0.33); d2 = round(n_cob*0.34); d3 = n_cob-d1-d2
        return [{'epoca': '1a Cobertura (V3-V4)', 'dose': d1, 'pct': 33},
                {'epoca': '2a Cobertura (V5-V6)', 'dose': d2, 'pct': 34},
                {'epoca': '3a Cobertura (V7-V8)', 'dose': d3, 'pct': 33}]

# ========================= FÓSFORO =========================
def classificar_fosforo(fosforo, teor_argila, irrigado=False):
    tabela = P_INTERP_IRRIGADO if irrigado else P_INTERP_SEQUEIRO
    limites = _lookup_argila(tabela, teor_argila)
    classes = ['Muito Baixo', 'Baixo', 'Médio', 'Adequado', 'Alto']
    for i, lim in enumerate(limites):
        if fosforo <= lim:
            return classes[i]
    return 'Alto'

def recomendar_fosforo(fosforo, teor_argila, irrigado=False):
    classe = classificar_fosforo(fosforo, teor_argila, irrigado)
    corr = P_CORRETIVA_IRRIGADO if irrigado else P_CORRETIVA_SEQUEIRO
    man = P_MANUTENCAO_IRRIGADO if irrigado else P_MANUTENCAO_SEQUEIRO
    idx = {'Muito Baixo': 0, 'Baixo': 1, 'Médio': 2}
    if classe in idx:
        doses = _lookup_argila(corr, teor_argila)
        d = doses[idx[classe]]
        return {'classe': classe, 'dose_min': d, 'dose_max': d, 'dose_rec': d, 'tipo': 'corretiva'}
    if classe in man:
        dmin, dmax = man[classe]
        return {'classe': classe, 'dose_min': dmin, 'dose_max': dmax,
                'dose_rec': round((dmin+dmax)/2), 'tipo': 'manutencao'}
    return {'classe': classe, 'dose_min': 0, 'dose_max': 0, 'dose_rec': 0, 'tipo': 'manutencao'}

# ========================= POTÁSSIO =========================
def classificar_potassio(k_cmolc, ctc):
    k_mg = _k_mgdm3(k_cmolc)
    tabela = K_INTERP_CTC_BAIXA if ctc < 4.0 else K_INTERP_CTC_ALTA
    for k_max in sorted(tabela.keys()):
        if k_mg <= k_max:
            interp, ct, cg = tabela[k_max]
            return {'classe': interp, 'k_mg': round(k_mg, 1),
                    'ctc_regime': 'baixa' if ctc < 4.0 else 'alta',
                    'corretiva_total': ct, 'corretiva_grad': cg, 'dose_rec': ct}
    last = tabela[max(tabela.keys())]
    return {'classe': last[0], 'k_mg': round(k_mg, 1),
            'ctc_regime': 'baixa' if ctc < 4.0 else 'alta',
            'corretiva_total': 0, 'corretiva_grad': 0, 'dose_rec': 0}

# ========================= NITROGÊNIO =========================
def recomendar_nitrogenio(meta_prod, teor_argila, historico='normal'):
    n_min = n_max = 80
    for pm, nm, nx in N_FAIXAS:
        if meta_prod <= pm:
            n_min, n_max = nm, nx
            break
    n_rec = round((n_min + n_max) / 2)
    ajuste_pct = 0
    if historico == 'apos_soja':
        ajuste_pct = -30
        n_rec = round(n_rec * 0.70)
        n_min = round(n_min * 0.60)
        n_max = round(n_max * 0.80)
    elif historico == 'cerrado_novo':
        ajuste_pct = +20
        n_rec = round(n_rec * 1.20)
        n_min = round(n_min * 1.20)
        n_max = round(n_max * 1.20)
    parc = _parcelamento_n(n_rec, teor_argila)
    return {'n_base': N_BASE_KGHA, 'n_cobertura_min': n_min,
            'n_cobertura_max': n_max, 'n_cobertura_rec': n_rec,
            'n_total_rec': N_BASE_KGHA + n_rec,
            'ajuste_pct': ajuste_pct, 'historico': historico,
            'parcelamento': parc}

# ========================= CALAGEM =========================
def calcular_calagem(v1, ctc, v2=50.0, prnt=100.0):
    if v1 >= v2:
        return 0.0
    return round(((v2-v1)*ctc/100.0)*(100.0/prnt), 2)

# ========================= INTERPRETAÇÕES =========================
def classificar_ph(ph):
    if ph < 4.5: return 'Muito Acido'
    if ph < 5.5: return 'Acido'
    if ph < 6.0: return 'Moderadamente Acido'
    if ph < 7.0: return 'Adequado'
    return 'Alto'

def classificar_ctc(ctc):
    if ctc < 4: return 'Muito Baixa'
    if ctc < 8: return 'Baixa'
    if ctc < 15: return 'Media'
    if ctc < 25: return 'Alta'
    return 'Muito Alta'

def interpretar_saturacao(v):
    if v < 30: return 'Muito Baixa'
    if v < 50: return 'Baixa'
    if v < 70: return 'Adequada'
    return 'Alta'

# ========================= FERTILIZANTES =========================
def calcular_dose_fertilizante(p2o5_rec, k2o_rec, n_base, fertilizante):
    comp = FERTILIZANTES_DISPONIVEIS.get(fertilizante)
    if not comp:
        return None
    doses = []
    if comp['p'] > 0 and p2o5_rec > 0: doses.append(p2o5_rec / comp['p'])
    if comp['k'] > 0 and k2o_rec > 0: doses.append(k2o_rec / comp['k'])
    if comp['n'] > 0 and n_base > 0: doses.append(n_base / comp['n'])
    if not doses: return None
    dose = max(doses)
    return {'dose_kgha': round(dose), 'n_fornecido': round(dose*comp['n']),
            'p_fornecido': round(dose*comp['p']), 'k_fornecido': round(dose*comp['k'])}

def calcular_dose_cobertura(n_cobertura, fertilizante):
    comp = COBERTURA_OPCOES.get(fertilizante) or FERTILIZANTES_DISPONIVEIS.get(fertilizante)
    if not comp or comp['n'] == 0: return None
    dose = n_cobertura / comp['n']
    return {'dose_kgha': round(dose), 'n_fornecido': round(dose*comp['n'])}

# ========================= ATENÇÕES =========================
def gerar_atencoes_doses(n_cob, k2o_rec, ctc, teor_argila, dose_base_kgha):
    atencoes = []
    if n_cob >= 100 and teor_argila > 15:
        atencoes.append({'nutriente':'N','nivel':'warning',
            'titulo':'Parcelamento obrigatorio do N em cobertura',
            'msg':(f'Dose N cobertura ({n_cob} kg/ha) >= 100 kg/ha em argila > 15%. '
                   f'Parcelar em 2x: 50% no V4-V5 + 50% no V6-V8 para reduzir volatilizacao.')})
    if n_cob >= 100 and teor_argila <= 15:
        atencoes.append({'nutriente':'N','nivel':'danger',
            'titulo':'Solo arenoso + alta dose N: parcelar em 3 vezes',
            'msg':(f'Argila <= 15% e N cobertura ({n_cob} kg/ha) >= 100 kg/ha. '
                   f'Alto risco de lixiviacao. Aplicar em 3 parcelas (V3-V4 / V5-V6 / V7-V8). '
                   f'Preferir sulfato de amonio ou nitrato nítrico-amoniacal.')})
    elif n_cob < 100 and teor_argila <= 15:
        atencoes.append({'nutriente':'N','nivel':'info',
            'titulo':'Solo arenoso: parcelar N mesmo em doses menores',
            'msg':(f'Argila <= 15% — parcelar cobertura em 2x para reduzir lixiviacao de N.')})
    if k2o_rec > 100:
        atencoes.append({'nutriente':'K','nivel':'warning',
            'titulo':'Dose elevada de K2O - parcelamento recomendado',
            'msg':(f'K2O ({k2o_rec} kg/ha) > 100 kg/ha. Preferir parcelamento ou aplicacao '
                   f'a lanco incorporado para evitar salinizacao e queima de sementes.')})
    if ctc < 4.0 and k2o_rec > 40:
        atencoes.append({'nutriente':'K','nivel':'danger',
            'titulo':'CTC baixa + dose K elevada: risco de lixiviacao',
            'msg':(f'CTC < 4,0 cmolc/dm3 — baixa capacidade de retencao de K. '
                   f'Parcelar a dose ou aplicar a lanco. Avaliar calagem para elevar CTC.')})
    if dose_base_kgha and dose_base_kgha > 500:
        atencoes.append({'nutriente':'NPK','nivel':'warning',
            'titulo':'Dose elevada no sulco de plantio',
            'msg':(f'{dose_base_kgha} kg/ha no sulco. Doses > 400-500 kg/ha podem causar '
                   f'salinizacao e queima de sementes. Considere fracionamento a lanco.')})
    return atencoes

# ========================= MOTOR PRINCIPAL =========================
def gerar_recomendacao_completa(dados):
    ph = float(dados.get('ph', 5.5))
    fosforo = float(dados.get('fosforo', 5.0))
    potassio = float(dados.get('potassio', 0.15))
    ctc = float(dados.get('ctc', 8.0))
    v1 = float(dados.get('saturacao_bases', 40.0))
    teor_argila = float(dados.get('teor_argila', 40.0))
    meta_prod = float(dados.get('meta_produtividade', 8.0))
    irrigado = dados.get('irrigado', False) in (True, 'True', 'true', '1', 'on')
    historico = dados.get('historico_area', 'normal')
    fert_base = dados.get('fertilizante_base', '04-14-08')
    fert_cob = dados.get('fertilizante_cobertura', 'Ureia (45% N)')
    prnt = float(dados.get('prnt_calcario', 100.0))
    area_ha = float(dados.get('area_ha', 1.0))
    preco_fert = float(dados.get('preco_fert_base', 0))
    preco_cob = float(dados.get('preco_fert_cob', 0))

    classe_ph = classificar_ph(ph)
    classe_sat = interpretar_saturacao(v1)
    classe_ctc = classificar_ctc(ctc)

    rec_p = recomendar_fosforo(fosforo, teor_argila, irrigado)
    rec_k = classificar_potassio(potassio, ctc)
    rec_n = recomendar_nitrogenio(meta_prod, teor_argila, historico)
    nc = calcular_calagem(v1, ctc, prnt=prnt)

    dose_base = calcular_dose_fertilizante(rec_p['dose_rec'], rec_k['dose_rec'], rec_n['n_base'], fert_base)
    dose_cob = calcular_dose_cobertura(rec_n['n_cobertura_rec'], fert_cob)

    custo_base = (dose_base['dose_kgha']*area_ha*preco_fert/1000) if (dose_base and preco_fert) else 0
    custo_cob = (dose_cob['dose_kgha']*area_ha*preco_cob/1000) if (dose_cob and preco_cob) else 0

    alertas = _gerar_alertas(ph, nc, rec_p['classe'], rec_k['classe'], v1)
    atencoes = gerar_atencoes_doses(
        n_cob=rec_n['n_cobertura_rec'],
        k2o_rec=rec_k['dose_rec'],
        ctc=ctc,
        teor_argila=teor_argila,
        dose_base_kgha=dose_base['dose_kgha'] if dose_base else 0,
    )

    return {
        'interpretacao': {
            'ph': classe_ph, 'fosforo': rec_p['classe'],
            'potassio': rec_k['classe'], 'saturacao': classe_sat, 'ctc': classe_ctc,
        },
        'recomendacao': {
            'n_base': rec_n['n_base'],
            'n_cobertura_min': rec_n['n_cobertura_min'],
            'n_cobertura_max': rec_n['n_cobertura_max'],
            'n_cobertura_rec': rec_n['n_cobertura_rec'],
            'n_total': rec_n['n_total_rec'],
            'p2o5': rec_p['dose_rec'],
            'p2o5_min': rec_p['dose_min'],
            'p2o5_max': rec_p['dose_max'],
            'p2o5_tipo': rec_p['tipo'],
            'k2o': rec_k['dose_rec'],
            'k2o_grad': rec_k['corretiva_grad'],
            'calcario': nc,
        },
        'parcelamento_n': rec_n['parcelamento'],
        'n_base_semeadura': rec_n['n_base'],
        'ajuste_n_pct': rec_n['ajuste_pct'],
        'fertilizante_base': {'produto': fert_base, **(dose_base or {})},
        'fertilizante_cobertura': {'produto': fert_cob, **(dose_cob or {})},
        'custo_estimado': {'base': round(custo_base, 2), 'cob': round(custo_cob, 2),
                           'total': round(custo_base + custo_cob, 2)},
        'alertas': alertas,
        'atencoes': atencoes,
        'modo': 'irrigado' if irrigado else 'sequeiro',
        'historico': historico,
    }

def _gerar_alertas(ph, nc, classe_p, classe_k, v1):
    alertas = []
    if nc > 0:
        alertas.append({'tipo': 'warning',
            'msg': f'Necessario {nc} t/ha de calcario — V% atual: {v1:.0f}% (meta: 50%)'})
    if ph < 5.5:
        alertas.append({'tipo': 'danger',
            'msg': f'pH {ph} muito baixo — risco de toxidez de Al3+ e Mn. Calagem prioritaria.'})
    if v1 < 30:
        alertas.append({'tipo': 'danger',
            'msg': f'Saturacao por bases muito baixa ({v1:.0f}%) — correcao urgente.'})
    if classe_p in ('Muito Baixo','Baixo'):
        alertas.append({'tipo': 'warning',
            'msg': f'Fosforo {classe_p} — alta probabilidade de resposta a adubacao fosfatada.'})
    if classe_k == 'Baixo':
        alertas.append({'tipo': 'warning',
            'msg': 'Potassio Baixo — risco de deficiencia no enchimento de graos.'})
    return alertas