from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from forms import StatsForm, PlayerForm, TeamsForm, LoginForm
from werkzeug.security import check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from functools import wraps
from dotenv import load_dotenv
import itertools
import statistics
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
Bootstrap(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATA_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))


class Season(db.Model):
    __tablename__ = 'seasons'
    season_id = db.Column(db.Integer, primary_key=True)
    games_played = db.Column(db.Integer, nullable=False)
    player_count = db.Column(db.Integer, nullable=False)

    # Establishing the relationship between Season and Game (one-to-many)
    games = relationship('Game', back_populates='season')

    # Establishing the relationship between Season and PlayerGameStats (one-to-many)
    player_stats = relationship('PlayerGameStats', back_populates='season')

    # Establishing the relationship between Season and Player (one-to-many)
    season_player = relationship('SeasonPlayer', back_populates='season')


class Game(db.Model):
    __tablename__ = 'games'
    game_id = db.Column(db.Integer, primary_key=True)
    map_name = db.Column(db.String(50), nullable=False)
    rounds = db.Column(db.Integer, nullable=False)

    season_id = db.Column(db.Integer, db.ForeignKey('seasons.season_id'), nullable=False)  # Foreign key to Season
    season = relationship('Season', back_populates='games')

    # Establishing the relationship between Game and PlayerGameStats (one-to-many)
    player_stats = relationship('PlayerGameStats', back_populates='game')


class SeasonPlayer(db.Model):
    __tablename__ = 'season_players'
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(50), nullable=False)

    played = db.Column(db.Integer, nullable=False)
    total_wins = db.Column(db.Integer, nullable=False)

    total_kills = db.Column(db.Integer, nullable=False)
    total_rounds = db.Column(db.Integer, nullable=False)
    AK = db.Column(db.Float, nullable=False)
    KPR = db.Column(db.Float, nullable=False)
    A_ADR = db.Column(db.Integer, nullable=False)

    winrate = db.Column(db.Integer, nullable=False)
    inconsistency = db.Column(db.Float, nullable=False)
    team_balance = db.Column(db.Integer, nullable=False)

    JLTV = db.Column(db.Float, nullable=False)
    individual = db.Column(db.Float, nullable=False)
    MLTV = db.Column(db.Float, nullable=False)

    season_id = db.Column(db.Integer, db.ForeignKey('seasons.season_id'), nullable=False)
    season = relationship('Season', back_populates='season_player')


class Player(db.Model):
    __tablename__ = 'players'
    player_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    played = db.Column(db.Integer, nullable=False)
    total_wins = db.Column(db.Integer, nullable=False)

    total_kills = db.Column(db.Integer, nullable=False)
    total_rounds = db.Column(db.Integer, nullable=False)
    AK = db.Column(db.Float, nullable=False)
    KPR = db.Column(db.Float, nullable=False)
    A_ADR = db.Column(db.Integer, nullable=False)

    winrate = db.Column(db.Integer, nullable=False)
    inconsistency = db.Column(db.Float, nullable=False)
    team_balance = db.Column(db.Integer, nullable=False)

    JLTV = db.Column(db.Float, nullable=False)
    individual = db.Column(db.Float, nullable=False)
    MLTV = db.Column(db.Float, nullable=False)

    # Establishing the relationship between Player and PlayerGameStats (one-to-many)
    player_stats = relationship('PlayerGameStats', back_populates='player')


class PlayerGameStats(db.Model):
    __tablename__ = 'player_stats'
    id = db.Column(db.Integer, primary_key=True)
    kills = db.Column(db.Integer, nullable=False)
    KPR = db.Column(db.Float, nullable=False)
    ADR = db.Column(db.Integer, nullable=False)
    win = db.Column(db.Boolean, nullable=False)
    JLTV = db.Column(db.Float)
    MLTV = db.Column(db.Float)

    player_id = db.Column(db.Integer, db.ForeignKey('players.player_id'), nullable=False)
    player = relationship('Player', back_populates='player_stats')

    game_id = db.Column(db.Integer, db.ForeignKey('games.game_id'), nullable=False)
    game = relationship('Game', back_populates='player_stats')

    season_id = db.Column(db.Integer, db.ForeignKey('seasons.season_id'), nullable=False)
    season = relationship('Season', back_populates='player_stats')


with app.app_context():
    db.create_all()


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if current_user.id != 1:
            return abort(403)

        return f(*args, **kwargs)

    return decorated_function


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if not user:
            flash("That user does not exist, please try again.")

            return redirect(url_for("login"))

        elif not check_password_hash(user.password, password):
            flash("Password incorrect, please try again.")

            form = LoginForm(username=username)

            return render_template('login.html', form=form)

        else:
            login_user(user)

            return redirect(url_for('home'))

    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()

    return redirect(url_for('home'))


