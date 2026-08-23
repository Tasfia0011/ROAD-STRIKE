from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math

WINDOW_WIDTH, WINDOW_HEIGHT = 1000, 800
GRID_LENGTH = 600

fovY = 80
cam_ht = 600 
cam_rad = 900 
cam_angle = 0
cam_config = 0    
p_in_position = [0, 0] 
p_in_angle = 90   
p_in_speed = 8
bults = []   
enem_L = []
Max_enem = 5
Enem_speed = 0.2 
P_score = 0
p_health = 5
bults_missed = 0
End_game = False
Cheat_media = False
Cheat_V = False
Re_load = 0


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT) 
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def enem():
    side = random.choice(['top', 'bottom', 'left', 'right'])
    if side == 'top':    
        x = random.randint(-GRID_LENGTH, GRID_LENGTH)
        y = GRID_LENGTH
    elif side == 'bottom': 
        x = random.randint(-GRID_LENGTH, GRID_LENGTH)
        y = -GRID_LENGTH
    elif side == 'left':   
        x = -GRID_LENGTH
        y = random.randint(-GRID_LENGTH, GRID_LENGTH)
    elif side == 'right':                  
        x = GRID_LENGTH
        y = random.randint(-GRID_LENGTH, GRID_LENGTH)
    
    enem_L.append({
        'x': x, 
        'y': y, 
        'Sz': 1.0, 
        'Chng': 0.02
    })


def re_game():
    global p_in_position, p_in_angle, bults, enem_L, P_score, p_health, bults_missed, End_game
    p_in_position = [0, 0]
    p_in_angle = 90
    bults = []
    enem_L = []
    P_score = 0
    p_health = 5
    bults_missed = 0
    End_game = False
    for i in range(Max_enem):
        enem()

def distance(a,b):
    return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

def draw_shaped_player():
    global p_in_position, p_in_angle, End_game
    glPushMatrix()
    glTranslatef(p_in_position[0], p_in_position[1], 15)
    if End_game:
        glRotatef(90, 1, 0, 0) 
    glRotatef(p_in_angle - 90, 0, 0, 1) 
    
    glColor3f(0, 0, 0)
    glPushMatrix()
    glTranslatef(0, 0, 30)
    gluSphere(gluNewQuadric(), 12, 10, 10)
    glPopMatrix()


    glColor3f(0.2, 0.4, 0.2) 
    glPushMatrix()
    glScalef(1, 0.5, 1.5)
    glutSolidCube(30)
    glPopMatrix()

    glColor3f(0.2, 0.4, 0.2) 
    glPushMatrix()
    glScalef(1, 0.5, 1.5)
    glutSolidCube(30)
    glPopMatrix()

    glColor3f(1.0, 0.8, 0.6)
    glPushMatrix()
    glTranslatef(-20, 0, 5)   
    glRotatef(-90, 1, 0, 0) 
    gluCylinder(gluNewQuadric(), 4, 1, 25, 10, 10)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(20, 0, 5)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 4, 1, 25, 10, 10)
    glPopMatrix()

    glColor3f(0.7, 0.7, 0.7)
    glPushMatrix()
    glTranslatef(15, 10, 10) 
    glRotatef(90, 0, 1, 0)
    glScalef(3, 0.5, 0.5)
    glutSolidCube(20)
    glPopMatrix()
    

    glColor3f(0, 0, 1)
    glPushMatrix()
    glTranslatef(-8, 0, -20)
    gluCylinder(gluNewQuadric(), 4, 3, 20, 10, 10)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(8, 0, -20)
    gluCylinder(gluNewQuadric(), 4, 3, 20, 10, 10)
    glPopMatrix()
    
    glPopMatrix()
    

def draw_enem():
    for e in enem_L:
        glPushMatrix()
        glTranslatef(e['x'], e['y'], 15)
        Sz = e['Sz']
        glScalef(Sz, Sz, Sz)
        glColor3f(1, 0, 0)
        gluSphere(gluNewQuadric(), 20, 15, 15)
        glColor3f(0, 0, 0)
        glTranslatef(0, 0, 15)
        gluSphere(gluNewQuadric(), 10, 10, 10)
        glPopMatrix()

