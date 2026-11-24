from flask import render_template, url_for, flash, redirect, request, abort, session as flask_session
from datetime import datetime, timezone
from datetime import date, timedelta
from flask import g
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
from reservaSalas.persistencia.forms import (
    AtendimentoForm,
    BloqueioForm,
    CancelarReservaForm,
    ReservaForm,
    RetirarBloqueioForm,
)
from reservaSalas.regras.regras import MENSAGENS
from reservaSalas.agenda.agenda import (
    cancelar_reserva,
    consultar_disponibilidade,
    criar_bloqueio,
    criar_reserva,
    encerrar_uso,
    listar_reservas,
    registrar_entrada,
    retirar_bloqueio,
)
from reservaSalas.relatorios.relatorios import gerar_relatorio
from flask_login import current_user

@app.route("/")
@app.route("/home")
@exige_permissao("CONSULTAR")
def home():
    return render_template("painel.html")

def hora_atual():
    agora = datetime.now()
    agora = agora.replace(second=0, microsecond=0)  # so ate os minutos
    return agora


def mensagem_do_erro(codigo):
    if codigo in MENSAGENS:
        return MENSAGENS[codigo]
    return codigo


def texto_para_data(texto):
    if texto is None or texto == "":
        return None
    try:
        return date.fromisoformat(texto)
    except ValueError:
        return None


def texto_para_inteiro(texto):
    if texto is None or texto == "":
        return None
    try:
        return int(texto)
    except ValueError:
        return None


def opcoes_dos_filtros():
    edificios_db = Edificio.query.order_by(Edificio.nome).all()

    andares = []
    for edificio in edificios_db:
        for andar in range(edificio.andar_minimo, edificio.andar_maximo + 1):
            if andar not in andares:
                andares.append(andar)
    andares.sort()

    salas_db = Sala.query.order_by(Sala.nome).all()
    return edificios_db, andares, salas_db


def nomes_dos_usuarios():
    nomes = {}
    for usuario in User.query.all():
        nomes[usuario.matricula] = usuario.nome
    return nomes


@app.route("/atendimento", methods=["GET", "POST"])
@exige_permissao("ATENDER")
def atendimento():
    agora = hora_atual()
    form = AtendimentoForm()

    if request.method == "POST":
        if form.validate_on_submit():
            reserva_id = texto_para_inteiro(form.reserva_id.data)

            if form.acao.data == "entrada":
                erro, reserva = registrar_entrada(reserva_id, agora)
                texto_sucesso = "Entrada registrada."
            else:
                erro, reserva = encerrar_uso(reserva_id, agora)
                texto_sucesso = "Saída registrada."

            if erro is None:
                flash(texto_sucesso, "sucesso")
            else:
                flash(mensagem_do_erro(erro), "danger")
        return redirect(request.full_path)

    data_filtro = texto_para_data(request.args.get("data"))
    if data_filtro is None:
        data_filtro = agora.date()

    filtros = {
        "periodo": "todas",
        "data": data_filtro,
        "edificio": request.args.get("edificio", ""),
        "andar": texto_para_inteiro(request.args.get("andar")),
        "sala": request.args.get("sala", ""),
    }

    usuario = g.autorizacao[0]
    perfil = g.autorizacao[1]
    reservas = listar_reservas(usuario, perfil, filtros, agora)
    edificios_db, andares, salas_db = opcoes_dos_filtros()

    return render_template(
        "atendimento.html",
        form=form,
        reservas=reservas,
        data_filtro=data_filtro,
        filtros=filtros,
        nomes=nomes_dos_usuarios(),
        edificios=edificios_db,
        andares=andares,
        salas=salas_db,
    )


