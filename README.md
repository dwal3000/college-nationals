# college-nationals
Simulating USA Ultimate College Nationals outcomes


Ultimate Frisbee college nationals coming up
20-team tournament first stage is pool play, i.e. round robin where each pool of 5 plays each other
Second stage is a 12-team single elimination bracket
So, the decision--and there should always be a decision with a data science project--was which teams to pick for the fantasy game.
Two mens division’s and two women’s division teams + one that can come from either division
Scoring system, where each win by a 1-seed gets 1 pt, 2-seed gets 2 pts, etc.

I figured that if I could simulate and score the tournament I could make more informed picks
So I is simulate each point of each game of the tournament.  And, I simulated the tournament 1000 times.  (Could do 10,000, but haven’t yet due to time constraints.)
I scraped power ratings of all college ultimate teams from the web and used Bernoulli trial kind of process to simulate a college ultimate game. 
Weighted coins are flipped, depending whether a team is on offense or defense
Continue flipping until one team reaches 15 points

