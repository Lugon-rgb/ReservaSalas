from reservaSalas import db
from reservaSalas.persistencia.models import Bloqueio, Edificio, Reserva, Sala
from reservaSalas.regras.regras import (
    SITUACOES_OCUPANTES,
    TOLERANCIA_ENTRADA,
    avaliar_reserva,
    intervalos_sobrepoem,
    sala_tem_recursos,
    validar_intervalo,
)


def atualizar_estados(agora):
    quantidade_alterada = 0

    confirmadas = Reserva.query.filter_by(situacao="CONFIRMADA").all()
    for reserva in confirmadas:
        limite_para_entrar = reserva.data_hora_inicio + TOLERANCIA_ENTRADA
        if agora > limite_para_entrar:
            reserva.situacao = "FALTA"
            quantidade_alterada = quantidade_alterada + 1

    em_uso = Reserva.query.filter_by(situacao="EM_USO").all()
    for reserva in em_uso:
        if agora >= reserva.data_hora_fim:
            reserva.situacao = "CONCLUIDA"
            reserva.saida = reserva.data_hora_fim
            quantidade_alterada = quantidade_alterada + 1

    if quantidade_alterada > 0:
        db.session.commit()
    return quantidade_alterada


def sala_ocupada(sala_id, inicio, fim):
    reservas = Reserva.query.filter_by(sala_id=sala_id).all()
    for reserva in reservas:
        if reserva.situacao in SITUACOES_OCUPANTES:
            if intervalos_sobrepoem(inicio, fim, reserva.data_hora_inicio, reserva.data_hora_fim):
                return True

    bloqueios = Bloqueio.query.filter_by(sala_id=sala_id, situacao="ATIVO").all()
    for bloqueio in bloqueios:
        if intervalos_sobrepoem(inicio, fim, bloqueio.data_hora_inicio, bloqueio.data_hora_fim):
            return True

    return False


def consultar_disponibilidade(inicio, fim, grupo, recursos, agora):
    erro = validar_intervalo(inicio, fim, "RESERVA", agora)
    if erro is not None:
        return erro, []
    if grupo is None or grupo < 2:
        return "DADOS_INVALIDOS", []

    atualizar_estados(agora)

    salas_livres = []
    salas_que_cabem = Sala.query.filter(Sala.capacidade >= grupo).order_by(Sala.nome).all()
    for sala in salas_que_cabem:
        if not sala_tem_recursos(sala, recursos):
            continue  # pula para a próxima sala
        if sala_ocupada(sala.id, inicio, fim):
            continue
        salas_livres.append(sala)

    return None, salas_livres


def criar_reserva(usuario, sala_id, inicio, fim, grupo, recursos, agora):
    atualizar_estados(agora)

    sala = db.session.get(Sala, sala_id)
    if sala is None:
        return "NAO_ENCONTRADO", None

    proposta = {
        "inicio": inicio,
        "fim": fim,
        "grupo": grupo,
        "recursos": recursos,
    }
    reservas_estudante = Reserva.query.filter_by(user_matricula=usuario.matricula).all()
    reservas_sala = Reserva.query.filter_by(sala_id=sala.id).all()
    bloqueios_sala = Bloqueio.query.filter_by(sala_id=sala.id).all()

    erro = avaliar_reserva(proposta, sala, reservas_estudante, reservas_sala, bloqueios_sala, agora)
    if erro is not None:
        return erro, None

    nova_reserva = Reserva()
    nova_reserva.user_matricula = usuario.matricula
    nova_reserva.sala_id = sala.id
    nova_reserva.grupo_size = grupo
    nova_reserva.data_hora_inicio = inicio
    nova_reserva.data_hora_fim = fim
    nova_reserva.recursos = recursos
    nova_reserva.situacao = "CONFIRMADA"

    db.session.add(nova_reserva)
    db.session.commit()
    return None, nova_reserva


def listar_reservas(usuario, perfil, filtros, agora):
    atualizar_estados(agora)

    consulta = Reserva.query.join(Sala, Reserva.sala_id == Sala.id)
    consulta = consulta.join(Edificio, Sala.edificio_id == Edificio.id)

    if perfil == "estudante":
        consulta = consulta.filter(Reserva.user_matricula == usuario.matricula)

    periodo = filtros.get("periodo", "todas")
    if periodo == "proximas":
        consulta = consulta.filter(Reserva.data_hora_fim > agora)
    if periodo == "anteriores":
        consulta = consulta.filter(Reserva.data_hora_fim <= agora)

    if filtros.get("situacao"):
        consulta = consulta.filter(Reserva.situacao == filtros["situacao"])

    if filtros.get("data"):
        dia = filtros["data"].isoformat()
        consulta = consulta.filter(db.func.date(Reserva.data_hora_inicio) == dia)

    if filtros.get("edificio"):
        consulta = consulta.filter(Edificio.nome == filtros["edificio"])

    if filtros.get("andar") is not None:
        consulta = consulta.filter(Sala.andar == filtros["andar"])

    if filtros.get("sala"):
        consulta = consulta.filter(Sala.nome == filtros["sala"])

    consulta = consulta.order_by(Reserva.data_hora_inicio, Reserva.id)
    return consulta.all()


