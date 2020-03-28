# ultimate.py
# Daniel Walton
# 3/27/2020


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib as mpl
import seaborn as sns
import re
import math
import collections
import random
from sklearn.model_selection import train_test_split, ShuffleSplit
from sklearn.linear_model import LogisticRegression
from scipy.optimize import curve_fit
from scipy.stats import percentileofscore
from numpy.random import binomial


#
# Default parameters (from 2019 Sectionals/Regionals)
#
def get_default_parameters(division):
    womens_optimal_p_a_offense = 0.65
    mens_optimal_p_a_offense = 0.8

    womens_k = 0.0022838954964262735
    mens_k   = 0.002138514393927596

    womens_rating_diff_to_victory_margin = \
        lambda x: logistic_victory_margin(x, womens_k)
    mens_rating_diff_to_victory_margin = \
        lambda x: logistic_victory_margin(x, mens_k)

    # Set standard game length
    game_to = 15

    if division in ['men','mens']:
        return mens_optimal_p_a_offense, mens_k, mens_rating_diff_to_victory_margin, game_to
    elif division in ['women','womens']:
        return womens_optimal_p_a_offense, womens_k, womens_rating_diff_to_victory_margin, game_to
    else:
        raise Exception("Can't load parameters: division not recognized!")




# Handy way for storing scores
Score = collections.namedtuple('Score', ['team_a', 'team_b'])

# Format for game logs
GameLog = collections.namedtuple('GameLog', ['level','name','team_a_name','team_b_name',\
                                             'score','winner','loser',\
                                             'child_a','child_b','parent'])



def simulate_binomial_game(game_to, p):
    """
    WARNING: NOT AS REALISITC AS simulate_double_negative_binomial_game

    Simulate a binomial game to game_to with a probability of success p.

    Game ends when either team's score reaches game_to.

    Returns a Score tuple of the scores.
    """

    team_a_score, team_b_score = 0, 0

    game_is_going = True

    while game_is_going:
        if np.random.rand() < p:
            team_a_score += 1
        else:
            team_b_score += 1
        game_is_going = (team_a_score < game_to) and (team_b_score < game_to)

    return Score(team_a=team_a_score, team_b=team_b_score)





def simulate_double_negative_binomial_game(game_to, p_a_offense, p_b_offense):
    """
    Simulate a game by flipping a coin with p_heads = p_a_offense until heads
    (heads->Team A, tails->Team B).  Then, flip a coin with p_heads = p_b_offense
    until heads (heads->Team B, tails->Team A).

    Game ends when either team's score reaches game_to.

    Returns a Score tuple of the scores.
    """

    # Determine starting team
    team_a_on_offense = np.random.rand() < 0.5

    # Game starts 0-0
    team_a_score, team_b_score = 0, 0

    # Start game
    game_is_going = True

    while game_is_going:
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
        game_is_going = (team_a_score < game_to) and (team_b_score < game_to)
    return Score(team_a=team_a_score, team_b=team_b_score)






def simulate_game_outcome(team_a_rating, team_b_rating,
                          rating_diff_to_victory_margin=None,
                          method='random',
                          game_to=15, p_a_offense=0.8):
    """
    Simulate the outcome of single game played between team A and team B.
    The result should be based on the teams' ratings.

    This function returns True if team A wins and False if team B wins, and
    the score.

    """

    # Team A always wins
    if method=='team_a':
        team_a_score = game_to
        team_b_score = np.max([0,team_a_score-2])

    # Team B always wins
    elif method=='team_b': # Team A wins
        team_b_score = game_to
        team_a_score = np.max([0,team_b_score-2])

    # Higher rating always wins
    elif method=='higher_rating': # Team A wins
        if team_a_rating > team_b_rating:
            team_a_score = game_to
            team_b_score = np.max([0,team_a_score-2])
        else:
            team_a_score = game_to
            team_b_score = np.max([0,team_a_score-2])

    # Random coin flip
    elif method=='random':
        if random.random()>0.5:
            team_a_score = game_to
            team_b_score = np.max([0,team_a_score-2])
        else:
            team_b_score = game_to
            team_a_score = np.max([0,team_b_score-2])

    # 'binomial': Simulate game as first to achieve 15 successes of a
    # weighted coin flip.
    #
    # Assume if game is expected to finish Team A 15-8 Team B, then the probability
    # of Team A winning a particular point is p = 15 / (15 + 8).
    # Then, a new full game can be simulated as a sequence of Bernoulli trials with
    # probability with p that terminates when either the number of success or failures
    # reaches game_to.
    elif method=='binomial': # Use ratings
        expected_score = convert_ratings_to_expected_game_score(team_a_rating,
                                                                team_b_rating,
                                                                game_to,
                                                                rating_diff_to_victory_margin)

        p = expected_score.team_a*1.0 / (expected_score.team_a + expected_score.team_b) # Prob A wins a given point

        actual_score_this_time = simulate_binomial_game(game_to, p)
        team_a_score = actual_score_this_time.team_a
        team_b_score = actual_score_this_time.team_b



