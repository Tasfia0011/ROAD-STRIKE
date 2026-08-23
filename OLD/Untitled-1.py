import sys
import random
from OpenGL.GL import *      # Core OpenGL functions
from OpenGL.GLUT import *    # GLUT library for window and input handling
from OpenGL.GLU import *     # OpenGL Utility library
import math

# ----------------------------
# Window / world settings
# ----------------------------
W, H = 900, 600

# Use a simple 2D "world" coordinate system:
# x in [0, 100], y in [0, 100]
WORLD_MIN, WORLD_MAX = 0.0, 100.0

# ----------------------------
# Rain configuration
# ----------------------------
NUM_DROPS = 120
rain_speed = 0.6  # world units per frame (adjustable)

# Drops are line segments, each with:
# x, y (head), len, drift
drops = []


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def make_drop():
    # Spawn near the top, across the whole sky width
    x = random.uniform(5.0, 95.0)
    y = random.uniform(60.0, 110.0)   # some start off-screen
    length = random.uniform(2.0, 5.0)
    drift = random.uniform(-0.08, 0.08)  # tiny horizontal drift
    return [x, y, length, drift]


def reset_drops():
    global drops
    drops = [make_drop() for _ in range(NUM_DROPS)]


# ----------------------------
# Drawing helpers (ONLY primitives)
# ----------------------------
def draw_house():
    """
    House built from triangles + lines:
      - base (rectangle) using two triangles
      - roof using one triangle + some lines
      - door using two triangles
      - windows using lines (frames) and a point (handle)
    """
    # ---- Ground line (GL_LINES) ----
    glColor3f(0.10, 0.45, 0.12)
    glLineWidth(3.0)
    glBegin(GL_LINES)
    glVertex2f(0.0, 20.0)
    glVertex2f(100.0, 20.0)
    glEnd()

    # ---- House body (two triangles) ----
    glColor3f(0.85, 0.75, 0.55)
    glBegin(GL_TRIANGLES)
    # rectangle corners: (30,20), (70,20), (70,55), (30,55)
    glVertex2f(30.0, 20.0)
    glVertex2f(70.0, 20.0)
    glVertex2f(70.0, 55.0)

    glVertex2f(30.0, 20.0)
    glVertex2f(70.0, 55.0)
    glVertex2f(30.0, 55.0)
    glEnd()

    # ---- Roof (one triangle) ----
    glColor3f(0.55, 0.20, 0.20)
    glBegin(GL_TRIANGLES)
    # roof triangle: left (27,55), right (73,55), top (50,75)
    glVertex2f(27.0, 55.0)
    glVertex2f(73.0, 55.0)
    glVertex2f(50.0, 75.0)
    glEnd()

    # ---- Outlines (GL_LINES) ----
    glColor3f(0.20, 0.15, 0.10)
    glLineWidth(2.0)

    # Body outline
    glBegin(GL_LINES)
    glVertex2f(30.0, 20.0); glVertex2f(70.0, 20.0)
    glVertex2f(70.0, 20.0); glVertex2f(70.0, 55.0)
    glVertex2f(70.0, 55.0); glVertex2f(30.0, 55.0)
    glVertex2f(30.0, 55.0); glVertex2f(30.0, 20.0)
    glEnd()

    # Roof outline
    glBegin(GL_LINES)
    glVertex2f(27.0, 55.0); glVertex2f(50.0, 75.0)
    glVertex2f(50.0, 75.0); glVertex2f(73.0, 55.0)
    glVertex2f(27.0, 55.0); glVertex2f(73.0, 55.0)
    glEnd()

    # ---- Door (two triangles) ----
    glColor3f(0.40, 0.25, 0.12)
    glBegin(GL_TRIANGLES)
    # door rectangle: (46,20), (54,20), (54,40), (46,40)
    glVertex2f(46.0, 20.0)
    glVertex2f(54.0, 20.0)
    glVertex2f(54.0, 40.0)

    glVertex2f(46.0, 20.0)
    glVertex2f(54.0, 40.0)
    glVertex2f(46.0, 40.0)
    glEnd()

    # Door outline
    glColor3f(0.15, 0.10, 0.06)
    glBegin(GL_LINES)
    glVertex2f(46.0, 20.0); glVertex2f(54.0, 20.0)
    glVertex2f(54.0, 20.0); glVertex2f(54.0, 40.0)
    glVertex2f(54.0, 40.0); glVertex2f(46.0, 40.0)
    glVertex2f(46.0, 40.0); glVertex2f(46.0, 20.0)
    glEnd()

    # Door knob (GL_POINTS)
    glPointSize(6.0)
    glColor3f(0.90, 0.85, 0.20)
    glBegin(GL_POINTS)
    glVertex2f(52.5, 30.0)
    glEnd()

    # ---- Windows (lines only) ----
    def window(cx, cy, w=10.0, h=10.0):
        x0, x1 = cx - w/2.0, cx + w/2.0
        y0, y1 = cy - h/2.0, cy + h/2.0

        # frame
        glColor3f(0.25, 0.25, 0.30)
        glBegin(GL_LINES)
        glVertex2f(x0, y0); glVertex2f(x1, y0)
        glVertex2f(x1, y0); glVertex2f(x1, y1)
        glVertex2f(x1, y1); glVertex2f(x0, y1)
        glVertex2f(x0, y1); glVertex2f(x0, y0)
        # cross
        glVertex2f(cx, y0); glVertex2f(cx, y1)
        glVertex2f(x0, cy); glVertex2f(x1, cy)
        glEnd()

    window(38.0, 42.0)
    window(62.0, 42.0)

    # ---- Chimney (two triangles + outline) ----
    glColor3f(0.60, 0.30, 0.30)
    glBegin(GL_TRIANGLES)
    # chimney rect: (60,62), (66,62), (66,74), (60,74)
    glVertex2f(60.0, 62.0)
    glVertex2f(66.0, 62.0)
    glVertex2f(66.0, 74.0)

    glVertex2f(60.0, 62.0)
    glVertex2f(66.0, 74.0)
    glVertex2f(60.0, 74.0)
    glEnd()

    glColor3f(0.20, 0.12, 0.12)
    glBegin(GL_LINES)
    glVertex2f(60.0, 62.0); glVertex2f(66.0, 62.0)
    glVertex2f(66.0, 62.0); glVertex2f(66.0, 74.0)
    glVertex2f(66.0, 74.0); glVertex2f(60.0, 74.0)
    glVertex2f(60.0, 74.0); glVertex2f(60.0, 62.0)
    glEnd()


