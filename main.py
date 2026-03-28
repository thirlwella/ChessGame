import os
import pygame
import chess
import chess.engine
import engine

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
PIECE_SETS = [
    {
        "name": "BW Classic",
        "path": "assets/classic_bw",
        "scale": 0.470,
    },
    {
        "name": "Blue Classic",
        "path": "assets/classic",
        "scale": 0.470,
    },
    {
        "name": "Lewis",
        "path": "assets/lewis",
        "scale": 0.80,
    }
]

# Stockfish path
STOCKFISH_PATH = "stockfish/stockfish-windows-x86-64-avx2.exe"

THEMES = [
    {
        "name": "Default",
        "background_top": (82, 82, 82),
        "background_bottom": (0, 0, 0),
        "board_light": (228, 238, 245),
        "board_dark": (127,127,127),
        "board_border": (65, 82, 96),
        "highlight": (204, 204, 204),
        "hud_bg": (108, 108, 108),
        "hud_border": (97, 97, 97),
        "hud_text": (18, 31, 54),
    },
    {
        "name": "Cyrus Blue",
        "background_top": (148, 171, 200),
        "background_bottom": (203, 216, 234),
        "board_light": (228, 238, 245),
        "board_dark": (54, 105, 196),
        "board_border": (19, 31, 72),
        "highlight": (167, 194, 255),
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
        "hud_bg": (229, 217, 190),
        "hud_border": (112, 75, 28),
        "hud_text": (67, 43, 13),
    },
]


class ChessGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess")
        self.clock = pygame.time.Clock()
        self.board = chess.Board()
        self.selected_square = None
        self.valid_moves = []
        self.engine = None
        self.ai_color = chess.BLACK
        self.perspective = chess.WHITE  # Perspective follows the human player
        self.theme_index = 0
        self.theme = THEMES[self.theme_index]
        self.piece_set_index = 0
        self.piece_set = PIECE_SETS[self.piece_set_index]

        self.pixel_font = pygame.font.SysFont("Consolas", 16, bold=True)
        self.small_font = pygame.font.SysFont("Consolas", 12, bold=True)
        self.title_font = pygame.font.SysFont("Consolas", 22, bold=True)

        self.board_rect = pygame.Rect(BOARD_LEFT, BOARD_TOP, BOARD_PIXELS, BOARD_PIXELS)
        self.bottom_bar_rect = pygame.Rect(40, HEIGHT - BOTTOM_BAR_HEIGHT - 30, WIDTH - 80, BOTTOM_BAR_HEIGHT)

        self.piece_sprites = {}
        self.setup_engine()
        self.generate_piece_sprites()

        # Animation state
        self.moving_piece = None  # (piece, from_sq, to_sq)
        self.animation_start = 0
        self.animation_duration = 1  # seconds

        # UI Buttons (using engine.py)
        self.setup_buttons()

    def setup_buttons(self):
        theme_colors = self.get_engine_theme_colors()
        
        # Bottom Bar Buttons
        bar = self.bottom_bar_rect
        btn_y = bar.top + 15
        btn_h = 30
        
        self.theme_btn = engine.Button(
            self.screen, f"THEME: {self.theme['name']}", "cycle_theme",
            bar.left + 20, btn_y, 210, btn_h,
            custom_colors=theme_colors
        )
        
        self.set_btn = engine.Button(
            self.screen, f"SET: {self.piece_set['name']}", "cycle_set",
            bar.left + 20, btn_y + 35, 210, btn_h,
            custom_colors=theme_colors
        )

        # Combined Game Controls Button
        self.game_btn = engine.Button(
            self.screen, "RESET", "game_menu",
            bar.right - 230, btn_y, 210, btn_h + 35,
            custom_colors=theme_colors
        )

        # Top Right Button (Legacy / Redundant but keeping structure for now)
        self.new_game_btn = engine.Button(
            self.screen, "NEW GAME", "new_game",
            WIDTH - 180, 20, 160, 40,
            custom_colors=theme_colors
        )


    def get_perspective_pos(self, col, row):
        # col, row are 0-7 visual coordinates (0,0 is top-left)
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
        # row is 0-7 visual coordinate (0 is top/back)
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
            # Default difficulty: Easy (Skill Level: 0)
            self.engine.configure({"Skill Level": 0})
        except Exception as exc:
            print(f"Failed to load engine: {exc}")

    def reset_game(self):
        self.board.reset()
        self.selected_square = None
        self.valid_moves = []

    def get_engine_theme_colors(self):
        engine_font = pygame.freetype.SysFont("Consolas", 14)

        return {
            "font_colour": self.theme["hud_text"],
            "colour": self.theme["hud_bg"],
            "colour_on": self.theme["highlight"],
            "border_colour": self.theme["hud_border"],
            "header_text_color": self.theme["hud_bg"],
            "header_background": self.theme["hud_border"],
            "dialogue_font_size": 14,
            "font": engine_font
        }

    def cycle_theme(self):
        self.theme_index = (self.theme_index + 1) % len(THEMES)
        self.theme = THEMES[self.theme_index]
        self.generate_piece_sprites()
        
        # Refresh all buttons
        self.setup_buttons()

    def cycle_piece_set(self):
        self.piece_set_index = (self.piece_set_index + 1) % len(PIECE_SETS)
        self.piece_set = PIECE_SETS[self.piece_set_index]
        self.load_piece_sprites()
        
        # Refresh buttons (to update set name)
        self.setup_buttons()

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
                path = os.path.join(self.piece_set["path"], filename)
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
        
        turn_text = "WHITE TO MOVE" if self.board.turn == chess.WHITE else "BLACK TO MOVE"
        if self.board.turn != self.ai_color:
            return f"YOUR TURN ({turn_text})"
        return turn_text

    def draw_background(self):
        self.draw_vertical_gradient(
            pygame.Rect(0, 0, WIDTH, HEIGHT),
            self.theme["background_top"],
            self.theme["background_bottom"],
        )

    def draw_board_frame(self):
        # Increased spacing for smaller font and cleaner look
        outer_rect = self.board_rect.inflate(24, 24)
        pygame.draw.rect(self.screen, self.theme["board_border"], outer_rect, border_radius=6)
        pygame.draw.rect(self.screen, self.theme["hud_bg"], self.board_rect.inflate(12, 12), border_radius=4)

    def draw_board(self):

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                # Map visual col, row to chess square
                if self.perspective == chess.WHITE:
                    square = chess.square(col, 7 - row)
                else:
                    square = chess.square(7 - col, row)

                color = self.theme["board_light"] if (row + col) % 2 == 0 else self.theme["board_dark"]

                if self.selected_square == square:
                    if (row + col) % 2 == 0:
                        color = self.theme["highlight"]
                    else:
                        # Darken highlight for dark squares
                        h = self.theme["highlight"]
                        color = (max(0, h[0] - 20), max(0, h[1] - 20), max(0, h[2] - 20))

                # Get 4 corners of the square in perspective
                p1 = self.get_perspective_pos(col - 0.5, row - 0.5)
                p2 = self.get_perspective_pos(col + 0.5, row - 0.5)
                p3 = self.get_perspective_pos(col + 0.5, row + 0.5)
                p4 = self.get_perspective_pos(col - 0.5, row + 0.5)
                
                # Draw square polygon
                pygame.draw.polygon(self.screen, color, [p1, p2, p3, p4])
                
        for move in self.valid_moves:
            # move.to_square is a chess.Square
            # We need to find its visual col, row
            if self.perspective == chess.WHITE:
                col = chess.square_file(move.to_square)
                row = 7 - chess.square_rank(move.to_square)
            else:
                col = 7 - chess.square_file(move.to_square)
                row = chess.square_rank(move.to_square)

            if (row + col) % 2 == 0:
                color = self.theme["highlight"]
            else:
                h = self.theme["highlight"]
                color = (max(0, h[0] - 20), max(0, h[1] - 20), max(0, h[2] - 20))

            # Get 4 corners of the square in perspective
            p1 = self.get_perspective_pos(col - 0.5, row - 0.5)
            p2 = self.get_perspective_pos(col + 0.5, row - 0.5)
            p3 = self.get_perspective_pos(col + 0.5, row + 0.5)
            p4 = self.get_perspective_pos(col - 0.5, row + 0.5)

            # Draw square polygon
            pygame.draw.polygon(self.screen, color, [p1, p2, p3, p4])

    def draw_pieces(self):
        # Draw in order from top rows to bottom rows for proper 3D stacking
        # row in loop is visual row from top to bottom
        for row in range(8):
            for col in range(8):
                # We need to find which square is at this visual (col, row)
                # If perspective is WHITE: col 0 is file A, row 0 is rank 8 (chess.square(0, 7))
                # If perspective is BLACK: col 0 is file H, row 0 is rank 1 (chess.square(7, 0))
                
                if self.perspective == chess.WHITE:
                    square = chess.square(col, 7 - row)
                else:
                    square = chess.square(7 - col, row)

                if self.moving_piece and square == self.moving_piece[2]:
                    # Don't draw the piece that is currently animating into this square
                    # but if there's a different piece here already (not the one moving)
                    # it means we are in the middle of animation but the board is updated
                    pass

                piece = self.board.piece_at(square)
                if not piece:
                    continue
                
                # Skip the piece that is currently being animated (it will be drawn separately)
                if self.moving_piece and square == self.moving_piece[2] and piece == self.moving_piece[0]:
                    continue

                pos = self.get_perspective_pos(col, row)
                scale = self.get_perspective_scale(row)
                self.draw_piece(piece, pos, scale, row)

        # Draw animating piece last (so it's on top)
        if self.moving_piece:
            piece, from_sq, to_sq = self.moving_piece
            elapsed = (pygame.time.get_ticks() / 1000) - self.animation_start
            t = min(1.0, elapsed / self.animation_duration)
            
            # Get start/end visual coordinates
            if self.perspective == chess.WHITE:
                from_col, from_row = chess.square_file(from_sq), 7 - chess.square_rank(from_sq)
                to_col, to_row = chess.square_file(to_sq), 7 - chess.square_rank(to_sq)
            else:
                from_col, from_row = 7 - chess.square_file(from_sq), chess.square_rank(from_sq)
                to_col, to_row = 7 - chess.square_file(to_sq), chess.square_rank(to_sq)

            # Interpolate visual position
            current_col = from_col + (to_col - from_col) * t
            current_row = from_row + (to_row - from_row) * t
            
            pos = self.get_perspective_pos(current_col, current_row)
            scale = self.get_perspective_scale(current_row)
            self.draw_piece(piece, pos, scale, current_row)
            
            if t >= 1.0:
                self.moving_piece = None

    def draw_piece(self, piece, pos, scale, row):
        sprite = self.piece_sprites[(piece.color, piece.piece_type)]
        
        # Scale sprite based on perspective and global scale factor
        orig_size = sprite.get_size()
        final_scale = scale * self.piece_set["scale"]
        new_size = (int(orig_size[0] * final_scale), int(orig_size[1] * final_scale))
        scaled_sprite = pygame.transform.smoothscale(sprite, new_size)
        
        # Adjust position so the base of the piece sits on the square
        # row can be a float during animation, which is fine
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

        # Status text
        status_text = self.pixel_font.render(self.get_status_text(), True, self.theme["hud_text"])
        self.screen.blit(status_text, status_text.get_rect(center=(mid_x, bar.top + 28)))
        
        # Draw last moves (Stockfish interaction)
        last_moves = self.board.move_stack[-12:]
        if last_moves:
            move_texts = []
            
            # We'll use a temp board to generate SAN for the last few moves.
            temp_board = chess.Board()
            for m in self.board.move_stack[:-len(last_moves)]:
                temp_board.push(m)
            
            for i, m in enumerate(last_moves):
                san = temp_board.san(m)
                temp_board.push(m)
                move_texts.append(san)
            
            # Draw moves in multiple lines
            line1_moves = move_texts[:6]
            line2_moves = move_texts[6:]
            
            if line1_moves:
                moves_str1 = " | ".join(line1_moves)
                moves_info1 = self.small_font.render(moves_str1, True, self.theme["hud_text"])
                self.screen.blit(moves_info1, moves_info1.get_rect(center=(mid_x, bar.top + 60)))
            
            if line2_moves:
                moves_str2 = " | ".join(line2_moves)
                moves_info2 = self.small_font.render(moves_str2, True, self.theme["hud_text"])
                self.screen.blit(moves_info2, moves_info2.get_rect(center=(mid_x, bar.top + 80)))

        # Draw engine buttons
        self.theme_btn.button_draw()
        self.set_btn.button_draw()
        self.game_btn.button_draw()

    def draw_title(self):
        title = self.title_font.render("CHESS", True, self.theme["hud_text"])
        self.screen.blit(title, ((WIDTH - title.get_width()) // 2, 25))

    def make_ai_move(self):
        if self.engine and self.board.turn == self.ai_color and not self.board.is_game_over() and not self.moving_piece:
            result = self.engine.play(self.board, chess.engine.Limit(time=0.15))
            move = result.move
            piece = self.board.piece_at(move.from_square)
            self.moving_piece = (piece, move.from_square, move.to_square)
            self.animation_start = pygame.time.get_ticks() / 1000
            self.board.push(move)

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
            # Map visual col, row to chess square
            if self.perspective == chess.WHITE:
                return chess.square(col, 7 - row)
            else:
                return chess.square(7 - col, row)
        return None

    def handle_click(self, mouse_pos):
        # Handle engine buttons
        # Note: check_if_pressed handles the button_switch (active toggle) internally
        self.theme_btn.check_if_pressed(mouse_pos)
        if self.theme_btn.over:
            if self.theme_btn.text_return == "cycle_theme":
                # Already toggled by check_if_pressed
                self.cycle_theme()
                return

        self.set_btn.check_if_pressed(mouse_pos)
        if self.set_btn.over:
            if self.set_btn.text_return == "cycle_set":
                # Already toggled by check_if_pressed
                self.cycle_piece_set()
                return

        self.game_btn.check_if_pressed(mouse_pos)
        if self.game_btn.over:
            if self.game_btn.text_return == "game_menu":
                # Already toggled by check_if_pressed
                self.open_game_menu()
                return

        square = self.get_square_under_mouse()
        if square is None or self.board.is_game_over() or self.board.turn == self.ai_color:
            return

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = square
                self.valid_moves = [move for move in self.board.legal_moves if move.from_square == square]
            return

        move = chess.Move(self.selected_square, square)
        final_move = None

        if move in self.board.legal_moves:
            final_move = move
        else:
            queen_promotion = chess.Move(self.selected_square, square, promotion=chess.QUEEN)
            if queen_promotion in self.board.legal_moves:
                final_move = queen_promotion
            else:
                piece = self.board.piece_at(square)
                if piece and piece.color == self.board.turn:
                    self.selected_square = square
                    self.valid_moves = [move for move in self.board.legal_moves if move.from_square == square]
                    return

        if final_move:
            piece = self.board.piece_at(final_move.from_square)
            self.moving_piece = (piece, final_move.from_square, final_move.to_square)
            self.animation_start = pygame.time.get_ticks() / 1000
            self.board.push(final_move)

        self.selected_square = None
        self.valid_moves = []

    def draw_all(self):
        self.draw_background()
        self.draw_title()
        self.draw_board()
        self.draw_pieces()
        self.draw_bottom_bar()

    def open_game_menu(self):
        # Directly call start_new_game_ui
        self.start_new_game_ui()
        
        # Ensure the button state is reset visually
        self.game_btn.active = False
        self.game_btn.button_colour = self.game_btn.colour

    def start_new_game_ui(self):
        theme_colors = self.get_engine_theme_colors()
        
        # 1. Ask for Difficulty using Menu_List
        # Need a temporary button for Menu_List to anchor to
        temp_btn = engine.Button(self.screen, "DIFFICULTY", "diff", WIDTH // 2 - 80, HEIGHT // 2 - 20, 160, 40, hidden=True, custom_colors=theme_colors)
        choices = ["Easy", "Medium", "Hard", "Cancel"]
        diff_menu = engine.Menu_List(self.screen, temp_btn, choices, hidden=False, custom_colors=theme_colors)
        diff_menu.activate_list()
        
        # Initial redraw
        self.draw_all()
        pygame.display.flip()

        diff_menu.like_dialogue(redraw_callback=self.draw_all)
        
        selection = diff_menu.text_return
        if not selection or selection == "Cancel" or selection == "shutdown" or selection == "click":
            return

        if self.engine:
            if selection == "Easy":
                self.engine.configure({"Skill Level": 0})
            elif selection == "Medium":
                self.engine.configure({"Skill Level": 10})
            elif selection == "Hard":
                self.engine.configure({"Skill Level": 20})
        
        # Redraw before next menu
        self.draw_all()
        pygame.display.flip()

        # 2. Ask for Color (White/Black)
        # Using Dialogue from engine.py
        color_dialogue = engine.Dialogue(self.screen, "PICK COLOR", ["Would you like to play", "as White?"], "choice", dialogue_type="yes_no", custom_colors=theme_colors, redraw_callback=self.draw_all)
        # yes_no returns "ok" for Yes and "no" for No
        if color_dialogue.text_return == "ok":
            self.ai_color = chess.BLACK
            self.perspective = chess.WHITE
        elif color_dialogue.text_return == "no":
            self.ai_color = chess.WHITE
            self.perspective = chess.BLACK
        else:
            return # User closed or cancelled

        # Start game
        self.reset_game()

    def handle_keydown(self, event):
        if event.key == pygame.K_r:
            self.reset_game()
        elif event.key == pygame.K_t:
            self.cycle_theme()
        elif event.key == pygame.K_s:
            self.cycle_piece_set()

    def run(self):
        running = True

        while running:
            # AI Move logic
            if self.board.turn == self.ai_color and not self.board.is_game_over():
                self.make_ai_move()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)

            self.draw_all()

            # Update button highlights
            mouse_pos = pygame.mouse.get_pos()
            self.theme_btn.check_if_over(mouse_pos)
            self.set_btn.check_if_over(mouse_pos)
            self.game_btn.check_if_over(mouse_pos)

            pygame.display.flip()
            self.clock.tick(FPS)

        if self.engine:
            self.engine.quit()
        pygame.quit()


if __name__ == "__main__":
    game = ChessGame()
    game.run()