#     'double negative binomial': Simulate game as using two weighted coins
#      (one for each team's offense).

#     Randomly decide which team starts on offense.  Say team A goes first,
#     flip their weighted coin with
#     probability P_a_offense until a heads is seen.  Record 1 point for
#     Team A and the number of tails seen as points for Team B.  Then it's
#     B's turn to be on offense.  Flip the weighted coin with probability
#     P_b_offense until a heads seen.  Record a 1 point from Team B and the
#     number of tails seen as points for Team A.

#     Repeat until one team has 15 points.

#     Assumes there are two distinct fixed probabilities:
#      -  P_a_offense = the prob A scores a point when on offense
#      -  P_b_offense = the prob B score a point when on offense

#     We don't know a priori what the relationship is between P_a_offense and
#     P_b_offense.  And we only have one input currently: the expected game score
#     (e.g. 15-8).  So we have two unknowns and one piece of information.
#     So, we make the simplifying assumption (based on data from Ultianalytics.com)
#     that for elite mens college teams, the winning team typically has a
#     P_a_offense = 0.8.  Then, to get an expected result 15-8, we need
#     P_b_offense = P_a_offense * 8/15.

#     Note: P_a_offense = 0.8 is an important assumption.  If it were greater,
#     scores would have less variance.  If it were less, scores would have more
#     variance.  Thus, if it's a cross wind, then P_a_offense would likely be
#     closer to 0.5.  Meanwhile, in perfect conditions, one would expect
#     P_a_offense to be slightly higher.
    elif method=='double negative binomial':
        # Convert ratings to expected score
        expected_score = convert_ratings_to_expected_game_score(team_a_rating,
                                                                team_b_rating,
                                                                game_to,
                                                                rating_diff_to_victory_margin)

        # Assign expected winner's probability of scoring an O-point to be
        # p_a_offense (usually 0.8)
        if expected_score.team_a > expected_score.team_b:
            p_a_offense = p_a_offense
            p_b_offense = p_a_offense * expected_score.team_b/(1.0*game_to)
        else:
            p_b_offense = p_a_offense
            p_a_offense = p_b_offense * expected_score.team_a/(1.0*game_to)

        # Simulate double binomial
        actual_score_this_time = simulate_double_negative_binomial_game(game_to, p_a_offense=p_a_offense, p_b_offense=p_b_offense)
        team_a_score = actual_score_this_time.team_a
        team_b_score = actual_score_this_time.team_b


    # Method not recognized
    else:
        raise ValueError('method not recognized')
        team_a_score = -1
        team_b_score = -2

    # Record score in named Tuple
    score = Score(team_a=team_a_score, team_b=team_b_score)

    # Team A wins if they have more points
    team_a_wins = score.team_a > score.team_b

    return team_a_wins, score






class Team:
    def __init__(self, name='', rating='', nickname='',
                 games_list=None, section='', region=''):
        self.name = name
        self.rating = rating
        self.games_list = games_list
        self.nickname = nickname
        if not games_list:
            self.games_list = []
        else:
            self.games_list = games_list





