# ====== PyOpenGL Multiple Bouncing Balls ======
# Features:
#   - Draws coordinate axes, triangle, and square
#   - Left-click to create unlimited balls
#   - Each ball has:
#       * Random color
#       * Random direction
#       * Random speed
#   - Balls bounce off all four walls
#   - Right-click creates an extra point
#   - UP/DOWN changes speed of all balls
#   - W/S changes size of all balls
#
# Author: Abid Jahan Apon (Modified)
# ==============================================

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

# ================= Global Variables =================

WINDOW_WIDTH = 500
WINDOW_HEIGHT = 500

BALL_SIZE = 8
BALL_SPEED = 3.0      # Current speed of all balls
balls = []          # Stores all balls
new_point = None    # Right-click point

LEFT = -250
RIGHT = 250
BOTTOM = -250
TOP = 250
blink = False          # Initially no blinking
show_balls = True      # Whether balls are currently visible
frame_count = 0

# ================= Coordinate Conversion =================

def convert_coordinate(x, y):
    """Convert screen coordinates to OpenGL coordinates."""
    a = x - WINDOW_WIDTH / 2
    b = WINDOW_HEIGHT / 2 - y
    return a, b


# ================= Drawing Functions =================

def draw_point(x, y, size, color):
    glPointSize(size)
    glColor3f(color[0], color[1], color[2])

    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()


def draw_axes():

    glLineWidth(1)

    glBegin(GL_LINES)

    # X-axis
    glColor3f(1, 0, 0)
    glVertex2f(-250, 0)
    glVertex2f(250, 0)

    # Y-axis
    glColor3f(0, 0, 1)
    glVertex2f(0, -250)
    glVertex2f(0, 250)

    glEnd()

    # Origin
    glPointSize(5)
    glColor3f(0, 1, 0)

    glBegin(GL_POINTS)
    glVertex2f(0, 0)
    glEnd()


def draw_shapes():

    # Triangle
    glBegin(GL_TRIANGLES)

    glColor3f(1, 0, 0)
    glVertex2f(-160, 150)

    glColor3f(0, 1, 0)
    glVertex2f(-180, 150)

    glColor3f(0, 0, 1)
    glVertex2f(-170, 170)

    glEnd()

    # Square
    glBegin(GL_QUADS)

    glColor3f(1, 0, 1)
    glVertex2f(-170, 120)

    glColor3f(0, 0, 1)
    glVertex2f(-150, 120)

    glColor3f(0, 1, 0)
    glVertex2f(-150, 140)

    glColor3f(1, 1, 0)
    glVertex2f(-170, 140)

    glEnd()


# ================= Keyboard =================

def keyboard_listener(key, x, y):

    if key == b'w':

        for ball in balls:
            ball["size"] += 1

    elif key == b's':

        for ball in balls:
            ball["size"] = max(1, ball["size"] - 1)

    glutPostRedisplay()


def special_key_listener(key, x, y):

    global BALL_SPEED

    if key == GLUT_KEY_UP:

        BALL_SPEED *= 1.2

        for ball in balls:
            ball["dx"] *= 1.2
            ball["dy"] *= 1.2

        print("Speed Increased")

    elif key == GLUT_KEY_DOWN:

        BALL_SPEED /= 1.2

        for ball in balls:
            ball["dx"] /= 1.2
            ball["dy"] /= 1.2

        print("Speed Decreased")

    glutPostRedisplay()


# ================= Mouse =================

def mouse_listener(button, state, x, y):

    global new_point

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:

        x, y = convert_coordinate(x, y)

        angle = random.uniform(0, 2 * math.pi)
        dx = math.cos(angle) * BALL_SPEED
        dy = math.sin(angle) * BALL_SPEED

        color = (
            random.random(),
            random.random(),
            random.random()
        )

        balls.append({
            "x": x,
            "y": y,
            "dx": dx,
            "dy": dy,
            "color": color,
            "size": BALL_SIZE
        })

        print("Ball Created")

    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:

        global blink

        new_point = convert_coordinate(x, y)

        blink = not blink      # Toggle blinking ON/OFF


# ================= Projection =================

def setup_projection():

    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    glOrtho(-250, 250, -250, 250, -1, 1)

    glMatrixMode(GL_MODELVIEW)


# ================= Display =================

def display():

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glLoadIdentity()

    setup_projection()

    draw_axes()
    draw_shapes()

    # Draw all balls
    if blink:
        for ball in balls:
            draw_point(
                ball["x"],
                ball["y"],
                ball["size"],
                ball["color"]
            )

    # Bounding L shape
    glColor3f(1, 1, 1)

    glBegin(GL_LINES)

    glVertex2f(180, 0)
    glVertex2f(180, 180)

    glVertex2f(180, 180)
    glVertex2f(0, 180)

    glEnd()

    # Draw right-click point
    if new_point is not None:

        draw_point(
            new_point[0],
            new_point[1],
            8,
            (0.7, 0.8, 0.6)
        )

    glutSwapBuffers()


# ================= Animation =================

def animate():
    global blink, frame_count, frame_count, show_balls

    if blink:
        frame_count += 1

        if frame_count >= 20:
            show_balls = not show_balls
            frame_count = 0
    else:
        show_balls = True

    frame_count += 1

    # Toggle every 20 frames
    if frame_count >= 20:
        blink = not blink
        frame_count = 0
    for ball in balls:

        ball["x"] += ball["dx"]
        ball["y"] += ball["dy"]

        # Left wall
        if ball["x"] <= LEFT:
            ball["x"] = LEFT
            ball["dx"] *= -1

        # Right wall
        if ball["x"] >= RIGHT:
            ball["x"] = RIGHT
            ball["dx"] *= -1

        # Bottom wall
        if ball["y"] <= BOTTOM:
            ball["y"] = BOTTOM
            ball["dy"] *= -1

        # Top wall
        if ball["y"] >= TOP:
            ball["y"] = TOP
            ball["dy"] *= -1

    glutPostRedisplay()


# ================= Main =================

def main():

    glutInit()

    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)

    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)

    glutCreateWindow(b"Multiple Bouncing Balls")

    glClearColor(0, 0, 0, 1)

    glutDisplayFunc(display)
    glutIdleFunc(animate)

    glutKeyboardFunc(keyboard_listener)
    glutSpecialFunc(special_key_listener)
    glutMouseFunc(mouse_listener)

    glutMainLoop()


# ================= Entry =================

if __name__ == "__main__":
    main()