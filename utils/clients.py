import json

def carregar_cliente(cliente_id):
    arquivo = f"clientes/{cliente_id}.json"

    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
