from flask import render_template, url_for, flash, redirect
from reservaSalas.persistencia.models import User, Sala, Reserva, Bloqueio, Edificio
from reservaSalas.acesso.forms import RegistrationForm, LoginForm
from reservaSalas import app

@app.route("/")
@app.route("/home")
def home():
    return render_template("painel.html")

@app.route("/atendimento")
def atendimento():
    return render_template("atendimento.html")

@app.route("/reservar")
def reservar():
    return render_template("reservar.html")

@app.route("/usuarios")
def usuarios():
    return render_template("usuarios.html")

@app.route("/relatorios")
def relatorios():
    return render_template("relatorios.html")

@app.route("/bloqueios")
def bloqueios():
    return render_template("bloqueios.html")

@app.route("/salas")
def salas():
    return render_template("salas.html")

@app.route("/minhas-reservas")
def minhas_reservas():
    return render_template("minhas-reservas.html")

@app.route("/login")
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.matricula.data == 'admin@blog.com' and form.password.data == 'password':
            flash('You have been logged in!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template("index.html", method=["GET", "POST"])
