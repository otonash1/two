"""游戏状态机：负责场景切换、事件分发和主循环。"""

from enum import Enum

import pygame

import config
import renderer
from board import Board
from levels import LEVELS


class Scene(Enum):
    """游戏当前所处的界面。"""

    MENU = "menu"                # 开始界面
    PLAYING = "playing"          # 游戏界面
    LEVEL_CLEAR = "level_clear"  # 过关界面
    GAME_OVER = "game_over"      # 失败界面
    ALL_CLEAR = "all_clear"      # 全部关卡通关


class Game:
    """管理整个游戏：当前关卡、当前界面，以及鼠标键盘的响应。"""

    def __init__(self):
        self.screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        pygame.display.set_caption(config.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        self.scene = Scene.MENU
        self.board = None
        self.level_index = 0
        self.selected = None            # 当前选中的格子 (row, col)，用于高亮显示

        self.message = ""               # 结算界面的主标题
        self.hint = ""                  # 结算界面的说明文字
        self.result_button_rect = config.BTN_LEVEL_CLEAR_NEXT
        self.result_button_label = "下一关"

    # ---------------------------------------------------------------
    # 关卡流程
    # ---------------------------------------------------------------
    def start_level(self, index):
        """载入第 index 关并进入游戏界面。"""
        level = LEVELS[index]
        self.level_index = index
        self.board = Board(
            level["grid"],
            max_mistakes=level.get("max_mistakes", config.DEFAULT_MAX_MISTAKES),
            name=level.get("name", f"第 {index + 1} 关"),
        )
        self.selected = None
        self.scene = Scene.PLAYING

    def restart_level(self):
        """重新开始当前关卡（T06）。"""
        if self.board is None:
            return
        self.board.restart()
        self.selected = None
        self.scene = Scene.PLAYING

    def next_level(self):
        """进入下一关，已经是最后一关则显示全部通关。"""
        if self.level_index + 1 < len(LEVELS):
            self.start_level(self.level_index + 1)
        else:
            self.show_all_clear()

    def finish_level(self):
        """当前关卡的箭头全部清空后调用。"""
        if self.level_index + 1 < len(LEVELS):
            self._show_result(Scene.LEVEL_CLEAR, "过关！", f"{self.board.name} 已完成", "下一关")
        else:
            self.show_all_clear()

    def show_game_over(self):
        """失误次数耗尽时调用（T05）。"""
        self._show_result(Scene.GAME_OVER, "本关失败", "失误次数已用完，再试一次吧", "重新开始")

    def show_all_clear(self):
        """所有关卡都通关时调用。"""
        self._show_result(Scene.ALL_CLEAR, "全部通关！", "你已经完成了所有关卡", "返回主菜单")

    def back_to_menu(self):
        self.scene = Scene.MENU
        self.board = None
        self.selected = None

    def _show_result(self, scene, message, hint, button_label):
        """切到结算界面，并记住这个界面的按钮。"""
        self.scene = scene
        self.message = message
        self.hint = hint
        self.result_button_label = button_label
        self.result_button_rect = {
            Scene.LEVEL_CLEAR: config.BTN_LEVEL_CLEAR_NEXT,
            Scene.GAME_OVER: config.BTN_GAME_OVER_RESTART,
            Scene.ALL_CLEAR: config.BTN_ALL_CLEAR_MENU,
        }[scene]

    # ---------------------------------------------------------------
    # 输入处理
    # ---------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._on_escape()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._on_click(event.pos)

    def _on_escape(self):
        if self.scene is Scene.MENU:
            self.running = False
        else:
            self.back_to_menu()

    def _on_click(self, pos):
        if self.scene is Scene.MENU:
            if self._hit(config.BTN_MENU_START, pos):
                self.start_level(0)

        elif self.scene is Scene.PLAYING:
            if self._hit(config.BTN_PLAYING_RESTART, pos):
                self.restart_level()
                return
            cell = self.cell_at(pos)
            if cell is not None:
                # 第二步会在这里改成调用 board.click()，接上完整的判定
                if self.board.arrow_at(*cell) is not None:
                    self.selected = cell

        else:  # 三个结算界面
            if self._hit(self.result_button_rect, pos):
                self._on_result_button()

    def _on_result_button(self):
        if self.scene is Scene.LEVEL_CLEAR:
            self.next_level()
        elif self.scene is Scene.GAME_OVER:
            self.restart_level()
        else:
            self.back_to_menu()

    @staticmethod
    def _hit(rect_tuple, pos):
        return pygame.Rect(rect_tuple).collidepoint(pos)

    def is_hovered(self, rect_tuple):
        """鼠标是否停在某个按钮上（用于绘制悬停颜色）。"""
        return self._hit(rect_tuple, pygame.mouse.get_pos())

    def cell_at(self, pos):
        """把窗口坐标换算成格子坐标，点在棋盘外返回 None。"""
        if self.board is None:
            return None
        origin_x, origin_y = config.BOARD_ORIGIN
        size = config.CELL_SIZE
        x, y = pos
        if not (origin_x <= x < origin_x + self.board.cols * size
                and origin_y <= y < origin_y + self.board.rows * size):
            return None
        return ((y - origin_y) // size, (x - origin_x) // size)

    # ---------------------------------------------------------------
    # 主循环
    # ---------------------------------------------------------------
    def draw(self):
        """先铺底色，再按当前场景绘制。"""
        self.screen.fill(config.COLOR_BG)
        if self.scene is Scene.MENU:
            renderer.draw_menu(self.screen, self)
        elif self.scene is Scene.PLAYING:
            renderer.draw_playing(self.screen, self)
        else:
            # 结算界面：只画棋盘做背景，再盖上半透明面板
            renderer.draw_board(self.screen, self)
            renderer.draw_result(self.screen, self)

    def run(self):
        while self.running:
            self.clock.tick(config.FPS)
            for event in pygame.event.get():
                self.handle_event(event)
            self.draw()
            pygame.display.flip()