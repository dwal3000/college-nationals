# test_ultimate.py
#
# Right now this has simple tests.  In the future, this
# could hold proper unit tests.

import pandas as pd
import ultimate
from ultimate import (
    Team,
    Game,
    Tournament,
    utils
)
from ultimate.utils import get_default_parameters

from ultimate.tournament import (
    play_eight_team_single_elimination_bracket,
    play_twelve_team_tournament,
)
from ultimate.team import (
    import_teams,
    get_top_teams_from_region,
    create_teams_from_dataframe,
)


# Get parameters for men's division
mens_p_a_offense, mens_k, mens_rating_diff_to_victory_margin, game_to = get_default_parameters(
    "men"
)

print(f"mens_p_a_offense: {mens_p_a_offense}, mens_k: {mens_k}, game_to: {game_to}")

p_a_offense = 0.7

print(f"Using p_a_offense = {p_a_offense}")


#
# Tests for Team class
#
ucla = Team(name="UCLA", rating=2200, nickname="Smaug")
ucsb = Team(name="UCSB", rating=2100, nickname="Black Tide")
ucsd = Team(name="UCSD", rating=2000, nickname="Air Squids")
cal = Team(name="Cal", rating=1900, nickname="UGMO")
print(ucla.name, ucla.nickname, ucla.rating, ucla.games_list)
print(ucsb.name, ucsb.nickname, ucsb.rating, ucsb.games_list)
print(ucsd.name, ucsd.nickname, ucsd.rating, ucsd.games_list)
print(cal.name, cal.nickname, cal.rating, cal.games_list)


#
# Tests for Game class
#
ucla = Team(name="UCLA", rating=2200, nickname="Smaug", games_list=[])
ucsb = Team(name="UCSB", rating=2000, nickname="Black Tide")
ucsd = Team(name="UCSD", rating=1700, nickname="Air Squids")
cal = Team(name="Cal", rating=1500, nickname="UGMO")

# Game 0
print("\nGame 0 (method='random')")
ucla_vs_ucsb = Game(ucla, ucsb)
ucla_vs_ucsb.play_game(method="random")
print("Score *should* be only 15-13 or 13-15.")


# Game 1
print("\nGame 1")
ucla_vs_ucsb = Game(ucla, ucsb)
ucla_vs_ucsb.play_game(
    method="double negative binomial",
    rating_diff_to_victory_margin=mens_rating_diff_to_victory_margin,
    p_a_offense=p_a_offense,
)


# Game 2
print("\nGame 2")
winner_vs_ucsd = Game(None, ucsd, child_a=ucla_vs_ucsb)

winner_vs_ucsd.play_game(
    method="double negative binomial",
    rating_diff_to_victory_margin=mens_rating_diff_to_victory_margin,
    p_a_offense=p_a_offense,
)


# Tournament 0
print("\nTournament 0")
semi1 = Game(ucla, ucsb, level="semi")
semi2 = Game(cal, ucsd, level="semi")
finals = Game(None, None, semi1, semi2, level="final")

finals.play_game(
    method="double negative binomial",
    rating_diff_to_victory_margin=mens_rating_diff_to_victory_margin,
    p_a_offense=p_a_offense,
)


# Tests for playing 8 team bracket
print("\nEight team bracket")
ucla = Team(name="UCLA", rating=2200, nickname="Smaug", games_list=[])
ucsb = Team(name="UCSB", rating=2100, nickname="Black Tide")
ucsd = Team(name="UCSD", rating=2000, nickname="Air Squids")
cal = Team(name="Cal", rating=1900, nickname="UGMO")
uw = Team(name="UW", rating=1800, nickname="Sundodgers")
ore = Team(name="Oregon", rating=1700, nickname="Ego")
whit = Team(name="Whitman", rating=1600, nickname="Sweets")
slo = Team(name="CalPolySLO", rating=1500, nickname="Slocore")

teams_list = [ucla, ucsb, ucsd, cal, uw, ore, whit, slo]

placement = play_eight_team_single_elimination_bracket(
    teams_list,
    method="double negative binomial",
    rating_diff_to_victory_margin=mens_rating_diff_to_victory_margin,
    p_a_offense=p_a_offense,
)

print(placement[0][1].name)