@app.route('/adjust-jltv')
@login_required
def adjust_jltv():
    season_id = Season.query.order_by(Season.season_id.desc()).first().season_id

    first_game_of_szn = PlayerGameStats.query.filter_by(
        season_id=season_id).order_by(
        PlayerGameStats.game_id).first().game_id

    latest_game = PlayerGameStats.query.order_by(PlayerGameStats.game_id.desc()).first().game_id

    for x in range(first_game_of_szn, latest_game + 1):
        player_games = PlayerGameStats.query.filter_by(game_id=x).all()
        current_season = Season.query.order_by(Season.season_id.desc()).first()
        season_id = current_season.season_id

        team_1 = 0
        team_2 = 0

        for player_game in player_games:
            if player_game.win == 1:
                team_1 += SeasonPlayer.query.filter_by(
                    season_id=season_id).filter_by(
                    player_id=player_game.player_id).first().individual

            else:
                team_2 += SeasonPlayer.query.filter_by(
                    season_id=season_id).filter_by(
                    player_id=player_game.player_id).first().individual

        team_1_avg = round(team_1 / 5, 1)
        team_2_avg = round(team_2 / 5, 1)

        for player_game in player_games:
            game = Game.query.filter_by(game_id=player_game.game_id).first()
            rounds = game.rounds

            player = SeasonPlayer.query.filter_by(
                season_id=season_id).filter_by(
                player_id=player_game.player_id).first()

            kpr = player_game.KPR
            adr = player_game.ADR

            if player_game.win == 1:
                jltv = round((((((kpr * 27) ** 0.8) *
                                ((player.winrate + 7) ** 0.1877) *
                                ((adr / 20) ** 0.1)) ** 0.8) * 1.39) * (team_2_avg / team_1_avg), 1)

            else:
                jltv = round((((((kpr * 27) ** 0.8) *
                                ((player.winrate + 7) ** 0.1877) *
                                ((adr / 20) ** 0.1)) ** 0.8) * 1.39) * (team_1_avg / team_2_avg), 1)

            player_game.JLTV = jltv

            all_player_games = PlayerGameStats.query.filter_by(
                season_id=season_id).filter_by(
                player_id=player_game.player_id).all()

            sum_jltv = 0
            sum_mltv = 0
            jltv_list = []

            # Sum stats for all player's games
            for a_player_game in all_player_games:
                sum_jltv += a_player_game.JLTV
                sum_mltv += a_player_game.MLTV
                jltv_list.append(a_player_game.JLTV)

            if player.played >= 2:
                player.inconsistency = round(statistics.stdev(jltv_list), 1)

            player.MLTV = round(sum_jltv / len(all_player_games), 1)

            player.team_balance = round((((((((player.KPR * 27) ** 0.8) * ((player.winrate + 7) ** 0.1877) *
                                             ((player.A_ADR / 20) ** 0.1)) ** 0.8) * 1.379)
                                          - player.MLTV) / player.MLTV) * 100, 0)

            player.JLTV = round(9.4 + (player.MLTV / 2) + sum_mltv, 2)

    # Calculate overall player stats for all seasons when season has been completed
    if current_season.games_played == 30:
        season_players = SeasonPlayer.query.filter_by(season_id=x).all()

        for season_player in season_players:
            if season_player.played > 0:
                overall_player = Player.query.filter_by(player_id=season_player.player_id).first()

                overall_player.played += season_player.played
                overall_player.total_wins += season_player.total_wins
                overall_player.total_kills += season_player.total_kills
                overall_player.total_rounds += season_player.total_rounds

                all_players_season = SeasonPlayer.query.filter_by(player_id=season_player.player_id).all()

                overall_adr = 0
                overall_mltv = 0
                for players_season in all_players_season:
                    overall_adr += players_season.A_ADR
                    overall_mltv += players_season.MLTV

                played_seasons = len(SeasonPlayer.query.filter_by(player_id=season_player.player_id).all())

                overall_player.AK = round(overall_player.total_kills / overall_player.played, 2)
                overall_player.KPR = round(overall_player.total_kills / overall_player.total_rounds, 3)
                overall_player.A_ADR = round(overall_adr / played_seasons, 0)
                overall_player.winrate = round((overall_player.total_wins / overall_player.played) * 100, 0)

                overall_player.individual = round(((((overall_player.KPR * 27) ** 0.8) * ((50 + 7) ** 0.1877) *
                                                    (overall_player.A_ADR / 20) ** 0.1) ** 0.8) * 1.379, 1)

                overall_player.MLTV = round(overall_mltv / played_seasons, 1)

                overall_player.team_balance = round((((((((overall_player.KPR * 27) ** 0.8) *
                                                         ((overall_player.winrate + 7) ** 0.1877) *
                                                         ((overall_player.A_ADR / 20) ** 0.1)) ** 0.8) * 1.379)
                                                      - overall_player.MLTV) / overall_player.MLTV) * 100, 0)

                player_stats = PlayerGameStats.query.filter_by(player_id=season_player.player_id).all()

                sum_mltv = 0
                jltv_list = []
                for player_stat in player_stats:
                    sum_mltv += player_stat.MLTV
                    jltv_list.append(player_stat.JLTV)

                if len(player_stats) >= 2:
                    overall_player.inconsistency = round(statistics.stdev(jltv_list), 1)

                overall_player.JLTV = round(9.4 + (overall_player.MLTV / 2) + sum_mltv, 2)

    db.session.commit()

    return redirect(url_for('home'))


