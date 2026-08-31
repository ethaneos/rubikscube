"""
Rubik's Cube — PyQt6 + PyOpenGL (raw)
--------------------------------------
pip install PyQt6 PyOpenGL PyOpenGL_accelerate numpy

Key architecture decisions:
  - Two VBOs: one for the 9 moving cubies, one for the 18 static ones.
    This lets us rotate only the moving face during animation without
    touching the rest of the cube.
  - One well-defined rotation convention throughout: positive angle =
    clockwise when viewed from the positive end of the axis.
  - cubie_list() verified face-by-face against a concrete solved state.
"""

import sys
import math
import time
import ctypes
import random
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QSurfaceFormat
from OpenGL import GL
from OpenGL.GL import shaders

# ── Shaders ────────────────────────────────────────────────────────────────

VERT_SRC = b"""
#version 330 core
layout(location = 0) in vec3 in_position;
layout(location = 1) in vec3 in_color;
layout(location = 2) in vec3 in_normal;
uniform mat4 mvp;
uniform mat4 model;
out vec3 v_color;
out vec3 v_normal;
void main() {
    gl_Position = mvp * vec4(in_position, 1.0);
    v_color  = in_color;
    v_normal = mat3(model) * in_normal;
}
"""

FRAG_SRC = b"""
#version 330 core
in vec3 v_color;
in vec3 v_normal;
out vec4 out_color;
void main() {
    vec3 light = normalize(vec3(2.0, 4.0, 3.0));
    float diff = max(dot(normalize(v_normal), light), 0.0);
    vec3 shaded = v_color * (0.45 + 0.65 * diff);
    out_color = vec4(shaded, 1.0);
}
"""

# ── Colors ─────────────────────────────────────────────────────────────────

FACE_COLORS = {
    'U': (0.94, 0.94, 0.94),   # white
    'D': (0.96, 0.83, 0.00),   # yellow
    'F': (0.90, 0.19, 0.12),   # red
    'B': (1.00, 0.55, 0.00),   # orange
    'L': (0.18, 0.43, 0.99),   # blue
    'R': (0.11, 0.72, 0.33),   # green
}
INNER = (0.05, 0.05, 0.07)

# ── Geometry ───────────────────────────────────────────────────────────────

BODY  = 0.455   # half-size of the black plastic body
STICK = 0.43    # half-size of the coloured sticker (inset from edge)
EPS   = 0.002   # sticker sits this far outside the body surface

FACE_DEFS = [
    ('U', np.array([ 0, 1, 0], 'f4')),
    ('D', np.array([ 0,-1, 0], 'f4')),
    ('F', np.array([ 0, 0, 1], 'f4')),
    ('B', np.array([ 0, 0,-1], 'f4')),
    ('L', np.array([-1, 0, 0], 'f4')),
    ('R', np.array([ 1, 0, 0], 'f4')),
]

def _quad_verts(normal, centre, half):
    """6 positions (2 triangles) for a quad facing `normal`, centred at `centre`."""
    n = normal / np.linalg.norm(normal)
    ref = np.array([0,1,0],'f4') if abs(n[1]) < 0.9 else np.array([1,0,0],'f4')
    t1 = np.cross(n, ref); t1 /= np.linalg.norm(t1)
    t2 = np.cross(n, t1)
    c = np.array(centre, 'f4')
    corners = [
        c - t1*half - t2*half,
        c + t1*half - t2*half,
        c + t1*half + t2*half,
        c - t1*half + t2*half,
    ]
    return [corners[i] for i in (0,1,2, 0,2,3)]

