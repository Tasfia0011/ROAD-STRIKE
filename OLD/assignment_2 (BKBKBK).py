from OpenGL.GL import *     
from OpenGL.GLUT import *   
from OpenGL.GLU import *    
import random
import time 

window_width, window_height=500, 500
game_over=False
paused=False
cheat_code=False
score=0

last_time=time.time()
delta_time=0

tray_x=window_width // 10
tray_y=10
tray_width=80
tray_height=15
tray_speed=500
tray_accelerate=15
tray_color=(0.0, 1.0, 0.0)


target_x=random.randint(10, window_width - 10)
target_y=window_height-50
target_size=15
target_speed=100  
target_accelerate=10
target_color=(random.random(), random.random(), random.random()) 

restart_button_pos=(window_width/15*1, window_height - 30)
pause_button_pos=(window_width/6*3, window_height - 28)
exit_button_pos=(window_width/5*4.5, window_height - 30)
button_size=10


def find_zone(x0, y0, x1, y1):
    dx=x1-x0
    dy=y1-y0
    zone=0
    if abs(dx)>=abs(dy):
        if dx>=0 and dy>=0:
            zone=0
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

def convert_in(x, y, z):
    a,b=0,0
    if z==0:
        a=x
        b=y
    elif z==1:
        a=y
        b=x
    elif z==2:
        a=y
        b=-x
    elif z==3:
        a=-x
        b=y
    elif z==4:
        a=-x
        b=-y
    elif z==5:
        a=-y
        b=-x
    elif z==6:
        a=-y
        b=x
    elif z==7:
        a=x
        b=-y
    return a,b

def convert_out(x, y, z):
    a,b=0,0
    if z==0:
        a=x
        b=y
    elif z==1:
        a=y
        b=x
    elif z==2:
        a=-y
        b=x
    elif z==3:
        a=-x
        b=y
    elif z==4:
        a=-x
        b=-y
    elif z==5:
        a=-y
        b=-x
    elif z==6:
        a=y
        b=-x
    elif z==7:
        a=x
        b=-y
    return a,b

def points(x0, y0, x1, y1):
    dx=x1-x0
    dy=y1-y0
    d=2*dy-dx
    incrE=2*dy
    incrNE=2*(dy-dx)
    x=x0
    y=y0
    a=[]
    
    while x<=x1:
        a.append((x, y))
        if d<=0:
            d+=incrE
            x+=1
        else:
            d+=incrNE
            x+=1
            y+=1
    return a

def draw_line(x0, y0, x1, y1):
    zone=find_zone(x0, y0, x1, y1)
    
    a0, b0=convert_in(x0, y0, zone)
    a1, b1=convert_in(x1, y1, zone)
    
    points_list=points(a0, b0, a1, b1)
    glPointSize(2)
    glBegin(GL_POINTS)
    for i, j in points_list:
        x, y=convert_out(i, j, zone)
        glVertex2f(x, y)
    glEnd()

def draw_tray(x, y, width, height, color):
    glColor3f(*color)
    s=width // 1
    h=height
    
    ##bottom
    draw_line(int(x-s)+10, int(y), int(x+s)-10, int(y))
    ##left
    draw_line(int(x-s)+10, int(y), int(x-s), int(y+h))
    ##right
    draw_line(int(x+s)-10, int(y), int(x+s), int(y+h))
    ##top
    draw_line(int(x-s), int(y+h), int(x+s), int(y+h))

##diamond drawing function
def draw_target(x, y, s, c):
    glColor3f(*c)
    ##top-right
    draw_line(int(x), int(y+s), int(x+s), int(y))
    ##right-bottom
    draw_line(int(x + s), int(y), int(x), int(y-s))
    ##bottom-left
    draw_line(int(x), int(y-s), int(x-s), int(y))
    ##left-top
    draw_line(int(x-s), int(y), int(x), int(y+s))

def draw_exit(x, y, s):
    glColor3f(1.0, 0.0, 0.0)  
    draw_line(int(x-s), int(y-s), int(x+s), int(y+s))
    draw_line(int(x-s), int(y+s), int(x+s), int(y-s))

def draw_pause(x, y, s):
    glColor3f(0.27, 0.77, 0.34)
    a=s//2
    ##left
    draw_line(int(x-a), int(y-s), int(x-a), int(y+s))
    ##right
    draw_line(int(x+a), int(y-s), int(x+a), int(y+s))
    
def draw_play(x, y, s):
    glColor3f(0.77, 0.48, 0.27)
    draw_line(int(x-s), int(y-s), int(x+s), int(y))
    draw_line(int(x+s), int(y), int(x-s), int(y+s))
    draw_line(int(x-s), int(y+s), int(x-s), int(y-s))

