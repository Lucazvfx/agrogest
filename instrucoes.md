# 🔐 Sistema de Login — AgroGest
## Guia de Instalação

---

## 1. Instale a dependência

```bash
pip install flask
```
O Flask já inclui suporte a sessões. Não precisa de lib extra.

---

## 2. Arquivos para substituir / criar

| Arquivo gerado         | Destino no projeto                        |
|------------------------|-------------------------------------------|
| `auth.py`              | `auth.py` (raiz do projeto)               |
| `database.py`          | `database.py` (raiz do projeto)           |
| `talhoes.py`           | `talhoes.py` (raiz do projeto)            |
| `login.html`           | `templates/auth/login.html`               |
| `usuarios.html`        | `templates/auth/usuarios.html`            |
| `form_usuario.html`    | `templates/auth/form_usuario.html`        |

> Crie a pasta `templates/auth/` se não existir.

---

## 3. Atualize o `__init__.py` / app principal

Adicione ao seu arquivo principal (onde cria o `app = Flask(__name__)`):

```python
from auth import auth_bp, login_required
from datetime import timedelta

app.secret_key = 'troque-por-uma-chave-secreta-longa-aqui'
app.permanent_session_lifetime = timedelta(days=7)

# Registre o blueprint de auth
app.register_blueprint(auth_bp)
```

---

## 4. Proteja todos os blueprints

Em **cada blueprint** (`plantio.py`, `colheita.py`, `custos.py`, etc.), adicione:

```python
from auth import login_required
from flask import session

def uid():
    return session['usuario_id']

# Adicione @login_required em todas as rotas
@plantio_bp.route('/')
@login_required
def index():
    db = get_db()
    # Filtre sempre por usuario_id via JOIN com talhoes
    plantios = db.execute("""
        SELECT p.*, t.nome as talhao_nome, t.area_ha
        FROM plantios p
        JOIN talhoes t ON t.id = p.talhao_id
        WHERE t.usuario_id = ?          -- ← isolamento
        ORDER BY p.safra DESC
    """, (uid(),)).fetchall()
    ...
```

---

## 5. Atualize o `base.html`

Adicione no topo da sidebar e do bottom nav o nome do usuário logado:

```html
<!-- No topo da sidebar, após .brand-sub -->
<div style="padding:12px 20px;border-bottom:1px solid rgba(255,255,255,.08);">
    <div style="font-size:12px;color:rgba(255,255,255,.5);">Logado como</div>
    <div style="font-size:14px;color:#fff;font-weight:600;">
        {{ session.get('usuario_nome', 'Usuário') }}
    </div>
    <a href="{{ url_for('auth.logout') }}"
       style="font-size:11px;color:rgba(255,255,255,.4);">
        <i class="bi bi-box-arrow-right me-1"></i>Sair
    </a>
</div>

<!-- Link de Usuários (só para admin) na sidebar -->
{% if session.get('usuario_tipo') == 'admin' %}
<a class="nav-link" href="{{ url_for('auth.usuarios') }}">
    <i class="bi bi-people"></i> Usuários
</a>
{% endif %}
```

---

## 6. Resete o banco de dados

Como adicionamos a coluna `usuario_id` nas tabelas, o banco precisa ser recriado:

```bash
python reset_db.py
```

Após o reset, o sistema cria automaticamente:
- **Login:** `admin@agrogest.com`
- **Senha:** `admin123`

> ⚠️ Troque a senha no primeiro login em "Minha Conta".

---

## 7. Como funciona o isolamento

```
Usuário A faz login → session['usuario_id'] = 1
  └── Talhões WHERE usuario_id = 1
      └── Plantios JOIN talhoes WHERE talhoes.usuario_id = 1
          └── Colheitas, Custos, Defensivos (via plantio → talhão → usuário)

Usuário B faz login → session['usuario_id'] = 2
  └── Talhões WHERE usuario_id = 2  ← dados completamente separados
```

Cada produtor **só enxerga e edita os próprios dados**. O admin vê tudo.

---

## 8. Fluxo de cadastro de novo produtor

1. Admin faz login
2. Vai em **Usuários → Novo Usuário**
3. Preenche nome, e-mail, senha e tipo = "Produtor"
4. O produtor recebe as credenciais e faz login
5. Ele começa a cadastrar seus próprios talhões/dados