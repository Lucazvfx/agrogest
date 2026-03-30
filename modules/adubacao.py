from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database import get_db
from modules.calculadora_adubacao import (
    gerar_recomendacao_completa,
    FERTILIZANTES_DISPONIVEIS, COBERTURA_OPCOES
)
from auth import login_required
from flask import session

adubacao_bp = Blueprint('adubacao', __name__)

def uid():
    return session['usuario_id']


# ===============================
# DASHBOARD
# ===============================
@adubacao_bp.route('/')
@login_required
def index():
    db = get_db()

    adubacao = db.execute("""
        SELECT p.*, t.nome as talhao_nome, t.area_ha
        FROM plantios p
        JOIN talhoes t ON t.id = p.talhao_id
        WHERE t.usuario_id = ?
        ORDER BY p.safra DESC
    """, (uid(),)).fetchall()

    return render_template("adubacao/index.html", adubacao=adubacao)


# ===============================
# LISTAR ANÁLISES
# ===============================
@adubacao_bp.route('/analises')
@login_required
def analises():
    db = get_db()

    analises = db.execute("""
        SELECT a.*, t.nome as talhao_nome
        FROM analises_solo a
        JOIN talhoes t ON t.id = a.talhao_id
        WHERE t.usuario_id = ?
        ORDER BY a.data_coleta DESC
    """, (uid(),)).fetchall()

    return render_template('adubacao/analises.html', analises=analises)


