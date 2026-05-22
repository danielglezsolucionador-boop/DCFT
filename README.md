# DCFT - Doctor Contable Financiero Tributario

Base operacional enterprise local para un copiloto contable, financiero y tributario.

## Local

```powershell
cd C:\Users\admin\dcft-knowledge-core
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
$env:PYTHONPATH="C:\Users\admin\dcft-knowledge-core\apps\backend"
python -m alembic upgrade head
python -m uvicorn app.main:app --app-dir apps/backend --host 127.0.0.1 --port 8200
```

Frontend:

```powershell
cd C:\Users\admin\dcft-knowledge-core\apps\frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5174
```

No external AI/OCR provider is enabled by default.