def draw_restart(x, y, s):
    glColor3f(0, 0.58, 1)
    draw_line(int(x+s), int(y+s), int(x), int(y))
    draw_line(int(x), int(y), int(x+s), int(y-s))
    draw_line(int(x), int(y), int(x+s), int(y))

def new_target():
    global target_x, target_y, target_color
    target_x=random.randint(target_size, window_width - target_size)
    target_y=window_height-45-target_size
    target_color=(random.uniform(0.5, 1.0), random.uniform(0.5, 1.0), random.uniform(0.5, 1.0))

def game_over():
    return (target_x-target_size < tray_x+tray_width//2 and 
            target_x+target_size > tray_x-tray_width//2 and
            target_y+target_size > tray_y and
            target_y-target_size < tray_y+tray_height
            )

def restart_game():
    global game_over, score, target_speed, tray_color, tray_x
    game_over=False
    score=0
    target_speed=100
    tray_color=(1.0, 1.0, 1.0)
    tray_x=window_width // 2
    new_target()
    print("Starting Over!")


def keyboard_listener(key, x, y):
    global cheat_code
    if key==b'c':
        if (cheat_code==False):
            cheat_code=True
            print("Cheat Mode: ON")
        else:
            cheat_code=False
            print("Cheat Mode: OFF")
    glutPostRedisplay()


def special_key_listener(key, x, y):
    global tray_x
    if game_over or paused:
        return
    move_amount=target_size
    if key==GLUT_KEY_LEFT:
        tray_x=max(tray_width//2, tray_x-move_amount)
    elif key==GLUT_KEY_RIGHT:
        tray_x=min(window_width-tray_width//2, tray_x+move_amount)
    glutPostRedisplay()


def mouse_listener(button, state, x, y):
    global paused
    
    if button==GLUT_LEFT_BUTTON and state==GLUT_DOWN:
        gl_y=window_height - y
        
        ##restart
        if restart_button_pos[0]-button_size < x < restart_button_pos[0]+button_size and restart_button_pos[1]-button_size < gl_y < restart_button_pos[1]+button_size:
            restart_game()
        
        ##pause/play
        elif pause_button_pos[0]-button_size < x < pause_button_pos[0]+button_size and pause_button_pos[1]-button_size < gl_y < pause_button_pos[1]+button_size:
            if paused:
                paused=False
                print("Game Resumed")
            else:
                paused=True
                print("Game Paused")

        ##exit
        elif exit_button_pos[0]-button_size<x<exit_button_pos[0]+button_size and exit_button_pos[1]-button_size<gl_y<exit_button_pos[1]+button_size:
            print(f"Goodbye! Final Score: {score}")
            glutLeaveMainLoop()


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    glViewport(0, 0, window_width, window_height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, window_width, 0, window_height, 0, 1)
    glMatrixMode(GL_MODELVIEW)
    
    ##buttons
    draw_restart(restart_button_pos[0], restart_button_pos[1], button_size)
    
    if paused:
        draw_play(pause_button_pos[0], pause_button_pos[1], button_size)
    else:
        draw_pause(pause_button_pos[0], pause_button_pos[1], button_size)
    
    draw_exit(exit_button_pos[0], exit_button_pos[1], button_size)
    
    ##tray
    draw_tray(tray_x, tray_y, tray_width, tray_height, tray_color)
    
    ##diamond
    if not game_over:
        draw_target(target_x, target_y, target_size, target_color)
    
    glutSwapBuffers()


def animate():
    global target_y, target_speed, score, game_over, tray_color, tray_speed
    global last_time, delta_time, tray_x
    current_time=time.time()
    delta_time=current_time-last_time
    last_time=current_time
    
    if game_over or paused:
        glutPostRedisplay()
        return
    
    ##cheat mode
    if cheat_code:
        if tray_x<target_x:
            tray_x=min(target_x, tray_x + tray_speed * delta_time)
        elif tray_x>target_x:
            tray_x=max(target_x, tray_x-tray_speed*delta_time)
        tray_x=max(tray_width//2, min(window_width - tray_width // 2, tray_x))
    
    target_y-=target_speed*delta_time
    
    ##collison
    if game_over():
        score+=1
        target_speed+=target_accelerate
        tray_speed+=tray_accelerate
        print(f"Score: {score}")
        new_target()
    
    ##game over
    if target_y<0:
        game_over=True
        tray_color=(1.0, 0.0, 0.0)
        print(f"OOps! Game Over! Final Score: {score} Better luck next time!!")    
    glutPostRedisplay()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
    glutInitWindowSize(window_width, window_height)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Catch the Diamonds!")
    
    glutDisplayFunc(display)
    glutIdleFunc(animate)
    glutKeyboardFunc(keyboard_listener)
    glutSpecialFunc(special_key_listener)
    glutMouseFunc(mouse_listener)
    
    glutMainLoop()


if __name__ == "__main__":
    main()