@app.route('/')
def home():
    current_season = Season.query.order_by(Season.season_id.desc()).first()

    if current_season is None:
        new_season = Season(
            games_played=0,
            player_count=0
        )

        db.session.add(new_season)
        db.session.commit()

        current_season = Season.query.order_by(Season.season_id.desc()).first()

    players = SeasonPlayer.query.filter_by(season_id=current_season.season_id).order_by(SeasonPlayer.JLTV.desc()).all()

    all_players = []

    s_tier_players = []
    a_tier_players = []
    b_tier_players = []
    c_tier_players = []
    unranked = []

    for player in players:
        if player.played > 0:
            if player.played < 7:
                unranked.append(player)

            else:
                all_players.append(player)

    for player in all_players:
        if player.JLTV >= 25.0:
            s_tier_players.append(player)

        elif player.JLTV >= 20.0:
            a_tier_players.append(player)

        elif player.JLTV >= 15.0:
            b_tier_players.append(player)

        else:
            c_tier_players.append(player)

    return render_template('index.html', current_season=current_season, s_tier=s_tier_players, a_tier=a_tier_players,
                           b_tier=b_tier_players, c_tier=c_tier_players, unranked=unranked)


@app.route('/lifetime-rankings')
def lifetime_rankings():
    players = Player.query.order_by(Player.JLTV.desc()).all()
    no_of_games = len(Game.query.all())

    all_players = []

    s_tier_players = []
    a_tier_players = []
    b_tier_players = []
    c_tier_players = []
    unranked = []

    for player in players:
        if player.played > 0:
            if player.played < 7:
                unranked.append(player)

            else:
                all_players.append(player)

    for player in all_players:
        if player.JLTV >= 25.0:
            s_tier_players.append(player)

        elif player.JLTV >= 20.0:
            a_tier_players.append(player)

        elif player.JLTV >= 15.0:
            b_tier_players.append(player)

        else:
            c_tier_players.append(player)

    return render_template('lifetime-ranks.html', games=no_of_games, s_tier=s_tier_players, a_tier=a_tier_players,
                           b_tier=b_tier_players, c_tier=c_tier_players, unranked=unranked)


@app.route('/games')
def games():
    all_seasons = Season.query.order_by(Season.season_id.desc()).all()

    all_info = {}
    for season in all_seasons:
        # Create a list assigned to each season
        all_info[season.season_id] = []

        # Access season's games
        season_games = Game.query.filter_by(season_id=season.season_id).order_by(Game.game_id.desc()).all()

        # Loop through all games
        for game in season_games:
            # Get all 10 Player Stats from current game
            game_player_stats = game.player_stats

            sum_jltv = 0
            winners = []
            # Sum all JLTV from 10 player stats of current game
            for game_player_stat in game_player_stats:
                sum_jltv += game_player_stat.JLTV

                if game_player_stat.win == 1:
                    winners.append(game_player_stat.player.name)

            # Calculate average jltv of current game
            average_jltv = round(sum_jltv / 10, 1)

            # Append game info to respective season
            all_info[season.season_id].append([game.game_id, game.map_name, game.rounds, average_jltv, winners])

    last_game_id = Game.query.order_by(Game.game_id.desc()).first().game_id

    return render_template('games.html', all_games=all_info, latest_game=last_game_id)


@app.route('/performance')
def performance():

    return render_template('performance.html')


