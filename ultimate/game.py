import re

import pandas as pd
import numpy as np
import collections

from .utils import get_default_parameters

# Handy way for storing scores
class Score:
    def __init__(self, team_a, team_b, point_log):
        self.team_a = team_a
        self.team_b = team_b
        self.point_log = point_log

    def __repr__(self):
        return f"{round(self.team_a, 1)} - {round(self.team_b, 1)}"


class Game:
    """
    Representation of a single ultimate game between two teams. It contains multiple different 
    methods for simulating the game, and can be initialized with a starting condition `p_a_offense`
    which can simulate how windy it is (a lower value means harder to score a possession)
    """

    def __init__(
        self,
        team_a=None,
        team_b=None,
        child_a=None,
        child_b=None,
        a_result="winner",
        b_result="winner",
        score=None,
        played=False,
        winner=None,
        loser=None,
        level=None,
        division="mens",
        method="double negative binomial",
        game_to=15,
        rating_diff_to_victory_margin=None,
        p_a_offense=0.7,
    ):
        (
            default_p_a_offense,
            default_k,
            default_rating_diff_to_victory_margin,
            default_game_to,
        ) = get_default_parameters(division)

        self.team_a = team_a
        self.team_b = team_b
        self.child_a = child_a
        self.child_b = child_b
        self.a_result = a_result
        self.b_result = b_result
        self.score = score
        self.played = played
        self.winner = winner
        self.loser = loser
        self.level = level
        self.method = method
        self.game_to = game_to or default_game_to
        self.rating_diff_to_victory_margin = (
            rating_diff_to_victory_margin or default_rating_diff_to_victory_margin
        )
        self.p_a_offense = p_a_offense or default_p_a_offense
        self.calculate_expected_score()

    def __repr__(self):
        if self.played:
            if self.level:
                return f"{self.level}: {self.team_a.name} {self.score.team_a}-{self.score.team_b} {self.team_b.name} (Expected {self.expected_score})"
            else:
                return f"{self.team_a.name} {self.score.team_a}-{self.score.team_b} {self.team_b.name} (Expected {self.expected_score})"
        else:
            return f"""Game between {self.team_a.name if self.team_a is not None else 'TBD'} and {self.team_b.name if self.team_b is not None else 'TBD'} has not yet been played. 
    Expected Score is: {self.expected_score}"""

    def display_point_log(self):
        if self.played:
            for point in self.score.point_log:
                print(f"{self.team_a.name} {point[0]}-{point[1]} {self.team_b.name}")

    def display_score(self):
        print(self)

    def to_series(self):
        return pd.Series(self.results_dict)

    def list_team_names(self):
        return [self.team_a.name, self.team_b.name]

    def calculate_expected_score(self):
        if self.team_a is not None and self.team_b is not None:
            self.expected_score = self.__class__.convert_ratings_to_expected_game_score(
                self.team_a.rating,
                self.team_b.rating,
                self.game_to,
                self.rating_diff_to_victory_margin,
            )
        else:
            self.expected_score = None

    @property
    def results_dict(self) -> dict:
        if self.played:
            return {
                "Game Level": self.level,
                "Team A Name": self.team_a.name,
                "Team A Score": self.score.team_a,
                "Team B Score": self.score.team_b,
                "Team B Name": self.team_b.name,
                "Expected Team A Score": self.expected_score.team_a,
                "Expected Team B Score": self.expected_score.team_b,
                "Upset": (
                    (self.expected_score.team_a == 15 and self.score.team_a < 15)
                    or (self.expected_score.team_b == 15 and self.score.team_b < 15)
                ),
                "Winner Name": self.winner.name,
                "Loser Name": self.loser.name,
            }
        else:
            return None

    # TODO:
    def resolve_children(self):
        # Check if there is a team_a.  If there is no team_a
        # then see if there is a play-in game.  If so, play it.
        # If not, then raise error because there is no one to play!
        if not self.team_a:
            if self.child_a:
                # Play child_a game
                self.child_a.play_game()
                # Winner of child_a becomes team_a unless a_result == 'loser'
                self.team_a = getattr(self.child_a, self.a_result)
            else:
                raise Exception("No team team_a or game child_a!")

        # Same for team_b
        if not self.team_b:
            if self.child_b:
                # Play child_b game
                self.child_b.play_game()
                # Winner of child_b becomes team_bunless b_result == 'loser'
                self.team_b = getattr(self.child_b, self.b_result)
            else:
                raise Exception("No team team_b or game child_b!")

    def play_game(
        self,
        method=None,
        game_to=None,
        rating_diff_to_victory_margin=None,
        p_a_offense=None,
        print_results=False,
    ) -> None:
        """
        Resolves the game and all children. Game settings can be overridden when calling 
        this method if we want to add unusual circumstances, but will default to how the
        game object was constructed. This game and all children will have Score objects
        and have played == True after this executes. 
        
        Parameters
        ----------
        method : str, optional
            statistical method to use to simulate the outcome, usually "double negative binomial", by default None
        game_to : int, optional
            Final score which would determine victory, usually 15, by default None
        rating_diff_to_victory_margin : [type], optional
            [description], by default None
        p_a_offense : [type], optional
            [description], by default None
        
        Returns
        -------
        None
        """
        # If user doesn't specify the options here, set them to game defaults
        if not method:
            method = self.method
        if not game_to:
            game_to = self.game_to
        if not rating_diff_to_victory_margin:
            rating_diff_to_victory_margin = self.rating_diff_to_victory_margin
        if not p_a_offense:
            p_a_offense = self.p_a_offense

        # Check if game has been played
        if not self.played:
            self.resolve_children()
            if self.expected_score is None:
                self.calculate_expected_score()
            # Actually play game
            team_a_wins, self.score = self.simulate_game_by_method(method)

            if team_a_wins:
                self.winner = self.team_a
                self.loser = self.team_b
            else:
                self.winner = self.team_b
                self.loser = self.team_a

            self.played = True
            if print_results:
                self.display_score()
            self.team_a.games_list.append(self)
            self.team_b.games_list.append(self)
            self.team_a.get_record()
            self.team_b.get_record()

    def play_binomial_game(self, game_to=15) -> Score:
        """
        WARNING: NOT AS REALISITC AS play_double_negative_binomial_game

        Simulate a binomial game to game_to with a probability of success p.
        Game ends when either team's score reaches game_to.
        Returns a Score tuple of the scores.

        Simulate game as first to achieve 15 successes of a weighted coin flip.
        
        Assume if game is expected to finish Team A 15-8 Team B, then the probability
        of Team A winning a particular point is p = 15 / (15 + 8).
        Then, a new full game can be simulated as a sequence of Bernoulli trials with
        probability with p that terminates when either the number of success or failures
        reaches game_to.
        """
        p = (
            self.expected_score.team_a
            * 1.0
            / (self.expected_score.team_a + self.expected_score.team_b)
        )  # Prob A wins a given point

        team_a_score, team_b_score = 0, 0
        game_is_going = True

        point_log = []
        while game_is_going:
            if np.random.rand() < p:
                team_a_score += 1
            else:
                team_b_score += 1
            point_log.append((team_a_score, team_b_score))
            game_is_going = (team_a_score < game_to) and (team_b_score < game_to)

        return Score(team_a=team_a_score, team_b=team_b_score, point_log=point_log)

    def play_double_negative_binomial_game(self, game_to=15) -> Score:
        """
        Simulate a game by flipping a coin with p_heads = p_a_offense until heads
        (heads->Team A, tails->Team B).  Then, flip a coin with p_heads = p_b_offense
        until heads (heads->Team B, tails->Team A).

        Game ends when either team's score reaches game_to.

        Returns a Score tuple of the scores.

        Simulate game as using two weighted coins (one for each team's offense).

        Randomly decide which team starts on offense.  Say team A goes first,
        flip their weighted coin with
        probability P_a_offense until a heads is seen.  Record 1 point for
        Team A and the number of tails seen as points for Team B.  Then it's
        B's turn to be on offense.  Flip the weighted coin with probability
        P_b_offense until a heads seen.  Record a 1 point from Team B and the
        number of tails seen as points for Team A.

        Repeat until one team has 15 points.

        Assumes there are two distinct fixed probabilities:
         -  P_a_offense = the prob A scores a point when on offense
         -  P_b_offense = the prob B score a point when on offense

        We don't know a priori what the relationship is between P_a_offense and
        P_b_offense.  And we only have one input currently: the expected game score
        (e.g. 15-8).  So we have two unknowns and one piece of information.
        So, we make the simplifying assumption (based on data from Ultianalytics.com)
        that for elite mens college teams, the winning team typically has a
        P_a_offense = 0.8.  Then, to get an expected result 15-8, we need
        P_b_offense = P_a_offense * 8/15.

        Note: P_a_offense = 0.8 is an important assumption.  If it were greater,
        scores would have less variance.  If it were less, scores would have more
        variance.  Thus, if it's a cross wind, then P_a_offense would likely be
        closer to 0.5.  Meanwhile, in perfect conditions, one would expect
        P_a_offense to be slightly higher.
        """
        expected_score = self.expected_score
        # Assign expected winner's probability of scoring an O-point to be
        # p_a_offense (usually 0.8)
        if expected_score.team_a > expected_score.team_b:
            p_a_offense = self.p_a_offense
            p_b_offense = p_a_offense * expected_score.team_b / (1.0 * game_to)
        else:
            p_b_offense = self.p_a_offense
            p_a_offense = p_b_offense * expected_score.team_a / (1.0 * game_to)

        # Determine starting team
        team_a_on_offense = np.random.rand() < 0.5

        # Game starts 0-0
        team_a_score, team_b_score = 0, 0

        point_log = []

        while (team_a_score < game_to) and (team_b_score < game_to):
            if team_a_on_offense:
                if np.random.rand() < p_a_offense:
                    team_a_score += 1
                    team_a_on_offense = False
                else:
                    team_b_score += 1
            else:
                if np.random.rand() < p_b_offense:
                    team_b_score += 1
                    team_a_on_offense = True
                else:
                    team_a_score += 1
            point_log.append((team_a_score, team_b_score))

        return Score(team_a=team_a_score, team_b=team_b_score, point_log=point_log)

    def simulate_game_by_method(self, method="random"):
        """
        Simulate the outcome of the game. The result should be based on the teams' ratings.
        When `play_game` is called, a single simulation will be run that stores the result
        in the Game object. This method can be called multiple times independently if we want
        to generate probabilistic results. 

        This function returns True if team A wins and False if team B wins, and
        the score.
        """
        game_to = self.game_to
        score = None
        # Team A always wins by 2 (usually 15-13)
        if method == "team_a":
            team_a_score = game_to
            team_b_score = np.max([0, team_a_score - 2])

        # Team B always wins by 2 (usually 15-13)
        elif method == "team_b":
            team_b_score = game_to
            team_a_score = np.max([0, team_b_score - 2])

        # Higher rating always wins
        elif method == "higher_rating":  # Team A wins
            if team_a_rating > team_b_rating:
                team_a_score = game_to
                team_b_score = np.max([0, team_a_score - 2])
            else:
                team_a_score = game_to
                team_b_score = np.max([0, team_a_score - 2])

        # Random coin flip
        elif method == "random":
            if np.random.rand() > 0.5:
                team_a_score = game_to
                team_b_score = np.max([0, team_a_score - 2])
            else:
                team_b_score = game_to
                team_a_score = np.max([0, team_b_score - 2])

        elif method == "binomial":  # Use ratings
            score = self.play_binomial_game()

        elif method == "double negative binomial":
            # Convert ratings to expected score
            score = self.play_double_negative_binomial_game()

        # Method not recognized
        else:
            raise ValueError("method not recognized")
            team_a_score = -1
            team_b_score = -2

        # Record score in named Tuple for methods where needed
        if score is None:
            score = Score(
                team_a=team_a_score,
                team_b=team_b_score,
                point_log=[(team_a_score, team_b_score)],
            )

        # Team A wins if they have more points
        team_a_wins = score.team_a > score.team_b

        return team_a_wins, score

    @staticmethod
    def convert_ratings_to_expected_game_score(
        team_a_rating, team_b_rating, game_to, rating_diff_to_victory_margin
    ):
        """
        Take USAU Power Ratings of two teams and get expected game_score
        """
        if team_a_rating >= team_b_rating:
            team_a_score = game_to
            team_b_score = team_a_score - rating_diff_to_victory_margin(
                team_a_rating - team_b_rating
            )
        else:
            team_b_score = game_to
            team_a_score = team_b_score - rating_diff_to_victory_margin(
                team_b_rating - team_a_rating
            )
        return Score(
            team_a=team_a_score,
            team_b=team_b_score,
            point_log=[(team_a_score, team_b_score)],
        )

    @classmethod
    def simulate_game_from_ratings(
        cls, team_a_rating, team_b_rating, game_to=15, method="double negative binomial"
    ) -> (bool, Score):
        """
        Simulates a single game with arbitrary teams given two ratings
        
        Parameters
        ----------
        team_a_rating : float
            USAU Rating to use for team A
        team_b_rating : float
            USAU Rating to use for team B
        game_to : int
            Final score to use for game initialization
        method : str
            Type of simulation that should be run for the game outcome
        Returns
        -------
        (bool, Score)
            Tuple of whether or not Team A wins and resulting Score object
        """
        g = cls(
            team_a=Team(name="Team A", rating=team_a_rating),
            team_b=Team(name="Team B", rating=team_b_rating),
            method=method,
            game_to=game_to,
        )
        return g.simulate_game_by_method(method)
