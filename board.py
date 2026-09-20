"""棋盘与核心规则逻辑。

这个模块只负责"数据"和"规则"，不涉及任何绘制代码，
因此可以脱离图形界面单独测试。
"""

from enum import Enum

from config import DEFAULT_MAX_MISTAKES


class Direction(Enum):
    """箭头的四个方向，枚举值同时就是关卡文件里使用的字符。"""

    UP = "^"
    DOWN = "v"
    LEFT = "<"
    RIGHT = ">"

    @property
    def delta(self):
        """该方向在棋盘上的位移 (行增量, 列增量)。

        行号向下递增、列号向右递增，所以"向上"是 (-1, 0)。
        """
        return {
            Direction.UP: (-1, 0),
            Direction.DOWN: (1, 0),
            Direction.LEFT: (0, -1),
            Direction.RIGHT: (0, 1),
        }[self]


# 关卡字符 -> 方向，用于解析关卡数据
CHAR_TO_DIRECTION = {direction.value: direction for direction in Direction}


class ClickResult(Enum):
    """点击一个箭头之后可能出现的判定结果。"""

    FLY_OUT = "fly_out"    # 前方畅通，箭头飞出棋盘并被消除
    BLOCKED = "blocked"    # 前方有箭头阻挡，本次点击消耗一次失误
    IGNORED = "ignored"    # 点到空格或者棋盘之外，不产生任何影响


class Board:
    """一个关卡的棋盘状态。

    箭头统一保存在 arrows 字典里，键是格子坐标 (row, col)，
    值是 Direction；已经飞出棋盘的箭头会从这个字典里删掉。
    """

    def __init__(self, grid, max_mistakes=DEFAULT_MAX_MISTAKES, name="关卡"):
        self.name = name
        self.max_mistakes = max_mistakes
        self.initial_grid = [line for line in grid]
        self.rows = len(self.initial_grid)
        self.cols = max((len(line) for line in self.initial_grid), default=0)
        self.arrows = {}
        self.mistakes = 0
        self._load()

    def _load(self):
        """按照关卡数据重建箭头（restart 时也会用到）。"""
        self.arrows.clear()
        for row, line in enumerate(self.initial_grid):
            for col, char in enumerate(line):
                direction = CHAR_TO_DIRECTION.get(char)
                if direction is not None:
                    self.arrows[(row, col)] = direction

    # ---------------------------------------------------------------
    # 状态查询
    # ---------------------------------------------------------------
    def restart(self):
        """把本关恢复到初始状态：箭头布局和失误次数都还原（T06）。"""
        self._load()
        self.mistakes = 0

    @property
    def remaining(self):
        """剩余箭头数量。"""
        return len(self.arrows)

    @property
    def cleared(self):
        """本关是否已经清空。"""
        return not self.arrows

    @property
    def mistakes_left(self):
        """剩余失误次数。"""
        return self.max_mistakes - self.mistakes

    @property
    def failed(self):
        """失误次数是否已经耗尽。"""
        return self.mistakes >= self.max_mistakes

    def arrow_at(self, row, col):
        """取某个格子上的箭头方向，空格子返回 None。"""
        return self.arrows.get((row, col))

    # ---------------------------------------------------------------
    # 规则判定（第二步：路径检测时实现）
    # ---------------------------------------------------------------
    def can_fly_out(self, row, col):
        """判断 (row, col) 上的箭头前方是否没有其他箭头阻挡。"""
        raise NotImplementedError("路径检测将在第二步实现")

    def click(self, row, col):
        """处理一次点击，返回 ClickResult。"""
        raise NotImplementedError("点击判定将在第二步实现")