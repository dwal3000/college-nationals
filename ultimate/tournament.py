
import pandas as pd

from .game import Game

class Tournament:
    def __init__(self, games_list=None, played=False):
        if games_list:
            self.games_list = games_list
        else:
            self.games_list = []
        self.played = played

    def play_games(
        self, method=None, rating_diff_to_victory_margin=None, p_a_offense=None
    ):
        for game in self.games_list:
            if (
                not method
            ):  # When no method provided in play_games, just use what was given in the game itself
                game.play_game(
                    method=game.method,
                    rating_diff_to_victory_margin=game.rating_diff_to_victory_margin,
                    p_a_offense=game.p_a_offense,
                )
            else:
                game.play_game(
                    method=method,
                    rating_diff_to_victory_margin=rating_diff_to_victory_margin,
                    p_a_offense=p_a_offense,
                )
        self.played = True

    def determine_placement(self, method="finals winner"):
        if self.played:
            if method == "finals winner":
                # Look for a team that won finals
                games_with_level_equal_finals = [
                    game for game in self.games_list if game.level == "final"
                ]
                if len(games_with_level_equal_finals) == 1:
                    return [(1, games_with_level_equal_finals[0].winner)]
                else:
                    raise Exception("Multiple teams won 'final' level game!")
            elif method == "round robin":
                # Pandas dataframe of each team
                df_teams = pd.DataFrame(
                    {
                        "Team": self.teams_list,
                        "Name": [team.name for team in self.teams_list],
                    }
                )

                # Data frame of each game
                df_games = pd.DataFrame(
                    [
                        (
                            game.team_a,
                            game.team_b,
                            game.team_a.name,
                            game.team_b.name,
                            game.score.team_a,
                            game.score.team_b,
                            game.winner,
                            game.loser,
                            game.winner.name,
                            game.loser.name,
                        )
                        for game in self.games_list
                    ],
                    columns=[
                        "Team A",
                        "Team B",
                        "Team A Name",
                        "Team B Name",
                        "Team A Score",
                        "Team B Score",
                        "Winner",
                        "Loser",
                        "Winner Name",
                        "Loser Name",
                    ],
                )

                df_games_by_winner_name = df_games.groupby("Winner Name").count()

                # print(df_games['Winner Name'].value_counts())

                # Premilinary finish
                df_teams["Wins"] = df_teams.Name.apply(
                    lambda x: len(df_games[df_games["Winner Name"] == x])
                )

                # Determine group for ties
                df_teams["Tie Group 1"] = -1
                first_groups_for_ties = (
                    df_teams[["Name", "Wins"]]
                    .groupby("Wins")
                    .agg(list)
                    .sort_index(ascending=False)
                )
                for i in range(len(first_groups_for_ties)):
                    for team in first_groups_for_ties.Name.iloc[i]:
                        # print((i, team))
                        index_of_team_with_this_name = df_teams.index[
                            df_teams.Name == team
                        ].tolist()
                        # print(index_of_team_with_this_name)
                        df_teams.loc[index_of_team_with_this_name, "Tie Group 1"] = i

                # Break ties among first group by
                # (1) wins against tied opponents
                # (2) point diff against tied opponents
                # (3) NON-USAU random number

                df_teams["Wins Against Tie Group 1"] = 0
                df_teams["Point Diff Against Tie Group 1"] = 0
                df_teams["Random Number"] = 0
                for i in df_teams.index:
                    name_here = df_teams.loc[i, "Name"]
                    tie_group_number_here = df_teams.loc[i, "Tie Group 1"]
                    tie_group_here = df_teams[
                        df_teams["Tie Group 1"] == tie_group_number_here
                    ].Name.tolist()
                    tie_group_here.remove(name_here)
                    # print(tie_group_here)
                    df_teams.loc[i, "Wins Against Tie Group 1"] = len(
                        df_games[
                            (df_games["Winner Name"] == name_here)
                            & (
                                df_games["Loser Name"].apply(
                                    lambda x: x in tie_group_here
                                )
                            )
                        ]
                    )

                    points_when_team_A = sum(
                        df_games[
                            (df_games["Team A Name"] == name_here)
                            & (
                                df_games["Team B Name"].apply(
                                    lambda x: x in tie_group_here
                                )
                            )
                        ]["Team A Score"]
                    )

                    points_when_team_B = sum(
                        df_games[
                            (df_games["Team B Name"] == name_here)
                            & (
                                df_games["Team A Name"].apply(
                                    lambda x: x in tie_group_here
                                )
                            )
                        ]["Team B Score"]
                    )

                    opponent_points_when_team_A = sum(
                        df_games[
                            (df_games["Team A Name"] == name_here)
                            & (
                                df_games["Team B Name"].apply(
                                    lambda x: x in tie_group_here
                                )
                            )
                        ]["Team B Score"]
                    )

                    opponent_points_when_team_B = sum(
                        df_games[
                            (df_games["Team B Name"] == name_here)
                            & (
                                df_games["Team A Name"].apply(
                                    lambda x: x in tie_group_here
                                )
                            )
                        ]["Team A Score"]
                    )

                    points_my_team_scored_against_tie_group_opponents = (
                        points_when_team_A + points_when_team_B
                    )

                    points_my_tie_group_opponents_scored_against_me = (
                        opponent_points_when_team_A + opponent_points_when_team_B
                    )

                    df_teams.loc[i, "Point Diff Against Tie Group 1"] = (
                        points_my_team_scored_against_tie_group_opponents
                        - points_my_tie_group_opponents_scored_against_me
                    )

                    df_teams.loc[i, "Random Number"] = random.random()

                df_teams_sorted = df_teams.sort_values(
                    [
                        "Wins",
                        "Wins Against Tie Group 1",
                        "Point Diff Against Tie Group 1",
                        "Random Number",
                    ],
                    ascending=False,
                )

                finish_list = df_teams_sorted["Team"].tolist()

                df_finish = df_teams_sorted.reset_index(drop=True)
                df_finish["Finish"] = df_finish.index + 1

                # print(df_finish)

                return df_finish

            else:
                raise Exception("Method unknown!")

        else:
            raise Exception("Games still need to be played!")