class Game:
    def __init__(self, team_a=None, team_b=None, child_a=None, child_b=None,
                 score=None, played=False, winner=None, loser=None,
                 level=None, method='random', game_to=15,
                 rating_diff_to_victory_margin=None, p_a_offense=0.8):
        self.team_a = team_a
        self.team_b = team_b
        self.child_a = child_a
        self.child_b = child_b
        self.score = score
        self.played = played
        self.winner = winner
        self.loser = loser
        self.level = level
        self.method = method
        self.game_to = game_to
        self.rating_diff_to_victory_margin = rating_diff_to_victory_margin
        self.p_a_offense = p_a_offense


    def display_score(self):
        if self.level:
            print(f"{self.level}: {self.team_a.name} {self.score.team_a}-{self.score.team_b} {self.team_b.name}")
        else:
            print(f"{self.team_a.name} {self.score.team_a}-{self.score.team_b} {self.team_b.name}")

    def list_team_names(self):
        return [self.team_a.name, self.team_b.name]

    def play_game(self, method=None, game_to=None,
                  rating_diff_to_victory_margin=None,
                  p_a_offense=None):

        # If user doesn't specify the options here, set them to game defaults
        if not method:
            method=self.method
        if not game_to:
            game_to=self.game_to
        if not rating_diff_to_victory_margin:
            rating_diff_to_victory_margin=self.rating_diff_to_victory_margin
        if not p_a_offense:
            p_a_offense=self.p_a_offense

        # Check if game has been played
        if not self.played:
            # Check if there is a team_a.  If there is no team_a
            # then see if there is a play-in game.  If so, play it.
            # If not, then raise error because there is no one to play!
            if not self.team_a:
                if self.child_a:
                    # Check if game has been played
                    if not self.child_a.played:
                        # Play child_a game
                        self.child_a.play_game(method=method,
                                               rating_diff_to_victory_margin=rating_diff_to_victory_margin,
                                               p_a_offense=p_a_offense)

                    # Winner of child_a becomes team_a
                    self.team_a = self.child_a.winner
                else:
                    raise Exception("No team team_a or game child_a!")

            # Same for team_b
            if not self.team_b:
                if self.child_b:
                    # Check if game has been played
                    if not self.child_b.played:
                        # Play child_b game
                        self.child_b.play_game(method=method,
                                               rating_diff_to_victory_margin=rating_diff_to_victory_margin,
                                               p_a_offense=p_a_offense)

                    # Winner of child_b becomes team_b
                    self.team_b = self.child_b.winner
                else:
                    raise Exception("No team team_b or game child_b!")


            # Actually play game
            team_a_wins, score_here = simulate_game_outcome(self.team_a.rating,
                    self.team_b.rating,
                    rating_diff_to_victory_margin=rating_diff_to_victory_margin,
                    method=method, game_to=game_to,
                    p_a_offense=p_a_offense)

            self.score = score_here

            if team_a_wins:
                self.winner = self.team_a
                self.loser = self.team_b
            else:
                self.winner = self.team_b
                self.loser = self.team_a


            # if method=='A always wins':
            #     self.winner = self.team_a
            #     self.loser = self.team_b
            #     self.score = Score(15,round(14*random.random()))
            # elif method=='random':
            #     self.score = Score(round(15*random.random()), round(15*random.random()))
            #     if self.score.team_a >= self.score.team_b:
            #         self.winner = self.team_a
            #         self.loser = self.team_b
            #     else:
            #         self.winner = self.team_b
            #         self.loser = self.team_a
            # elif method=='double negative binomial':
            #     team_a_wins, score = simulate_game_outcome(self.team_a.rating, self.team_b.rating,
            #               rating_diff_to_victory_margin=mens_rating_diff_to_victory_margin,
            #               method='double negative binomial',
            #               game_to=game_to, p_a_offense=0.8)
            #     if team_a_wins:
            #         self.winner = self.team_a
            #         self.loser = self.team_b
            #     else:
            #         self.winner = self.team_b
            #         self.loser = self.team_a
            #     self.score = score
            #
            # else:
            #     raise Exception('Method not recognized!')


            self.played = True
            self.display_score()
            self.team_a.games_list.append(self)
            self.team_b.games_list.append(self)





