from flask_wtf import FlaskForm
from wtforms import (
    DateTimeLocalField,
    HiddenField,
    TextAreaField,
    IntegerField,
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    SelectField,
    SelectMultipleField,
    ValidationError,
)
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange
from reservaSalas.persistencia.models import Sala, User
from wtforms.widgets import CheckboxInput, ListWidget


def opcional_inteiro(valor):
    return int(valor) if valor else None

class RegistrationForm(FlaskForm):
    matricula = StringField('Matrícula', 
                            validators=[DataRequired(), Length(min=2, max=20)])
    nome = StringField('Nome completo',
                       validators=[DataRequired(), Length(min=2, max=100)])
    type = SelectField('Perfil',
                       choices=[
                           ('ESTUDANTE', 'Estudante'),
                           ('ATENDENTE', 'Atendente'),
                           ('ADMINISTRADOR', 'Administrador'),
                       ],
                       validators=[DataRequired()])
    password = PasswordField('Senha inicial',
                             validators=[DataRequired(), Length(min=6, max=20)])
    submit = SubmitField('Cadastrar usuário')
    
    def validate_matricula(self, matricula):
        if User.query.filter_by(matricula=matricula.data).first():
            raise ValidationError('Matrícula já cadastrada. Por favor, escolha outra matrícula.')
        pass
    
class LoginForm(FlaskForm):
    matricula = StringField('Matrícula', 
                        validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password',
                             validators=[DataRequired(), Length(min=6, max=20)])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')
    
class SalaForm(FlaskForm):
    nome = StringField(
        'Código',
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    capacidade = IntegerField(
        'Capacidade',
        validators=[DataRequired(), NumberRange(min=2)],
    )
    edificio_id = SelectField(
        'Edifício',
        coerce=opcional_inteiro,
        choices=[('', 'Escolha...')],
        validators=[DataRequired()],
    )
    andar = SelectField(
        'Andar',
        coerce=opcional_inteiro,
        choices=[('', 'Escolha...')],
        validators=[DataRequired()],
    )
    recursos = SelectMultipleField(
        'Recursos',
        choices=[
            ('Quadro branco', 'Quadro branco'),
            ('TV', 'TV'),
            ('Projetor', 'Projetor'),
            ('Computador', 'Computadores'),
        ],
        option_widget=CheckboxInput(),
        widget=ListWidget(prefix_label=False),
    )
    submit = SubmitField('Cadastrar sala')
    
    def validate_nome(self, nome):
        if Sala.query.filter_by(nome=nome.data).first():
            raise ValidationError('Nome da sala já cadastrado. Por favor, escolha outro nome.')


class ReservaForm(FlaskForm):
    sala_id = HiddenField(validators=[DataRequired()])
    inicio = HiddenField(validators=[DataRequired()])
    duracao = HiddenField(validators=[DataRequired()])
    grupo = HiddenField(validators=[DataRequired()])
    recursos = HiddenField()
    submit_reservar = SubmitField('Reservar')


class CancelarReservaForm(FlaskForm):
    reserva_id = SelectField('Reserva', coerce=opcional_inteiro, validators=[DataRequired()])
    motivo = TextAreaField('Motivo do cancelamento',
                           validators=[DataRequired(message='O motivo é obrigatório.'),
                                       Length(max=200)])
    submit_cancelar = SubmitField('Confirmar cancelamento')


class AtendimentoForm(FlaskForm):
    reserva_id = HiddenField(validators=[DataRequired()])
    acao = HiddenField(validators=[DataRequired()])


class BloqueioForm(FlaskForm):
    sala_id = SelectField('Sala', coerce=opcional_inteiro, validators=[DataRequired()])
    inicio = DateTimeLocalField('Início', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    fim = DateTimeLocalField('Fim', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    motivo = StringField('Motivo', validators=[DataRequired(), Length(max=200)])
    submit_bloqueio = SubmitField('Criar bloqueio')


class RetirarBloqueioForm(FlaskForm):
    bloqueio_id = HiddenField(validators=[DataRequired()])
    submit_retirar = SubmitField('Retirar bloqueio')