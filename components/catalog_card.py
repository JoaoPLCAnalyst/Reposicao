import streamlit as st
import os

def render_catalog_banner(
    slug: str,
    titulo: str,
    subtitulo: str,
    preview_img: str = None,
    key_suffix: str = ""
) -> bool:

    css_key = "_catalog_banner_css"
    if css_key not in st.session_state:
        st.markdown("""
        <style>
        .banner-card {
            background: linear-gradient(90deg, #ffffff 0%, #f2f8ff 100%);
            border-radius: 16px;
            padding: 22px 26px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 10px 30px rgba(0,0,0,0.06);
            margin-bottom: 16px;
        }
        .banner-text h2 {
            font-size: 26px;
            margin: 0;
            color: #0f172a;
            font-weight: 700;
        }
        .banner-text p {
            margin: 6px 0 14px 0;
            color: #475569;
            font-size: 15px;
        }
        .banner-btn {
            background-color: #0f766e;
            color: white;
            padding: 10px 18px;
            border-radius: 10px;
            font-weight: 600;
            display: inline-block;
            text-decoration: none;
        }
        .banner-btn:hover {
            background-color: #115e59;
        }
        .banner-img img {
            max-height: 120px;
            object-fit: contain;
        }
        @media (max-width: 900px) {
            .banner-card {
                flex-direction: column;
                text-align: center;
                gap: 14px;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        st.session_state[css_key] = True

    clicked = False

    with st.container():
        col_click = st.columns([1, 0.0001])[0]

        st.markdown('<div class="banner-card">', unsafe_allow_html=True)

        # Texto
        st.markdown(f"""
        <div class="banner-text">
            <h2>{titulo}</h2>
            <p>{subtitulo}</p>
        </div>
        """, unsafe_allow_html=True)

        # Imagem
        if preview_img and os.path.exists(preview_img):
            st.markdown(f"""
            <div class="banner-img">
                <img src="data:image/png;base64,{open(preview_img,'rb').read().hex()}">
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Botão funcional (Streamlit)
        clicked = st.button("Ver catálogo", key=f"open_{slug}_{key_suffix}")

    return clicked
git