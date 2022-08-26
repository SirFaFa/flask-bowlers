from flask import Flask, render_template, url_for, redirect, request, abort, flash
from flask_socketio import SocketIO, emit
from proto import Partida
from flask_sqlalchemy import SQLAlchemy
import csv
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
from flask_ckeditor import CKEditor
from functools import wraps
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import LoginForm, RegisterForm, CreatePartidaForm

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

ckeditor = CKEditor(app)
Bootstrap(app)

##CREATE DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///books.db"
#Optional: But it will silence the deprecation warning in the console.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

socketio = SocketIO(app)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))

db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(current_user)
        if not current_user:
            return redirect('register')
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


partida1=Partida(jugadores=["CristoReyxxxxxxxxxxxxxxxxxxxx😡😡", "Mati", "Anónimo"], id=0)
partida2=Partida(jugadores=["Alguien😡😡"], id=1)
partida3=Partida(jugadores=["CristoRey", "M","Anónimo"], id=2)
partida4=Partida(jugadores=["CristoRey", "M","Anónimo"], id=3)

arrayPista=[partida1, partida2, partida3, partida4]


#Vistas Principales
@app.route('/')
def home():
    return render_template("index.html", data=partida1)

@app.route('/pista/<int:pista>')
@login_required
def pistas(pista):
    return render_template("index.html", data=arrayPista[pista])


@app.route('/<int:pista>/<int:valor>', methods = ['GET', 'POST'])
def actualizaPartida(pista, valor):
    partida=arrayPista[pista]
    if valor == 10:
        partida.actualizaMarcador('/')
    elif valor == 11:
        partida.actualizaMarcador('X')
        partida.actualizaMarcador(' ')
    else:
        partida.actualizaMarcador(valor)
    partida.calculaSuma()

    if valor==0:
        return redirect(url_for("risas", id=pista, lista_de_birlas=[0,1,1,0]))

    return redirect(url_for("pistas", pista=pista))

@app.route('/transicion/<int:id>/<lista_de_birlas>')
@login_required
def risas(id, lista_de_birlas):
    redirect_url = url_for("pistas", pista=id)
    return render_template("jajas.html", redirect_url=redirect_url, data=lista_de_birlas)


#Asignar valores / Conexión con ESP32
@app.route('/esp32/<int:pista>', methods=["POST"])
def asignaValor(pista):
    partida = arrayPista[pista]
    dataPartida = request.get_json()
    data = dataPartida
    if int(data['tirada']) == partida.tirada:
        if dataPartida["api_key"]=='8BYkEfBA6O6donzWlSihBXox7C0sKR6b':
            sum = 0
            lista_birla=[]
            for subdata in data:
                if 'birla' in subdata:
                    sum += int(data[subdata])
                    lista_birla.append(int(data[subdata]))
            if sum == 10:
                if data['tirada'] == '0':
                    partida.actualizaMarcador('X')
                    partida.actualizaMarcador(' ')
                else:
                    partida.actualizaMarcador('/')
                    partida.cambiaTirada()
            else:
                partida.actualizaMarcador(sum)
                partida.cambiaTirada()
            partida.calculaSuma()
            socketio.emit('nueva-tirada', (lista_birla, pista))
        return "Todo OK"
    return "No es la tirada"

@socketio.on('partida-finalizada')
def handle_json(data):
    partida = arrayPista[data['pista']]
    partida.guardaCSV(data)
    arrayPista[data['pista']] = ''



@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        if User.query.filter_by(name=form.name.data).first():
            print(User.query.filter_by(name=form.name.data).first())
            #User already exists
            flash("You've already signed up with that name, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home"))

    return render_template("register.html", form=form, current_user=current_user)

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        name = form.name.data
        password = form.password.data

        user = User.query.filter_by(name=name).first()

        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))
    return render_template("login.html", form=form, current_user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


#Vistas Administrador
@app.route("/add/<int:id>", methods=["GET", "POST"])
@login_required
@admin_only
def addPartida(id):

    if arrayPista[id]:
        return redirect(url_for('admin'))

    form = CreatePartidaForm()
    if form.validate_on_submit():

        if id >= 0 and id <=3:
            arrayPista[id] = Partida(jugadores=form.jugadores.data.split(', '), modo=form.modo.data, id=id)
        return redirect(url_for('admin'))
    return render_template('crear-partida.html', form=form, current_user=current_user)

@app.route("/pistas")
@admin_only
def pistass():
    with open('cafe-data.csv', newline='') as csv_file:
        csv_data = csv.reader(csv_file, delimiter='')
        lista_de_pistas = []
        for pista in csv_data:
            lista_de_pistas.append(pista)
    return render_template('pistas.html', pistas=lista_de_pistas)

@app.route("/delete/<int:id>")
@login_required
@admin_only
def deletePartida(id):
    arrayPista[id]=''
    return redirect(url_for('admin'))



@app.route('/admin')
@login_required
@admin_only
def admin():
    return render_template("pistas.html")



if __name__ == '__main__':
    app.run(debug=True)