@app.route('/delete-game/<int:game_id>')
@login_required
@admin_only
def delete_game(game_id):
    # Get player IDs from game to be deleted
    players_game = PlayerGameStats.query.filter_by(game_id=game_id).all()

    # Remove stats from these games from Player and SeasonPlayer table
    for player_stat in players_game:
        overall_player = Player.query.filter_by(player_id=player_stat.player_id).first()

        season_player = SeasonPlayer.query.filter_by(
            season_id=player_stat.season_id).filter_by(
            player_id=player_stat.player_id
        ).first()

        overall_player.played -= 1
        season_player.played -= 1

        if player_stat.win == 1:
            overall_player.total_wins -= 1
            season_player.total_wins -= 1

        overall_player.total_kills -= player_stat.kills
        season_player.total_kills -= player_stat.kills

        overall_player.total_rounds -= player_stat.game.rounds
        season_player.total_rounds -= player_stat.game.rounds

    # Remove this games player stats from the PlayerGameStats table
    for player_stat in players_game:
        db.session.delete(player_stat)

    # Remove this game from the Games table
    game = Game.query.filter_by(game_id=game_id).first()
    db.session.delete(game)

    # If this game is at the beginning of a season, delete this seasonplayers entries and season
    current_season = Season.query.order_by(Season.season_id.desc()).first()

    if current_season.games_played == 1:
        all_season_players = SeasonPlayer.query.filter_by(season_id=current_season.season_id).all()

        for season_player in all_season_players:
            db.session.delete(season_player)

        db.session.delete(current_season)

    else:
        current_season.games_played -= 1

        for player_stat in players_game:

            season_player = SeasonPlayer.query.filter_by(
                season_id=player_stat.season_id).filter_by(
                player_id=player_stat.player_id
            ).first()

            if season_player.played > 0:
                season_player.AK = round(season_player.total_kills / season_player.played, 2)
                season_player.KPR = round(season_player.total_kills / season_player.total_rounds, 3)

                season_player.winrate = round((season_player.total_wins / season_player.played) * 100, 0)

                all_player_games = PlayerGameStats.query.filter_by(
                    season_id=player_stat.season_id).filter_by(
                    player_id=player_stat.player_id
                ).all()

                sum_adr = 0

                # Sum stats for all player's games
                for player_game in all_player_games:
                    sum_adr += player_game.ADR

                # Calculate average ADR for all games played in current season
                season_player.A_ADR = round(sum_adr / len(all_player_games), 0)

                season_player.individual = round(((((season_player.KPR * 27) ** 0.8) * ((50 + 7) ** 0.1877) *
                                                   (season_player.A_ADR / 20) ** 0.1) ** 0.8) * 1.379, 1)

            else:
                season_player.total_wins = 0
                season_player.total_kills = 0
                season_player.total_rounds = 0
                season_player.AK = 0
                season_player.KPR = 0
                season_player.A_ADR = 0
                season_player.winrate = 0
                season_player.inconsistency = 0
                season_player.team_balance = 0
                season_player.JLTV = 0
                season_player.individual = 0
                season_player.MLTV = 0

        all_season_players = SeasonPlayer.query.all()

        no_of_players = 0
        for player in all_season_players:
            if player.played > 0:
                no_of_players += 1

        current_season = Season.query.order_by(Season.season_id.desc()).first()
        current_season.player_count = no_of_players

        season_id = current_season.season_id

        # Query game_id from first game of the season
        first_game_of_szn = PlayerGameStats.query.filter_by(
            season_id=season_id).order_by(
            PlayerGameStats.game_id).first().game_id

        # Query game_id from the latest game of the season
        latest_game = PlayerGameStats.query.order_by(PlayerGameStats.game_id.desc()).first().game_id

        # Recalculate every past game's JLTV and overall statistic: Inconsistency, Team Balance, MLTV and JLTV
        for x in range(first_game_of_szn, latest_game + 1):
            # Query 10 player stats for each game of the current season
            player_games = PlayerGameStats.query.filter_by(game_id=x).filter_by(season_id=season_id).all()

            team_1 = 0
            team_2 = 0

            # Recalculate Individual average
            for player_game in player_games:
                if player_game.win == 1:
                    team_1 += SeasonPlayer.query.filter_by(
                        season_id=season_id).filter_by(
                        player_id=player_game.player_id).first().individual

                else:
                    team_2 += SeasonPlayer.query.filter_by(
                        season_id=season_id).filter_by(
                        player_id=player_game.player_id).first().individual

            team_1_avg = round(team_1 / 5, 1)
            team_2_avg = round(team_2 / 5, 1)

            # Recalculate every game's jltv
            for player_game in player_games:
                game = Game.query.filter_by(game_id=player_game.game_id).first()
                rounds = game.rounds

                player = SeasonPlayer.query.filter_by(
                    season_id=season_id).filter_by(
                    player_id=player_game.player_id).first()

                kpr = player_game.KPR
                adr = player_game.ADR

                if player_game.win == 1:
                    jltv = round((((((kpr * 27) ** 0.8) *
                                    ((player.winrate + 7) ** 0.1877) *
                                    ((adr / 20) ** 0.1)) ** 0.8) * 1.39) * (team_2_avg / team_1_avg), 1)

                else:
                    jltv = round((((((kpr * 27) ** 0.8) *
                                    ((player.winrate + 7) ** 0.1877) *
                                    ((adr / 20) ** 0.1)) ** 0.8) * 1.39) * (team_1_avg / team_2_avg), 1)

                player_game.JLTV = jltv

                seasons_games = PlayerGameStats.query.filter_by(
                    season_id=season_id).filter_by(
                    player_id=player_game.player_id).all()

                sum_jltv = 0
                sum_mltv = 0
                jltv_list = []

                # Sum stats for all player's games
                for each_player_game in seasons_games:
                    sum_jltv += each_player_game.JLTV
                    sum_mltv += each_player_game.MLTV
                    jltv_list.append(each_player_game.JLTV)

                # Calculate standard deviation from individual performance of every game in current season
                if player.played >= 2:
                    player.inconsistency = round(statistics.stdev(jltv_list), 1)

                player.MLTV = round(sum_jltv / len(seasons_games), 1)

                player.team_balance = round((((((((player.KPR * 27) ** 0.8) * ((player.winrate + 7) ** 0.1877) *
                                                 ((player.A_ADR / 20) ** 0.1)) ** 0.8) * 1.379)
                                              - player.MLTV) / player.MLTV) * 100, 0)

                player.JLTV = round(9.4 + (player.MLTV / 2) + sum_mltv, 2)

    current_season = Season.query.order_by(Season.season_id.desc()).first()

    if current_season.games_played == 29:
        if current_season.season_id == 1:
            overall_player = Player.query.all()
            for player in overall_player:

                player.played = 0
                player.total_wins = 0
                player.total_kills = 0
                player.total_rounds = 0
                player.AK = 0
                player.KPR = 0
                player.A_ADR = 0
                player.winrate = 0
                player.individual = 0
                player.MLTV = 0
                player.team_balance = 0
                player.inconsistency = 0
                player.JLTV = 0

        else:
            for player_stat in players_game:
                season_player = SeasonPlayer.query.filter_by(
                    season_id=player_stat.season_id).filter_by(
                    player_id=player_stat.player_id
                ).first()

                overall_player = Player.query.filter_by(player_id=player_stat.player_id).first()

                if overall_player.played > 0:
                    overall_player.played -= season_player.played
                    overall_player.total_wins -= season_player.total_wins
                    overall_player.total_kills -= season_player.total_kills
                    overall_player.total_rounds -= season_player.total_rounds

                    all_players_season = SeasonPlayer.query.filter_by(player_id=player_stat.player_id).all()

                    overall_adr = 0
                    overall_mltv = 0
                    for players_season in all_players_season:
                        overall_adr += players_season.A_ADR
                        overall_mltv += players_season.MLTV

                    played_seasons = len(SeasonPlayer.query.filter_by(player_id=player_stat.player_id).all())

                    overall_player.AK = round(overall_player.total_kills / overall_player.played, 2)
                    overall_player.KPR = round(overall_player.total_kills / overall_player.total_rounds, 3)
                    overall_player.A_ADR = round(overall_adr / played_seasons, 0)
                    overall_player.winrate = round((overall_player.total_wins / overall_player.played) * 100, 0)

                    overall_player.individual = round(
                        ((((overall_player.KPR * 27) ** 0.8) * ((50 + 7) ** 0.1877) *
                          (overall_player.A_ADR / 20) ** 0.1) ** 0.8) * 1.379, 1)

                    overall_player.MLTV = round(overall_mltv / played_seasons, 1)

                    overall_player.team_balance = round((((((((overall_player.KPR * 27) ** 0.8) *
                                                             ((overall_player.winrate + 7) ** 0.1877) *
                                                             ((overall_player.A_ADR / 20) ** 0.1)) ** 0.8) * 1.379)
                                                          - overall_player.MLTV) / overall_player.MLTV) * 100, 0)

                    player_stats = PlayerGameStats.query.filter_by(player_id=player_stat.player_id).all()

                    sum_mltv = 0
                    jltv_list = []
                    for players_stat in player_stats:
                        sum_mltv += players_stat.MLTV
                        jltv_list.append(players_stat.JLTV)

                    if len(player_stats) >= 2:
                        overall_player.inconsistency = round(statistics.stdev(jltv_list), 1)

                    overall_player.JLTV = round(9.4 + (overall_player.MLTV / 2) + sum_mltv, 2)

    db.session.commit()

    return redirect(url_for('adjust_jltv'))