class Tournament:
    def __init__(self, games_list=None, played=False):
        if games_list:
            self.games_list = games_list
        else:
            self.games_list = []
        self.played = played

    def play_games(self, method=None, rating_diff_to_victory_margin=None, p_a_offense=None):
        for game in self.games_list:
            if not method: # When no method provided in play_games, just use what was given in the game itself
                game.play_game(method=game.method, rating_diff_to_victory_margin=game.rating_diff_to_victory_margin, p_a_offense=game.p_a_offense)
            else:
                game.play_game(method=method, rating_diff_to_victory_margin=rating_diff_to_victory_margin, p_a_offense=p_a_offense)
        self.played = True

    def determine_placement(self, method='finals winner'):
        if self.played:
            if method=='finals winner':
                # Look for a team that won finals
                games_with_level_equal_finals = [game for game in self.games_list if game.level=='final']
                if len(games_with_level_equal_finals)==1:
                    return [(1, games_with_level_equal_finals[0].winner)]
                else:
                    raise Exception("Multiple teams won 'final' level game!")
            elif method=='round robin':
                # Pandas dataframe of each team
                df_teams = pd.DataFrame({"Team":self.teams_list,
                                         'Name':[team.name for team in self.teams_list]})

                # Data frame of each game
                df_games = pd.DataFrame([(game.team_a, game.team_b,
                                          game.team_a.name, game.team_b.name,
                                          game.score.team_a, game.score.team_b,
                                          game.winner, game.loser,
                                          game.winner.name, game.loser.name)
                                         for game in self.games_list],
                                        columns = ["Team A","Team B",
                                                   "Team A Name", "Team B Name",
                                                   "Team A Score","Team B Score",
                                                   "Winner","Loser",
                                                   "Winner Name", "Loser Name"])

                df_games_by_winner_name = df_games.groupby('Winner Name').count()

                #print(df_games['Winner Name'].value_counts())

                # Premilinary finish
                df_teams['Wins'] = df_teams.Name.apply(lambda x: len(df_games[df_games["Winner Name"]==x]))

                # Determine group for ties
                df_teams['Tie Group 1'] = -1
                first_groups_for_ties = df_teams[['Name','Wins']].groupby('Wins').agg(list).sort_index(ascending=False)
                for i in range(len(first_groups_for_ties)):
                    for team in first_groups_for_ties.Name.iloc[i]:
                        #print((i, team))
                        index_of_team_with_this_name = df_teams.index[df_teams.Name==team].tolist()
                        #print(index_of_team_with_this_name)
                        df_teams.loc[index_of_team_with_this_name, 'Tie Group 1'] = i

                # Break ties among first group by
                # (1) wins against tied opponents
                # (2) point diff against tied opponents
                # (3) NON-USAU random number

                df_teams['Wins Against Tie Group 1'] = 0
                df_teams['Point Diff Against Tie Group 1'] = 0
                df_teams['Random Number'] = 0
                for i in df_teams.index:
                    name_here = df_teams.loc[i, 'Name']
                    tie_group_number_here = df_teams.loc[i, 'Tie Group 1']
                    tie_group_here = df_teams[df_teams['Tie Group 1']==tie_group_number_here].Name.tolist()
                    tie_group_here.remove(name_here)
                    #print(tie_group_here)
                    df_teams.loc[i, 'Wins Against Tie Group 1'] = len(df_games[(df_games["Winner Name"]==name_here) & (df_games["Loser Name"].apply(lambda x: x in tie_group_here))])

                    points_when_team_A = sum(df_games[(df_games["Team A Name"]==name_here) &
                                                      (df_games["Team B Name"].apply(lambda x: x in tie_group_here))
                                                     ]["Team A Score"])

                    points_when_team_B = sum(df_games[(df_games["Team B Name"]==name_here) &
                                                      (df_games["Team A Name"].apply(lambda x: x in tie_group_here))
                                                     ]["Team B Score"])

                    opponent_points_when_team_A = sum(df_games[(df_games["Team A Name"]==name_here) &
                                                      (df_games["Team B Name"].apply(lambda x: x in tie_group_here))
                                                     ]["Team B Score"])

                    opponent_points_when_team_B = sum(df_games[(df_games["Team B Name"]==name_here) &
                                                      (df_games["Team A Name"].apply(lambda x: x in tie_group_here))
                                                     ]["Team A Score"])

                    points_my_team_scored_against_tie_group_opponents = points_when_team_A + points_when_team_B

                    points_my_tie_group_opponents_scored_against_me = opponent_points_when_team_A + opponent_points_when_team_B

                    df_teams.loc[i,'Point Diff Against Tie Group 1'] = points_my_team_scored_against_tie_group_opponents - \
                                                                       points_my_tie_group_opponents_scored_against_me

                    df_teams.loc[i, 'Random Number'] = random.random()

                df_teams_sorted = df_teams.sort_values(['Wins', 'Wins Against Tie Group 1', 'Point Diff Against Tie Group 1', 'Random Number'], ascending=False)

                finish_list = df_teams_sorted['Team'].tolist()

                df_finish = df_teams_sorted.reset_index(drop=True)
                df_finish['Finish'] = df_finish.index + 1

                #print(df_finish)

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
        games_list = [[Game(teams_list[i], teams_list[j]) for j in range(i)]for i in range(num_teams)]
        games_list = sum(games_list, [])

        Tournament.__init__(self, games_list=games_list, played=played)

    def determine_placement(self):
        return Tournament.determine_placement(self, method='round robin')






