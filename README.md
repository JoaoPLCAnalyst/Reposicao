criar o repositorio virtual

py -m venv .venv

liberar politica de execução 

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

entrar no ambiente virtual 

.venv\Scripts\Activate.ps1

instalar as libs 

C:\Users\Amanda\Desktop\AppReposicao\.venv\Scripts\python.exe -m pip install -U pip setuptools wheel

instalar a lib do streamlit

pip install -U streamlit

rodar a aplicação

streamlit run app.py
