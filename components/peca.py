import streamlit as st

# -----------------------------------------------------------
# Função para renderizar cada peça
# -----------------------------------------------------------
def render_peca(peca, idx, quantidades, pecas_selecionadas):
    col_img, col_info, col_sel = st.columns([1.4, 3, 1.1])

    # Imagem
    with col_img:
        if peca.get("imagem"):
            st.image(peca["imagem"], use_container_width=True)
        else:
            st.write("Sem imagem")

    # Informações
    with col_info:
        st.write(f"### {peca.get('nome', '—')}")
        st.write(f"**Código:** {peca.get('codigo', '—')}")
        st.write(f"**Descrição:** {peca.get('descricao', '—')}")

    # Seleção
    with col_sel:
        key_chk = f"chk_{peca['codigo']}_{idx}"
        key_qtd = f"qtd_{peca['codigo']}_{idx}"
        adicionar = st.checkbox("Selecionar", key=key_chk)
        if adicionar:
            qtd = st.number_input(
                "Quantidade",
                min_value=1,
                step=1,
                key=key_qtd
            )
            pecas_selecionadas.append(peca)
            quantidades[peca['codigo']] = qtd
