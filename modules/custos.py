from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db

custos_bp = Blueprint('custos', __name__)

@custos_bp.route('/')
def index():
    db = get_db()
    custos = db.execute("""
        SELECT c.*, p.safra, t.nome as talhao_nome
        FROM custos c
        JOIN plantios p ON p.id = c.plantio_id
        JOIN talhoes t ON t.id = p.talhao_id
        ORDER BY c.data_custo DESC
    """).fetchall()
    plantios = db.execute("SELECT p.id, p.safra, t.nome as talhao_nome FROM plantios p JOIN talhoes t ON t.id=p.talhao_id ORDER BY p.safra DESC").fetchall()
    
    # Totais por categoria
    totais = db.execute("""
        SELECT categoria, SUM(valor) as total
        FROM custos GROUP BY categoria
    """).fetchall()
    
    return render_template('custos/index.html', custos=custos, plantios=plantios, totais=totais)

@custos_bp.route('/novo', methods=['POST'])
def novo():
    db = get_db()
    f = request.form
    db.execute("""
        INSERT INTO custos (plantio_id, categoria, descricao, valor, data_custo, observacoes)
        VALUES (?,?,?,?,?,?)
    """, (f['plantio_id'], f['categoria'], f['descricao'], f['valor'], f.get('data_custo'), f.get('observacoes')))
    db.commit()
    flash('Custo registrado!', 'success')
    return redirect(url_for('custos.index'))
