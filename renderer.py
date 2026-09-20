"""绘制层：把游戏状态画到 Surface 上。

所有文字都通过 draw_text() 输出，字体和配色统一由 config 控制。
这一层不做任何规则判断，只负责"把数据画出来"。
"""

import math
import os

import pygame

import config
from board import Direction

_font_cache = {}


# ---------------------------------------------------------------
# 基础绘制工具
# ---------------------------------------------------------------
def _load_font(size, bold):
    """加载中文字体：优先用系统字体文件，找不到就用 pygame 自带字体兜底。"""
    for path in config.FONT_FILES:
        if os.path.isfile(path):
            font = pygame.font.Font(path, size)
            font.set_bold(bold)
            return font
    font = pygame.font.Font(None, size)
    font.set_bold(bold)
    return font


def get_font(size, bold=False):
    """按字号取字体（带缓存）。"""
    key = (size, bold)
    if key not in _font_cache:
        _font_cache[key] = _load_font(size, bold)
    return _font_cache[key]


def draw_text(surface, text, size, center=None, topleft=None, topright=None,
              color=None, bold=False):
    """绘制一行文字，返回它占用的矩形。"""
    image = get_font(size, bold).render(text, True, color or config.COLOR_TEXT)
    rect = image.get_rect()
    if center is not None:
        rect.center = center
    elif topleft is not None:
        rect.topleft = topleft
    elif topright is not None:
        rect.topright = topright
    surface.blit(image, rect)
    return rect


def draw_button(surface, rect_tuple, label, hovered=False):
    """绘制一个圆角按钮。"""
    rect = pygame.Rect(rect_tuple)
    color = config.COLOR_BUTTON_HOVER if hovered else config.COLOR_BUTTON
    pygame.draw.rect(surface, color, rect, border_radius=10)
    draw_text(surface, label, config.FONT_NORMAL, center=rect.center, color=config.COLOR_BUTTON_TEXT)
    return rect


# ---------------------------------------------------------------
# 棋盘几何
# ---------------------------------------------------------------
def board_rect(board):
    """棋盘白底在窗口中的矩形。"""
    return pygame.Rect(
        config.BOARD_ORIGIN[0] - config.BOARD_PADDING,
        config.BOARD_ORIGIN[1] - config.BOARD_PADDING,
        board.cols * config.CELL_SIZE + config.BOARD_PADDING * 2,
        board.rows * config.CELL_SIZE + config.BOARD_PADDING * 2,
    )