def play_eight_team_single_elimination_bracket(teams_list, num_bids=1, method='random',
                                               rating_diff_to_victory_margin=None,
                                               p_a_offense=None):
    # Play a bracket with 8 teams, one winner, single elim.
    q1 = Game(teams_list[0],teams_list[7], level='quarter')
    q2 = Game(teams_list[1],teams_list[6], level='quarter')
    q3 = Game(teams_list[2],teams_list[5], level='quarter')
    q4 = Game(teams_list[3],teams_list[4], level='quarter')
    s1 = Game(child_a=q1, child_b=q4, level='semi')
    s2 = Game(child_a=q2, child_b=q3, level='semi')
    f = Game(child_a=s1, child_b=s2, level='final')

    tourney = Tournament(games_list=[q1,q2,q3,q4,s1,s2,f])

    tourney.play_games(method=method,
                       rating_diff_to_victory_margin=rating_diff_to_victory_margin,
                       p_a_offense=p_a_offense)

    return tourney.determine_placement()





def play_twelve_team_tournament(teams_list, num_bids, method='random',
                                rating_diff_to_victory_margin=None,
                                p_a_offense=None):
    # Assumes teams_list is in seed order!
    # Currently in two pools of six format
    # then single elimnation 8 team bracket.

    # NEEDS TO BE UPDATED WITH DESIRED FORMATS!

    if num_bids == 1:
        #
        # Pool play
        #
        a_seeds = [1, 3, 6, 7, 10, 12]
        b_seeds = [2, 4, 5, 8,  9, 11]

        pool_a_teams = [teams_list[i-1] for i in a_seeds]
        pool_b_teams = [teams_list[i-1] for i in b_seeds]

        pool_a = RoundRobinTournament(pool_a_teams)
        pool_b = RoundRobinTournament(pool_b_teams)

        print("\nPool A")
        pool_a.play_games(method=method,
                          rating_diff_to_victory_margin=rating_diff_to_victory_margin,
                          p_a_offense=p_a_offense)
        print("\nPool B")
        pool_b.play_games(method=method,
                          rating_diff_to_victory_margin=rating_diff_to_victory_margin,
                          p_a_offense=p_a_offense)
        pool_a_finish = pool_a.determine_placement()
        pool_b_finish = pool_b.determine_placement()

        #
        # Bracket
        #
        remaining_teams = [
            pool_a_finish.loc[0,'Team'],
            pool_b_finish.loc[0,'Team'],
            pool_a_finish.loc[1,'Team'],
            pool_b_finish.loc[1,'Team'],
            pool_b_finish.loc[2,'Team'],
            pool_a_finish.loc[2,'Team'],
            pool_a_finish.loc[3,'Team'],
            pool_b_finish.loc[3,'Team']
        ]


        print("\n8-team bracket")
        placement = play_eight_team_single_elimination_bracket(remaining_teams, num_bids=1, method=method,
                                                               rating_diff_to_victory_margin=rating_diff_to_victory_margin,
                                                               p_a_offense=p_a_offense)

        return placement

    else:
        raise Exception("Can't do num_bids={num_bids} right now!")




