import math
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Variables from Elem.txt and our additions
camera_pos = (0, 500, 500)
fovY = 80
GRID_LENGTH = 600
rand_var = 423
wheel_rot = 0
bike_pos_x = 0
size = 10

# Game State
speed = 0.0
rpm = 0.0
score = 0.0
road_offset = 0.0
frames = 0
game_over = False
traffic_list = []
env_list = []
headlight_on = True
view_mode = 0  # 0 for 1st person, 1 for 3rd person
paused = False
cruise_control = False
cruise_speed = 0.0
level = 1
traffic_signal = None
next_signal_score = 1500.0
turn_state = 0
turn_progress = 0.0
curve_x = 0.0
curve_z = 0.0
target_curve_x = 0.0
target_curve_z = 0.0
bank_angle = 0.0
offroad_timer = 900
player_fly_x = 0.0
player_fly_y = 0.0
player_fly_z = 90.0
player_fly_angle = 0.0
camera_angle = 0.0
accident_x = 0.0
distance = 0.0
curve_distance_timer = 0.0

quadric = None

def trigger_game_over():
    global game_over, view_mode, player_fly_x, player_fly_y, player_fly_z, player_fly_angle, camera_angle, accident_x
    if not game_over:
        game_over = True
        view_mode = 1
        player_fly_x = bike_pos_x
        player_fly_y = 0.0
        player_fly_z = 90.0
        player_fly_angle = 0.0
        camera_angle = 0.0
        accident_x = bike_pos_x

# Hardcoded Trigonometry for dial drawing since 'math' is forbidden in original, but we use it via get_sin_cos wrapper
sin_arr = {
    0: 0.0, 30: 0.5, 60: 0.866, 90: 1.0,
    120: 0.866, 150: 0.5, 180: 0.0,
    210: -0.5, 240: -0.866, 270: -1.0,
    300: -0.866, 330: -0.5
}
cos_arr = {
    0: 1.0, 30: 0.866, 60: 0.5, 90: 0.0,
    120: -0.5, 150: -0.866, 180: -1.0,
    210: -0.866, 240: -0.5, 270: 0.0,
    300: 0.5, 330: 0.866
}

speed_angles = [240, 210, 180, 150, 120, 90, 60, 30, 0, 330, 300]
speed_labels = ['0', '30', '60', '90', '120', '150', '180', '210', '240', '270', '300']
rpm_angles = [240, 210, 180, 150, 120, 90, 60, 30, 0, 330, 300]
rpm_labels = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']

def p_sin(x_deg):
    x = x_deg * 3.14159265 / 180.0
    x2 = x*x
    return x - (x*x2)/6.0 + (x*x2*x2)/120.0 - (x*x2*x2*x2)/5040.0

def p_cos(x_deg):
    x = x_deg * 3.14159265 / 180.0
    x2 = x*x
    return 1.0 - x2/2.0 + (x2*x2)/24.0 - (x2*x2*x2)/720.0

def get_sin_cos(deg):
    deg = deg % 360
    if deg < 0: deg += 360
    if deg <= 90: return p_sin(deg), p_cos(deg)
    elif deg <= 180: return p_sin(180 - deg), -p_cos(180 - deg)
    elif deg <= 270: return -p_sin(deg - 180), -p_cos(deg - 180)
    else: return -p_sin(360 - deg), p_cos(360 - deg)

def get_curve_offset(y_pos):
    dist = abs(y_pos - 500) / 1000.0
    cx = curve_x * (dist * dist)
    cz = curve_z * (dist * dist)
    return cx, cz

def get_rand():
    global rand_var
    rand_var = (rand_var * 1103515245 + 12345) % 2147483648
    return rand_var / 2147483648.0

def rand_choice(lst):
    idx = int(get_rand() * len(lst))
    return lst[idx]

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18, c=(1,1,1)):
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glColor3f(c[0], c[1], c[2])
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text: glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

def draw_mpl_line(x0, y0, x1, y1):
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    glBegin(GL_POINTS)
    if dx > dy:
        d = 2 * dy - dx
        incE = 2 * dy
        incNE = 2 * (dy - dx)
        x, y = x0, y0
        glVertex3f(x, y, 0)
        while x != x1:
            if d <= 0: d += incE; x += sx
            else: d += incNE; x += sx; y += sy
            glVertex3f(x, y, 0)
    else:
        d = 2 * dx - dy
        incN = 2 * dx
        incNE = 2 * (dx - dy)
        x, y = x0, y0
        glVertex3f(x, y, 0)
        while y != y1:
            if d <= 0: d += incN; y += sy
            else: d += incNE; x += sx; y += sy
            glVertex3f(x, y, 0)
    glEnd()

def draw_connected_wheel():
    glColor3f(0.1, 0.1, 0.1)
    glPushMatrix()
    glRotatef(90, 0, 1, 0)
    glScalef(1.0, 1.0, 1.2)
    glutSolidTorus(8, 30, 20, 20)
    glPopMatrix()
    glColor3f(0.4, 0.4, 0.4)
    glPushMatrix()
    glRotatef(90, 0, 1, 0)
    glScalef(0.5, 1.0, 1.0)
    glutSolidSphere(10, 15, 15)
    glPopMatrix()

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 15000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    angle = turn_progress * 90.0 if turn_state == 1 else turn_progress * -90.0
    cv = p_cos(angle)
    sv = p_sin(angle)

    if game_over:
        cam_y = 480
        cx, cz = get_curve_offset(cam_y)
        dx_eye = 400 * p_sin(camera_angle)
        dy_eye = -400 * p_cos(camera_angle)
        ex = accident_x + dx_eye
        ey = 480 + dy_eye
        ez = 350
        gluLookAt(ex + cx, ey, ez + cz, accident_x + cx, 480, 0 + cz, 0, 0, 1)
        return

    if view_mode == 0:
        cam_y = 500
        cx, cz = get_curve_offset(cam_y)
        dy = -1000.0
        nx = -dy * sv
        ny = dy * cv
        # Scaled down eye height to create massive road illusion
        gluLookAt(bike_pos_x + cx, cam_y, 110 + cz, 
                  bike_pos_x + nx + cx, 500 + ny, 80 + cz, 
                  0, 0, 1)
    else:
        cam_y = 900
        cx, cz = get_curve_offset(cam_y)
        dx_eye = 0
        dy_eye = 420
        er_x = dx_eye * cv - dy_eye * sv
        er_y = dx_eye * sv + dy_eye * cv
        ex = bike_pos_x + er_x
        ey = 480 + er_y
        tr_x = 480 * sv
        tr_y = -480 * cv
        tx = bike_pos_x + tr_x
        ty = 480 + tr_y
        tcx, tcz = get_curve_offset(480)
        gluLookAt(ex + cx, ey, 350 + cz, tx + tcx, ty, 0 + tcz, 0, 0, 1)

