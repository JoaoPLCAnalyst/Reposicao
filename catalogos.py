import streamlit as st
import json
import os
import urllib.parse

from utils.images import img_to_base64
from utils.clients import carregar_cliente
from utils.importDatabase import carregar_database
from components.header import render_header
from components.wpp_button import render_wpp_button
from components.peca import render_peca

# -----------------------------------------------------------
# CONFIG INICIAL
# -----------------------------------------------------------
st.set_page_config(page_title="WCE", layout="wide")

logo_base64 = img_to_base64("imagens/Logo.png")
render_header(logo_base64)

ADMIN_PASSWORD = "SV2024"

# -----------------------------------------------------------
# ESTILO (cards, botões, tipografia e miniaturas)
# -----------------------------------------------------------
st.markdown(
    """
    <style>
    /* Importa fonte moderna (fallbacks incluídos) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    :root{
      --card-bg: linear-gradient(180deg,#ffffff 0%,#f7fbff 100%);
      --accent: #0b5fff; /* cor do botão */
      --muted: #6b7280;
      --title: #08365c;
      --radius: 12px;
      --shadow: 0 8px 24px rgba(8,54,92,0.06);
    }

    body, .stApp {
      font-family: 'Inter', system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    }

    .card {
        display:flex;
        gap:16px;
        align-items:center;
        background: var(--card-bg);
        border-radius: var(--radius);
        padding: 14px;
        box-shadow: var(--shadow);
        transition: transform .18s ease, box-shadow .18s ease;
        overflow: hidden;
        min-height: 110px;
    }
    .card:hover { transform: translateY(-6px); box-shadow: 0 14px 40px rgba(8,54,92,0.10); }

    /* imagem à esquerda com corte preciso */
    .card-thumb {
        width: 160px;
        height: 100px;
        flex-shrink: 0;
        border-radius: 10px;
        overflow: hidden;
        background: linear-gradient(180deg,#eef6ff,#ffffff);
        border: 1px solid #e6eef8;
        display:flex;
        align-items:center;
        justify-content:center;
    }
    .card-thumb img {
        width: 100%;
        height: 100%;
        object-fit: cover; /* garante corte centralizado */
        display:block;
    }

    .card-body {
        flex:1;
        display:flex;
        flex-direction:column;
        justify-content:center;
        min-width:0;
    }
    .card-title {
        font-size: 18px;
        font-weight: 700;
        color: var(--title);
        line-height:1.05;
        margin-bottom:6px;
        white-space:nowrap;
        overflow:hidden;
        text-overflow:ellipsis;
    }
    .card-sub {
        color: var(--muted);
        font-size: 13px;
        margin-bottom:8px;
        display:block;
        white-space:nowrap;
        overflow:hidden;
        text-overflow:ellipsis;
    }
    .card-meta {
        color: #475569;
        font-size: 13px;
        margin-bottom:8px;
    }

    .card-actions {
        display:flex;
        gap:8px;
        align-items:center;
        margin-top:6px;
    }

    .open-btn {
        display:inline-block;
        text-decoration:none !important;
        padding:10px 16px;
        border-radius:10px;
        background: var(--accent);
        color:white !important;
        font-weight:700;
        font-size:14px;
        border: 0;
        box-shadow: 0 6px 18px rgba(11,95,255,0.14);
        transition: transform .12s, box-shadow .12s;
    }
    .open-btn:hover { transform: translateY(-2px); box-shadow: 0 12px 30px rgba(11,95,255,0.18); }

    /* badge opcional (ex: NOVO) */
    .badge {
        display:inline-block;
        background:#ff6b00;
        color:white;
        padding:6px 8px;
        border-radius:8px;
        font-weight:700;
        font-size:12px;
        margin-left:6px;
    }

    /* responsividade */
    @media (max-width: 900px) {
        .card { flex-direction:row; gap:12px; padding:12px; }
        .card-thumb { width:120px; height:80px; }
        .card-title { font-size:16px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------
# PASTA DE CLIENTES (lista / arquivos individuais)
# -----------------------------------------------------------
CLIENTES_DIR = "clientes"
os.makedirs(CLIENTES_DIR, exist_ok=True)

# -------------------------
# Helpers
# -------------------------
def listar_clientes():
    arquivos = [f for f in os.listdir(CLIENTES_DIR) if f.endswith(".json")]
    clientes = []
    for arq in arquivos:
        caminho = os.path.join(CLIENTES_DIR, arq)
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                data = json.load(f)
            clientes.append({
                "cliente": data.get("cliente", "Sem nome"),
                "qtd_pecas": len(data.get("pecas", []))
            })
        except Exception as e:
            st.error(f"Erro ao ler {arq}: {e}")
    return clientes

def carregar_cliente_por_slug(slug: str):
    slug = (slug or "").lower()
    for arq in os.listdir(CLIENTES_DIR):
        if not arq.endswith(".json"):
            continue
        caminho = os.path.join(CLIENTES_DIR, arq)
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                data = json.load(f)
            nome_slug = data.get("cliente", "").lower().replace(" ", "_")
            if nome_slug == slug:
                return data
        except Exception:
            continue
    return None

def abrir_catalogo_por_slug(slug: str):
    slug = slug or ""
    try:
        st.experimental_set_query_params(cliente=slug)
        try:
            st.experimental_rerun()
        except Exception:
            st.rerun()
        return
    except Exception:
        st.session_state["cliente_atual"] = slug
        try:
            st.rerun()
        except Exception:
            return

# -------------------------
# Inicializa session_state
# -------------------------
if "cliente_atual" not in st.session_state:
    st.session_state["cliente_atual"] = None

# Sincroniza query param com session_state quando possível
try:
    params = st.experimental_get_query_params()
    cliente_param = params.get("cliente", [None])[0]
    if cliente_param:
        st.session_state["cliente_atual"] = urllib.parse.unquote(cliente_param)
except Exception:
    try:
        qp = getattr(st, "query_params", {})
        val = qp.get("cliente", "")
        if isinstance(val, list):
            st.session_state["cliente_atual"] = val[0] if val else None
        else:
            st.session_state["cliente_atual"] = val or None
    except Exception:
        pass

# -----------------------------------------------------------
# Se cliente selecionado na sessão, delega para a página de catálogo
# -----------------------------------------------------------
if st.session_state["cliente_atual"]:
    cliente_slug = st.session_state["cliente_atual"]
    dados_cliente = carregar_cliente_por_slug(cliente_slug)

    if dados_cliente is None:
        st.warning("Cliente não encontrado. Verifique o nome ou volte à lista.")
        if st.button("⬅️ Voltar para a lista"):
            st.session_state["cliente_atual"] = None
            try:
                st.experimental_set_query_params()
            except Exception:
                try:
                    if hasattr(st, "query_params"):
                        st.query_params.clear()
                except Exception:
                    pass
            try:
                st.experimental_rerun()
            except Exception:
                st.rerun()
        st.stop()

    # Renderiza catálogo (comportamento original)
    nome_cliente = dados_cliente.get("cliente", cliente_slug)
    contato_vendedor = dados_cliente.get("contato", "")

    pecas_raw = dados_cliente.get("pecas", [])
    codigos_pecas = []
    for item in pecas_raw:
        if isinstance(item, dict):
            if "codigo" in item:
                codigos_pecas.append(item["codigo"])
            else:
                st.warning(f"Formato inesperado de peça no cliente '{nome_cliente}': {item}")
        else:
            codigos_pecas.append(item)

    pecas_bd = carregar_database()
    pecas = []
    for codigo in codigos_pecas:
        if codigo in pecas_bd:
            item = pecas_bd[codigo].copy()
            item["codigo"] = codigo
            pecas.append(item)
        else:
            st.warning(f"⚠ Peça '{codigo}' não encontrada no database.")

    # Cabeçalho do catálogo com botão Voltar
    col1, col2 = st.columns([1, 8])
    with col1:
        if st.button("⬅️ Voltar"):
            st.session_state["cliente_atual"] = None
            try:
                st.experimental_set_query_params()
            except Exception:
                try:
                    if hasattr(st, "query_params"):
                        st.query_params.clear()
                except Exception:
                    pass
            try:
                st.experimental_rerun()
            except Exception:
                st.rerun()
    with col2:
        st.header(f"Catalogo de Peças — {nome_cliente}")

    st.subheader("Selecione as peças desejadas abaixo:")

    pecas_selecionadas = []
    quantidades = {}

    st.subheader("📦 Lista de Peças Disponíveis")
    for idx, peca in enumerate(pecas):
        st.markdown("---")
        render_peca(peca, idx, quantidades, pecas_selecionadas)
        manual_url = peca.get("manual")
        if manual_url:
            safe_url = urllib.parse.quote(manual_url, safe=":/?&=#%")
            st.markdown(f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer" class="open-btn">📘 Abrir manual</a>', unsafe_allow_html=True)

    if not pecas_selecionadas:
        st.warning("Selecione pelo menos uma peça para continuar.")
        st.stop()

    texto_itens = "\n".join([f"- {p['nome']} (código {p['codigo']}) — Quantidade: {quantidades[p['codigo']]}" for p in pecas_selecionadas])
    mensagem = f"Pedido de Aquisição de Peças\nCliente: {nome_cliente}\n\nItens Selecionados:\n{texto_itens}"
    render_wpp_button(contato_vendedor, mensagem)

    st.stop()

# -----------------------------------------------------------
# Lista de catálogos (nova UI em cards)
# -----------------------------------------------------------
st.title("Catálogos Disponíveis")
st.write("Escolha um catálogo para visualizar os itens e fazer pedidos.")

clientes = listar_clientes()
if not clientes:
    st.warning("Nenhum catálogo cadastrado ainda.")
    st.stop()

# Carrega database para prévisualizações
pecas_bd = carregar_database()

# Grid responsivo: 3 colunas (mostra imagem do primeiro componente do catálogo)
cols = st.columns(3, gap="large")
for i, c in enumerate(clientes):
    col = cols[i % 3]
    slug = c["cliente"].lower().replace(" ", "_")
    with col:
        # tenta carregar dados completos do cliente para obter a primeira peça
        cliente_data = carregar_cliente_por_slug(slug)
        preview_img = None
        preview_title = ""
        if cliente_data:
            pecas_list = cliente_data.get("pecas", [])
            first = None
            if pecas_list:
                first = pecas_list[0]
            # resolve dados da primeira peça a partir do database
            if first:
                codigo_first = first.get("codigo") if isinstance(first, dict) else first
                detalhe = pecas_bd.get(codigo_first, {}) if pecas_bd else {}
                preview_img = detalhe.get("imagem") or (first.get("imagem") if isinstance(first, dict) else None)
                preview_title = detalhe.get("nome") or (first.get("nome") if isinstance(first, dict) else codigo_first)

        # Render do card com layout controlado por CSS acima
        # Construímos HTML manual para garantir posicionamento e corte da imagem
        if preview_img and isinstance(preview_img, str):
            # se for caminho local, converte para caminho relativo; st aceita ambos
            img_src = preview_img
            # monta HTML do card
            card_html = f"""
            <div class="card">
              <div class="card-thumb">
                <img src="{img_src}" alt="thumb" />
              </div>
              <div class="card-body">
                <div class="card-title">{c['cliente']}</div>
                <div class="card-meta">Itens no catálogo: <strong>{c['qtd_pecas']}</strong></div>
                <div class="card-sub">{preview_title}</div>
                <div class="card-actions">
                  <a class="open-btn" href="javascript:void(0)" id="open_{slug}">Abrir Catálogo</a>
                </div>
              </div>
            </div>
            """
        else:
            # fallback sem imagem
            initials = (c['cliente'][:2] or "CL").upper()
            card_html = f"""
            <div class="card">
              <div class="card-thumb">
                <div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:#6b7280;font-weight:700">{initials}</div>
              </div>
              <div class="card-body">
                <div class="card-title">{c['cliente']}</div>
                <div class="card-meta">Itens no catálogo: <strong>{c['qtd_pecas']}</strong></div>
              </div>
            </div>
            """

        st.markdown(card_html, unsafe_allow_html=True)

        # Botão funcional: usamos st.button abaixo para manter comportamento do Streamlit
        btn_open = st.button("Abrir Catálogo", key=f"open_{slug}")
        if btn_open:
            abrir_catalogo_por_slug(slug)

st.markdown("---")
