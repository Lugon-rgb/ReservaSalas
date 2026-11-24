from reservaSalas.persistencia.models import Relatorio, User, Sala, Reserva, Bloqueio, Edificio
from datetime import datetime, timezone
from reservaSalas import app, db, Bcrypt

salas_iniciais = [
    {
        "nome": "F305",
        "capacidade": 2,
        "edificio": "Edifício Frings",
        "andar": 3,
        "recursos": []
    },
    {
        "nome": "K210",
        "capacidade": 8,
        "edificio": "Edifício Kennedy",
        "andar": 2,
        "recursos": ["Projetor", "Quadro branco", "Computador"]
    },
    {
        "nome": "L101",
        "capacidade": 4,
        "edificio": "Edifício Leme",
        "andar": 1,
        "recursos": ["Quadro branco"]
    },
    {
        "nome": "L104",
        "capacidade": 6,
        "edificio": "Edifício Leme",
        "andar": 1,
        "recursos": ["Quadro branco", "TV"]
    }
]

usuarios_iniciais = [
    {
        "nome": "Ana Souza",
        "matricula": "0000001",
        "password": "password",
        "type": "administrador"
    },
    {
        "nome": "Marcos Pereira",
        "matricula": "0000002",
        "password": "password",
        "type": "atendente"
    },
    {
        "nome": "Bruno Lima",
        "matricula": "2410001",
        "password": "password",
        "type": "estudante"
    },
    {
        "nome": "Carla Dias",
        "matricula": "2410002",
        "password": "password",
        "type": "estudante"
    },
    {
        "nome": "Diego Alves",
        "matricula": "2410003",
        "password": "password",
        "type": "estudante"
    },
    {
        "nome": "Elisa Rocha",
        "matricula": "2410004",
        "password": "password",
        "type": "estudante"
    }
]

bloqueios_iniciais = [
    {
        "sala_id": 2,
        "data_hora_inicio": datetime(2026, 11, 26, 8, 0, tzinfo=timezone.utc),
        "data_hora_fim": datetime(2026, 11, 28, 22, 0, tzinfo=timezone.utc),
        "motivo": "Troca do projetor"
    },
    {
        "sala_id": 3,
        "data_hora_inicio": datetime(2026, 11, 10, 8, 0, tzinfo=timezone.utc),
        "data_hora_fim": datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc),
        "motivo": "Pintura"
    }
]

reservas = [
    {
        "user_matricula": "2410001",
        "sala_id": 4,
        "grupo_size": 4,
        "data_hora_inicio": datetime(2026, 11, 20, 10, 0, tzinfo=timezone.utc),
        "data_hora_fim": datetime(2026, 11, 20, 11, 30, tzinfo=timezone.utc)
    },
    {
        "user_matricula": "2410002",
        "sala_id": 2,
        "grupo_size": 6,
        "data_hora_inicio": datetime(2026, 11, 27, 14, 0, tzinfo=timezone.utc),
        "data_hora_fim": datetime(2026, 11, 27, 16, 0, tzinfo=timezone.utc)
    },
    {
        "user_matricula": "2410003",
        "sala_id": 3,
        "grupo_size": 3,
        "data_hora_inicio": datetime(2026, 11, 20, 9, 0, tzinfo=timezone.utc),
        "data_hora_fim": datetime(2026, 11, 20, 10, 0, tzinfo=timezone.utc)
    },
    {
        "user_matricula": "2410004",
        "sala_id": 4,
        "grupo_size": 5,
        "data_hora_inicio": datetime(2026, 11, 18, 15, 0, tzinfo=timezone.utc),
        "data_hora_fim": datetime(2026, 11, 18, 16, 30, tzinfo=timezone.utc)
    },
    {
        "user_matricula": "2410001",
        "sala_id": 2,
        "grupo_size": 4,
        "data_hora_inicio": datetime(2026, 11, 17, 11, 0, tzinfo=timezone.utc),
        "data_hora_fim": datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)
    }
]

edificios = [
    {
        "nome": "Edifício Frings",
        "andar_minimo": -1,
        "andar_maximo": 3
    },
    {
        "nome": "Edifício Kennedy",
        "andar_minimo": -1,
        "andar_maximo": 2
    },
    {
        "nome": "Edifício Leme",
        "andar_minimo": -1,
        "andar_maximo": 2
    },
    {
        "nome": "Rio DataCentro(RDC)",
        "andar_minimo": -1,
        "andar_maximo": 2
    }
]