def get_color(r, g, b, x_pos, y_pos):
    s_val, cycle_val = get_sin_cos((frames % 3600) * 0.1)
    day_factor = (cycle_val + 1.0) / 2.0
    ambient = 0.35 + 0.55 * day_factor
    r_fin = r * ambient
    g_fin = g * ambient
    b_fin = b * ambient

    if headlight_on:
        dy = 500 - y_pos
        dx = x_pos - bike_pos_x
        angle = turn_progress * 90.0 if turn_state == 1 else turn_progress * -90.0
        if angle != 0:
            cv = p_cos(angle)
            sv = p_sin(angle)
            rx = dx * cv + dy * sv
            ry = -dx * sv + dy * cv
            dx = rx
            dy = ry

        if 0 < dy < 3500:
            depth_ratio = dy / 3500.0
            depth_intensity = max(0.0, 1.0 - depth_ratio)
            cone_radius = 80 + (dy * 0.25)
            if abs(dx) < cone_radius:
                edge_intensity = max(0.0, 1.0 - (abs(dx) / cone_radius)**1.5)
                intensity = depth_intensity * edge_intensity * 1.5
                r_fin += intensity * 1.0
                g_fin += intensity * 0.95
                b_fin += intensity * 0.8
                
    return (min(1.0, r_fin), min(1.0, g_fin), min(1.0, b_fin))

def draw_traffic_light(x, y, z, color_state):
    c = get_color(0.1, 0.1, 0.1, x, y)
    glColor3f(c[0], c[1], c[2])
    glPushMatrix()
    glTranslatef(x, y, z + 50)
    glScalef(15, 15, 100)
    glutSolidCube(1.0)
    glPopMatrix()
    
    c = get_color(0.2, 0.2, 0.2, x, y)
    glColor3f(c[0], c[1], c[2])
    glPushMatrix()
    glTranslatef(x, y, z + 130)
    glScalef(25, 25, 90)
    glutSolidCube(1.0)
    glPopMatrix()
    
    for i, c_val in enumerate([(1.0, 0.0, 0.0), (1.0, 0.8, 0.0), (0.0, 1.0, 0.0)]):
        if i == color_state:
            glMaterialfv(GL_FRONT, GL_EMISSION, [c_val[0], c_val[1], c_val[2], 1.0])
            glColor3f(c_val[0], c_val[1], c_val[2])
        else:
            c = get_color(c_val[0]*0.2, c_val[1]*0.2, c_val[2]*0.2, x, y)
            glColor3f(c[0], c[1], c[2])
        glPushMatrix()
        z_pos = z + 160 - (i * 30)
        x_off = 13 if x < 0 else -13
        glTranslatef(x + x_off, y, z_pos)
        glScalef(10, 10, 10)
        glutSolidSphere(1.0, 15, 15)
        glPopMatrix()
        if i == color_state:
            glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])

def draw_environment():
    global env_list
    for e in env_list:
        cx, cz = get_curve_offset(e[1])
        if e[2] == 0:
            x, y, typ, scale = e
            c = get_color(0.05, 0.05, 0.05, x, y)
            glColor3f(c[0], c[1], c[2])
            glPushMatrix()
            glTranslatef(x + cx, y, cz)
            glRotatef(bank_angle, 0, 1, 0)
            glRotatef(-90, 1, 0, 0)
            if quadric: gluCylinder(quadric, 10*scale, 10*scale, 100*scale, 10, 1)
            glTranslatef(0, 0, 80*scale)
            glutSolidCone(60*scale, 200*scale, 10, 10)
            glPopMatrix()
        else:
            x, y, typ, w, d, h, col = e
            c = get_color(0.1, 0.1, 0.1, x, y)
            glColor3f(c[0], c[1], c[2])
            glPushMatrix()
            glTranslatef(x + cx, y, h / 2 + cz)
            glScalef(w, d, h)
            glutSolidCube(1.0)
            glPopMatrix()
            
            if y < 4000:
                glMaterialfv(GL_FRONT, GL_EMISSION, [0.8, 0.8, 0.2, 1.0])
                glColor3f(0.8, 0.8, 0.2)
                inner_x = x + w/2 + 1 if x < 0 else x - w/2 - 1
                num_floors = int(h / 60)
                for fl in range(2, num_floors):
                    fz = 20 + fl * 60
                    for wy in [-d/3, 0, d/3]:
                        if (fl + int(y/100)) % 3 != 0:
                            glPushMatrix()
                            glTranslatef(inner_x + cx, y + wy, fz + cz)
                            glScalef(5, 15, 20)
                            glutSolidCube(1.0)
                            glPopMatrix()
                glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])

