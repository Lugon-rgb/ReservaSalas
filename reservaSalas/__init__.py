from flask import Flask, render_template, url_for, flash, redirect
from reservaSalas.acesso.forms import RegistrationForm, LoginForm
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

app = Flask(__name__)

app.config['SECRET_KEY'] = 'fbc50d9869d71b7076f8e7a369882e3d'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)