def build_cubie(cx, cy, cz, sticker_colors):
    """
    Returns flat float32 list: [x,y,z, r,g,b, nx,ny,nz] per vertex.
    sticker_colors: {face_name: (r,g,b)} for outer faces only.
    """
    verts = []
    centre = np.array([cx, cy, cz], 'f4')

    for face_name, n in FACE_DEFS:
        # Black body face
        pts = _quad_verts(n, centre + n*BODY, BODY)
        for p in pts:
            verts += [p[0],p[1],p[2], *INNER, n[0],n[1],n[2]]

        # Coloured sticker on top, offset just past the body surface
        if face_name in sticker_colors:
            pts = _quad_verts(n, centre + n*(BODY+EPS), STICK)
            col = sticker_colors[face_name]
            for p in pts:
                verts += [p[0],p[1],p[2], *col, n[0],n[1],n[2]]

    return verts

def make_vertex_array(cubie_data):
    """cubie_data: list of ((cx,cy,cz), sticker_colors_dict)"""
    verts = []
    for (cx,cy,cz), fc in cubie_data:
        verts += build_cubie(cx, cy, cz, fc)
    return np.array(verts, dtype='f4')

# ── Maths ──────────────────────────────────────────────────────────────────

def perspective(fovy_deg, aspect, near, far):
    f  = 1.0 / math.tan(math.radians(fovy_deg) / 2)
    nf = 1.0 / (near - far)
    return np.array([
        [f/aspect, 0, 0,              0            ],
        [0,        f, 0,              0            ],
        [0,        0, (far+near)*nf,  2*far*near*nf],
        [0,        0, -1,             0            ],
    ], 'f4')

def look_at(eye, target, up):
    f = target - eye;  f /= np.linalg.norm(f)
    r = np.cross(f, up); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    m = np.eye(4, dtype='f4')
    m[0,:3]=r; m[1,:3]=u; m[2,:3]=-f
    m[0,3]=-r.dot(eye); m[1,3]=-u.dot(eye); m[2,3]=f.dot(eye)
    return m

def rot_mat(axis, angle):
    """Rodrigues rotation: `angle` radians around `axis` (right-hand rule)."""
    a = np.array(axis, 'f4'); a /= np.linalg.norm(a)
    c, s, t = math.cos(angle), math.sin(angle), 1-math.cos(angle)
    x, y, z = a
    return np.array([
        [t*x*x+c,   t*x*y-s*z, t*x*z+s*y, 0],
        [t*x*y+s*z, t*y*y+c,   t*y*z-s*x, 0],
        [t*x*z-s*y, t*y*z+s*x, t*z*z+c,   0],
        [0,         0,         0,          1],
    ], 'f4')

def upload_mat4(loc, m):
    GL.glUniformMatrix4fv(loc, 1, GL.GL_FALSE, m.T.astype('f4'))

# ── GPU buffer helpers ─────────────────────────────────────────────────────

def make_vao_vbo():
    vao = GL.glGenVertexArrays(1)
    vbo = GL.glGenBuffers(1)
    return vao, vbo

def upload_to_vao(vao, vbo, verts):
    """Upload vertex data and set attribute pointers. Returns vertex count."""
    GL.glBindVertexArray(vao)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, verts.nbytes, verts, GL.GL_DYNAMIC_DRAW)
    stride = 9 * 4  # 9 floats × 4 bytes
    GL.glEnableVertexAttribArray(0)
    GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, ctypes.c_void_p(0))
    GL.glEnableVertexAttribArray(1)
    GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, ctypes.c_void_p(12))
    GL.glEnableVertexAttribArray(2)
    GL.glVertexAttribPointer(2, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, ctypes.c_void_p(24))
    GL.glBindVertexArray(0)
    return len(verts) // 9

# ── Logical cube ───────────────────────────────────────────────────────────

FACE_NAMES = ['U','D','F','B','L','R']

