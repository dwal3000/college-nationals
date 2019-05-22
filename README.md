# college-nationals
Simulating USA Ultimate College Nationals outcomes


USA Ultimate D-I College Nationals happen May 24-27, 2019.
Nationals has 40 teams: 20 in the women's tournament and 20 in the men's.
The first stage is pool play, where the teams are divided up into 4 pools of five teams each.
The pool play format is a round robin, each team playes every other team in their pool once.
The second stage is a 12-team single elimination bracket.  Winners of the pools advance straight to the quarters, while the second and third place teams in each pool advance to the prequarters round.
The winner of the bracket is crowned the 2019 D-1 college champion.

So, the decision--and there should always be a decision with a data science project--is to determine which teams to pick for the fantasy game.
The fantasy game works like this:  A participant selects two men's division and two women’s division teams + one that can come from either division.
To score your picks, first, note their seed in their pool.  If a team is seeded first in their pool, they are the 1-seed, second in the pool they are the 2-seed, ..., last in their pool they are the 5-seed.
Then, points aarded in the following manner: each win by a 1-seed gets 1 point, each win by a 2-seed gets 2, and so on.
Bonus points are awarded as follows: finishing at the top of your pool get you 1 point, winning a quarterfinal game (1 point), winning a semifinal game (2 points), and winning the finals (3 points).

So, the ultimate goal of this analysis is to get determine which combination of teams should be selected to maximize your chance of winning the fantasy contest.

I figured that if I could simulate and score the tournament I could make more informed picks
So I is simulate each point of each game of the tournament.  And, I simulated the tournament 1000 times.  (Could do 10,000, but haven’t yet due to time constraints.)
I scraped power ratings of all college ultimate teams from the web and used Bernoulli trial kind of process to simulate a college ultimate game. 
Weighted coins are flipped, depending whether a team is on offense or defense
Continue flipping until one team reaches 15 points

