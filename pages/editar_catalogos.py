import streamlit as st
import json
import os
from PIL import Image
import base64
import requests
import time

st.set_page_config(page_title="Editar Catálogo", page_icon="📘")

CATALOGOS_DIR = "clientes"
IMAGENS_DIR = "imagens"
PDFS_DIR = "pdfs"
PRODUTOS_FILE = "database/database.json"
DEFAULT_BRANCH = st.secrets.get("GITHUB_BRANCH", "main")

# --------------------------------------------------
# Funções auxiliares
# --------------------------------------------------
def carregar_catalogo(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_catalogo(caminho, dados):
    os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def carregar_produtos():
    if not os.path.exists(PRODUTOS_FILE):
        return []
    with open(PRODUTOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_produtos(produtos):
    os.makedirs(os.path.dirname(PRODUTOS_FILE) or ".", exist_ok=True)
    with open(PRODUTOS_FILE, "w", encoding="utf-8") as f:
        json.dump(produtos, f, indent=2, ensure_ascii=False)

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

def github_raw_url(repo_path):
    """Monta a URL pública do GitHub para abrir direto no navegador (usa branch configurável)."""
    user = st.secrets["GITHUB_USER"]
    repo = st.secrets["GITHUB_REPO"]
    branch = st.secrets.get("GITHUB_BRANCH", DEFAULT_BRANCH)
    return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{repo_path}"

def github_upload(path, repo_path, message, max_retries=2):
    """Envia QUALQUER arquivo ao GitHub (API Contents)."""
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

# --------------------------------------------------
# Página
# --------------------------------------------------
st.header("🛠 Editar Catálogos Existentes")

if not os.path.exists(CATALOGOS_DIR):
    st.warning(f"A pasta '{CATALOGOS_DIR}' não existe.")
    st.stop()

arquivos = [f for f in os.listdir(CATALOGOS_DIR) if f.endswith(".json")]
if len(arquivos) == 0:
    st.warning("Nenhum catálogo encontrado na pasta.")
    st.stop()

nome_catalogo = st.selectbox("Selecione um catálogo:", arquivos)
caminho_catalogo = os.path.join(CATALOGOS_DIR, nome_catalogo)

catalogo = carregar_catalogo(caminho_catalogo)

if "pecas" not in catalogo:
    st.error("Esse catálogo não possui o formato esperado (sem 'pecas').")
    st.stop()

catalogo.setdefault("cliente", "")

cliente_edit = st.text_input("Nome do cliente:", value=catalogo["cliente"])

st.markdown("---")
st.subheader("Peças do catálogo")

remover_indices = []

for i, p in enumerate(catalogo["pecas"]):
    with st.expander(f"{p.get('nome', 'Sem nome')} — {p.get('codigo', '')}", expanded=False):
        form_key = f"form_peca_{i}"
        with st.form(key=form_key):
            nome_input = st.text_input("Nome:", value=p.get("nome", ""), key=f"nome_{i}")
            desc_input = st.text_area("Descrição:", value=p.get("descricao", ""), key=f"desc_{i}")

            st.write("Imagem atual:")
            imagem_atual = p.get("imagem", None)
            if imagem_atual and os.path.exists(imagem_atual):
                st.image(imagem_atual, width=200)
            else:
                st.info("Imagem não encontrada localmente.")

            if p.get("manual"):
                st.markdown(f"[📘 Manual atual em PDF]({p['manual']})")

            nova_img = st.file_uploader("Nova imagem (opcional)", type=["png", "jpg", "jpeg"], key=f"img_{i}")
            nova_pdf = st.file_uploader("Novo manual em PDF (opcional)", type=["pdf"], key=f"pdf_{i}")

            confirmar = st.form_submit_button("Confirmar alterações")
            remover = st.form_submit_button("Remover peça")

            if remover:
                remover_indices.append(i)
                st.success("Peça marcada para remoção. Clique em 'Salvar catálogo' para confirmar.")
                st.rerun()

            if confirmar:
                # Atualiza campos locais
                catalogo["pecas"][i]["nome"] = nome_input
                catalogo["pecas"][i]["descricao"] = desc_input

                img_filename = None
                manual_filename = None
                manual_url = None

                # Nova imagem: salva localmente e faz upload (mas mantém caminho local no catálogo)
                if nova_img is not None:
                    ext = nova_img.name.split(".")[-1].lower()
                    if ext == "jpeg":
                        ext = "jpg"
                    img_filename = f"{p.get('codigo', i)}.{ext}"
                    img_path = os.path.join(IMAGENS_DIR, img_filename)

                    os.makedirs(IMAGENS_DIR, exist_ok=True)

                    image = Image.open(nova_img)
                    if ext == "jpg" and image.mode in ("RGBA", "P"):
                        image = image.convert("RGB")
                    format_map = {"jpg": "JPEG", "png": "PNG"}
                    image_format = format_map.get(ext)
                    image.save(img_path, format=image_format)

                    # Mantém caminho local no catálogo (conforme solicitado)
                    catalogo["pecas"][i]["imagem"] = f"{IMAGENS_DIR}/{img_filename}"

                    # Faz upload ao GitHub (mantendo comportamento anterior)
                    resp_img = github_upload(
                        img_path,
                        f"imagens/{img_filename}",
                        f"Atualizando imagem da peça {p.get('codigo', i)}"
                    )
                    if getattr(resp_img, "status_code", None) in [200, 201]:
                        st.success("📸 Imagem atualizada no GitHub!")
                    else:
                        st.error("Erro ao atualizar imagem no GitHub")
                        st.code(getattr(resp_img, "text", str(resp_img)))

                # Novo PDF: salva localmente, tenta upload e só grava URL pública se upload OK
                if nova_pdf is not None:
                    manual_filename = f"{p.get('codigo', i)}.pdf"
                    manual_path = os.path.join(PDFS_DIR, manual_filename)
                    os.makedirs(PDFS_DIR, exist_ok=True)
                    with open(manual_path, "wb") as f:
                        f.write(nova_pdf.read())

                    resp_pdf = github_upload(
                        manual_path,
                        f"pdfs/{manual_filename}",
                        f"Atualizando manual PDF da peça {p.get('codigo', i)}"
                    )
                    if getattr(resp_pdf, "status_code", None) in [200, 201]:
                        manual_url = github_raw_url(f"pdfs/{manual_filename}")
                        catalogo["pecas"][i]["manual"] = manual_url
                        st.success("📑 Manual PDF atualizado no GitHub!")
                    else:
                        st.error("Erro ao atualizar manual PDF no GitHub")
                        st.code(getattr(resp_pdf, "text", str(resp_pdf)))

                # Atualiza também o database/local produtos (mantendo imagem como caminho local)
                produtos = carregar_produtos()
                for prod in produtos:
                    if prod.get("codigo") == p.get("codigo"):
                        prod["nome"] = nome_input
                        prod["descricao"] = desc_input
                        if img_filename:
                            prod["imagem"] = f"{IMAGENS_DIR}/{img_filename}"
                        if manual_filename and manual_url:
                            prod["manual"] = manual_url
                        break
                salvar_produtos(produtos)

                # Tenta atualizar database.json no GitHub (se falhar, mantemos local)
                resp_db = github_upload(
                    PRODUTOS_FILE,
                    "database/database.json",
                    f"Atualizando produto {p.get('codigo')} no database.json"
                )
                if getattr(resp_db, "status_code", None) in [200, 201]:
                    st.success("📘 database.json atualizado no GitHub!")
                else:
                    st.warning("database.json salvo localmente; envio ao GitHub falhou ou não autorizado.")

                st.success("Alterações aplicadas localmente. Clique em 'Salvar catálogo' para gravar no arquivo.")
                st.rerun()

# --------------------------------------------------
# Remover peças
# --------------------------------------------------
if remover_indices:
    for idx in sorted(remover_indices, reverse=True):
        p_to_remove = catalogo["pecas"][idx]
        codigo_removido = p_to_remove.get("codigo")
        catalogo["pecas"].pop(idx)

        produtos = carregar_produtos()
        produtos = [prod for prod in produtos if prod.get("codigo") != codigo_removido]
        salvar_produtos(produtos)

        resp_db = github_upload(
            PRODUTOS_FILE,
            "database/database.json",
            f"Removendo produto {codigo_removido} do database.json"
        )
        if getattr(resp_db, "status_code", None) in [200, 201]:
            st.success("📘 database.json atualizado no GitHub!")
        else:
            st.warning("database.json salvo localmente; envio ao GitHub falhou ou não autorizado.")

    st.success("Peças removidas localmente. Clique em 'Salvar catálogo' para gravar no arquivo.")
    st.rerun()

st.markdown("---")
st.subheader("Adicionar nova peça ao catálogo")

codigo_novo = st.text_input("Código da peça (nova):", key="codigo_novo")
nome_novo = st.text_input("Nome da peça (nova):", key="nome_novo")
desc_novo = st.text_area("Descrição (nova):", key="desc_novo")
img_nova = st.file_uploader("Imagem (nova):", type=["png", "jpg", "jpeg"], key="img_nova")
pdf_novo = st.file_uploader("Manual em PDF (novo):", type=["pdf"], key="pdf_novo")

if st.button("Adicionar peça"):
    if not codigo_novo or not nome_novo or not img_nova:
        st.error("Preencha todos os campos e envie uma imagem.")
    else:
        # ---------------- SALVAR IMAGEM ----------------
        ext = img_nova.name.split(".")[-1].lower()
        if ext == "jpeg":
            ext = "jpg"

        img_filename = f"{codigo_novo}.{ext}"
        img_path = os.path.join(IMAGENS_DIR, img_filename)

        os.makedirs(IMAGENS_DIR, exist_ok=True)

        image = Image.open(img_nova)
        if ext == "jpg" and image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        format_map = {"jpg": "JPEG", "png": "PNG"}
        image_format = format_map.get(ext)
        image.save(img_path, format=image_format)

        # ---------------- SALVAR PDF (se existir) ----------------
        manual_filename = None
        manual_url = None
        if pdf_novo is not None:
            manual_filename = f"{codigo_novo}.pdf"
            manual_path = os.path.join(PDFS_DIR, manual_filename)
            os.makedirs(PDFS_DIR, exist_ok=True)
            with open(manual_path, "wb") as f:
                f.write(pdf_novo.read())

            resp_pdf = github_upload(
                manual_path,
                f"pdfs/{manual_filename}",
                f"Adicionando manual PDF da peça {codigo_novo}"
            )
            if getattr(resp_pdf, "status_code", None) in [200, 201]:
                manual_url = github_raw_url(f"pdfs/{manual_filename}")
                st.success("📑 Manual PDF enviado ao GitHub!")
            else:
                st.error("Erro ao enviar manual PDF")
                st.code(getattr(resp_pdf, "text", str(resp_pdf)))

        # ---------------- CRIAR PEÇA ----------------
        nova_peca = {
            "codigo": codigo_novo,
            "nome": nome_novo,
            "descricao": desc_novo,
            # manter imagem como caminho local (conforme solicitado)
            "imagem": f"{IMAGENS_DIR}/{img_filename}"
        }
        if manual_url:
            nova_peca["manual"] = manual_url

        catalogo["pecas"].append(nova_peca)

        produtos = carregar_produtos()
        produtos.append(nova_peca)
        salvar_produtos(produtos)

        # Faz upload da imagem ao GitHub (mantendo comportamento anterior)
        resp_img = github_upload(
            img_path,
            f"imagens/{img_filename}",
            f"Adicionando imagem da peça {codigo_novo}"
        )
        if getattr(resp_img, "status_code", None) in [200, 201]:
            st.success("📸 Imagem enviada ao GitHub!")
        else:
            st.warning("Imagem salva localmente; envio ao GitHub falhou ou não autorizado.")

        resp_db = github_upload(
            PRODUTOS_FILE,
            "database/database.json",
            f"Atualizando database.json após adicionar produto {codigo_novo}"
        )
        if getattr(resp_db, "status_code", None) in [200, 201]:
            st.success("📘 database.json atualizado no GitHub!")
        else:
            st.warning("database.json salvo localmente; envio ao GitHub falhou ou não autorizado.")

        st.success("Peça adicionada com sucesso! Clique em 'Salvar catálogo' para gravar no arquivo.")
        st.rerun()

st.markdown("---")

# --------------------------------------------------
# Botão final para salvar todas as alterações no catálogo
# --------------------------------------------------
if st.button("💾 Salvar catálogo"):
    catalogo["cliente"] = cliente_edit
    salvar_catalogo(caminho_catalogo, catalogo)

    resp_json = github_upload(
        caminho_catalogo,
        f"clientes/{nome_catalogo}",
        f"Atualizando catálogo do cliente {cliente_edit}"
    )
    if getattr(resp_json, "status_code", None) in [200, 201]:
        st.success("🎉 Catálogo atualizado e enviado ao GitHub!")
    else:
        st.warning("Catálogo salvo localmente; envio ao GitHub falhou ou não autorizado.")

    st.rerun()
