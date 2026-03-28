from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db

defensivos_bp = Blueprint('defensivos', __name__)

@defensivos_bp.route('/')
def index():
    db = get_db()
    apls = db.execute("""
        SELECT d.*, p.safra, t.nome as talhao_nome
        FROM aplicacoes_defensivos d
        JOIN plantios p ON p.id = d.plantio_id
        JOIN talhoes t ON t.id = p.talhao_id
        ORDER BY d.data_aplicacao DESC
    """).fetchall()
    plantios = db.execute("SELECT p.id, p.safra, t.nome as talhao_nome FROM plantios p JOIN talhoes t ON t.id=p.talhao_id ORDER BY p.safra DESC").fetchall()
    return render_template('defensivos/index.html', aplicacoes=apls, plantios=plantios)

@defensivos_bp.route('/novo', methods=['POST'])
def novo():
    db = get_db()
    f = request.form
    db.execute("""
        INSERT INTO aplicacoes_defensivos (plantio_id, data_aplicacao, produto, tipo, dose_lha, area_ha, custo_litro, estagio_cultura, observacoes)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (f['plantio_id'], f.get('data_aplicacao'), f['produto'], f.get('tipo'),
          f.get('dose_lha'), f.get('area_ha'), f.get('custo_litro'), f.get('estagio_cultura'), f.get('observacoes')))
    db.commit()
    flash('Aplicação de defensivo registrada!', 'success')
    return redirect(url_for('defensivos.index'))
