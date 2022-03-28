# coding:utf-8

import random
import setup
import qlearn
import config as cfg
from time import *
import queue
import dqn
# reload(setup)
# reload(qlearn)


def pick_random_location():    # 选择一个不是墙并且没有智能体的地方生成
    while 1:
        x = random.randrange(world.width)
        y = random.randrange(world.height)
        cell = world.get_cell(x, y)
        if not (cell.wall or len(cell.agents) > 0):
            return cell


class Cat(setup.Agent):
    def __init__(self, filename):
        self.cell = None       # 赋值为best_move，表示自己已经走到了那个cell
        self.catWin = 0
        self.color = cfg.cat_color
        f = open(filename)
        lines = f.readlines()
        lines = [x.rstrip() for x in lines]
        self.fh = len(lines)
        self.fw = max([len(x) for x in lines])
        self.grid_list = [[1 for x in range(self.fw)] for y in range(self.fh)]
        # self.move = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]    # 可以移动8个方位
        self.move = [(-1, 0), (0, -1), (0, 1), (1, 0)]    # 可以移动4个方位

        for y in range(self.fh):
            line = lines[y]
            for x in range(min(self.fw, len(line))):
                t = 1 if (line[x] == 'X') else 0
                self.grid_list[y][x] = t            # 是墙的地方显示为1，其余地方是0

        # print 'cat init success......'

    # using BFS algorithm to move quickly to target：mouse.
    def bfs_move(self, target):            # --------------------还需要再看看---------------------
        if self.cell == target:
            return

        for n in self.cell.neighbors:
            if n == target:
                self.cell = target  # if next move can go towards target
                return

        best_move = None
        q = queue.Queue()
        start = (self.cell.y, self.cell.x)   # 声明移动的开始位置与结束位置
        end = (target.y, target.x)
        q.put(start)
        step = 1
        V = {}         # 访问过的
        preV = {}
        V[(start[0], start[1])] = 1

        # print 'begin BFS......'         # 开始广度优先搜索
        while not q.empty():
            grid = q.get()     # 队头的元素出队

            for i in range(4):   # 依次搜索当前节点8个方向的节点，能访问的入队
                ny, nx = grid[0] + self.move[i][0], grid[1] + self.move[i][1]    # 往旁边一个移
                if nx < 0 or ny < 0 or nx > (self.fw-1) or ny > (self.fh-1):  # 表示该搜索到的节点未在范围内，则放弃这次，进行下一个节点搜索
                    continue
                if self.get_value(V, (ny, nx)) or self.grid_list[ny][nx] == 1:  # has visit or is wall.
                    continue

                preV[(ny, nx)] = self.get_value(V, (grid[0], grid[1]))     # （ny，nx）这个节点的之前访问的节点
                if ny == end[0] and nx == end[1]:    # 移到了目标处
                    V[(ny, nx)] = step + 1   # 需要走这么多步-1
                    seq = []
                    last = V[(ny, nx)]      # 走到这个节点需要走多少次
                    while last > 1:   # 开始循环需要走的节点，加入seq中，得到怎么通过开始节点走向结束节点的序列
                        k = [key for key in V if V[key] == last]
                        seq.append(k[0])
                        assert len(k) == 1
                        last = preV[(k[0][0], k[0][1])]
                    seq.reverse()
                    # print seq

                    best_move = world.grid[seq[0][0]][seq[0][1]]    # 得到此时应该往什么cell走

                q.put((ny, nx))         # 将已经访问的邻居节点加入
                step += 1
                V[(ny, nx)] = step      # 更新走到这里需要走少次

        if best_move is not None:
            self.cell = best_move

        else:     # 如果没有最好的移动位置，便自动生成一个方向
            dir = random.randrange(cfg.directions)
            self.go_direction(dir)
            # print "!!!!!!!!!!!!!!!!!!"

    def get_value(self, mdict, key):     # 检查key下标的节点值，不为零则表示访问过
        try:
            return mdict[key]
        except KeyError:
            return 0

    def update(self):
        # print 'cat update begin..'
        if self.cell != mouse.cell:       # 开始广度优先搜索，每次只能得出最好的一步，因为老鼠也是在移动的！！！
            self.bfs_move(mouse.cell)
            # print 'cat move..'


