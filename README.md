# Simulating USA Ultimate College Nationals outcomes

## The Tournament

USA Ultimate D-I College Nationals happen May 24-27, 2019.
Nationals has 40 teams: 20 in the women's tournament and 20 in the men's.
The first stage is pool play, where the teams are divided up into four pools of five teams each.
The pool-play format is a round robin where each team plays every other team in their pool once.
The second stage is a 12-team single elimination bracket.  Winners of the pools advance straight to the quarters, while the second and third place teams in each pool advance to the prequarters round.
The winner of the bracket is crowned the 2019 D-1 college champion.

## Picking Teams for Fantasy Ultimate

So, the decision--and there should always be a decision with a data science project--is to determine which teams to pick for the fantasy game.
The fantasy game works like this:  A participant selects two men's division and two women’s division teams, plus one that can come from either division.
To score your picks, first note their seed in their pool.  If a team is seeded first in their pool, they are the 1-seed, second in the pool they are the 2-seed, ..., last in their pool they are the 5-seed.
Then, points awarded in the following manner: each win by a 1-seed gets 1 point, each win by a 2-seed gets 2, and so on.
Bonus points are awarded as follows: finishing at the top of your pool get you 1 point, winning a quarterfinal game (1 point), winning a semifinal game (2 points), and winning the finals (3 points).

So, the ultimate goal of this analysis is to get determine which combination of teams should be selected to maximize your points and thus your chance of winning the fantasy contest.

(Note: with a large number of players, it may not be good to pursue a strategy of maximizing expected points.
While this strategy would be expected to maximize your average points over 1,000s of tournaments.  It may not maximize the likelihood of you being the _top_ point scorer in a given game.  
If the goal is to be the top point scorer, you may want to consider a riskier strategy that has the possibility of scoring a larger number of points, even if there is also a stronger liklihood of scoring fewer points.  This a high celing, lower floor, i.e. high variance strategy.) 

## Simulating the Tournament

To make informed picks, I decided to simulate and score the tournament.
I simulate each point of each game of the tournament, advancing the teams throught the bracket and determine the winner.
I simulated the tournament 1000 times.  
(I could do 10,000, but haven’t yet due to time constraints.)
I used Bernoulli trials to simulate a college ultimate game. 
Two weighted coins are used.  
One is flipped when team A is on offense and the other is flipped when team B is on offense.
Team A's coin is flipped until they score, then team B's coin is flipped until they score.
This process is repeated flipping until one team reaches 15 points.

To decide the weights of the coins, I used two pieces of information.
The first is the difference in power ratings between two teams.
The power ratings of all college ultimate teams were scraped from the USAU website.  
The power ratings are calculated based on the victory margin (winning team score minus losing team score).
So, I can invert this process and difference the power ratings of two teams to get their expected game score.
For example, if team A has a power rating of 2300 and team B has a power rating of 2000, then the expected score in agame to 15 is approximately 15-12 (a victory margin of 3).

The second piece of information is the offensive success rate of the higher rated team. 
This is the probability that team A scores an offensive point if A is the higher rated team.
Based on data from ultianalytics--there is only a small amount of data on this--national's bound college teams consistently have a value of 0.8 for this probability.
In other words, on average, the higher rated offense holds 4 out of 5 points and gets broken 1 out of 5 points.
I don't have much data on this, and this parameter is very important to the model.  Changing the value to 1.0 means tthat the higher rated offense scores _every_ time they start an offense--an unlikely scenario.  Changing the value to 0.25 means that the higher rated team scores only one out of every four offensive points.
Games played with this value are characterized by long streaks breaks that are also highly unlikely.
Generally speaking, the higher this value, the more certain the outcome (less variance).
The lower the value, the less certain the outcome and the more possibility of widely divergent outcomes.
The value may vary with conditions.
In poor conditions (wind, rain, mud, etc.) the value is probably lower (high variance in outcomes).
In perfect conditions (sunny, little wind) the value is probaly higher.

So, based on the expected score and the probability the higher rated offense holds, how do we determine the probabilities of the coins flipped in our Bernoulli trials?

Let's assume without loss of generality, that team A is the higher rated team. Then,

Coin 1: probability that team A scores on an offensive point = 0.8 (or whatever value we get)

Coin 2: probability that team B scores on an offsensive point =

 0.8 * (expected points for B) / (expected points for A)

Ex: If the expected score is 15-10, then coin 1 has probability of heads 0.8 and coin 2 has probability of heads 0.8 * 10/15 = 0.53.   




