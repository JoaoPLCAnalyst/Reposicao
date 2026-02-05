import streamlit as st
import os
import urllib.parse

def render_catalog_card(slug: str, cliente_name: str, qtd_pecas: int,
                        preview_img: str = None, preview_title: str = "",
                        key_suffix: str = "") -> bool:
    """
    Renderiza um card retangular com:
    - texto (título, meta, subtítulo, botão funcional) à esquerda
    - imagem à direita (background-image) dentro do mesmo retângulo
    - retorna True se o st.button for clicado
    """

    # Injeta CSS uma vez
    css_key = "_catalog_card_css_injected"
    if css_key not in st.session_state:
        st.markdown(
            """
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

            .wce-card-wrap {
                background: #ffffff;
                border-radius: 12px;
                padding: 12px;
                box-shadow: 0 8px 24px rgba(8,54,92,0.06);
                transition: transform .14s ease, box-shadow .14s ease;
                overflow: hidden;
                border: 1px solid rgba(230,238,248,1);
            }
            .wce-card-wrap:hover {
                transform: translateY(-4px);
                box-shadow: 0 14px 40px rgba(8,54,92,0.08);
            }

            .wce-row {
                display:flex;
                gap:16px;
                align-items:center;
                justify-content:space-between;
            }

            .wce-left {
                flex:1;
                min-width:0;
            }

            .wce-title {
                font-family: 'Inter', system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
                font-size:18px;
                font-weight:700;
                color:#08365c;
                margin:0 0 6px 0;
                white-space:nowrap;
                overflow:hidden;
                text-overflow:ellipsis;
            }
            .wce-sub {
                color:#6b7280;
                font-size:13px;
                margin:0 0 8px 0;
                white-space:nowrap;
                overflow:hidden;
                text-overflow:ellipsis;
            }
            .wce-meta {
                color:#475569;
                font-size:13px;
                margin:0 0 8px 0;
            }

            /* caixa da imagem (direita) - retângulo com border-radius */
            .wce-thumb-box {
                width: 180px;
                height: 110px;
                flex-shrink: 0;
                border-radius: 10px;
                overflow: hidden;
                background: #f1f5f9;
                border: 1px solid rgba(230,238,248,1);
                display:flex;
                align-items:center;
                justify-content:center;
                background-size: cover;
                background-position: center;
            }

            .wce-thumb-fallback {
                width:100%;
                height:100%;
                display:flex;
                align-items:center;
                justify-content:center;
                color:#6b7280;
                font-weight:700;
                font-size:20px;
            }

            .wce-visual-link {
                display:inline-block;
                padding:8px 14px;
                border-radius:8px;
                background:#ffffff;
                color:#08365c;
                font-weight:700;
                font-size:13px;
                border:1px solid rgba(8,54,92,0.06);
                box-shadow: 0 4px 12px rgba(8,54,92,0.06);
                text-decoration:none !important;
            }

            @media (max-width:900px){
                .wce-thumb-box { width:120px; height:80px; }
                .wce-row { gap:12px; }
                .wce-title { font-size:16px; }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.session_state[css_key] = True

    # Normaliza preview_img (verifica caminhos locais)
    img_src = None
    if preview_img and isinstance(preview_img, str):
        src = preview_img.strip()
        if src.startswith("http://") or src.startswith("https://"):
            img_src = src
        else:
            # tenta caminhos locais
            if os.path.exists(src):
                img_src = src
            else:
                alt = src.lstrip("/")
                if os.path.exists(alt):
                    img_src = alt
                else:
                    img_src = None

    # Renderiza tudo dentro do mesmo wrapper para garantir que título e imagem fiquem dentro do retângulo
    with st.container():
        # abre o wrapper
        st.markdown('<div class="wce-card-wrap">', unsafe_allow_html=True)

        # cria a linha com duas "colunas" (texto à esquerda, imagem à direita)
        st.markdown('<div class="wce-row">', unsafe_allow_html=True)

        # esquerda: título, meta, subtítulo e botão funcional
        st.markdown('<div class="wce-left">', unsafe_allow_html=True)
        st.markdown(f'<div class="wce-title">{cliente_name}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="wce-meta">Itens no catálogo: <strong>{qtd_pecas}</strong></div>', unsafe_allow_html=True)
        if preview_title:
            st.markdown(f'<div class="wce-sub">{preview_title}</div>', unsafe_allow_html=True)

        # espaço antes do botão
        st.write("")
        btn_key = f"open_{slug}_{key_suffix}"
        clicked = st.button("Abrir Catálogo", key=btn_key)
        st.markdown('</div>', unsafe_allow_html=True)  # fecha wce-left

        # direita: imagem como background dentro do mesmo wrapper
        if img_src:
            # para URLs externas, quote; para caminhos locais, usa caminho direto
            if img_src.startswith("http://") or img_src.startswith("https://"):
                bg_url = urllib.parse.quote(img_src, safe=":/?&=#%")
            else:
                bg_url = img_src.replace("\\", "/")
            thumb_html = f'<div class="wce-thumb-box" style="background-image: url(\'{bg_url}\');"></div>'
            st.markdown(f'<div>{thumb_html}</div>', unsafe_allow_html=True)
        else:
            initials = (cliente_name[:2] or "CL").upper()
            st.markdown(f'<div><div class="wce-thumb-box"><div class="wce-thumb-fallback">{initials}</div></div></div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)  # fecha wce-row
        st.markdown('</div>', unsafe_allow_html=True)  # fecha wce-card-wrap

    return clicked