def draw_bults():
    glColor3f(1, 1, 0) 
    for b in bults:
        glPushMatrix()
        glTranslatef(b['x'], b['y'], 15) 
        glutSolidCube(10)
        glPopMatrix()

def keyboardListener(key, x, y):
    global p_in_position, p_in_angle, Cheat_media, Cheat_V
    
    if End_game and key == b'r':
        re_game()
        return

    if not End_game:
        step_x = math.cos(math.radians(p_in_angle)) * p_in_speed
        step_y = math.sin(math.radians(p_in_angle)) * p_in_speed

        if key == b's': 
            if -GRID_LENGTH < p_in_position[0] - step_x < GRID_LENGTH:
                p_in_position[0] -= step_x
            if -GRID_LENGTH < p_in_position[1] - step_y < GRID_LENGTH:
                p_in_position[1] -= step_y

        if key == b'w': 
            if -GRID_LENGTH < p_in_position[0] + step_x < GRID_LENGTH:
                p_in_position[0] += step_x
            if -GRID_LENGTH < p_in_position[1] + step_y < GRID_LENGTH:
                p_in_position[1] += step_y
  
        if key == b'd': 
            p_in_angle -= 3 
  
        if key == b'a': 
            p_in_angle += 3 
      
        if key == b'c':
            Cheat_media = not Cheat_media
            if Cheat_media:
                print("Cheat Mode Activated!")
            else:
                print("Cheat Mode Deactivated!")
      
        if key == b'v':
            Cheat_V = not Cheat_V
            if Cheat_V:
                print("Cheat Vision Activated!")
            else:
                print("Cheat Vision Deactivated!")

    glutPostRedisplay()

def specialKeyListener(key, x, y):
    global cam_angle, cam_ht
    
    if key == GLUT_KEY_LEFT: cam_angle -= 5
    if key == GLUT_KEY_RIGHT: cam_angle += 5
    
    if key == GLUT_KEY_UP:
        cam_ht -= 20
        if cam_ht < 100: cam_ht = 100
    if key == GLUT_KEY_DOWN:
        cam_ht += 20
        if cam_ht > 1500: cam_ht = 1500
    glutPostRedisplay()


def mouseListener(button, state, x, y):
    global cam_config, bults
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not End_game:
        rad = math.radians(p_in_angle)
        bults.append({
            'x': p_in_position[0],
            'y': p_in_position[1],
            'dx': math.cos(rad) * 10,
            'dy': math.sin(rad) * 10
        })
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        cam_config = 1 - cam_config
        glutPostRedisplay()


def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WINDOW_WIDTH/WINDOW_HEIGHT, 0.1, 3000) 
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if cam_config == 0:
        rad = math.radians(cam_angle)
        cam_x = math.sin(rad) * cam_rad
        cam_y = math.cos(rad) * -cam_rad 
        cam_z = cam_ht
        gluLookAt(cam_x, cam_y, cam_z, 0, 0, 0, 0, 0, 1)
        
    else:
        rad = math.radians(p_in_angle)
        cam_dist = 100
        cam_x = p_in_position[0] - math.cos(rad) * cam_dist
        cam_y = p_in_position[1] - math.sin(rad) * cam_dist
        cam_z = 50 if not (Cheat_media and Cheat_V) else 150
        
        target_x = p_in_position[0] + math.cos(rad) * 200
        target_y = p_in_position[1] + math.sin(rad) * 200
        target_z = 15
        
        gluLookAt(cam_x, cam_y, cam_z, target_x, target_y, target_z, 0, 0, 1)