class LogicCube:
    def __init__(self):
        # Each face: 9 colour chars in reading order (top-left → bottom-right)
        # when looking at that face from outside.
        self.faces = {f: [f]*9 for f in FACE_NAMES}

    def _cw(self, f):
        a = self.faces[f]
        self.faces[f] = [a[6],a[3],a[0], a[7],a[4],a[1], a[8],a[5],a[2]]

    def _ccw(self, f):
        a = self.faces[f]
        self.faces[f] = [a[2],a[5],a[8], a[1],a[4],a[7], a[0],a[3],a[6]]

    def _cycle(self, a, b, c, d):
        """Rotate four strips of stickers: a→b→c→d→a."""
        get = lambda g: [self.faces[f][i] for f,i in g]
        put = lambda g, v: [self.faces[f].__setitem__(i, v[k]) for k,(f,i) in enumerate(g)]
        va,vb,vc,vd = get(a),get(b),get(c),get(d)
        put(b,va); put(c,vb); put(d,vc); put(a,vd)

    def apply(self, move):
        m = move
        if   m == 'U':  self._cw('U');  self._cycle([('B',0),('B',1),('B',2)],[('R',0),('R',1),('R',2)],[('F',0),('F',1),('F',2)],[('L',0),('L',1),('L',2)])
        elif m == "U'": self._ccw('U'); self._cycle([('L',0),('L',1),('L',2)],[('F',0),('F',1),('F',2)],[('R',0),('R',1),('R',2)],[('B',0),('B',1),('B',2)])
        elif m == 'U2': self.apply('U'); self.apply('U'); return
        elif m == 'D':  self._cw('D');  self._cycle([('F',6),('F',7),('F',8)],[('R',6),('R',7),('R',8)],[('B',6),('B',7),('B',8)],[('L',6),('L',7),('L',8)])
        elif m == "D'": self._ccw('D'); self._cycle([('L',6),('L',7),('L',8)],[('B',6),('B',7),('B',8)],[('R',6),('R',7),('R',8)],[('F',6),('F',7),('F',8)])
        elif m == 'D2': self.apply('D'); self.apply('D'); return
        elif m == 'F':  self._cw('F');  self._cycle([('U',6),('U',7),('U',8)],[('R',0),('R',3),('R',6)],[('D',2),('D',1),('D',0)],[('L',8),('L',5),('L',2)])
        elif m == "F'": self._ccw('F'); self._cycle([('L',2),('L',5),('L',8)],[('D',0),('D',1),('D',2)],[('R',6),('R',3),('R',0)],[('U',8),('U',7),('U',6)])
        elif m == 'F2': self.apply('F'); self.apply('F'); return
        elif m == 'B':  self._cw('B');  self._cycle([('U',2),('U',1),('U',0)],[('L',0),('L',3),('L',6)],[('D',6),('D',7),('D',8)],[('R',8),('R',5),('R',2)])
        elif m == "B'": self._ccw('B'); self._cycle([('R',8),('R',5),('R',2)],[('D',6),('D',7),('D',8)],[('L',0),('L',3),('L',6)],[('U',2),('U',1),('U',0)])
        elif m == 'B2': self.apply('B'); self.apply('B'); return
        elif m == 'L':  self._cw('L');  self._cycle([('U',0),('U',3),('U',6)],[('F',0),('F',3),('F',6)],[('D',0),('D',3),('D',6)],[('B',8),('B',5),('B',2)])
        elif m == "L'": self._ccw('L'); self._cycle([('B',2),('B',5),('B',8)],[('D',6),('D',3),('D',0)],[('F',6),('F',3),('F',0)],[('U',6),('U',3),('U',0)])
        elif m == 'L2': self.apply('L'); self.apply('L'); return
        elif m == 'R':  self._cw('R');  self._cycle([('U',8),('U',5),('U',2)],[('B',0),('B',3),('B',6)],[('D',8),('D',5),('D',2)],[('F',8),('F',5),('F',2)])
        elif m == "R'": self._ccw('R'); self._cycle([('F',2),('F',5),('F',8)],[('D',2),('D',5),('D',8)],[('B',6),('B',3),('B',0)],[('U',2),('U',5),('U',8)])
        elif m == 'R2': self.apply('R'); self.apply('R'); return

    def is_solved(self):
        return all(self.faces[f] == [f]*9 for f in FACE_NAMES)

    def to_kociemba_string(self):
        """
        Serialize to the 54-character format kociemba.solve() expects:
        facelets concatenated in U,R,F,D,L,B order, each face read in
        the same top-left-to-bottom-right order (as viewed from outside)
        that we already use internally — so this is a direct concatenation,
        no reordering needed.
        """
        order = ['U', 'R', 'F', 'D', 'L', 'B']
        return ''.join(''.join(self.faces[f]) for f in order)

    def cubie_list(self):
        """
        Returns [(grid_pos, sticker_colors), ...] for all 27 cubies.

        Index = row*3 + col, where row/col are as seen looking at that
        face from outside the cube (row 0 = top, col 0 = left).

        Mappings derived and verified against apply() move logic:
          U  (viewed from above, +x=right, +z=near/F side)
             row = z+1,  col = x+1
          D  (viewed from below, +x=right, -z=near from below = F side)
             row = 1-z,  col = x+1
          F  (viewed from front, +x=right, -y=down)
             row = 1-y,  col = x+1
          B  (viewed from back,  -x=right, -y=down)
             row = 1-y,  col = 1-x
          L  (viewed from left,  +z=right from outside, -y=down)
             row = 1-y,  col = z+1
          R  (viewed from right, -z=right from outside, -y=down)
             row = 1-y,  col = 1-z
        """
        result = []
        for x in range(-1, 2):
            for y in range(-1, 2):
                for z in range(-1, 2):
                    fc = {}
                    if y ==  1: fc['U'] = FACE_COLORS[self.faces['U'][(z+1)*3 + (x+1)]]
                    if y == -1: fc['D'] = FACE_COLORS[self.faces['D'][(1-z)*3 + (x+1)]]
                    if z ==  1: fc['F'] = FACE_COLORS[self.faces['F'][(1-y)*3 + (x+1)]]
                    if z == -1: fc['B'] = FACE_COLORS[self.faces['B'][(1-y)*3 + (1-x)]]
                    if x == -1: fc['L'] = FACE_COLORS[self.faces['L'][(1-y)*3 + (z+1)]]
                    if x ==  1: fc['R'] = FACE_COLORS[self.faces['R'][(1-y)*3 + (1-z)]]
                    result.append(((float(x), float(y), float(z)), fc))
        return result

    def split_cubie_list(self, face):
        """
        Return (moving, static) cubie data for a given face move.
        moving: the 9 cubies on that face.
        static: the other 18.
        """
        sel = {
            'U': lambda x,y,z: y ==  1,
            'D': lambda x,y,z: y == -1,
            'F': lambda x,y,z: z ==  1,
            'B': lambda x,y,z: z == -1,
            'L': lambda x,y,z: x == -1,
            'R': lambda x,y,z: x ==  1,
        }[face]
        all_cubies = self.cubie_list()
        moving = [(pos, fc) for pos, fc in all_cubies if sel(round(pos[0]), round(pos[1]), round(pos[2]))]
        static = [(pos, fc) for pos, fc in all_cubies if not sel(round(pos[0]), round(pos[1]), round(pos[2]))]
        return moving, static

