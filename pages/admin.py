import streamlit as st
import json
import os
from PIL import Image
import base64, requests

# ===========================
# CONFIGURAÇÕES
# ===========================
st.set_page_config(page_title="Criar Catálogo", page_icon="📘")

PASSWORD = st.secrets["ADMIN_PASSWORD"]

PRODUTOS_FILE = "database/database.json"
CLIENTES_DIR = "clientes"
IMAGENS_DIR = "imagens"

os.makedirs(CLIENTES_DIR, exist_ok=True)
os.makedirs(IMAGENS_DIR, exist_ok=True)

# ===========================
# FUNÇÕES AUXILIARES
# ===========================
def carregar_produtos():
    if not os.path.exists(PRODUTOS_FILE):
        return []
    with open(PRODUTOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_produtos(produtos):
    with open(PRODUTOS_FILE, "w", encoding="utf-8") as f:
        json.dump(produtos, f, indent=2, ensure_ascii=False)

def buscar_produto_por_codigo(produtos, codigo):
    for p in produtos:
        if p["codigo"] == codigo:
            return p
    return None

def github_upload(path, repo_path, message):
    """Envia QUALQUER arquivo ao GitHub."""
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GITHUB_REPO = st.secrets["GITHUB_REPO"]
    GITHUB_USER = st.secrets["GITHUB_USER"]
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{repo_path}"

    with open(path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode()

    get_file = requests.get(url, headers=headers)
    sha = get_file.json().get("sha") if get_file.status_code == 200 else None

    payload = {"message": message, "content": content_b64}
    if sha:
        payload["sha"] = sha

    return requests.put(url, headers=headers, json=payload)

# ===========================
# LOGIN
# ===========================
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Área Restrita")
    senha = st.text_input("Digite a senha:", type="password")

    if st.button("Entrar"):
        if senha == PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# ===========================
# SESSION STATE
# ===========================
defaults = {
    "cliente": "",
    "vendedor": "",
    "contato": "",
    "codigo_busca": "",
    "nome_novo": "",
    "descricao_novo": "",
    "pecas_cliente": [],
    "reset": False
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

def reset_form():
    for key in defaults:
        if key != "pecas_cliente":
            st.session_state[key] = ""
    st.session_state.pecas_cliente = []
    st.session_state.reset = False
    st.rerun()

if st.session_state.reset:
    reset_form()

# ===========================
# INTERFACE
# ===========================
st.title("📘 Criar Catálogo")

cliente = st.text_input("Nome do Cliente", key="cliente")
vendedor = st.text_input("Nome do Vendedor", key="vendedor")
contato = st.text_input("Contato do Vendedor", key="contato")

st.subheader("🔧 Adicionar Peças ao Catálogo")

produtos = carregar_produtos()

# ------------------------------
# BUSCAR PRODUTO EXISTENTE
# ------------------------------
codigo_busca = st.text_input("Código da Peça", key="codigo_busca")

if st.button("🔍 Buscar peça por código"):
    produto = buscar_produto_por_codigo(produtos, codigo_busca)
    if produto:
        st.success(f"Produto encontrado: {produto['nome']}")
        st.session_state.pecas_cliente.append(produto)
    else:
        st.warning("Produto não encontrado. Cadastre abaixo.")

# ------------------------------
# CADASTRAR NOVO PRODUTO
# ------------------------------
st.markdown("### ➕ Cadastrar Novo Produto")

nome_novo = st.text_input("Nome da Nova Peça", key="nome_novo")
descricao_novo = st.text_area("Descrição da Nova Peça", key="descricao_novo")
upload_novo = st.file_uploader("Imagem da Nova Peça", type=["png", "jpg", "jpeg"])
upload_pdf = st.file_uploader("Manual em PDF (opcional)", type=["pdf"])

if st.button("💾 Salvar Novo Produto"):
    if not codigo_busca:
        st.error("Digite o CÓDIGO do novo produto!")
    elif not nome_novo or not descricao_novo or upload_novo is None:
        st.error("Preencha todos os campos e envie a imagem!")
    else:
        # ---------------- SALVAR IMAGEM ----------------
        orig_ext = upload_novo.name.split(".")[-1].lower()
        if orig_ext == "jpeg":
            orig_ext = "jpg"

        img_filename = f"{codigo_busca}.{orig_ext}"
        img_path = os.path.join(IMAGENS_DIR, img_filename)

        # Abrir imagem
        image = Image.open(upload_novo)

        # Se for JPG, converter para RGB (evita erro com transparência)
        if orig_ext == "jpg" and image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        # Mapear extensão para formato Pillow
        format_map = {"jpg": "JPEG", "png": "PNG"}
        image_format = format_map.get(orig_ext)

        # Salvar com formato correto
        image.save(img_path, format=image_format)


        # ---------------- SALVAR PDF (se existir) ----------------
        manual_filename = None
        if upload_pdf is not None:
            manual_filename = f"{codigo_busca}.pdf"
            manual_path = os.path.join("pdfs", manual_filename)
            os.makedirs("pdfs", exist_ok=True)
            with open(manual_path, "wb") as f:
                f.write(upload_pdf.read())

            # Upload para GitHub
            resp_pdf = github_upload(
                manual_path,
                f"pdfs/{manual_filename}",
                f"Adicionando manual PDF do produto {codigo_busca}"
            )
            if resp_pdf.status_code in [200, 201]:
                st.success("📑 Manual PDF enviado ao GitHub!")
            else:
                st.error("Erro ao enviar manual PDF")
                st.code(resp_pdf.text)

        # ---------------- CRIAR PRODUTO ----------------
        novo_produto = {
            "codigo": codigo_busca,
            "nome": nome_novo,
            "descricao": descricao_novo,
            "imagem": f"imagens/{img_filename}"
        }
        if manual_filename:
            novo_produto["manual"] = f"pdfs/{manual_filename}"

        produtos.append(novo_produto)
        salvar_produtos(produtos)

        # Uploads GitHub da imagem e database.json
        resp_img = github_upload(
            img_path,
            f"imagens/{img_filename}",
            f"Adicionando imagem do produto {codigo_busca}"
        )
        if resp_img.status_code in [200, 201]:
            st.success("📸 Imagem enviada ao GitHub!")
        else:
            st.error("Erro ao enviar imagem")
            st.code(resp_img.text)

        resp_db = github_upload(
            PRODUTOS_FILE,
            "database/database.json",
            "Atualizando database.json após cadastrar produto"
        )
        if resp_db.status_code in [200, 201]:
            st.success("📘 database.json atualizado no GitHub!")
        else:
            st.error("Erro ao enviar database.json")
            st.code(resp_db.text)

        st.session_state.pecas_cliente.append(novo_produto)
        st.success("Produto cadastrado e adicionado ao catálogo!")

# ------------------------------
# LISTA DE PEÇAS + REMOVER ITEM
# ------------------------------
st.markdown("### 📄 Peças adicionadas ao catálogo")

if len(st.session_state.pecas_cliente) == 0:
    st.info("Nenhuma peça adicionada ainda.")
else:
    for i, p in enumerate(st.session_state.pecas_cliente):
        with st.container(border=True):
            st.write(f"**{p['nome']}** — {p['codigo']}")
            st.write(p["descricao"])

            col1, col2 = st.columns([5, 1])
            with col2:
                if st.button("🗑 Remover", key=f"remove_{i}"):
                    st.session_state.pecas_cliente.pop(i)
                    st.rerun()
        st.write("")

# ------------------------------
# SALVAR CATÁLOGO DO CLIENTE
# ------------------------------
if st.button("📁 Salvar Catálogo do Cliente"):
    if not cliente or not vendedor or not contato:
        st.error("Preencha os dados do cliente!")
        st.stop()

    if len(st.session_state.pecas_cliente) == 0:
        st.error("Adicione ao menos uma peça!")
        st.stop()

    data = {
        "cliente": cliente,
        "vendedor": vendedor,
        "contato": contato,
        "pecas": st.session_state.pecas_cliente
    }

    json_name = f"{cliente.replace(' ', '_').lower()}.json"
    json_path_local = f"{CLIENTES_DIR}/{json_name}"

    with open(json_path_local, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    st.success("Catálogo salvo localmente!")

    resp_json = github_upload(
        json_path_local,
        f"clientes/{json_name}",
        f"Salvando catálogo do cliente {cliente}"
    )

    if resp_json.status_code in [200, 201]:
        st.success("🎉 Catálogo enviado ao GitHub!")
    else:
        st.error("❌ Erro ao enviar catálogo")
        st.code(resp_json.text)

    st.success("🎯 Catálogo completo enviado ao GitHub!")

    st.session_state.reset = True
    st.rerun()
