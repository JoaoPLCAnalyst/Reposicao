import streamlit as st
import json
import os
import urllib.parse

from utils.images import img_to_base64
from utils.importDatabase import carregar_database
from components.catalog_card import render_catalog_card
from components.wpp_button import render_wpp_button
from components.peca import render_peca

# --- CONFIG INICIAL ---
st.set_page_config(page_title="WCE Brasil", layout="wide")

# CSS para o Header Industrial e Layout
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .block-container { max-width: 550px; padding-top: 0rem; }
    header, footer { visibility: hidden; }
    .custom-header {
        background-color: #1a3930; margin: 0 -1rem 20px -1rem;
        padding: 30px 20px; display: flex; align-items: center; color: white;
    }
    .header-logo { width: 75px; margin-right: 15px; }
    .header-info { border-left: 1px solid rgba(255,255,255,0.3); padding-left: 15px; }
    .header-info h1 { font-size: 1.2rem; margin: 0; font-weight: 700; }
    .header-info p { font-size: 0.75rem; margin: 0; opacity: 0.8; }
    </style>
""", unsafe_allow_html=True)

CLIENTES_DIR = "clientes"

# --- HELPERS DE DADOS ---
def listar_clientes():
    if not os.path.exists(CLIENTES_DIR): return []
    arquivos = [f for f in os.listdir(CLIENTES_DIR) if f.endswith(".json")]
    clientes = []
    for arq in arquivos:
        try:
            with open(os.path.join(CLIENTES_DIR, arq), "r", encoding="utf-8") as f:
                data = json.load(f)
                clientes.append({"cliente": data.get("cliente", "Sem nome"), "qtd_pecas": len(data.get("pecas", []))})
        except: continue
    return clientes

def carregar_cliente_por_slug(slug: str):
    slug = (slug or "").lower()
    for arq in os.listdir(CLIENTES_DIR):
        try:
            with open(os.path.join(CLIENTES_DIR, arq), "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("cliente", "").lower().replace(" ", "_") == slug: return data
        except: continue
    return None

# --- GERENCIAMENTO DE NAVEGAÇÃO ---
if "cliente_atual" not in st.session_state:
    st.session_state["cliente_atual"] = None

# Sincroniza via URL
params = st.query_params
if "cliente" in params:
    st.session_state["cliente_atual"] = params["cliente"]

# --- TELA 1: LISTA DE CATÁLOGOS ---
if not st.session_state["cliente_atual"]:
    logo_b64 = img_to_base64("imagens/Logo.png")
    st.markdown(f"""
        <div class="custom-header">
            <img src="data:image/png;base64,{logo_b64}" class="header-logo">
            <div class="header-info">
                <h1>Catálogos Digitais</h1>
                <p>Soluções Industriais | WCE Brasil</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("Nossos Catálogos")
    
    clientes = listar_clientes()
    pecas_bd = carregar_database()

    for i, c in enumerate(clientes):
        slug = c["cliente"].lower().replace(" ", "_")
        cliente_data = carregar_cliente_por_slug(slug)
        
        # Lógica de preview para o card
        preview_img = None
        preview_title = ""
        if cliente_data and cliente_data.get("pecas"):
            first = cliente_data["pecas"][0]
            cod = first.get("codigo") if isinstance(first, dict) else first
            detalhe = pecas_bd.get(cod, {})
            preview_img = detalhe.get("imagem")
            preview_title = detalhe.get("nome", cod)

        # AQUI É ONDE O ERRO ACONTECIA - Agora os nomes batem 100%
        render_catalog_card(
            slug=slug,
            cliente_name=c["cliente"],
            qtd_pecas=c["qtd_pecas"],
            preview_img=preview_img,
            preview_title=preview_title,
            key_suffix=str(i),
            is_new=(i == 0) # Exemplo: o primeiro catálogo da lista ganha o badge "Novo"
        )

# --- TELA 2: CONTEÚDO DO CATÁLOGO ---
else:
    cliente_slug = st.session_state["cliente_atual"]
    dados_cliente = carregar_cliente_por_slug(cliente_slug)

    if st.button("⬅️ Voltar para a lista"):
        st.query_params.clear()
        st.session_state["cliente_atual"] = None
        st.rerun()

    if dados_cliente:
        nome_cliente = dados_cliente.get("cliente")
        st.header(f"Catálogo — {nome_cliente}")
        
        # Sua lógica original de carregar e renderizar peças
        pecas_raw = dados_cliente.get("pecas", [])
        pecas_bd = carregar_database()
        
        pecas_selecionadas = []
        quantidades = {}

        for idx, item in enumerate(pecas_raw):
            cod = item.get("codigo") if isinstance(item, dict) else item
            if cod in pecas_bd:
                peca = pecas_bd[cod].copy()
                peca["codigo"] = cod
                st.markdown("---")
                render_peca(peca, idx, quantidades, pecas_selecionadas)
        
        # Botão WhatsApp
        if pecas_selecionadas:
            msg = f"Olá, gostaria de solicitar orçamento para o cliente {nome_cliente}."
            render_wpp_button(dados_cliente.get("contato", ""), msg)