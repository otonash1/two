"""全局配置：窗口尺寸、棋盘布局、颜色、字体等常量。

这里只放"数据"不放逻辑，想调整界面外观时改这个文件就够了。
"""

# ---------- 窗口 ----------
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 720
WINDOW_TITLE = "一箭又一箭"
FPS = 60

# ---------- 棋盘 ----------
CELL_SIZE = 96                 # 格子边长的上限（像素），棋盘较大时会自动缩小
BOARD_TOP = 150                # 棋盘区域的上边界
BOARD_BOTTOM = 620             # 棋盘区域的下边界（给底部按钮留出空间）
BOARD_MARGIN_X = 40            # 棋盘左右两侧至少保留的空白
BOARD_PADDING = 10             # 棋盘白底相对格子的外扩留白
GRID_LINE_WIDTH = 2
ARROW_RATIO = 0.62             # 箭头大小相对格子的比例
HIGHLIGHT_RING_WIDTH = 4       # 碰撞高亮圆环的线宽

# ---------- 颜色 ----------
COLOR_BG = (241, 245, 249)
COLOR_PANEL = (255, 255, 255)
COLOR_BOARD_BG = (255, 255, 255)
COLOR_BOARD_BORDER = (148, 163, 184)
COLOR_GRID_LINE = (203, 213, 225)
COLOR_ARROW = (37, 99, 235)
COLOR_ARROW_BLOCKED = (220, 38, 38)
COLOR_TEXT = (30, 41, 59)
COLOR_TEXT_MUTED = (100, 116, 139)
COLOR_BUTTON = (37, 99, 235)
COLOR_BUTTON_HOVER = (59, 130, 246)
COLOR_BUTTON_TEXT = (255, 255, 255)
COLOR_OVERLAY = (15, 23, 42, 150)

# ---------- 字体 ----------
# 中文字体文件（按优先级尝试）。直接读字体文件而不走 SysFont，
# 可以避开 pygame 在部分 Windows 上读取字体注册表时的崩溃问题。
FONT_FILES = (
    r"C:\Windows\Fonts\msyh.ttc",    # 微软雅黑
    r"C:\Windows\Fonts\msyhbd.ttc",  # 微软雅黑 Bold
    r"C:\Windows\Fonts\simhei.ttf",  # 黑体
    r"C:\Windows\Fonts\simsun.ttc",  # 宋体
)
FONT_TITLE = 56
FONT_HEADING = 34
FONT_NORMAL = 22
FONT_SMALL = 18

# ---------- 界面元素位置 (x, y, width, height) ----------
BTN_MENU_START = (350, 430, 200, 58)
BTN_PLAYING_RESTART = (380, 645, 140, 46)
BTN_LEVEL_CLEAR_NEXT = (350, 430, 200, 58)
BTN_GAME_OVER_RESTART = (350, 430, 200, 58)
BTN_ALL_CLEAR_MENU = (350, 430, 200, 58)

# ---------- 动画 ----------
ANIM_FLY_TIME = 0.30           # 箭头飞出动画的时长（秒）
ANIM_SHAKE_TIME = 0.60         # 碰撞抖动 / 红色高亮的持续时长（秒）
ANIM_SHAKE_AMPLITUDE = 12      # 碰撞抖动的最大偏移（像素）
ANIM_HINT_TIME = 1.6           # 顶部碰撞提示文字的停留时长（秒）

# ---------- 规则 ----------
DEFAULT_MAX_MISTAKES = 3       # 每关默认的失误次数上限