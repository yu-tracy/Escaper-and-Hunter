# coding:utf-8

import time
import tkinter
from io import BytesIO
import random
import config as cfg


class Cell:   # cell类的颜色显示
    def __init__(self):
        self.wall = False  # 用于显示这里是否有墙

    def color(self):
        if self.wall:
            return cfg.wall_color
        else:
            return 'papayawhip'  # 没有墙，是路

    def load(self, data):
        if data == 'X':   # 为x时，有墙
            self.wall = True
        else:
            self.wall = False

    def __getattr__(self, key):
        if key == 'neighbors':
            opts = [self.world.get_next_grid(self.x, self.y, dir) for dir in range(self.world.directions)]
            next_states = tuple(self.world.grid[y][x] for (x, y) in opts)
            return next_states   # 返回下一个可能状态的grid（里面存放的是cell的信息）
        raise AttributeError(key)


class Agent:
    def __setattr__(self, key, value):
        if key == 'cell':
            old = self.__dict__.get(key, None)
            if old is not None:
                old.agents.remove(self)  # 将原来cell里面的agent删除
            if value is not None:
                value.agents.append(self)   # 在现在这个新的cell里面加上该agent，表示这个agent已经移位了
        self.__dict__[key] = value   # 该智能体位于哪个valuecell

    def go_direction(self, dir):
        target = self.cell.neighbors[dir]   # 这里调用了cell的默认getattr函数
        if getattr(target, 'wall', False):  # 判断下一个位置是不是墙
            # print "hit a wall"
            return False
        self.cell = target   # 调用了setattr函数，表示agent已经在这个新的地方了
        return True

class World:
    def __init__(self, cell=None, directions=cfg.directions, filename=None):
        if cell is None:
            cell = Cell
        self.Cell = cell
        self.display = make_display(self)  # 将世界展示出来
        self.directions = directions   # 方向
        self.filename = filename

        self.grid = None
        self.dictBackup = None
        self.agents = []
        self.age = 0

        self.height = None
        self.width = None
        self.get_file_size(filename)  # 获得长和宽

        self.image = None
        self.mouseWin = None
        self.catWin = None
        self.run_time = None
        self.reset()
        self.load(filename)

    def get_file_size(self, filename):  # 获得world的长，宽
        if filename is None:
            raise Exception("world file not exist!")
        data = open(filename).readlines()
        if self.height is None:
            self.height = len(data)
        if self.width is None:
            self.width = max([len(x.rstrip()) for x in data])

    def reset(self):
        # grid中存放的是cell类，将world里的每一格信息存在grid里
        self.grid = [[self.make_cell(i, j) for i in range(self.width)] for j in range(self.height)]   # 颠倒地放world
        self.dictBackup = [[{} for _i in range(self.width)] for _j in range(self.height)]  # 备份
        self.agents = []
        self.age = 0  # 过了多少年

    def make_cell(self, x, y):   # cell中的属性集
        c = self.Cell()
        c.x = x
        c.y = y
        c.world = self
        c.agents = []
        return c

    def get_cell(self, x, y):
        return self.grid[y][x]

    def get_relative_cell(self, x, y):  # 要是超过world的大小了，便取余数
        return self.grid[y % self.height][x % self.width]

    def load(self, f):   # 将wall与通道分开
        if not hasattr(self.Cell, 'load'):
            return
        if isinstance(f, type('')):
            f = open(f)   # 创建file对象
        lines = f.readlines()
        lines = [x.rstrip() for x in lines]  # 去掉前后空格
        fh = len(lines)
        fw = max([len(x) for x in lines])

        if fh > self.height:
            fh = self.height
            start_y = 0
        else:
            start_y = int((self.height - fh) / 2)
        if fw > self.width:
            fw = self.width
            start_x = 0
        else:
            start_x = int((self.width - fw) / 2)

        self.reset()
        for j in range(fh):
            line = lines[j]
            for i in range(min(fw, len(line))):
                self.grid[start_y + j][start_x + i].load(line[i])  # 调用cell的函数load加载墙或路

    def update(self, mouse_win=None, cat_win=None, run_time=None):  # -----------？？？？？？？？？？？------------
        if hasattr(self.Cell, 'update'):
            for a in self.agents:
                a.update()
            self.display.redraw()
        else:
            for a in self.agents:
                old_cell = a.cell
                a.update()         # 调用智能体的update函数
                if old_cell != a.cell:  # old cell won't disappear when new cell
                    self.display.redraw_cell(old_cell.x, old_cell.y)

                self.display.redraw_cell(a.cell.x, a.cell.y)

        if mouse_win:
            self.mouseWin = mouse_win
        if cat_win:
            self.catWin = cat_win
        self.run_time = run_time
        self.display.update()
        self.age += 1

    def get_next_grid(self, x, y, dir):
        dx = 0
        dy = 0
        if self.directions == 8:
            dx, dy = [(0, -1), (1, -1), (
                1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)][dir]
        elif self.directions == 4:
            dx, dy = [(0, -1), (1, 0), (0, 1), (-1, 0)][dir]
        x2 = x + dx
        y2 = y + dy

        if x2 < 0:   # 可以从左边通向右边
            x2 += self.width
        if y2 < 0:
            y2 += self.height
        if x2 >= self.width:
            x2 -= self.width
        if y2 >= self.height:
            y2 -= self.height

        return x2, y2

    def add_agent(self, agent, x=None, y=None, cell=None, dir=None):  # 在任意位置随机生成一个agent
        self.agents.append(agent)  # 世界里添加智能体
        if cell is not None:
            x = cell.x
            y = cell.y
        if x is None:
            x = random.randrange(self.width)
        if y is None:
            y = random.randrange(self.height)
        if dir is None:
            dir = random.randrange(self.directions)

        agent.cell = self.grid[y][x]    # 智能体位于哪个cell
        agent.dir = dir
        agent.world = self


