"""
Solver Thread — PyQt6
----------------------
pip install kociemba

Wraps kociemba.solve() in a QThread so the ~0.1-1s solve computation
doesn't freeze the UI. Import SolverThread and connect to its signals.
"""

from PyQt6.QtCore import QThread, pyqtSignal
import kociemba


class SolverThread(QThread):
    """
    Runs kociemba.solve() on a background thread.

    Usage:
        thread = SolverThread(cube_string)
        thread.solved.connect(lambda moves: ...)   # list[str] of moves
        thread.failed.connect(lambda msg: ...)      # str error message
        thread.start()

    The thread object must be kept alive (e.g. as self._solver_thread)
    until it finishes, or Qt will garbage-collect it mid-run.
    """

    solved = pyqtSignal(list)   # emits list of move strings, e.g. ["R","U'","F2"]
    failed = pyqtSignal(str)    # emits a human-readable error message

    def __init__(self, cube_string, parent=None):
        super().__init__(parent)
        self.cube_string = cube_string

    def run(self):
        # This executes on the background thread — never touch GUI
        # widgets directly from here, only emit signals.
        try:
            solution = kociemba.solve(self.cube_string)
            moves = solution.split()
            self.solved.emit(moves)
        except Exception as e:
            self.failed.emit(str(e))