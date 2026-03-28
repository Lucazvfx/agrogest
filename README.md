# 🌽 AgroMilho — Sistema de Gestão Agrícola

Sistema web completo para gestão de propriedades agrícolas focado na **cultura do milho**, com calculadora de adubação NPK baseada no Manual da Embrapa Cerrado.

---

## 🚀 Instalação e Execução

### Pré-requisitos
- Python 3.10+
- pip

### 1. Instalar dependências

```bash
pip install flask pandas weasyprint
```

> **Nota:** `weasyprint` requer algumas bibliotecas de sistema para geração de PDF.
> Em Ubuntu/Debian: `sudo apt install libpango-1.0-0 libpangoft2-1.0-0`
> Se preferir não usar WeasyPrint, o sistema funciona normalmente sem PDF — as demais funcionalidades não são afetadas.

### 2. Ativar venv

venv\Scripts\activate

### 3. Iniciar o sistema

```bash
python app.py
```

Acesse: **http://localhost:5000**

### 4. (Opcional) Carregar dados de demonstração

```bash
python seed.py

### 5. Carregar dados de att

```
git add .
git commit -m "Ajuste no sistema do sistema"
git push origin main

Popula o banco com 4 talhões, análises de solo, plantios de duas safras, colheitas e custos de exemplo.

---

## 📁 Estrutura do Projeto

```
fazenda_milho/
│
├── app.py                          # Aplicação Flask principal
├── config.py                       # Configurações
├── database.py                     # Inicialização SQLite e schema completo
├── seed.py                         # Dados de demonstração
├── requirements.txt
│
├── modules/
│   ├── calculadora_adubacao.py     # 🧮 Motor de cálculo NPK (Embrapa)
│   ├── talhoes.py                  # CRUD de talhões
│   ├── plantio.py                  # Gestão de plantios
│   ├── adubacao.py                 # Análises de solo + recomendações
│   ├── defensivos.py               # Aplicação de defensivos
│   ├── custos.py                   # Lançamento de custos
│   ├── colheita.py                 # Registro de colheitas
│   ├── dashboard.py                # Dashboard com KPIs
│   └── relatorios.py               # Relatórios e PDF
│
├── templates/
│   ├── base.html                   # Layout base com sidebar
│   ├── dashboard.html              # Dashboard principal
│   ├── talhoes/
│   ├── plantio/
│   ├── adubacao/
│   ├── defensivos/
│   ├── custos/
│   ├── colheita/
│   └── relatorios/
│
└── static/
```

---

## 🌿 Funcionalidades

### Dashboard
- KPIs: área total, área plantada, produtividade média, resultado estimado
- Gráfico de produtividade por safra (barras + linha de receita)
- Gráfico de custos por categoria (doughnut)
- Plantios em andamento e últimas colheitas
- **Alertas de estoque de fertilizantes** (< 500 kg)
- Ações rápidas

### 🗺️ Talhões
- Cadastro com nome, área, localização e tipo de solo
- Card com número de plantios, análises e melhor produtividade
- Detalhe com histórico completo de análises e safras

### 🌱 Plantios
- Vínculo por talhão e safra
- Informações de híbrido, população e área
- Status: planejado → plantado → emergência → vegetativo → reprodutivo → maturação → colhido
- Registro de aplicações de adubação por plantio

### 🧪 Análises de Solo
Campos completos do laudo laboratorial:
- pH, P (Mehlich-1), K, Ca, Mg, Al, H+Al
- CTC, Saturação por Bases (V%), Teor de Argila, MO
- Histórico por talhão com cores de interpretação

### 🧮 Calculadora NPK — Motor Embrapa Cerrado

**Calagem — Método da Saturação por Bases:**
```
NC = (V₂ - V₁) × CTC / 100
```
Meta: V₂ = 50% para milho. Ajuste pelo PRNT.

**Fósforo — Interpretação por classe de argila (Mehlich-1):**

