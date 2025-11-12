import pygame
import sys
import random
import logging
import time
import mysql.connector

logging.basicConfig(filename="sudoku_error.log", level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

class MySQLRanking:
    def __init__(self, host="localhost", user="root", password="root", database="sudoku_db"):
        try:
            self.conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            self.cursor = self.conn.cursor()
            self.create_table()
        except mysql.connector.Error as e:
            logging.error(f"Erro ao conectar ao MySQL: {e}")
            print(e)
            print("⚠️ Aviso: não foi possível conectar ao banco MySQL. Continuando sem ranking.")
            self.conn = None
            self.cursor = None

    def create_table(self):
        if not self.conn:
            return
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS ranking (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nome VARCHAR(50),
                    dificuldade VARCHAR(20),
                    tempo FLOAT
                )
            """)
            self.conn.commit()
        except mysql.connector.Error as e:
            logging.error(f"Erro ao criar tabela: {e}")

    def add_score(self, nome, dificuldade, tempo):
        if not self.conn:
            return
        try:
            self.cursor.execute(
                "INSERT INTO ranking (nome, dificuldade, tempo) VALUES (%s, %s, %s)",
                (nome, dificuldade, tempo)
            )
            self.conn.commit()
        except mysql.connector.Error as e:
            logging.error(f"Erro ao inserir score: {e}")

    def get_top_scores(self, dificuldade, limit=5):
        if not self.conn:
            return []
        try:
            self.cursor.execute(
                "SELECT nome, tempo FROM ranking WHERE dificuldade = %s ORDER BY tempo ASC LIMIT %s",
                (dificuldade, limit)
            )
            return self.cursor.fetchall()
        except mysql.connector.Error as e:
            logging.error(f"Erro ao buscar ranking: {e}")
            return []

class SudokuBoard:
    def __init__(self, dificuldade="fácil"):
        self.dificuldade = dificuldade
        self.board = self.generate_board()
        self.original_board = [row[:] for row in self.board]
        self.selected = None
        self.errors = {}

    def generate_board(self):
        board = [[0 for _ in range(9)] for _ in range(9)]
        for i in range(0, 9, 3):
            self.fill_box(board, i, i)
        self.solve(board)
        dificuldade_vazios = {"fácil": 40, "médio": 50, "difícil": 60}
        remov = dificuldade_vazios.get(self.dificuldade, 45)
        for _ in range(remov):
            i, j = random.randint(0, 8), random.randint(0, 8)
            board[i][j] = 0
        return board

    def fill_box(self, board, row, col):
        nums = list(range(1, 10))
        random.shuffle(nums)
        for i in range(3):
            for j in range(3):
                board[row + i][col + j] = nums.pop()

    def valid(self, board, num, pos):
        for j in range(9):
            if board[pos[0]][j] == num and j != pos[1]:
                return False
        for i in range(9):
            if board[i][pos[1]] == num and i != pos[0]:
                return False
        box_x, box_y = pos[1] // 3, pos[0] // 3
        for i in range(box_y * 3, box_y * 3 + 3):
            for j in range(box_x * 3, box_x * 3 + 3):
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
                    self.errors[(row, col)] = 0
                    return True
                else:
                    self.errors[(row, col)] = self.errors.get((row, col), 0) + 1
                    logging.warning(f"Tentativa inválida: {num} em ({row},{col}) - Erros: {self.errors[(row,col)]}")
                    return False
        return True

    def is_complete(self):
        for row in self.board:
            if 0 in row:
                return False
        return True

class SudokuGame:
    def __init__(self):
        pygame.init()
        self.width, self.height = 540, 650
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Sudoku - PyGame + MySQL")
        self.font = pygame.font.SysFont("comicsansms", 40)
        self.small_font = pygame.font.SysFont("comicsansms", 24)
        self.db = MySQLRanking(host="localhost", user="root", password="root", database="sudoku_db")

        self.nome = ""
        self.dificuldade = ""
        self.phase = 1
        self.max_phases = 2
        self.board = None
        self.start_time = 0
        self.error_limit = 5
        self.show_phase_screen = False

        # Rodar tela inicial para pegar nome e dificuldade
        self.get_name_screen()
        self.choose_difficulty_screen()

        self.show_phase_screen = True
        self.run_game()

    def get_name_screen(self):
        input_box = pygame.Rect(100, 300, 340, 50)
        color_inactive = pygame.Color('lightskyblue3')
        color_active = pygame.Color('dodgerblue2')
        color = color_inactive
        active = False
        text = ''
        done = False

        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Se clicou na caixa de texto ativa ou desativa
                    if input_box.collidepoint(event.pos):
                        active = not active
                    else:
                        active = False
                    color = color_active if active else color_inactive
                if event.type == pygame.KEYDOWN:
                    if active:
                        if event.key == pygame.K_RETURN:
                            if text.strip() != '':
                                self.nome = text.strip()
                                done = True
                        elif event.key == pygame.K_BACKSPACE:
                            text = text[:-1]
                        else:
                            if len(text) < 15 and event.unicode.isprintable():
                                text += event.unicode

            self.screen.fill((230, 230, 250))
            # Texto instrução
            instr = self.small_font.render("Digite seu nome e pressione ENTER:", True, (50, 50, 100))
            self.screen.blit(instr, (100, 260))
            # Caixa de texto
            pygame.draw.rect(self.screen, color, input_box, 2)
            txt_surface = self.font.render(text, True, (0, 0, 0))
            self.screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
            pygame.display.flip()

    def choose_difficulty_screen(self):
        # Botões para dificuldade
        button_easy = pygame.Rect(120, 300, 100, 50)
        button_medium = pygame.Rect(220, 300, 100, 50)
        button_hard = pygame.Rect(320, 300, 100, 50)

        done = False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    if button_easy.collidepoint(pos):
                        self.dificuldade = "fácil"
                        done = True
                    elif button_medium.collidepoint(pos):
                        self.dificuldade = "médio"
                        done = True
                    elif button_hard.collidepoint(pos):
                        self.dificuldade = "difícil"
                        done = True

            self.screen.fill((230, 230, 250))
            instr = self.small_font.render("Escolha a dificuldade:", True, (50, 50, 100))
            self.screen.blit(instr, (180, 260))

            pygame.draw.rect(self.screen, (100, 200, 100), button_easy)
            pygame.draw.rect(self.screen, (200, 200, 50), button_medium)
            pygame.draw.rect(self.screen, (200, 100, 100), button_hard)

            text_easy = self.small_font.render("Fácil", True, (0, 0, 0))
            text_medium = self.small_font.render("Médio", True, (0, 0, 0))
            text_hard = self.small_font.render("Difícil", True, (0, 0, 0))

            self.screen.blit(text_easy, (button_easy.x + 25, button_easy.y + 15))
            self.screen.blit(text_medium, (button_medium.x + 20, button_medium.y + 15))
            self.screen.blit(text_hard, (button_hard.x + 15, button_hard.y + 15))

            pygame.display.flip()

    def draw_grid(self):
        for i in range(10):
            thickness = 4 if i % 3 == 0 else 1
            color = (50, 50, 50) if i % 3 == 0 else (180, 180, 180)
            pygame.draw.line(self.screen, color, (0, i * 60), (540, i * 60), thickness)
            pygame.draw.line(self.screen, color, (i * 60, 0), (i * 60, 540), thickness)

    def draw_numbers(self):
        for i in range(9):
            for j in range(9):
                num = self.board.board[i][j]
                if num != 0:
                    color = (0, 0, 0) if self.board.original_board[i][j] != 0 else (30, 144, 255)
                    text = self.font.render(str(num), True, color)
                    self.screen.blit(text, (j * 60 + 18, i * 60 + 12))

    def highlight_cell(self):
        if self.board.selected:
            row, col = self.board.selected
            pygame.draw.rect(self.screen, (255, 255, 100), (col * 60, row * 60, 60, 60), 4)

    def click_cell(self, pos):
        x, y = pos
        if x < 540 and y < 540:
            col, row = x // 60, y // 60
            self.board.selected = (row, col)

    def show_ranking(self):
        scores = self.db.get_top_scores(self.dificuldade)
        y = 560
        for idx, (nome, tempo) in enumerate(scores, 1):
            text = self.small_font.render(f"{idx}. {nome} - {tempo:.2f}s", True, (0, 0, 128))
            self.screen.blit(text, (20, y))
            y += 25

    def show_phase_info(self):
        self.screen.fill((240, 240, 255))
        msg = self.font.render(f"Fase {self.phase} / {self.max_phases}", True, (70, 70, 200))
        self.screen.blit(msg, (540 // 2 - msg.get_width() // 2, 300))
        pygame.display.flip()
        pygame.time.wait(1500)
        self.show_phase_screen = False
        self.start_time = time.time()

    def game_over_screen(self):
        running = True
        while running:
            self.screen.fill((200, 50, 50))
            title = self.font.render("Game Over!", True, (255, 255, 255))
            msg = self.small_font.render(f"Erros demais! Você perdeu.", True, (255, 255, 255))
            info = self.small_font.render("Pressione ESC para sair.", True, (255, 255, 255))
            self.screen.blit(title, (540 // 2 - title.get_width() // 2, 250))
            self.screen.blit(msg, (540 // 2 - msg.get_width() // 2, 310))
            self.screen.blit(info, (540 // 2 - info.get_width() // 2, 360))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

        pygame.quit()
        sys.exit()

    def next_phase(self):
        if self.phase < self.max_phases:
            self.phase += 1
            self.board = SudokuBoard(self.dificuldade)
            self.show_phase_screen = True
        else:
            tempo_total = time.time() - self.start_time
            if self.db:
                self.db.add_score(self.nome, self.dificuldade, tempo_total)

            running = True
            while running:
                self.screen.fill((255, 255, 255))
                title = self.font.render("🏆 Parabéns!", True, (0, 128, 0))
                msg = self.small_font.render(f"{self.nome}, tempo total: {tempo_total:.2f}s", True, (0, 0, 0))
                info = self.small_font.render("Pressione ESC para sair.", True, (128, 0, 0))
                self.screen.blit(title, (150, 250))
                self.screen.blit(msg, (150, 320))
                self.screen.blit(info, (120, 380))
                pygame.display.flip()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        running = False

            pygame.quit()
            sys.exit()

    def run_game(self):
        clock = pygame.time.Clock()
        self.board = SudokuBoard(self.dificuldade)
        self.start_time = time.time()

        while True:
            if self.show_phase_screen:
                self.show_phase_info()

            self.screen.fill((250, 250, 250))
            self.draw_grid()
            self.draw_numbers()
            self.highlight_cell()

            tempo_jogo = time.time() - self.start_time
            tempo_text = self.small_font.render(f"Tempo: {tempo_jogo:.1f}s | Fase {self.phase}", True, (50, 100, 50))
            self.screen.blit(tempo_text, (10, 550))

            if self.board.selected:
                erros = self.board.errors.get(self.board.selected, 0)
                error_text = self.small_font.render(f"Erros nesta célula: {erros} / {self.error_limit}", True, (180, 30, 30))
                self.screen.blit(error_text, (320, 550))
                if erros >= self.error_limit:
                    self.game_over_screen()

            if self.board.is_complete():
                win_text = self.font.render("Fase completa!", True, (0, 128, 0))
                self.screen.blit(win_text, (150, 580))
                pygame.display.flip()
                pygame.time.wait(2000)
                self.next_phase()
                continue

            self.show_ranking()

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
                            ok = self.board.place_number(num)
                            if not ok:
                                pass

            pygame.display.flip()
            clock.tick(30)

if __name__ == "__main__":
    try:
        SudokuGame()
    except Exception as e:
        logging.error(f"Erro fatal: {e}")
        pygame.quit()
        sys.exit()