# ===============================
# NOVA ANÁLISE
# ===============================
@adubacao_bp.route('/analises/nova', methods=['GET', 'POST'])
@login_required
def nova_analise():
    db = get_db()

    talhoes = db.execute(
        "SELECT * FROM talhoes WHERE usuario_id=? ORDER BY nome",
        (uid(),)
    ).fetchall()

    if request.method == 'POST':

        f = request.form

        db.execute("""
            INSERT INTO analises_solo 
            (talhao_id, data_coleta, safra, profundidade, ph, fosforo, potassio,
             calcio, magnesio, aluminio, h_al, ctc, saturacao_bases, teor_argila,
             materia_organica, observacoes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            f['talhao_id'],
            f['data_coleta'],
            f.get('safra'),
            f.get('profundidade', '0-20 cm'),
            f.get('ph'),
            f.get('fosforo'),
            f.get('potassio'),
            f.get('calcio'),
            f.get('magnesio'),
            f.get('aluminio'),
            f.get('h_al'),
            f.get('ctc'),
            f.get('saturacao_bases'),
            f.get('teor_argila'),
            f.get('materia_organica'),
            f.get('observacoes')
        ))

        db.commit()

        flash('Análise de solo cadastrada!', 'success')

        return redirect(url_for('adubacao.analises'))

    return render_template('adubacao/form_analise.html', talhoes=talhoes, analise=None)


# ===============================
# EDITAR ANÁLISE
# ===============================
@adubacao_bp.route('/analises/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_analise(id):

    db = get_db()

    analise = db.execute(
        "SELECT * FROM analises_solo WHERE id=?",
        (id,)
    ).fetchone()

    talhoes = db.execute(
        "SELECT * FROM talhoes WHERE usuario_id=? ORDER BY nome",
        (uid(),)
    ).fetchall()

    if request.method == 'POST':

        f = request.form

        db.execute("""
            UPDATE analises_solo
            SET talhao_id=?, data_coleta=?, safra=?, profundidade=?,
                ph=?, fosforo=?, potassio=?, calcio=?, magnesio=?, aluminio=?, h_al=?,
                ctc=?, saturacao_bases=?, teor_argila=?, materia_organica=?, observacoes=?
            WHERE id=?
        """, (
            f['talhao_id'],
            f['data_coleta'],
            f.get('safra'),
            f.get('profundidade', '0-20 cm'),
            f.get('ph'),
            f.get('fosforo'),
            f.get('potassio'),
            f.get('calcio'),
            f.get('magnesio'),
            f.get('aluminio'),
            f.get('h_al'),
            f.get('ctc'),
            f.get('saturacao_bases'),
            f.get('teor_argila'),
            f.get('materia_organica'),
            f.get('observacoes'),
            id
        ))

        db.commit()

        flash('Análise atualizada!', 'success')

        return redirect(url_for('adubacao.analises'))

    return render_template(
        'adubacao/form_analise.html',
        talhoes=talhoes,
        analise=analise
    )


# ===============================
# DELETAR ANÁLISE
# ===============================
@adubacao_bp.route('/analises/<int:id>/deletar', methods=['POST'])
@login_required
def deletar_analise(id):

    db = get_db()

    analise = db.execute("""
        SELECT a.id
        FROM analises_solo a
        JOIN talhoes t ON t.id = a.talhao_id
        WHERE a.id=? AND t.usuario_id=?
    """, (id, uid())).fetchone()

    if not analise:
        flash("Análise não encontrada.", "danger")
        return redirect(url_for("adubacao.analises"))

    db.execute(
        "DELETE FROM analises_solo WHERE id=?",
        (id,)
    )

    db.commit()

    flash("Análise removida com sucesso!", "success")

    return redirect(url_for("adubacao.analises"))


# ===============================
# LISTAR RECOMENDAÇÕES
# ===============================
@adubacao_bp.route('/recomendacoes')
@login_required
def recomendacoes():

    db = get_db()

    recs = db.execute("""
        SELECT r.*, t.nome as talhao_nome
        FROM recomendacoes_adubacao r
        JOIN talhoes t ON t.id = r.talhao_id
        WHERE t.usuario_id = ?
        ORDER BY r.criado_em DESC
    """, (uid(),)).fetchall()

    return render_template(
        'adubacao/recomendacoes.html',
        recomendacoes=recs
    )


# ===============================
# NOVA RECOMENDAÇÃO
# ===============================
@adubacao_bp.route('/recomendacoes/nova', methods=['GET', 'POST'])
@login_required
def nova_recomendacao():

    db = get_db()

    talhoes = db.execute(
        "SELECT * FROM talhoes WHERE usuario_id=? ORDER BY nome",
        (uid(),)
    ).fetchall()

    fertilizantes = list(FERTILIZANTES_DISPONIVEIS.keys())
    coberturas = list(COBERTURA_OPCOES.keys())

    resultado = None

    if request.method == 'POST':

        f = request.form

        talhao_id = int(f['talhao_id'])

        analise_id = f.get('analise_id') or None

        if analise_id:
            analise = db.execute(
                "SELECT * FROM analises_solo WHERE id=?",
                (analise_id,)
            ).fetchone()
        else:
            analise = db.execute(
                "SELECT * FROM analises_solo WHERE talhao_id=? ORDER BY data_coleta DESC LIMIT 1",
                (talhao_id,)
            ).fetchone()

        dados = {
            'ph': float(f.get('ph') or (analise['ph'] if analise else 5.5)),
            'fosforo': float(f.get('fosforo') or (analise['fosforo'] if analise else 5)),
            'potassio': float(f.get('potassio') or (analise['potassio'] if analise else 0.1)),
            'ctc': float(f.get('ctc') or (analise['ctc'] if analise else 8)),
            'saturacao_bases': float(f.get('saturacao_bases') or (analise['saturacao_bases'] if analise else 35)),
            'teor_argila': float(f.get('teor_argila') or (analise['teor_argila'] if analise else 40)),
            'meta_produtividade': float(f.get('meta_produtividade', 8)),
            'fertilizante_base': f.get('fertilizante_base', '04-14-08'),
            'fertilizante_cobertura': f.get('fertilizante_cobertura', 'Ureia (45% N)'),
            'prnt_calcario': float(f.get('prnt_calcario', 100)),
            'area_ha': float(f.get('area_ha', 1)),
            'preco_fert_base': float(f.get('preco_fert_base', 0)),
            'preco_fert_cob': float(f.get('preco_fert_cob', 0)),
        }

        resultado = gerar_recomendacao_completa(dados)

    analises_lista = db.execute("""
        SELECT a.id, a.data_coleta, a.safra, t.nome as talhao_nome
        FROM analises_solo a
        JOIN talhoes t ON t.id = a.talhao_id
        WHERE t.usuario_id = ?
        ORDER BY a.data_coleta DESC
    """, (uid(),)).fetchall()

    return render_template(
        'adubacao/nova_recomendacao.html',
        talhoes=talhoes,
        fertilizantes=fertilizantes,
        coberturas=coberturas,
        resultado=resultado,
        analises=analises_lista
    )


# ===============================
# API ANALISE TALHÃO
# ===============================
@adubacao_bp.route('/api/analise/<int:talhao_id>')
@login_required
def api_analise_talhao(talhao_id):

    db = get_db()

    analise = db.execute("""
        SELECT *
        FROM analises_solo
        WHERE talhao_id=?
        ORDER BY data_coleta DESC
        LIMIT 1
    """, (talhao_id,)).fetchone()

    if analise:
        return jsonify(dict(analise))

    return jsonify({})