def draw_road():
    global road_offset
    for i in range(-45, 15):
        mark_y = i * 200 + (road_offset % 200)
        cx, cz = get_curve_offset(mark_y)

        c_gl = get_color(0.05, 0.1, 0.05, -2000, mark_y)
        glColor3f(c_gl[0], c_gl[1], c_gl[2])
        glPushMatrix()
        glTranslatef(cx, mark_y, cz)
        glRotatef(bank_angle, 0, 1, 0)
        glTranslatef(-2650, 0, -5)
        glScalef(5000, 200, 1)
        glutSolidCube(1.0)
        glPopMatrix()

        c_gr = get_color(0.05, 0.1, 0.05, 2000, mark_y)
        glColor3f(c_gr[0], c_gr[1], c_gr[2])
        glPushMatrix()
        glTranslatef(cx, mark_y, cz)
        glRotatef(bank_angle, 0, 1, 0)
        glTranslatef(2650, 0, -5)
        glScalef(5000, 200, 1)
        glutSolidCube(1.0)
        glPopMatrix()

        for j in range(-15, 15):
            rx = j * 20 + 10
            c_rd = get_color(0.05, 0.05, 0.06, rx, mark_y)
            glColor3f(c_rd[0], c_rd[1], c_rd[2])
            glPushMatrix()
            glTranslatef(cx, mark_y, cz)
            glRotatef(bank_angle, 0, 1, 0)
            glTranslatef(rx, 0, -2)
            glScalef(20.5, 200, 1)
            glutSolidCube(1.0)
            glPopMatrix()

        in_intersection = False
        if traffic_signal is not None:
            iy = traffic_signal['y'] - 600
            if abs(mark_y - iy) < 400: in_intersection = True

        if not in_intersection:
            is_black = (i % 2 == 0)
            if is_black: c_bar = get_color(0.1, 0.1, 0.1, -300, mark_y)
            else: c_bar = get_color(0.8, 0.8, 0.8, -300, mark_y)
            
            for lx in [-320, 320]:
                glColor3f(c_bar[0], c_bar[1], c_bar[2])
                glPushMatrix()
                glTranslatef(cx, mark_y, cz)
                glRotatef(bank_angle, 0, 1, 0)
                glTranslatef(lx, 0, 15)
                glScalef(40, 200, 35)
                glutSolidCube(1.0)
                glPopMatrix()
                
            c_sw = get_color(0.2, 0.2, 0.2, -450, mark_y)
            glColor3f(c_sw[0], c_sw[1], c_sw[2])
            for lx in [-450, 450]:
                glPushMatrix()
                glTranslatef(cx, mark_y, cz)
                glRotatef(bank_angle, 0, 1, 0)
                glTranslatef(lx, 0, 2)
                glScalef(220, 200, 5)
                glutSolidCube(1.0)
                glPopMatrix()
        else:
            if i % 3 == 0:
                for lx in range(-250, 251, 80):
                    c = get_color(0.9, 0.9, 0.9, lx, mark_y)
                    glColor3f(c[0], c[1], c[2])
                    glPushMatrix()
                    glTranslatef(cx, mark_y, cz)
                    glRotatef(bank_angle, 0, 1, 0)
                    glTranslatef(lx, 0, -1)
                    glScalef(40, 150, 1)
                    glutSolidCube(1.0)
                    glPopMatrix()

        if i % 2 == 0:
            for lx in [-75, 75]:
                cl = get_color(0.8, 0.8, 0.8, lx, mark_y)
                glColor3f(cl[0], cl[1], cl[2])
                glPushMatrix()
                glTranslatef(cx, mark_y, cz)
                glRotatef(bank_angle, 0, 1, 0)
                glTranslatef(lx, 0, -1)
                glScalef(10, 100, 1)
                glutSolidCube(1.0)
                glPopMatrix()
            for lx in [-225, 225]:
                cr = get_color(0.8, 0.8, 0.8, lx, mark_y)
                glColor3f(cr[0], cr[1], cr[2])
                glPushMatrix()
                glTranslatef(cx, mark_y, cz)
                glRotatef(bank_angle, 0, 1, 0)
                glTranslatef(lx, 0, -1)
                glScalef(10, 200, 1)
                glutSolidCube(1.0)
                glPopMatrix()
                
        if i % 4 == 0:
            for lx in [-340, 340]:
                glPushMatrix()
                glTranslatef(cx + lx, mark_y, cz + 30)
                glRotatef(bank_angle, 0, 1, 0)
                # Base
                c_pole = get_color(0.3, 0.3, 0.3, lx, mark_y)
                glColor3f(c_pole[0], c_pole[1], c_pole[2])
                glPushMatrix()
                glTranslatef(0, 0, 100)
                glScalef(8, 8, 200)
                glutSolidCube(1.0)
                glPopMatrix()
                
                # Arm
                arm_dir = 1 if lx < 0 else -1
                glPushMatrix()
                glTranslatef(40 * arm_dir, 0, 195)
                glScalef(80, 6, 6)
                glutSolidCube(1.0)
                glPopMatrix()
                
                # Fixture
                glPushMatrix()
                glTranslatef(80 * arm_dir, 0, 195)
                glScalef(25, 12, 6)
                glutSolidCube(1.0)
                glPopMatrix()

                # Light Bulb
                glPushMatrix()
                glTranslatef(80 * arm_dir, 0, 190)
                glMaterialfv(GL_FRONT, GL_EMISSION, [1.0, 1.0, 0.8, 1.0])
                glColor3f(1.0, 1.0, 0.8)
                glutSolidSphere(10, 15, 15)
                glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])
                glPopMatrix()
                glPopMatrix()

