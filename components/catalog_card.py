# components/catalog_card.py
import streamlit as st
import os
import urllib.parse

def render_catalog_card(
    slug: str,
    cliente_name: str,
    qtd_pecas: int,
    preview_img: str = None,
    preview_title: str = "",
    key_suffix: str = ""
) -> bool:
    """
    Renderiza um card retangular com:
    - texto (nome, qtd, subtítulo, botão funcional) à esquerda
    - imagem à direita (dentro do mesmo retângulo)
    Retorna True se o botão "Abrir Catálogo" for clicado.
    """

    # Injeta CSS apenas uma vez
    css_flag = "_wce_card_css_vfinal"
    if css_flag not in st.session_state:
        st.markdown(
            """
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

            .wce-card {
                display:flex;
                align-items:center;
                justify-content:space-between;
                gap:18px;
                background: #ffffff;
                border-radius: 12px;
                padding: 14px;
                box-shadow: 0 8px 24px rgba(8,54,92,0.06);
                border: 1px solid rgba(230,238,248,1);
                overflow: hidden;
                width:100%;
                box-sizing:border-box;
            }

            .wce-left {
                flex: 1 1 auto;
                min-width: 0;
                display:flex;
                flex-direction:column;
                gap:8px;
            }

            .wce-title {
                font-family: 'Inter', system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
                font-size: 18px;
                font-weight: 700;
                color: #08365c;
                margin: 0;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .wce-meta {
                color: #475569;
                font-size: 13px;
                margin: 0;
            }

            .wce-sub {
                color: #6b7280;
                font-size: 13px;
                margin: 0;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .wce-actions {
                margin-top: 6px;
                display:flex;
                gap:8px;
                align-items:center;
            }

            /* botão visual (apenas visual) — ação real via st.button */
            .wce-visual-btn {
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

            /* Caixa da imagem à direita (retângulo com border-radius) */
            .wce-thumb {
                width: 180px;
                height: 110px;
                flex-shrink: 0;
                border-radius: 10px;
                overflow: hidden;
                background: #f1f5f9 center/cover no-repeat;
                border: 1px solid rgba(230,238,248,1);
                display:flex;
                align-items:center;
                justify-content:center;
            }

            .wce-thumb img {
                width:100%;
                height:100%;
                object-fit:cover;
                display:block;
            }

            .wce-thumb-fallback {
                color:#6b7280;
                font-weight:700;
                font-size:20px;
            }

            @media (max-width: 900px) {
                .wce-thumb { width:120px; height:80px; }
                .wce-title { font-size:16px; }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.session_state[css_flag] = True

    # Normaliza e valida preview_img
    img_src = None
    if preview_img and isinstance(preview_img, str):
        src = preview_img.strip()
        if src.startswith("http://") or src.startswith("https://"):
            img_src = src
        else:
            # tenta caminhos locais relativos ao app
            if os.path.exists(src):
                img_src = src.replace("\\", "/")
            else:
                alt = src.lstrip("/")
                if os.path.exists(alt):
                    img_src = alt.replace("\\", "/")
                else:
                    img_src = None

    # Renderiza o card inteiro dentro de um único wrapper
    with st.container():
        # abre wrapper
        st.markdown('<div class="wce-card">', unsafe_allow_html=True)

        # lado esquerdo: texto e botão funcional
        st.markdown('<div class="wce-left">', unsafe_allow_html=True)
        st.markdown(f'<div class="wce-title">{cliente_name}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="wce-meta">Itens no catálogo: <strong>{qtd_pecas}</strong></div>', unsafe_allow_html=True)
        if preview_title:
            st.markdown(f'<div class="wce-sub">{preview_title}</div>', unsafe_allow_html=True)

        # ações: botão funcional do Streamlit (branco)
        st.markdown('<div class="wce-actions">', unsafe_allow_html=True)
        btn_key = f"open_{slug}_{key_suffix}"
        clicked = st.button("Abrir Catálogo", key=btn_key)
        # opcional: botão visual ao lado (não substitui ação)
        st.markdown('<a class="wce-visual-btn" href="javascript:void(0)">Ver catálogo</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)  # fecha wce-actions

        st.markdown('</div>', unsafe_allow_html=True)  # fecha wce-left

        # lado direito: imagem dentro do mesmo retângulo
        if img_src:
            # para URLs externas, quote; para caminhos locais, usa caminho direto
            if img_src.startswith("http://") or img_src.startswith("https://"):
                safe_bg = urllib.parse.quote(img_src, safe=":/?&=#%")
                thumb_html = f'<div class="wce-thumb" style="background-image: url(\'{safe_bg}\');"></div>'
                st.markdown(thumb_html, unsafe_allow_html=True)
            else:
                # caminho local: renderiza <img> dentro do div para garantir carregamento
                local_path = img_src.replace("'", "\\'")
                thumb_html = f'<div class="wce-thumb"><img src="{local_path}" alt="thumb" /></div>'
                st.markdown(thumb_html, unsafe_allow_html=True)
        else:
            initials = (cliente_name[:2] or "CL").upper()
            fallback_html = f'<div class="wce-thumb"><div class="wce-thumb-fallback">{initials}</div></div>'
            st.markdown(fallback_html, unsafe_allow_html=True)

        # fecha wrapper
        st.markdown('</div>', unsafe_allow_html=True)

    return clicked
