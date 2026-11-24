from datetime import timedelta

HORA_ABERTURA = 8
HORA_FECHAMENTO = 22
DURACAO_MINIMA = 30
DURACAO_MAXIMA = 120
DIAS_ANTECEDENCIA = 7
LIMITE_PESSOAL = 2
TOLERANCIA_ENTRADA = timedelta(minutes=15)  # RN07

SITUACOES_OCUPANTES = ["CONFIRMADA", "EM_USO"]

MENSAGENS = {
    "DADOS_INVALIDOS": "Algum campo está vazio ou com valor inválido.",
    "NAO_ENCONTRADO": "Registro não encontrado.",
    "SEM_PERMISSAO": "Você não tem permissão para esta ação.",
    "INTERVALO_INVALIDO": "O início precisa ser antes do fim.",
    "HORARIO_INVALIDO": "Reservas só das 08h às 22h, no mesmo dia, começando em hora cheia ou meia hora.",
    "DURACAO_INVALIDA": "A reserva deve durar de 30 a 120 minutos.",
    "ANTECEDENCIA_INVALIDA": "O início precisa ser depois de agora e, para reservas, no máximo 7 dias à frente.",
    "CAPACIDADE_EXCEDIDA": "O grupo é maior que a capacidade da sala.",
    "RECURSO_INDISPONIVEL": "A sala não tem todos os recursos pedidos.",
    "LIMITE_ATINGIDO": "Você já tem 2 reservas confirmadas futuras. Cancele uma para reservar outra.",
    "CONFLITO_ESTUDANTE": "Você já tem outra reserva nesse mesmo horário.",
    "CONFLITO_SALA": "A sala já está reservada nesse horário. Faça uma nova consulta.",
    "SALA_BLOQUEADA": "A sala está bloqueada para manutenção nesse horário.",
    "SITUACAO_INVALIDA": "A situação atual da reserva não permite esta ação.",
    "PRAZO_ENCERRADO": "A reserva já começou e não pode mais ser cancelada.",
    "FORA_DA_JANELA": "A entrada só pode ser registrada a partir do horário de início.",
    "SALA_EM_USO": "Há uma reserva em uso nesse intervalo. Não é possível bloquear.",
    "BLOQUEIO_SOBREPOSTO": "Já existe um bloqueio ativo nesse intervalo.",
}


def intervalos_sobrepoem(inicio_a, fim_a, inicio_b, fim_b):
    if inicio_a < fim_b and inicio_b < fim_a:
        return True
    else:
        return False


def sala_tem_recursos(sala, recursos_pedidos):
    recursos_da_sala = sala.recursos
    if recursos_da_sala is None:
        recursos_da_sala = []

    for recurso in recursos_pedidos:
        if recurso not in recursos_da_sala:
            return False
    return True


def validar_intervalo(inicio, fim, finalidade, agora):
    if finalidade != "RESERVA" and finalidade != "BLOQUEIO":
        return "DADOS_INVALIDOS"
    if inicio is None or fim is None:
        return "DADOS_INVALIDOS"
    if inicio >= fim:
        return "INTERVALO_INVALIDO"

    if finalidade == "BLOQUEIO":
        if inicio < agora:
            return "ANTECEDENCIA_INVALIDA"
        return None

    if inicio.date() != fim.date():
        return "HORARIO_INVALIDO"

    if inicio.minute != 0 and inicio.minute != 30:
        return "HORARIO_INVALIDO"
    if fim.minute != 0 and fim.minute != 30:
        return "HORARIO_INVALIDO"

    abertura = inicio.replace(hour=HORA_ABERTURA, minute=0)
    fechamento = inicio.replace(hour=HORA_FECHAMENTO, minute=0)
    if inicio < abertura:
        return "HORARIO_INVALIDO"
    if fim > fechamento:
        return "HORARIO_INVALIDO"

    duracao_em_minutos = (fim - inicio).total_seconds() / 60
    if duracao_em_minutos < DURACAO_MINIMA:
        return "DURACAO_INVALIDA"
    if duracao_em_minutos > DURACAO_MAXIMA:
        return "DURACAO_INVALIDA"

    limite = agora + timedelta(days=DIAS_ANTECEDENCIA)
    if inicio <= agora:
        return "ANTECEDENCIA_INVALIDA"
    if inicio > limite:
        return "ANTECEDENCIA_INVALIDA"

    return None


def avaliar_reserva(proposta, sala, reservas_estudante, reservas_sala, bloqueios_sala, agora):
    inicio = proposta["inicio"]
    fim = proposta["fim"]
    grupo = proposta["grupo"]

    erro = validar_intervalo(inicio, fim, "RESERVA", agora)
    if erro is not None:
        return erro

    if grupo is None or grupo < 2:
        return "DADOS_INVALIDOS"

    if grupo > sala.capacidade:
        return "CAPACIDADE_EXCEDIDA"

    if not sala_tem_recursos(sala, proposta["recursos"]):
        return "RECURSO_INDISPONIVEL"

    quantidade_futuras = 0
    for reserva in reservas_estudante:
        if reserva.situacao == "CONFIRMADA" and reserva.data_hora_inicio > agora:
            quantidade_futuras = quantidade_futuras + 1
    if quantidade_futuras >= LIMITE_PESSOAL:
        return "LIMITE_ATINGIDO"

    for reserva in reservas_estudante:
        if reserva.situacao in SITUACOES_OCUPANTES:
            if intervalos_sobrepoem(inicio, fim, reserva.data_hora_inicio, reserva.data_hora_fim):
                return "CONFLITO_ESTUDANTE"

    for bloqueio in bloqueios_sala:
        if bloqueio.situacao == "ATIVO":
            if intervalos_sobrepoem(inicio, fim, bloqueio.data_hora_inicio, bloqueio.data_hora_fim):
                return "SALA_BLOQUEADA"

    for reserva in reservas_sala:
        if reserva.situacao in SITUACOES_OCUPANTES:
            if intervalos_sobrepoem(inicio, fim, reserva.data_hora_inicio, reserva.data_hora_fim):
                return "CONFLITO_SALA"

    return None