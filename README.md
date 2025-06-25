Run these commands in the same order:

```
cd app

python -m venv .venv

\# Activate (each new terminal)

\# macOS/Linux: source .venv/bin/activate

\# Windows CMD: .venv\Scripts\activate.bat

\# Windows PowerShell: .venv\Scripts\Activate.ps1

python -m pip install google-adk

export SSL_CERT_FILE=$(python -m certifi)

create .env file following the .env.example

uvicorn main:app
```
