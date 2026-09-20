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
def board_layout(board):
    """算出棋盘的位置和格子大小，返回 (origin_x, origin_y, cell_size)。

    棋盘水平居中、竖直放在棋盘区域里；关卡比可用空间大时自动缩小格子，
    这样不同尺寸的关卡（5x5、6x6……）都能完整显示。
    绘制和"点击坐标 -> 格子"的换算共用这一份几何信息，保证两边一致。
    """
    size = min(
        config.CELL_SIZE,
        (config.WINDOW_WIDTH - config.BOARD_MARGIN_X * 2) // board.cols,
        (config.BOARD_BOTTOM - config.BOARD_TOP) // board.rows,
    )
    origin_x = (config.WINDOW_WIDTH - board.cols * size) // 2
    area_height = config.BOARD_BOTTOM - config.BOARD_TOP
    origin_y = config.BOARD_TOP + (area_height - board.rows * size) // 2
    return origin_x, origin_y, size


def board_rect(board):
    """棋盘白底在窗口中的矩形。"""
    origin_x, origin_y, size = board_layout(board)
    return pygame.Rect(
        origin_x - config.BOARD_PADDING,
        origin_y - config.BOARD_PADDING,
        board.cols * size + config.BOARD_PADDING * 2,
        board.rows * size + config.BOARD_PADDING * 2,
    )


def cell_center(board, row, col):
    """格子中心在窗口中的坐标。"""
    origin_x, origin_y, size = board_layout(board)
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


def draw_arrow(surface, center, direction, color, size):
    """在 center 处画一个指定方向、指定大小的箭头。"""
    pygame.draw.polygon(surface, color, arrow_points(center, size, direction))


def draw_board(surface, game):
    """画棋盘白底、网格线和所有未消除的箭头。"""
    board = game.board
    origin_x, origin_y, size = board_layout(board)
    rect = board_rect(board)
    pygame.draw.rect(surface, config.COLOR_BOARD_BG, rect, border_radius=12)

    for row in range(board.rows):
        for col in range(board.cols):
            cell = pygame.Rect(origin_x + col * size, origin_y + row * size, size, size)
            pygame.draw.rect(surface, config.COLOR_GRID_LINE, cell, width=config.GRID_LINE_WIDTH)

    pygame.draw.rect(surface, config.COLOR_BOARD_BORDER, rect, width=3, border_radius=12)

    for (row, col), direction in board.arrows.items():
        center = cell_center(board, row, col)
        progress = game.blocked_elapsed / config.ANIM_SHAKE_TIME
        blocked = game.blocked_cell == (row, col) and progress < 1.0
        if blocked:
            # 刚被挡住的箭头：朝自己的方向"撞"一下再弹回来，并套一圈红色圆环
            delta_row, delta_col = direction.delta
            shake = math.sin(progress * math.pi * 3) * config.ANIM_SHAKE_AMPLITUDE * (1 - progress)
            center = (center[0] + delta_col * shake, center[1] + delta_row * shake)
            pygame.draw.circle(surface, config.COLOR_ARROW_BLOCKED,
                               (int(center[0]), int(center[1])),
                               int(size * 0.46), config.HIGHLIGHT_RING_WIDTH)
        draw_arrow(surface, center, direction,
                   config.COLOR_ARROW_BLOCKED if blocked else config.COLOR_ARROW,
                   size=size * config.ARROW_RATIO)

    draw_flying_arrows(surface, game)


def draw_flying_arrows(surface, game):
    """正在飞出的箭头：沿自己的方向冲向棋盘外，同时逐渐变淡。"""
    board = game.board
    _, _, size = board_layout(board)
    for item in game.flying:
        progress = min(item["elapsed"] / config.ANIM_FLY_TIME, 1.0)
        center = cell_center(board, item["row"], item["col"])
        delta_row, delta_col = item["direction"].delta
        # 算一下这个箭头还要走几格才算飞出棋盘，动画正好在"刚出界"时结束
        if delta_row > 0:
            steps = board.rows - item["row"]
        elif delta_row < 0:
            steps = item["row"] + 1
        elif delta_col > 0:
            steps = board.cols - item["col"]
        else:
            steps = item["col"] + 1
        travel = (steps + 0.5) * size * progress
        center = (center[0] + delta_col * travel, center[1] + delta_row * travel)
        # 画在带透明通道的小画布上，实现"越飞越淡"
        patch = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.polygon(
            patch,
            config.COLOR_ARROW + (int(255 * (1.0 - progress)),),
            arrow_points((size / 2, size / 2), size * config.ARROW_RATIO, item["direction"]),
        )
        surface.blit(patch, (int(center[0] - size / 2), int(center[1] - size / 2)))


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
    if game.blocked_cell is not None and game.blocked_elapsed < config.ANIM_HINT_TIME:
        draw_text(surface, "前方有箭头阻挡，不能飞出（失误 +1）", config.FONT_SMALL,
                  center=(width // 2, 122), color=config.COLOR_ARROW_BLOCKED)

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