# ── Animation ──────────────────────────────────────────────────────────────

# Rotation axes (right-hand rule: curl fingers in CW direction from outside = negative)
# We define CW moves as viewed from outside, which is a negative rotation
# around the outward-pointing axis using the right-hand rule.
MOVE_AXIS = {
    'U': ( 0, 1, 0), 'D': ( 0,-1, 0),
    'F': ( 0, 0, 1), 'B': ( 0, 0,-1),
    'L': (-1, 0, 0), 'R': ( 1, 0, 0),
}

ALL_MOVES = [
    'U',"U'",'U2', 'D',"D'",'D2', 'F',"F'",'F2',
    'B',"B'",'B2', 'L',"L'",'L2', 'R',"R'",'R2',
]

class MoveAnimation:
    DURATION = 0.18  # seconds per quarter turn

    def __init__(self, move):
        base   = move.rstrip("'2")
        prime  = "'" in move
        double = "2" in move
        self.face     = base
        self.axis     = np.array(MOVE_AXIS[base], 'f4')
        # CW from outside = negative rotation around outward axis (right-hand rule)
        self.total    = -math.pi/2 * (2 if double else 1) * (-1 if prime else 1)
        self.duration = self.DURATION * (1.6 if double else 1.0)
        self.elapsed  = 0.0

    def angle(self):
        p = min(self.elapsed / self.duration, 1.0)
        return self.total * p*p*(3 - 2*p)  # smoothstep ease in/out