def import_teams(ranking_html_file):
    # From a USAU ranking page html file
    # read the html in as a dataframe and save the info
    # about the teams, one row for each team.
    result = pd.read_html(ranking_html_file)
    df = result[0]

    # remove last row because it contains junk
    df = df.drop(index=len(df)-1)

    # Convert numeric columns to from string/object to correct type
    cols = ['Rank', 'Power Rating', 'Wins', 'Losses']
    df[cols] = df[cols].apply(pd.to_numeric)

    return df




def get_top_teams_from_region(df_rankings, region, n=12, division='Division I'):
    # Based on either the mens or women's df_rankings dataframe,
    # grab the top n teams from the region by USAU ranking.
    sorted_teams_from_the_region = \
        df_rankings[(df_rankings['College Region']==region) &
                    (df_rankings['Competition Division']==division)].sort_values(['Rank','Power Rating'], ascending=[True, False])

    return sorted_teams_from_the_region.head(n)





def create_teams_from_dataframe(df_teams):
    # Create teams_list from teams data frame
    # output is a list of Team objects representing
    # the teams in the dataframe.
    # Captures their name, section, region, and power rating
    teams_list = []
    for i in df_teams.index:
        team_here = Team(name=df_teams.loc[i, 'Team'],
                         rating=df_teams.loc[i, 'Power Rating'],
                         section=df_teams.loc[i, 'College Conference'],
                         region=df_teams.loc[i, 'College Region'])
        teams_list.append(team_here)

    return teams_list











def fit_logreg_to_win_loss_outcomes(X_train, y_train_class):
    """
    Returns a logistic regression model fit to outcome (W/L) vs rating diff.
    """
    logreg = LogisticRegression(fit_intercept=False, solver='lbfgs')
    logreg.fit(X_train['RatingDiff'].values.reshape(-1, 1),
               y_train_class['GameTo15VictoryMargin'].values.ravel())
    return logreg





def logistic_victory_margin(x, k, game_to=15):
    """
    Form for a logistic function with values between -15 and 15
    and has value = 0 at x = 0.

    Used for fitting victory margin vs rating difference.
    """

    return 2*game_to/(1. + np.exp(-k*x)) - game_to





def fit_logistic_to_victory_margin(X, y):
    """
    Fit logistic to victory margin vs rating difference.

    Assumes X, y and come from train_test_split.
    """

    xdata = X['RatingDiff'].values.ravel()
    ydata = y['GameTo15VictoryMargin'].values.ravel()
    popt, pcov = curve_fit(logistic_victory_margin, xdata, ydata)
    print(*popt)
    return lambda x: logistic_victory_margin(x, *popt)





def convert_ratings_to_expected_game_score(team_a_rating, team_b_rating, game_to,
                                          rating_diff_to_victory_margin):
    """
    Take USAU Power Ratings of two teams and get expected game_score
    """
    if team_a_rating >= team_b_rating:
        team_a_score = game_to
        team_b_score = team_a_score - rating_diff_to_victory_margin(team_a_rating-team_b_rating)
    else:
        team_b_score = game_to
        team_a_score = team_b_score - rating_diff_to_victory_margin(team_b_rating-team_a_rating)
    score = Score(team_a=team_a_score, team_b=team_b_score)
    return score





