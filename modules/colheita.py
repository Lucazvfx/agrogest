from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db

colheita_bp = Blueprint('colheita', __name__)

@colheita_bp.route('/')
def index():
    db = get_db()
    colheitas = db.execute("""
        SELECT c.*, p.safra, p.hibrido, t.nome as talhao_nome, t.area_ha
        FROM colheitas c
        JOIN plantios p ON p.id = c.plantio_id
        JOIN talhoes t ON t.id = p.talhao_id
        ORDER BY c.data_colheita DESC
    """).fetchall()
    plantios = db.execute("""
        SELECT p.id, p.safra, t.nome as talhao_nome, t.area_ha
        FROM plantios p JOIN talhoes t ON t.id=p.talhao_id
        WHERE p.id NOT IN (SELECT plantio_id FROM colheitas)
        ORDER BY p.safra DESC
    """).fetchall()
    return render_template('colheita/index.html', colheitas=colheitas, plantios=plantios)

@colheita_bp.route('/nova', methods=['POST'])
def nova():
    db = get_db()
    f = request.form
    prod_total = float(f.get('producao_total', 0))
    umidade = float(f.get('umidade_colheita', 13))
    area_ha = float(f.get('area_ha', 1))
    
    # Correção para 13% de umidade
    prod_corrigida = prod_total * ((100 - umidade) / (100 - 13)) if umidade != 13 else prod_total
    prod_kgha = prod_corrigida / area_ha if area_ha > 0 else 0
    prod_scha = prod_kgha / 60  # saca de 60kg
    preco_saca = float(f.get('preco_saca', 0))
    receita = prod_corrigida / 60 * preco_saca if preco_saca else 0
    
    db.execute("""
        INSERT INTO colheitas (plantio_id, data_colheita, producao_total, umidade_colheita,
        producao_corrigida, produtividade_kgha, produtividade_scha, preco_saca, receita_bruta, observacoes)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (f['plantio_id'], f.get('data_colheita'), prod_total, umidade,
          round(prod_corrigida, 1), round(prod_kgha, 1), round(prod_scha, 2),
          preco_saca, round(receita, 2), f.get('observacoes')))
    db.commit()
    flash('Colheita registrada!', 'success')
    return redirect(url_for('colheita.index'))