@app.route('/add-game', methods=['GET', 'POST'])
@login_required
def add_game():
    form = StatsForm()
    all_players = [(player.player_id, player.name) for player in Player.query.order_by(Player.name).all()]

    form.player1.choices = all_players
    form.player2.choices = all_players
    form.player3.choices = all_players
    form.player4.choices = all_players
    form.player5.choices = all_players
    form.player6.choices = all_players
    form.player7.choices = all_players
    form.player8.choices = all_players
    form.player9.choices = all_players
    form.player10.choices = all_players

    if form.validate_on_submit():
        # Add new Season if 30 games have already been played or there is not a 1st Season
        current_season = Season.query.order_by(Season.season_id.desc()).first()

        if current_season.games_played == 30:
            new_season = Season(
                games_played=0,
                player_count=0
            )

            db.session.add(new_season)
            db.session.commit()

            current_season_id = Season.query.order_by(Season.season_id.desc()).first().season_id
            past_season_id = int(current_season_id) - 1

            season_players = SeasonPlayer.query.filter_by(season_id=past_season_id).all()

            for season_player in season_players:
                new_player = SeasonPlayer(
                    player_id=season_player.player_id,
                    name=season_player.name,
                    played=0,
                    total_wins=0,
                    total_kills=0,
                    total_rounds=0,
                    AK=0,
                    KPR=0,
                    A_ADR=0,
                    winrate=0,
                    inconsistency=0,
                    team_balance=0,
                    JLTV=0,
                    individual=season_player.individual,
                    MLTV=0,
                    season_id=current_season_id,
                )

                db.session.add(new_player)

            db.session.commit()

        # Add new Game to database
        season_id = Season.query.order_by(Season.season_id.desc()).first().season_id

        new_game = Game(
            map_name=request.form.get('map_name'),
            rounds=request.form.get('rounds'),
            season_id=season_id
        )

        db.session.add(new_game)

        # Find amount of games played in current season and update value
        games_played = len(Game.query.filter_by(season_id=season_id).all())
        current_season = Season.query.order_by(Season.season_id.desc()).first()
        current_season.games_played = games_played

        # Get all Player entries
        data = request.form

        all_player_stats = [
            [data.get('player1'), data.get('kills1'), data.get('adr1'), data.get('win1')],
            [data.get('player2'), data.get('kills2'), data.get('adr2'), data.get('win2')],
            [data.get('player3'), data.get('kills3'), data.get('adr3'), data.get('win3')],
            [data.get('player4'), data.get('kills4'), data.get('adr4'), data.get('win4')],
            [data.get('player5'), data.get('kills5'), data.get('adr5'), data.get('win5')],
            [data.get('player6'), data.get('kills6'), data.get('adr6'), data.get('win6')],
            [data.get('player7'), data.get('kills7'), data.get('adr7'), data.get('win7')],
            [data.get('player8'), data.get('kills8'), data.get('adr8'), data.get('win8')],
            [data.get('player9'), data.get('kills9'), data.get('adr9'), data.get('win9')],
            [data.get('player10'), data.get('kills10'), data.get('adr10'), data.get('win10')],
        ]

        # Get winning and losing team average individual
        team_1 = 0
        team_2 = 0

        # Sum up teams individual stats
        for stat in all_player_stats:
            if stat[3] == 'y':
                team_1 += SeasonPlayer.query.filter_by(
                    season_id=season_id).filter_by(
                    player_id=int(stat[0])).first().individual

            else:
                team_2 += SeasonPlayer.query.filter_by(
                    season_id=season_id).filter_by(
                    player_id=int(stat[0])).first().individual

        # Teams average individual
        team_1_avg = round(team_1 / 5, 1)
        team_2_avg = round(team_2 / 5, 1)

        # Get amount of rounds from most recent game
        game = Game.query.order_by(Game.game_id.desc()).first()

        rounds = int(game.rounds)
        game_id = game.game_id

        # Calculate KPR, ADR for Individual Stat
        for stat in all_player_stats:
            kpr = round(int(stat[1]) / rounds, 2)
            adr = int(stat[2])

            player = SeasonPlayer.query.filter_by(season_id=season_id).filter_by(player_id=int(stat[0])).first()

            win = 0

            # Calculate specific PlayerGame JLTV & MLTV depending on win
            if stat[3] == 'y':
                mltv = kpr * 0.8 * 0.8 / (100 / 55)

                jltv = round((((((kpr * 27) ** 0.8) *
                                ((player.winrate + 7) ** 0.1877) *
                                ((adr / 20) ** 0.1)) ** 0.8) * 1.39) * (team_2_avg / team_1_avg), 1)

                win = 1
                player.total_wins += 1

            else:
                mltv = -(29 * 0.8 * 0.8 / 140) / kpr

                jltv = round((((((kpr * 27) ** 0.8) *
                                ((player.winrate + 7) ** 0.1877) *
                                ((adr / 20) ** 0.1)) ** 0.8) * 1.39) * (team_1_avg / team_2_avg), 1)

            # Input calculated stats into PlayerGameStats table
            new_player_stat = PlayerGameStats(
                kills=int(stat[1]),
                KPR=kpr,
                ADR=adr,
                win=win,
                JLTV=jltv,
                MLTV=mltv,
                player_id=int(stat[0]),
                game_id=game_id,
                season_id=season_id
            )

            db.session.add(new_player_stat)

            # Update overall Player stats
            player.played += 1
            player.total_rounds += rounds
            player.total_kills += int(stat[1])

            player.KPR = round(player.total_kills / player.total_rounds, 3)

            # Get all player's games for current season
            player_games = PlayerGameStats.query.filter_by(season_id=season_id).filter_by(player_id=int(stat[0])).all()

            sum_adr = 0

            # Sum stats for all player's games
            for player_game in player_games:
                sum_adr += player_game.ADR

            # Calculate average ADR for all games played in current season
            player.A_ADR = round(sum_adr / len(player_games), 0)
            player.winrate = round((player.total_wins / player.played) * 100, 0)
            player.AK = round(player.total_kills / player.played, 2)

            # Calculate JLTV, MLTV, Individual
            player.individual = round(((((player.KPR * 27) ** 0.8) * ((50 + 7) ** 0.1877) *
                                        (player.A_ADR / 20) ** 0.1) ** 0.8) * 1.379, 1)

        all_players = SeasonPlayer.query.filter_by(season_id=season_id).all()
        no_of_players = 0

        for player in all_players:
            if player.played > 0:
                no_of_players += 1

        current_season.player_count = no_of_players

        current_season = Season.query.order_by(Season.season_id.desc()).first()
        season_id = current_season.season_id

        # Query game_id from first game of the season
        first_game_of_szn = PlayerGameStats.query.filter_by(
            season_id=season_id).order_by(
            PlayerGameStats.game_id).first().game_id

        # Query game_id from the latest game of the season
        latest_game = PlayerGameStats.query.order_by(PlayerGameStats.game_id.desc()).first().game_id

        # Recalculate every past game's JLTV and overall statistic: Inconsistency, Team Balance, MLTV and JLTV
        for x in range(first_game_of_szn, latest_game + 1):
            # Query 10 player stats for each game of the current season
            player_games = PlayerGameStats.query.filter_by(game_id=x).filter_by(season_id=season_id).all()

            team_1 = 0
            team_2 = 0

            # Recalculate Individual average
            for player_game in player_games:
                if player_game.win == 1:
                    team_1 += SeasonPlayer.query.filter_by(
                        season_id=season_id).filter_by(
                        player_id=player_game.player_id).first().individual

                else:
                    team_2 += SeasonPlayer.query.filter_by(
                        season_id=season_id).filter_by(
                        player_id=player_game.player_id).first().individual

            team_1_avg = round(team_1 / 5, 1)
            team_2_avg = round(team_2 / 5, 1)

            # Recalculate every game's jltv
            for player_game in player_games:
                game = Game.query.filter_by(game_id=player_game.game_id).first()
                rounds = game.rounds

                player = SeasonPlayer.query.filter_by(
                    season_id=season_id).filter_by(
                    player_id=player_game.player_id).first()

                kpr = player_game.KPR
                adr = player_game.ADR

                if player_game.win == 1:
                    jltv = round((((((kpr * 27) ** 0.8) *
                                    ((player.winrate + 7) ** 0.1877) *
                                    ((adr / 20) ** 0.1)) ** 0.8) * 1.39) * (team_2_avg / team_1_avg), 1)

                else:
                    jltv = round((((((kpr * 27) ** 0.8) *
                                    ((player.winrate + 7) ** 0.1877) *
                                    ((adr / 20) ** 0.1)) ** 0.8) * 1.39) * (team_1_avg / team_2_avg), 1)

                player_game.JLTV = jltv

                seasons_games = PlayerGameStats.query.filter_by(
                    season_id=season_id).filter_by(
                    player_id=player_game.player_id).all()

                sum_jltv = 0
                sum_mltv = 0
                jltv_list = []

                # Sum stats for all player's games
                for players_game in seasons_games:
                    sum_jltv += players_game.JLTV
                    sum_mltv += players_game.MLTV
                    jltv_list.append(players_game.JLTV)

                # Calculate standard deviation from individual performance of every game in current season
                if player.played >= 2:
                    player.inconsistency = round(statistics.stdev(jltv_list), 1)

                player.MLTV = round(sum_jltv / len(seasons_games), 1)

                player.team_balance = round((((((((player.KPR * 27) ** 0.8) * ((player.winrate + 7) ** 0.1877) *
                                                 ((player.A_ADR / 20) ** 0.1)) ** 0.8) * 1.379)
                                              - player.MLTV) / player.MLTV) * 100, 0)

                player.JLTV = round(9.4 + (player.MLTV / 2) + sum_mltv, 2)

        # Calculate overall player stats for all seasons when season has been completed
        if current_season.games_played == 30:
            season_players = SeasonPlayer.query.filter_by(season_id=current_season.season_id).all()

            for season_player in season_players:
                if season_player.played > 0:
                    overall_player = Player.query.filter_by(player_id=season_player.player_id).first()

                    overall_player.played += season_player.played
                    overall_player.total_wins += season_player.total_wins
                    overall_player.total_kills += season_player.total_kills
                    overall_player.total_rounds += season_player.total_rounds

                    all_players_season = SeasonPlayer.query.filter_by(player_id=season_player.player_id).all()

                    overall_adr = 0
                    overall_mltv = 0
                    for players_season in all_players_season:
                        overall_adr += players_season.A_ADR
                        overall_mltv += players_season.MLTV

                    played_seasons = len(SeasonPlayer.query.filter_by(player_id=season_player.player_id).all())

                    overall_player.AK = round(overall_player.total_kills / overall_player.played, 2)
                    overall_player.KPR = round(overall_player.total_kills / overall_player.total_rounds, 3)
                    overall_player.A_ADR = round(overall_adr / played_seasons, 0)
                    overall_player.winrate = round((overall_player.total_wins / overall_player.played) * 100, 0)

                    overall_player.individual = round(
                        ((((overall_player.KPR * 27) ** 0.8) * ((50 + 7) ** 0.1877) *
                          (overall_player.A_ADR / 20) ** 0.1) ** 0.8) * 1.379, 1)

                    overall_player.MLTV = round(overall_mltv / played_seasons, 1)

                    overall_player.team_balance = round((((((((overall_player.KPR * 27) ** 0.8) *
                                                             ((overall_player.winrate + 7) ** 0.1877) *
                                                             ((overall_player.A_ADR / 20) ** 0.1)) ** 0.8) * 1.379)
                                                          - overall_player.MLTV) / overall_player.MLTV) * 100, 0)

                    player_stats = PlayerGameStats.query.filter_by(player_id=season_player.player_id).all()

                    sum_mltv = 0
                    jltv_list = []
                    for player_stat in player_stats:
                        sum_mltv += player_stat.MLTV
                        jltv_list.append(player_stat.JLTV)

                    if len(player_stats) >= 2:
                        overall_player.inconsistency = round(statistics.stdev(jltv_list), 1)

                    overall_player.JLTV = round(9.4 + (overall_player.MLTV / 2) + sum_mltv, 2)

        db.session.commit()

        return redirect(url_for('home'))

    return render_template('add_game.html', form=form)


