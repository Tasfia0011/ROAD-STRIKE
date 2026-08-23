

from OpenGL.GL import *      # Core OpenGL functions
from OpenGL.GLUT import *    # GLUT library for window and input handling
from OpenGL.GLU import *     # OpenGL Utility library
import math
import random
sky = 1.0
a = 1.0
b = 1.0
c = 1.0
v=2
fade_step = 0.00002 
change = 0.05
rain_x = random.uniform(-250, 250)
rain_y = 250
rain_tilt = 0.0
WINDOW_WIDTH, WINDOW_HEIGHT = 500, 500
ball_x, ball_y = 0, 250
ball_speed = 3.0     
ball_size = 18      
n_point = False            
def convert_coordinate(x, y):

    a = x - (WINDOW_WIDTH / 2)
    b = (WINDOW_HEIGHT / 2) - y
    return a, b

def draw_shapes():
    glBegin(GL_TRIANGLES)
    glColor3f(0.2, 0.8, 0.2)  
    glVertex2f(250, -250)
    glVertex2f(-250, -250)
    glVertex2f(250, -110)
    glVertex2f(-250, -110)
    glVertex2f(250, -110)
    glVertex2f(-250, -250)
    glEnd()

    glBegin(GL_TRIANGLES)
    glColor3f(a, b, c)  
    glVertex2f(250, 250)
    glVertex2f(-250, -110)
    glVertex2f(250, -110)
    glVertex2f(-250, 250)
    glVertex2f(-250, -110)
    glVertex2f(250, 250)
    glEnd()
    glBegin(GL_TRIANGLES)
    glColor3f(0.55, 0.27, 0.07)
    glVertex2d(200, -200)
    glVertex2d(170, -200)
    glVertex2d(170, -60)
    glVertex2d(200, -200)
    glVertex2d(170, -60)
    glVertex2d(200, -60)
    glEnd()

    glBegin(GL_TRIANGLES)
    glColor3f(0.0, 0.6, 0.0)
    glVertex2d(220, -60)
    glVertex2d(150, -60)
    glVertex2d(185, 10)

    glColor3f(0.0, 0.6, 0.0)
    glVertex2d(240, -120)
    glVertex2d(130, -120)
    glVertex2d(185, -25)
    glEnd()

    glBegin(GL_TRIANGLES)
    glColor3f(0.9, 0.8, 0.6)      
    glVertex2f(-150, -200)
    glVertex2f(150, -200)
    glVertex2f(150, -50)
    glVertex2f(-150, -200)
    glVertex2f(150, -50)
    glVertex2f(-150, -50)
    glEnd()

    glBegin(GL_TRIANGLES)
    glColor3f(1, 0, 1)      
    glVertex2f(-180, -50)
    glVertex2f(0, 50)
    glVertex2f(180, -50)
    glEnd()

    glBegin(GL_TRIANGLES)
    glColor3f(0.4, 0.2, 0.1)  
    glVertex2f(-30, -200)
    glVertex2f(30, -200)
    glVertex2f(30, -95)
    glVertex2f(-30, -200)
    glVertex2f(30, -95)
    glVertex2f(-30, -95)
    glEnd()

    glBegin(GL_TRIANGLES)
    glColor3f(0.6, 0.85, 1.0)  
    glVertex2f(-120, -150)
    glVertex2f(-70, -150)
    glVertex2f(-70, -110)
    glVertex2f(-120, -150)
    glVertex2f(-70, -110)
    glVertex2f(-120, -110)
    glColor3f(0.6, 0.85, 1.0)  
    glVertex2f(70, -150)
    glVertex2f(120, -150)
    glVertex2f(120, -110)
    glVertex2f(70, -150)
    glVertex2f(120, -110)
    glVertex2f(70, -110)
    glEnd()

    glBegin(GL_TRIANGLES)
    glColor3f(0.55, 0.27, 0.07)
    glVertex2d(-200, -220)
    glVertex2d(-170, -220)
    glVertex2d(-170, -60)
    glVertex2d(-200, -220)
    glVertex2d(-170, -60)
    glVertex2d(-200, -60)
    glEnd()

    glBegin(GL_TRIANGLES)
    glColor3f(0.0, 0.6, 0.0)
    glVertex2d(-220, -60)
    glVertex2d(-150, -60)
    glVertex2d(-185, 10)

    glColor3f(0.0, 0.6, 0.0)
    glVertex2d(-240, -120)
    glVertex2d(-130, -120)
    glVertex2d(-185, -25)
    glEnd()

