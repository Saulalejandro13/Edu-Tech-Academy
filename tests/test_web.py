from pathlib import Path

def test_ui_has_real_role_login():
    base=Path(__file__).resolve().parents[1]/'src/edutech/api/static'
    html=(base/'index.html').read_text(encoding='utf-8')
    js=(base/'app.js').read_text(encoding='utf-8')
    assert 'login-form' in html and 'register-form' in html
    assert 'Cliente empresarial' in html and 'Control Escolar' in html
    assert 'company-form' in html and 'instructor-list' in html
    assert "'/auth/login'" in js and "'/auth/me'" in js
    assert 'Authorization' in js and 'Bearer ' in js
    assert '/empresas/inscripciones' in js
    assert '/solicitudes/' in js