def draw_vehicle(v_type, c_body, t_x, t_y, t_dir):
    cx, cz = get_curve_offset(t_y)
    glPushMatrix()
    glTranslatef(cx + t_x, t_y, cz)
    glRotatef(bank_angle, 0, 1, 0)
    if t_dir == -1: glRotatef(180, 0, 0, 1)

    if v_type == 0: # Car (Width 110, Length 240)
        glColor3f(c_body[0], c_body[1], c_body[2])
        glPushMatrix()
        glTranslatef(0, 0, 40)
        glScalef(100, 240, 60)
        glutSolidCube(1.0)
        glPopMatrix()
        c_cab = get_color(0.1, 0.1, 0.1, t_x, t_y)
        glColor3f(c_cab[0], c_cab[1], c_cab[2])
        glPushMatrix()
        glTranslatef(0, -10, 90)
        glScalef(80, 120, 50)
        glutSolidCube(1.0)
        glPopMatrix()
        glMaterialfv(GL_FRONT, GL_EMISSION, [1.0, 0.0, 0.0, 1.0])
        glColor3f(1.0, 0.0, 0.0)
        for tx in [-35, 35]:
            glPushMatrix()
            glTranslatef(tx, -120, 40)
            glScalef(20, 5, 10)
            glutSolidCube(1.0)
            glPopMatrix()
        glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])
        
    elif v_type == 1: # Truck (Width 130, Length 380)
        glColor3f(c_body[0], c_body[1], c_body[2])
        glPushMatrix()
        glTranslatef(0, -90, 100)
        glScalef(120, 120, 180)
        glutSolidCube(1.0)
        glPopMatrix()
        c_trail = get_color(0.8, 0.8, 0.8, t_x, t_y)
        glColor3f(c_trail[0], c_trail[1], c_trail[2])
        glPushMatrix()
        glTranslatef(0, 50, 110)
        glScalef(120, 240, 200)
        glutSolidCube(1.0)
        glPopMatrix()
        glMaterialfv(GL_FRONT, GL_EMISSION, [1.0, 0.0, 0.0, 1.0])
        glColor3f(1.0, 0.0, 0.0)
        for tx in [-50, 50]:
            glPushMatrix()
            glTranslatef(tx, -190, 40)
            glScalef(20, 5, 10)
            glutSolidCube(1.0)
            glPopMatrix()
        glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])
        
    elif v_type == 2: # Bus (Width 120, Length 450)
        glColor3f(c_body[0], c_body[1], c_body[2])
        glPushMatrix()
        glTranslatef(0, 0, 100)
        glScalef(110, 450, 180)
        glutSolidCube(1.0)
        glPopMatrix()
        glMaterialfv(GL_FRONT, GL_EMISSION, [1.0, 0.0, 0.0, 1.0])
        glColor3f(1.0, 0.0, 0.0)
        for tx in [-45, 45]:
            glPushMatrix()
            glTranslatef(tx, -225, 40)
            glScalef(20, 5, 10)
            glutSolidCube(1.0)
            glPopMatrix()
        glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])

    elif v_type == 3: # Bike (Width 60, Length 110)
        glColor3f(c_body[0], c_body[1], c_body[2])
        glPushMatrix()
        glTranslatef(0, 0, 30)
        glScalef(30, 110, 50)
        glutSolidCube(1.0)
        glPopMatrix()
        glMaterialfv(GL_FRONT, GL_EMISSION, [1.0, 0.0, 0.0, 1.0])
        glColor3f(1.0, 0.0, 0.0)
        glPushMatrix()
        glTranslatef(0, -55, 30)
        glScalef(15, 5, 10)
        glutSolidCube(1.0)
        glPopMatrix()
        glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])
        
    glPopMatrix()

def draw_traffic():
    for t in traffic_list:
        if len(t) == 4: t.append(0)
        v_type = t[4]
        if t[2] == 1:
            if v_type == 0: c = get_color(0.2, 0.8, 0.2, t[0], t[1])
            elif v_type == 1: c = get_color(0.2, 0.5, 0.9, t[0], t[1])
            elif v_type == 2: c = get_color(0.8, 0.8, 0.2, t[0], t[1])
            else: c = get_color(0.7, 0.1, 0.7, t[0], t[1])
        else:
            if v_type == 0: c = get_color(0.8, 0.2, 0.2, t[0], t[1])
            elif v_type == 1: c = get_color(0.8, 0.4, 0.1, t[0], t[1])
            elif v_type == 2: c = get_color(0.8, 0.1, 0.5, t[0], t[1])
            else: c = get_color(0.1, 0.7, 0.7, t[0], t[1])
        draw_vehicle(v_type, c, t[0], t[1], t[2])

def draw_realistic_dial(cx, cy, radius, value, max_val, title, angles, labels):
    glPushMatrix()
    glTranslatef(cx, cy, 0)
    lo = 0.15 if headlight_on else 0.0
    glColor3f(0.02 + lo, 0.02 + lo, 0.02 + lo)
    glPushMatrix()
    glScalef(1.0, 1.0, 0.01)
    glutSolidSphere(radius, 30, 30)
    glPopMatrix()
    
    glColor3f(0.4 + lo, 0.4 + lo, 0.4 + lo)
    glPushMatrix()
    glScalef(radius, radius, 0.01)
    glutSolidTorus(0.05, 1.0, 30, 30)
    glPopMatrix()
    
    glColor3f(0.9, 0.9, 0.9)
    for target in angles:
        glPushMatrix()
        glRotatef(target, 0, 0, 1)
        glTranslatef(radius - 15, 0, 0)
        glScalef(15, 3, 0.01)
        glutSolidCube(1.0)
        glPopMatrix()

    if value > max_val: value = max_val
    if value < 0: value = 0
    fraction = value / float(max_val)
    sweep = angles[0] - angles[-1]
    if sweep < 0: sweep += 360
    needle_target = angles[0] - fraction * sweep
    
    s, c = get_sin_cos(needle_target)
    ex = (radius - 15) * c
    ey = (radius - 15) * s
    
    glClear(GL_DEPTH_BUFFER_BIT)
    glColor3f(0.8, 0.0, 0.0)
    glEnable(GL_POINT_SMOOTH)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glPointSize(2.5)
    draw_mpl_line(0, 0, ex, ey)
    glDisable(GL_BLEND)
    glDisable(GL_POINT_SMOOTH)
    glPointSize(1.0)
    
    glColor3f(0.8, 0.0, 0.0)
    glScalef(12, 12, 0.01)
    glutSolidSphere(1.0, 20, 20)
    glPopMatrix()
    
    for i, target in enumerate(angles):
        if i >= len(labels): break
        t_key = int(target) % 360
        sx = cx + (radius - 32) * cos_arr[t_key]
        sy = cy + (radius - 32) * sin_arr[t_key]
        text = labels[i]
        offset_x = len(text) * 3
        draw_text(sx - offset_x, sy - 3, text, font=GLUT_BITMAP_HELVETICA_12)
        
    draw_text(cx - len(title)*4, cy - 35, title)

