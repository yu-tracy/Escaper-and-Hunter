import tensorflow as tf
import numpy as np
import random
import collections

GAMMA = 0.9  # discount factor for target Q
INITIAL_EPSILON = 0.4  # starting value of epsilon
FINAL_EPSILON = 0.1  # final value of epsilon  最开始是0.01
REPLAY_SIZE = 5000  # experience replay buffer size
BATCH_SIZE = 32  # size of minibatch

class DQN:
    # DQN Agent
    def __init__(self, actions):      # 怎样改变这个-----------env------------
        # init experience replay
        self.replay_buffer = collections.deque()    # 缓冲池
        # init some parameters
        self.time_step = 0
        self.epsilon = INITIAL_EPSILON
        # -------------下面这两个需要修改-----------------
        self.state_dim = 8   # 状态的维度，方块的8个方向
        self.action_dim = 4     # 行为的维度，可以走8个方向
        self.actions = actions

        self.create_q_network()
        self.create_training_method()

        # Init session
        self.session = tf.InteractiveSession()
        self.session.run(tf.initialize_all_variables())    # run 所有的变量，tf1----------

    def create_q_network(self):   # 构造q网络
        # network weights（网络中变量的维度)
        W1 = self.weight_variable([self.state_dim, 20])
        b1 = self.bias_variable([20])
        W2 = self.weight_variable([20, self.action_dim])
        b2 = self.bias_variable([self.action_dim])
        # input layer
        self.state_input = tf.placeholder("float", [None, self.state_dim])
        # hidden layers
        h_layer = tf.nn.relu(tf.matmul(self.state_input, W1) + b1)
        # Q Value layer
        self.Q_value = tf.matmul(h_layer, W2) + b2

    def create_training_method(self):   # -----------训练方法---------------
        self.action_input = tf.placeholder("float", [None, self.action_dim])  # one hot presentation
        self.y_input = tf.placeholder("float", [None])

        # 行求和，这是对应的q行为的值，然后将其化为1维，得到最后的行为值
        Q_action = tf.reduce_sum(tf.multiply(self.Q_value, self.action_input), reduction_indices=1)
        self.cost = tf.reduce_mean(tf.square(self.y_input - Q_action))   # 计算平均代价
        self.optimizer = tf.train.AdamOptimizer(0.0001).minimize(self.cost)   # 用梯度下降的方法来定义优化器

    def perceive(self, state, action, reward, next_state, done):
        one_hot_action = np.zeros(self.action_dim)     # 初始化0矩阵
        one_hot_action[action] = 1    # 对应的行为赋1，也就是当前状态下采用的行为为1
        self.replay_buffer.append((state, one_hot_action, reward, next_state, done))
        if len(self.replay_buffer) > REPLAY_SIZE:
            self.replay_buffer.popleft()

        if len(self.replay_buffer) > BATCH_SIZE:
            # 先将一些经验缓存到缓冲池中，当需要训练的时候再开始训练网络
            self.train_q_network()

    def train_q_network(self):
        self.time_step += 1
        # Step 1: obtain random minibatch from replay memory，随机抽batch_size个样本用于训练
        minibatch = random.sample(self.replay_buffer, BATCH_SIZE)
        state_batch = [data[0] for data in minibatch]
        action_batch = [data[1] for data in minibatch]
        reward_batch = [data[2] for data in minibatch]
        next_state_batch = [data[3] for data in minibatch]

        # Step 2: calculate y
        y_batch = []   # 由q_learning计算出来的真实值
        Q_value_batch = self.Q_value.eval(feed_dict={self.state_input: next_state_batch})   # 赋值之后参与求值运算然后返回结果
        for i in range(0, BATCH_SIZE):
            done = minibatch[i][4]
            if done:
                y_batch.append(reward_batch[i])
            else:
                y_batch.append(reward_batch[i] + GAMMA * np.max(Q_value_batch[i]))    # 这里就类比于q_learning算法
        print(y_batch)
        self.optimizer.run(feed_dict={     # 优化器开始计算
            self.y_input: y_batch,
            self.action_input: action_batch,
            self.state_input: state_batch
        })

    def egreedy_action(self, state):    # 输入状态之后用贪婪算法来得到行为
        Q_value = self.Q_value.eval(feed_dict={   # 这里通过赋值已经得出q值
            self.state_input: [state]
        })[0]
        if random.random() <= self.epsilon:
            self.epsilon -= (INITIAL_EPSILON - FINAL_EPSILON) / 10000
            return self.actions[random.randint(0, self.action_dim - 1)]
        else:
            self.epsilon -= (INITIAL_EPSILON - FINAL_EPSILON) / 10000
            return self.actions[np.argmax(Q_value)]   # 返回最大数的索引

    def action(self, state):   # 测试时需要用到的函数
        return np.argmax(self.Q_value.eval(feed_dict={
            self.state_input: [state]
        })[0])

    def weight_variable(self, shape):
        initial = tf.truncated_normal(shape)
        return tf.Variable(initial)

    def bias_variable(self, shape):
        initial = tf.constant(0.01, shape=shape)
        return tf.Variable(initial)


EPISODE = 10000 # Episode limitation
STEP = 300 # Step limitation in an episode
TEST = 10 # The number of experiment test every 100 episode

# def run_dqn():
#     # initialize OpenAI Gym env and dqn agent
#
#     # env = gym.make(ENV_NAME)      # ----------这里需要改---------------
#     dqn_network = DQN()
#
#     for episode in range(EPISODE):    # 只循环10000次
#         # initialize task
#         state = env.reset()          # 获得最初的状态，训练部分
#         # Train
#         for step in range(STEP):    # 在每个大循环里，step只循环300次
#             action = agent.egreedy_action(state)  # e-greedy action for train，选取一个行为
#             next_state, reward, done, _ = env.step(action)    # 获取环境信息
#             # Define reward for agent
#             reward_agent = -1 if done else 0.1    # 智能体的奖励，--------需要修改--------
#             agent.perceive(state, action, reward, next_state, done)    # 对环境进行感知
#             state = next_state    # 换到下一状态
#             if done:     # done表示是否游戏结束
#                 break
#         # Test every 100 episodes     测试部分，这部分用于展现，上部分用于训练，不展现
#         if episode % 100 == 0:
#             total_reward = 0
#             for i in range(TEST):     # 测试十次
#                 state = env.reset()
#                 for j in range(STEP):
#                     env.render()
#                     action = agent.action(state) # direct action for test，直接根据神经网络来输出，没有任何探索
#                     state, reward, done, _ = env.step(action)
#                     total_reward += reward
#                     if done:
#                         break
#             ave_reward = total_reward/TEST
#             # print 'episode: ',episode,'Evaluation Average Reward:',ave_reward
#             if ave_reward >= 200:
#                 break
