from reservaSalas.agenda.agenda import atualizar_estados
from reservaSalas.persistencia.models import Reserva, Sala


def minutos_dentro_do_periodo(inicio, fim, periodo_inicio, periodo_fim):
    if inicio > periodo_inicio:
        comeco = inicio
    else:
        comeco = periodo_inicio

    if fim < periodo_fim:
        final = fim
    else:
        final = periodo_fim

    if final <= comeco:
        return 0

    segundos = (final - comeco).total_seconds()
    return int(segundos // 60)

def gerar_relatorio(periodo_inicio, periodo_fim, sala_id, agora):
    if periodo_inicio is None or periodo_fim is None:
        return "DADOS_INVALIDOS", []
    if periodo_inicio >= periodo_fim:
        return "DADOS_INVALIDOS", []

    if sala_id:
        salas = Sala.query.filter_by(id=sala_id).all()
        if len(salas) == 0:
            return "NAO_ENCONTRADO", []
    else:
        salas = Sala.query.order_by(Sala.nome).all()

    atualizar_estados(agora)

    linhas = []
    for sala in salas:
        linha = {
            "sala": sala.nome,
            "CONFIRMADA": 0,
            "EM_USO": 0,
            "CONCLUIDA": 0,
            "FALTA": 0,
            "CANCELADA": 0,
            "min_uso": 0,
        }

        reservas = Reserva.query.filter_by(sala_id=sala.id).all()
        for reserva in reservas:
            if reserva.data_hora_inicio >= periodo_inicio and reserva.data_hora_inicio < periodo_fim:
                linha[reserva.situacao] = linha[reserva.situacao] + 1

            if reserva.situacao == "CONCLUIDA" and reserva.entrada is not None and reserva.saida is not None:
                minutos = minutos_dentro_do_periodo(reserva.entrada, reserva.saida, periodo_inicio, periodo_fim)
                linha["min_uso"] = linha["min_uso"] + minutos

            if reserva.situacao == "EM_USO" and reserva.entrada is not None:
                if agora < reserva.data_hora_fim:
                    ate_quando = agora
                else:
                    ate_quando = reserva.data_hora_fim
                minutos = minutos_dentro_do_periodo(reserva.entrada, ate_quando, periodo_inicio, periodo_fim)
                linha["min_uso"] = linha["min_uso"] + minutos

        linhas.append(linha)

    return None, linhas