def draw_rain():
    global rain_x, rain_y, rain_tilt
    glColor3f(0.0, 0.0, 0.0)
    glLineWidth(1.5)
    glBegin(GL_LINES)
    glVertex2f(rain_x, rain_y)
    glVertex2f(rain_x + rain_tilt, rain_y - 20)
    glEnd()


def update_rain():
    global rain_x, rain_y
    rain_y -= 3
    if rain_y < -250:
        rain_y = 250
        rain_x = random.uniform(-250, 250)    

def special_key_listener(key, x, y):
    global sky, a, b, c, rain_tilt
    if key == GLUT_KEY_RIGHT:
        rain_tilt = min(rain_tilt + 1.0, 20.0) 
        print("Rain tilting right:", rain_tilt)

    elif key == GLUT_KEY_LEFT:
        if rain_tilt > 0:
            rain_tilt = max(rain_tilt - 1.0, 0.0)
        else:
            rain_tilt = max(rain_tilt - 1.0, -20.0) 
        print("Rain tilt:", rain_tilt)

    if key == GLUT_KEY_UP:
        while a != 1.0 and b != 1.0 and c != 1.0:
            a +=0.25
            b +=0.25
            c +=0.25
        v=1    
        print("Day mode")

    elif key == GLUT_KEY_DOWN:
        while a != 0.0 and b != 0.0 and c != 0.0:
            a -=0.25
            b -=0.25
            c -=0.25
        v=0    
        print("Night mode")

    glutPostRedisplay()

def mouse_listener(button, state, x, y):
    """
    Handles mouse clicks.
    Left-click: Move ball.
    Right-click: Create a new point.
    """
    global ball_x, ball_y, n_point
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        ball_x, ball_y = convert_coordinate(x, y)
        print(f"Ball moved to ({ball_x}, {ball_y})")

    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        n_point = convert_coordinate(x, y)
        print(f"New point created at {n_point}")

def setup_projection():
    """Defines a 2D orthographic coordinate system."""
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-250, 250, -250, 250, 0, 1)
    glMatrixMode(GL_MODELVIEW)

def display():
    """Main display callback for rendering each frame."""
    global a, b, c, v
    if a < 1.0 and b < 1.0 and c < 1.0 and (v==1.0):
        a = min(1.0, a + fade_step)
        b = min(1.0, b + fade_step)
        c = min(1.0, c + fade_step)
    elif a > 0.0 and b > 0.0 and c > 0.0 and (v==1.0):
        a = min(0.0, a - fade_step)
        b = min(0.0, a - fade_step)
        c = min(0.0, a - fade_step)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    setup_projection()
    draw_shapes()
    draw_rain()
    glColor3f(1, 1, 1)
    glBegin(GL_LINES)
    glEnd()
    

    if n_point:
        px, py = n_point
        glColor3f(0.7, 0.8, 0.6)
        draw_point(px, py, 6)
    glutSwapBuffers()
    glClearColor(sky, sky, sky, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)



def animate():
    """Continuously moves the ball diagonally."""
    global ball_x, ball_y, ball_speed
    ball_x = (ball_x + ball_speed) % 100
    ball_y = (ball_y + ball_speed) % 100
    update_rain()
    glutPostRedisplay()
    update_rain()
    glutPostRedisplay()
    update_rain()
    glutPostRedisplay()
    brightness = 1.0; 
    speed = 0.001;      
    direction = -1;        
    glutPostRedisplay()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_RGBA)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA)
    glutInitWindowSize(500, 500)

    glutCreateWindow(b"OpenGL Interactive Animation")

    glutDisplayFunc(display) 
    glutIdleFunc(animate)
    glutSpecialFunc(special_key_listener)
    glutMouseFunc(mouse_listener)
    glutInit()



    glutMainLoop()

if __name__ == "__main__":
    main()











