# Chess with 3D Perspective

A stylish, interactive Chess game built with Python and Pygame, featuring a pseudo-3D perspective board, multiple themes, and integration with the Stockfish chess engine for AI play.

![Chess Gameplay Placeholder](https://via.placeholder.com/800x600?text=Chess+with+3D+Perspective+Gameplay)

## Features

- **Pseudo-3D Perspective:** A unique tapered board view for a more immersive experience.
- **Smooth Animations:** Pieces slide fluidly between squares rather than jumping instantly.
- **Stockfish AI Integration:** Play against one of the world's strongest chess engines with adjustable difficulty levels.
- **Multiple Themes:** Switch between different color schemes (Default, Cyrus Blue, Emerald Terminal, Amber CRT).
- **Custom Piece Sets:** Choose between different piece styles, including BW Classic, Blue Classic, and Lewis.
- **Intuitive UI:** Easy-to-use buttons for changing themes, piece sets, and starting new games.
- **Legal Move Highlighting:** Displays all valid moves for the selected piece, with darkened highlights on dark squares for better visibility.

## Installation

### Prerequisites

- Python 3.x
- [Pygame](https://www.pygame.org/)
- [python-chess](https://python-chess.readthedocs.io/)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/Chess.git
   cd Chess
   ```

2. **Install dependencies:**
   ```bash
   pip install pygame python-chess
   ```

3. **Stockfish Engine:**
   The project includes a Stockfish binary for Windows in the `stockfish/` directory. If you are on another operating system, you may need to download the appropriate Stockfish binary and update the `STOCKFISH_PATH` in `main.py`.

## How to Play

1. **Run the game:**
   ```bash
   python main.py
   ```

2. **Controls:**
   - **Select a piece:** Click on a piece of your color.
   - **Move a piece:** Click on a highlighted valid move square.
   - **Cycle Theme:** Click the "THEME" button in the bottom bar.
   - **Cycle Piece Set:** Click the "SET" button in the bottom bar.
   - **New Game:** Click the "RESET" button to configure a new game (Difficulty and Color).

## Project Structure

- `main.py`: The entry point and main game logic (rendering, input handling, animation).
- `engine.py`: UI components (Buttons, Dialogues, Menus).
- `assets/`: Directory containing piece sprites for different sets.
- `stockfish/`: Contains the Stockfish engine binary.

## Credits

- Developed with Python, Pygame, and python-chess.
- Stockfish Engine by the Stockfish team.
- Piece assets: Classic and Lewis sets.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*This project was developed with AI assistance and reviewed by the user.*