def draw_dashboard():
    glClear(GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    lo = 0.05 if headlight_on else 0.0
    glColor3f(0.04 + lo, 0.04 + lo, 0.04 + lo)
    
    # Windshield / Body
    glBegin(GL_POLYGON)
    glVertex2f(0, 0)
    glVertex2f(0, 150)
    for a in range(180, -1, -1):
        s, c = get_sin_cos(a)
        glVertex2f(500 + c * 500, 150 + s * 150)
    glVertex2f(1000, 150)
    glVertex2f(1000, 0)
    glEnd()
    
    draw_realistic_dial(320, 240, 130, speed, 300.0, "KM/H", speed_angles, speed_labels)
    draw_realistic_dial(680, 240, 130, rpm, 10000.0, "x1000 RPM", rpm_angles, rpm_labels)
    
    # Center Display
    glColor3f(0.08, 0.08, 0.08)
    glBegin(GL_QUADS)
    glVertex2f(470, 180)
    glVertex2f(530, 180)
    glVertex2f(530, 300)
    glVertex2f(470, 300)
    glEnd()
    
    gear = int(speed / 50) + 1
    if gear > 6: gear = 6
    if speed == 0: gear = 1
    
    s_txt = f"{int(abs(speed))}"
    draw_text(500 - len(s_txt)*6, 260, s_txt, font=GLUT_BITMAP_TIMES_ROMAN_24, c=(0.4, 0.7, 0.9))
    draw_text(485, 245, "KM/H", font=GLUT_BITMAP_HELVETICA_10, c=(0.5, 0.5, 0.5))
    draw_text(495, 210, f"{gear}", font=GLUT_BITMAP_TIMES_ROMAN_24, c=(0.4, 0.7, 0.9))
    draw_text(485, 195, "GEAR", font=GLUT_BITMAP_HELVETICA_10, c=(0.5, 0.5, 0.5))

    # Handlebars
    glColor3f(0.12, 0.12, 0.12)
    glBegin(GL_QUADS)
    glVertex2f(0, 100)
    glVertex2f(190, 140)
    glVertex2f(190, 170)
    glVertex2f(0, 130)
    glVertex2f(1000, 100)
    glVertex2f(810, 140)
    glVertex2f(810, 170)
    glVertex2f(1000, 130)
    glEnd()
    
    glColor3f(0.6, 0.0, 0.0)
    glBegin(GL_QUADS)
    glVertex2f(890, 150)
    glVertex2f(930, 160)
    glVertex2f(930, 190)
    glVertex2f(890, 180)
    glEnd()

    # HUD
    draw_text(20, 760, "SCORE: ", font=GLUT_BITMAP_HELVETICA_18, c=(1,1,1))
    draw_text(100, 760, f"{int(score)}", font=GLUT_BITMAP_HELVETICA_18, c=(1,0.8,0))
    draw_text(20, 730, "DISTANCE: ", font=GLUT_BITMAP_HELVETICA_18, c=(1,1,1))
    draw_text(120, 730, f"{distance:.2f} KM", font=GLUT_BITMAP_HELVETICA_18, c=(0.5,1,0.5))

    draw_text(760, 760, "SPEED: ", font=GLUT_BITMAP_HELVETICA_18, c=(1,1,1))
    draw_text(840, 760, f"{int(abs(speed))}", font=GLUT_BITMAP_TIMES_ROMAN_24, c=(1,0.8,0))
    draw_text(890, 760, " KM/H", font=GLUT_BITMAP_HELVETICA_18, c=(1,1,1))
    draw_text(760, 730, "HIGH SCORE: ", font=GLUT_BITMAP_HELVETICA_18, c=(1,1,1))
    draw_text(890, 730, "5620", font=GLUT_BITMAP_HELVETICA_18, c=(0.5,1,0.5))

    if game_over:
        draw_text(20, 40, "PRESS ", font=GLUT_BITMAP_HELVETICA_18, c=(1,1,1))
        draw_text(90, 40, "R", font=GLUT_BITMAP_HELVETICA_18, c=(1,0,0))
        draw_text(110, 40, " TO RESTART", font=GLUT_BITMAP_HELVETICA_18, c=(1,1,1))

    if traffic_signal is not None:
        int_dist_in_km = (1080 - traffic_signal['y']) * 0.0003
        if 0 < int_dist_in_km <= 6.0:
            draw_text(350, 420, f"INTERSECTION AHEAD IN {int_dist_in_km:.2f} KM", font=GLUT_BITMAP_HELVETICA_18, c=(1, 0.8, 0))

        if traffic_signal['color'] == 0 and not traffic_signal['passed']:
            dist_in_km = (480 - traffic_signal['y']) * 0.0003
            if 0 < dist_in_km <= 3.6:
                draw_text(320, 470, f"! ALERT: UPCOMING RED LIGHT IN {dist_in_km:.2f} KM !", font=GLUT_BITMAP_HELVETICA_18, c=(1, 0, 0))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_intersection():
    global traffic_signal
    if traffic_signal is None: return
    sig_y = traffic_signal['y'] - 600 
    cx, cz = get_curve_offset(sig_y)
    
    c_rd = get_color(0.1, 0.1, 0.1, 0, sig_y)
    glColor3f(c_rd[0], c_rd[1], c_rd[2])
    glPushMatrix()
    glTranslatef(0 + cx, sig_y, -1.8 + cz)
    glScalef(5000, 700, 1)
    glutSolidCube(1.0)
    glPopMatrix()
    
    for lx in [-200, -100, 0, 100, 200]:
        c_zb = get_color(0.8, 0.8, 0.8, lx, sig_y)
        glColor3f(c_zb[0], c_zb[1], c_zb[2])
        glPushMatrix()
        glTranslatef(lx + cx, traffic_signal['y'] - 200, -1.0 + cz)
        glScalef(40, 100, 1)
        glutSolidCube(1.0)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(lx + cx, traffic_signal['y'] - 1000, -1.0 + cz)
        glScalef(40, 100, 1)
        glutSolidCube(1.0)
        glPopMatrix()
        
    for ly in [sig_y - 200, sig_y - 100, sig_y, sig_y + 100, sig_y + 200]:
        c_zb = get_color(0.8, 0.8, 0.8, 0, ly)
        glColor3f(c_zb[0], c_zb[1], c_zb[2])
        glPushMatrix()
        glTranslatef(-350 + cx, ly, -1.0 + cz)
        glScalef(100, 40, 1)
        glutSolidCube(1.0)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(350 + cx, ly, -1.0 + cz)
        glScalef(100, 40, 1)
        glutSolidCube(1.0)
        glPopMatrix()

def draw_signal():
    global traffic_signal
    if traffic_signal is None: return
    y = traffic_signal['y']
    c_state = traffic_signal['color']
    cx, cz = get_curve_offset(y)
    
    # Left Pillar
    c = get_color(0.2, 0.2, 0.2, -300, y)
    glColor3f(c[0], c[1], c[2])
    glPushMatrix()
    glTranslatef(-300 + cx, y, 125 + cz)
    glScalef(15, 15, 250)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Right Pillar
    glPushMatrix()
    glTranslatef(300 + cx, y, 125 + cz)
    glScalef(15, 15, 250)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Top Beam
    c_top = get_color(0.15, 0.15, 0.15, 0, y)
    glColor3f(c_top[0], c_top[1], c_top[2])
    glPushMatrix()
    glTranslatef(0 + cx, y, 240 + cz)
    glScalef(600, 15, 15)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Signal Boxes and Lights (placed right over the 3 lanes)
    for lx in [-150, 0, 150]:
        c_box = get_color(0.05, 0.05, 0.05, lx, y)
        glColor3f(c_box[0], c_box[1], c_box[2])
        glPushMatrix()
        glTranslatef(lx + cx, y, 200 + cz)
        glScalef(35, 15, 80)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Red
        if c_state == 0: r,g,b = 1.0, 0.0, 0.0
        else: r,g,b = 0.1, 0.0, 0.0
        glColor3f(r, g, b)
        glMaterialfv(GL_FRONT, GL_EMISSION, [r, g, b, 1.0])
        glPushMatrix()
        glTranslatef(lx + cx, y+8, 225 + cz)
        glutSolidSphere(12, 12, 12)
        glPopMatrix()
        
        # Yellow
        if c_state == 1: r,g,b = 1.0, 1.0, 0.0
        else: r,g,b = 0.1, 0.1, 0.0
        glColor3f(r, g, b)
        glMaterialfv(GL_FRONT, GL_EMISSION, [r, g, b, 1.0])
        glPushMatrix()
        glTranslatef(lx + cx, y+8, 200 + cz)
        glutSolidSphere(12, 12, 12)
        glPopMatrix()
        
        # Green
        if c_state == 2: r,g,b = 0.0, 1.0, 0.0
        else: r,g,b = 0.0, 0.1, 0.0
        glColor3f(r, g, b)
        glMaterialfv(GL_FRONT, GL_EMISSION, [r, g, b, 1.0])
        glPushMatrix()
        glTranslatef(lx + cx, y+8, 175 + cz)
        glutSolidSphere(12, 12, 12)
        glPopMatrix()
        
        glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])