@app.route("/reservar", methods=["GET", "POST"])
@exige_permissao("RESERVAR")
def reservar():
    agora = hora_atual()
    form = ReservaForm()

    if request.method == "POST":
        if form.validate_on_submit():
            try:
                inicio = datetime.strptime(form.inicio.data, "%Y-%m-%dT%H:%M")
            except ValueError:
                inicio = None

            duracao = texto_para_inteiro(form.duracao.data)
            if inicio is not None and duracao is not None:
                fim = inicio + timedelta(minutes=duracao)
            else:
                fim = None

            recursos = []
            if form.recursos.data:
                recursos = form.recursos.data.split(",")

            usuario = g.autorizacao[0]  # o responsável é quem está logado
            erro, reserva = criar_reserva(
                usuario,
                texto_para_inteiro(form.sala_id.data),
                inicio,
                fim,
                texto_para_inteiro(form.grupo.data),
                recursos,
                agora,
            )

            if erro is None:
                dia = reserva.data_hora_inicio.strftime("%d/%m/%Y")
                hora_inicio = reserva.data_hora_inicio.strftime("%H:%M")
                hora_fim = reserva.data_hora_fim.strftime("%H:%M")
                flash(
                    f"Reserva confirmada: sala {reserva.sala.nome}, {dia}, das {hora_inicio} às {hora_fim}.",
                    "sucesso",
                )
                return redirect(url_for("minhas_reservas"))

            flash(mensagem_do_erro(erro), "danger")

        if request.referrer:
            return redirect(request.referrer)
        return redirect(url_for("reservar"))

    amanha = agora + timedelta(days=1)
    consulta = {
        "data": request.args.get("data", amanha.date().isoformat()),
        "hora": request.args.get("inicio-hora", "10"),
        "minuto": request.args.get("inicio-minuto", "00"),
        "duracao": request.args.get("duracao", "90"),
        "grupo": request.args.get("grupo", "4"),
        "recursos": request.args.getlist("recursos"),
    }

    salas_livres = None
    inicio = None
    fim = None
    erro = None

    if "data" in request.args:
        texto_inicio = consulta["data"] + " " + consulta["hora"] + ":" + consulta["minuto"]
        try:
            inicio = datetime.strptime(texto_inicio, "%Y-%m-%d %H:%M")
        except ValueError:
            inicio = None

        duracao = texto_para_inteiro(consulta["duracao"])
        if inicio is not None and duracao is not None:
            fim = inicio + timedelta(minutes=duracao)

        grupo = texto_para_inteiro(consulta["grupo"])
        erro, salas_livres = consultar_disponibilidade(inicio, fim, grupo, consulta["recursos"], agora)

    if erro is not None:
        texto_erro = mensagem_do_erro(erro)
    else:
        texto_erro = None

    return render_template(
        "reservar.html",
        form=form,
        consulta=consulta,
        salas_livres=salas_livres,
        inicio=inicio,
        fim=fim,
        erro=texto_erro,
    )

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

@app.route("/relatorios")
@exige_permissao("RELATORIO")
def relatorios():
    agora = hora_atual()

    hoje = agora.date()
    primeiro_dia_do_mes = hoje.replace(day=1)
    dia_no_proximo_mes = primeiro_dia_do_mes + timedelta(days=32)
    primeiro_dia_do_proximo_mes = dia_no_proximo_mes.replace(day=1)
    ultimo_dia_do_mes = primeiro_dia_do_proximo_mes - timedelta(days=1)

    de = texto_para_data(request.args.get("de"))
    if de is None:
        de = primeiro_dia_do_mes

    ate = texto_para_data(request.args.get("ate"))
    if ate is None:
        ate = ultimo_dia_do_mes

    sala_id = texto_para_inteiro(request.args.get("sala"))

    periodo_inicio = datetime(de.year, de.month, de.day)
    dia_seguinte = ate + timedelta(days=1)
    periodo_fim = datetime(dia_seguinte.year, dia_seguinte.month, dia_seguinte.day)

    erro, linhas = gerar_relatorio(periodo_inicio, periodo_fim, sala_id, agora)
    if erro is not None:
        texto_erro = mensagem_do_erro(erro)
    else:
        texto_erro = None

    return render_template(
        "relatorios.html",
        linhas=linhas,
        erro=texto_erro,
        de=de,
        ate=ate,
        sala_id=sala_id,
        salas=Sala.query.order_by(Sala.nome).all(),
        gerado_em=agora,
    )


