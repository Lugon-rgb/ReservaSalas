import unittest
from reservaSalas import app
import reservaSalas.acesso.routes

app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
response = app.test_client().get('/login')
assert response.status_code == 200, response.status_code
html = response.get_data(as_text=True)
assert 'class="pagina-login"' in html
assert 'name="matricula"' in html
assert 'name="password"' in html
assert 'Entrar' in html
assert 'Matrícula ou senha inválidas.' not in html
print('GET /login template render: OK')