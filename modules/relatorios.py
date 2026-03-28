
from flask import Blueprint, render_template # e outros imports que você usa

# ESTA LINHA ABAIXO É A QUE ESTÁ FALTANDO:
relatorios_bp = Blueprint('relatorios', __name__)

@relatorios_bp.route('/adubacao/<int:rec_id>/pdf')
def gerar_pdf(rec_id):
    db = get_db()
    rec = db.execute("""
        SELECT r.*, t.nome as talhao_nome, t.area_ha
        FROM recomendacoes_adubacao r
        JOIN talhoes t ON t.id = r.talhao_id
        WHERE r.id=?
    """, (rec_id,)).fetchone()
    analise = None
    if rec and rec['analise_solo_id']:
        analise = db.execute("SELECT * FROM analises_solo WHERE id=?", (rec['analise_solo_id'],)).fetchone()

    # Importações das funções de classificação e parcelamento
    from modules.calculadora_adubacao import (
        classificar_ph,
        classificar_fosforo,
        classificar_potassio,
        interpretar_saturacao,
        classificar_ctc,
        _parcelamento_n
    )

    # Variáveis a serem passadas para o template
    interpretacoes = {}
    parcelamento = []
    n_base_semeadura = 20  # kg N/ha fixo na semeadura (de acordo com o motor de cálculo)
    custo_base = None
    custo_cob = None

    # Se houver análise, calculamos as interpretações e o parcelamento
    if analise:
        # Interpretação do pH
        interpretacoes['ph_classe'] = classificar_ph(analise['ph'])

        # Interpretação do fósforo (sequeiro como padrão)
        irrigado = False
        interpretacoes['p_classe'] = classificar_fosforo(
            analise['fosforo'],
            analise['teor_argila'],
            irrigado
        )

        # Interpretação do potássio
        k_info = classificar_potassio(analise['potassio'], analise['ctc'])
        interpretacoes['k_classe'] = k_info['classe']

        # Interpretação da saturação por bases
        interpretacoes['v_classe'] = interpretar_saturacao(analise['saturacao_bases'])

        # Interpretação da CTC
        interpretacoes['ctc_classe'] = classificar_ctc(analise['ctc'])

        # Parcelamento do nitrogênio em cobertura
        n_total = rec['n_recomendado']
        n_cob = n_total - n_base_semeadura
        teor_argila = analise['teor_argila'] if analise['teor_argila'] else 40
        parcelamento = _parcelamento_n(n_cob, teor_argila)

    html_content = render_template(
        'relatorios/adubacao_pdf.html',
        rec=rec,
        analise=analise,
        interpretacoes=interpretacoes,
        parcelamento=parcelamento,
        n_base_semeadura=n_base_semeadura,
        custo_base=custo_base,
        custo_cob=custo_cob
    )

    if WEASYPRINT_OK:
        pdf = HTML(string=html_content).write_pdf()
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=recomendacao_{rec_id}.pdf'
        return response
    else:
        # Fallback: retorna HTML
        return html_content