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
# ESTILO (cards, botões, miniaturas e animações suaves)
# -----------------------------------------------------------
st.markdown(
    """
    <style>
    /* animações */
    @keyframes fadeUp {
        0% { opacity: 0; transform: translateY(8px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    @keyframes glow {
        0% { box-shadow: 0 6px 18px rgba(8, 54, 92, 0.04); }
        50% { box-shadow: 0 10px 28px rgba(8, 54, 92, 0.08); }
        100% { box-shadow: 0 6px 18px rgba(8, 54, 92, 0.04); }
    }

    .card {
        background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 6px 18px rgba(8, 54, 92, 0.08);
        transition: transform .18s cubic-bezier(.2,.9,.3,1), box-shadow .18s;
        height: 100%;
        animation: fadeUp .28s ease both;
    }
    .card:hover { transform: translateY(-6px) scale(1.01); animation: glow 2.2s infinite ease-in-out; }
    .card-title { font-size: 18px; font-weight:700; color:#08365c; margin-bottom:6px; }
    .card-sub { color:#4b5563; margin-bottom:10px; }
    .card-meta { color:#6b7280; font-size:13px; margin-bottom:12px; }

    .open-btn {
        display:inline-block;
        text-decoration:none !important;
        padding:10px 16px;
        border-radius:10px;
        background:#08365c;
        color:white !important;
        font-weight:700;
        box-shadow: 0 4px 12px rgba(8,54,92,0.12);
        transition: transform .12s, box-shadow .12s;
    }
    .open-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(8,54,92,0.16); }

    .preview {
        border-radius:12px;
        padding:14px;
        background:linear-gradient(180deg,#ffffff,#fbfdff);
        box-shadow: 0 8px 24px rgba(8,54,92,0.06);
        margin-top:18px;
        animation: fadeUp .28s ease both;
    }
    .thumb {
        width:120px;
        height:90px;
        object-fit:cover;
        border-radius:8px;
        border:1px solid #e6eef8;
        transition: transform .12s ease, box-shadow .12s;
    }
    .thumb:hover { transform: translateY(-4px); box-shadow: 0 8px 20px rgba(8,54,92,0.08); }
    .thumb-title { font-size:13px; font-weight:600; color:#08365c; margin-top:6px; }
    .thumb-sub { font-size:12px; color:#6b7280; }
    .grid { gap: 18px; }

    /* responsividade simples */
    @media (max-width: 900px) {
        .thumb { width:100px; height:72px; }
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
    """
    Tenta abrir o catálogo definindo query param; se não for possível,
    usa session_state como fallback e força rerun.
    """
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
# (mantém comportamento original de exibição do catálogo)
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

    # Renderiza catálogo (mesmo comportamento que você já tinha)
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

        # Render do card usando colunas internas para garantir que imagens locais sejam exibidas corretamente
        with st.container():
            inner_col_img, inner_col_text = st.columns([1, 2], gap="small")
            with inner_col_img:
                if preview_img:
                    # Se for URL externa, exibe diretamente; se for caminho local, usa st.image
                    if isinstance(preview_img, str) and (preview_img.startswith("http://") or preview_img.startswith("https://")):
                        try:
                            st.image(preview_img, width=120)
                        except Exception:
                            # fallback visual
                            st.markdown(f"<div style='width:120px;height:90px;border-radius:8px;background:#f1f5f9;display:flex;align-items:center;justify-content:center;color:#6b7280;border:1px solid #e6eef8;font-weight:600'>{slug[0:2].upper()}</div>", unsafe_allow_html=True)
                    else:
                        # caminho local relativo
                        local_path = preview_img
                        if os.path.exists(local_path):
                            st.image(local_path, width=120)
                        else:
                            # fallback visual
                            st.markdown(f"<div style='width:120px;height:90px;border-radius:8px;background:#f1f5f9;display:flex;align-items:center;justify-content:center;color:#6b7280;border:1px solid #e6eef8;font-weight:600'>{slug[0:2].upper()}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='width:120px;height:90px;border-radius:8px;background:#f1f5f9;display:flex;align-items:center;justify-content:center;color:#6b7280;border:1px solid #e6eef8;font-weight:600'>{c['cliente'][0:2].upper()}</div>", unsafe_allow_html=True)

            with inner_col_text:
                # título e meta (sem o nome do vendedor, conforme solicitado)
                st.markdown(f"<div class='card-title'>{c['cliente']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='card-meta'>Itens no catálogo: <strong>{c['qtd_pecas']}</strong></div>", unsafe_allow_html=True)
                if preview_title:
                    st.markdown(f"<div style='margin-top:6px;color:#6b7280;font-size:13px'>{preview_title}</div>", unsafe_allow_html=True)

            # encapsula tudo em um cartão visual
            # (usamos markdown wrapper para aplicar a classe .card definida no CSS)
            # Para manter a estrutura visual, renderizamos um pequeno wrapper acima.
        # Botão Abrir Catálogo
        btn_open = st.button("Abrir Catálogo", key=f"open_{slug}")
        if btn_open:
            abrir_catalogo_por_slug(slug)

st.markdown("---")