@app.route('/add-player', methods=['GET', 'POST'])
@login_required
def add_player():
    form = PlayerForm()

    if form.validate_on_submit():
        player_name = request.form.get('player_name')
        individual = float(request.form.get('individual'))

        if individual == 0:
            individual = 1.0

        season_id = Season.query.order_by(Season.season_id.desc()).first().season_id

        new_player = Player(
            name=player_name,
            played=0,
            total_wins=0,
            total_kills=0,
            total_rounds=0,
            AK=0,
            KPR=0,
            A_ADR=0,
            winrate=0,
            inconsistency=0,
            team_balance=0,
            JLTV=0,
            individual=individual,
            MLTV=0
        )

        db.session.add(new_player)
        db.session.commit()

        new_player_id = Player.query.order_by(Player.player_id.desc()).first().player_id

        new_season_player = SeasonPlayer(
            player_id=new_player_id,
            name=player_name,
            played=0,
            total_wins=0,
            total_kills=0,
            total_rounds=0,
            AK=0,
            KPR=0,
            A_ADR=0,
            winrate=0,
            inconsistency=0,
            team_balance=0,
            JLTV=0,
            individual=individual,
            MLTV=0,
            season_id=season_id
        )

        db.session.add(new_season_player)
        db.session.commit()

        return redirect(url_for('add_game'))

    return render_template('add_player.html', form=form)


