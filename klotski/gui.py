import time
import tkinter as tk
from tkinter import ttk
from typing import List

import sv_ttk

from klotski.solver import Board, State


class PuzzleGUI:
    def __init__(self, root: tk.Tk, solution: List[State]) -> None:
        self.root = root
        self.solution = solution
        self.board_frame = ttk.Frame(root)
        self.board_frame.grid(row=0, column=0, padx=10, pady=10)
        self.cell_size = 70.0  # Size of each cell in pixels
        self.spacing = 10.0  # Space between cells
        self.rows = len(solution[0].board.grid)
        self.cols = len(solution[0].board.grid[0])
        self.canvas = tk.Canvas(
            self.board_frame,
            width=self.cols * (self.cell_size + self.spacing),
            height=self.rows * (self.cell_size + self.spacing),
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0)
        self.current_step = 0
        self.is_animating = False  # Track animation state

        # Render the first state
        self.draw_board(solution[0].board)

        # Navigation buttons
        self.control_frame = ttk.Frame(root)
        self.control_frame.grid(row=1, column=0, pady=10)

        self.prev_button = ttk.Button(self.control_frame, text="Previous", command=self.show_previous_step)
        self.prev_button.grid(row=0, column=0, padx=5)

        self.next_button = ttk.Button(self.control_frame, text="Next", command=self.show_next_step)
        self.next_button.grid(row=0, column=1, padx=5)

        self.animate_button = ttk.Button(self.control_frame, text="Play", command=self.toggle_animation)
        self.animate_button.grid(row=0, column=2, padx=5)

        # Slider for navigation
        self.slider = ttk.Scale(self.control_frame, from_=0, to=len(solution) - 1, orient="horizontal", command=self.slider_update)
        self.slider.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5)

        # Bind scroll wheel
        self.root.bind("<MouseWheel>", self.on_scroll)  # Windows
        self.root.bind("<Button-4>", self.on_scroll)  # Linux scroll up
        self.root.bind("<Button-5>", self.on_scroll)  # Linux scroll down
        sv_ttk.set_theme("dark")

    def draw_board(self, board: Board) -> None:
        """Draw the board with pieces and goal area."""
        self.canvas.delete("all")

        # Draw pieces
        for piece in board.pieces:
            size = piece.size
            x0 = piece.coord_x * (self.cell_size + self.spacing)
            y0 = piece.coord_y * (self.cell_size + self.spacing)
            x1 = x0 + size[1] * self.cell_size + (size[1] - 1) * self.spacing
            y1 = y0 + size[0] * self.cell_size + (size[0] - 1) * self.spacing
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=piece.color, tags="piece")

        # Draw dotted lines for goal cell (2 x 2 at the bottom middle)
        x0 = (board.width // 2 - 1) * (self.cell_size + self.spacing) - self.spacing // 2
        y0 = (board.height - 2) * (self.cell_size + self.spacing) - self.spacing // 2
        x1 = x0 + 2 * self.cell_size + self.spacing * 2
        y1 = y0 + 2 * self.cell_size + self.spacing * 2
        self.canvas.create_rectangle(x0, y0, x1, y1, outline="#A0D2A1", dash=(4, 4), tags="goal", width=2)

    def show_next_step(self) -> None:
        """Show the next step in the solution."""
        if self.current_step < len(self.solution) - 1:
            self.current_step += 1
            self.animate_move(self.solution[self.current_step - 1].board, self.solution[self.current_step].board)
            self.slider.set(self.current_step)

    def show_previous_step(self) -> None:
        """Show the previous step in the solution."""
        if self.current_step > 0:
            self.current_step -= 1
            self.animate_move(self.solution[self.current_step + 1].board, self.solution[self.current_step].board)
            self.slider.set(self.current_step)

    def animate_move(self, from_board: "Board", to_board: "Board") -> None:
        """Animate the transition between two board states."""
        steps = 10
        delay = 10  # milliseconds

        for i in range(steps):
            self.canvas.delete("piece")
            for i, piece in enumerate(from_board.pieces):
                from_x = piece.coord_x * (self.cell_size + self.spacing)
                from_y = piece.coord_y * (self.cell_size + self.spacing)
                to_piece = to_board.pieces[i]
                to_x = to_piece.coord_x * (self.cell_size + self.spacing)
                to_y = to_piece.coord_y * (self.cell_size + self.spacing)

                current_x = from_x + (to_x - from_x) * (i + 1) / steps
                current_y = from_y + (to_y - from_y) * (i + 1) / steps

                size = piece.size
                x0 = current_x
                y0 = current_y
                x1 = x0 + size[1] * self.cell_size + (size[1] - 1) * self.spacing
                y1 = y0 + size[0] * self.cell_size + (size[0] - 1) * self.spacing
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=piece.color, tags="piece")

            self.root.update()
            time.sleep(delay / 1000)

        self.draw_board(to_board)

    def animate_solution(self) -> None:
        """Animate the entire solution step by step."""
        while self.is_animating and self.current_step < len(self.solution) - 1:
            self.current_step += 1
            self.animate_move(self.solution[self.current_step - 1].board, self.solution[self.current_step].board)
            self.slider.set(self.current_step)
            self.root.update()
            time.sleep(0.2)  # Pause between steps

        self.is_animating = False
        self.animate_button.config(text="Play")

    def toggle_animation(self) -> None:
        """Toggle the animation state between play and pause."""
        if self.is_animating:
            self.is_animating = False
            self.animate_button.config(text="Play")
        else:
            self.is_animating = True
            self.animate_button.config(text="Pause")
            self.root.after(0, self.animate_solution)

    def slider_update(self, value: str) -> None:
        """Update the current step based on the slider value."""
        step = int(float(value))
        if step != self.current_step:
            self.current_step = step
            self.draw_board(self.solution[self.current_step].board)

    def on_scroll(self, event: tk.Event) -> None:
        """Handle scroll wheel event to navigate steps."""
        if event.num == 4 or event.delta > 0:
            self.show_previous_step()
        elif event.num == 5 or event.delta < 0:
            self.show_next_step()


def run_gui(solution: List[State]) -> None:
    """Run the GUI application."""
    root = tk.Tk()
    root.title("Klotski Puzzle Solver")
    app = PuzzleGUI(root, solution)
    root.mainloop()