# ── CubeWidget ─────────────────────────────────────────────────────────────

class CubeWidget(QOpenGLWidget):

    # Emitted when the user presses Escape — lets a host window (e.g. a
    # main menu) know it should switch away from the cube view.
    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.logic = LogicCube()

        # Camera (spherical)
        self.cam_theta = 0.6
        self.cam_phi   = 0.9
        self.cam_dist  = 7.0
        self._drag     = False
        self._last_xy  = (0, 0)

        # Move queue
        self._queue          = []
        self._anim           = None   # current MoveAnimation
        self._move_in_flight = None   # move name string
        self._last_t         = None

        # GL objects — initialised in initializeGL
        self._prog         = None
        self._loc_mvp      = None
        self._loc_model    = None

        # Two VAO/VBO pairs: static cubies and moving cubies
        self._vao_static  = None
        self._vbo_static  = None
        self._cnt_static  = 0
        self._vao_moving  = None
        self._vbo_moving  = None
        self._cnt_moving  = 0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(16)

    # ── GL lifecycle ──────────────────────────────────────────────────────

    def initializeGL(self):
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_CULL_FACE)
        GL.glClearColor(0.03, 0.03, 0.05, 1.0)

        vert = shaders.compileShader(VERT_SRC, GL.GL_VERTEX_SHADER)
        frag = shaders.compileShader(FRAG_SRC, GL.GL_FRAGMENT_SHADER)
        self._prog = shaders.compileProgram(vert, frag)

        self._loc_mvp   = GL.glGetUniformLocation(self._prog, 'mvp')
        self._loc_model = GL.glGetUniformLocation(self._prog, 'model')

        self._vao_static, self._vbo_static = make_vao_vbo()
        self._vao_moving, self._vbo_moving = make_vao_vbo()

        self._upload_all_to_static()

    def _upload_all_to_static(self):
        """Idle state: all 27 cubies in the static VBO, moving VBO empty."""
        verts = make_vertex_array(self.logic.cubie_list())
        self._cnt_static = upload_to_vao(self._vao_static, self._vbo_static, verts)
        self._cnt_moving = 0

    def _upload_split(self, face):
        """
        Animation start: split cubies into moving (9) and static (18).
        The moving VBO gets the rotation matrix; static gets identity.
        """
        moving, static = self.logic.split_cubie_list(face)
        v_moving = make_vertex_array(moving)
        v_static = make_vertex_array(static)
        self._cnt_moving = upload_to_vao(self._vao_moving, self._vbo_moving, v_moving)
        self._cnt_static = upload_to_vao(self._vao_static, self._vbo_static, v_static)

    def resizeGL(self, w, h):
        GL.glViewport(0, 0, w, h)

    def paintGL(self):
        now = time.perf_counter()
        dt  = (now - self._last_t) if self._last_t else 0.0
        self._last_t = now
        self._tick(dt)

        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glUseProgram(self._prog)

        # Camera
        w, h = self.width(), self.height()
        eye = np.array([
            self.cam_dist * math.sin(self.cam_phi) * math.sin(self.cam_theta),
            self.cam_dist * math.cos(self.cam_phi),
            self.cam_dist * math.sin(self.cam_phi) * math.cos(self.cam_theta),
        ], 'f4')
        view = look_at(eye, np.zeros(3, dtype='f4'), np.array([0,1,0],'f4'))
        proj = perspective(42, w / max(h, 1), 0.1, 100)
        vp   = proj @ view   # view-projection, no model yet

        identity = np.eye(4, dtype='f4')

        # ── Draw static cubies (identity model matrix) ──
        if self._cnt_static > 0:
            upload_mat4(self._loc_mvp,   vp @ identity)
            upload_mat4(self._loc_model, identity)
            GL.glBindVertexArray(self._vao_static)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, self._cnt_static)

        # ── Draw moving cubies (rotation model matrix) ──
        if self._anim and self._cnt_moving > 0:
            model = rot_mat(self._anim.axis, self._anim.angle())
            upload_mat4(self._loc_mvp,   vp @ model)
            upload_mat4(self._loc_model, model)
            GL.glBindVertexArray(self._vao_moving)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, self._cnt_moving)

        GL.glBindVertexArray(0)
        GL.glUseProgram(0)

    # ── Animation tick ────────────────────────────────────────────────────

    def _tick(self, dt):
        if self._anim:
            self._anim.elapsed += dt
            if self._anim.elapsed >= self._anim.duration:
                # Commit move to logic, rebuild geometry, return to idle
                self.logic.apply(self._move_in_flight)
                self._anim           = None
                self._move_in_flight = None
                self._upload_all_to_static()
                self._next()
        elif self._queue:
            self._next()

    def _next(self):
        if not self._queue:
            return
        move = self._queue.pop(0)
        self._move_in_flight = move
        self._anim = MoveAnimation(move)
        # Split geometry so the moving face is in a separate VBO
        self._upload_split(self._anim.face)

    def queue_move(self, move):
        self._queue.append(move)

    def scramble(self, n=20):
        """Queue n random moves, never repeating the same face twice in a row."""
        last_face = None
        for _ in range(n):
            move = random.choice(ALL_MOVES)
            while move[0] == last_face:
                move = random.choice(ALL_MOVES)
            last_face = move[0]
            self.queue_move(move)

    def reset_solved(self):
        """Return the cube to a solved state immediately (no animation)."""
        self._queue.clear()
        self._anim = None
        self._move_in_flight = None
        self.logic = LogicCube()
        self._upload_all_to_static()

    # ── Input ─────────────────────────────────────────────────────────────

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.back_requested.emit()
            return

        MAP = {
            Qt.Key.Key_U:'U', Qt.Key.Key_D:'D', Qt.Key.Key_F:'F',
            Qt.Key.Key_B:'B', Qt.Key.Key_L:'L', Qt.Key.Key_R:'R',
        }
        face = MAP.get(e.key())
        if face:
            prime = bool(e.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            self.queue_move(face + ("'" if prime else ''))

    def mousePressEvent(self, e):
        self._drag    = True
        self._last_xy = (e.position().x(), e.position().y())

    def mouseReleaseEvent(self, e):
        self._drag = False

    def mouseMoveEvent(self, e):
        if not self._drag:
            return
        x, y = e.position().x(), e.position().y()
        self.cam_theta -= (x - self._last_xy[0]) * 0.008
        self.cam_phi = max(0.1, min(math.pi-0.1, self.cam_phi + (y - self._last_xy[1]) * 0.008))
        self._last_xy = (x, y)

    def wheelEvent(self, e):
        self.cam_dist = max(4.0, min(15.0, self.cam_dist - e.angleDelta().y() * 0.01))

# ── Main ───────────────────────────────────────────────────────────────────

def configure_surface_format():
    """
    Requests OpenGL 3.3 Core Profile with 4x MSAA and a 24-bit depth buffer.
    Must be called BEFORE the QApplication is constructed — any file that
    creates a CubeWidget (this one, or a host app like a main menu) needs
    to call this first.
    """
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    fmt.setDepthBufferSize(24)
    fmt.setSamples(4)
    QSurfaceFormat.setDefaultFormat(fmt)


def main():
    configure_surface_format()

    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle("Rubik's Cube — PyQt6 + PyOpenGL")
    win.resize(900, 700)
    cube = CubeWidget()
    win.setCentralWidget(cube)
    win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()