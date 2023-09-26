from flask_wtf import FlaskForm
from wtforms import BooleanField, SubmitField, SelectField, IntegerField, StringField, FloatField, PasswordField
from wtforms.validators import DataRequired

MAP_NAME = [('Dust II', 'Dust II'), ('Mirage', 'Mirage'), ('Inferno', 'Inferno'), ('Train', 'Train'),
            ('Overpass', 'Overpass'), ('Cache', 'Cache'), ('Ancient', 'Ancient'), ('Nuke', 'Nuke'),
            ('Anubis', 'Anubis'), ('Vertigo', 'Vertigo')]


# WTForm
class StatsForm(FlaskForm):
    map_name = SelectField(u'Map', choices=MAP_NAME)
    rounds = IntegerField('Rounds', validators=[DataRequired()])

    player1 = SelectField(u'Player 1', coerce=int)
    kills1 = IntegerField('Kills', validators=[DataRequired()])
    adr1 = IntegerField('ADR', validators=[DataRequired()])
    win1 = BooleanField('Win', default=True)

    player2 = SelectField(u'Player 2', coerce=int)
    kills2 = IntegerField('Kills', validators=[DataRequired()])
    adr2 = IntegerField('ADR', validators=[DataRequired()])
    win2 = BooleanField('Win', default=True)

    player3 = SelectField(u'Player 3', coerce=int)
    kills3 = IntegerField('Kills', validators=[DataRequired()])
    adr3 = IntegerField('ADR', validators=[DataRequired()])
    win3 = BooleanField('Win', default=True)

    player4 = SelectField(u'Player 4', coerce=int)
    kills4 = IntegerField('Kills', validators=[DataRequired()])
    adr4 = IntegerField('ADR', validators=[DataRequired()])
    win4 = BooleanField('Win', default=True)

    player5 = SelectField(u'Player 5', coerce=int)
    kills5 = IntegerField('Kills', validators=[DataRequired()])
    adr5 = IntegerField('ADR', validators=[DataRequired()])
    win5 = BooleanField('Win', default=True)

    player6 = SelectField(u'Player 6', coerce=int)
    kills6 = IntegerField('Kills', validators=[DataRequired()])
    adr6 = IntegerField('ADR', validators=[DataRequired()])
    win6 = BooleanField('Win')

    player7 = SelectField(u'Player 7', coerce=int)
    kills7 = IntegerField('Kills', validators=[DataRequired()])
    adr7 = IntegerField('ADR', validators=[DataRequired()])
    win7 = BooleanField('Win')

    player8 = SelectField(u'Player 8', coerce=int)
    kills8 = IntegerField('Kills', validators=[DataRequired()])
    adr8 = IntegerField('ADR', validators=[DataRequired()])
    win8 = BooleanField('Win')

    player9 = SelectField(u'Player 9', coerce=int)
    kills9 = IntegerField('Kills', validators=[DataRequired()])
    adr9 = IntegerField('ADR', validators=[DataRequired()])
    win9 = BooleanField('Win')

    player10 = SelectField(u'Player 10', coerce=int)
    kills10 = IntegerField('Kills', validators=[DataRequired()])
    adr10 = IntegerField('ADR', validators=[DataRequired()])
    win10 = BooleanField('Win')

    submit = SubmitField("Submit")


class PlayerForm(FlaskForm):
    player_name = StringField('Player Name', validators=[DataRequired()])
    individual = FloatField('Individual', validators=[DataRequired()])

    submit = SubmitField("Submit")


class TeamsForm(FlaskForm):
    player1 = SelectField(u'Player 1', coerce=int)
    player2 = SelectField(u'Player 2', coerce=int)
    player3 = SelectField(u'Player 3', coerce=int)
    player4 = SelectField(u'Player 4', coerce=int)
    player5 = SelectField(u'Player 5', coerce=int)
    player6 = SelectField(u'Player 6', coerce=int)
    player7 = SelectField(u'Player 7', coerce=int)
    player8 = SelectField(u'Player 8', coerce=int)
    player9 = SelectField(u'Player 9', coerce=int)
    player10 = SelectField(u'Player 10', coerce=int)

    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

    submit = SubmitField("Let Me In!")
