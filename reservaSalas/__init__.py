from flask import Flask, render_template, url_for, flash, redirect
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timezone, timedelta
from flask_bcrypt import Bcrypt

app = Flask(__name__)
Bcrypt = Bcrypt(app)

app.config['SECRET_KEY'] = 'fbc50d9869d71b7076f8e7a369882e3d'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
setattr(login_manager, 'login_view', 'login')
setattr(login_manager, 'refresh_view', 'login')


from reservaSalas.persistencia import models
