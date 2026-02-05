# components/catalog_card.py
import streamlit as st
import os
import urllib.parse

def render_catalog_card(slug: str, cliente_name: str, qtd_pecas: int,
                        preview_img: str = None, preview_title: str = "",
                        key_suffix: str = "") -> bool:
    """
    Renderiza um card com:
    - texto à esquerda
    - imagem à direita com corte diagonal (clip-path)
    - botão funcional do Streamlit (branco) abaixo/ao lado para abrir o catálogo

    Retorna True se o st.button for clicado.
    """

    # Injeta CSS uma vez por sessão
    css_key = "_wce_catalog_card_css"
    if css_key not in st.session_state:
        st.markdown(
            """
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

            :root{
              --card-bg: linear-gradient(180deg,#ffffff 0%,#f7fbff 100%);
              --muted: #6b7280;
              --title: #08365c;
              --radius: 12px;
              --shadow: 0 8px 24px rgba(8,54,92,0.06);
            }

            .wce-card {
                display:flex;
                gap:18px;
                align-items:center;
                justify-content:space-between;
                background: var(--card-bg);
                border-radius: var(--radius);
                padding: 14px;
                box-shadow: var(--shadow);
                transition: transform .18s ease, box-shadow .18s ease;
                overflow: hidden;
                min-height: 110px;
            }
            .wce-card:hover { transform: translateY(-6px); box-shadow: 0 14px 40px rgba(8,54,92,0.10); }

            .wce-body {
                flex:1;
                display:flex;
                flex-direction:column;
                justify-content:center;
                min-width:0;
                order:1;
            }
            .wce-title {
                font-family: 'Inter', system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
                font-size:18px;
                font-weight:700;
                color: var(--title);
                margin:0 0 6px 0;
                white-space:nowrap;
                overflow:hidden;
                text-overflow:ellipsis;
            }
            .wce-sub {
                color: var(--muted);
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
            .wce-actions { display:flex; gap:8px; align-items:center; margin-top:6px; }

            /* Thumb à direita com corte diagonal (clip-path) */
            .wce-thumb-wrap {
                width: 180px;
                height: 110px;
                flex-shrink:0;
                order:2;
                display:flex;
                align-items:center;
                justify-content:center;
            }
            .wce-thumb {
                width:100%;
                height:100%;
                border-radius:10px;
                overflow:hidden;
                background-size:cover;
                background-position:center;
                background-repeat:no-repeat;
                -webkit-clip-path: polygon(0 0, 100% 0, 85% 100%, 0% 100%);
                clip-path: polygon(0 0, 100% 0, 85% 100%, 0% 100%);
                border: 1px solid rgba(230,238,248,1);
                box-shadow: 0 6px 18px rgba(8,54,92,0.06);
            }
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

            /* Visual link (apenas visual) - mantemos o botão funcional do Streamlit branco */
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
                .wce-thumb-wrap { width:120px; height:80px; }
                .wce-card { padding:10px; gap:12px; min-height:90px; }
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

    # Monta HTML do card com imagem à direita (background-image + clip-path)
    if img_src:
        # Para background-image, usamos a URL "segura" — para caminhos locais, não quote demais
        if img_src.startswith("http://") or img_src.startswith("https://"):
            bg_url = urllib.parse.quote(img_src, safe=":/?&=#%")
        else:
            # caminho local: tenta usar caminho relativo sem encoding
            bg_url = img_src.replace("\\", "/")
        card_html = f"""
        <div class="wce-card">
          <div class="wce-body">
            <div class="wce-title">{cliente_name}</div>
            <div class="wce-meta">Itens no catálogo: <strong>{qtd_pecas}</strong></div>
            <div class="wce-sub">{preview_title}</div>
            <div class="wce-actions">
              <a class="wce-visual-link" href="javascript:void(0)">Ver catálogo</a>
            </div>
          </div>

          <div class="wce-thumb-wrap">
            <div class="wce-thumb" style="background-image: url('{bg_url}');"></div>
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
              <a class="wce-visual-link" href="javascript:void(0)">Ver catálogo</a>
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