relatorios_iniciais = [
    {
        "sala_id": 1,
        "cofirmadas": 1,
        "em_uso": 0,
        "concluidas": 6,
        "faltas": 1,
        "canceladas": 0,
        "min_uso": 340
    },
    {
        "sala_id": 2,
        "cofirmadas": 2,
        "em_uso": 0,
        "concluidas": 9,
        "faltas": 2,
        "canceladas": 3,
        "min_uso": 760
    },
    {
        "sala_id": 3,
        "cofirmadas": 0,
        "em_uso": 0,
        "concluidas": 12,
        "faltas": 0,
        "canceladas": 1,
        "min_uso": 655
    },
    {
        "sala_id": 4,
        "cofirmadas": 1,
        "em_uso": 1,
        "concluidas": 8,
        "faltas": 3,
        "canceladas": 2,
        "min_uso": 590
    }
]

@app.cli.command("seed-data")
def seed_data():
    edificios_por_nome = {}
    for datos_edificio in edificios:
        edificio = Edificio.query.filter_by(nome=datos_edificio["nome"]).first()
        if edificio is None:
            edificio = Edificio()
            edificio.nome = datos_edificio["nome"]
            db.session.add(edificio)
        edificio.andar_minimo = datos_edificio["andar_minimo"]
        edificio.andar_maximo = datos_edificio["andar_maximo"]
        db.session.flush()
        edificios_por_nome[edificio.nome] = edificio

    for datos_usuario in usuarios_iniciais:
        if db.session.get(User, datos_usuario["matricula"]) is None:
            usuario = User()
            usuario.nome = datos_usuario["nome"]
            usuario.matricula = datos_usuario["matricula"]
            usuario.password = Bcrypt.generate_password_hash(datos_usuario["password"]).decode("utf-8")
            usuario.type = datos_usuario["type"]
            db.session.add(usuario)

    for datos_relatorio in relatorios_iniciais:
        sala = Sala.query.filter_by(id=datos_relatorio["sala_id"]).first()
        if sala is None:
            continue
        existente = Relatorio.query.filter_by(sala_id=sala.id).first()
        if existente is None:
            relatorio = Relatorio()
            relatorio.sala_id = sala.id
            relatorio.confirmadas = datos_relatorio["cofirmadas"]
            relatorio.em_uso = datos_relatorio["em_uso"]
            relatorio.concluidas = datos_relatorio["concluidas"]
            relatorio.faltas = datos_relatorio["faltas"]
            relatorio.canceladas = datos_relatorio["canceladas"]
            relatorio.min_uso = datos_relatorio["min_uso"]
            db.session.add(relatorio)
    
    salas_por_indice = {}
    for indice, datos_sala in enumerate(salas_iniciais, start=1):
        sala = Sala.query.filter_by(nome=datos_sala["nome"]).first()
        if sala is None:
            sala = Sala()
            sala.nome = datos_sala["nome"]
            sala.capacidade = datos_sala["capacidade"]
            sala.edificio_id = edificios_por_nome[datos_sala["edificio"]].id
            sala.andar = datos_sala["andar"]
            sala.recursos = datos_sala["recursos"]
            db.session.add(sala)
            db.session.flush()
        salas_por_indice[indice] = sala

    for datos_bloqueio in bloqueios_iniciais:
        sala = salas_por_indice[datos_bloqueio["sala_id"]]
        inicio = datos_bloqueio["data_hora_inicio"].astimezone().replace(tzinfo=None)
        fim = datos_bloqueio["data_hora_fim"].astimezone().replace(tzinfo=None)
        existente = Bloqueio.query.filter_by(
            sala_id=sala.id,
            data_hora_inicio=inicio,
            data_hora_fim=fim,
            motivo=datos_bloqueio["motivo"],
        ).first()
        if existente is None:
            bloqueio = Bloqueio()
            bloqueio.sala_id = sala.id
            bloqueio.data_hora_inicio = inicio
            bloqueio.data_hora_fim = fim
            bloqueio.motivo = datos_bloqueio["motivo"]
            db.session.add(bloqueio)

    for datos_reserva in reservas:
        inicio = datos_reserva["data_hora_inicio"].astimezone().replace(tzinfo=None)
        fim = datos_reserva["data_hora_fim"].astimezone().replace(tzinfo=None)
        sala = salas_por_indice[datos_reserva["sala_id"]]
        existente = Reserva.query.filter_by(
            user_matricula=datos_reserva["user_matricula"],
            sala_id=sala.id,
            data_hora_inicio=inicio,
            data_hora_fim=fim,
        ).first()
        if existente is None:
            reserva = Reserva()
            reserva.user_matricula = datos_reserva["user_matricula"]
            reserva.sala_id = sala.id
            reserva.grupo_size = datos_reserva["grupo_size"]
            reserva.data_hora_inicio = inicio
            reserva.data_hora_fim = fim
            db.session.add(reserva)

    db.session.commit()
    print("Initial development data loaded.")
