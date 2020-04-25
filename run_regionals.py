import pandas as pd
import numpy as np

import ultimate
from ultimate import Team, Game, utils, tournament

mens_adjustments = {"Atlantic Coast": 0, "New England": 0}
mens_bid_path = "./Rankings/2019CollegeMensDivisionBidAllocation.htm"
womens_bid_path = "./Rankings/2019CollegeWomensDivisionBidAllocation.htm"
womens_ranking_html = r"Rankings/USAU_team_rankings.women.2020-03-11.html"
mens_ranking_html = r"Rankings/USAU_team_rankings.men.2020-03-11.html"
custom_ranks_path = "./Rankings/2020_04_24_USAU Human Ratings.xlsx"

four_pools_of_three_seeds = {
    "pool_a": [1, 8, 9],
    "pool_b": [2, 7, 10],
    "pool_c": [3, 6, 11],
    "pool_d": [4, 5, 12],
}

# Table 16.1.2
four_pools_of_four_seeds = {
    "pool_a": [1, 8, 12, 16],
    "pool_b": [2, 7, 11, 15],
    "pool_c": [3, 6, 10, 14],
    "pool_d": [4, 5, 9, 13],
}

two_pools_of_four_seeds = {"pool_a": [1, 4, 6, 7], "pool_b": [2, 3, 5, 8]}

two_pools_of_five_seeds = {"pool_a": [1, 3, 6, 8, 9], "pool_b": [2, 4, 5, 7, 10]}
two_pools_of_six_seeds = {"pool_a": [1, 4, 5, 7, 10, 12], "pool_b": [2, 3, 6, 8, 9, 11]}

pool_seeding = {
    8: two_pools_of_four_seeds,
    10: two_pools_of_five_seeds,
    12: four_pools_of_three_seeds,
    16: four_pools_of_four_seeds,
}


def get_d1_teams(teams: pd.DataFrame, custom_ranks: pd.DataFrame) -> pd.DataFrame:
    """
    Takes dataframe of D1 and D3 teams along with custom ratings
    for this season and returns a DataFrame of single rating
    with only D1 teams

    Parameters
    ----------
    teams : DataFrame 
        Table representing all D1 and D3 teams who have played a game this year

    custom_ranks : DataFrame
        Table representing a list of team names with custom rankings if desired

    Returns
    -------
    DataFrame
        Table of teams eligible to compete for nationals with updated rankings.
    """
    return (
        teams[teams.competition_division == "Division I"]
        .merge(
            custom_ranks[["Team", "Adjusted Rating"]],
            left_on="team",
            right_on="Team",
            how="inner",
        )
        .assign(
            custom_rating=lambda x: x["Adjusted Rating"].combine_first(x.power_rating).astype(int)
        )
    )


# bids
def calculate_size_and_bids(tables, d1_teams, rankings_col='custom_rating'):
    """
    Iterates through eligible teams by specified ranking type and returns
    a table of size and number of bids for the region.

    Parameters
    ----------
    tables : List[DataFrame]
        Set of tables read from USAU regional size allocation website
    d1_teams : DataFrame
        Return value from get_d1_teams()
    rankings_col : str, optional
        Which column to use from d1_teams to order bids, 
        by default 'custom_rating'

    Returns
    -------
    DataFrame
        One row per region with number of bids and number of teams competing
    """
    total_bids = 20
    # store boolean for whether autobid has been reached while iterating through rankings
    _bids = {region: [1, False] for region in d1_teams.college_region.unique()}
    for i, team in d1_teams.sort_values(rankings_col, ascending=False).iterrows():
        if sum(v[0] for k, v in _bids.items()) < total_bids:
            if _bids[team.college_region][1]:
                _bids[team.college_region][0] += 1
            else:
                _bids[team.college_region][1] = True

    # now just a dict of region name: number of bids
    bids = {k: v[0] for k, v in _bids.items()}

    conference_lookup = (
        d1_teams.drop_duplicates(subset=["college_conference", "college_region"])
        .set_index("college_conference")
        .college_region.to_dict()
    )

    combined = (
        pd.concat(
            [
                table
                for table in tables
                if table.columns.isin(
                    ["Conference", "Division", "Auto bids", "Strength bids", "Total"]
                ).min()
                and (table.Division == "D-I").max()
            ]
        )
        .reset_index(drop=True)
        .assign(region=lambda x: x["Conference"].map(conference_lookup))
    )
    region_details = (
        combined.groupby("region")
        .Total.sum()
        .rename("size")
        .to_frame()
        .assign(bids=lambda x: x.index.map(bids))
    )
    return region_details


def play_pools(teams, pool_seeds):
    results = {}
    for name, seeds in pool_seeds.items():
        pool = tournament.RoundRobinTournament(
            teams_list=teams.iloc[[i - 1 for i in seeds]].tolist(), name=f"Pool {name}"
        )
        pool.play_games()
        results[name] = pool
    return results


def determine_regional_qualifiers(
    division_teams, region, n_teams, rankings_var="power_rating"
):
    return (
        division_teams[division_teams.college_region == region]
        .head(n_teams)
        .apply(
            lambda r: Team(
                name=r.team, rating=int(r[rankings_var]), region=r.college_region
            ),
            axis=1,
        )
    )