def draw_player_bike():
    if view_mode == 0: return
    glPushMatrix()
    glTranslatef(0, 480, 0)
    glRotatef(bank_angle, 0, 1, 0)
    angle = turn_progress * 90.0 if turn_state == 1 else turn_progress * -90.0
    glTranslatef(bike_pos_x, 0, 0)
    glRotatef(angle, 0, 0, 1)
    glTranslatef(-bike_pos_x, 0, 0)
    c = get_color(0.9, 0.1, 0.1, bike_pos_x, 480)
    glColor3f(c[0], c[1], c[2])
    glPushMatrix()
    glTranslatef(bike_pos_x, 0, 50)
    glScalef(30, 110, 50)
    glutSolidCube(1.0)
    glPopMatrix()
    
    if game_over:
        c_rider = get_color(0.2, 0.2, 0.8, player_fly_x, 480 + player_fly_y)
        glColor3f(c_rider[0], c_rider[1], c_rider[2])
        glPushMatrix()
        glTranslatef(player_fly_x, player_fly_y, player_fly_z)
        glRotatef(player_fly_angle, 1, 0, 0)
        glRotatef(player_fly_angle, 0, 1, 0)
        glScalef(30, 40, 50)
        glutSolidCube(1.0)
        glPopMatrix()
    else:
        c_rider = get_color(0.2, 0.2, 0.8, bike_pos_x, 480)
        glColor3f(c_rider[0], c_rider[1], c_rider[2])
        glPushMatrix()
        glTranslatef(bike_pos_x, 0, 90)
        glScalef(30, 40, 50)
        glutSolidCube(1.0)
        glPopMatrix()

    glColor3f(0.2, 0.2, 0.2)
    glPushMatrix()
    glTranslatef(bike_pos_x, -60, 30)
    glScalef(1.0, 1.0, 1.0)
    draw_connected_wheel()
    glPopMatrix()
    glPushMatrix()
    glTranslatef(bike_pos_x, 60, 30)
    glScalef(1.0, 1.0, 1.0)
    draw_connected_wheel()
    glPopMatrix()
    glPopMatrix()

def draw_red_screen():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glClear(GL_DEPTH_BUFFER_BIT)
    glColor3f(1.0, 0.0, 0.0)
    for y in range(0, 800, 4): draw_mpl_line(0, y, 1000, y)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def showScreen():
    s_val, cycle_val = get_sin_cos((frames % 3600) * 0.1)
    day_factor = (cycle_val + 1.0) / 2.0
    sky_r = 0.4 * day_factor
    sky_g = 0.6 * day_factor
    sky_b = 0.2 + 0.7 * day_factor

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    # Draw sky background using 2D projection
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glColor3f(sky_r, sky_g, sky_b)
    glTranslatef(500, 400, 0)
    glScalef(1000, 800, 1)
    glutSolidCube(1.0)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glClear(GL_DEPTH_BUFFER_BIT)

    setupCamera()
    draw_road()
    draw_intersection()
    draw_environment()
    draw_signal()
    draw_traffic()
    draw_player_bike()
    draw_dashboard()

    if game_over: draw_red_screen()
    glutSwapBuffers()

# -------------- EXACT ORIGINAL LOGIC ----------------

