import sys
import random
from typing import List, Optional, Tuple

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox
)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import QTimer, Qt, QRectF


def generate_knights_tour_nxn(start_x: int, start_y: int, board_size: int, max_attempts: int = 100) -> Optional[List[List[int]]]:
    KNIGHT_MOVES = [(-2, -1), (-1, -2), (1, -2), (2, -1),
                    (2, 1), (1, 2), (-1, 2), (-2, 1)]

    def is_valid(x: int, y: int, board: List[List[int]]) -> bool:
        return 0 <= x < board_size and 0 <= y < board_size and board[y][x] == -1

    def count_onward_moves(x: int, y: int, board: List[List[int]]) -> int:
        count = 0
        for dx, dy in KNIGHT_MOVES:
            if is_valid(x + dx, y + dy, board):
                count += 1
        return count

    for attempt in range(max_attempts):
        board = [[-1 for _ in range(board_size)] for _ in range(board_size)]
        x, y = start_x, start_y
        board[y][x] = 1

        for move_no in range(2, board_size * board_size + 1):
            random.shuffle(KNIGHT_MOVES)
            min_deg = 9
            next_move: Optional[Tuple[int, int]] = None

            for dx, dy in KNIGHT_MOVES:
                nx, ny = x + dx, y + dy
                if is_valid(nx, ny, board):
                    deg = count_onward_moves(nx, ny, board)
                    if deg < min_deg:
                        min_deg = deg
                        next_move = (nx, ny)

            if not next_move:
                break

            x, y = next_move
            board[y][x] = move_no
        else:
            return board
    return None


class BoardWidget(QWidget):
    def __init__(self, board_size: int, square_size: int, board_data: List[List[int]]):
        super().__init__()
        self.board_size = board_size
        self.square_size = square_size
        self.board_data = board_data  # 2D list with move numbers
        self.current_pos = (0, 0)     # (x, y) current knight position
        self.prev_pos = None          # previous knight position
        self.move_numbers = {}        # squares that should show numbers after knight leaves
        self.knight_pixmap = QPixmap("knight.png").scaled(square_size - 10, square_size - 10, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setFixedSize(board_size * square_size, board_size * square_size)

    def set_knight_position(self, x: int, y: int, prev_x: Optional[int] = None, prev_y: Optional[int] = None, move_number: Optional[int] = None):
        self.current_pos = (x, y)
        if prev_x is not None and prev_y is not None and move_number is not None:
            self.move_numbers[(prev_x, prev_y)] = move_number
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        # Draw the big board background (optional)
        painter.fillRect(0, 0, self.width(), self.height(), QColor(230, 230, 230))

        # Draw all small squares inside the big board, same color
        square_color = QColor(180, 210, 230)
        pen_color = QColor(150, 180, 210)
        painter.setPen(pen_color)

        for row in range(self.board_size):
            for col in range(self.board_size):
                rect = QRectF(col * self.square_size, row * self.square_size, self.square_size, self.square_size)
                painter.fillRect(rect, square_color)
                painter.drawRect(rect)

        # Draw move numbers on squares that knight has left behind
        painter.setPen(QColor(0, 0, 0))
        font = QFont("Arial", max(8, self.square_size // 4), QFont.Bold)
        painter.setFont(font)
        for (x, y), move_num in self.move_numbers.items():
            text = str(move_num)
            rect = QRectF(x * self.square_size, y * self.square_size, self.square_size, self.square_size)
            painter.drawText(rect, Qt.AlignCenter, text)

        # Draw knight icon at current position
        x, y = self.current_pos
        knight_x = x * self.square_size + (self.square_size - self.knight_pixmap.width()) / 2
        knight_y = y * self.square_size + (self.square_size - self.knight_pixmap.height()) / 2
        painter.drawPixmap(int(knight_x), int(knight_y), self.knight_pixmap)


        painter.end()


class KnightTourGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Knight's Tour with Numbered Trail")
        self.board_size = 5
        self.square_size = 60
        self.board = []
        self.move_positions = []
        self.current_move_index = 0
        self.timer_interval = 600  # ms
        self.is_paused = False

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Input fields and buttons
        controls_layout = QHBoxLayout()
        self.size_input = QLineEdit()
        self.size_input.setPlaceholderText("Board size (min 5)")
        self.size_input.setFixedWidth(120)

        self.start_row_input = QLineEdit()
        self.start_row_input.setPlaceholderText("Start row (0-index)")
        self.start_row_input.setFixedWidth(120)

        self.start_col_input = QLineEdit()
        self.start_col_input.setPlaceholderText("Start col (0-index)")
        self.start_col_input.setFixedWidth(120)

        self.start_btn = QPushButton("Start Tour")
        self.start_btn.clicked.connect(self.start_tour)

        controls_layout.addWidget(self.size_input)
        controls_layout.addWidget(self.start_row_input)
        controls_layout.addWidget(self.start_col_input)
        controls_layout.addWidget(self.start_btn)

        layout.addLayout(controls_layout)

        # Board widget placeholder (set later)
        self.board_widget = None
        layout.setAlignment(Qt.AlignTop)

        # Animation controls
        anim_layout = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.play_animation)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_animation)
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_animation)

        anim_layout.addWidget(self.play_btn)
        anim_layout.addWidget(self.pause_btn)
        anim_layout.addWidget(self.reset_btn)

        layout.addLayout(anim_layout)

        self.setLayout(layout)

        # Timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_moves)

    def start_tour(self):
        try:
            size = int(self.size_input.text())
            if size < 5:
                raise ValueError("Minimum board size is 5.")
            start_row = int(self.start_row_input.text())
            start_col = int(self.start_col_input.text())
            if not (0 <= start_row < size and 0 <= start_col < size):
                raise ValueError("Start position out of range.")
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))
            return

        self.board_size = size
        self.square_size = max(30, min(60, 480 // size))  # Keep square size reasonable
        self.board = generate_knights_tour_nxn(start_col, start_row, size)

        if not self.board:
            QMessageBox.information(self, "No Solution", "No complete Knight's Tour found from this position.")
            return

        # Prepare move_positions list for animation (move_number - 1) => (x, y)
        self.move_positions = [None] * (size * size)
        for y in range(size):
            for x in range(size):
                move_num = self.board[y][x]
                if move_num > 0:
                    self.move_positions[move_num - 1] = (x, y)

        self.current_move_index = 0
        self.is_paused = False

        # Create and add the BoardWidget (remove old if exists)
        if self.board_widget:
            self.layout().removeWidget(self.board_widget)
            self.board_widget.deleteLater()
            self.board_widget = None

        self.board_widget = BoardWidget(self.board_size, self.square_size, self.board)
        self.layout().insertWidget(1, self.board_widget, alignment=Qt.AlignHCenter)

        # Set initial knight position
        start_pos = self.move_positions[0]
        self.board_widget.set_knight_position(start_pos[0], start_pos[1])

        self.play_animation()

    def animate_moves(self):
        if self.is_paused:
            return

        self.current_move_index += 1
        if self.current_move_index >= len(self.move_positions):
            self.timer.stop()
            QMessageBox.information(self, "Done", "Knight's Tour animation completed!")
            return

        current = self.move_positions[self.current_move_index]
        prev = self.move_positions[self.current_move_index - 1]

        # Tell board widget to update knight pos and show move number on previous square
        self.board_widget.set_knight_position(current[0], current[1], prev[0], prev[1], self.current_move_index)

    def play_animation(self):
        if not self.board_widget:
            return
        self.is_paused = False
        if not self.timer.isActive():
            self.timer.start(self.timer_interval)

    def pause_animation(self):
        self.is_paused = True
        if self.timer.isActive():
            self.timer.stop()

    def reset_animation(self):
        if not self.board_widget:
            return
        self.current_move_index = 0
        start_pos = self.move_positions[0]
        self.board_widget.move_numbers.clear()
        self.board_widget.set_knight_position(start_pos[0], start_pos[1])
        self.pause_animation()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = KnightTourGUI()
    gui.resize(400, 500)
    gui.show()
    sys.exit(app.exec())
