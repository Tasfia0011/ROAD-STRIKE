from OpenGL.GL import *      # Core OpenGL functions
from OpenGL.GLUT import *    # GLUT library for window and input handling
from OpenGL.GLU import *     # OpenGL Utility library
import time
import random

WINDOW_WIDTH, WINDOW_HEIGHT = 500, 500
game_over=False
play_pause=False
cheat_code=False
score=0
init_time=time.time()
delay_time=0
tray_pos_x=WINDOW_WIDTH//10
tray_pos_y=10
tray_width=60
tray_height=10
tray_speed=500
tray_speed_increase=10
tray_color=(0.0, 1.0, 0.0)
ball_pos_x=random.randint(10, WINDOW_WIDTH-10)
ball_pos_y=WINDOW_HEIGHT-50
ball_size=10
ball_speed=120
ball_speed_increase=15
ball_color=(random.random(), random.random(), random.random())
restart_pos=(WINDOW_WIDTH/15*1, WINDOW_HEIGHT-28)
play_pause_pos=(WINDOW_WIDTH/6*3, WINDOW_HEIGHT-28)
end_pos=(WINDOW_WIDTH/5*4.5, WINDOW_HEIGHT-30)
btn_size=10


def zone_finder(x1, y1, x2, y2):
    dx=x2-x1
    dy=y2-y1
    zone=0
    if abs(dx)>=abs(dy):
        if dx>=0 and dy>=0:
            zon=0
        elif dx<0 and dy>=0:
            zone= 3
        elif dx<0 and dy<0:
            zone= 4
        elif dx>=0 and dy<0:
            zone=7
    else:
        if dx>=0 and dy>0:
            zone= 1
        elif dx<0 and dy>0:
            zone= 2
        elif dx<0 and dy<0:
            zone=5
        elif dx>=0 and dy<0:
            zone=6
    return zone

def convert_to(x, y, zone):
    a,b=0,0
    if zone==0:
        a=x
        b=y
    elif zone==1:
        a=y
        b=x
    elif zone==2:
        a=y
        b=-x
    elif zone==3:
        a=-x
        b=y
    elif zone==4:
        a=-x
        b=-y
    elif zone==5:
        a=-y
        b=-x
    elif zone==6:
        a=-y
        b=x
    elif zone==7:
        a=x
        b=-y
    return a,b

def convert_from(x, y, zone):
    a,b=0,0
    if zone==0:
        a=x
        b=y
    elif zone==1:
        a=y
        b=x
    elif zone==2:
        a=-y
        b=x
    elif zone==3:
        a=-x
        b=y
    elif zone==4:
        a=-x
        b=-y
    elif zone==5:
        a=-y
        b=-x
    elif zone==6:
        a=y
        b=-x
    elif zone==7:
        a=x
        b=-y
    return a,b

def Draw_point(x1, y1, x2, y2):
    dx=x2-x1
    dy=y2-y1
    d=2*dy-dx
    incrE=2*dy
    incrNE=2*(dy-dx)
    x=x1
    y=y1
    axy=[]
    while x<=x2:
        axy.append((x, y))
        if d<=0:
            d+=incrE
            x+=1
        else:
            d+=incrNE
            x+=1
            y+=1
    return axy

def Draw_line(x1, y1, x2, y2):
    zone=zone_finder(x1, y1, x2, y2)
    a1, b1=convert_to(x1, y1, zone)
    a2, b2=convert_to(x2, y2, zone)
    pointer=Draw_point(a1, b1, a2, b2)
    glPointSize(2)
    glBegin(GL_POINTS)
    for j, k in pointer:
        x, y=convert_from(j, k, zone)
        glVertex2f(x, y)
    glEnd()


def Draw_tray(x, y, width, height, color):
    glColor3f(*color)
    w=width//1
    h=height
    Draw_line(int(x-w)+10, int(y), int(x+w)-10, int(y))
    Draw_line(int(x-w)+10, int(y), int(x-w), int(y+h))
    Draw_line(int(x+w)-10, int(y), int(x+w), int(y+h))
    Draw_line(int(x-w), int(y+h), int(x+w), int(y+h))

def Draw_ball(x, y, w, color):
    glColor3f(*color)
    Draw_line(int(x), int(y+w), int(x+w), int(y))
    Draw_line(int(x+w), int(y), int(x), int(y-w))
    Draw_line(int(x), int(y-w), int(x-w), int(y))
    Draw_line(int(x-w), int(y), int(x), int(y+w))

def Draw_close(x, y, w):
    glColor3f(1.0, 0.0, 0.0)  
    Draw_line(int(x-w), int(y-w), int(x+w), int(y+w))
    Draw_line(int(x-w), int(y+w), int(x+w), int(y-w))

def Draw_play(x, y, w):
    glColor3f(0.76, 0.45, 0.26)
    Draw_line(int(x-w), int(y-w), int(x+w), int(y))
    Draw_line(int(x+w), int(y), int(x-w), int(y+w))
    Draw_line(int(x-w), int(y+w), int(x-w), int(y-w))
def pause(x, y, w):
    glColor3f(0.26, 0.76, 0.35)
    a=w//2
    Draw_line(int(x-a), int(y-w), int(x-a), int(y+w))
    Draw_line(int(x+a), int(y-w), int(x+a), int(y+w))

