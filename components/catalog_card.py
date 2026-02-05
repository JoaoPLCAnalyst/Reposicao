import streamlit as st
import os
import urllib.parse

def render_catalog_card(slug: str, cliente_name: str, qtd_pecas: int,
                        preview_img: str = None, preview_title: str = "",
                        key_suffix: str = "") -> bool:
    """
    Componente de card de catálogo com imagem posicionada à direita
    e corte diagonal na miniatura.

    Retorna True se o botão funcional do Streamlit for clicado.

    Parâmetros:
    - slug: identificador do cliente (usado para keys)
    - cliente_name: nome exibido do catálogo
    - qtd_pecas: número de itens no catálogo
    - preview_img: URL externa ou caminho local relativo para a imagem do primeiro item
    - preview_title: texto pequeno exibido abaixo do meta
    - key_suffix: sufixo para keys de botões (evita colisão)
    """

    # Injeta CSS apenas uma vez por sessão
    css_key = "_catalog_card_css_injected"
    if css_key not in st.session_state:
        st.markdown(
            """
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

            :root{
              --card-bg: linear-gradient(180deg,#ffffff 0%,#f7fbff 100%);
              --accent: #0b5fff;
              --muted: #6b7280;
              --title: #08365c;
              --radius: 12px;
              --shadow: 0 8px 24px rgba(8,54,92,0.06);
            }

            body, .stApp { font-family: 'Inter', system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial; }

            /* Card container */
            .wce-card {
                display:flex;
                gap:16px;
                align-items:center;
                justify-content:space-between;
                background: var(--card-bg);
                border-radius: var(--radius);
                padding: 12px;
                box-shadow: var(--shadow);
                transition: transform .18s ease, box-shadow .18s ease;
                overflow: hidden;
                min-height: 110px;
            }
            .wce-card:hover { transform: translateY(-6px); box-shadow: 0 14px 40px rgba(8,54,92,0.10); }

            /* Body (texto) fica à esquerda */
            .wce-body {
                flex:1;
                display:flex;
                flex-direction:column;
                justify-content:center;
                min-width:0;
                order:1;
            }
            .wce-title {
                font-size: 18px;
                font-weight: 700;
                color: var(--title);
                line-height:1.05;
                margin-bottom:6px;
                white-space:nowrap;
                overflow:hidden;
                text-overflow:ellipsis;
            }
            .wce-sub {
                color: var(--muted);
                font-size: 13px;
                margin-bottom:8px;
                display:block;
                white-space:nowrap;
                overflow:hidden;
                text-overflow:ellipsis;
            }
            .wce-meta {
                color: #475569;
                font-size: 13px;
                margin-bottom:8px;
            }
            .wce-actions { display:flex; gap:8px; align-items:center; margin-top:6px; }

            /* Thumb à direita com corte diagonal */
            .wce-thumb-wrap {
                width: 180px;
                height: 110px;
                flex-shrink: 0;
                display:flex;
                align-items:center;
                justify-content:center;
                order:2;
                position:relative;
            }

            /* elemento que contém a imagem com clip-path diagonal */
            .wce-thumb {
                width:100%;
                height:100%;
                border-radius:10px;
                overflow:hidden;
                box-shadow: 0 6px 18px rgba(8,54,92,0.06);
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                /* diagonal cut: bottom-right slanted */
                -webkit-clip-path: polygon(0 0, 100% 0, 85% 100%, 0% 100%);
                clip-path: polygon(0 0, 100% 0, 85% 100%, 0% 100%);
                border: 1px solid rgba(230,238,248,1);
            }

            /* fallback quando não há imagem: mostra iniciais dentro do mesmo shape */
            .wce-thumb-fallback {
                width:100%;
                height:100%;
                display:flex;
                align-items:center;
                justify-content:center;
                background: linear-gradient(180deg,#eef6ff,#ffffff);
                color:#6b7280;
                font-weight:700;
                font-size:20px;
                -webkit-clip-path: polygon(0 0, 100% 0, 85% 100%, 0% 100%);
                clip-path: polygon(0 0, 100% 0, 85% 100%, 0% 100%);
                border-radius:10px;
                border: 1px solid rgba(230,238,248,1);
            }

            /* Botão visual (link) — apenas visual; ação real via st.button abaixo */
            .wce-open-btn {
                display:inline-block;
                text-decoration:none !important;
                padding:10px 16px;
                border-radius:10px;
                background: #ffffff;
                color:#08365c !important;
                font-weight:700;
                font-size:14px;
                border: 1px solid rgba(8,54,92,0.06);
                box-shadow: 0 4px 12px rgba(8,54,92,0.06);
            }
            .wce-open-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(8,54,92,0.08); }

            @media (max-width: 900px) {
                .wce-card { gap:12px; padding:10px; min-height:90px; }
                .wce-thumb-wrap { width:120px; height:80px; }
                .wce-title { font-size:16px; }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.session_state[css_key] = True

    # Normaliza preview_img e determina se existe localmente
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

    # Monta HTML do card com imagem à direita e corte diagonal via clip-path
    if img_src:
        # usa URL segura para background-image
        safe_img = urllib.parse.quote(img_src, safe=":/?&=#%")
        card_html = f"""
        <div class="wce-card">
          <div class="wce-body">
            <div class="wce-title">{cliente_name}</div>
            <div class="wce-meta">Itens no catálogo: <strong>{qtd_pecas}</strong></div>
            <div class="wce-sub">{preview_title}</div>
            <div class="wce-actions">
              <a class="wce-open-btn" href="javascript:void(0)" id="open_{slug}_{key_suffix}">Ver catálogo</a>
            </div>
          </div>

          <div class="wce-thumb-wrap">
            <div class="wce-thumb" style="background-image: url('{safe_img}');"></div>
          </div>
        </div>
        """
    else:
        initials = (cliente_name[:2] or "CL").upper()
        card_html = f"""
        <div class="wce-card">
          <div class="wce-body">
            <div class="wce-title">{cliente_name}</div>
            <div class="wce-meta">Itens no catálogo: <strong>{qtd_pecas}</strong></div>
            <div class="wce-sub">{preview_title}</div>
            <div class="wce-actions">
              <a class="wce-open-btn" href="javascript:void(0)" id="open_{slug}_{key_suffix}">Ver catálogo</a>
            </div>
          </div>

          <div class="wce-thumb-wrap">
            <div class="wce-thumb-fallback">{initials}</div>
          </div>
        </div>
        """

    st.markdown(card_html, unsafe_allow_html=True)

    # Botão funcional do Streamlit (branco, preservado)
    btn_key = f"open_{slug}_{key_suffix}"
    clicked = st.button("Abrir Catálogo", key=btn_key)
    return clicked