def keyboardListener(key, x, y):
    global speed, score, traffic_list, game_over, headlight_on, road_offset, frames, view_mode, paused, cruise_control, cruise_speed, level, traffic_signal, next_signal_score, turn_state, turn_progress, curve_x, curve_z, target_curve_x, target_curve_z, bank_angle, offroad_timer, distance, curve_distance_timer, player_fly_x, player_fly_y, player_fly_z, player_fly_angle, camera_angle, accident_x, bike_pos_x, env_list

    if key == b' ':
        paused = not paused
        return

    if game_over:
        if key in (b'r', b'R'):
            speed = 0.0
            score = 0.0
            distance = 0.0
            curve_distance_timer = 0.0
            bike_pos_x = 0
            traffic_list = []
            env_list = []
            headlight_on = True
            game_over = False
            road_offset = 0.0
            frames = 0
            level = 1
            cruise_control = False
            traffic_signal = None
            next_signal_score = 1500.0
            turn_state = 0
            turn_progress = 0.0
            curve_x = 0.0
            curve_z = 0.0
            target_curve_x = 0.0
            target_curve_z = 0.0
            bank_angle = 0.0
            offroad_timer = 900
            player_fly_x = 0.0
            player_fly_y = 0.0
            player_fly_z = 0.0
            player_fly_angle = 0.0
            camera_angle = 0.0
            accident_x = 0.0
            view_mode = 0
        return

    if paused:
        return

    if key in (b'w', b'W'): 
        cruise_control = False
        speed += 1.5
        if speed > 300.0: speed = 300.0
    elif key in (b's', b'S'): 
        cruise_control = False
        speed -= 4.0
        if speed < -50.0: speed = -50.0
    elif key in (b'a', b'A'): 
        if traffic_signal is not None and 480 < traffic_signal['y'] < 1200:
            turn_state = 1
            turn_progress = 0.0
        else:
            bike_pos_x += 25
            if bike_pos_x > 3000: bike_pos_x = 3000
    elif key in (b'd', b'D'): 
        if traffic_signal is not None and 480 < traffic_signal['y'] < 1200:
            turn_state = -1
            turn_progress = 0.0
        else:
            bike_pos_x -= 25
            if bike_pos_x < -3000: bike_pos_x = -3000
    elif key in (b'f', b'F'): 
        cruise_control = False
        if speed > 0:
            speed -= 10.0
            if speed < 0: speed = 0.0
            if bank_angle > 0: bike_pos_x += 10.0
            elif bank_angle < 0: bike_pos_x -= 10.0
        elif speed < 0:
            speed += 10.0
            if speed > 0: speed = 0.0
    elif key in (b'l', b'L'): headlight_on = not headlight_on
    elif key in (b'v', b'V'): view_mode = 1 - view_mode
    elif key in (b'c', b'C'): 
        cruise_control = not cruise_control
        if cruise_control:
            cruise_speed = speed

def specialKeyListener(key, x, y):
    global speed, cruise_control, bike_pos_x, turn_state, turn_progress
    if not game_over:
        if key == GLUT_KEY_UP: 
            cruise_control = False
            speed += 1.5
            if speed > 300.0: speed = 300.0
        elif key == GLUT_KEY_DOWN: 
            cruise_control = False
            if speed > 0:
                speed -= 1.0
                if speed < 0: speed = 0.0
            elif speed < 0:
                speed += 1.0
                if speed > 0: speed = 0.0
        elif key == GLUT_KEY_LEFT: 
            if traffic_signal is not None and 480 < traffic_signal['y'] < 1200:
                turn_state = 1
                turn_progress = 0.0
            else:
                bike_pos_x += 25
                if bike_pos_x > 3000: bike_pos_x = 3000
        elif key == GLUT_KEY_RIGHT: 
            if traffic_signal is not None and 480 < traffic_signal['y'] < 1200:
                turn_state = -1
                turn_progress = 0.0
            else:
                bike_pos_x -= 25
                if bike_pos_x < -3000: bike_pos_x = -3000

