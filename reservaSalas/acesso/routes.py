from flask import render_template, url_for, flash, redirect, request, abort, session as flask_session
from datetime import datetime, timezone
from reservaSalas import app
from reservaSalas.persistencia.models import Relatorio, User, Sala, Reserva, Bloqueio, Edificio
from reservaSalas.persistencia.forms import RegistrationForm, LoginForm, SalaForm
from reservaSalas.persistencia.data import salas_iniciais, usuarios_iniciais, bloqueios_iniciais, relatorios_iniciais, edificios, reservas
from reservaSalas.catalogo.catalogo import cadastrar_sala, consultar_salas, consultar_usuarios
from reservaSalas.acesso.acesso import (
    autenticar,
    cadastrar_usuario,
    encerraSessao,
    exige_permissao,
    is_safe_url,
)
from flask_login import current_user

@app.route("/")
@app.route("/home")
@exige_permissao("CONSULTAR")
def home():
    return render_template("painel.html")

@app.route("/atendimento")
@exige_permissao("ATENDER")
def atendimento():
    return render_template("atendimento.html")

@app.route("/reservar")
@exige_permissao("RESERVAR")
def reservar():
    return render_template("reservar.html")

@app.route("/usuarios", methods=["GET", "POST"])
@exige_permissao("ADMINISTRAR")
def usuarios():
    form = RegistrationForm()
    filtro_matricula = request.args.get("filtro-matricula", "").strip()
    filtro_nome = request.args.get("filtro-nome", "").strip()
    filtro_perfil = request.args.get("filtro-perfil", "all").lower()
    usuarios = consultar_usuarios(filtro_matricula, filtro_nome, filtro_perfil)
    
    perfis = {
            "estudante": "Estudante",
            "user": "Estudante",
            "ESTUDANTE": "Estudante",
            "atendente": "Atendente",
            "ATENDENTE": "Atendente",
            "administrador": "Administrador",
            "admin": "Administrador",
            "ADMINISTRADOR": "Administrador",
    }

    if request.method == "POST":
        novo_usuario = cadastrar_usuario(
            flask_session.get("sessao_acesso"),
            form,
            datetime.now(timezone.utc),
        )
        if novo_usuario is not None:
            flash("Usuário cadastrado com sucesso.", "sucesso")
            return redirect(url_for("usuarios"))
    return render_template(
        "usuarios.html",
        form=form,
        usuarios=usuarios,
        filtro_matricula=filtro_matricula,
        filtro_nome=filtro_nome,
        filtro_perfil=filtro_perfil,
        perfis=perfis,
    )

@app.route("/relatorios", methods=["GET", "POST"])
@exige_permissao("RELATORIO")
def relatorios():
    relatorios = Relatorio.query.order_by(Relatorio.sala_id).all()
    salas = Sala.query.order_by(Sala.nome).all()
    salas_por_id = {sala.id: sala.nome for sala in salas}
    return render_template("relatorios.html", relatorios=relatorios, salas=salas, salas_por_id=salas_por_id)

@app.route("/bloqueios")
@exige_permissao("ADMINISTRAR")
def bloqueios():
    registros = Bloqueio.query.order_by(Bloqueio.data_hora_inicio).all()
    salas = Sala.query.order_by(Sala.nome).all()
    salas_por_id = {sala.id: sala.nome for sala in salas}
    return render_template(
        "bloqueios.html",
        bloqueios=registros,
        salas=salas,
        salas_por_id=salas_por_id,
        agora=datetime.now(),
    )

@app.route("/salas", methods=["GET", "POST"])
@exige_permissao(
    lambda: "ADMINISTRAR" if request.method == "POST" else "CONSULTAR"
)
def salas():
    form = SalaForm()
    edificios_db = Edificio.query.order_by(Edificio.nome).all()
    form.edificio_id.choices = [("", "Escolha...")] + [
        (edificio.id, edificio.nome) for edificio in edificios_db
    ]
    edificio_form = next(
        (edificio for edificio in edificios_db if edificio.id == form.edificio_id.data),
        None,
    )
    edificios_para_andares = [edificio_form] if edificio_form else edificios_db
    andares_form = sorted(
        {
            andar
            for edificio in edificios_para_andares
            for andar in range(edificio.andar_minimo, edificio.andar_maximo + 1)
        }
    )
    form.andar.choices = [("", "Escolha...")] + [
        (
            andar,
            f"{abs(andar)}º subsolo" if andar < 0
            else "Térreo" if andar == 0
            else f"{andar}º andar",
        )
        for andar in andares_form
    ]

    filtro_edificio = request.args.get("filtro-edificio", "")
    valor_filtro_andar = request.args.get("filtro-andar", "").strip()
    try:
        filtro_andar = int(valor_filtro_andar) if valor_filtro_andar else None
    except ValueError:
        abort(400)

    dados_salas = consultar_salas(edificios_db, filtro_edificio, filtro_andar)
    if request.method == "POST" and form.validate_on_submit():
        cadastrar_sala(form.data)
        flash("Sala cadastrada com sucesso.", "sucesso")
        return redirect(url_for("salas"))
    return render_template(
        "salas.html",
        form=form,
        **dados_salas,
    )

@app.route("/minhas-reservas")
@exige_permissao("LISTAR_RESERVAS")
def minhas_reservas():
    return render_template("minhas-reservas.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    auth = autenticar(form, datetime.now(timezone.utc))
    if auth:
        next_page = request.args.get('next')
        if next_page and not is_safe_url(next_page):
             return abort(400)
        return redirect(next_page) if next_page else redirect(url_for('home'))
    elif request.method == 'POST':
        flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template("index.html", form=form)

@app.route("/logout")
def logout():
    encerraSessao(current_user)
    return redirect(url_for('login'))
