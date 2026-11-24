from reservaSalas.persistencia.models import Edificio, Sala, User
from reservaSalas import db

def cadastrar_sala(dados_sala):
    nova_sala = Sala()
    nova_sala.nome = dados_sala['nome']
    nova_sala.capacidade = dados_sala['capacidade']
    nova_sala.edificio_id = dados_sala['edificio_id']
    nova_sala.andar = dados_sala['andar']
    nova_sala.recursos = dados_sala['recursos']

    db.session.add(nova_sala)
    db.session.commit()
    return nova_sala

def consultar_salas(e_db, filtro_edificio, filtro_andar):
    edificio_selecionado = next(
        (edificio for edificio in e_db if edificio.nome == filtro_edificio),
        None,
    )
    if filtro_edificio and edificio_selecionado is None:
        filtro_edificio = ""

    consulta_salas = Sala.query.join(Edificio)
    if filtro_edificio:
        consulta_salas = consulta_salas.filter(Edificio.nome == filtro_edificio)
    if filtro_andar is not None:
        consulta_salas = consulta_salas.filter(Sala.andar == filtro_andar)
    salas_db = consulta_salas.order_by(Sala.nome).all()

    contagem_edificios = {
        edificio.nome: len(edificio.salas)
        for edificio in e_db
    }
    edificios_para_andares = (
        [edificio_selecionado]
        if edificio_selecionado
        else e_db
    )
    andares = sorted(
        {
            andar
            for edificio in edificios_para_andares
            for andar in range(edificio.andar_minimo, edificio.andar_maximo + 1)
        }
    )

    return {
        "edificios": e_db,
        "edificios_com_contagem": contagem_edificios,
        "salas": salas_db,
        "andares": andares,
        "filtro_edificio": filtro_edificio,
        "filtro_andar": filtro_andar,
    }

def consultar_usuarios(filtro_matricula, filtro_nome, filtro_perfil):
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
    tipos_por_perfil = {
        "estudante": ("estudante", "user", "ESTUDANTE", "USER"),
        "atendente": ("atendente", "ATENDENTE"),
        "administrador": ("administrador", "admin", "ADMINISTRADOR", "ADMIN"),
    }

    consulta_usuarios = User.query
    if filtro_matricula:
        consulta_usuarios = consulta_usuarios.filter(
            User.matricula.ilike(f"%{filtro_matricula}%")
        )
    if filtro_nome:
        consulta_usuarios = consulta_usuarios.filter(
            User.nome.ilike(f"%{filtro_nome}%")
        )
    if filtro_perfil in tipos_por_perfil:
        consulta_usuarios = consulta_usuarios.filter(
            User.type.in_(tipos_por_perfil[filtro_perfil])
        )
    else:
        filtro_perfil = "all"
    consulta_usuarios.order_by(User.matricula).all()
    return consulta_usuarios