def idle():
    global speed, bike_pos_x, road_offset, rpm, score, game_over, traffic_list, env_list, frames, paused, cruise_control, cruise_speed, level, traffic_signal, next_signal_score, turn_state, turn_progress, curve_x, curve_z, target_curve_x, target_curve_z, bank_angle, offroad_timer, camera_angle, player_fly_x, player_fly_y, player_fly_z, player_fly_angle, distance, curve_distance_timer

    if paused:
        glutPostRedisplay()
        return

    if turn_state != 0:
        turn_progress += max(0.015, speed * 0.0004)
        if turn_progress >= 1.0:
            turn_state = 0
            turn_progress = 0.0
            traffic_list = []
            env_list = []
            traffic_signal = None
            next_signal_score = score + 1500 + get_rand() * 3500
            bike_pos_x = 0
            speed *= 0.8
        glutPostRedisplay()
        return

    if not game_over:
        frames += 1
        level = int(distance / 10.0) + 1
        hardness = distance / 10.0
        if hardness > 20.0: hardness = 20.0

        if speed > 0.0:
            curve_distance_timer += speed
            if curve_distance_timer > 20000.0:
                curve_distance_timer = 0.0
                target_curve_x = (get_rand() - 0.5) * 350.0
                target_curve_z = (get_rand() - 0.5) * 200.0
                if get_rand() > 0.6:
                    target_curve_x = 0.0
                    target_curve_z = 0.0

            step_x = speed * 0.002
            step_z = speed * 0.0013
            
            if curve_x < target_curve_x:
                curve_x += step_x
                if curve_x > target_curve_x: curve_x = target_curve_x
            elif curve_x > target_curve_x:
                curve_x -= step_x
                if curve_x < target_curve_x: curve_x = target_curve_x
                
            if curve_z < target_curve_z:
                curve_z += step_z
                if curve_z > target_curve_z: curve_z = target_curve_z
            elif curve_z > target_curve_z:
                curve_z -= step_z
                if curve_z < target_curve_z: curve_z = target_curve_z
                
            max_bank = 45.0 * (hardness / 20.0) 
            ideal_bank = (curve_x / 175.0) * max_bank
            if ideal_bank > 45.0: ideal_bank = 45.0
            if ideal_bank < -45.0: ideal_bank = -45.0
            
            step_bank = speed * 0.0013
            if bank_angle < ideal_bank:
                bank_angle += step_bank
                if bank_angle > ideal_bank: bank_angle = ideal_bank
            elif bank_angle > ideal_bank:
                bank_angle -= step_bank
                if bank_angle < ideal_bank: bank_angle = ideal_bank

            drift = curve_x * (speed / 180.0) * 0.06
            bike_pos_x -= drift

        road_offset += speed
        score += max(0.0, speed) * 0.05
        distance += speed * 0.0003
        if distance < 0:
            distance = 0.0

        if cruise_control:
            if speed < cruise_speed: speed += 0.25
            elif speed > cruise_speed: speed -= 0.25
            if abs(speed - cruise_speed) < 0.3: speed = cruise_speed

        if abs(bike_pos_x) > 280:
            if speed > 150: speed -= 0.5
            offroad_timer -= 1
            if offroad_timer <= 0:
                accident_x = bike_pos_x
                trigger_game_over()
        else:
            offroad_timer = 900

        score += speed * 0.05

        if traffic_signal is None and score > next_signal_score:
            col = int(get_rand() * 3)
            timer = 0
            if col == 0:
                timer = 180 + int(get_rand() * 300)
            elif col == 1:
                timer = 120
            traffic_signal = {'y': -16000, 'color': col, 'timer': timer, 'passed': False}
            
        if traffic_signal is not None:
            traffic_signal['y'] += speed
            
            if traffic_signal['color'] == 0:
                traffic_signal['timer'] -= 1
                if traffic_signal['timer'] <= 0:
                    traffic_signal['color'] = 1
                    traffic_signal['timer'] = 120
            elif traffic_signal['color'] == 1:
                traffic_signal['timer'] -= 1
                if traffic_signal['timer'] <= 0:
                    traffic_signal['color'] = 2
                    
            if not traffic_signal['passed'] and traffic_signal['y'] > 480:
                traffic_signal['passed'] = True
                if traffic_signal['color'] == 0:
                    score = 0.0

            if traffic_signal is not None and traffic_signal['y'] > 1200:
                traffic_signal = None
                next_signal_score = score + 1500 + get_rand() * 3500

        gear = int(speed / 50.0) + 1
        if gear > 6: gear = 6
        speed_in_gear = speed - (gear - 1) * 50.0
        rpm = 1000 + (speed_in_gear / 50.0) * 8000.0
        if rpm > 9500: rpm = 9500 + get_rand() * 500

        spawn_chance = 0.005 + (hardness * 0.003)
        max_cars_on_screen = 1 + int(hardness * 0.4)

        if get_rand() < spawn_chance:
            lane_x = rand_choice([-150, 0, 150])
            valid = len(traffic_list) < max_cars_on_screen
            new_y = -8000
            min_gap = 2500 - hardness * 80
            if min_gap < 600: min_gap = 600

            adjacent_cars = 0
            for t in traffic_list:
                dist = abs(t[1] - new_y)
                if dist < min_gap and t[0] == lane_x:
                    valid = False
                    break
                if dist < 800:
                    adjacent_cars += 1
            
            if adjacent_cars >= 2:
                valid = False

            if valid:
                opp_chance = hardness * 0.02
                dir_val = -1 if get_rand() < opp_chance else 1
                v_type = int(get_rand() * 4)
                if v_type > 3: v_type = 3
                traffic_list.append([lane_x, new_y, dir_val, False, v_type])

        new_list = []
        for t in traffic_list:
            if len(t) == 4: t.append(0)
            v_type = t[4]

            if t[2] == 1:
                t[1] += speed - (40.0 + hardness * 2.0)
            else:
                t[1] += speed + (60.0 + hardness * 5.0)

            v_len = 380 if v_type == 1 else (450 if v_type == 2 else (110 if v_type == 3 else 240))
            col_x = 65 if v_type == 1 else (60 if v_type == 2 else (30 if v_type == 3 else 55))

            half_len = v_len / 2.0
            bumper = t[1] + half_len
            rear = t[1] - half_len
            
            if rear <= 510 and bumper >= 450:
                dist_x = abs(t[0] - bike_pos_x)
                if dist_x < col_x:
                    trigger_game_over()
                elif dist_x < (col_x + 35) and not t[3]:
                    score += 500
                    t[3] = True

            if t[1] < 1200:
                new_list.append(t)
        traffic_list = new_list

        new_env = []
        for e in env_list:
            e[1] += speed
            
            if 430 < e[1] < 530:
                prop_x = e[0]
                if e[2] == 0:
                    col_width = 20 * e[3]
                else:
                    col_width = e[3] / 2.0
                if abs(prop_x - bike_pos_x) < (col_width + 30):
                    accident_x = prop_x
                    trigger_game_over()
                    
            if e[1] < 1200:
                new_env.append(e)
        env_list = new_env

        if frames % 10 == 0:
            new_y = -12000
            side = rand_choice([-1, 1])
            x_pos = side * int(650 + get_rand() * 800)
            env_t = 0 if get_rand() < 0.5 else 1
            if env_t == 1:
                w = 150 + get_rand() * 200
                d = 150 + get_rand() * 300
                h = 300 + get_rand() * 800
                col = get_rand() * 0.4
                env_list.append([x_pos, new_y, env_t, w, d, h, col])
            else:
                s = 1.0 + get_rand() * 2.0
                env_list.append([x_pos, new_y, env_t, s])

    if game_over:
        if camera_angle > -120.0:
            camera_angle -= 0.5
            
        if player_fly_z > 10.0:
            player_fly_y += 8.0
            player_fly_x -= 4.0
            player_fly_z -= 3.0
            player_fly_angle += 15.0
        elif player_fly_z < 10.0:
            player_fly_z = 10.0

    glutPostRedisplay()

def init():
    global quadric
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glShadeModel(GL_SMOOTH)
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.1, 0.1, 0.1, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.6, 0.6, 0.7, 1.0])
    glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 1.0, 0.0, 0.0])
    
    # Enable Smooth Anti-Aliasing
    glEnable(GL_MULTISAMPLE)
    glEnable(GL_LINE_SMOOTH)
    glEnable(GL_POLYGON_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST)
    
    quadric = gluNewQuadric()

if __name__ == "__main__":
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH | GLUT_MULTISAMPLE)
    glutInitWindowSize(1000, 800)
    glutCreateWindow(b"Road Rush Bike - Night Highway")

    init()

    glutDisplayFunc(showScreen)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)

    glutMainLoop()