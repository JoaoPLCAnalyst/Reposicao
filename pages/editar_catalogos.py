import streamlit as st
import json
import os
from PIL import Image
import base64, requests

st.set_page_config(page_title="Editar Catálogo", page_icon="📘")

CATALOGOS_DIR = "clientes"
IMAGENS_DIR = "imagens"
PDFS_DIR = "pdfs"
PRODUTOS_FILE = "database/database.json"

# --------------------------------------------------
# Funções auxiliares
# --------------------------------------------------
def carregar_catalogo(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_catalogo(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def carregar_produtos():
    if not os.path.exists(PRODUTOS_FILE):
        return []
    with open(PRODUTOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_produtos(produtos):
    with open(PRODUTOS_FILE, "w", encoding="utf-8") as f:
        json.dump(produtos, f, indent=2, ensure_ascii=False)

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
                catalogo["pecas"][i]["nome"] = nome_input
                catalogo["pecas"][i]["descricao"] = desc_input

                img_filename = None
                if nova_img is not None:
                    ext = nova_img.name.split(".")[-1].lower()
                    if ext == "jpeg":
                        ext = "jpg"
                    img_filename = f"{p.get('codigo', i)}.{ext}"
                    img_path = os.path.join(IMAGENS_DIR, img_filename)

                    os.makedirs(IMAGENS_DIR, exist_ok=True)

                    image = Image.open(nova_img)
                    image.save(img_path)

                    catalogo["pecas"][i]["imagem"] = f"{IMAGENS_DIR}/{img_filename}"

                    resp_img = github_upload(
                        img_path,
                        f"imagens/{img_filename}",
                        f"Atualizando imagem da peça {p.get('codigo', i)}"
                    )
                    if resp_img.status_code in [200, 201]:
                        st.success("📸 Imagem atualizada no GitHub!")
                    else:
                        st.error("Erro ao atualizar imagem no GitHub")
                        st.code(resp_img.text)

                manual_filename = None
                if nova_pdf is not None:
                    manual_filename = f"{p.get('codigo', i)}.pdf"
                    manual_path = os.path.join(PDFS_DIR, manual_filename)
                    os.makedirs(PDFS_DIR, exist_ok=True)
                    with open(manual_path, "wb") as f:
                        f.write(nova_pdf.read())

                    catalogo["pecas"][i]["manual"] = f"{PDFS_DIR}/{manual_filename}"

                    resp_pdf = github_upload(
                        manual_path,
                        f"pdfs/{manual_filename}",
                        f"Atualizando manual PDF da peça {p.get('codigo', i)}"
                    )
                    if resp_pdf.status_code in [200, 201]:
                        st.success("📑 Manual PDF atualizado no GitHub!")
                    else:
                        st.error("Erro ao atualizar manual PDF no GitHub")
                        st.code(resp_pdf.text)

                produtos = carregar_produtos()
                for prod in produtos:
                    if prod["codigo"] == p.get("codigo"):
                        prod["nome"] = nome_input
                        prod["descricao"] = desc_input
                        if img_filename:
                            prod["imagem"] = f"imagens/{img_filename}"
                        if manual_filename:
                            prod["manual"] = f"pdfs/{manual_filename}"
                    break
                salvar_produtos(produtos)

                resp_db = github_upload(
                    PRODUTOS_FILE,
                    "database/database.json",
                    f"Atualizando produto {p.get('codigo')} no database.json"
                )
                if resp_db.status_code in [200, 201]:
                    st.success("📘 database.json atualizado no GitHub!")
                else:
                    st.error("Erro ao enviar database.json")
                    st.code(resp_db.text)

                st.success("Alterações aplicadas localmente. Clique em 'Salvar catálogo' para gravar no arquivo.")
                st.rerun()

# --------------------------------------------------
# Remover peças
# --------------------------------------------------
if remover_indices:
    for idx in sorted(remover_indices, reverse=True):
        p_to_remove = catalogo["pecas"][idx]
        codigo_removido = p_to_remove.get("codigo")

        img_path = p_to_remove.get("imagem")
        if img_path and os.path.exists(img_path):
            try:
                os.remove(img_path)
            except Exception:
                pass

        pdf_path = p_to_remove.get("manual")
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception:
                pass

        catalogo["pecas"].pop(idx)

        produtos = carregar_produtos()
        produtos = [prod for prod in produtos if prod["codigo"] != codigo_removido]
        salvar_produtos(produtos)

        resp_db = github_upload(
            PRODUTOS_FILE,
            "database/database.json",
            f"Removendo produto {codigo_removido} do database.json"
        )
        if resp_db.status_code in [200, 201]:
            st.success("📘 database.json atualizado no GitHub!")
        else:
            st.error("Erro ao enviar database.json")
            st.code(resp_db.text)

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
        image.save(img_path)

        # ---------------- SALVAR PDF (se existir) ----------------
        manual_filename = None
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
            if resp_pdf.status_code in [200, 201]:
                st.success("📑 Manual PDF enviado ao GitHub!")
            else:
                st.error("Erro ao enviar manual PDF")
                st.code(resp_pdf.text)

        # ---------------- CRIAR PEÇA ----------------
        nova_peca = {
            "codigo": codigo_novo,
            "nome": nome_novo,
            "descricao": desc_novo,
            "imagem": f"{IMAGENS_DIR}/{img_filename}"
        }
        if manual_filename:
            nova_peca["manual"] = f"pdfs/{manual_filename}"

        catalogo["pecas"].append(nova_peca)

        produtos = carregar_produtos()
        produtos.append(nova_peca)
        salvar_produtos(produtos)

        resp_img = github_upload(
            img_path,
            f"imagens/{img_filename}",
            f"Adicionando imagem da peça {codigo_novo}"
        )
        if resp_img.status_code in [200, 201]:
            st.success("📸 Imagem enviada ao GitHub!")
        else:
            st.error("Erro ao enviar imagem")
            st.code(resp_img.text)

        resp_db = github_upload(
            PRODUTOS_FILE,
            "database/database.json",
            f"Atualizando database.json após adicionar produto {codigo_novo}"
        )
        if resp_db.status_code in [200, 201]:
            st.success("📘 database.json atualizado no GitHub!")
        else:
            st.error("Erro ao enviar database.json")
            st.code(resp_db.text)

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
    if resp_json.status_code in [200, 201]:
        st.success("🎉 Catálogo atualizado e enviado ao GitHub!")
    else:
        st.error("❌ Erro ao enviar catálogo")
        st.code(resp_json.text)

    st.rerun()