def determine_optimal_value_of_p_a_offense(X_train, y_train,
                                           n_simulations=1000,
                                           possible_pa_values=np.arange(0.70,.95,0.05)):
    """
    Returns the optimal probability p_a_offense to use
    for the higher rated team.

    Run time is O(n_simulations * possible_pa_values * rating_diff_samples).
    So, it can take minutes to run for n_simulations = 10,000. That's why
    the default value is set to 1,000.
    """
    y_train_class = y_train > 0

    # Sample at X_train values
    rating_diff_samples = X_train.values.ravel()

    n_possible_pa_values = len(possible_pa_values)
    n_rating_diff_samples = len(rating_diff_samples)

    # Get the empirical win_loss fit and victory margin fit
    logreg = fit_logreg_to_win_loss_outcomes(X_train, y_train_class) # win/loss
    rating_diff_to_victory_margin = fit_logistic_to_victory_margin(X_train, y_train) # margin

    # Do simulations and calculate error
    team_a_rating = 2500 # Arbitrary, since only difference matters
    win_prob_array = np.zeros((n_possible_pa_values, n_rating_diff_samples))
    rmse = np.zeros(n_possible_pa_values)
    X_sample = rating_diff_samples.reshape(-1, 1)
    y_sample_predict = logreg.predict_proba(X_sample)[:,1]

    # Calculate error for each p_a_offense value
    for i, p_a_offense in enumerate(possible_pa_values):
        for j, rating_diff in enumerate(X_train['RatingDiff'].values):

            team_b_rating = team_a_rating - rating_diff

            n_team_a_wins = 0
            n_team_a_losses = 0
            for _ in range(n_simulations):
                team_a_wins, _ = simulate_game_outcome(team_a_rating, team_b_rating,
                                                       rating_diff_to_victory_margin=rating_diff_to_victory_margin,
                                                       method='double negative binomial',
                                                       game_to=game_to,
                                                       p_a_offense=p_a_offense)
                if team_a_wins:
                    n_team_a_wins += 1
                else:
                    n_team_a_losses += 1

            win_prob_array[i,j] = n_team_a_wins*1./(n_team_a_wins + n_team_a_losses)
        rmse[i] = np.sqrt(np.mean((win_prob_array[i,:]-y_sample_predict)**2))

    optimal_p_a_offense = possible_pa_values[np.argmin(rmse)]

    #print(f'optimal p_a_offense: {optimal_p_a_offense:.3}')

    return optimal_p_a_offense





def get_rmse_outcome_prob(X_test, y_test, p_a_offense, rating_diff_to_victory_margin,
                          n_simulations=1000):
    """
    Get the RMSE when an existing optimal p_a_offense and rating_diff_to_victory_margin
    have already been fit.
    """
    logreg = fit_logreg_to_win_loss_outcomes(X_test, y_test>0) # Calculate empirical "Truth" for test set

    X_sample = X_test.values.reshape(-1, 1)
    y_sample_predict = logreg.predict_proba(X_sample)[:,1]
    n_samples = len(X_sample)

    x_line = np.arange(0,2700,10)
    y_line = logreg.predict_proba(x_line.reshape(-1, 1))[:,1]

    team_a_rating = 2500 # Arbitrary, only difference matters

    win_prob_array = np.zeros(n_samples)
    for j, rating_diff in enumerate(X_sample):

        team_b_rating = team_a_rating - rating_diff

        n_team_a_wins = 0
        n_team_a_losses = 0
        for _ in range(n_simulations):
            team_a_wins, _ = simulate_game_outcome(team_a_rating, team_b_rating,
                                                   rating_diff_to_victory_margin=rating_diff_to_victory_margin,
                                                   method='double negative binomial',
                                                   game_to=game_to,
                                                   p_a_offense=p_a_offense)
            if team_a_wins:
                n_team_a_wins += 1
            else:
                n_team_a_losses += 1

        win_prob_array[j] = n_team_a_wins*1./(n_team_a_wins + n_team_a_losses)

    rmse = np.sqrt(np.mean((win_prob_array-y_sample_predict)**2))

    fig = plt.figure(figsize=(6,4.5), dpi=200)
    fig.patch.set_facecolor('white')
    plt.plot([0, 1000], [1, 1], 'gray', linewidth=0.5)
    plt.plot([0, 1000], [0, 0], 'gray', linewidth=0.5)
    s1 = plt.scatter(X_sample, y_test>0, alpha=0.3, label='Test Data')
    p1 = plt.plot(x_line, y_line, alpha=0.7, linewidth=2, label='Win Prob. inferred from Test Data')
    s2 = plt.scatter(X_sample, win_prob_array, alpha=0.3, label='Model Predicted Win Prob.')
    leg = plt.legend(loc='best', bbox_to_anchor=(0.1, 0.2, 0.9, 0.2))
    plt.title('Evaluation of Predicted Win Probability')
    plt.xlabel('Rating Difference')
    plt.ylabel('Probability of Winning')
    plt.xlim([0, 1000])
    #plt.ylim(bottom=.45)
    plt.text(700, 0.65, f'RMSE: {rmse:.2}')
    plt.show()

    return rmse






