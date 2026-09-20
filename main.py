"""程序入口：初始化 pygame，创建游戏并进入主循环。

运行方式：
    python main.py
"""

import pygame

from game import Game


def main():
    pygame.init()
    try:
        Game().run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()