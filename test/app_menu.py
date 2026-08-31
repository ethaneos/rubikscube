"""
Main Menu — PyQt6
------------------
pip install PyQt6 PyOpenGL PyOpenGL_accelerate numpy

Hosts the Rubik's Cube (cube_pyopengl.CubeWidget) behind a menu screen.
Uses a QStackedWidget with two pages:
  index 0 — the menu
  index 1 — the cube, created fresh each time "Play" is clicked

Run this file (not cube_pyopengl.py) to get the app with a menu.
cube_pyopengl.py remains runnable standalone for quick testing of the
cube in isolation.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox,
)
from PyQt6.QtCore import Qt

# Import the cube module — this is the "same framework, different file"
# integration point. configure_surface_format() must run before QApplication
# is constructed, and CubeWidget is the actual 3D view we embed.
from cube_pyopengl import CubeWidget, configure_surface_format
from solver_thread import SolverThread


# ── Menu page ────────────────────────────────────────────────────────────

class MenuPage(QWidget):
    """
    Plain menu screen. Doesn't know anything about OpenGL — it just emits
    requests (via the callbacks passed in) that MainWindow acts on.
    """

    def __init__(self, on_play, on_scramble, on_quit, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #08080c;")

        title = QLabel("RUBIK'S CUBE")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: #e8e8f0;
            font-size: 42px;
            font-weight: 800;
            letter-spacing: 6px;
        """)

        subtitle = QLabel("PyQt6 + PyOpenGL")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            color: #55556a;
            font-size: 13px;
            letter-spacing: 3px;
            margin-bottom: 40px;
        """)

        btn_play = self._make_button("▶  PLAY  (SOLVED)")
        btn_scramble = self._make_button("🔀  PLAY  (SCRAMBLED)")
        btn_quit = self._make_button("✕  QUIT", danger=True)

        btn_play.clicked.connect(on_play)
        btn_scramble.clicked.connect(on_scramble)
        btn_quit.clicked.connect(on_quit)

        hint = QLabel("U D F B L R to turn faces  ·  Shift = counter-clockwise  ·  Esc = back to menu")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #33334a; font-size: 11px; letter-spacing: 1px; margin-top: 40px;")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addWidget(btn_play, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(12)
        layout.addWidget(btn_scramble, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(12)
        layout.addWidget(btn_quit, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)
        layout.addStretch(1)

    def _make_button(self, text, danger=False):
        btn = QPushButton(text)
        btn.setFixedSize(280, 52)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        base_color = "#ff5566" if danger else "#7c6fff"
        hover_color = "#ff7788" if danger else "#9a8fff"
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #14141c;
                color: #e8e8f0;
                border: 1px solid {base_color};
                border-radius: 4px;
                font-size: 14px;
                font-weight: 600;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                background-color: {base_color};
                color: #08080c;
                border-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {hover_color};
            }}
        """)
        return btn


# ── Cube page (cube + solve control bar) ────────────────────────────────

class CubePage(QWidget):
    """
    Wraps CubeWidget with a thin control bar underneath holding the Solve
    button. CubeWidget itself stays untouched — this is purely a host
    container, same pattern as MenuPage.
    """

    def __init__(self, cube: CubeWidget, on_solve, parent=None):
        super().__init__(parent)
        self.cube = cube

        self.solve_btn = QPushButton("🧩  SOLVE")
        self.solve_btn.setFixedSize(160, 40)
        self.solve_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.solve_btn.setStyleSheet("""
            QPushButton {
                background-color: #14141c;
                color: #e8e8f0;
                border: 1px solid #7c6fff;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 600;
                letter-spacing: 1px;
            }
            QPushButton:hover:!disabled {
                background-color: #7c6fff;
                color: #08080c;
            }
            QPushButton:disabled {
                color: #444458;
                border-color: #2a2a3a;
            }
        """)
        self.solve_btn.clicked.connect(on_solve)

        bar = QHBoxLayout()
        bar.addStretch(1)
        bar.addWidget(self.solve_btn)
        bar.addStretch(1)
        bar.setContentsMargins(0, 8, 0, 8)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(cube, stretch=1)
        layout.addLayout(bar)


# ── Main window ──────────────────────────────────────────────────────────

class MainWindow(QMainWindow):

    MENU_INDEX = 0
    CUBE_INDEX = 1

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rubik's Cube")
        self.resize(1000, 750)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Menu page is built once and reused.
        self.menu_page = MenuPage(
            on_play=lambda: self._open_cube(scrambled=False),
            on_scramble=lambda: self._open_cube(scrambled=True),
            on_quit=self.close,
        )
        self.stack.addWidget(self.menu_page)   # index 0

        self._cube_widget = None  # created fresh each time we enter Play
        self._cube_page = None
        self._solver_thread = None  # must stay referenced while running

        self.stack.setCurrentIndex(self.MENU_INDEX)
        self.statusBar().showMessage("Select an option to begin")

    # ── Navigation ───────────────────────────────────────────────────────

    def _open_cube(self, scrambled: bool):
        """
        Create a brand-new CubeWidget and switch to it. Building a fresh
        widget each time is simpler than resetting animation/queue state
        on a reused one, and it's cheap — geometry upload is a few
        hundred vertices.
        """
        if self._cube_page is not None:
            self.stack.removeWidget(self._cube_page)
            self._cube_page.deleteLater()

        cube = CubeWidget()
        cube.back_requested.connect(self._return_to_menu)

        page = CubePage(cube, on_solve=self._solve_cube)

        self._cube_widget = cube
        self._cube_page = page
        self.stack.addWidget(page)          # index 1
        self.stack.setCurrentIndex(self.CUBE_INDEX)
        cube.setFocus()                      # so keyboard moves work immediately

        if scrambled:
            cube.scramble(20)

        self.statusBar().showMessage(
            "U D F B L R — turn face   ·   Shift — counter-clockwise   ·   Esc — back to menu"
        )

    def _solve_cube(self):
        """
        Kick off a background solve. The button disables itself while the
        solver runs (usually well under a second, but never block the UI
        thread on it) and the resulting moves are queued into the cube's
        existing animation queue exactly like a manual keypress would be.
        """
        cube = self._cube_widget
        if cube is None:
            return

        if cube.logic.is_solved():
            self.statusBar().showMessage("Already solved!")
            return

        self._cube_page.solve_btn.setEnabled(False)
        self._cube_page.solve_btn.setText("SOLVING…")
        self.statusBar().showMessage("Solving…")

        cube_string = cube.logic.to_kociemba_string()
        self._solver_thread = SolverThread(cube_string)
        self._solver_thread.solved.connect(self._on_solved)
        self._solver_thread.failed.connect(self._on_solve_failed)
        self._solver_thread.start()

    def _on_solved(self, moves: list):
        cube = self._cube_widget
        if cube is not None:
            for move in moves:
                cube.queue_move(move)
            cube.setFocus()
        self._cube_page.solve_btn.setEnabled(True)
        self._cube_page.solve_btn.setText("🧩  SOLVE")
        self.statusBar().showMessage(f"Solved in {len(moves)} moves")

    def _on_solve_failed(self, message: str):
        self._cube_page.solve_btn.setEnabled(True)
        self._cube_page.solve_btn.setText("🧩  SOLVE")
        self.statusBar().showMessage("Solve failed")
        QMessageBox.warning(self, "Solve failed", message)

    def _return_to_menu(self):
        self.stack.setCurrentIndex(self.MENU_INDEX)
        self.statusBar().showMessage("Select an option to begin")
        # Cube widget is left alive but hidden; it's replaced (not reused)
        # next time Play is clicked, so no stale animation state carries over.


# ── Entry point ────────────────────────────────────────────────────────────

def main():
    # Must run before QApplication is constructed.
    configure_surface_format()

    app = QApplication(sys.argv)
    app.setApplicationName("Rubik's Cube")

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()