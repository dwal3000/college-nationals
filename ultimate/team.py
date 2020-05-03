import pandas as pd


class Team:
    def __init__(
        self, name="", rating="", nickname="", games_list=None, section="", region=""
    ):
        self.name = name
        self.rating = rating
        self.games_list = games_list
        self.nickname = nickname
        self.wins = 0
        self.losses = 0
        if not games_list:
            self.games_list = []
        else:
            self.games_list = games_list
            self.get_record()

    def __repr__(self):
        return f"{self.name} ({self.wins} - {self.losses})"

    def get_record(self):
        self.wins = 0
        self.losses = 0
        for game in self.games_list:
            if game.winner.name == self.name:
                self.wins += 1
            else: 
                self.losses += 1
        return (self.wins, self.losses)


def import_teams(ranking_html_file):
    # From a USAU ranking page html file
    # read the html in as a dataframe and save the info
    # about the teams, one row for each team.
    result = pd.read_html(ranking_html_file)
    df = result[0]

    # remove last row because it contains junk
    df = df.drop(index=len(df) - 1)

    # Convert numeric columns to from string/object to correct type
    cols = ["Rank", "Power Rating", "Wins", "Losses"]
    df[cols] = df[cols].apply(pd.to_numeric)

    return df


def get_top_teams_from_region(df_rankings, region, n=12, division="Division I"):
    # Based on either the mens or women's df_rankings dataframe,
    # grab the top n teams from the region by USAU ranking.
    sorted_teams_from_the_region = df_rankings[
        (df_rankings["College Region"] == region)
        & (df_rankings["Competition Division"] == division)
    ].sort_values(["Rank", "Power Rating"], ascending=[True, False])

    return sorted_teams_from_the_region.head(n)


def create_teams_from_dataframe(df_teams):
    # Create teams_list from teams data frame
    # output is a list of Team objects representing
    # the teams in the dataframe.
    # Captures their name, section, region, and power rating
    teams_list = []
    for i in df_teams.index:
        team_here = Team(
            name=df_teams.loc[i, "Team"],
            rating=df_teams.loc[i, "Power Rating"],
            section=df_teams.loc[i, "College Conference"],
            region=df_teams.loc[i, "College Region"],
        )
        teams_list.append(team_here)

    return teams_list