@app.route('/create-teams', methods=['GET', 'POST'])
def create_teams():
    form = TeamsForm()

    all_players = [(player.player_id, player.name) for player in Player.query.order_by(Player.name).all()]
    form.player1.choices = all_players
    form.player2.choices = all_players
    form.player3.choices = all_players
    form.player4.choices = all_players
    form.player5.choices = all_players
    form.player6.choices = all_players
    form.player7.choices = all_players
    form.player8.choices = all_players
    form.player9.choices = all_players
    form.player10.choices = all_players

    if form.validate_on_submit():
        # Get all Player IDs from Select Fields
        data = request.form

        player_ids = [data.get('player1'), data.get('player2'), data.get('player3'), data.get('player4'),
                      data.get('player5'), data.get('player6'), data.get('player7'), data.get('player8'),
                      data.get('player9'), data.get('player10')]

        selected_players = []
        # Query Player name and append to list
        for player_id in player_ids:
            player_name = Player.query.filter_by(player_id=int(player_id)).first().name

            selected_players.append(player_name)

        # Create team combinations using itertools
        team_combinations = list(itertools.combinations(selected_players, 5))

        # Calculates difference between team's elo
        def calculate_difference(team_1, team_2):
            average_rating_team1 = sum(Player.query.filter_by(name=name).first().JLTV for name in team_1) / 5
            average_rating_team2 = sum(Player.query.filter_by(name=name).first().JLTV for name in team_2) / 5

            return abs(average_rating_team1 - average_rating_team2)

        iterations = []

        # Create 2 sets of teams with difference of elo
        for combination in team_combinations:
            team1 = list(combination)
            team2 = list(set(selected_players) - set(combination))
            difference = calculate_difference(team1, team2)
            iterations.append((team1, team2, difference))

        sorted_iterations = sorted(iterations, key=lambda x: x[2])[:3]

        teams = ''
        for i, result in enumerate(sorted_iterations):
            teams += f'Iteration {i + 1}#Team 1: {result[0]}#Team 2: {result[1]}#Difference: {result[2]}#'

        return redirect(url_for('display_teams', teams=teams))

    return render_template('create_teams.html', form=form)