def cell_center(row, col):
    """格子中心在窗口中的坐标。"""
    origin_x, origin_y = config.BOARD_ORIGIN
    size = config.CELL_SIZE
    return (origin_x + col * size + size // 2, origin_y + row * size + size // 2)


# ---------------------------------------------------------------
# 箭头
# ---------------------------------------------------------------
# 以"朝右"为基准的箭头形状，坐标是相对格子大小的比例，
# 其余三个方向由这个形状旋转得到。
_ARROW_SHAPE = [
    (0.50, 0.00),    # 箭尖
    (0.05, -0.34),   # 箭头下沿
    (0.05, -0.14),
    (-0.50, -0.14),  # 箭尾
    (-0.50, 0.14),
    (0.05, 0.14),
    (0.05, 0.34),    # 箭头上沿
]

_DIRECTION_ANGLE = {
    Direction.RIGHT: 0,
    Direction.DOWN: 90,
    Direction.LEFT: 180,
    Direction.UP: 270,
}


def arrow_points(center, size, direction):
    """算出箭头多边形的顶点：基准形状 -> 按方向旋转 -> 平移到格子中心。"""
    angle = math.radians(_DIRECTION_ANGLE[direction])
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    center_x, center_y = center
    points = []
    for x, y in _ARROW_SHAPE:
        px, py = x * size, y * size
        points.append((center_x + px * cos_a - py * sin_a,
                       center_y + px * sin_a + py * cos_a))
    return points


def draw_arrow(surface, center, direction, color, size=None):
    """在 center 处画一个指定方向的箭头。"""
    size = size or config.CELL_SIZE * config.ARROW_RATIO
    pygame.draw.polygon(surface, color, arrow_points(center, size, direction))


def draw_board(surface, game):
    """画棋盘白底、网格线和所有未消除的箭头。"""
    board = game.board
    rect = board_rect(board)
    pygame.draw.rect(surface, config.COLOR_BOARD_BG, rect, border_radius=12)

    origin_x, origin_y = config.BOARD_ORIGIN
    size = config.CELL_SIZE
    for row in range(board.rows):
        for col in range(board.cols):
            cell = pygame.Rect(origin_x + col * size, origin_y + row * size, size, size)
            pygame.draw.rect(surface, config.COLOR_GRID_LINE, cell, width=config.GRID_LINE_WIDTH)

    pygame.draw.rect(surface, config.COLOR_BOARD_BORDER, rect, width=3, border_radius=12)

    for (row, col), direction in board.arrows.items():
        center = cell_center(row, col)
        selected = game.selected == (row, col)
        if selected:
            pygame.draw.circle(surface, config.COLOR_ARROW_SELECTED, center,
                               int(size * 0.46), config.SELECT_RING_WIDTH)
        draw_arrow(surface, center, direction,
                   config.COLOR_ARROW_SELECTED if selected else config.COLOR_ARROW)


# ---------------------------------------------------------------
# 各个界面
# ---------------------------------------------------------------
def draw_menu(surface, game):
    """开始界面。"""
    width, height = surface.get_size()
    draw_text(surface, "一箭又一箭", config.FONT_TITLE, center=(width // 2, 240), bold=True)
    draw_text(surface, "点击箭头，让它飞出棋盘", config.FONT_NORMAL,
              center=(width // 2, 320), color=config.COLOR_TEXT_MUTED)
    draw_text(surface, "前方有箭头阻挡时不能飞出，并且会消耗一次失误", config.FONT_SMALL,
              center=(width // 2, 372), color=config.COLOR_TEXT_MUTED)
    draw_button(surface, config.BTN_MENU_START, "开始游戏",
                hovered=game.is_hovered(config.BTN_MENU_START))
    draw_text(surface, "按 ESC 退出游戏", config.FONT_SMALL,
              center=(width // 2, height - 40), color=config.COLOR_TEXT_MUTED)


def draw_playing(surface, game):
    """游戏界面：顶部信息 + 棋盘 + 底部按钮。"""
    board = game.board
    width, _ = surface.get_size()

    draw_text(surface, board.name, config.FONT_HEADING, topleft=(40, 32), bold=True)
    draw_text(surface, f"剩余箭头：{board.remaining}", config.FONT_NORMAL,
              topright=(width - 40, 42))
    draw_text(surface, f"剩余失误：{board.mistakes_left} / {board.max_mistakes}",
              config.FONT_NORMAL, topright=(width - 40, 74),
              color=config.COLOR_ARROW_BLOCKED if board.mistakes_left <= 1 else config.COLOR_TEXT)

    draw_board(surface, game)

    button = config.BTN_PLAYING_RESTART
    draw_button(surface, button, "重新开始", hovered=game.is_hovered(button))
    draw_text(surface, "按 ESC 返回主菜单", config.FONT_SMALL,
              topleft=(40, button[1] + 12), color=config.COLOR_TEXT_MUTED)


def draw_result(surface, game):
    """过关 / 失败 / 全部通关界面：棋盘上盖一层遮罩，再弹出提示面板。"""
    width, height = surface.get_size()
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill(config.COLOR_OVERLAY)
    surface.blit(overlay, (0, 0))

    panel = pygame.Rect(0, 0, 520, 300)
    panel.center = (width // 2, 400)
    pygame.draw.rect(surface, config.COLOR_PANEL, panel, border_radius=16)

    draw_text(surface, game.message, config.FONT_TITLE, center=(width // 2, 330), bold=True)
    draw_text(surface, game.hint, config.FONT_NORMAL, center=(width // 2, 396),
              color=config.COLOR_TEXT_MUTED)
    draw_button(surface, game.result_button_rect, game.result_button_label,
                hovered=game.is_hovered(game.result_button_rect))