from reservaSalas import app, db
from datetime import datetime, timezone

class User(db.Model):
    matricula = db.Column(db.String(20), unique=True, primary_key=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    
    def __repr__(self):
        return f"User('{self.matricula}', '{self.password}')"

class Sala(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    capacidade = db.Column(db.Integer, nullable=False)
    localizacao = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f"Sala('{self.nome}', '{self.capacidade}', '{self.localizacao}')"
    
class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_matricula = db.Column(db.String(20), db.ForeignKey('user.matricula'), nullable=False)
    sala_id = db.Column(db.Integer, db.ForeignKey('sala.id'), nullable=False)
    data_hora_inicio = db.Column(db.DateTime, nullable=False)
    data_hora_fim = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f"Reserva('{self.user_matricula}', '{self.sala_id}', '{self.data_hora_inicio}', '{self.data_hora_fim}')"
    
class Bloqueio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sala_id = db.Column(db.Integer, db.ForeignKey('sala.id'), nullable=False)
    data_hora_inicio = db.Column(db.DateTime, nullable=False)
    data_hora_fim = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f"Bloqueio('{self.sala_id}', '{self.data_hora_inicio}', '{self.data_hora_fim}')"
    
class Edificio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    localizacao = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f"Edificio('{self.nome}', '{self.localizacao}')"