class Cheese(setup.Agent):
    def __init__(self):
        self.color = cfg.cheese_color

    def update(self):
        # print 'cheese update...'
        pass


class Mouse(setup.Agent):    # 继承agent类
    def __init__(self):
        self.ai = None
        self.ai = dqn.DQN(actions=range(cfg.directions))
        self.catWin = 0
        self.mouseWin = 0
        self.round = 0
        self.lastState = None
        self.lastAction = 1
        self.color = cfg.mouse_color
        self.time = time()

        # print 'mouse init...'

    def update(self):
        # print 'mouse update begin...'
        state = self.calculate_state()    # 返回周围的路况，用0，1，2，3来表示方位们的情况，也就是是否有墙之类的
        reward = cfg.MOVE_REWARD
        done = False

        if time() - self.time >= 5:
            self.mouseWin += 1
            self.lastState = None
            self.cell = pick_random_location()
            self.time = time()
            return

        if self.cell == cat.cell:
            # print 'eaten by cat...'
            self.catWin += 1
            self.round += 1
            reward = cfg.EATEN_BY_CAT
            done = True
            if self.lastState is not None:
                self.ai.perceive(self.lastState, self.lastAction, reward, state, done)
                # print 'mouse learn...'
            self.lastState = None
            self.cell = pick_random_location()    # 被猫吃之后，重新生成
            self.time = time()
            # print 'mouse random generate..'
            return

        if self.cell == cheese.cell:          # 吃到了奶酪
            self.mouseWin += 1
            self.round += 1
            done = True
            reward = 50
            cheese.cell = pick_random_location()
            self.time = time()

        if self.lastState is not None:
            self.ai.perceive(self.lastState, self.lastAction, reward, state, done)

        # choose a new action and execute it
        action = self.ai.egreedy_action(state)
        self.lastState = state
        self.lastAction = action
        self.go_direction(action)          # 移向下一个状态

    def calculate_state(self):    # 计算周围方位的cell状态是什么，用数字来区分，以便判断cat，cheese，wall，路
        def cell_value(cell):
            if cat.cell is not None and (cell.x == cat.cell.x and cell.y == cat.cell.y):  # 和猫是在一起的
                return 3
            elif cheese.cell is not None and (cell.x == cheese.cell.x and cell.y == cheese.cell.y):   # 吃到了cheese
                return 2
            else:
                return 1 if cell.wall else 0   # 1撞到了墙，0则可以自己走

        dirs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

        # dirs = [(-1, 0), (0, -1), (0, 1), (1, 0)]
        return tuple([cell_value(world.get_relative_cell(self.cell.x + dir[0], self.cell.y + dir[1])) for dir in dirs])


if __name__ == '__main__':
    # EPISODE = 8001 # Episode limitation
    # STEP = 300 # Step limitation in an episode
    # TEST = 100 # The number of experiment test every 100 episode

    mouse = Mouse()
    cat = Cat(filename='resources/world.txt')
    cheese = Cheese()
    world = setup.World(filename='resources/world.txt')

    world.add_agent(mouse, cell=pick_random_location())
    world.add_agent(cheese, cell=pick_random_location())
    world.add_agent(cat, cell=pick_random_location())

    world.display.activate()
    world.display.speed = cfg.speed

    int_begin_time = begin_time = time()

    while 1:
        run_time1 = int(time() - int_begin_time)     # 游戏的总时间
        world.update(mouse.mouseWin, mouse.catWin, run_time1)
        end_time = time()
        run_time = end_time - begin_time
        if run_time - 5 > 10e-6:       # 在这里可以改变时间，选择每几秒进行一次记录
            if mouse.mouseWin:
                m_win = mouse.mouseWin
            else:
                m_win = 0
            if mouse.catWin:
                c_win = mouse.catWin
            else:
                c_win = 0
            print('==================================================')
            print(run_time, mouse.catWin, mouse.mouseWin)
            print('==================================================')
            f = open('record.txt', 'a')
            f.write('%d\t%d\n' % (c_win, m_win))
            f.close()
            begin_time = time()


    # ai = dqn.DQN(actions=range(cfg.directions))
    #
    # for episode in range(EPISODE):
    #     # 训练
    #
    #     if episode % 2000 == 0:
    #         for _ in range(TEST):  # 测试
    #             world.update(mouse.mouseWin, mouse.catWin)