def idle():
    global bults, enem_L, p_health, P_score, bults_missed, End_game, p_in_angle, Re_load
    if End_game: return

    if Cheat_media:
        near_distance = 99999
        targeted_enem = None
        for e in enem_L:
            d = distance(p_in_position, (e['x'], e['y']))
            if d < near_distance:
                near_distance = d
                targeted_enem = e
        if targeted_enem:
            dx = targeted_enem['x'] - p_in_position[0]
            dy = targeted_enem['y'] - p_in_position[1]
            angle_rad = math.atan2(dy, dx)
            p_in_angle = math.degrees(angle_rad)
            Re_load += 1
            if Re_load > 20: 
                bults.append({
                    'x': p_in_position[0], 'y': p_in_position[1],
                    'dx': math.cos(angle_rad) * 10, 'dy': math.sin(angle_rad) * 10
                })
                Re_load = 0

    survive_bults = []
    for b in bults:
        b['x'] += b['dx']
        b['y'] += b['dy']
        hit = False
        for c in enem_L[:]:
            if distance((b['x'], b['y']), (c['x'], c['y'])) < 30: 
                enem_L.remove(c)
                P_score += 1
                hit = True
                enem() 
                break
        if not hit:
            if -GRID_LENGTH <= b['x'] <= GRID_LENGTH and -GRID_LENGTH <= b['y'] <= GRID_LENGTH:
                survive_bults.append(b)
            else: bults_missed += 1
    bults = survive_bults

    for j in enem_L:
        ex, ey = j['x'], j['y']
        px, py = p_in_position[0], p_in_position[1]
        vis_len = distance((ex, ey), (px, py))
        if vis_len > 0:
            j['x'] += (px - ex) / vis_len * Enem_speed
            j['y'] += (py - ey) / vis_len * Enem_speed
        if vis_len < 30: 
            p_health -= 1
            enem_L.remove(j)
            enem()
        j['Sz'] += j['Chng']
        if j['Sz'] > 1.6 or j['Sz'] < 0.6: j['Chng'] *= -1

    if p_health <= 0 or bults_missed >= 10:
        End_game = True
        print("GAME OVER")
    glutPostRedisplay()


def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity() 
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)  
    setupCamera()  

    ##grid
    b=100
    glBegin(GL_QUADS)
    for i in range(-GRID_LENGTH, GRID_LENGTH, b):
        for j in range(-GRID_LENGTH, GRID_LENGTH, b):
            if ((i // b) + (j // b)) % 2 == 0:
                glColor3f(1.0, 1.0, 1.0)
            else:
                glColor3f(0.0, 1.0, 0.0)
            
            glVertex3f(i, j, 0.0)
            glVertex3f(i + b, j, 0.0)
            glVertex3f(i + b, j + b, 0.0)
            glVertex3f(i, j + b, 0.0)
    glEnd()

    #wall configs
    ht= 50
    glBegin(GL_QUADS)
    
    
    glColor3f(0, 0, 1)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH,ht)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, ht)

    glColor3f(0.7, 0.5, 0.95)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, ht)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, ht)

    glColor3f(0, 1, 1)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, ht)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, ht)
    
    glColor3f(1, 0, 1)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, ht)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, ht)
    
    glEnd()

    draw_shaped_player()
    if not End_game:
        draw_enem()
        draw_bults()
        draw_text(10, WINDOW_HEIGHT - 30, f"Player Life: {p_health}")
        draw_text(10, WINDOW_HEIGHT - 60, f"Score: {P_score}")
        draw_text(10, WINDOW_HEIGHT - 90, f"Missed: {bults_missed}")
    if End_game:
         draw_text(10, WINDOW_HEIGHT - 30, f"Game is over. Your Score is {P_score}")
         draw_text(10, WINDOW_HEIGHT - 60, f"Press 'R' to RESTART the game")
    glutSwapBuffers()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)  # Double buffering, RGB color, depth test
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)  # Window size
    glutInitWindowPosition(0, 0)  # Window position
    wind = glutCreateWindow(b"Fighting Game")  # Create the window
    re_game()
    glutDisplayFunc(showScreen)  # Register display function
    glutKeyboardFunc(keyboardListener)  # Register keyboard listener
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)  # Register the idle function to move the bullet automatically

    glutMainLoop()  # Enter the GLUT main loop

if __name__ == "__main__":
    main()
