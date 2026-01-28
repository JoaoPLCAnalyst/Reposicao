import streamlit as st
import json
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
# ESTILO DA TELA INICIAL
# -----------------------------------------------------------
st.markdown("""
<style>
.box {
    padding: 25px;
    border-radius: 12px;
    background-color: #f5f5f5;
    border: 1px solid #ddd;
    margin-bottom: 25px;
}
.title-center {
    text-align: center;
}
.pdf-button {
    display:inline-block;
    text-decoration: none !important;
    padding:8px 14px;
    border-radius:8px;
    background:#08365c;
    color:white !important;
    font-weight:600;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    margin-top:8px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# Função: botão estilizado para PDF (apenas para a exibição do catálogo do cliente)
# -------------------------
def pdf_button(url: str, label: str = "📘 Abrir manual"):
    """
    Exibe um botão estilizado que abre `url` em nova aba.
    Use apenas na página do cliente; não altera outros módulos.
    """
    if not url:
        st.info("Sem manual disponível.")
        return

    # Escapa a URL para segurança
    safe_url = urllib.parse.quote(url, safe=":/?&=#%")

    button_html = f"""
    <div>
      <a href="{safe_url}" target="_blank" rel="noopener noreferrer" class="pdf-button">
        {label}
      </a>
    </div>
    """
    st.markdown(button_html, unsafe_allow_html=True)


# -----------------------------------------------------------
# 0. TELA INICIAL — APARECE QUANDO NÃO TEM CLIENTE NA URL
# -----------------------------------------------------------

query_params = st.query_params
cliente_id = query_params.get("cliente", "")

if cliente_id == "":
    st.markdown("<h1 class='title-center'>🔧 Sistema de Catálogo WCE</h1>", unsafe_allow_html=True)
    st.markdown("<h3 class='title-center'>Escolha uma opção para continuar</h3>", unsafe_allow_html=True)
    st.write("")

    # ---------------- LOGIN ADMIN ----------------
    st.subheader("🔐 Área do Administrador")
    if st.button("Entrar como Admin"):
        st.switch_page("pages/admin.py")

    # ---------------- LOGIN CLIENTE ----------------
    st.subheader("👤 Acessar Catálogo")
    nome_cliente_digitado = st.text_input("Nome do Catálogo:")

    if st.button("Entrar como Cliente"):
        if nome_cliente_digitado.strip() == "":
            st.error("Digite o nome do Catálogo.")
        else:
            st.query_params["cliente"] = nome_cliente_digitado.lower().replace(" ", "_")
            st.rerun()

    st.stop()

# -----------------------------------------------------------
# 1. PROCESSAR CLIENTE
# -----------------------------------------------------------

dados_cliente = carregar_cliente(cliente_id)

if dados_cliente is None:
    st.error(f"❌ O cliente '{cliente_id}' não foi encontrado.")
    st.stop()

nome_cliente = dados_cliente.get("cliente", cliente_id)
contato_vendedor = dados_cliente.get("contato", "")

# Normalizar lista de peças do cliente
pecas_raw = dados_cliente.get("pecas", [])

codigos_pecas = []

for item in pecas_raw:
    if isinstance(item, dict):
        # caso venha algo como {"codigo": "123"}
        if "codigo" in item:
            codigos_pecas.append(item["codigo"])
        else:
            st.warning(f"Formato inesperado de peça no cliente '{nome_cliente}': {item}")
    else:
        # caso seja apenas o código como string
        codigos_pecas.append(item)


# -----------------------------------------------------------
# 2. CARREGAR BASE DE PRODUTOS DO DATABASE.JSON
# -----------------------------------------------------------
pecas_bd = carregar_database()

pecas = []
for codigo in codigos_pecas:
    if codigo in pecas_bd:
        item = pecas_bd[codigo].copy()
        item["codigo"] = codigo
        pecas.append(item)
    else:
        st.warning(f"⚠ Peça '{codigo}' não encontrada no database.")

# -----------------------------------------------------------
# 3. EXIBIR LISTA DE PEÇAS
# -----------------------------------------------------------
st.header(f"Reposição de Peças — {nome_cliente}")
st.subheader("Selecione as peças desejadas abaixo:")

pecas_selecionadas = []
quantidades = {}

st.subheader("📦 Lista de Peças Disponíveis")

for idx, peca in enumerate(pecas):
    st.markdown("---")
    # renderiza o componente visual da peça (mantém comportamento atual)
    render_peca(peca, idx, quantidades, pecas_selecionadas)

    # Ao exibir o catálogo para o cliente, se a peça tiver manual, mostramos um botão estilizado
    manual_url = peca.get("manual")
    if manual_url:
        pdf_button(manual_url, "📘 Abrir manual")

if not pecas_selecionadas:
    st.warning("Selecione pelo menos uma peça para continuar.")
    st.stop()

texto_itens = "\n".join([f"- {p['nome']} (código {p['codigo']}) — Quantidade: {quantidades[p['codigo']]}" for p in pecas_selecionadas])
mensagem = f"Pedido de Reposição de Peças\nCliente: {nome_cliente}\n\nItens Selecionados:\n{texto_itens}"
render_wpp_button(contato_vendedor, mensagem)