def new_game(x, y, w):
    glColor3f(0, 0.55, 1)
    Draw_line(int(x+w), int(y+w), int(x), int(y))
    Draw_line(int(x), int(y), int(x+w), int(y-w))
    Draw_line(int(x), int(y), int(x+w), int(y))

def new_ball():
    global ball_pos_x, ball_pos_y, ball_color
    ball_pos_x=random.randint(ball_size, WINDOW_WIDTH-ball_size)
    ball_pos_y=WINDOW_HEIGHT-50
    ball_color=(random.uniform(0.5, 1.0), random.uniform(0.5, 1.0), random.uniform(0.5, 1.0))

def catch_checker():
    return(ball_pos_x-ball_size<tray_pos_x+tray_width//2 and
           ball_pos_x+ball_size>tray_pos_x-tray_width//2 and
           ball_pos_y+ball_size>tray_pos_y and
           ball_pos_y-ball_size<tray_pos_y+tray_height)

def game_restart():
    global game_over, score, ball_speed, tray_color, tray_pos_x
    game_over=False
    score=0
    ball_speed=100
    tray_color=(1.0, 1.0, 1.0)
    tray_pos_x=WINDOW_WIDTH//2
    new_ball()
    print("Start Again!")

def keyboard_listener(key, x, y):
    """Handles normal keyboard inputs."""
    global ball_size, cheat_code
    if key == b'c': 
        if cheat_code==False:
            cheat_code=True
            print("Cheat Code Mode: ON")
        else:  
            cheat_code=False
            print("Cheat Code Mode: OFF")
    glutPostRedisplay()


def special_key_listener(key, x, y):
    """Handles special keys (arrows, F-keys, etc.)."""
    global tray_pos_x
    if play_pause or game_over:
        return
    move=ball_size
    if key == GLUT_KEY_LEFT:
        tray_pos_x=max(tray_width//2, tray_pos_x-move)
    elif key == GLUT_KEY_RIGHT:
        tray_pos_x=min(WINDOW_WIDTH-tray_width//2, tray_pos_x+move)
    glutPostRedisplay()


def mouse_listener(button, state, x, y):
    """
    Handles mouse clicks.
    Left-click: Move ball.
    Right-click: Create a new point.
    """
    global play_pause
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        gl_y=WINDOW_HEIGHT-y
        if restart_pos[0]-btn_size<x<restart_pos[0]+btn_size and restart_pos[1]-btn_size<gl_y<restart_pos[1]+btn_size:
            game_restart()
        elif play_pause_pos[0]-btn_size<x<play_pause_pos[0]+btn_size and play_pause_pos[1]-btn_size<gl_y<play_pause_pos[1]+btn_size:
            if play_pause:
                play_pause=False
                print("Game Is Resume")
            else:
                play_pause=True
                print("Game Is Paused")
        elif end_pos[0]-btn_size<x<end_pos[0]+btn_size and end_pos[1]-btn_size<gl_y<end_pos[1]+btn_size:
            print(f"Goodbye!Your Final Score: {score}")
            glutLeaveMainLoop()        


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, 0, 1)
    glMatrixMode(GL_MODELVIEW)

    new_game(restart_pos[0], restart_pos[1], btn_size)
    
    if play_pause:
        Draw_play(play_pause_pos[0], play_pause_pos[1], btn_size)
    else:
        pause(play_pause_pos[0], play_pause_pos[1], btn_size)
    
    Draw_close(end_pos[0], end_pos[1], btn_size)
    Draw_tray(tray_pos_x, tray_pos_y, tray_width, tray_height, tray_color)
    if not game_over:
        Draw_ball(ball_pos_x, ball_pos_y, ball_size, ball_color)
    glutSwapBuffers()

def animate():
    global ball_pos_y, ball_speed, score, game_over, tray_color, tray_speed, cheat_code   
    global init_time, delay_time, tray_pos_x
    present_time=time.time()
    delay_time=present_time-init_time
    init_time=present_time
    if game_over or play_pause:
        glutPostRedisplay()
        return

    if cheat_code:
        if tray_pos_x<ball_pos_x:
            tray_pos_x=min(ball_pos_x, tray_pos_x + tray_speed * delay_time)
        elif tray_pos_x>ball_pos_x:
            tray_pos_x=max(ball_pos_x, tray_pos_x-tray_speed*delay_time)
        tray_pos_x=max(tray_width//2, min(WINDOW_WIDTH-tray_width//2, tray_pos_x))
    ball_pos_y-=ball_speed*delay_time

    if catch_checker():
        score+=1
        ball_speed+=ball_speed_increase
        tray_speed+=tray_speed_increase
        print(f"Score: {score}")
        new_ball()

    if ball_pos_y<0:
        game_over=True
        tray_color=(1.0, 0.0, 0.0)
        print(f"OOps! Game Over! Final Score: {score} Better luck next time!!")    
    glutPostRedisplay()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Diamond Catcher!")
    glutDisplayFunc(display)
    glutIdleFunc(animate)
    glutKeyboardFunc(keyboard_listener)
    glutSpecialFunc(special_key_listener)
    glutMouseFunc(mouse_listener)
    glutMainLoop()
    
if __name__ == "__main__":
    main()
