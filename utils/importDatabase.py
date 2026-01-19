import json
import streamlit as st

def carregar_database():
    try:
        with open("database/database.json", "r", encoding="utf-8") as f:
            lista = json.load(f)

        # converter para dict por código
        return {item["codigo"]: item for item in lista}

    except FileNotFoundError:
        st.error("❌ O arquivo 'database.json' não foi encontrado em /database/")
        return {}
    except Exception as e:
        st.error(f"Erro ao carregar database.json: {e}")
        return {}