# GUI display
class TkinterDisplay:
    def __init__(self, size=cfg.grid_width):
        self.activated = False
        self.paused = False
        self.title = ''
        self.updateEvery = 1
        self.root = None
        self.speed = cfg.speed
        self.size = size  # 每一个grid的像素大小
        self.imageLabel = None
        self.frameWidth = 0    # 框架的长宽
        self.frameHeight = 0
        self.world = None
        self.bg = None
        self.image = None
        self.m_last = 0
        self.c_last = 0

    def activate(self):
        if self.root is None:
            self.root = tkinter.Tk()
        for c in self.root.winfo_children():
            c.destroy()  # 销毁root中的小部件
        self.bg = None
        self.activated = True
        self.imageLabel = tkinter.Label(self.root)  # 在指定的root窗口中显示图像
        self.imageLabel.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=1)  # 设定应该出现的位置，fill表示当窗口变化时，是x变化还是y变化还是both变化
        self.frameWidth, self.frameHeight = self.world.width * self.size, self.world.height * self.size
        self.root.geometry('%dx%d' % (self.world.width * self.size, self.world.height * self.size))   # 设置窗口大小
        self.root.update()
        self.redraw()
        self.root.bind('<Escape>', self.quit)    # make Esc exit the program 调用quit函数

    def quit(self):
        self.root.destroy()  # 销毁root中的所有控件

    def update(self):
        if not self.activated:
            return
        if self.world.age % self.updateEvery != 0 and not self.paused:  # ------------这里没懂--------------
            return
        self.set_title(self.title)
        self.imageLabel.update()
        if self.speed > 0:
            time.sleep(float(1)/self.speed)

    def make_title(self, world):  # 制造窗口左上角的title字符串
        text = 'time: %ds' % world.run_time
        extra = []
        if world.mouseWin:
            extra.append('逃生者：%d' % world.mouseWin)
            m_win = world.mouseWin
        else:
            m_win = 0
        if world.catWin:
            extra.append('杀手：%d' % world.catWin)
            c_win = world.catWin
        else:
            c_win = 0
        if world.display.paused:           # ----------------这两个需要后来看看-----------------
            extra.append('paused')
        if world.display.updateEvery != 1:
            extra.append('skip=%d' % world.display.updateEvery)
        if world.display.speed > 0:
            extra.append('speed=%dm/s' % world.display.speed)

        self.m_last = m_win
        self.c_last = c_win

        if len(extra) > 0:
            text += ' [%s]' % ', '.join(extra)   # 转换成字符串类型
        return text

    def set_title(self, title):       # 设置标题
        if not self.activated:
            return
        self.title = title
        title += ' %s' % self.make_title(self.world)
        if self.root.title() != title:
            self.root.title(title)

    def pause(self):        # 没有暂停就一直update
        self.paused = not self.paused
        while self.paused:
            self.update()

    def getBackground(self):  # ------------获取或者是制作背景，还需要再看看-------------
        if self.bg is None:
            r, g, b = self.imageLabel.winfo_rgb(self.root['background'])   # 该方法将颜色字符串转换为三元组，但background是怎么来的？？？？
            self.bg = '%c%c%c' % (r >> 8, g >> 8, b >> 8)    # 将其转换到255位的颜色范围
        return self.bg

    def redraw(self):
        if not self.activated:
            return

        # iw = self.world.width * self.size
        # ih = self.world.height * self.size

        # hexgrid = self.world.directions == 6
        # if hexgrid:
        #     iw += self.size / 2

        # f = open('temp.ppm', 'wb')
        # input_str = 'P6\n%d %d\n255\n' % (iw, ih)
        # f.write(input_str.encode(encoding='UTF-8'))    # 定义temp文件
        # # 'P6\n%d %d\n255\n' % (iw, ih)
        #
        # # odd = False
        # for row in self.world.grid:
        #     line = BytesIO()     # 向内存写文件
        #     # if hexgrid and odd:
        #     #     line.write(self.getBackground() * (self.size / 2))
        #     for cell in row:
        #         if len(cell.agents) > 0:     # 如果一个cell里有多个智能体，那么呈现最后一个到达的智能体的颜色
        #             c = self.get_data_color(cell.agents[-1])    # 返回颜色的三原色信息
        #         else:
        #             c = self.get_data_color(cell)
        #
        #         str1 = c * self.size
        #         line.write(str1.encode(encoding='UTF-8'))    # 将cell的行颜色信息以像素块的形式写在line中,得到一个重复了self.size的c的字符串
        #
        #     # if hexgrid and not odd:
        #     #     line.write(self.getBackground() * (self.size / 2))
        #     # odd = not odd
        #     str2 = line.getvalue() * self.size
        #     f.write(str2)   # 获取line中的值，写入temp文件中，得到了self.size的line字符串
        # f.close()

        self.image = tkinter.PhotoImage(file='temp.ppm')
        self.imageLabel.config(image=self.image)   # 显示图像

    imageCache = {}

    def redraw_cell(self, x, y):    # ----------？？？-------------
        if not self.activated:
            return
        sx = x * self.size
        sy = y * self.size
        # if y % 2 == 1 and self.world.directions == 6:
        #     sx += self.size / 2

        cell = self.world.grid[y][x]
        if len(cell.agents) > 0:     # 获取cell的颜色
            c = self.get_text_color(cell.agents[-1])  # 显示最后一个到的智能体的颜色
        else:
            c = self.get_text_color(cell)
        # 得到的c为颜色的十六位表示（#06B1C8）或white
        sub = self.imageCache.get(c, None)
        if sub is None:    # -------------这里还有一点没看懂---------------
            sub = tkinter.PhotoImage(width=1, height=1)
            sub.put(c, to=(0, 0))
            sub = sub.zoom(self.size)
            self.imageCache[c] = sub
        self.image.tk.call(self.image, 'copy', sub, '-from', 0, 0, self.size, self.size, '-to', sx, sy)    # 将cell中的图像更新

    def get_text_color(self, obj):
        c = getattr(obj, 'color', None)   # 如果传进来的是智能体，则是有color的属性，否则就是路
        if c is None:
            c = getattr(obj, 'color', 'papayawhip')
        if callable(c):
            c = c()
        if isinstance(c, type(())):
            if isinstance(c[0], type(0.0)):
                c = (int(c[0] * 255), int(c[1] * 255), int(c[2] * 255))
            return '#%02x%02x%02x' % c
        return c

    dataCache = {}

    def get_data_color(self, obj):     # ---------返回的颜色格式是适合ppm文件的颜色格式，注意和上面相似函数的区别！！！！！！！！！！
        c = getattr(obj, 'color', None)    # 获取c的颜色值
        if c is None:
            c = getattr(obj, 'color', 'papayawhip')
        if callable(c):
            c = c()
        if isinstance(c, type(())):
            if isinstance(c[0], type(0.0)):
                c = (int(c[0] * 255), int(c[1] * 255), int(c[2] * 255))
            return '%c%c%c' % c
        else:
            val = self.dataCache.get(c, None)
            if val is None:
                r, g, b = self.imageLabel.winfo_rgb(c)
                val = '%c%c%c' % (r >> 8, g >> 8, b >> 8)
                self.dataCache[c] = val
            return val


def make_display(world):
    d = TkinterDisplay()
    d.world = world
    return d