def evaluate_win_probabilities(X_train, y_train, y_train_class,
                               X_test, y_test, y_test_class,
                               possible_pa_values=np.arange(0.6,.85,0.025)):
    """
    Fit model to training data and test it against testing data
    """

    # Determine optimal p_a_offense value
    optimal_p_a_offense = \
            determine_optimal_value_of_p_a_offense(X_train,
                                                   y_train,
                                                   n_simulations=1000,
                                                   possible_pa_values=possible_pa_values)

    # Fit logistic function to victory margin data
    log_victory_margin_here = fit_logistic_to_victory_margin(X_train, y_train)

    # How well does it do on the test set?
    rmse = get_rmse_outcome_prob(X_test, y_test, optimal_p_a_offense,
                                 log_victory_margin_here, n_simulations=1000)
    print(f'RMSE between simulated and empirical probabilities: {rmse:.2}')
    print(f'Optimal p_a_offense: {optimal_p_a_offense:0.3}')







def fit_final_model(X, y, y_class, possible_pa_values=np.arange(0.6,.85,0.025)):
    """
    Fit model to full data and
    """

    # Fit logistic model to victory margin
    # Note: this is *regression* NOT *logistic regression*
    log_victory_margin_here = fit_logistic_to_victory_margin(X, y)

    # Determine optimal p_a_offense value
    optimal_p_a_offense = \
            determine_optimal_value_of_p_a_offense(X, y ,n_simulations=200,
                                                   possible_pa_values=possible_pa_values)

    #print(f'Optimal p_a_offense: {optimal_p_a_offense:0.3}')

    return optimal_p_a_offense, log_victory_margin_here







def main():
    # Get 2019 USAU post-regionals ratings for calculating parameters
    #
    # Read in FullTeamRankings saved from USAU Ultimate Rankings Page 5/16/2019
    # link: https://play.usaultimate.org/teams/events/team_rankings/?RankSet=College-Women
    #
    # Couldn't get all teams directly, so just clicked show all and then saved as .html locally.

    womens_ranking_html = r'Rankings/FullTeamRankings_women_post-regionals_2019.htm'
    mens_ranking_html   = r'Rankings/FullTeamRankings_men_post-regionals_2019.htm'

    # Import teams
    df_women = import_teams(womens_ranking_html)
    df_men = import_teams(mens_ranking_html)

    print(df_women.head())


    # Load scraped game data
    #
    # For all Top 50 teams (as of final regular season ranking), load
    # all of the their 2019 Sectionals and Regionals game data.
    #
    # Data has been pre-scraped using Scrape_Ultimate_Games

    womens_full_results = pd.read_csv('Results/results_womens_games_rank1-50_2019-04-04_to_2019-05-23.csv')
    mens_full_results = pd.read_csv('Results/results_mens_games_rank1-50_2019-04-04_to_2019-05-23.csv')

    # Drop missing values
    womens_full_results.dropna(inplace=True)
    mens_full_results.dropna(inplace=True)


    # Gather data into right format to train model
    womens_X = womens_full_results[['RatingDiff']]
    womens_y = womens_full_results[['GameTo15VictoryMargin']]
    womens_y_class = womens_y>=0 # convert to bool

    mens_X = mens_full_results[['RatingDiff']]
    mens_y = mens_full_results[['GameTo15VictoryMargin']]
    mens_y_class = mens_y>=0 # convert to bool


    # Fit final model to 2019 Sectionals and Regionals data

    FIT_DATA = False # it takes a while, can just skip and load
    if FIT_DATA:
        # Womens
        womens_optimal_p_a_offense, womens_rating_diff_to_victory_margin = \
                fit_final_model(womens_X, womens_y, womens_y_class)

        print(f'Women\'s optimal p_a_offense: {womens_optimal_p_a_offense:0.3}')

        # Mens
        mens_optimal_p_a_offense, mens_rating_diff_to_victory_margin = \
                fit_final_model(mens_X, mens_y, mens_y_class)

        print(f'Men\'s optimal p_a_offense: {mens_optimal_p_a_offense:0.3}')

    else:
        # Load known parameters
        womens_optimal_p_a_offense = 0.65
        mens_optimal_p_a_offense = 0.8

        womens_k = 0.0022838954964262735
        mens_k   = 0.002138514393927596

        womens_rating_diff_to_victory_margin = \
            lambda x: logistic_victory_margin(x, womens_k)
        mens_rating_diff_to_victory_margin = \
            lambda x: logistic_victory_margin(x, mens_k)










if __name__ == "__main__":
    main()
