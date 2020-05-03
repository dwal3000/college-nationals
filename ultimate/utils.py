import numpy as np


def get_default_parameters(division):
    womens_optimal_p_a_offense = 0.65
    mens_optimal_p_a_offense = 0.7

    womens_k = 0.0022838954964262735
    mens_k = 0.002138514393927596

    womens_rating_diff_to_victory_margin = lambda x: logistic_victory_margin(x, womens_k)
    mens_rating_diff_to_victory_margin = lambda x: logistic_victory_margin(x, mens_k)

    # Set standard game length
    game_to = 15

    if division in ["men", "mens"]:
        return (
            mens_optimal_p_a_offense,
            mens_k,
            mens_rating_diff_to_victory_margin,
            game_to,
        )
    elif division in ["women", "womens"]:
        return (
            womens_optimal_p_a_offense,
            womens_k,
            womens_rating_diff_to_victory_margin,
            game_to,
        )
    else:
        raise Exception("Can't load parameters: division not recognized!")


def logistic_victory_margin(x, k, game_to=15):
    """
    Form for a logistic function with values between -15 and 15
    and has value = 0 at x = 0.

    Used for fitting victory margin vs rating difference.
    """

    return 2 * game_to / (1.0 + np.exp(-k * x)) - game_to
