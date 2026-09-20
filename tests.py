"""T01–T06 自动化测试。

对应作业要求的六项测试：
    T01  点击前方畅通的箭头 -> 飞出并消除
    T02  点击前方被挡住的箭头 -> 不能飞出，失误 +1
    T03  位于边界、朝棋盘外的箭头 -> 可以飞出
    T04  清空一个关卡的全部箭头 -> 判定过关（三个关卡都验证一遍）
    T05  失误次数耗尽 -> 判定失败
    T06  重新开始 -> 箭头布局与失误次数还原

测试使用 pygame 的 dummy 视频驱动，不需要真实显示器；
在项目目录下运行：
    python tests.py
"""

import os
import unittest

# 必须在导入 pygame 之前设置，这样在没有显示器的环境里也能跑测试
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

import config
from board import Board, ClickResult, Direction
from game import Game, Scene
from levels import LEVELS


def make_board(grid, max_mistakes=config.DEFAULT_MAX_MISTAKES):
    """按字符矩阵造一个棋盘，方便写用例。"""
    return Board(grid, max_mistakes=max_mistakes, name="测试关卡")


def first_flyable(board):
    """找出当前第一个能飞出的箭头，没有则返回 None。"""
    for cell in board.arrows:
        if board.can_fly_out(*cell):
            return cell
    return None


class BoardRulesTest(unittest.TestCase):
    """T01–T03：只依赖 board.py 的核心规则判定。"""

    def test_t01_前方畅通的箭头可以飞出(self):
        """T01 前方没有箭头阻挡时，点击后箭头飞出并从棋盘上消失。"""
        board = make_board([
            "....",
            ".>..",
            "....",
        ])
        result = board.click(1, 1)
        self.assertIs(result, ClickResult.FLY_OUT)
        self.assertIsNone(board.arrow_at(1, 1), "飞出的箭头应该从棋盘上移除")
        self.assertEqual(board.remaining, 0)
        self.assertEqual(board.mistakes, 0, "顺利飞出不消耗失误次数")

    def test_t02_前方被挡住的箭头不能飞出(self):
        """T02 前方有箭头阻挡时不能飞出，箭头留在原地且失误 +1。"""
        board = make_board([
            "....",
            ".><.",
            "....",
        ])
        result = board.click(1, 1)
        self.assertIs(result, ClickResult.BLOCKED)
        self.assertIsNotNone(board.arrow_at(1, 1), "被挡住的箭头应该留在棋盘上")
        self.assertEqual(board.mistakes, 1, "被挡住应记一次失误")
        self.assertEqual(board.mistakes_left, board.max_mistakes - 1)

    def test_t03_边界处朝棋盘外的箭头可以飞出(self):
        """T03 贴着边界、方向朝棋盘外的箭头可以直接飞出。"""
        board = make_board([
            "..^..",
            ".....",
            "<...>",
            ".....",
            "..v..",
        ])
        for cell in [(0, 2), (2, 0), (2, 4), (4, 2)]:
            self.assertIs(board.click(*cell), ClickResult.FLY_OUT,
                          f"{cell} 朝棋盘外，应该能飞出")
        self.assertTrue(board.cleared)
        self.assertEqual(board.mistakes, 0)


class GameFlowTest(unittest.TestCase):
    """T04–T06：通过 game.py 走完整的界面流程。"""

    def setUp(self):
        self.game = Game()

    def test_t04_清空全部箭头后判定过关(self):
        """T04 存在能清空所有箭头的点击顺序，清空后进入过关界面。"""
        # 棋盘层：三个关卡都能按"能飞就飞"的顺序清空
        for level in LEVELS:
            board = Board(level["grid"], max_mistakes=level["max_mistakes"],
                          name=level["name"])
            clicks = 0
            while not board.cleared:
                cell = first_flyable(board)
                self.assertIsNotNone(cell, f"{level['name']} 还有箭头却都飞不出去")
                self.assertIs(board.click(*cell), ClickResult.FLY_OUT)
                clicks += 1
            self.assertGreater(clicks, 0)
            self.assertEqual(board.mistakes, 0)

        # 界面层：清空当前关卡后，游戏界面切换到过关界面
        self.game.start_level(0)
        while not self.game.board.cleared:
            cell = first_flyable(self.game.board)
            self.assertIsNotNone(cell)
            self.game.handle_cell_click(cell)
        self.assertIs(self.game.scene, Scene.LEVEL_CLEAR)
        self.assertEqual(self.game.result_button_label, "下一关")

    def test_t05_失误次数耗尽后判定失败(self):
        """T05 失误次数用完后，进入失败界面。"""
        # 棋盘层：失误次数记满即失败
        board = make_board([
            "....",
            ".><.",
            "....",
        ], max_mistakes=2)
        board.click(1, 1)
        self.assertFalse(board.failed, "还有失误次数，不算失败")
        board.click(1, 1)
        self.assertTrue(board.failed)
        self.assertEqual(board.mistakes_left, 0)

        # 界面层：连续点击被挡住的箭头，失误用完后切到失败界面
        self.game.start_level(0)
        blocked_cell = (1, 2)   # 第 1 关中间一列向下的箭头，被下面的箭头挡住
        for _ in range(config.DEFAULT_MAX_MISTAKES):
            self.game.handle_cell_click(blocked_cell)
        self.assertEqual(self.game.board.mistakes, config.DEFAULT_MAX_MISTAKES)
        self.assertIs(self.game.scene, Scene.GAME_OVER)
        self.assertEqual(self.game.result_button_label, "重新开始")

    def test_t06_重新开始后关卡还原(self):
        """T06 重新开始后，飞出的箭头回来、失误次数清零。"""
        # 棋盘层：飞出一支、故意失误两次之后 restart
        board = make_board([
            "..>..",
            "..><.",
        ], max_mistakes=2)
        self.assertIs(board.click(0, 2), ClickResult.FLY_OUT)
        self.assertIs(board.click(1, 2), ClickResult.BLOCKED)
        self.assertIs(board.click(1, 3), ClickResult.BLOCKED)
        self.assertTrue(board.failed)

        board.restart()
        self.assertEqual(
            board.arrows,
            {(0, 2): Direction.RIGHT, (1, 2): Direction.RIGHT, (1, 3): Direction.LEFT},
            "重新开始后应恢复初始布局（飞出的箭头回来）",
        )
        self.assertEqual(board.mistakes, 0)
        self.assertFalse(board.failed)

        # 界面层：游玩中点击"重新开始"按钮，当前关卡还原
        self.game.start_level(0)
        total = self.game.board.remaining
        self.game.handle_cell_click(first_flyable(self.game.board))
        self.assertEqual(self.game.board.remaining, total - 1)

        restart_button = pygame.Rect(config.BTN_PLAYING_RESTART)
        self.game.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": restart_button.center}))
        self.assertEqual(self.game.board.remaining, total, "重新开始后箭头数量应还原")
        self.assertEqual(self.game.board.mistakes, 0)
        self.assertIs(self.game.scene, Scene.PLAYING)


def setUpModule():
    pygame.init()


def tearDownModule():
    pygame.quit()


if __name__ == "__main__":
    unittest.main(verbosity=2)