@app.route("/bloqueios", methods=["GET", "POST"])
@exige_permissao("ADMINISTRAR")
def bloqueios():
    agora = hora_atual()
    salas = Sala.query.order_by(Sala.nome).all()

    form = BloqueioForm()
    form.sala_id.choices = [("", "Selecione")]
    for sala in salas:
        form.sala_id.choices.append((sala.id, sala.nome))

    form_retirar = RetirarBloqueioForm()

    if request.method == "POST":
        usuario = g.autorizacao[0]

        if form_retirar.submit_retirar.data and form_retirar.validate_on_submit():
            bloqueio_id = texto_para_inteiro(form_retirar.bloqueio_id.data)
            erro, bloqueio = retirar_bloqueio(usuario, bloqueio_id, agora)
            if erro is None:
                flash("Bloqueio retirado.", "sucesso")
            else:
                flash(mensagem_do_erro(erro), "danger")
            return redirect(url_for("bloqueios"))

        if form.submit_bloqueio.data and form.validate_on_submit():
            erro, bloqueio, cancelados = criar_bloqueio(
                usuario,
                form.sala_id.data,
                form.inicio.data,
                form.fim.data,
                form.motivo.data,
                agora,
            )
            if erro is None:
                texto = "Bloqueio criado."
                if len(cancelados) > 0:
                    texto = texto + f" {len(cancelados)} reserva(s) cancelada(s) por interdição."
                flash(texto, "sucesso")
                return redirect(url_for("bloqueios"))
            flash(mensagem_do_erro(erro), "danger")

    salas_por_id = {}
    for sala in salas:
        salas_por_id[sala.id] = sala.nome

    registros = Bloqueio.query.order_by(Bloqueio.data_hora_inicio).all()
    return render_template(
        "bloqueios.html",
        form=form,
        form_retirar=form_retirar,
        bloqueios=registros,
        salas=salas,
        salas_por_id=salas_por_id,
        agora=agora,
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

def permissao_minhas_reservas():
    if request.method == "POST":
        return "CANCELAR"
    return "LISTAR_RESERVAS"


@app.route("/minhas-reservas", methods=["GET", "POST"])
@exige_permissao(permissao_minhas_reservas)
def minhas_reservas():
    agora = hora_atual()
    usuario = g.autorizacao[0]
    perfil = g.autorizacao[1]

    proximas_confirmadas = listar_reservas(
        usuario, perfil, {"periodo": "proximas", "situacao": "CONFIRMADA"}, agora
    )
    cancelaveis = []
    for reserva in proximas_confirmadas:
        if reserva.data_hora_inicio > agora:
            cancelaveis.append(reserva)

    form = CancelarReservaForm()
    form.reserva_id.choices = [("", "Escolha...")]
    ids_cancelaveis = []
    for reserva in cancelaveis:
        dia_e_hora = reserva.data_hora_inicio.strftime("%d/%m/%Y · %H:%M")
        hora_fim = reserva.data_hora_fim.strftime("%H:%M")
        texto = f"{reserva.sala.nome} · {dia_e_hora} – {hora_fim}"
        form.reserva_id.choices.append((reserva.id, texto))
        ids_cancelaveis.append(reserva.id)

    if request.method == "POST":
        if form.validate_on_submit():
            erro, reserva = cancelar_reserva(usuario, perfil, form.reserva_id.data, form.motivo.data, agora)
            if erro is None:
                flash("Reserva cancelada.", "sucesso")
                return redirect(url_for("minhas_reservas"))
            flash(mensagem_do_erro(erro), "danger")

    if request.method == "GET" and request.args.get("cancelar"):
        form.reserva_id.data = texto_para_inteiro(request.args.get("cancelar"))

    filtros = {
        "periodo": request.args.get("periodo", "proximas"),
        "situacao": request.args.get("situacao", ""),
    }
    reservas = listar_reservas(usuario, perfil, filtros, agora)

    return render_template(
        "minhas-reservas.html",
        form=form,
        reservas=reservas,
        filtros=filtros,
        ids_cancelaveis=ids_cancelaveis,
        nomes=nomes_dos_usuarios(),
        perfil=perfil,
    )

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
