"""游戏状态机：负责场景切换、事件分发和主循环。"""

from enum import Enum

import pygame

import config
import renderer
from board import Board, ClickResult
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
        self.blocked_cell = None        # 最近一次被挡住的格子 (row, col)，用于碰撞高亮
        self.blocked_elapsed = 0.0      # 碰撞发生之后过了多久（秒），驱动抖动和提示淡出
        self.flying = []                # 正在播飞出动画的箭头：{row, col, direction, elapsed}

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
        self._clear_feedback()
        self.scene = Scene.PLAYING

    def restart_level(self):
        """重新开始当前关卡（T06）。"""
        if self.board is None:
            return
        self.board.restart()
        self._clear_feedback()
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
        self._clear_feedback()

    def _clear_feedback(self):
        """清掉碰撞提示和还没播完的飞出动画。"""
        self.blocked_cell = None
        self.blocked_elapsed = 0.0
        self.flying.clear()

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
                self.handle_cell_click(cell)

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

    def handle_cell_click(self, cell):
        """点击棋盘的某个格子：先交给 Board 判定，再按结果推进游戏流程。"""
        direction = self.board.arrow_at(*cell)
        result = self.board.click(*cell)
        if result is ClickResult.IGNORED:
            return
        if result is ClickResult.FLY_OUT:
            self.blocked_cell = None
            # 已经消除的箭头不能再从棋盘上取，这里记下它飞出的方向播动画
            self.flying.append({"row": cell[0], "col": cell[1],
                                "direction": direction, "elapsed": 0.0})
            if self.board.cleared:
                self.finish_level()          # 箭头全部清空 -> 过关（T04）
        else:
            self.blocked_cell = cell         # 被挡住：高亮这个箭头，提示碰撞
            self.blocked_elapsed = 0.0
            if self.board.failed:
                self.show_game_over()        # 失误次数耗尽 -> 失败（T05）

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
        origin_x, origin_y, size = renderer.board_layout(self.board)
        x, y = pos
        if not (origin_x <= x < origin_x + self.board.cols * size
                and origin_y <= y < origin_y + self.board.rows * size):
            return None
        return ((y - origin_y) // size, (x - origin_x) // size)

    # ---------------------------------------------------------------
    # 主循环
    # ---------------------------------------------------------------
    def update(self, dt):
        """推进动画：飞出动画到时后移除，碰撞计时用于抖动和提示的淡出。"""
        for item in self.flying:
            item["elapsed"] += dt
        self.flying = [item for item in self.flying if item["elapsed"] < config.ANIM_FLY_TIME]
        if self.blocked_cell is not None:
            self.blocked_elapsed += dt

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
            dt = self.clock.tick(config.FPS) / 1000.0   # 距上一帧的秒数，用于推进动画
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
            pygame.display.flip()