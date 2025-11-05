import pygame
import sys
import random
import logging


logging.basicConfig(filename="error.log", level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")


class SudokuBoard:
    def __init__(self):
        self.board = self.generate_board()
        self.original_board = [row[:] for row in self.board]
        self.selected = None

    def generate_board(self):
        board = [[0 for _ in range(9)] for _ in range(9)]
        for i in range(0, 9, 3):
            self.fill_box(board, i, i)
        self.solve(board)
        for _ in range(45):
            i, j = random.randint(0, 8), random.randint(0, 8)
            board[i][j] = 0
        return board

    def fill_box(self, board, row, col):
        nums = list(range(1, 10))
        random.shuffle(nums)
        for i in range(3):
            for j in range(3):
                board[row+i][col+j] = nums.pop()

    def valid(self, board, num, pos):
        for j in range(9):
            if board[pos[0]][j] == num and j != pos[1]:
                return False
        for i in range(9):
            if board[i][pos[1]] == num and i != pos[0]:
                return False
        box_x, box_y = pos[1] // 3, pos[0] // 3
        for i in range(box_y*3, box_y*3 + 3):
            for j in range(box_x*3, box_x*3 + 3):
                if board[i][j] == num and (i, j) != pos:
                    return False
        return True

    def find_empty(self, board):
        for i in range(9):
            for j in range(9):
                if board[i][j] == 0:
                    return (i, j)
        return None

    def solve(self, board):
        find = self.find_empty(board)
        if not find:
            return True
        row, col = find
        for i in range(1, 10):
            if self.valid(board, i, (row, col)):
                board[row][col] = i
                if self.solve(board):
                    return True
                board[row][col] = 0
        return False

    def place_number(self, num):
        if self.selected:
            row, col = self.selected
            if self.original_board[row][col] == 0:
                if self.valid(self.board, num, (row, col)):
                    self.board[row][col] = num
                else:
                    logging.warning(f"Tentativa inválida: {num} em ({row},{col})")

    def is_complete(self):
        for row in self.board:
            if 0 in row:
                return False
        return True

class SudokuGame:
    def __init__(self):
        pygame.init()
        self.width, self.height = 540, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Sudoku - PyGame")
        self.font = pygame.font.SysFont("arial", 40)
        self.board = SudokuBoard()
        self.run_game()

    def draw_grid(self):
        for i in range(10):
            thickness = 4 if i % 3 == 0 else 1
            pygame.draw.line(self.screen, (0, 0, 0), (0, i*60), (540, i*60), thickness)
            pygame.draw.line(self.screen, (0, 0, 0), (i*60, 0), (i*60, 540), thickness)

    def draw_numbers(self):
        for i in range(9):
            for j in range(9):
                num = self.board.board[i][j]
                if num != 0:
                    color = (0, 0, 0) if self.board.original_board[i][j] != 0 else (0, 0, 255)
                    text = self.font.render(str(num), True, color)
                    self.screen.blit(text, (j*60 + 20, i*60 + 10))

    def highlight_cell(self):
        if self.board.selected:
            row, col = self.board.selected
            pygame.draw.rect(self.screen, (255, 255, 0), (col*60, row*60, 60, 60), 3)

    def click_cell(self, pos):
        x, y = pos
        if x < 540 and y < 540:
            col, row = x // 60, y // 60
            self.board.selected = (row, col)

    def run_game(self):
        clock = pygame.time.Clock()
        while True:
            self.screen.fill((255, 255, 255))
            self.draw_grid()
            self.draw_numbers()
            self.highlight_cell()

            if self.board.is_complete():
                win_text = self.font.render("Você venceu!", True, (0, 128, 0))
                self.screen.blit(win_text, (170, 550))
            else:
                info_text = self.font.render("Clique e digite (1-9)", True, (128, 0, 0))
                self.screen.blit(info_text, (120, 550))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.click_cell(pygame.mouse.get_pos())
                if event.type == pygame.KEYDOWN:
                    if event.unicode.isdigit():
                        num = int(event.unicode)
                        if 1 <= num <= 9:
                            try:
                                self.board.place_number(num)
                            except Exception as e:
                                logging.error(f"Erro ao inserir número: {e}")

            pygame.display.flip()
            clock.tick(30)


if __name__ == "__main__":
    try:
        SudokuGame()
    except Exception as e:
        logging.error(f"Erro fatal: {e}")
        pygame.quit()
        sys.exit()
