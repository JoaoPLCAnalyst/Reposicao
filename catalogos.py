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
from components.catalog_card import render_catalog_card

# -----------------------------------------------------------
# CONFIG INICIAL
# -----------------------------------------------------------
st.set_page_config(page_title="WCE", layout="wide")

logo_base64 = img_to_base64("imagens/Logo.png")
render_header(logo_base64)

ADMIN_PASSWORD = "SV2024"

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
# Lista de catálogos (nova UI em cards) usando componente separado
# -----------------------------------------------------------
st.title("Catálogos Disponíveis")
st.write("Escolha um catálogo para visualizar os itens e fazer pedidos.")

clientes = listar_clientes()
if not clientes:
    st.warning("Nenhum catálogo cadastrado ainda.")
    st.stop()

# Carrega database para prévisualizações
pecas_bd = carregar_database()

cols = st.columns(3, gap="large")
for i, c in enumerate(clientes):
    col = cols[i % 3]
    slug = c["cliente"].lower().replace(" ", "_")
    with col:
        # resolve preview (primeira peça) a partir do cliente e database
        cliente_data = carregar_cliente_por_slug(slug)
        preview_img = None
        preview_title = ""
        if cliente_data:
            pecas_list = cliente_data.get("pecas", [])
            if pecas_list:
                first = pecas_list[0]
                codigo_first = first.get("codigo") if isinstance(first, dict) else first
                detalhe = pecas_bd.get(codigo_first, {}) if pecas_bd else {}
                preview_img = detalhe.get("imagem") or (first.get("imagem") if isinstance(first, dict) else None)
                preview_title = detalhe.get("nome") or (first.get("nome") if isinstance(first, dict) else codigo_first)

        # usa o componente para renderizar o card; retorna True se o botão interno foi clicado
        clicked = render_catalog_card(
            slug=slug,
            cliente_name=c["cliente"],
            qtd_pecas=c["qtd_pecas"],
            preview_img=preview_img,
            preview_title=preview_title,
            key_suffix=str(i)
        )
        if clicked:
            abrir_catalogo_por_slug(slug)

st.markdown("---")
