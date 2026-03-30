from flask import Blueprint, render_template
from database import get_db
from auth import login_required
from flask import session

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    db = get_db()

    # KPIs principais
    total_talhoes = db.execute("SELECT COUNT(*) FROM talhoes").fetchone()[0]
    area_total = db.execute("SELECT COALESCE(SUM(area_ha),0) FROM talhoes").fetchone()[0]
    
    area_plantada = db.execute("""
        SELECT COALESCE(SUM(area_plantada),0) FROM plantios WHERE status != 'colhido'
    """).fetchone()[0]
    
    prod_media = db.execute("""
        SELECT COALESCE(AVG(produtividade_scha),0) FROM colheitas
    """).fetchone()[0]
    
    receita_total = db.execute("SELECT COALESCE(SUM(receita_bruta),0) FROM colheitas").fetchone()[0]
    custo_total = db.execute("SELECT COALESCE(SUM(valor),0) FROM custos").fetchone()[0]
    lucro_estimado = receita_total - custo_total

    # Produtividade por safra (gráfico)
    prod_safra = db.execute("""
        SELECT p.safra, 
               ROUND(AVG(c.produtividade_scha),2) as prod_media,
               ROUND(SUM(c.receita_bruta),2) as receita,
               COUNT(c.id) as num_talhoes
        FROM colheitas c
        JOIN plantios p ON p.id = c.plantio_id
        GROUP BY p.safra
        ORDER BY p.safra
    """).fetchall()

    # Custos por categoria (gráfico pizza)
    custos_cat = db.execute("""
        SELECT categoria, ROUND(SUM(valor),2) as total
        FROM custos GROUP BY categoria
    """).fetchall()

    # Últimas atividades
    ultimas_colheitas = db.execute("""
        SELECT c.*, p.safra, p.hibrido, t.nome as talhao_nome
        FROM colheitas c
        JOIN plantios p ON p.id = c.plantio_id
        JOIN talhoes t ON t.id = p.talhao_id
        ORDER BY c.data_colheita DESC LIMIT 5
    """).fetchall()

    # Alertas estoque fertilizantes
    alertas_estoque = db.execute("""
        SELECT * FROM estoque_fertilizantes WHERE quantidade_kg < 500
    """).fetchall()

    # Plantios ativos
    plantios_ativos = db.execute("""
        SELECT p.*, t.nome as talhao_nome, t.area_ha
        FROM plantios p JOIN talhoes t ON t.id = p.talhao_id
        WHERE p.status NOT IN ('colhido')
        ORDER BY p.data_plantio DESC
    """).fetchall()

    return render_template('dashboard.html',
        total_talhoes=total_talhoes,
        area_total=round(area_total, 1),
        area_plantada=round(area_plantada, 1),
        prod_media=round(prod_media, 2),
        receita_total=round(receita_total, 2),
        custo_total=round(custo_total, 2),
        lucro_estimado=round(lucro_estimado, 2),
        prod_safra=prod_safra,
        custos_cat=custos_cat,
        ultimas_colheitas=ultimas_colheitas,
        alertas_estoque=alertas_estoque,
        plantios_ativos=plantios_ativos,
    )