class RoundRobinTournament(Tournament):
    teams_list = []

    def __init__(self, teams_list, played=False):
        self.teams_list = teams_list

        # Games list is each team playing every other team
        # Warning: doesn't care about order of games
        num_teams = len(teams_list)
        games_list = [
            [Game(teams_list[i], teams_list[j]) for j in range(i)]
            for i in range(num_teams)
        ]
        games_list = sum(games_list, [])

        Tournament.__init__(self, games_list=games_list, played=played)

    def determine_placement(self):
        return Tournament.determine_placement(self, method="round robin")


def play_eight_team_single_elimination_bracket(
    teams_list,
    num_bids=1,
    method="random",
    rating_diff_to_victory_margin=None,
    p_a_offense=None,
):
    # Play a bracket with 8 teams, one winner, single elim.
    q1 = Game(teams_list[0], teams_list[7], level="quarter")
    q2 = Game(teams_list[1], teams_list[6], level="quarter")
    q3 = Game(teams_list[2], teams_list[5], level="quarter")
    q4 = Game(teams_list[3], teams_list[4], level="quarter")
    s1 = Game(child_a=q1, child_b=q4, level="semi")
    s2 = Game(child_a=q2, child_b=q3, level="semi")
    f = Game(child_a=s1, child_b=s2, level="final")

    tourney = Tournament(games_list=[q1, q2, q3, q4, s1, s2, f])

    tourney.play_games(
        method=method,
        rating_diff_to_victory_margin=rating_diff_to_victory_margin,
        p_a_offense=p_a_offense,
    )

    return tourney.determine_placement()


def play_twelve_team_tournament(
    teams_list,
    num_bids,
    method="random",
    rating_diff_to_victory_margin=None,
    p_a_offense=None,
):
    # Assumes teams_list is in seed order!
    # Currently in two pools of six format
    # then single elimnation 8 team bracket.

    # NEEDS TO BE UPDATED WITH DESIRED FORMATS!

    if num_bids == 1:
        #
        # Pool play
        #
        a_seeds = [1, 3, 6, 7, 10, 12]
        b_seeds = [2, 4, 5, 8, 9, 11]

        pool_a_teams = [teams_list[i - 1] for i in a_seeds]
        pool_b_teams = [teams_list[i - 1] for i in b_seeds]

        pool_a = RoundRobinTournament(pool_a_teams)
        pool_b = RoundRobinTournament(pool_b_teams)

        print("\nPool A")
        pool_a.play_games(
            method=method,
            rating_diff_to_victory_margin=rating_diff_to_victory_margin,
            p_a_offense=p_a_offense,
        )
        print("\nPool B")
        pool_b.play_games(
            method=method,
            rating_diff_to_victory_margin=rating_diff_to_victory_margin,
            p_a_offense=p_a_offense,
        )
        pool_a_finish = pool_a.determine_placement()
        pool_b_finish = pool_b.determine_placement()

        #
        # Bracket
        #
        remaining_teams = [
            pool_a_finish.loc[0, "Team"],
            pool_b_finish.loc[0, "Team"],
            pool_a_finish.loc[1, "Team"],
            pool_b_finish.loc[1, "Team"],
            pool_b_finish.loc[2, "Team"],
            pool_a_finish.loc[2, "Team"],
            pool_a_finish.loc[3, "Team"],
            pool_b_finish.loc[3, "Team"],
        ]

        print("\n8-team bracket")
        placement = play_eight_team_single_elimination_bracket(
            remaining_teams,
            num_bids=1,
            method=method,
            rating_diff_to_victory_margin=rating_diff_to_victory_margin,
            p_a_offense=p_a_offense,
        )

        return placement

    else:
        raise Exception("Can't do num_bids={num_bids} right now!")