def draw_raindrops():
    """
    Each raindrop is a short slanted line (GL_LINES).
    """
    glColor3f(0.35, 0.65, 1.00)
    glLineWidth(2.0)
    glBegin(GL_LINES)
    for x, y, length, drift in drops:
        # slant slightly
        glVertex2f(x, y)
        glVertex2f(x + 0.6, y - length)
    glEnd()


def draw_clouds_simple():
    """
    Simple clouds made ONLY from triangles (a few triangles approximating blobs).
    Not necessary, but makes the scene nicer while still respecting primitive rules.
    """
    glColor3f(0.92, 0.92, 0.95)

    def tri(ax, ay, bx, by, cx, cy):
        glVertex2f(ax, ay); glVertex2f(bx, by); glVertex2f(cx, cy)

    glBegin(GL_TRIANGLES)
    # Left cloud
    tri(10, 85, 18, 90, 26, 85)
    tri(18, 90, 26, 85, 30, 92)
    tri(18, 90, 10, 85, 12, 93)
    tri(26, 85, 30, 92, 34, 86)

    # Right cloud
    tri(68, 88, 76, 93, 84, 88)
    tri(76, 93, 84, 88, 88, 96)
    tri(76, 93, 68, 88, 70, 96)
    tri(84, 88, 88, 96, 92, 90)
    glEnd()


# ----------------------------
# Animation / update
# ----------------------------
def update_rain():
    global drops
    for d in drops:
        d[0] += d[3]               # drift
        d[1] -= rain_speed         # fall

        # wrap if below ground line, respawn on top
        if d[1] < 18.0:
            d[0] = random.uniform(5.0, 95.0)
            d[1] = random.uniform(95.0, 115.0)
            d[2] = random.uniform(2.0, 5.0)
            d[3] = random.uniform(-0.08, 0.08)

        # keep x within bounds
        d[0] = (d[0] - WORLD_MIN) % (WORLD_MAX - WORLD_MIN) + WORLD_MIN


def timer(_):
    update_rain()
    glutPostRedisplay()
    glutTimerFunc(16, timer, 0)  # ~60 FPS


# ----------------------------
# GLUT callbacks
# ----------------------------
def display():
    glClear(GL_COLOR_BUFFER_BIT)

    # Sky background (single huge rectangle via two triangles)
    glColor3f(0.08, 0.10, 0.18)
    glBegin(GL_TRIANGLES)
    glVertex2f(0.0, 0.0)
    glVertex2f(100.0, 0.0)
    glVertex2f(100.0, 100.0)

    glVertex2f(0.0, 0.0)
    glVertex2f(100.0, 100.0)
    glVertex2f(0.0, 100.0)
    glEnd()

    draw_clouds_simple()
    draw_raindrops()
    draw_house()

    glutSwapBuffers()


def reshape(w, h):
    global W, H
    W, H = w, h
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(WORLD_MIN, WORLD_MAX, WORLD_MIN, WORLD_MAX)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def keyboard(key, x, y):
    global rain_speed
    k = key.decode("utf-8", errors="ignore").lower()

    if key == b"\x1b":  # ESC
        sys.exit(0)
    elif k == "+" or key == b"=":
        rain_speed = clamp(rain_speed + 0.1, 0.0, 5.0)
    elif k == "-" or key == b"_":
        rain_speed = clamp(rain_speed - 0.1, 0.0, 5.0)
    elif k == "r":
        reset_drops()


def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glDisable(GL_DEPTH_TEST)
    reset_drops()


def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(W, H)
    glutCreateWindow(b"House + Animated Rain (GL_POINTS/GL_LINES/GL_TRIANGLES only)")

    init()

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutTimerFunc(0, timer, 0)

    glutMainLoop()


if __name__ == "__main__":
    main()