@app.route('/display-teams/<teams>')
def display_teams(teams):
    teams = list(teams.split('#'))

    iteration1 = [teams[0], teams[1], teams[2], teams[3]]
    iteration2 = [teams[4], teams[5], teams[6], teams[7]]
    iteration3 = [teams[8], teams[9], teams[10], teams[11]]

    return render_template('display_teams.html', iteration_1=iteration1, iteration_2=iteration2, iteration_3=iteration3)


if __name__ == '__main__':
    app.run(host='0.0.0.0')

# TODO: Pull data from forms ✔

# TODO: Do calculations ✔

# TODO: Calculate MLTV, JLTV for each game ✔

# TODO: Recalculate every game's JLTV and overall JLTV, MLTV and Team Balancing ✔

# TODO: Input data into database ✔

# TODO: Create 'Add a Player' page ✔

# TODO: Pull data from Players table ✔

# TODO: Display players data on Home page in order ✔

# TODO: Tweak top3 in jinja to make sure first, second and third will display even if one doesn't have 7 games played ✔

# TODO: Style home page ✔

# TODO: Integrate team iterations code, and display on a page ✔

# TODO: Test 'Add Game' route with Season 15 games manually, and remove unecessary commits ✔

# TODO: Add Inconsistency formula ✔

# TODO: Find a way to permanantly store each players end of season stats ✔

# TODO: Calculate overall stats and add to Players table at the end of season in '/add-game' and '/adjust-jltv' ✔

# TODO: Test new features by adding a new player and adding new game in a new season: ✔

# Adding a new player should be recorded with same player_id in both Player and SeasonPlayer ✔
# Overall Player stats should be created ✔
# Duplicate of SeasonPlayer stats should be created with new season id ✔

# TODO: Create 'Delete Game' page and recalculate stats ✔

# Create a Games page to view rows of all game's map name, rounds, average jltv of the game, and winners ✔
# Delete game button to delete game from table and recalculate stats accordingly ✔

# TODO: Ideas for customised Performance page

# Who you win/lose with the most
# Best/Worst map for each player
# Which player has the most Kills/Deaths/ADR/Games Played/Wins

# TODO: Add 'Login' page ✔

# TODO: Require Login for 'Add Game', 'Add Player', 'Delete Game' ✔
