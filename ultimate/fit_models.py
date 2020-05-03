# fit_models.py
# Daniel Walton
# 3/27/2020

# forked by Alex Trahey
# 3/29/2020


import re

import matplotlib as mpl
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.optimize import curve_fit
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from .game import Game
from .utils import logistic_victory_margin

#
# Default parameters (from 2019 Sectionals/Regionals)
#


def fit_logreg_to_win_loss_outcomes(X_train, y_train_class):
    """
    Returns a logistic regression model fit to outcome (W/L) vs rating diff.
    """
    logreg = LogisticRegression(fit_intercept=False, solver="lbfgs")
    logreg.fit(
        X_train["RatingDiff"].values.reshape(-1, 1),
        y_train_class["GameTo15VictoryMargin"].values.ravel(),
    )
    return logreg


def fit_logistic_to_victory_margin(X, y):
    """
    Fit logistic to victory margin vs rating difference.

    Assumes X, y and come from train_test_split.
    """

    xdata = X["RatingDiff"].values.ravel()
    ydata = y["GameTo15VictoryMargin"].values.ravel()
    popt, pcov = curve_fit(logistic_victory_margin, xdata, ydata)
    print(*popt)
    return lambda x: logistic_victory_margin(x, *popt)


def determine_optimal_value_of_p_a_offense(
    X_train, y_train, n_simulations=1000, possible_pa_values=np.arange(0.70, 0.95, 0.05)
):
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
    logreg = fit_logreg_to_win_loss_outcomes(X_train, y_train_class)  # win/loss
    rating_diff_to_victory_margin = fit_logistic_to_victory_margin(
        X_train, y_train
    )  # margin

    # Do simulations and calculate error
    team_a_rating = 2500  # Arbitrary, since only difference matters
    win_prob_array = np.zeros((n_possible_pa_values, n_rating_diff_samples))
    rmse = np.zeros(n_possible_pa_values)
    X_sample = rating_diff_samples.reshape(-1, 1)
    y_sample_predict = logreg.predict_proba(X_sample)[:, 1]

    # Calculate error for each p_a_offense value
    for i, p_a_offense in enumerate(possible_pa_values):
        for j, rating_diff in enumerate(X_train["RatingDiff"].values):

            team_b_rating = team_a_rating - rating_diff

            n_team_a_wins = 0
            n_team_a_losses = 0
            for _ in range(n_simulations):
                team_a_wins, _ = Game.simulate_game_from_ratings(
                    team_a_rating,
                    team_b_rating,
                    rating_diff_to_victory_margin=rating_diff_to_victory_margin,
                    method="double negative binomial",
                    game_to=game_to,
                    p_a_offense=p_a_offense,
                )
                if team_a_wins:
                    n_team_a_wins += 1
                else:
                    n_team_a_losses += 1

            win_prob_array[i, j] = (
                n_team_a_wins * 1.0 / (n_team_a_wins + n_team_a_losses)
            )
        rmse[i] = np.sqrt(np.mean((win_prob_array[i, :] - y_sample_predict) ** 2))

    optimal_p_a_offense = possible_pa_values[np.argmin(rmse)]

    # print(f'optimal p_a_offense: {optimal_p_a_offense:.3}')

    return optimal_p_a_offense


def get_rmse_outcome_prob(
    X_test, y_test, p_a_offense, rating_diff_to_victory_margin, n_simulations=1000
):
    """
    Get the RMSE when an existing optimal p_a_offense and rating_diff_to_victory_margin
    have already been fit.
    """
    logreg = fit_logreg_to_win_loss_outcomes(
        X_test, y_test > 0
    )  # Calculate empirical "Truth" for test set

    X_sample = X_test.values.reshape(-1, 1)
    y_sample_predict = logreg.predict_proba(X_sample)[:, 1]
    n_samples = len(X_sample)

    x_line = np.arange(0, 2700, 10)
    y_line = logreg.predict_proba(x_line.reshape(-1, 1))[:, 1]

    team_a_rating = 2500  # Arbitrary, only difference matters

    win_prob_array = np.zeros(n_samples)
    for j, rating_diff in enumerate(X_sample):

        team_b_rating = team_a_rating - rating_diff

        n_team_a_wins = 0
        n_team_a_losses = 0
        for _ in range(n_simulations):
            team_a_wins, _ = Game.simulate_game_from_ratings(
                team_a_rating,
                team_b_rating,
                rating_diff_to_victory_margin=rating_diff_to_victory_margin,
                method="double negative binomial",
                game_to=game_to,
                p_a_offense=p_a_offense,
            )
            if team_a_wins:
                n_team_a_wins += 1
            else:
                n_team_a_losses += 1

        win_prob_array[j] = n_team_a_wins * 1.0 / (n_team_a_wins + n_team_a_losses)

    rmse = np.sqrt(np.mean((win_prob_array - y_sample_predict) ** 2))

    fig = plt.figure(figsize=(6, 4.5), dpi=200)
    fig.patch.set_facecolor("white")
    plt.plot([0, 1000], [1, 1], "gray", linewidth=0.5)
    plt.plot([0, 1000], [0, 0], "gray", linewidth=0.5)
    s1 = plt.scatter(X_sample, y_test > 0, alpha=0.3, label="Test Data")
    p1 = plt.plot(
        x_line,
        y_line,
        alpha=0.7,
        linewidth=2,
        label="Win Prob. inferred from Test Data",
    )
    s2 = plt.scatter(
        X_sample, win_prob_array, alpha=0.3, label="Model Predicted Win Prob."
    )
    leg = plt.legend(loc="best", bbox_to_anchor=(0.1, 0.2, 0.9, 0.2))
    plt.title("Evaluation of Predicted Win Probability")
    plt.xlabel("Rating Difference")
    plt.ylabel("Probability of Winning")
    plt.xlim([0, 1000])
    # plt.ylim(bottom=.45)
    plt.text(700, 0.65, f"RMSE: {rmse:.2}")
    plt.show()

    return rmse


