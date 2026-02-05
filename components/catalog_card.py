import streamlit as st
import os
import urllib.parse

# Renderiza um card de catálogo com imagem à esquerda, título, meta e botão.
# Retorna True se o botão funcional do Streamlit for clicado.
def render_catalog_card(slug: str, cliente_name: str, qtd_pecas: int,
                        preview_img: str = None, preview_title: str = "",
                        key_suffix: str = "") -> bool:
    """
    Parâmetros:
    - slug: identificador do cliente (usado para keys)
    - cliente_name: nome exibido do catálogo
    - qtd_pecas: número de itens no catálogo
    - preview_img: URL externa ou caminho local relativo para a imagem do primeiro item
    - preview_title: texto pequeno exibido abaixo do meta
    - key_suffix: sufixo para keys de botões (evita colisão)
    """

    # Injeta CSS apenas uma vez por sessão para evitar duplicação
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

            .wce-card {
                display:flex;
                gap:16px;
                align-items:center;
                background: var(--card-bg);
                border-radius: var(--radius);
                padding: 14px;
                box-shadow: var(--shadow);
                transition: transform .18s ease, box-shadow .18s ease;
                overflow: hidden;
                min-height: 110px;
            }
            .wce-card:hover { transform: translateY(-6px); box-shadow: 0 14px 40px rgba(8,54,92,0.10); }

            .wce-thumb {
                width: 160px;
                height: 100px;
                flex-shrink: 0;
                border-radius: 10px;
                overflow: hidden;
                background: linear-gradient(180deg,#eef6ff,#ffffff);
                border: 1px solid #e6eef8;
                display:flex;
                align-items:center;
                justify-content:center;
            }
            .wce-thumb img {
                width: 100%;
                height: 100%;
                object-fit: cover;
                display:block;
            }

            .wce-body {
                flex:1;
                display:flex;
                flex-direction:column;
                justify-content:center;
                min-width:0;
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

            .wce-actions {
                display:flex;
                gap:8px;
                align-items:center;
                margin-top:6px;
            }

            .wce-open-btn {
                display:inline-block;
                text-decoration:none !important;
                padding:10px 16px;
                border-radius:10px;
                background: var(--accent);
                color:white !important;
                font-weight:700;
                font-size:14px;
                border: 0;
                box-shadow: 0 6px 18px rgba(11,95,255,0.14);
                transition: transform .12s, box-shadow .12s;
            }
            .wce-open-btn:hover { transform: translateY(-2px); box-shadow: 0 12px 30px rgba(11,95,255,0.18); }

            @media (max-width: 900px) {
                .wce-card { flex-direction:row; gap:12px; padding:12px; }
                .wce-thumb { width:120px; height:80px; }
                .wce-title { font-size:16px; }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.session_state[css_key] = True

    # Normaliza preview_img
    img_src = None
    is_external = False
    if preview_img and isinstance(preview_img, str):
        preview_img = preview_img.strip()
        if preview_img.startswith("http://") or preview_img.startswith("https://"):
            img_src = preview_img
            is_external = True
        else:
            # caminho local relativo
            if os.path.exists(preview_img):
                # converte para caminho relativo (funciona no Streamlit)
                img_src = preview_img
            else:
                # tenta remover leading slash e verificar
                alt_path = preview_img.lstrip("/")
                if os.path.exists(alt_path):
                    img_src = alt_path
                else:
                    img_src = None

    # Monta HTML do card (imagem via <img> para URLs externas e caminhos locais)
    if img_src:
        # Escapa atributos mínimos
        safe_img = urllib.parse.quote(img_src, safe=":/?&=#%")
        card_html = f"""
        <div class="wce-card">
          <div class="wce-thumb">
            <img src="{safe_img}" alt="thumb" />
          </div>
          <div class="wce-body">
            <div class="wce-title">{cliente_name}</div>
            <div class="wce-meta">Itens no catálogo: <strong>{qtd_pecas}</strong></div>
            <div class="wce-sub">{preview_title}</div>
            <div class="wce-actions">
              <a class="wce-open-btn" href="javascript:void(0)" id="open_{slug}_{key_suffix}">Ver catálogo</a>
            </div>
          </div>
        </div>
        """
    else:
        initials = (cliente_name[:2] or "CL").upper()
        card_html = f"""
        <div class="wce-card">
          <div class="wce-thumb">
            <div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:#6b7280;font-weight:700">{initials}</div>
          </div>
          <div class="wce-body">
            <div class="wce-title">{cliente_name}</div>
            <div class="wce-meta">Itens no catálogo: <strong>{qtd_pecas}</strong></div>
          </div>
        </div>
        """

    st.markdown(card_html, unsafe_allow_html=True)

    # Botão funcional do Streamlit (ação real)
    btn_key = f"open_{slug}_{key_suffix}"
    clicked = st.button("Abrir Catálogo", key=btn_key)
    return clicked
