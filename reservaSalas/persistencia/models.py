from flask_login import UserMixin
from reservaSalas import db, login_manager
from sqlalchemy import JSON
from datetime import datetime, timezone

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)

class User(db.Model, UserMixin):
    matricula = db.Column(db.String(20), unique=True, primary_key=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(60), nullable=False)
    type = db.Column(db.String(20), nullable=False, default='user')  # 'user', 'admin' ou 'atendente'

    def get_id(self):
        return self.matricula
    
    def __repr__(self):
        return f"User('{self.matricula}', '{self.nome}', '{self.password}', '{self.type}')"


class SessaoAcesso(db.Model):
    id = db.Column(db.String(64), primary_key=True)
    user_matricula = db.Column(
        db.String(20), db.ForeignKey('user.matricula'), nullable=False, index=True
    )
    criada_em = db.Column(db.DateTime(timezone=True), nullable=False)
    expira_em = db.Column(db.DateTime(timezone=True), nullable=False)
    revogada_em = db.Column(db.DateTime(timezone=True))


class Sala(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    capacidade = db.Column(db.Integer, nullable=False)
    edificio_id = db.Column(db.Integer, db.ForeignKey('edificio.id'), nullable=False)
    andar = db.Column(db.Integer, nullable=False)
    recursos = db.Column(JSON, nullable=False, default=list)
    
    def __repr__(self):
        return f"Sala('{self.nome}', '{self.capacidade}', '{self.edificio_id}', '{self.recursos}')"
    
class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_matricula = db.Column(db.String(20), db.ForeignKey('user.matricula'), nullable=False)
    sala_id = db.Column(db.Integer, db.ForeignKey('sala.id'), nullable=False)
    grupo_size = db.Column(db.Integer, nullable=False)
    data_hora_inicio = db.Column(db.DateTime, nullable=False)
    data_hora_fim = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f"Reserva('{self.user_matricula}', '{self.sala_id}', '{self.grupo_size}', '{self.data_hora_inicio}', '{self.data_hora_fim}')"

class Relatorio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sala_id = db.Column(db.Integer, db.ForeignKey('sala.id'), nullable=False)
    confirmadas = db.Column(db.Integer, nullable=False)
    concluidas = db.Column(db.Integer, nullable=False)
    canceladas = db.Column(db.Integer, nullable=False)
    em_uso = db.Column(db.Integer, nullable=False)
    faltas = db.Column(db.Integer, nullable=False)
    min_uso = db.Column(db.Integer, nullable=False)
    
    def __repr__(self):
        return f"Relatorio('{self.sala_id}', '{self.confirmadas}', '{self.concluidas}', '{self.canceladas}', '{self.em_uso}', '{self.faltas}', '{self.min_uso}')"

class Bloqueio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sala_id = db.Column(db.Integer, db.ForeignKey('sala.id'), nullable=False)
    data_hora_inicio = db.Column(db.DateTime, nullable=False)
    data_hora_fim = db.Column(db.DateTime, nullable=False)
    motivo = db.Column(db.String(200), nullable=False)
    
    def __repr__(self):
        return f"Bloqueio('{self.sala_id}', '{self.data_hora_inicio}', '{self.data_hora_fim}')"
    
class Edificio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    andar_minimo = db.Column(db.Integer, nullable=False)
    andar_maximo = db.Column(db.Integer, nullable=False)
    salas = db.relationship('Sala', backref='edificio', lazy=True)
    
    def __repr__(self):
        return f"Edificio('{self.nome}', '{self.andar_maximo + abs(self.andar_minimo)}', '{self.andar_minimo}', '{self.andar_maximo}', '{self.salas}')"