import math
import itertools
from abc import ABC, abstractmethod


import numpy as np
import pandas as pd

from .game import Game


class Tournament(ABC):
    def __init__(self, games_list=None, played=False, teams_list=None, name=None):
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
        self.name = name or self.__class__.__name__

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

    def show_results(self):
        if not self.played:
            print("Games have not yet been finished")
            return
        order = self.determine_placement()
        print(f"{self.name} - Final Results")
        for i, team in enumerate(order):
            print(f"{i+1}. {team.name}")


class SingleEliminationBracket(Tournament):
    def __init__(self, games_list=None, played=False, teams_list=None, name=None):
        super().__init__(
            games_list=games_list, played=played, teams_list=teams_list, name=name
        )

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

    def __init__(self, teams_list=None, played=False, name=None):
        self.teams_list = teams_list

        # Games list is each team playing every other team
        # Warning: doesn't care about order of games
        num_teams = len(teams_list)
        combinations = itertools.combinations(teams_list, 2)
        games_list = [
            Game(pair[0], pair[1], level="pool")
            for pair in combinations
            if pair[0] != pair[1]
        ]
        super().__init__(games_list=games_list, played=played, name=name)

    def determine_placement(self):
        df_teams = pd.DataFrame(
            {"Team": self.teams_list, "Name": [team.name for team in self.teams_list],}
        )

        # Data frame of each game
        df_games = pd.DataFrame([game.results_dict for game in self.games_list])
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
                    & (df_games["Loser Name"].apply(lambda x: x in tie_group_here))
                ]
            )

            points_when_team_A = sum(
                df_games[
                    (df_games["Team A Name"] == name_here)
                    & (df_games["Team B Name"].apply(lambda x: x in tie_group_here))
                ]["Team A Score"]
            )

            points_when_team_B = sum(
                df_games[
                    (df_games["Team B Name"] == name_here)
                    & (df_games["Team A Name"].apply(lambda x: x in tie_group_here))
                ]["Team B Score"]
            )

            opponent_points_when_team_A = sum(
                df_games[
                    (df_games["Team A Name"] == name_here)
                    & (df_games["Team B Name"].apply(lambda x: x in tie_group_here))
                ]["Team B Score"]
            )

            opponent_points_when_team_B = sum(
                df_games[
                    (df_games["Team B Name"] == name_here)
                    & (df_games["Team A Name"].apply(lambda x: x in tie_group_here))
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

        return df_finish.Team.tolist()


class BracketThreeOne(Tournament):
    pass


class BracketFourOne(Tournament):
    """
    Bracket 4.1
    This should never be used alone. A team should never be eliminated from a tournament
    after losing only one game. On the other hand, this is a fairly typical format for
    use in the second half of a tournament. 
    """

    def __init__(self, teams_list, name=None):
        a = Game(teams_list[0], teams_list[3], level="semi")
        b = Game(teams_list[1], teams_list[2], level="semi")
        c = Game(None, None, child_a=a, child_b=b, level="final")
        super().__init__(games_list=[a, b, c], teams_list=teams_list, name=name)

    def determine_placement(self):
        a, b, c = self.games_list
        return [c.winner, c.loser, b.loser, a.loser]


class BracketFourTwoOne(Tournament):
    """
    Bracket 4.2.1
    modified four-team double elimination. This format is very exciting if second place matters. 
    Alone, it doesn't offer much. A team that loses two games is finished. 
    But it has its place if used as the second day of a tournament where you have eliminated 
    down to four teams the day earlier. 
    """

    def __init__(self, teams_list, name=None):
        a, b, c = BracketFourOne(teams_list).games_list
        d = Game(child_a=a, child_b=b, a_result="loser", b_result="loser")
        e = Game(child_a=c, a_result="loser", child_b=d)
        super().__init__(games_list=[a, b, c, d, e], teams_list=teams_list, name=name)

    def determine_placement(self):
        a, b, c, d, e = self.games_list
        return [c.winner, e.winner, e.loser, d.loser]


class BracketFourTwoTwo(BracketFourTwoOne):
    """
    modified four-team double elimination – seeding out of two pools.
    Reseed teams before calling.
    """

    def __init__(self, teams_list, name=None):
        super().__init__(teams_list=teams_list, name=name)

    # return four_two_one(teams_list)


class BracketFourThree(Tournament):
    """
    This is essentially table 4.4.1, four team double elimination, with the first round
    removed. It should never be used by itself, but it is used in some formats after
    pool play.
    """

    def __init__(self, teams_list, name=None):
        a = Game(teams_list[0], teams_list[1])
        b = Game(teams_list[2], teams_list[3])
        c = Game(a.loser, child_b=b)
        super().__init__(games_list=[a, b, c], teams_list=teams_list, name=name)

    def determine_placement(self):
        return [a.winner, c.winner, c.loser, b.loser]


class BracketFiveOne(Tournament):
    def __init__(self, teams_list, name=None):
        a = Game(teams_list[1], teams_list[2])
        b = Game(teams_list[0], child_b=a)
        c = Game(teams_list[3], teams_list[4])
        d = Game(child_a=a, a_result="loser", child_b=c)
        super().__init__(games_list=[a, b, c, d], teams_list=teams_list, name=name)

    def determine_placement(self):
        a, b, c, d = self.games_list
        return [b.winner, b.loser, d.winner, d.loser, c.loser]


class BracketFiveTwo(Tournament):
    def __init__(self, teams_list, name=None):
        a = Game(teams_list[1], teams_list[4])
        b = Game(teams_list[3], teams_list[2])
        c = Game(child_a=a, child_b=b)
        d = Game(child_a=a, child_b=b, a_result="loser", b_result="loser")
        super().__init__(games_list=[a, b, c, d], teams_list=teams_list, name=name)

    def determine_placement(self):
        return [self.teams_list[0], c.winner, c.loser, d.winner, d.loser]


class BracketSixOneOne(Tournament):
    def __init__(self, teams_list, name=None):
        a = Game(teams_list[3], teams_list[4])
        b = Game(teams_list[2], teams_list[5])
        c = Game(teams_list[0], child_b=a)
        d = Game(teams_list[1], child_b=b)
        e = Game(child_a=c, child_b=d)
        f = Game(child_a=c, child_b=d, a_result="loser", b_result="loser")
        g = Game(child_a=a, child_b=b, a_result="loser", b_result="loser")
        super().__init__(
            games_list=[a, b, c, d, e, f, g], teams_list=teams_list, name=name
        )

    def determine_placement(self):
        a, b, c, d, e, f, g = self.games_list
        return [e.winner, e.loser, f.winner, f.loser, g.winner, g.loser]


class BracketSixOneTwo(BracketSixOneOne):
    """Seeding should be determined from pools, 1=A1, 2=B1, 3=A2, 4=B2, 5=A3, 6=B3"""

    def __init__(self, teams_list, name=None):
        super().__init__(teams_list=teams_list, name=name)

    @classmethod
    def from_pools(cls, pool_a, pool_b):
        return cls(pool_a[0], pool_b[0], pool_a[1], pool_b[1], pool_a[2], pool_b[2])


class BracketSixTwo(Tournament):
    """
    Note  that  this  bracket  is  not  to  be  used  in  situations  where  more  
    than  two  teams qualify for the next level. 
    """

    def __init__(self, pool_a, pool_b, name=None):
        a = Game(pool_a[0], pool_b[0])
        b = Game(pool_a[1], pool_b[2])
        c = Game(pool_a[2], pool_b[1])
        d = Game(child_a=b, child_b=c)
        e = Game(child_a=a, child_b=d, a_result="loser")
        super().__init__(games_list=[a, b, c, d, e], teams_list=teams_list, name=name)

    def determine_result(self):
        a, b, c, d, e = self.games_list
        return [a.winner, e.winner, e.loser, d.loser, b.loser, c.loser]


class BracketSixThree(Tournament):
    """
    The following approach in used in certain formats where the top three teams must 
    be determined in only two rounds. The finals game is for place only, as both teams 
    have already qualified for the next event. 
    """

    def __init__(self, teams_list, name=None):
        a = Game(teams_list[0], teams_list[1])
        b = Game(teams_list[2], teams_list[5])
        c = Game(teams_list[3], teams_list[4])
        d = Game(child_a=b, child_b=c)
        super().__init__(games_list=[a, b, c, d], teams_list=teams_list, name=name)

    def determine_placement(self):
        a, b, c, d = self.games_list
        return [a.winner, a.loser, d.winner, d.loser, c.loser, b.loser]


class BracketSixFour(Tournament):
    """
    The following approach is used in certain formats where the top four teams must be 
    determined  in  only  two  rounds.  The  finals and the 2/3 game are for place only, 
    as both teams have already qualified for the next event.  The last game for second 
    place can be left unplayed if it meets the conditions outlined in the section on 
    Placement Games on page 2.
    """

    def __init__(self, teams_list, name=None):
        a = Game(teams_list[0], teams_list[1])
        b = Game(teams_list[2], teams_list[3])
        c = Game(child_a=a, child_b=b, a_result="loser")
        d = Game(teams_list[4], teams_list[5])
        e = Game(child_a=b, child_b=d, a_result="loser")
        super().__init__(games_list=[a, b, c, d, e], teams_list=teams_list, name=name)

    def determine_placement(self):
        a, b, c, d, e = self.games_list
        return [a.winner, c.winner, c.loser, e.winner, e.loser, d.loser]


class BracketSevenOne(Tournament):
    """
    The finals are for place only, as the top three teams have already qualified for the next event.
    """

    def __init__(self, teams_list, name=None):
        a = Game(teams_list[0], teams_list[1])
        c = Game(teams_list[3], teams_list[4])
        d = Game(teams_list[5], teams_list[6])
        e = Game(child_a=c, child_b=d, a_result="loser")
        super().__init__(games_list=[a, c, d, e], teams_list=teams_list, name=name)

    def determine_placement(self):
        a, c, d, e = self.games_list
        return [
            a.winner,
            a.loser,
            self.teams_list[2],
            c.winner,
            e.winner,
            e.loser,
            d.loser,
        ]


class BracketSevenTwo(Tournament):
    """
    The finals are for place only, as the top three teams have already qualified for the next event.
    """

    def __init__(self, teams_list, name=None):
        a = Game(teams_list[0], teams_list[1])
        b = Game(teams_list[3], teams_list[6])
        c = Game(teams_list[4], teams_list[5])
        d = Game(child_a=b, child_b=c, a_result="loser", b_result="loser")
        super().__init__(games_list=[a, b, c, d], teams_list=teams_list, name=name)

    def determine_placement(self):
        a, b, c, d = self.games_list
        return [
            a.winner,
            a.loser,
            self.teams_list[2],
            b.winner,
            c.winner,
            d.winner,
            d.loser,
        ]


class BracketEightOne(Tournament):
    def __init__(self, pool_a, pool_b, name=None):
        a = Game(pool_a[0], pool_b[3])
        b = Game(pool_b[1], pool_a[2])
        c = Game(pool_a[1], pool_b[2])
        d = Game(pool_b[0], pool_a[3])
        e = Game(child_a=a, child_b=b, level="semi")
        f = Game(child_a=c, child_b=d, level="semi")
        g = Game(child_a=e, child_b=f, level="final")
        h = Game(child_a=a, a_result="loser", child_b=b, b_result="loser")
        i = Game(child_a=c, child_b=d, a_result="loser", b_result="loser")
        j = Game(child_a=h, child_b=i)
        k = Game(
            child_a=e, child_b=f, a_result="loser", b_result="loser", level="3rd place"
        )
        l = Game(child_a=h, child_b=i, a_result="loser", b_result="loser")
        super().__init__(
            games_list=[a, b, c, d, e, f, g, h, i, j, k, l],
            teams_list=[*pool_a, *pool_b],
            name=name,
        )

    def determine_placement(self):
        a, b, c, d, e, f, g, h, i, j, k, l = self.games_list
        return [
            g.winner,
            g.loser,
            k.winner,
            k.loser,
            j.winner,
            j.loser,
            l.winner,
            l.loser,
        ]


class BracketEightTwoOne(Tournament):
    def __init__(self, pool_a, pool_b, name=None):
        a = Game(pool_a[0], pool_b[1], level="semi")
        b = Game(pool_a[1], pool_b[0], level="semi")
        c = Game(child_a=a, child_b=b, level="final")
        d = Game(pool_a[2], pool_b[3])
        e = Game(pool_a[3], pool_b[2])
        f = Game(child_a=a, a_result="loser", child_b=d)
        g = Game(child_a=e, child_b=b, b_result="loser")
        h = Game(child_a=f, child_b=g)
        i = Game(child_a=c, a_result="loser", child_b=h, level="2nd place")
        j = Game(child_a=d, child_b=e, a_result="loser", b_result="loser")
        k = Game(child_a=f, child_b=g, a_result="loser", b_result="loser")
        super().__init__(
            games_list=[a, b, c, d, e, f, g, h, i, j, k],
            teams_list=[*pool_a, *pool_b],
            name=name,
        )

    def determine_placement(self):
        a, b, c, d, e, f, g, h, i, j, k = self.games_list
        return [
            c.winner,
            i.winner,
            i.loser,
            h.loser,
            k.winner,
            k.loser,
            j.winner,
            j.loser,
        ]


class BracketTwelveFourPools(Tournament):
    def __init__(self, pool_a, pool_b, pool_c, pool_d, name=None):
        # prequarters
        a = Game(pool_b[1], pool_c[2])
        b = Game(pool_c[1], pool_b[2])
        c = Game(pool_d[1], pool_a[2])
        d = Game(pool_d[2], pool_a[1])
        # quarters
        e = Game(pool_a[0], child_b=a, level="quarter")
        f = Game(pool_d[0], child_b=b, level="quarter")
        g = Game(pool_c[0], child_b=c, level="quarter")
        h = Game(pool_b[0], child_b=d, level="quarter")

        # semis
        i = Game(child_a=e, child_b=f, level="semi")
        j = Game(child_a=g, child_b=h, level="semi")

        # finals
        k = Game(child_a=i, child_b=j, level="final")

        # 3rd place
        l = Game(
            child_a=i, child_b=j, a_result="loser", b_result="loser", level="3rd place"
        )

        # 5th place
        m = Game(
            child_a=e,
            child_b=g,
            a_result="loser",
            b_result="loser",
            level="5th place semis",
        )
        n = Game(
            child_a=f,
            child_b=h,
            a_result="loser",
            b_result="loser",
            level="5th place semis",
        )
        o = Game(child_a=m, child_b=n, level="5th place")

        # 7th place
        p = Game(child_a=m, child_b=n, a_result="loser", b_result="loser")

        # 9th place
        q = Game(
            child_a=a,
            child_b=b,
            a_result="loser",
            b_result="loser",
            level="9th place semis",
        )
        r = Game(
            child_a=c,
            child_b=d,
            a_result="loser",
            b_result="loser",
            level="9th place semis",
        )
        s = Game(child_a=q, child_b=r, level="9th place")

        # 11th place
        t = Game(
            child_a=q, child_b=r, a_result="loser", b_result="loser", level="11th place"
        )

        super().__init__(
            games_list=[a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t],
            teams_list=[*pool_a, *pool_b, *pool_c, *pool_d],
            name=name,
        )

    def determine_placement(self):
        a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t = self.games_list
        return [
            k.winner,
            k.loser,
            l.winner,
            l.loser,
            o.winner,
            o.loser,
            p.winner,
            p.loser,
            s.winner,
            s.loser,
            t.winner,
            t.loser,
        ]


class BracketSixteenOne(Tournament):
    """
    The bracket only contains 12 teams, as the pool losers do not advance to the bracket
    """

    def __init__(self, pool_a, pool_b, pool_c, pool_d, name=None):
        # prequarters
        a = Game(pool_b[1], pool_c[2], level="prequarters")
        b = Game(pool_c[1], pool_b[2], level="prequarters")
        c = Game(pool_a[2], pool_d[1], level="prequarters")
        d = Game(pool_d[2], pool_a[1], level="prequarters")

        # quarters
        e = Game(pool_a[0], child_b=a, level="quarters")
        f = Game(pool_d[0], child_b=b, level="quarters")
        g = Game(pool_c[0], child_b=c, level="quarters")
        h = Game(pool_b[0], child_b=d, level="quarters")

        # semis
        i = Game(child_a=e, child_b=f, level="semis")
        j = Game(child_a=g, child_b=h, level="semis")

        # finals
        k = Game(child_a=i, child_b=j, level="final")

        # meaningless_games
        l = Game(pool_a[3], pool_b[3], level="last 4")
        m = Game(pool_c[3], pool_d[3], level="last 4")

        super().__init__(
            games_list=[a, b, c, d, e, f, g, h, i, j, k, l, m],
            teams_list=[*pool_a, *pool_b, *pool_c, *pool_d],
            name=name,
        )

    def determine_placement(self):
        a, b, c, d, e, f, g, h, i, j, k, l, m = self.games_list
        return [
            k.winner,
            k.loser,
            i.loser,
            j.loser,
            e.loser,
            f.loser,
            g.loser,
            h.loser,
            a.loser,
            b.loser,
            c.loser,
            d.loser,
            l.winner,
            m.winner,
            l.loser,
            m.loser,
        ]


class BracketSixteenTwoTwo(Tournament):
    def __init__(self, pool_a, pool_b, pool_c, pool_d, name=None):
        a = Game(pool_a[0], pool_d[0])
        b = Game(pool_c[0], pool_b[0])
        c = Game(child_a=a, child_b=b, level="final")
        d = Game(pool_c[1], pool_d[2])
        e = Game(pool_a[2], pool_b[1])
        f = Game(pool_a[1], pool_b[2])
        g = Game(pool_c[2], pool_d[1])

        h = Game(child_a=d, child_b=e, level="2nd place pre-q")
        i = Game(child_a=f, child_b=g, level="2nd place pre-q")

        j = Game(child_a=a, a_result="loser", child_b=h, level="2nd place q")
        k = Game(child_a=i, child_b=b, b_result="loser", level="2nd place q")

        l = Game(child_a=j, child_b=k, level="2nd place play-in")
        m = Game(child_a=c, a_result="loser", child_b=l, level="2nd place")

        n = Game(child_a=h, child_b=i, a_result="loser", b_result="loser")
        o = Game(
            child_a=d,
            child_b=e,
            a_result="loser",
            b_result="loser",
            level="9th place semis",
        )
        p = Game(
            child_a=f,
            child_b=g,
            a_result="loser",
            b_result="loser",
            level="9th place semis",
        )
        q = Game(child_a=o, child_b=p, level="9th place")

        r = Game(
            child_a=o, child_b=p, a_result="loser", b_result="loser", level="11th place"
        )

        s = Game(pool_a[3], pool_d[3])
        t = Game(pool_c[3], pool_b[3])
        u = Game(child_a=s, child_b=t, level="13th place")
        v = Game(
            child_a=s, child_b=t, a_result="loser", b_result="loser", level="15th place"
        )
        super().__init__(
            games_list=[a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v],
            teams_list=[*pool_a, *pool_b, *pool_c, *pool_d],
            name=name,
        )

    def determine_placement(self):
        a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v = self.games_list
        return [
            c.winner,
            m.winner,
            m.loser,
            l.loser,
            j.loser,
            k.loser,
            n.winner,
            n.loser,
            q.winner,
            q.loser,
            r.winner,
            r.loser,
            u.winner,
            u.loser,
            v.winner,
            v.loser,
        ]
