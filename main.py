import os
import pygame
import chess
import chess.engine

# Configuration
WIDTH, HEIGHT = 1000, 750
FPS = 60
BOARD_SIZE = 8
BOARD_PIXELS = 600
BOARD_LEFT = (WIDTH - BOARD_PIXELS) // 2
BOARD_TOP = 120
BOTTOM_BAR_HEIGHT = 100
SQUARE_SIZE = BOARD_PIXELS // BOARD_SIZE

# Perspective settings
PERSPECTIVE_SCALE = 0.5  # Tapering factor at the top (0.5 means top is half as wide as bottom)
PERSPECTIVE_OFFSET_Y = 160 # Extra vertical squeeze for 3D look
BOARD_BOTTOM_WIDTH = 800
BOARD_TOP_WIDTH = 550
BOARD_HEIGHT = 380
BOARD_CENTER_X = WIDTH // 2
BOARD_CENTER_Y = 340
PIECE_SCALE_FACTOR = 0.470  # Overall size reduction for sprites

# Stockfish path
STOCKFISH_PATH = "stockfish/stockfish-windows-x86-64-avx2.exe"

THEMES = [
    {
        "name": "Cyrus Blue",
        "background_top": (148, 171, 200),
        "background_bottom": (203, 216, 234),
        "board_light": (228, 238, 245),
        "board_dark": (54, 105, 196),
        "board_border": (19, 31, 72),
        "highlight": (167, 194, 255),
        "move_dot": (18, 34, 79),
        "hud_bg": (210, 220, 235),
        "hud_border": (33, 52, 97),
        "hud_text": (19, 26, 54),
    },
    {
        "name": "Emerald Terminal",
        "background_top": (63, 92, 84),
        "background_bottom": (176, 199, 186),
        "board_light": (224, 237, 227),
        "board_dark": (57, 126, 99),
        "board_border": (24, 59, 46),
        "highlight": (173, 224, 195),
        "move_dot": (18, 66, 48),
        "hud_bg": (208, 224, 214),
        "hud_border": (35, 82, 63),
        "hud_text": (18, 45, 34),
    },
    {
        "name": "Amber CRT",
        "background_top": (97, 79, 51),
        "background_bottom": (221, 208, 181),
        "board_light": (245, 235, 209),
        "board_dark": (176, 125, 52),
        "board_border": (89, 55, 17),
        "highlight": (243, 210, 128),
        "move_dot": (99, 59, 19),
        "hud_bg": (229, 217, 190),
        "hud_border": (112, 75, 28),
        "hud_text": (67, 43, 13),
    },
]


class ChessGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Adam's Chess")
        self.clock = pygame.time.Clock()
        self.board = chess.Board()
        self.selected_square = None
        self.valid_moves = []
        self.engine = None
        self.ai_color = chess.BLACK
        self.theme_index = 0
        self.theme = THEMES[self.theme_index]

        self.pixel_font = pygame.font.SysFont("Consolas", 24, bold=True)
        self.small_font = pygame.font.SysFont("Consolas", 18, bold=True)
        self.title_font = pygame.font.SysFont("Consolas", 30, bold=True)

        self.board_rect = pygame.Rect(BOARD_LEFT, BOARD_TOP, BOARD_PIXELS, BOARD_PIXELS)
        self.bottom_bar_rect = pygame.Rect(40, HEIGHT - BOTTOM_BAR_HEIGHT - 30, WIDTH - 80, BOTTOM_BAR_HEIGHT)

        self.piece_sprites = {}
        self.setup_engine()
        self.generate_piece_sprites()

    def get_perspective_pos(self, col, row):
        # col, row are 0-7
        # y is from top to bottom (0 to BOARD_HEIGHT)
        y_rel = row / 7.0
        
        # Calculate width at this row
        current_width = BOARD_TOP_WIDTH + (BOARD_BOTTOM_WIDTH - BOARD_TOP_WIDTH) * y_rel
        
        # Calculate x position relative to center
        x_rel = (col - 3.5) / 4.0 # range from -1 to 1 approximately
        x = BOARD_CENTER_X + x_rel * (current_width / 2.0)
        
        # y position with some perspective squeeze
        y = BOARD_CENTER_Y - (BOARD_HEIGHT / 2.0) + (y_rel * BOARD_HEIGHT)
        
        return x, y

    def get_perspective_scale(self, row):
        y_rel = row / 7.0
        return 0.75 + 0.25 * y_rel # pieces at the back are 75% size

    def setup_engine(self):
        # Prefer stockfish in the current directory, but also try to find it in PATH
        stockfish_path = STOCKFISH_PATH
        if not os.path.exists(stockfish_path):
            import shutil
            stockfish_path = shutil.which("stockfish")
            if not stockfish_path:
                print(f"Stockfish not found at {STOCKFISH_PATH} or in PATH. AI moves will be disabled.")
                return

        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        except Exception as exc:
            print(f"Failed to load engine: {exc}")

    def reset_game(self):
        self.board.reset()
        self.selected_square = None
        self.valid_moves = []

    def cycle_theme(self):
        self.theme_index = (self.theme_index + 1) % len(THEMES)
        self.theme = THEMES[self.theme_index]
        self.generate_piece_sprites()

    def load_piece_sprites(self):
        self.piece_sprites = {}
        piece_names = {
            chess.PAWN: "pawn",
            chess.ROOK: "rook",
            chess.KNIGHT: "knight",
            chess.BISHOP: "bishop",
            chess.QUEEN: "queen",
            chess.KING: "king",
        }

        for color in (chess.WHITE, chess.BLACK):
            color_prefix = "white" if color == chess.WHITE else "black"
            for piece_type, name in piece_names.items():
                filename = f"{color_prefix}_{name}.png"
                path = os.path.join("assets", filename)
                if os.path.exists(path):
                    sprite = pygame.image.load(path).convert_alpha()
                    self.piece_sprites[(color, piece_type)] = sprite
                else:
                    print(f"Error: {path} not found. Game may be unplayable.")

    def generate_piece_sprites(self):
        self.load_piece_sprites()

    def draw_vertical_gradient(self, rect, top_color, bottom_color):
        if rect.height <= 0:
            return

        for y in range(rect.height):
            blend = y / max(1, rect.height - 1)
            color = (
                int(top_color[0] + (bottom_color[0] - top_color[0]) * blend),
                int(top_color[1] + (bottom_color[1] - top_color[1]) * blend),
                int(top_color[2] + (bottom_color[2] - top_color[2]) * blend),
            )
            pygame.draw.line(self.screen, color, (rect.left, rect.top + y), (rect.right, rect.top + y))

    def get_status_text(self):
        if self.board.is_checkmate():
            return "CHECKMATE"
        if self.board.is_stalemate():
            return "STALEMATE"
        if self.board.is_insufficient_material():
            return "DRAW: INSUFFICIENT MATERIAL"
        if self.board.is_fivefold_repetition() or self.board.is_seventyfive_moves():
            return "DRAW"
        if self.board.is_check():
            return "CHECK"
        return "WHITE TO MOVE" if self.board.turn == chess.WHITE else "BLACK TO MOVE"

    def draw_background(self):
        self.draw_vertical_gradient(
            pygame.Rect(0, 0, WIDTH, HEIGHT),
            self.theme["background_top"],
            self.theme["background_bottom"],
        )

    def draw_board_frame(self):
        outer_rect = self.board_rect.inflate(20, 20)
        pygame.draw.rect(self.screen, self.theme["board_border"], outer_rect, border_radius=6)
        pygame.draw.rect(self.screen, self.theme["hud_bg"], self.board_rect.inflate(8, 8), border_radius=4)

    def draw_board(self):

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                square = chess.square(col, 7 - row)
                color = self.theme["board_light"] if (row + col) % 2 == 0 else self.theme["board_dark"]

                if self.selected_square == square:
                    color = self.theme["highlight"]

                # Get 4 corners of the square in perspective
                p1 = self.get_perspective_pos(col - 0.5, row - 0.5)
                p2 = self.get_perspective_pos(col + 0.5, row - 0.5)
                p3 = self.get_perspective_pos(col + 0.5, row + 0.5)
                p4 = self.get_perspective_pos(col - 0.5, row + 0.5)
                
                # Draw square polygon
                pygame.draw.polygon(self.screen, color, [p1, p2, p3, p4])
                
                # Draw subtle grid lines
                #pygame.draw.aalines(self.screen, self.theme["board_border"], True, [p1, p2, p3, p4])

        for move in self.valid_moves:
            col = chess.square_file(move.to_square)
            row = 7 - chess.square_rank(move.to_square)
            #center = self.get_perspective_pos(col, row)
            #pygame.draw.circle(self.screen, self.theme["move_dot"], (int(center[0]), int(center[1])), int(SQUARE_SIZE // 8 * self.get_perspective_scale(row)))
            color = self.theme["highlight"]

            # Get 4 corners of the square in perspective
            p1 = self.get_perspective_pos(col - 0.5, row - 0.5)
            p2 = self.get_perspective_pos(col + 0.5, row - 0.5)
            p3 = self.get_perspective_pos(col + 0.5, row + 0.5)
            p4 = self.get_perspective_pos(col - 0.5, row + 0.5)

            # Draw square polygon
            pygame.draw.polygon(self.screen, color, [p1, p2, p3, p4])

    def draw_pieces(self):
        # Draw in order from top rows to bottom rows for proper 3D stacking
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                piece = self.board.piece_at(square)
                if not piece:
                    continue

                pos = self.get_perspective_pos(col, row)
                scale = self.get_perspective_scale(row)

                sprite = self.piece_sprites[(piece.color, piece.piece_type)]
                
                # Scale sprite based on perspective and global scale factor
                orig_size = sprite.get_size()
                final_scale = scale * PIECE_SCALE_FACTOR
                new_size = (int(orig_size[0] * final_scale), int(orig_size[1] * final_scale))
                scaled_sprite = pygame.transform.smoothscale(sprite, new_size)
                
                # Adjust position so the base of the piece sits on the square
                rect = scaled_sprite.get_rect(midbottom=(pos[0], pos[1] + 40 * final_scale))
                
                # Draw piece
                self.screen.blit(scaled_sprite, rect)

    def draw_bottom_bar(self):
        # Background
        pygame.draw.rect(self.screen, self.theme["hud_bg"], self.bottom_bar_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.theme["hud_border"], self.bottom_bar_rect, 4, border_radius=8)

        # Draw inner dividers
        bar = self.bottom_bar_rect
        pygame.draw.line(self.screen, self.theme["hud_border"], (bar.left + 250, bar.top), (bar.left + 250, bar.bottom), 2)
        pygame.draw.line(self.screen, self.theme["hud_border"], (bar.right - 250, bar.top), (bar.right - 250, bar.bottom), 2)

        left_x = bar.left + 24
        mid_x = bar.centerx
        right_x = bar.right - 24

        player_text = self.title_font.render("PLAYER", True, self.theme["hud_text"])
        cyrus_text = self.title_font.render("Adam", True, self.theme["hud_text"])
        status_text = self.pixel_font.render(self.get_status_text(), True, self.theme["hud_text"])

        # Render timers (mockup style)
        timer_white = self.pixel_font.render("0:00:20", True, self.theme["hud_text"])
        timer_black = self.pixel_font.render("0:00:03", True, self.theme["hud_text"])

        self.screen.blit(player_text, (left_x, bar.top + 18))
        self.screen.blit(timer_white, (left_x + 120, bar.top + 20))
        
        self.screen.blit(status_text, status_text.get_rect(center=(mid_x, bar.top + 34)))
        
        self.screen.blit(cyrus_text, (bar.right - 230, bar.top + 18))
        self.screen.blit(timer_black, (right_x - 110, bar.top + 20))

        ai_state = "AI ON" if self.engine else "AI OFF"
        theme_label = f"THEME: {self.theme['name']}"
        controls_label = "R RESET   T THEME"

        theme_info = self.small_font.render(theme_label, True, self.theme["hud_text"])
        controls_info = self.small_font.render(controls_label, True, self.theme["hud_text"])
        ai_info = self.small_font.render(ai_state, True, self.theme["hud_text"])

        self.screen.blit(theme_info, (left_x, bar.top + 65))
        self.screen.blit(controls_info, controls_info.get_rect(center=(mid_x, bar.top + 75)))
        self.screen.blit(ai_info, (right_x - 80, bar.top + 65))

    def draw_title(self):
        title = self.title_font.render("ADAM'S CHESS", True, self.theme["hud_text"])
        self.screen.blit(title, ((WIDTH - title.get_width()) // 2, 25))

    def make_ai_move(self):
        if self.engine and self.board.turn == self.ai_color and not self.board.is_game_over():
            result = self.engine.play(self.board, chess.engine.Limit(time=0.15))
            self.board.push(result.move)

    def get_square_under_mouse(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Simple iterative closest point search for perspective board
        best_square = None
        min_dist = 1000000
        
        for row in range(8):
            for col in range(8):
                pos = self.get_perspective_pos(col, row)
                dist = (pos[0] - mouse_x)**2 + (pos[1] - mouse_y)**2
                if dist < min_dist:
                    min_dist = dist
                    best_square = (col, row)
        
        if min_dist < (SQUARE_SIZE * 0.8)**2:
            col, row = best_square
            return chess.square(col, 7 - row)
        return None

    def handle_click(self, square):
        if square is None or self.board.is_game_over():
            return

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = square
                self.valid_moves = [move for move in self.board.legal_moves if move.from_square == square]
            return

        move = chess.Move(self.selected_square, square)

        if move in self.board.legal_moves:
            self.board.push(move)
        else:
            queen_promotion = chess.Move(self.selected_square, square, promotion=chess.QUEEN)
            if queen_promotion in self.board.legal_moves:
                self.board.push(queen_promotion)
            else:
                piece = self.board.piece_at(square)
                if piece and piece.color == self.board.turn:
                    self.selected_square = square
                    self.valid_moves = [move for move in self.board.legal_moves if move.from_square == square]
                    return

        self.selected_square = None
        self.valid_moves = []

    def handle_keydown(self, event):
        if event.key == pygame.K_r:
            self.reset_game()
        elif event.key == pygame.K_t:
            self.cycle_theme()

    def run(self):
        running = True

        while running:
            if self.board.turn == self.ai_color and not self.board.is_game_over():
                self.make_ai_move()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event)
                elif event.type == pygame.MOUSEBUTTONDOWN and self.board.turn != self.ai_color:
                    self.handle_click(self.get_square_under_mouse())

            self.draw_background()
            self.draw_title()
            self.draw_board()
            self.draw_pieces()
            self.draw_bottom_bar()

            pygame.display.flip()
            self.clock.tick(FPS)

        if self.engine:
            self.engine.quit()
        pygame.quit()


if __name__ == "__main__":
    game = ChessGame()
    game.run()