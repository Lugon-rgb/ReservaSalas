from datetime import datetime, timedelta, timezone
from functools import wraps
import hashlib
import secrets
from urllib.parse import urlparse, urljoin
from flask import abort, g, redirect, request, session as flask_session, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import text
from reservaSalas import app, db, Bcrypt
from reservaSalas.persistencia.models import SessaoAcesso, User


class RecusaAutorizacao(Exception):
    def __init__(self, codigo):
        self.codigo = codigo
        super().__init__(codigo)


PERMISSOES_POR_PERFIL = {
    "estudante": {"CONSULTAR", "LISTAR_RESERVAS", "RESERVAR", "CANCELAR"},
    "atendente": {"CONSULTAR", "LISTAR_RESERVAS", "ATENDER"},
    "administrador": {
        "CONSULTAR",
        "LISTAR_RESERVAS",
        "CANCELAR",
        "ATENDER",
        "ADMINISTRAR",
        "RELATORIO",
        "RESERVAR"
    },
}

PERFIL_CANONICO = {
    "user": "estudante",
    "estudante": "estudante",
    "atendente": "atendente",
    "admin": "administrador",
    "administrador": "administrador",
}


@app.context_processor
def disponibilizar_verificacao_permissao():
    def tem_permissao(permissao):
        if not current_user.is_authenticated:
            return False
        perfil = PERFIL_CANONICO.get(current_user.type.lower())
        return (
            perfil is not None
            and permissao in PERMISSOES_POR_PERFIL.get(perfil, set())
        )

    return {"tem_permissao": tem_permissao}


def _id_sessao_persistido(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _utc_sem_fuso(valor):
    if valor.tzinfo is None or valor.utcoffset() is None:
        return valor.replace(tzinfo=timezone.utc).replace(tzinfo=None)
    return valor.astimezone(timezone.utc).replace(tzinfo=None)


def autenticar(user_info, agora):
    if not user_info.validate_on_submit():
        return False

    user = User.query.filter_by(matricula=user_info.matricula.data).first()
    if user is None or not Bcrypt.check_password_hash(user.password, user_info.password.data):
        return False
    if not user.is_active:
        return False

    agora_utc = _utc_sem_fuso(agora)
    token = secrets.token_urlsafe(32)
    sessao_anterior = flask_session.get("sessao_acesso")
    if sessao_anterior:
        registro_anterior = db.session.get(
            SessaoAcesso, _id_sessao_persistido(sessao_anterior)
        )
        if registro_anterior and registro_anterior.revogada_em is None:
            registro_anterior.revogada_em = agora_utc

    db.session.add(
        SessaoAcesso(
            id=_id_sessao_persistido(token),
            user_matricula=user.matricula,
            criada_em=agora_utc,
            expira_em=agora_utc + timedelta(hours=8),
        )
    )
    db.session.commit()

    if not login_user(user, remember=False):
        return False
    flask_session["sessao_acesso"] = token
    flask_session.permanent = bool(user_info.remember.data)
    return True


def autorizar(sessao, permissao, agora):
    if permissao not in {
        permissao
        for permissoes in PERMISSOES_POR_PERFIL.values()
        for permissao in permissoes
    }:
        raise ValueError(f"Permissão desconhecida: {permissao}")
    if not sessao or not current_user.is_authenticated:
        raise RecusaAutorizacao("NAO_AUTENTICADO")
    if agora.tzinfo is None or agora.utcoffset() is None:
        raise ValueError("agora precisa incluir fuso horário")

    registro = db.session.get(SessaoAcesso, _id_sessao_persistido(sessao))
    if (
        registro is None
        or registro.revogada_em is not None
        or registro.user_matricula != current_user.get_id()
        or _utc_sem_fuso(agora) >= _utc_sem_fuso(registro.expira_em)
    ):
        raise RecusaAutorizacao("NAO_AUTENTICADO")

    user = db.session.get(User, registro.user_matricula)
    if user is None:
        raise RecusaAutorizacao("NAO_AUTENTICADO")
    perfil = PERFIL_CANONICO.get(user.type.lower())
    if perfil is None or permissao not in PERMISSOES_POR_PERFIL[perfil]:
        raise RecusaAutorizacao("SEM_PERMISSAO")

    versao_snapshot = db.session.execute(
        text("SELECT version_num FROM alembic_version")
    ).scalar_one()
    return user, perfil, versao_snapshot


def exige_permissao(permissao):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            permissao_atual = permissao() if callable(permissao) else permissao
            try:
                g.autorizacao = autorizar(
                    flask_session.get("sessao_acesso"),
                    permissao_atual,
                    datetime.now(timezone.utc),
                )
            except RecusaAutorizacao as recusa:
                if recusa.codigo == "NAO_AUTENTICADO":
                    logout_user()
                    flask_session.clear()
                    return redirect(url_for("login", next=request.url))
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def cadastrar_usuario(sessao, user_info, agora) -> User | None:
    autorizar(sessao, "ADMINISTRAR", agora)
    if not user_info.validate_on_submit():
        return None

    perfil_para_tipo = {
        "ESTUDANTE": "user",
        "ATENDENTE": "atendente",
        "ADMINISTRADOR": "admin",
    }
    novo_usuario = User(
        matricula=user_info.matricula.data,
        nome=user_info.nome.data,
        password=Bcrypt.generate_password_hash(user_info.password.data).decode("utf-8"),
        type=perfil_para_tipo[user_info.type.data],
    )
    db.session.add(novo_usuario)
    db.session.commit()
    return novo_usuario
        
def encerraSessao(user):
    token = flask_session.get("sessao_acesso")
    if token:
        registro = db.session.get(SessaoAcesso, _id_sessao_persistido(token))
        if registro and registro.revogada_em is None:
            registro.revogada_em = _utc_sem_fuso(datetime.now(timezone.utc))
            db.session.commit()
    flask_session.clear()
    return logout_user()

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc