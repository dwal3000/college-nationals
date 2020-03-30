import math
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from .game import Game


class Tournament(ABC):
    def __init__(self, games_list=None, played=False, teams_list=None):
        if games_list:
            self.games_list = games_list
        else:
            self.games_list = []
        if teams_list:
            self.teams_list = teams_list
        else: 
            unique_teams = set()
            for game in self.games_list:
                unique_teams.add(game.team_a)
                unique_teams.add(game.team_b)
            self.teams_list = list(unique_teams)
        self.played = played

    @property
    def num_teams(self):
        return len(self.teams_list)

    @property
    def num_games(self):
        return len(self.games_list)

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

    @abstractmethod
    def determine_placement(self):
        pass

class SingleEliminationBracket(Tournament):
    def __init__(self, games_list=None, played=False, teams_list=None):
        super().__init__(games_list=games_list, played=played, teams_list=teams_list)

    def determine_placement(self):
        if self.played:
            # Look for a team that won finals
            games_with_level_equal_finals = [
                game for game in self.games_list if game.level == "final"
            ]
            if len(games_with_level_equal_finals) == 1:
                return [(1, games_with_level_equal_finals[0].winner)]
            elif len(games_with_level_equal_finals) == 0:
                raise Exception("No 'final' level games were played!")
            else:
                raise Exception("Multiple teams won 'final' level game!")

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

        super.__init__(self, games_list=games_list, played=played)

    def determine_placement(self):
        df_teams = pd.DataFrame(
            {
                "Team": self.teams_list,
                "Name": [team.name for team in self.teams_list],
            }
        )

        # Data frame of each game
        df_games = pd.DataFrame([game.results_dict for game in games_list])
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

            df_teams.loc[i, "Random Number"] = np.random.rand()

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

class BracketThreeOne(Tournament):
    pass

class BracketFourOne(Tournament):
    """
    Bracket 4.1
    This should never be used alone. A team should never be eliminated from a tournament
    after losing only one game. On the other hand, this is a fairly typical format for
    use in the second half of a tournament. 
    """
    def __init__(self, teams_list):
        a = Game(teams_list[0], teams_list[3])
        b = Game(teams_list[1], teams_list[2])
        c = Game(None, None, child_a=a, child_b=b)
        super().__init__(games_list=[a, b, c], teams_list=teams_list)

    def determine_placement(self):
        a, b, c = self.games_list
        return [c.winner, c.loser, b.loser, a.loser]

class BracketFourTwoOne(Tournament):
    """
    Bracket 4.2.1
    modified four-team double elimination. This format is very exciting if second place matters. Alone, it doesn't offer much.
    A team that loses two games is finished. But it has its place if used as the second
    day of a tournament where you have eliminated down to four teams the day earlier. 
    """
    def __init__(self, teams_list):
        a, b, c = BracketFourOne(teams_list).games_list
        d = Game(child_a=a, child_b=b, a_result='loser', b_result='loser')
        e = Game(child_a=c, a_result='loser', child_b=d)
        super().__init__(games_list=[a, b, c, d, e], teams_list=teams_list)
    
    def determine_placement(self):
        a, b, c, d, e = self.games_list
        return [c.winner, e.winner, e.loser, d.loser]

class BracketFourTwoTwo(BracketFourTwoOne):
    """
    modified four-team double elimination – seeding out of two pools.
    Reseed teams before calling.
    """
    def __init__(self, teams_list):
        super().__init__(teams_list=teams_list)
    # return four_two_one(teams_list)

class BracketFourThree(Tournament):
    """
    This is essentially table 4.4.1, four team double elimination, with the first round
    removed. It should never be used by itself, but it is used in some formats after
    pool play.
    """
    def __init__(self, teams_list):
        a = Game(teams_list[0], teams_list[1])
        b = Game(teams_list[2], teams_list[3])
        c = Game(a.loser, child_b=b)
        super().__init__(games_list=[a, b, c], teams_list=teams_list)

    def determine_placement(self):
        return [a.winner, c.winner, c.loser, b.loser]


class BracketFiveOne(Tournament):
    def __init__(self, teams_list):
        a = Game(teams_list[1], teams_list[2])
        b = Game(teams_list[0], child_b=a)
        c = Game(teams_list[3], teams_list[4])
        d = Game(a.loser, child_b=c)
        super().__init__(games_list=[a, b, c, d], teams_list=teams_list)
    
    def determine_placement(self):
        return [b.winner, b.loser, d.winner, d.loser, c.loser]

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
