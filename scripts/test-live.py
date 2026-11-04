"""Run real frontend HTTP requests against a disposable company in test PostgreSQL only."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
from urllib.request import urlopen
from uuid import uuid4

root = Path(__file__).resolve().parents[1]
config = json.loads((root / '.local/config.json').read_text(encoding='utf-8'))
base = f"postgresql+psycopg://{config['user']}:{config['password']}@127.0.0.1:{config['port']}/"
os.environ['DATABASE_URL'] = base + 'baby_belo_test'
os.environ['TEST_AUTH_DATABASE_URL'] = base + 'baby_belo_auth_test'
os.environ['SECRET_KEY'] = config['secret']
os.environ['PYTHONUTF8'] = '1'
sys.path.insert(0, str(root / 'backend'))
from app.main import app  # Registers existing models; no application changes.
from app.auth.service import AuthService
from app.auth.models import EmpresaUsuario
from app.application.company_service import CompanyApplicationService
from app.shared.database import SessionLocal
from sqlalchemy.engine import make_url
assert make_url(os.environ['DATABASE_URL']).database == 'baby_belo_test'

suffix = uuid4().hex
email, password = f'owner-{suffix}@example.com', secrets.token_urlsafe(32)
viewer_email, viewer_password = f'viewer-{suffix}@example.com', secrets.token_urlsafe(32)
with SessionLocal() as db:
    owner = AuthService.create_user(db, nome='Verificação isolada', email=email, senha=password)
    company = CompanyApplicationService.create_company(db, user_id=owner.id, nome='Baby Belo Ateliê')
    viewer = AuthService.create_user(db, nome='Consulta isolada', email=viewer_email, senha=viewer_password)
    db.add(EmpresaUsuario(empresa_id=company.id, usuario_id=viewer.id, papel='VIEWER', ativo=True))
    other = CompanyApplicationService.create_company(db, user_id=viewer.id, nome='Outra empresa de teste')
    db.commit()
    other_id = other.id

env = {**os.environ, 'BABY_BELO_TEST_API':'http://127.0.0.1:8001', 'BABY_BELO_TEST_EMAIL':email,
       'BABY_BELO_TEST_PASSWORD':password, 'BABY_BELO_VIEWER_EMAIL':viewer_email,
       'BABY_BELO_VIEWER_PASSWORD':viewer_password, 'BABY_BELO_OTHER_COMPANY':str(other_id)}
log_path = root / '.local/live-api.log'
with log_path.open('w', encoding='utf-8') as log:
    server = subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--app-dir','backend','--host','127.0.0.1','--port','8001'], cwd=root, env=env, stdout=log, stderr=log, creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    try:
        ready = False
        for _ in range(100):
            if server.poll() is not None:
                raise RuntimeError('A API de testes encerrou. Consulte .local/live-api.log.')
            try:
                with urlopen('http://127.0.0.1:8001/openapi.json', timeout=1) as response:
                    ready = response.status == 200
            except Exception:
                time.sleep(.2)
                continue
            break
        if not ready:
            raise RuntimeError('A API de testes não ficou pronta.')
        result = subprocess.run(['node','frontend/tests/live.mjs'],cwd=root,env=env)
        if result.returncode:
            raise SystemExit(result.returncode)
    finally:
        server.terminate()
        server.wait(timeout=15)
