@app.route('/redo-kpr')
def update_kpr():
    playergames = PlayerGameStats.query.all()

    for playergame in playergames:
        rounds = playergame.game.rounds
        kills = playergame.kills

        kpr = round(kills / rounds, 2)

        playergame.KPR = kpr

    db.session.commit()

    return redirect(url_for('home'))


@app.route('/update-season')
def update_season():
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
                mltv = kpr * 0.8 * 0.8 / (100 / 55)

                jltv = round((((((kpr * 27) ** 0.8) *
                                ((player.winrate + 7) ** 0.1877) *
                                ((adr / 20) ** 0.1)) ** 0.8) * 1.39) * (team_2_avg / team_1_avg), 1)

                player.total_wins += 1

            else:
                mltv = -(29 * 0.8 * 0.8 / 140) / kpr

                jltv = round((((((kpr * 27) ** 0.8) *
                                ((player.winrate + 7) ** 0.1877) *
                                ((adr / 20) ** 0.1)) ** 0.8) * 1.39) * (team_1_avg / team_2_avg), 1)

            player_game.JLTV = jltv
            player_game.MLTV = mltv

            player.played += 1
            player.total_rounds += rounds
            player.total_kills += player_game.kills
            player.KPR = round(player.total_kills / player.total_rounds, 3)

            all_player_games = PlayerGameStats.query.filter_by(
                season_id=season_id).filter_by(
                player_id=player_game.player_id).all()

            sum_adr = 0
            sum_jltv = 0
            sum_mltv = 0
            jltv_list = []

            # Sum stats for all player's games
            for a_player_game in all_player_games:
                sum_adr += a_player_game.ADR
                sum_jltv += a_player_game.JLTV
                sum_mltv += a_player_game.MLTV
                jltv_list.append(a_player_game.JLTV)

            player.A_ADR = round(sum_adr / len(all_player_games), 0)
            player.winrate = round((player.total_wins / player.played) * 100, 0)
            player.AK = round(player.total_kills / player.played, 2)

            player.individual = round(((((player.KPR * 27) ** 0.8) * ((50 + 7) ** 0.1877) *
                                        (player.A_ADR / 20) ** 0.1) ** 0.8) * 1.379, 1)

            if len(all_player_games) >= 2:
                player.inconsistency = round(statistics.stdev(jltv_list), 1)

            player.MLTV = round(sum_jltv / len(all_player_games), 1)

            player.team_balance = round((((((((player.KPR * 27) ** 0.8) * ((player.winrate + 7) ** 0.1877) *
                                             ((player.A_ADR / 20) ** 0.1)) ** 0.8) * 1.379)
                                          - player.MLTV) / player.MLTV) * 100, 0)

            player.JLTV = round(9.4 + (player.MLTV / 2) + sum_mltv, 2)

    db.session.commit()

    return redirect(url_for('home'))