def play_bracket(n_bids, **pools):
    n_teams = sum([len(pool) for name, pool in pools.items()])
    if n_teams in (8, 10):
        if n_bids == 1:
            t = tournament.BracketEightOne(**pools)
        elif n_bids in (2, 3):
            t = tournament.BracketEightTwoOne(**pools)
    elif n_teams == 12:
        if n_bids in [1, 2, 3]:
            t = tournament.BracketTwelveFourPools(**pools)
        if n_bids == 4:
            t = tournament.BracketEightFour(**pools)
    elif n_teams == 16:
        if n_bids == 1:
            t = tournament.BracketSixteenOne(**pools)
        if n_bids in (2, 3):
            t = tournament.BracketSixteenTwoTwo(**pools)
        if n_bids == 4:
            t = tournament.BracketSixteenFourTwo(**pools)
    else:
        return
    try:
        t.play_games()
    except:
        print(n_teams, n_bids)
        raise
    return t


def play_all_regions(d1_teams, region_details, writer, game_log_writer, division):
    summary = {}
    overall_pools = {}
    overall_placements = pd.DataFrame()
    for region, (n_teams, n_bids) in region_details.iterrows():
        if n_teams == 15:
            n_teams = 16
        teams = determine_regional_qualifiers(
            d1_teams, region, n_teams, rankings_var="custom_rating"
        )
        #This is hacky, we don't like the resulting br
        if n_teams == 12 and n_bids == 4:
            seeding = two_pools_of_six_seeds
        else: 
            seeding = pool_seeding[n_teams]
        pool_results = play_pools(teams, seeding)
        pool_finishes = {
            name: pool.determine_placement() for name, pool in pool_results.items()
        }
        overall_pools[region] = pd.DataFrame(pool_finishes).astype(str)
    
        bracket = play_bracket(n_bids, **pool_finishes)
        region_summary = {
            "Tournament": f"{division}'s {region} - {n_teams} Teams with {n_bids} Bids",
            "Format": f"{len(pool_results.keys())} pools of {len(pool_finishes['pool_a'])} -> {bracket.__class__.__name__}",
            "Qualifiers": ", ".join(
                [str(team) for team in bracket.determine_placement()[:n_bids]]
            ),
        }
        summary[region] = region_summary
        print()
        for k, v in region_summary.items():
            print(k.upper(), "-", v)
        overall_placements[f"{region} ({n_bids} bids)"] = pd.Series(
            bracket.determine_placement()
        )

        pool_games = []
        for name, pool in pool_results.items():
            for i, game in enumerate(pool.games_list):
                pool_games.append(game.results_dict)

        pd.DataFrame(pool_games).to_excel(
            writer, sheet_name=f"3. {division} {region} Pools"
        )
        pd.DataFrame([game.results_dict for game in bracket.games_list]).to_excel(
            writer, sheet_name=f"2. {division} {region} Bracket"
        )
        for i, game in enumerate(bracket.games_list):
            game_log = pd.Series(game.score.point_log).apply(
                lambda x: pd.Series({game.team_a.name: x[0], game.team_b.name: x[1]})
            )
            sheet_name = f"{division}{region[:8]}{game.level}{i}"
            if len(sheet_name) > 30 or game.level is None:
                continue
            game_log.to_excel(game_log_writer, sheet_name=sheet_name)

    pd.DataFrame(summary).T.to_excel(writer, sheet_name=f"1. {division} Overall Summary")
    pd.concat(
        [
            pd.DataFrame(index=[region], columns=v.columns, data="--").append(
                v.rename(lambda x: region)
            )
            for region, v in overall_pools.items()
        ]
    ).to_excel(writer, sheet_name=f"1. {division} Overall Pools")
    overall_placements.to_excel(writer, sheet_name=f"1. {division} Overall Placement")
    game_log_writer.save()


def run_all_regionals():

    # Use pandas html reader to extract dataframe
    result = pd.read_html(womens_ranking_html)
    df_women = result[0].rename(columns=lambda x: x.replace(" ", "_").lower()).iloc[0:-1]

    result = pd.read_html(mens_ranking_html)
    df_men = result[0].rename(columns=lambda x: x.replace(" ", "_").lower()).iloc[0:-1]

    custom_ranks_men = pd.read_excel(custom_ranks_path, sheet_name="Men").dropna(
        subset=["USAU Rank"]
    )
    custom_ranks_women = pd.read_excel(custom_ranks_path, sheet_name="Women").dropna(
        subset=["USAU Rank"]
    )
    d1_men = get_d1_teams(df_men, custom_ranks_men)
    d1_women = get_d1_teams(df_women, custom_ranks_women)

    mens_region_details = calculate_size_and_bids(
        pd.read_html(mens_bid_path, header=0), d1_men,
    )
    mens_region_details.loc["North Central", "size"] = 12
    mens_region_details.loc["Northwest", "size"] = 12
    mens_region_details.loc["New England", "size"] = 12

    for region, val in mens_adjustments.items():
        mens_region_details.loc[region, "bids"] += val

    womens_region_details = calculate_size_and_bids(
        pd.read_html(womens_bid_path, header=0), d1_women,
    )
    womens_region_details.loc["New England", "size"] = 12
    # print(womens_region_details)
    writer = pd.ExcelWriter("regionals_results.xlsx")

    pd.concat(
        [
            womens_region_details.rename(columns=lambda x: f"womens_{x}"),
            mens_region_details.rename(columns=lambda x: f"mens_{x}"),
        ],
        axis=1,
    ).to_excel(writer, "0. Bid Allocation")

    mens_game_log_writer = pd.ExcelWriter("mens_regionals_game_logs.xlsx")
    womens_game_log_writer = pd.ExcelWriter("womens_regionals_game_logs.xlsx")
    play_all_regions(
        d1_men, mens_region_details, writer, mens_game_log_writer, division="M"
    )
    play_all_regions(
        d1_women, womens_region_details, writer, womens_game_log_writer, division="W"
    )
    writer.book.worksheets_objs.sort(key=lambda x: x.name)
    writer.save()


if __name__ == "__main__":
    np.random.seed(42)
    run_all_regionals()
