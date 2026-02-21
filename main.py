import pygame
import chess
import chess.engine
import os

# Configuration
WIDTH, HEIGHT = 800, 600
BOARD_SIZE = 8
SQUARE_SIZE = 600 // BOARD_SIZE
FPS = 60

# Stockfish path - Adjust this to your local Stockfish executable path
STOCKFISH_PATH = "stockfish/stockfish-windows-x86-64-avx2.exe"

# Colors
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT_COLOR = (186, 202, 68)
TEXT_COLOR = (255, 255, 255)

class ChessGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess with Stockfish")
        self.clock = pygame.time.Clock()
        self.board = chess.Board()
        self.selected_square = None
        self.valid_moves = []
        self.engine = None
        self.ai_color = chess.BLACK
        self.is_game_over = False
        self.setup_engine()
        self.font = pygame.font.SysFont("Arial", 40)
        self.small_font = pygame.font.SysFont("Arial", 24)

    def setup_engine(self):
        if os.path.exists(STOCKFISH_PATH):
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
            except Exception as e:
                print(f"Failed to load engine: {e}")
        else:
            print(f"Stockfish not found at {STOCKFISH_PATH}. AI moves will be disabled.")

    def draw_sidebar(self):
        sidebar_rect = pygame.Rect(600, 0, 200, 600)
        pygame.draw.rect(self.screen, (50, 50, 50), sidebar_rect)
        
        turn_text = "White's Turn" if self.board.turn == chess.WHITE else "Black's Turn"
        if self.board.is_checkmate():
            turn_text = "Checkmate!"
        elif self.board.is_stalemate():
            turn_text = "Stalemate!"
        elif self.board.is_insufficient_material():
            turn_text = "Insufficient Material"
        elif self.board.is_fivefold_repetition() or self.board.is_seventyfive_moves():
            turn_text = "Draw (Repetition/75 Moves)"
        elif self.board.is_game_over():
            turn_text = "Game Over"

        text_surface = self.small_font.render(turn_text, True, TEXT_COLOR)
        self.screen.blit(text_surface, (610, 20))
        
        ai_info = "AI: Enabled" if self.engine else "AI: Disabled (Binary missing)"
        ai_surface = self.small_font.render(ai_info, True, (200, 200, 200))
        self.screen.blit(ai_surface, (610, 60))
        
        if self.engine:
            color_text = "AI is Black" if self.ai_color == chess.BLACK else "AI is White"
            color_surface = self.small_font.render(color_text, True, (200, 200, 200))
            self.screen.blit(color_surface, (610, 90))

    def make_ai_move(self):
        if self.engine and self.board.turn == self.ai_color and not self.board.is_game_over():
            result = self.engine.play(self.board, chess.engine.Limit(time=0.1))
            self.board.push(result.move)

    def draw_board(self):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                
                # Highlight selected square
                if self.selected_square is not None:
                    s_row, s_col = 7 - chess.square_rank(self.selected_square), chess.square_file(self.selected_square)
                    if row == s_row and col == s_col:
                        color = HIGHLIGHT_COLOR
                
                pygame.draw.rect(self.screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
                
                # Highlight valid moves
                for move in self.valid_moves:
                    if move.to_square == chess.square(col, 7 - row):
                        pygame.draw.circle(self.screen, (0, 0, 0, 50), 
                                         (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), 
                                         SQUARE_SIZE // 6)

    def draw_pieces(self):
        # Temporary piece drawing using text until images are ready
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                symbol = piece.symbol()
                color = (255, 255, 255) if piece.color == chess.WHITE else (0, 0, 0)
                text_surface = self.font.render(symbol, True, color)
                
                col = chess.square_file(square)
                row = 7 - chess.square_rank(square)
                
                text_rect = text_surface.get_rect(center=(col * SQUARE_SIZE + SQUARE_SIZE // 2, 
                                                         row * SQUARE_SIZE + SQUARE_SIZE // 2))
                self.screen.blit(text_surface, text_rect)

    def get_square_under_mouse(self):
        mouse_pos = pygame.mouse.get_pos()
        col = mouse_pos[0] // SQUARE_SIZE
        row = 7 - (mouse_pos[1] // SQUARE_SIZE)
        if 0 <= col < 8 and 0 <= row < 8:
            return chess.square(col, row)
        return None

    def handle_click(self, square):
        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = square
                self.valid_moves = [move for move in self.board.legal_moves if move.from_square == square]
        else:
            move = chess.Move(self.selected_square, square)
            
            # Pawn promotion handling (defaulting to Queen for simplicity)
            if move in self.board.legal_moves:
                self.board.push(move)
            elif chess.Move(self.selected_square, square, promotion=chess.QUEEN) in self.board.legal_moves:
                self.board.push(chess.Move(self.selected_square, square, promotion=chess.QUEEN))
                
            self.selected_square = None
            self.valid_moves = []

    def run(self):
        running = True
        while running:
            # AI Move
            if self.board.turn == self.ai_color and not self.board.is_game_over():
                self.make_ai_move()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and self.board.turn != self.ai_color:
                    square = self.get_square_under_mouse()
                    if square is not None:
                        self.handle_click(square)

            self.screen.fill((0, 0, 0))
            self.draw_board()
            self.draw_pieces()
            self.draw_sidebar()
            pygame.display.flip()
            self.clock.tick(FPS)
        
        if self.engine:
            self.engine.quit()
        pygame.quit()

if __name__ == "__main__":
    game = ChessGame()
    game.run()
