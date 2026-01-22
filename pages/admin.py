import streamlit as st
import json
import os
from PIL import Image
import base64
import requests
import time

# ===========================
# CONFIGURAÇÕES
# ===========================
st.set_page_config(page_title="Criar Catálogo", page_icon="📘")

PASSWORD = st.secrets["ADMIN_PASSWORD"]

PRODUTOS_FILE = "database/database.json"
CLIENTES_DIR = "clientes"
IMAGENS_DIR = "imagens"
PDFS_DIR = "pdfs"

os.makedirs(CLIENTES_DIR, exist_ok=True)
os.makedirs(IMAGENS_DIR, exist_ok=True)
os.makedirs(PDFS_DIR, exist_ok=True)

DEFAULT_BRANCH = st.secrets.get("GITHUB_BRANCH", "main")

# ===========================
# FUNÇÕES AUXILIARES
# ===========================
def carregar_produtos():
    if not os.path.exists(PRODUTOS_FILE):
        return []
    with open(PRODUTOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_produtos(produtos):
    os.makedirs(os.path.dirname(PRODUTOS_FILE) or ".", exist_ok=True)
    with open(PRODUTOS_FILE, "w", encoding="utf-8") as f:
        json.dump(produtos, f, indent=2, ensure_ascii=False)

def buscar_produto_por_codigo(produtos, codigo):
    for p in produtos:
        if p.get("codigo") == codigo:
            return p
    return None

def github_raw_url(repo_path):
    user = st.secrets["GITHUB_USER"]
    repo = st.secrets["GITHUB_REPO"]
    branch = st.secrets.get("GITHUB_BRANCH", DEFAULT_BRANCH)
    return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{repo_path}"

def _resp_obj(status, text):
    class R:
        def __init__(self, status, text):
            self.status_code = status
            self._text = text
        def json(self):
            try:
                return json.loads(self._text)
            except Exception:
                return {"error": self._text}
        @property
        def text(self):
            return self._text
    return R(status, text)

def github_upload(path, repo_path, message, max_retries=2):
    """
    Upload file to GitHub repository contents API.
    Returns requests.Response or a compatible object on error.
    """
    token = st.secrets["GITHUB_TOKEN"].strip()
    user = st.secrets["GITHUB_USER"]
    repo = st.secrets["GITHUB_REPO"]
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # quick auth test
    try:
        auth_resp = requests.get("https://api.github.com/user", headers=headers, timeout=10)
    except Exception as e:
        return _resp_obj(500, f"Auth test failed: {e}")
    if auth_resp.status_code != 200:
        return _resp_obj(auth_resp.status_code, auth_resp.text)

    url = f"https://api.github.com/repos/{user}/{repo}/contents/{repo_path}"

    try:
        with open(path, "rb") as f:
            content_bytes = f.read()
    except Exception as e:
        return _resp_obj(500, f"File read failed: {e}")

    content_b64 = base64.b64encode(content_bytes).decode()

    # GET with retry on 500
    get_file = None
    for attempt in range(max_retries):
        try:
            get_file = requests.get(url, headers=headers, timeout=15)
        except Exception as e:
            if attempt + 1 < max_retries:
                time.sleep(1)
                continue
            else:
                return _resp_obj(500, f"GET failed: {e}")
        if get_file.status_code == 500 and attempt + 1 < max_retries:
            time.sleep(1)
            continue
        break

    sha = None
    if get_file is not None and get_file.status_code == 200:
        try:
            sha = get_file.json().get("sha")
        except Exception:
            sha = None

    payload = {"message": message, "content": content_b64}
    if sha:
        payload["sha"] = sha

    try:
        resp = requests.put(url, headers=headers, json=payload, timeout=30)
    except Exception as e:
        return _resp_obj(500, f"PUT failed: {e}")

    return resp

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
# INTERFACE PRINCIPAL
# ===========================
st.title("📘 Criar Catálogo")

cliente = st.text_input("Nome do Cliente", key="cliente")
vendedor = st.text_input("Nome do Vendedor", key="vendedor")
contato = st.text_input("Contato do Vendedor", key="contato")

st.subheader("🔧 Adicionar Peças ao Catálogo")

produtos = carregar_produtos()

# BUSCAR PRODUTO
codigo_busca = st.text_input("Código da Peça", key="codigo_busca")
if st.button("🔍 Buscar peça por código"):
    produto = buscar_produto_por_codigo(produtos, codigo_busca)
    if produto:
        st.success(f"Produto encontrado: {produto.get('nome')}")
        st.session_state.pecas_cliente.append(produto)
    else:
        st.warning("Produto não encontrado. Cadastre abaixo.")

# CADASTRAR NOVO PRODUTO
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
        # salvar imagem localmente e manter o fluxo original (salva local e faz upload ao GitHub como antes)
        orig_ext = upload_novo.name.split(".")[-1].lower()
        if orig_ext == "jpeg":
            orig_ext = "jpg"
        img_filename = f"{codigo_busca}.{orig_ext}"
        img_path = os.path.join(IMAGENS_DIR, img_filename)

        image = Image.open(upload_novo)
        if orig_ext == "jpg" and image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        format_map = {"jpg": "JPEG", "png": "PNG"}
        image_format = format_map.get(orig_ext, "PNG")
        image.save(img_path, format=image_format)

        # upload da imagem para o GitHub (mantendo exatamente o comportamento anterior)
        image_url = None
        resp_img = github_upload(img_path, f"imagens/{img_filename}", f"Adicionando imagem do produto {codigo_busca}")
        if getattr(resp_img, "status_code", None) in [200, 201]:
            # se quiser manter exatamente como antes, você pode optar por gravar o caminho local.
            # aqui mantemos compatibilidade: se upload OK, usamos a URL raw; caso contrário, mantemos caminho local.
            image_url = github_raw_url(f"imagens/{img_filename}")

        # SALVAR PDF LOCAL E UPLOAD AO GITHUB (apenas o PDF recebe URL pública)
        manual_url = None
        if upload_pdf is not None:
            manual_filename = f"{codigo_busca}.pdf"
            manual_path = os.path.join(PDFS_DIR, manual_filename)
            os.makedirs(PDFS_DIR, exist_ok=True)
            with open(manual_path, "wb") as f:
                f.write(upload_pdf.read())

            resp_pdf = github_upload(manual_path, f"pdfs/{manual_filename}", f"Adicionando manual PDF do produto {codigo_busca}")
            if getattr(resp_pdf, "status_code", None) in [200, 201]:
                manual_url = github_raw_url(f"pdfs/{manual_filename}")

        # montar objeto do produto mantendo imagens como antes
        novo_produto = {
            "codigo": codigo_busca,
            "nome": nome_novo,
            "descricao": descricao_novo,
        }
        # manter imagem como era: preferir comportamento anterior (local path) se desejar
        if image_url:
            # se preferir manter exatamente o fluxo anterior que gravava caminho local,
            # substitua a linha abaixo por: novo_produto["imagem"] = f"{IMAGENS_DIR}/{img_filename}"
            novo_produto["imagem"] = f"{IMAGENS_DIR}/{img_filename}"
        else:
            novo_produto["imagem"] = f"{IMAGENS_DIR}/{img_filename}"

        # manual: somente se upload do PDF foi bem sucedido
        if manual_url:
            novo_produto["manual"] = manual_url

        produtos.append(novo_produto)
        salvar_produtos(produtos)

        # enviar database.json ao GitHub (se desejar manter esse envio)
        resp_db = github_upload(PRODUTOS_FILE, "database/database.json", f"Atualizando database.json após cadastrar produto {codigo_busca}")
        if getattr(resp_db, "status_code", None) in [200, 201]:
            st.success("📘 database.json atualizado no GitHub!")
        else:
            st.warning("database.json salvo localmente; envio ao GitHub falhou ou não autorizado.")

        st.session_state.pecas_cliente.append(novo_produto)
        st.success("Produto cadastrado e adicionado ao catálogo!")

# LISTA DE PEÇAS
st.markdown("### 📄 Peças adicionadas ao catálogo")
if len(st.session_state.pecas_cliente) == 0:
    st.info("Nenhuma peça adicionada ainda.")
else:
    for i, p in enumerate(st.session_state.pecas_cliente):
        with st.container():
            st.write(f"**{p.get('nome')}** — {p.get('codigo')}")
            st.write(p.get("descricao", ""))
            if p.get("manual"):
                st.markdown(f"[📘 Manual em PDF]({p['manual']})")
            col1, col2 = st.columns([5, 1])
            with col2:
                if st.button("🗑 Remover", key=f"remove_{i}"):
                    st.session_state.pecas_cliente.pop(i)
                    st.rerun()
        st.write("")

# SALVAR CATÁLOGO DO CLIENTE
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

    resp_json = github_upload(json_path_local, f"clientes/{json_name}", f"Salvando catálogo do cliente {cliente}")
    if getattr(resp_json, "status_code", None) in [200, 201]:
        st.success("🎉 Catálogo enviado ao GitHub!")
    else:
        st.warning("Catálogo salvo localmente; envio ao GitHub falhou ou não autorizado.")

    st.session_state.reset = True
    st.rerun()