| Argila (%) | Muito Baixo | Baixo | Médio | Adequado | Alto |
|-----------|-------------|-------|-------|----------|------|
| ≥ 60 | ≤ 4 | ≤ 8 | ≤ 12 | ≤ 20 | > 20 |
| 36–60 | ≤ 6 | ≤ 12 | ≤ 18 | ≤ 30 | > 30 |
| 20–36 | ≤ 8 | ≤ 16 | ≤ 24 | ≤ 40 | > 40 |
| < 20 | ≤ 10 | ≤ 20 | ≤ 30 | ≤ 50 | > 50 |

**Recomendação P₂O₅:**

| Classe | P₂O₅ (kg/ha) |
|--------|--------------|
| Muito Baixo | 120 |
| Baixo | 100 |
| Médio | 80 |
| Adequado | 40 |
| Alto | 0 |

**Recomendação K₂O:**

| Classe | K₂O (kg/ha) |
|--------|-------------|
| Muito Baixo | 120 |
| Baixo | 90 |
| Médio | 60 |
| Adequado | 30 |
| Alto | 0 |

**Nitrogênio por meta de produtividade:**

| Produtividade | N (kg/ha) |
|--------------|-----------|
| ≤ 6 t/ha | 80 |
| 8 t/ha | 120 |
| 10 t/ha | 160 |
| 12 t/ha | 200 |
| 14 t/ha | 220 |

**Parcelamento do N:**
- 30% base (semeadura)
- 40% 1ª cobertura (V4–V5)
- 30% 2ª cobertura (V6–V8)

**Conversão para fertilizante comercial:**
```
dose = nutriente_recomendado / percentual_no_fertilizante
```

**Fertilizantes disponíveis:** 04-14-08, 08-28-16, 05-25-15, 10-10-10, 02-20-20, 04-20-20, 06-30-06, 00-18-18, Superfosfato Simples, Superfosfato Triplo, KCl, Ureia, Sulfato de Amônio, MAP, DAP.

### 🛡️ Defensivos
- Registro por plantio: herbicidas, fungicidas, inseticidas
- Dose (L/ha), área, custo por litro
- Estágio da cultura no momento da aplicação

### 💰 Custos
- Categorias: Sementes, Fertilizantes, Defensivos, Combustível, Mão de Obra, Maquinário, Colheita, Transporte, etc.
- Totais por categoria exibidos em cards
- Totalizador automático

### 🌾 Colheitas
- Produção total, umidade na colheita
- **Correção automática de umidade para 13%**
- Cálculo de produtividade (kg/ha e sc/ha)
- Receita bruta (sc colhidas × preço)
- Prévia em tempo real antes de salvar

### 📊 Relatórios
- **Relatório de safra:** comparação de produtividade, receita e resultado por talhão
- **Relatório de adubação:** análise de solo + recomendação NPK + fertilizantes
- **PDF de adubação** via WeasyPrint (ou HTML como fallback)

---

## 🗃️ Banco de Dados (SQLite)

Tabelas:
- `talhoes` — cadastro de talhões
- `analises_solo` — laudos laboratoriais
- `recomendacoes_adubacao` — recomendações NPK geradas
- `plantios` — safras por talhão
- `aplicacoes_adubacao` — adubações aplicadas
- `aplicacoes_defensivos` — defensivos aplicados
- `custos` — lançamentos de custo
- `colheitas` — resultados de colheita
- `estoque_fertilizantes` — controle de estoque

---

## 🎨 Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3 + Flask |
| Banco | SQLite (via módulo nativo) |
| Templates | Jinja2 + HTML5 |
| CSS | Bootstrap 5.3 + CSS customizado |
| Gráficos | Chart.js 4.4 |
| Fontes | Syne (títulos) + DM Sans (corpo) |
| Ícones | Bootstrap Icons |
| PDF | WeasyPrint |
| Dados | Pandas (disponível para análises) |

---

## 📌 Referências Técnicas

- **Embrapa Cerrado** — Manual de Adubação e Calagem para o Cerrado
- Método da Saturação por Bases para calagem
- Fósforo Mehlich-1 com interpretação por teor de argila
- Tabelas de recomendação para milho grão (cerrado)

---

*Sistema desenvolvido para auxílio na gestão agrícola. Consulte sempre um Engenheiro Agrônomo habilitado para validação das recomendações.*
