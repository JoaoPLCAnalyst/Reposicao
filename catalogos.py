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
# PASTA DE CLIENTES (lista / arquivos individuais)
# -----------------------------------------------------------
CLIENTES_DIR = "clientes"
os.makedirs(CLIENTES_DIR, exist_ok=True)


# -------------------------
# Helpers para a lista de clientes
# -------------------------
def listar_clientes():
    arquivos = [f for f in os.listdir(CLIENTES_DIR) if f.endswith(".json")]
    clientes = []
    for arq in arquivos:
        caminho = os.path.join(CLIENTES_DIR, arq)
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                data = json.load(f)
            cliente = data.get("cliente", "Sem nome")
            vendedor = data.get("vendedor", "—")
            pecas = data.get("pecas", [])
            qtd_pecas = len(pecas)
            clientes.append({
                "cliente": cliente,
                "vendedor": vendedor,
                "qtd_pecas": qtd_pecas
            })
        except Exception as e:
            # não interrompe a listagem por um arquivo corrompido
            st.error(f"Erro ao ler {arq}: {e}")
    return clientes


def carregar_cliente_por_slug(slug: str):
    """Procura e retorna o conteúdo do arquivo do cliente cujo slug bate com `slug`."""
    slug = (slug or "").lower()
    for arq in os.listdir(CLIENTES_DIR):
        if not arq.endswith(".json"):
            continue
        caminho = os.path.join(CLIENTES_DIR, arq)
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                data = json.load(f)
            nome = data.get("cliente", "")
            nome_slug = nome.lower().replace(" ", "_")
            if nome_slug == slug:
                return data
        except Exception:
            continue
    return None


# -------------------------
# Lógica principal: detectar query param e decidir o que renderizar
# -------------------------
params = st.experimental_get_query_params()
cliente_param = params.get("cliente", [None])[0]
cliente_slug = cliente_param or ""

# Se houver cliente na query, renderiza o catálogo correspondente
if cliente_slug:
    # decodifica caso venha codificado
    cliente_slug = urllib.parse.unquote(cliente_slug)
    dados_cliente = carregar_cliente_por_slug(cliente_slug)

    if dados_cliente is None:
        st.warning("Cliente não encontrado. Verifique o nome ou volte à lista.")
        st.markdown('[⬅️ Voltar para a lista](?cliente=)', unsafe_allow_html=True)
        st.stop()

    # -----------------------------------------------------------
    # 1. PROCESSAR CLIENTE (comportamento original)
    # -----------------------------------------------------------
    nome_cliente = dados_cliente.get("cliente", cliente_slug)
    contato_vendedor = dados_cliente.get("contato", "")

    # Normalizar lista de peças do cliente
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
    # 3. EXIBIR LISTA DE PEÇAS (comportamento original)
    # -----------------------------------------------------------
    st.header(f"Reposição de Peças — {nome_cliente}")
    # botão de voltar para a lista de seleção do catálogo
    col1, col2 = st.columns([1, 8])
    with col1:
        if st.button("⬅️ Voltar"):
            # limpa o query param 'cliente' e provoca rerun
            st.set_query_params()
            st.rerun()
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

    st.markdown("")  # espaçamento
    st.markdown('[⬅️ Voltar para a lista](?cliente=)', unsafe_allow_html=True)
    st.stop()

# -----------------------------------------------------------
# Caso não haja cliente na query, mostra a lista de clientes
# -----------------------------------------------------------
st.title("Lista de Clientes Cadastrados")

clientes_dados = listar_clientes()

if not clientes_dados:
    st.warning("Nenhum cliente cadastrado ainda.")
    st.stop()

# ================================================
# TABELA RESUMIDA
# ================================================
st.subheader("📊 Visão Geral")
# st.dataframe não interpreta Markdown; mostramos tabela simples com st.table
tabela = []
for c in clientes_dados:
    tabela.append({
        "Cliente": c["cliente"],
        "Vendedor": c["vendedor"],
        "Itens no catálogo": c["qtd_pecas"]
    })
st.table(tabela)

st.markdown(
    "<style>td, th {padding: 10px}</style>",
    unsafe_allow_html=True
)

# ================================================
# CARDS DETALHADOS COM LINKS (apontam para ?cliente=slug)
# ================================================
st.subheader("🗂 Detalhes dos Clientes")

for c in clientes_dados:
    cliente_url = urllib.parse.quote(c["cliente"].lower().replace(" ", "_"))
    # link relativo correto (sem barra escapada)
    st.markdown(f"### 👤 <a href='?cliente={cliente_url}' target='_self'>{c['cliente']}</a>", unsafe_allow_html=True)
    st.write(f"**Vendedor:** {c['vendedor']}")
    st.write(f"**Itens no catálogo:** {c['qtd_pecas']}")
