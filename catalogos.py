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


# -----------------------------------------------------------
# ESTILO (cards, botões e miniaturas)
# -----------------------------------------------------------
st.markdown(
    """
    <style>
    .card {
        background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 6px 18px rgba(8, 54, 92, 0.08);
        transition: transform .12s ease-in-out;
        height: 100%;
    }
    .card:hover { transform: translateY(-4px); }
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
    }
    .preview {
        border-radius:12px;
        padding:14px;
        background:linear-gradient(180deg,#ffffff,#fbfdff);
        box-shadow: 0 8px 24px rgba(8,54,92,0.06);
        margin-top:18px;
    }
    .thumb {
        width:120px;
        height:90px;
        object-fit:cover;
        border-radius:8px;
        border:1px solid #e6eef8;
    }
    .thumb-title { font-size:13px; font-weight:600; color:#08365c; margin-top:6px; }
    .thumb-sub { font-size:12px; color:#6b7280; }
    .grid { gap: 18px; }
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
                "vendedor": data.get("vendedor", "—"),
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
if "preview_cliente" not in st.session_state:
    st.session_state["preview_cliente"] = None

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
        st.header(f"Reposição de Peças — {nome_cliente}")

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
    mensagem = f"Pedido de Reposição de Peças\nCliente: {nome_cliente}\n\nItens Selecionados:\n{texto_itens}"
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

# Grid responsivo: 3 colunas
cols = st.columns(3, gap="large")
for i, c in enumerate(clientes):
    col = cols[i % 3]
    slug = c["cliente"].lower().replace(" ", "_")
    with col:
        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">{c['cliente']}</div>
                <div class="card-sub">Vendedor: <strong>{c['vendedor']}</strong></div>
                <div class="card-meta">Itens no catálogo: <strong>{c['qtd_pecas']}</strong></div>
            """,
            unsafe_allow_html=True,
        )

        # Botões: Pré-visualizar e Abrir Catálogo
        btn_preview = st.button("Pré‑visualizar", key=f"preview_{slug}")
        btn_open = st.button("Abrir Catálogo", key=f"open_{slug}")

        if btn_preview:
            st.session_state["preview_cliente"] = slug
            # tenta sincronizar query param também (não obrigatório)
            try:
                st.experimental_set_query_params(cliente=slug)
            except Exception:
                pass
            try:
                st.rerun()
            except Exception:
                pass

        if btn_open:
            abrir_catalogo_por_slug(slug)

        # link alternativo (apenas visual)
        cliente_url = urllib.parse.quote(slug)
        st.markdown(f'<div style="margin-top:8px;"><a href="?cliente={cliente_url}" class="open-btn" style="background:#0b5fa5">Abrir via link</a></div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------------------------------
# Painel de pré-visualização (quando definido)
# -----------------------------------------------------------
if st.session_state.get("preview_cliente"):
    preview_slug = st.session_state["preview_cliente"]
    preview_data = carregar_cliente_por_slug(preview_slug)
    if preview_data:
        st.markdown("<div class='preview'>", unsafe_allow_html=True)
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.markdown(f"### Pré‑visualização — {preview_data.get('cliente','—')}")
            st.write(f"**Vendedor:** {preview_data.get('vendedor','—')}")
            st.write(f"**Total de itens:** {len(preview_data.get('pecas', []))}")
            st.markdown("---")

            # mostra até 6 miniaturas com nome e código
            pecas_preview = preview_data.get("pecas", [])[:6]
            thumbs_cols = st.columns(len(pecas_preview) if pecas_preview else 1)
            for idx, p in enumerate(pecas_preview):
                pc = pecas_preview[idx]
                # resolve dados da peça a partir do database se for código
                if isinstance(pc, dict):
                    codigo = pc.get("codigo") or pc.get("codigo", "")
                else:
                    codigo = pc
                detalhe = pecas_bd.get(codigo, {}) if pecas_bd else {}
                nome = detalhe.get("nome") or (pc.get("nome") if isinstance(pc, dict) else codigo)
                imagem = detalhe.get("imagem") or (pc.get("imagem") if isinstance(pc, dict) else None)

                with thumbs_cols[idx]:
                    if imagem:
                        try:
                            st.image(imagem, width=120)
                        except Exception:
                            st.markdown(f"<div style='width:120px;height:90px;border-radius:8px;background:#f1f5f9;display:flex;align-items:center;justify-content:center;color:#6b7280;border:1px solid #e6eef8'>{codigo}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='width:120px;height:90px;border-radius:8px;background:#f1f5f9;display:flex;align-items:center;justify-content:center;color:#6b7280;border:1px solid #e6eef8'>{codigo}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='thumb-title'>{nome}</div><div class='thumb-sub'>{codigo}</div>", unsafe_allow_html=True)

        with col_b:
            if st.button("Abrir Catálogo", key=f"preview_open_{preview_slug}"):
                abrir_catalogo_por_slug(preview_slug)
            if st.button("Fechar Pré‑visualização", key=f"preview_close_{preview_slug}"):
                st.session_state["preview_cliente"] = None
                try:
                    st.experimental_set_query_params()
                except Exception:
                    pass
                try:
                    st.rerun()
                except Exception:
                    pass

        st.markdown("</div>", unsafe_allow_html=True)