# Tests for playing 12-team 1-bid tournament
print("\n\nTest for playing 12-team 1-bid")
uw = Team(name="UW", rating=2400, nickname="Sundodgers")
ore = Team(name="Oregon", rating=2300, nickname="Ego")
slo = Team(name="CalPolySLO", rating=2250, nickname="Slocore")
ucla = Team(name="UCLA", rating=2200, nickname="Smaug", games_list=[])
stan = Team(name="Stanford", rating=2150, nickname="Bloodthirsty")
ucsb = Team(name="UCSB", rating=2100, nickname="Black Tide")
ucsd = Team(name="UCSD", rating=2000, nickname="Air Squids")
cal = Team(name="Cal", rating=1900, nickname="UGMO")
whit = Team(name="Whitman", rating=1600, nickname="Sweets")
sdsu = Team(name="SDSU", rating=1400, nickname="")
orst = Team(name="Oregon State", rating=1300, nickname="?")
wwu = Team(name="Western Washington", rating=1200, nickname="Dirt")

teams_list = [uw, ore, slo, ucla, stan, ucsb, ucsd, cal, whit, sdsu, orst, wwu]

placement = play_twelve_team_tournament(
    teams_list,
    num_bids=1,
    method="double negative binomial",
    rating_diff_to_victory_margin=mens_rating_diff_to_victory_margin,
    p_a_offense=p_a_offense,
)

print(placement[0][1].name)


# Import rankings and regions and sections and ratings
# Get USAU Ratings and rankings

womens_ranking_html = r"Rankings/USAU_team_rankings.women.2020-03-11.html"
mens_ranking_html = r"Rankings/USAU_team_rankings.men.2020-03-11.html"

# Use pandas html reader to extract dataframe
result = pd.read_html(womens_ranking_html)
df_women = result[0]

result = pd.read_html(mens_ranking_html)
df_men = result[0]

# Last row contains garbage, so remove it.
df_women = df_women.drop(index=len(df_women) - 1)
df_men = df_men.drop(index=len(df_men) - 1)

# Convert numeric columns to from string/object to correct type
cols = ["Rank", "Power Rating", "Wins", "Losses"]
df_women[cols] = df_women[cols].apply(pd.to_numeric)
df_men[cols] = df_men[cols].apply(pd.to_numeric)


def simulate_regionals(
    df,
    region,
    division="Division I",
    num_participants=12,
    num_bids=1,
    method="double negative binomial",
    rating_diff_to_victory_margin=mens_rating_diff_to_victory_margin,
    p_a_offense=p_a_offense,
):
    df_teams = get_top_teams_from_region(
        df, region, n=num_participants, division=division
    )
    teams_list = create_teams_from_dataframe(df_teams)
    print(region)
    print(f"Teams list: {teams_list}")
    if num_participants == 12:
        placement = play_twelve_team_tournament(
            teams_list,
            num_bids=num_bids,
            method=method,
            rating_diff_to_victory_margin=rating_diff_to_victory_margin,
            p_a_offense=p_a_offense,
        )
    else:
        raise Exception(
            "Sorry!  Nothing here yet besides a twelve team single bid bracket!"
        )

    return placement


#
# Simulate Men's Northwest Regionals
#

print("\n\nNorthwest Regionals (Men)\n")
# Get top men's team from the northwest
df_teams = get_top_teams_from_region(df_men, "Northwest", n=12, division="Division I")
teams_list = create_teams_from_dataframe(df_teams)
placement = play_twelve_team_tournament(
    teams_list,
    num_bids=1,
    method="double negative binomial",
    rating_diff_to_victory_margin=mens_rating_diff_to_victory_margin,
    p_a_offense=p_a_offense,
)
print(placement[0][1].name)


#
# Simulate every men's regionals
#

regions = sorted(list(set(df_men["College Region"].dropna().to_list())))

for region in regions:
    print(f"\n\n{region}\n")
    placement = simulate_regionals(
        df_men,
        region,
        division="Division I",
        num_participants=12,
        num_bids=1,
        method="double negative binomial",
        rating_diff_to_victory_margin=mens_rating_diff_to_victory_margin,
        p_a_offense=p_a_offense,
    )

    print("\n", placement[0][1].name)
