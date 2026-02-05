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
# CONFIG & ESTILIZAÇÃO GLOBAL
# -----------------------------------------------------------
st.set_page_config(page_title="WCE - Catálogos Digitais", layout="wide")

# CSS para esconder o Streamlit padrão e criar o Header da imagem
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .block-container { max-width: 550px; padding-top: 0rem; }
    header, footer { visibility: hidden; }
    
    /* Header Verde Industrial */
    .custom-header {
        background-color: #1a3930;
        margin: 0 -1rem 20px -1rem;
        padding: 25px 20px;
        display: flex;
        align-items: center;
        color: white;
    }
    .header-logo { width: 75px; margin-right: 15px; }
    .header-text { border-left: 1px solid rgba(255,255,255,0.3); padding-left: 15px; }
    .header-text h1 { font-size: 1.25rem; margin: 0; font-weight: 700; }
    .header-text p { font-size: 0.8rem; margin: 0; opacity: 0.8; }

    /* Barra de Busca */
    .search-container {
        background: #f1f3f4;
        border-radius: 25px;
        padding: 10px 20px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        color: #666;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# TODAS AS SUAS FUNÇÕES ORIGINAIS (PRESERVADAS)
# -----------------------------------------------------------
CLIENTES_DIR = "clientes"
os.makedirs(CLIENTES_DIR, exist_ok=True)

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
        if not arq.endswith(".json"): continue
        caminho = os.path.join(CLIENTES_DIR, arq)
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                data = json.load(f)
                nome_slug = data.get("cliente", "").lower().replace(" ", "_")
                if nome_slug == slug: return data
        except Exception: continue
    return None

# -----------------------------------------------------------
# NAVEGAÇÃO & QUERY PARAMS
# -----------------------------------------------------------
if "cliente_atual" not in st.session_state:
    st.session_state["cliente_atual"] = None

# Sincronização com a URL
params = st.query_params
if "cliente" in params:
    st.session_state["cliente_atual"] = params["cliente"]

# -----------------------------------------------------------
# LÓGICA DE TELAS (LISTA vs DETALHE)
# -----------------------------------------------------------

# --- TELA 2: SE O CLIENTE ESTIVER SELECIONADO ---
if st.session_state["cliente_atual"]:
    cliente_slug = st.session_state["cliente_atual"]
    dados_cliente = carregar_cliente_por_slug(cliente_slug)

    if dados_cliente is None:
        st.warning("Catálogo não encontrado.")
        if st.button("⬅️ Voltar"):
            st.query_params.clear()
            st.session_state["cliente_atual"] = None
            st.rerun()
        st.stop()

    # Botão de Voltar Minimalista
    if st.button("⬅️ Voltar para a lista"):
        st.query_params.clear()
        st.session_state["cliente_atual"] = None
        st.rerun()

    # Lógica de renderização das peças (Sua lógica original completa)
    nome_cliente = dados_cliente.get("cliente", cliente_slug)
    contato_vendedor = dados_cliente.get("contato", "")
    pecas_raw = dados_cliente.get("pecas", [])
    
    pecas_bd = carregar_database()
    pecas = []
    for item in pecas_raw:
        cod = item.get("codigo") if isinstance(item, dict) else item
        if cod in pecas_bd:
            peca_data = pecas_bd[cod].copy()
            peca_data["codigo"] = cod
            pecas.append(peca_data)

    st.header(f"Catálogo — {nome_cliente}")
    
    pecas_selecionadas = []
    quantidades = {}

    for idx, peca in enumerate(pecas):
        st.markdown("---")
        render_peca(peca, idx, quantidades, pecas_selecionadas)
        if peca.get("manual"):
            st.markdown(f' <a href="{peca.get("manual")}" target="_blank">📘 Manual Técnico</a>', unsafe_allow_html=True)

    if pecas_selecionadas:
        texto_itens = "\n".join([f"- {p['nome']} ({p['codigo']}) — Qtd: {quantidades[p['codigo']]}" for p in pecas_selecionadas])
        mensagem = f"Pedido de Peças\nCliente: {nome_cliente}\n\nItens:\n{texto_itens}"
        render_wpp_button(contato_vendedor, mensagem)

# --- TELA 1: LISTA DE CARD (TELA INICIAL) ---
else:
    # Header Customizado (O da Imagem)
    logo_b64 = img_to_base64("imagens/Logo.png")
    st.markdown(f"""
        <div class="custom-header">
            <img src="data:image/png;base64,{logo_b64}" class="header-logo">
            <div class="header-text">
                <h1>Catálogos Digitais</h1>
                <p>Soluções Industriais | WCE Brasil</p>
            </div>
        </div>
        <div class="search-container">
            <span>🔍 Buscar produto ou catálogo</span>
            <span>🔍</span>
        </div>
        <h2 style="color:#1a1a1a; font-weight:800; font-size:1.5rem;">Nossos Catálogos</h2>
    """, unsafe_allow_html=True)

    clientes = listar_clientes()
    pecas_bd = carregar_database()

    if not clientes:
        st.warning("Nenhum catálogo disponível.")
    else:
        # Loop para renderizar os cards usando a lógica de busca de preview que você criou
        for i, c in enumerate(clientes):
            slug = c["cliente"].lower().replace(" ", "_")
            
            # Buscando o preview (Sua lógica original)
            cliente_data = carregar_cliente_por_slug(slug)
            preview_img = None
            preview_title = ""
            
            if cliente_data and cliente_data.get("pecas"):
                first = cliente_data["pecas"][0]
                cod = first.get("codigo") if isinstance(first, dict) else first
                detalhe = pecas_bd.get(cod, {})
                preview_img = detalhe.get("imagem")
                preview_title = detalhe.get("nome", cod)

            # Renderiza o card visual
            render_catalog_card(
                slug=slug,
                cliente_name=c["cliente"],
                qtd_pecas=c["qtd_pecas"],
                preview_img=preview_img,
                preview_title=preview_title,
                key_suffix=str(i)
            )