def cancelar_reserva(usuario, perfil, reserva_id, motivo, agora):
    atualizar_estados(agora)

    reserva = db.session.get(Reserva, reserva_id)
    if reserva is None:
        return "NAO_ENCONTRADO", None

    if perfil == "atendente":
        return "SEM_PERMISSAO", None
    if perfil == "estudante" and reserva.user_matricula != usuario.matricula:
        return "SEM_PERMISSAO", None

    if motivo is None or motivo.strip() == "":
        return "DADOS_INVALIDOS", None
    if reserva.situacao != "CONFIRMADA":
        return "SITUACAO_INVALIDA", None
    if agora >= reserva.data_hora_inicio:
        return "PRAZO_ENCERRADO", None

    reserva.situacao = "CANCELADA"
    reserva.motivo_cancelamento = motivo.strip()
    reserva.cancelada_por = usuario.matricula
    reserva.cancelada_em = agora
    db.session.commit()
    return None, reserva


def registrar_entrada(reserva_id, agora):
    """F15 registrarEntrada (RN07): do início até 15 minutos depois."""
    atualizar_estados(agora)

    reserva = db.session.get(Reserva, reserva_id)
    if reserva is None:
        return "NAO_ENCONTRADO", None
    if reserva.situacao != "CONFIRMADA":
        return "SITUACAO_INVALIDA", None
    if agora < reserva.data_hora_inicio:
        return "FORA_DA_JANELA", None

    reserva.situacao = "EM_USO"
    reserva.entrada = agora
    db.session.commit()
    return None, reserva


def encerrar_uso(reserva_id, agora):
    atualizar_estados(agora)

    reserva = db.session.get(Reserva, reserva_id)
    if reserva is None:
        return "NAO_ENCONTRADO", None

    if reserva.situacao == "CONCLUIDA":
        return None, reserva
    if reserva.situacao != "EM_USO":
        return "SITUACAO_INVALIDA", None

    reserva.situacao = "CONCLUIDA"
    reserva.saida = agora
    db.session.commit()
    return None, reserva


def criar_bloqueio(usuario, sala_id, inicio, fim, motivo, agora):
    erro = validar_intervalo(inicio, fim, "BLOQUEIO", agora)
    if erro is not None:
        return erro, None, []
    if motivo is None or motivo.strip() == "":
        return "DADOS_INVALIDOS", None, []

    atualizar_estados(agora)

    sala = db.session.get(Sala, sala_id)
    if sala is None:
        return "NAO_ENCONTRADO", None, []

    reservas_atingidas = []
    reservas_sala = Reserva.query.filter_by(sala_id=sala.id).all()
    for reserva in reservas_sala:
        if reserva.situacao in SITUACOES_OCUPANTES:
            if intervalos_sobrepoem(inicio, fim, reserva.data_hora_inicio, reserva.data_hora_fim):
                reservas_atingidas.append(reserva)

    for reserva in reservas_atingidas:
        if reserva.situacao == "EM_USO":
            return "SALA_EM_USO", None, []

    bloqueios_ativos = Bloqueio.query.filter_by(sala_id=sala.id, situacao="ATIVO").all()
    for outro in bloqueios_ativos:
        if intervalos_sobrepoem(inicio, fim, outro.data_hora_inicio, outro.data_hora_fim):
            return "BLOQUEIO_SOBREPOSTO", None, []

    novo_bloqueio = Bloqueio()
    novo_bloqueio.sala_id = sala.id
    novo_bloqueio.data_hora_inicio = inicio
    novo_bloqueio.data_hora_fim = fim
    novo_bloqueio.motivo = motivo.strip()
    novo_bloqueio.situacao = "ATIVO"
    novo_bloqueio.criado_por = usuario.matricula
    db.session.add(novo_bloqueio)
    db.session.flush()

    ids_cancelados = []
    for reserva in reservas_atingidas:
        reserva.situacao = "CANCELADA"
        reserva.motivo_cancelamento = "Interdição da sala: " + novo_bloqueio.motivo
        reserva.cancelada_por = usuario.matricula
        reserva.cancelada_em = agora
        reserva.bloqueio_id = novo_bloqueio.id
        ids_cancelados.append(reserva.id)

    db.session.commit()
    return None, novo_bloqueio, ids_cancelados


def retirar_bloqueio(usuario, bloqueio_id, agora):
    bloqueio = db.session.get(Bloqueio, bloqueio_id)
    if bloqueio is None:
        return "NAO_ENCONTRADO", None

    if bloqueio.situacao == "CANCELADO":
        return None, bloqueio

    bloqueio.situacao = "CANCELADO"
    bloqueio.retirado_por = usuario.matricula
    bloqueio.retirado_em = agora
    db.session.commit()
    return None, bloqueio