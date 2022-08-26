from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Registra Usuario")

class LoginForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Inicia sesión")

class CreatePartidaForm(FlaskForm):
    jugadores = StringField("Jugadores", validators=[DataRequired()])
    modo = SelectField("Modo",choices=["Normal", "Próximamente"], validators=[DataRequired()])
    submit = SubmitField("Crear Partida")