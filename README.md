Q-LearningGame
===================================================

The original version is from [vmayoral](https://github.com/vmayoral): [basic_reinforcement_learning:tutorial1](https://github.com/vmayoral/basic_reinforcement_learning/tree/master/tutorial1).

## About the game
Hunter always chases the escaper in the shortest path using BFS, and the escaper always learns to escape using Q-Learning algorithm from Reinforcement Learning.
## About the Q-Learning  
The algorithm of Q-Learning is:  
```
Q(s, a) += alpha * (reward(s,a) + gamma * max(Q(s', a') - Q(s,a))
```

```alpha``` is the learning rate.
```gamma``` is the value of the future reward.
It use the best next choice of utility in later state to update the former state.