def evaluate_win_probabilities(
    X_train,
    y_train,
    y_train_class,
    X_test,
    y_test,
    y_test_class,
    possible_pa_values=np.arange(0.6, 0.85, 0.025),
):
    """
    Fit model to training data and test it against testing data
    """

    # Determine optimal p_a_offense value
    optimal_p_a_offense = determine_optimal_value_of_p_a_offense(
        X_train, y_train, n_simulations=1000, possible_pa_values=possible_pa_values
    )

    # Fit logistic function to victory margin data
    log_victory_margin_here = fit_logistic_to_victory_margin(X_train, y_train)

    # How well does it do on the test set?
    rmse = get_rmse_outcome_prob(
        X_test, y_test, optimal_p_a_offense, log_victory_margin_here, n_simulations=1000
    )
    print(f"RMSE between simulated and empirical probabilities: {rmse:.2}")
    print(f"Optimal p_a_offense: {optimal_p_a_offense:0.3}")


def fit_final_model(X, y, y_class, possible_pa_values=np.arange(0.6, 0.85, 0.025)):
    """
    Fit model to full data and
    """

    # Fit logistic model to victory margin
    # Note: this is *regression* NOT *logistic regression*
    log_victory_margin_here = fit_logistic_to_victory_margin(X, y)

    # Determine optimal p_a_offense value
    optimal_p_a_offense = determine_optimal_value_of_p_a_offense(
        X, y, n_simulations=200, possible_pa_values=possible_pa_values
    )

    # print(f'Optimal p_a_offense: {optimal_p_a_offense:0.3}')

    return optimal_p_a_offense, log_victory_margin_here


def main():
    # Get 2019 USAU post-regionals ratings for calculating parameters
    #
    # Read in FullTeamRankings saved from USAU Ultimate Rankings Page 5/16/2019
    # link: https://play.usaultimate.org/teams/events/team_rankings/?RankSet=College-Women
    #
    # Couldn't get all teams directly, so just clicked show all and then saved as .html locally.

    womens_ranking_html = r"../Rankings/FullTeamRankings_women_post-regionals_2019.htm"
    mens_ranking_html = r"../Rankings/FullTeamRankings_men_post-regionals_2019.htm"

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

    womens_full_results = pd.read_csv(
        "../Results/results_womens_games_rank1-50_2019-04-04_to_2019-05-23.csv"
    )
    mens_full_results = pd.read_csv(
        "../Results/results_mens_games_rank1-50_2019-04-04_to_2019-05-23.csv"
    )

    # Drop missing values
    womens_full_results.dropna(inplace=True)
    mens_full_results.dropna(inplace=True)

    # Gather data into right format to train model
    womens_X = womens_full_results[["RatingDiff"]]
    womens_y = womens_full_results[["GameTo15VictoryMargin"]]
    womens_y_class = womens_y >= 0  # convert to bool

    mens_X = mens_full_results[["RatingDiff"]]
    mens_y = mens_full_results[["GameTo15VictoryMargin"]]
    mens_y_class = mens_y >= 0  # convert to bool

    # Fit final model to 2019 Sectionals and Regionals data

    FIT_DATA = False  # it takes a while, can just skip and load
    if FIT_DATA:
        # Womens
        womens_optimal_p_a_offense, womens_rating_diff_to_victory_margin = fit_final_model(
            womens_X, womens_y, womens_y_class
        )

        print(f"Women's optimal p_a_offense: {womens_optimal_p_a_offense:0.3}")

        # Mens
        mens_optimal_p_a_offense, mens_rating_diff_to_victory_margin = fit_final_model(
            mens_X, mens_y, mens_y_class
        )

        print(f"Men's optimal p_a_offense: {mens_optimal_p_a_offense:0.3}")

    else:
        # Load known parameters
        womens_optimal_p_a_offense = 0.65
        mens_optimal_p_a_offense = 0.8

        womens_k = 0.0022838954964262735
        mens_k = 0.002138514393927596

        womens_rating_diff_to_victory_margin = lambda x: logistic_victory_margin(
            x, womens_k
        )
        mens_rating_diff_to_victory_margin = lambda x: logistic_victory_margin(
            x, mens_k
        )


if __name__ == "__main__":
    main()
