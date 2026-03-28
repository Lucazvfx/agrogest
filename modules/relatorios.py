from flask import Blueprint, render_template, request, make_response
from database import get_db
try:
    from weasyprint import HTML
    WEASYPRINT_OK = True
except Exception:
    WEASYPRINT_OK = False

# Importações das funções de classificação e parcelamento
from modules.calculadora_adubacao import (
    classificar_ph,
    classificar_fosforo,
    classificar_potassio,
    interpretar_saturacao,
    classificar_ctc,
    _parcelamento_n
)

relatorios_bp = Blueprint('relatorios', __name__)

@relatorios_bp.route('/')
def index():
    db = get_db()
    talhoes = db.execute("SELECT * FROM talhoes ORDER BY nome").fetchall()
    safras = db.execute("SELECT DISTINCT safra FROM plantios ORDER BY safra DESC").fetchall()
    return render_template('relatorios/index.html', talhoes=talhoes, safras=safras)

@relatorios_bp.route('/adubacao/<int:rec_id>')
def relatorio_adubacao(rec_id):
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
    return render_template('relatorios/adubacao.html', rec=rec, analise=analise)

@relatorios_bp.route('/adubacao/<int:rec_id>/pdf')
def pdf_adubacao(rec_id):
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

    interpretacoes = {}
    parcelamento = []
    n_base_semeadura = 20
    custo_base = custo_cob = None

    if analise:
        interpretacoes['ph_classe'] = classificar_ph(analise['ph'])
        irrigado = False  # Melhorar futuramente
        interpretacoes['p_classe'] = classificar_fosforo(
            analise['fosforo'], analise['teor_argila'], irrigado
        )
        k_info = classificar_potassio(analise['potassio'], analise['ctc'])
        interpretacoes['k_classe'] = k_info['classe']
        interpretacoes['v_classe'] = interpretar_saturacao(analise['saturacao_bases'])
        interpretacoes['ctc_classe'] = classificar_ctc(analise['ctc'])

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
        return html_content

@relatorios_bp.route('/safra')
def relatorio_safra():
    db = get_db()
    safra = request.args.get('safra')
    talhao_id = request.args.get('talhao_id')
    
    query = """
        SELECT c.*, p.safra, p.hibrido, t.nome as talhao_nome, t.area_ha,
               (SELECT SUM(valor) FROM custos WHERE plantio_id = p.id) as total_custo
        FROM colheitas c
        JOIN plantios p ON p.id = c.plantio_id
        JOIN talhoes t ON t.id = p.talhao_id
        WHERE 1=1
    """
    params = []
    if safra:
        query += " AND p.safra = ?"
        params.append(safra)
    if talhao_id:
        query += " AND t.id = ?"
        params.append(talhao_id)
    query += " ORDER BY t.nome"
    
    dados = db.execute(query, params).fetchall()
    return render_template('relatorios/safra.html', dados=dados, safra=safra)