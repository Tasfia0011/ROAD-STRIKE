from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random, math, time


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
time_of_day = 0.0  
game_state = "PLAYING"
day_shifting_light = 1.0


rsm_bttn = (0, 0, 0, 0)
qit_bttn = (0, 0, 0, 0)


carz_x, carz_z = 0.0, 0.0     
camra_x, camra_z = 0.0, 15.0  
cam_angle = 0.0     
camera_mode = "3rd"          
current_rpm = 900.0          
steering_ngle = 0.0   

  
RAIN_COUNT = 1000 
raindrops = []
is_raining = False
last_rain_toggle = time.time() 

 
carz_health = 5
plr_hlth = 5.0
score = 0
killed_enemies = 0
star_wanted = 0
activated_police= False
police_pos_x, police_pos_y, police_pos_z = 0.0, 0.0, 0.0
police_head = 0.0
consecutive_bosts = 0
plyr_bltts = []
bosts = []
puddles = []
health_bosts = []
last_hlth_spawner_z = 0.0
uncontrolled_period = 0.0
passed_red_light_factor = {(0, 0)}
zone_speed_limit = False
car_exploision = False
wanted_busted = False
last_boost_z = 0.0


target_carz_heading = 0.0  
carz_heading = 0.0
last_turn_time = 0.0
total_distance_travelled = 0.0


carz_speed = 0.0
max_speed = 300.0         
max_reverse_speed = -60.0 
acceleration = 5.0       
deceleration = 15.0       
steering_speed = 3.0     


INTERSECTION_INTERVAL = 3  
ROAD_DRAW_RADIUS = 2       


MAX_ENEMIES = 2
enemies = []
bullets = []


ENEMY_COLORS = {
    1: (0.1, 0.8, 0.2),  
    2: (0.1, 0.3, 0.9),  
    3: (0.9, 0.1, 0.1)   
}


key_sign = {'w': False, 's': False, 'a': False, 'd': False, 'up': False, 'down': False, 'left': False, 'right': False, 'space': False}
drift_angle = 0.0
gun_angle = 0.0
last_frame_time = time.time()


cheat_mode = False
cheat_speed = 90.0
CHEAT_BULLET_COOLDOWN = 0.18
CHEAT_VISION_DISTANCE = 150.0
CHEAT_VISION_ANGLE = 45.0

last_cheat_shot = 0.0


ROAD_WIDTH = 20.0
FOOTPATH_WIDTH = 4.0
CELL_SIZE = 150               
BLOCK_MARGIN = ROAD_WIDTH / 2.0 + FOOTPATH_WIDTH  

VIEW_RADIUS = 1                 
PRUNE_MARGIN = VIEW_RADIUS + 2    

block_cache = {}
street_lamp_radius=[]

BUILDING_COLORS = [
    (0.70, 0.70, 0.75),
    (0.80, 0.60, 0.50),
    (0.60, 0.65, 0.80),
    (0.55, 0.55, 0.60),
    (0.75, 0.70, 0.60),
    (0.65, 0.70, 0.65),
    (0.85, 0.75, 0.55),
    (0.50, 0.55, 0.60),]


def camera_block(cx, cz):
    return int(math.floor(cx / CELL_SIZE)), int(math.floor(cz / CELL_SIZE))


def set_env_color(r, g, b):
    glColor3f(r * day_shifting_light, g * day_shifting_light, b * day_shifting_light)


def generate_block(bi, bj):
    global INTERSECTION_INTERVAL, BLOCK_MARGIN


    seed = (bi * 73856093) ^ (bj * 19349663) ^ 0x9E3779B9
    rnd = random.Random(seed)


    bx0 = bi * CELL_SIZE + BLOCK_MARGIN
    bx1 = (bi + 1) * CELL_SIZE - BLOCK_MARGIN
    bz0 = bj * CELL_SIZE + BLOCK_MARGIN
    bz1 = (bj + 1) * CELL_SIZE - BLOCK_MARGIN


    area_w = bx1 - bx0
    area_d = bz1 - bz0


    trees = []
    buildings = []
    hospitals = []
    schools = []
    lamps=[]
    street_lamps=[]
    traffic_lights = []
    road_signs=[]
    garage=[]


    fz0 = bj * CELL_SIZE + ROAD_WIDTH / 2.0 + FOOTPATH_WIDTH / 2.0
    fx0 = bi * CELL_SIZE + ROAD_WIDTH / 2.0 + FOOTPATH_WIDTH / 2.0
    fx1 = (bi + 1) * CELL_SIZE - ROAD_WIDTH / 2.0 - FOOTPATH_WIDTH / 2.0
    fz1 = (bj + 1) * CELL_SIZE - ROAD_WIDTH / 2.0 - FOOTPATH_WIDTH / 2.0


    borders_road = (bi % INTERSECTION_INTERVAL == 0) or (bj % INTERSECTION_INTERVAL == 0)
    landmark_roll = rnd.random() if borders_road else 1.0


    if landmark_roll < 0.05:
        x = (bx0 + bx1) / 2.0
        z = (bz0 + bz1) / 2.0
        hospitals.append((x, z, 22.0, 22.0, 18.0))


        road_signs.append((fx0, fz0+5, 0))
        road_signs.append((fx1, fz0+5, 0))
        road_signs.append((fx0 , fz1-5 , 0))
        road_signs.append((fx1, fz1-5, 0))


    elif landmark_roll < 0.1:
        x = (bx0 + bx1) / 2.0
        z = (bz0 + bz1) / 2.0
        schools.append((x, z, 28.0, 16.0, 10.0))


        road_signs.append((fx0, fz0 + 5, 0))
        road_signs.append((fx1, fz0 + 5, 0))
        road_signs.append((fx0, fz1 - 5, 0))
        road_signs.append((fx1, fz1 - 5, 0))


    elif landmark_roll < 0.13:
        x = (bx0 + bx1) / 2.0
        z = (bz0 + bz1) / 2.0
        garage.append((x, z, 28.0, 16.0, 10.0))


    else:
        cols = max(1, int(area_w / 16))
        rows = max(1, int(area_d / 16))
        cw = area_w / cols
        cd = area_d / rows


        for gx in range(cols):
            for gz in range(rows):
                cx0 = bx0 + gx * cw
                cz0 = bz0 + gz * cd
                x = cx0 + rnd.uniform(cw * 0.25, cw * 0.75)
                z = cz0 + rnd.uniform(cd * 0.25, cd * 0.75)
                r = rnd.random()


                if r < 0.22:
                    height = rnd.uniform(5.0, 8.5)
                    kind = 'pine' if rnd.random() < 0.4 else 'round'
                    trees.append((x, z, height, kind))
                elif r < 0.88:
                    w = rnd.uniform(6.0, 11.0)
                    d = rnd.uniform(6.0, 11.0)
                    h = rnd.uniform(10.0, 34.0)
                    color = rnd.choice(BUILDING_COLORS)
                    win_seed = rnd.uniform(0, 1000)
                    buildings.append((x, z, w, d, h, color, win_seed))


        temp=7 
        lamps = [(fx0, fz0+temp), (fx1, fz0+temp), (fx0, fz1-temp), (fx1, fz1-temp),
                 ((fx0 + fx1) / 2.0, fz0+temp), ((fx0 + fx1) / 2.0, fz1-temp)]
        LAMP_SPACING = 35.0
        inset = 10.0


        z_pos = fz0 + inset
        while z_pos <= fz1 - inset:
            street_lamps.append((fx0, z_pos, 90))
            street_lamps.append((fx1, z_pos, -90))
            z_pos += LAMP_SPACING


        x_pos = fx0 + inset
        while x_pos <= fx1 - inset:
            street_lamps.append((x_pos, fz0, 0))
            street_lamps.append((x_pos, fz1, 180))
            x_pos += LAMP_SPACING

            
        if bi % INTERSECTION_INTERVAL == 0 and bj % INTERSECTION_INTERVAL == 0:
            x = bi * CELL_SIZE
            z = bj * CELL_SIZE
            offset = ROAD_WIDTH / 2.0 + FOOTPATH_WIDTH / 2.0  

            traffic_lights = [
                (x - offset, z - offset, 90),  
                (x + offset, z - offset, 0),  
                (x + offset, z + offset, 270),  
                (x - offset, z + offset, 180)  
            ]

    return {
        "buildings": buildings,
        "hospitals": hospitals,
        "schools": schools,
        "trees": trees,
        "lamps": lamps,
        "street_lamps": street_lamps,
        "traffic_lights": traffic_lights,
        "road_signs": road_signs,
        "garage": garage
    }


def stream_world(cx, cz):
    ci, cj = camera_block(cx, cz)
    for bi in range(ci - VIEW_RADIUS, ci + VIEW_RADIUS + 1):
        for bj in range(cj - VIEW_RADIUS, cj + VIEW_RADIUS + 1):
            if (bi, bj) not in block_cache:
                block_cache[(bi, bj)] = generate_block(bi, bj)


    stale = [key for key in block_cache
             if abs(key[0] - ci) > PRUNE_MARGIN or abs(key[1] - cj) > PRUNE_MARGIN]
    for key in stale:
        del block_cache[key]


    return ci, cj


def update_time(value):
    global time_of_day, game_state


    if game_state == "PLAYING":
        time_of_day += 0.0005
        if time_of_day >= 1.0:
            time_of_day = 0.0


    glutPostRedisplay()
    glutTimerFunc(16, update_time, 0)


def draw_button(rect, label):
    x1, y1, x2, y2 = rect
    glColor3f(0.15, 0.15, 0.15)
    glBegin(GL_QUADS)
    glVertex2f(x1, y1); glVertex2f(x2, y1)
    glVertex2f(x2, y2); glVertex2f(x1, y2)
    glEnd()


    glColor3f(1, 1, 1)
    glLineWidth(2)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x1, y1)
    glVertex2f(x2, y1)
    glVertex2f(x2, y2)
    glVertex2f(x1, y2)
    glEnd()


    glRasterPos2f(x1 + 80, (y1 + y2) / 2 - 5)
    for ch in label:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))


def draw_pause_overlay():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT)


    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_FOG)


    glEnable(GL_BLEND)
    glColor4f(0, 0, 0, 0.6)
    glBegin(GL_QUADS)
    glVertex2f(0, 0); glVertex2f(SCREEN_WIDTH, 0)
    glVertex2f(SCREEN_WIDTH, SCREEN_HEIGHT); glVertex2f(0, SCREEN_HEIGHT)
    glEnd()


    glColor3f(1, 1, 1)
    glRasterPos2f(SCREEN_WIDTH / 2 -40, SCREEN_HEIGHT / 2 + 150)
    for ch in "PAUSED":
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))


    draw_button(rsm_bttn, "Resume")
    draw_button(qit_bttn, "Quit")


    glEnable(GL_DEPTH_TEST)
    glEnable(GL_FOG)


    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


play_again_bttn = (0, 0, 0, 0)
game_over_qit_bttn = (0, 0, 0, 0)


def layout_game_over_buttons():
    global play_again_bttn, game_over_qit_bttn
    cx = SCREEN_WIDTH // 2
    btn_w, btn_h = 220, 60
    gap = 30

    y1 = SCREEN_HEIGHT // 2 - btn_h // 2
    y2 = y1 + btn_h

    play_again_bttn    = (cx - gap // 2 - btn_w, y1, cx - gap // 2, y2)
    game_over_qit_bttn = (cx + gap // 2, y1, cx + gap // 2 + btn_w, y2)

def draw_game_over_overlay():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_FOG)

   
    glEnable(GL_BLEND)
    glColor4f(0, 0, 0, 0.7)
    glBegin(GL_QUADS)
    glVertex2f(0, 0); glVertex2f(SCREEN_WIDTH, 0)
    glVertex2f(SCREEN_WIDTH, SCREEN_HEIGHT); glVertex2f(0, SCREEN_HEIGHT)
    glEnd()

    
    glColor3f(1, 0.2, 0.2)  
    glRasterPos2f(SCREEN_WIDTH / 2 - 60, SCREEN_HEIGHT / 2 + 100)
    for ch in "GAME OVER":
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))

   
    draw_button(play_again_bttn, "Play Again")
    draw_button(game_over_qit_bttn, "Quit")

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_FOG)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)



def point_in_rect(px, py, rect):
    x1, y1, x2, y2 = rect
    min_x, max_x = min(x1, x2), max(x1, x2)
    min_y, max_y = min(y1, y2), max(y1, y2)
    return min_x <= px <= max_x and min_y <= py <= max_y
  


def draw_ground(cx, cz):
    size = CELL_SIZE * (ROAD_DRAW_RADIUS + 3)
    set_env_color(0.30, 0.55, 0.25)
    glBegin(GL_QUADS)
    glVertex3f(cx - size, 0, cz + size)
    glVertex3f(cx + size, 0, cz + size)
    glVertex3f(cx + size, 0, cz - size)
    glVertex3f(cx - size, 0, cz - size)
    glEnd()


def draw_footpaths(ci, cj):
    global INTERSECTION_INTERVAL
    half = ROAD_WIDTH / 2.0 + FOOTPATH_WIDTH
    lo = -(ROAD_DRAW_RADIUS + 2) * CELL_SIZE
    hi = (ROAD_DRAW_RADIUS + 2) * CELL_SIZE


    set_env_color(0.45, 0.45, 0.45)


    for i in range(ci - ROAD_DRAW_RADIUS - 1, ci + ROAD_DRAW_RADIUS + 2):
        if i % INTERSECTION_INTERVAL == 0:
            x = i * CELL_SIZE
            glBegin(GL_QUADS)
            glVertex3f(x - half, 0.015, cj * CELL_SIZE + hi)
            glVertex3f(x + half, 0.015, cj * CELL_SIZE + hi)
            glVertex3f(x + half, 0.015, cj * CELL_SIZE + lo)
            glVertex3f(x - half, 0.015, cj * CELL_SIZE + lo)
            glEnd()
    for j in range(cj - ROAD_DRAW_RADIUS - 1, cj + ROAD_DRAW_RADIUS + 2):
        if j % INTERSECTION_INTERVAL == 0:
            z = j * CELL_SIZE
            glBegin(GL_QUADS)
            glVertex3f(ci * CELL_SIZE + lo, 0.016, z - half)
            glVertex3f(ci * CELL_SIZE + hi, 0.016, z - half)
            glVertex3f(ci * CELL_SIZE + hi, 0.016, z + half)
            glVertex3f(ci * CELL_SIZE + lo, 0.016, z + half)
            glEnd()


def draw_roads(ci, cj):
    half = ROAD_WIDTH / 2.0
    lo = -(ROAD_DRAW_RADIUS + 1) * CELL_SIZE
    hi = (ROAD_DRAW_RADIUS + 1) * CELL_SIZE


    glDisable(GL_FOG)
    set_env_color(0.01, 0.01, 0.01)


    for i in range(ci - ROAD_DRAW_RADIUS, ci + ROAD_DRAW_RADIUS + 1):
        if i % INTERSECTION_INTERVAL == 0:
            x = i * CELL_SIZE
            glBegin(GL_QUADS)
            glVertex3f(x - half, 0.02, cj * CELL_SIZE + hi)
            glVertex3f(x + half, 0.02, cj * CELL_SIZE + hi)
            glVertex3f(x + half, 0.02, cj * CELL_SIZE + lo)
            glVertex3f(x - half, 0.02, cj * CELL_SIZE + lo)
            glEnd()
    for j in range(cj - ROAD_DRAW_RADIUS, cj + ROAD_DRAW_RADIUS + 1):
        if j % INTERSECTION_INTERVAL == 0:
            z = j * CELL_SIZE
            glBegin(GL_QUADS)
            glVertex3f(ci * CELL_SIZE + lo, 0.021, z - half)
            glVertex3f(ci * CELL_SIZE + hi, 0.021, z - half)
            glVertex3f(ci * CELL_SIZE + hi, 0.021, z + half)
            glVertex3f(ci * CELL_SIZE + lo, 0.021, z + half)
            glEnd()


    draw_lane_markings(ci, cj)
    draw_intersections(ci, cj)


    glEnable(GL_FOG)


def draw_lane_markings(ci, cj):
    dash_len, gap_len = 4.0, 4.0
    step = dash_len + gap_len
    lo = -(ROAD_DRAW_RADIUS + 1) * CELL_SIZE
    hi = (ROAD_DRAW_RADIUS + 1) * CELL_SIZE


    glColor3f(1.0, 1.0, 1.0)
    for i in range(ci - ROAD_DRAW_RADIUS, ci + ROAD_DRAW_RADIUS + 1):
        if i % INTERSECTION_INTERVAL == 0:
            x = i * CELL_SIZE
            z = math.floor((cj * CELL_SIZE + hi) / step) * step
            z_end = cj * CELL_SIZE + lo
            while z > z_end:
                glBegin(GL_QUADS)
                glVertex3f(x - 0.15, 0.025, z)
                glVertex3f(x + 0.15, 0.025, z)
                glVertex3f(x + 0.15, 0.025, z - dash_len)
                glVertex3f(x - 0.15, 0.025, z - dash_len)
                glEnd()
                z -= step


    for j in range(cj - ROAD_DRAW_RADIUS, cj + ROAD_DRAW_RADIUS + 1):
        if j % INTERSECTION_INTERVAL == 0:
            z = j * CELL_SIZE
            x = math.floor((ci * CELL_SIZE + hi) / step) * step
            x_end = ci * CELL_SIZE + lo
            while x > x_end:
                glBegin(GL_QUADS)
                glVertex3f(x, 0.026, z - 0.15)
                glVertex3f(x - dash_len, 0.026, z - 0.15)
                glVertex3f(x - dash_len, 0.026, z + 0.15)
                glVertex3f(x, 0.026, z + 0.15)
                glEnd()
                x -= step


    glColor3f(0.95, 0.85, 0.2)
    half = ROAD_WIDTH / 2.0 - 0.15
    for i in range(ci - ROAD_DRAW_RADIUS, ci + ROAD_DRAW_RADIUS + 1):
        if i % INTERSECTION_INTERVAL == 0:
            x = i * CELL_SIZE
            for side in (-1, 1):
                ex = x + side * half
                glBegin(GL_QUADS)
                glVertex3f(ex - 0.1, 0.022, cj * CELL_SIZE + hi)
                glVertex3f(ex + 0.1, 0.022, cj * CELL_SIZE + hi)
                glVertex3f(ex + 0.1, 0.022, cj * CELL_SIZE + lo)
                glVertex3f(ex - 0.1, 0.022, cj * CELL_SIZE + lo)
                glEnd()


def draw_box(cx, base_y, cz, w, h, d, color):
    x0, x1 = cx - w / 2, cx + w / 2
    y0, y1 = base_y, base_y + h
    z0, z1 = cz - d / 2, cz + d / 2


    faces = [
        ((0, 0, 1), [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]),  
        ((0, 0, -1), [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)]),  
        ((-1, 0, 0), [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)]),  
        ((1, 0, 0), [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)]),  
        ((0, 1, 0), [(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)]),  
        ((0, -1, 0), [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)]),  
    ]
    set_env_color(*color)


    glBegin(GL_QUADS)
    for normal, verts in faces:
        glNormal3fv(normal)
        for v in verts:
            glVertex3fv(v)
    glEnd()


def draw_3d_text(x, y, z, text, color=(0, 0, 0), scale=0.01, angle=0):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(angle, 0, 1, 0)
    glColor3f(*color)
    glScalef(scale, scale, scale)


    for ch in text:
        glutStrokeCharacter(GLUT_STROKE_ROMAN, ord(ch))
    glPopMatrix()


def draw_slow_sign(cx, cz, angle=0):
    pole = (0.2, 0.2, 0.2)
    red = (0.9, 0.05, 0.05)
    white = (1.0, 1.0, 1.0)
    black = (0.05, 0.05, 0.05)


    glPushMatrix()
    glTranslatef(cx, 0, cz)
    glRotatef(angle, 0, 1, 0)


    draw_box(0, 0, 0, 0.8, 4, 0.2, pole)
    draw_box(0, 5.6, 0, 2.5, 0.5, 0.2, red)
    draw_box(0, 3.2, 0, 4.5, 2.8, 0.2, red)
    draw_box(0, 3.2, -0.12, 3.8, 2.4, 0.03, white)
    draw_box(0, 3.2, 0.12, 3.8, 2.4, 0.03, white)


    draw_3d_text(1.7, 4.9, -0.25, "Max Speed", color=black, scale=0.005, angle=180)
    draw_3d_text(0.7, 3.5, -0.25, "90", color=black, scale=0.012, angle=180)


    glPushMatrix()
    glRotatef(180, 0, 1, 0)
    draw_3d_text(1.7, 4.9, -0.25, "Max Speed", color=black, scale=0.005, angle=180)
    draw_3d_text(0.7, 3.5, -0.25, "90", color=black, scale=0.012, angle=180)
    glPopMatrix()


    glPopMatrix()


def draw_hospital(cx, cz):
    white = (0.9, 0.9, 0.9)
    red = (0.8, 0.05, 0.05)


    glPushMatrix()
    glTranslatef(cx, 0, cz)
    glScalef(1.4, 1.4, 1.4)
    glTranslatef(-cx, 0, -cz)


    draw_box(cx, 0, cz, 24, 10, 16, white)
    draw_box(cx, 10, cz, 14, 7, 12, white)


    draw_box(cx, 13.5, cz + 6.05, 5, 1.0, 0.1, red)
    draw_box(cx, 11.5, cz + 6.05, 1.2, 5, 0.1, red)
    draw_box(cx, 13.5, cz - 6.05, 5, 1.0, 0.1, red)
    draw_box(cx, 11.5, cz - 6.05, 1.2, 5, 0.1, red)
    draw_box(cx + 7.05, 13.5, cz, 0.1, 1.0, 5, red)
    draw_box(cx + 7.05, 11.5, cz, 0.1, 5, 1.2, red)
    draw_box(cx - 7.05, 13.5, cz, 0.1, 1.0, 5, red)
    draw_box(cx - 7.05, 11.5, cz, 0.1, 5, 1.2, red)


    draw_3d_text(cx, 5, cz + 8.1, "HOSPITAL", red, 0.012, 0)
    draw_3d_text(cx, 5, cz - 8.1, "HOSPITAL", red, 0.012, 180)
    draw_3d_text(cx + 12.1, 5, cz, "HOSPITAL", red, 0.012, 90)
    draw_3d_text(cx - 12.1, 5, cz, "HOSPITAL", red, 0.012, 270)
    glPopMatrix()


    draw_tree(cx - 50, cz - 5, 6, "round")
    draw_tree(cx + 50, cz - 5, 6, "round")
    draw_tree(cx - 50, cz + 5, 5, "round")


def draw_school(cx, cz):
    brick = (0.65, 0.3, 0.2)
    white = (0.9, 0.85, 0.7)
    blue = (0.3, 0.65, 0.85)


    glPushMatrix()
    glTranslatef(cx, 0, cz)
    glScalef(2.5, 2.5, 2.5)
    glTranslatef(-cx, 0, -cz)


    draw_box(cx, 0, cz, 30, 8, 14, brick)
    draw_box(cx, 8, cz, 31, 0.6, 15, white)
    draw_box(cx, 3.5, cz + 7.1, 24, 3, 0.1, blue)
    draw_box(cx, 0, cz + 7.2, 4, 4, 0.2, white)


    draw_3d_text(cx, 4, cz + 7.1, "SCHOOL", white, 0.012, 0)
    draw_3d_text(cx, 4, cz - 7.1, "SCHOOL", white, 0.012, 180)
    draw_3d_text(cx + 15.1, 4, cz, "SCHOOL", white, 0.012, 90)
    draw_3d_text(cx - 15.1, 4, cz, "SCHOOL", white, 0.012, 270)
    glPopMatrix()


    draw_tree(cx - 50, cz - 4, 6, "round")
    draw_tree(cx + 50, cz - 4, 6, "round")
    draw_tree(cx - 50, cz + 4, 5, "round")
    draw_tree(cx + 50, cz + 4, 5, "round")


def draw_garage(cx, cz):
    gray = (0.35, 0.35, 0.35)
    dark_gray = (0.15, 0.15, 0.15)
    white = (0.9, 0.9, 0.9)
    yellow = (0.9, 0.7, 0.05)


    glPushMatrix()
    glTranslatef(cx, 0, cz)
    glScalef(2.0, 2.0, 2.0)
    glTranslatef(-cx, 0, -cz)


    draw_box(cx, 0, cz, 24, 10, 18, gray)
    draw_box(cx, 10, cz, 26, 1, 20, dark_gray)
    draw_box(cx, 5, cz + 9.1, 16, 8, 0.2, dark_gray)


    for y in [2, 4, 6, 8]:
        draw_box(cx, y, cz + 9.25, 15.5, 0.15, 0.1, white)


    draw_3d_text(cx - 4, 6.5, cz + 9.2,"GARAGE", yellow, 0.016, 0)
    draw_3d_text(cx + 4, 6.5, cz - 9.2,"GARAGE", yellow, 0.016, 180)
    draw_3d_text(cx + 12.1, 6.5, cz + 4,"GARAGE", yellow, 0.016, 90)
    draw_3d_text(cx - 12.1, 6.5, cz - 4,"GARAGE", yellow, 0.016, 270)
    glPopMatrix()


    draw_tree(cx - 50, cz - 4, 6, "round")
    draw_tree(cx + 50, cz - 4, 6, "round")
    draw_tree(cx - 50, cz + 4, 5, "round")
    draw_tree(cx + 50, cz + 4, 5, "round")


def draw_intersections(ci, cj):
    stripe_w, stripe_len, gap = 0.6, ROAD_WIDTH - 2.0, 0.6
    inset = ROAD_WIDTH / 2.0 + 0.6


    glColor3f(0.95, 0.95, 0.9)
    for i in range(ci - ROAD_DRAW_RADIUS, ci + ROAD_DRAW_RADIUS + 1):
        if i % INTERSECTION_INTERVAL != 0:
            continue
        for j in range(cj - ROAD_DRAW_RADIUS, cj + ROAD_DRAW_RADIUS + 1):
            if j % INTERSECTION_INTERVAL != 0:
                continue
            x, z = i * CELL_SIZE, j * CELL_SIZE
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                cx = x + dx * inset
                cz = z + dz * inset
                for s in range(-3, 4):
                    if dx != 0:
                        gx, gz = cx, z + s * (stripe_w + gap)
                        glBegin(GL_QUADS)
                        glVertex3f(gx - 0.6, 0.03, gz - stripe_w / 2)
                        glVertex3f(gx + 0.6, 0.03, gz - stripe_w / 2)
                        glVertex3f(gx + 0.6, 0.03, gz + stripe_w / 2)
                        glVertex3f(gx - 0.6, 0.03, gz + stripe_w / 2)
                        glEnd()
                    else:
                        gx, gz = x + s * (stripe_w + gap), cz
                        glBegin(GL_QUADS)
                        glVertex3f(gx - stripe_w / 2, 0.03, gz - 0.6)
                        glVertex3f(gx + stripe_w / 2, 0.03, gz - 0.6)
                        glVertex3f(gx + stripe_w / 2, 0.03, gz + 0.6)
                        glVertex3f(gx - stripe_w / 2, 0.03, gz + 0.6)
                        glEnd()


def get_traffic_states():
    if cheat_mode:
        return "green"
    TRAFFIC_GREEN_TIME = 6
    TRAFFIC_YELLOW_TIME = 3
    TRAFFIC_RED_TIME = 10
    t=time.time()
    cycle=TRAFFIC_GREEN_TIME+TRAFFIC_YELLOW_TIME+TRAFFIC_RED_TIME
    t=t%cycle


    if t<TRAFFIC_GREEN_TIME:
        return "green"
    elif t<TRAFFIC_GREEN_TIME+TRAFFIC_YELLOW_TIME:
        return "yellow"
    else:
        return "red"


def draw_tree(x, z, height, kind):
    glPushMatrix()
    glTranslatef(x, 0, z)


    set_env_color(0.45, 0.28, 0.13)
    quad = gluNewQuadric()
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quad, 0.5, 0.4, height * 0.5, 8, 1)
    glPopMatrix()


    if kind == 'pine':
        set_env_color(0.08, 0.4, 0.18)
        for i, scale in enumerate((1.0, 0.7, 0.42)):
            glPushMatrix()
            glTranslatef(0, height * 0.5 + i * height * 0.28, 0)
            glRotatef(-90, 1, 0, 0)
            gluCylinder(quad, height * 0.32 * scale, 0.0, height * 0.4, 10, 1)
            glPopMatrix()
    else:
        set_env_color(0.1, 0.5, 0.15)
        glPushMatrix()
        glTranslatef(0, height * 0.5, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quad, height * 0.35, 0.0, height * 1.0, 10, 1)
        glPopMatrix()


    glPopMatrix()


def _hash01(a, b, seed):
    v = math.sin(a * 12.9898 + b * 78.233 + seed * 37.719) * 43758.5453
    return v - math.floor(v)


def draw_SCREENs(hw, hd, h, seed):
    win_w, win_h = 0.9, 1.3
    margin = 1.2
    spacing_x, spacing_y = 1.9, 2.5


    rows = max(1, int((h - 2 * margin) / spacing_y))
    cols = max(1, int((2 * hw - 2 * margin) / spacing_x))


    glBegin(GL_QUADS)
    for row in range(rows):
        cy = margin + row * spacing_y + spacing_y / 2
        for col in range(cols):
            cx = -hw + margin + col * spacing_x + spacing_x / 2
            lit = _hash01(row, col, seed) > 0.55
            glColor3f(1.0, 0.92, 0.55) if lit else glColor3f(0.25, 0.35, 0.45)
            for zc in (hd + 0.03, -hd - 0.03):
                glVertex3f(cx - win_w / 2, cy - win_h / 2, zc)
                glVertex3f(cx + win_w / 2, cy - win_h / 2, zc)
                glVertex3f(cx + win_w / 2, cy + win_h / 2, zc)
                glVertex3f(cx - win_w / 2, cy + win_h / 2, zc)
    glEnd()


def draw_building(x, z, w, d, h, color, win_seed):
    glPushMatrix()
    glTranslatef(x, 0, z)


    draw_box(0, 0, 0, w, h, d, color)


    roof_color = tuple(min(1.0, c * 0.75) for c in color)
    set_env_color(*roof_color)


    glBegin(GL_QUADS)
    glVertex3f(-w/2, h, -d/2)
    glVertex3f(w/2, h, -d/2)
    glVertex3f(w/2, h, d/2)
    glVertex3f(-w/2, h, d/2)
    glEnd()


    draw_SCREENs(w/2, d/2, h, win_seed)


    glPopMatrix()


def draw_lamp(x, z):
    glPushMatrix()
    glTranslatef(x, 0, z)
    quad = gluNewQuadric()


    glColor3f(0.2, 0.2, 0.2)
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quad, 0.15, 0.12, 4.0, 6, 1)
    glPopMatrix()


    glTranslatef(0, 4.0, 0)
    glColor3f(1.0, 0.95, 0.6)
    glutSolidSphere(0.25, 8, 8)
    glPopMatrix()


def draw_lamp_glow(radius=10.0):
    global day_shifting_light
    night_factor = max(0.0, 1.0 - (day_shifting_light - 0.2) / 0.8)
    if night_factor <= 0.01:
        return


    glDepthMask(GL_FALSE)
    glBegin(GL_TRIANGLE_FAN)


    glColor4f(1.0, 0.85, 0.3, 0.45 * night_factor)
    glVertex3f(0.0, 0.03, 0.0)


    glColor4f(1.0, 0.8, 0.2, 0.0)
    segments = 16
    for i in range(segments + 1):
        angle = (2.0 * math.pi * i) / segments
        gx = math.cos(angle) * radius
        gz = math.sin(angle) * radius
        glVertex3f(gx, 0.03, gz)


    glEnd()
    glDepthMask(GL_TRUE)


def draw_Street_lamp(x, z, angle):
    glPushMatrix()
    glTranslatef(x, 0, z)
    glRotatef(angle, 0, 1, 0)
    glScalef(1.5, 1.5, 1.5)
    quad = gluNewQuadric()

    glColor3f(0.25, 0.25, 0.28)
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quad, 0.22, 0.16, 8.0, 10, 1)
    glPopMatrix()


    glPushMatrix()
    glTranslatef(0, 8.0, 0)
    glRotatef(180, 0, 1, 0)
    gluCylinder(quad, 0.15, 0.10, 3.0, 10, 1)
    glPopMatrix()


    glPushMatrix()
    glRotatef(90, 0, 1, 0)
    glTranslatef(3.0, 8.0, 0)


    glColor3f(0.15, 0.15, 0.17)
    glPushMatrix()
    glScalef(1.4, 0.25, 0.7)
    glutSolidCube(1)
    glPopMatrix()


    glColor3f(1.0, 0.9, 0.6)
    glBegin(GL_QUADS)
    glVertex3f(-0.6, -0.13, -0.3)
    glVertex3f(0.6, -0.13, -0.3)
    glVertex3f(0.6, -0.13, 0.3)
    glVertex3f(-0.6, -0.13, 0.3)
    glEnd()


    glPopMatrix()
    gluDeleteQuadric(quad)


    glPushMatrix()
    glTranslatef(0, 0, -4.0)
    draw_lamp_glow(radius=8.0)
    glPopMatrix()


    glPopMatrix()


def draw_traffic_light(x, z, rotation, state):
    glPushMatrix()
    glTranslatef(x, 0, z)
    glRotatef(rotation, 0, 1, 0)
    glScalef(2.5, 1.5, 2.5)


    glColor3f(0.15, 0.15, 0.15)
    glBegin(GL_QUADS)
    glVertex3f(-0.12, 0, -0.12)
    glVertex3f(0.12, 0, -0.12)
    glVertex3f(0.12, 5, -0.12)
    glVertex3f(-0.12, 5, -0.12)
    glVertex3f(-0.12, 0, 0.12)
    glVertex3f(0.12, 0, 0.12)
    glVertex3f(0.12, 5, 0.12)
    glVertex3f(-0.12, 5, 0.12)
    glEnd()


    glColor3f(0.03, 0.03, 0.03)
    glPushMatrix()
    glTranslatef(0, 5, 0)
    glScalef(0.8, 2.0, 0.5)
    glutSolidCube(1)
    glPopMatrix()


    if state == "red":
        glColor3f(1, 0, 0)
    else:
        glColor3f(0.15, 0, 0)
    glPushMatrix()
    glTranslatef(0, 5.45, -0.26)
    glutSolidSphere(0.18, 12, 12)
    glPopMatrix()


    if state == "yellow":
        glColor3f(1, 1, 0)
    else:
        glColor3f(0.15, 0.15, 0)
    glPushMatrix()
    glTranslatef(0, 5, -0.26)
    glutSolidSphere(0.18, 12, 12)
    glPopMatrix()


    if state == "green":
        glColor3f(0, 1, 0)
    else:
        glColor3f(0, 0.15, 0)
    glPushMatrix()
    glTranslatef(0, 4.55, -0.26)
    glutSolidSphere(0.18, 12, 12)
    glPopMatrix()


    glPopMatrix()


def draw_cuboid_enemy(enemy):
    x, y, z = enemy['x'], enemy['y'], enemy['z']
    level = enemy['level']
    shirt_color = ENEMY_COLORS.get(level, (0.5, 0.5, 0.5))


    skin_color = (0.9, 0.7, 0.5)
    pants_color = (0.15, 0.15, 0.2)


    glPushMatrix()
    glTranslatef(x, y, z)


    draw_box(-0.35, 0.0, 0.0, 0.4, 1.2, 0.4, pants_color)
    draw_box( 0.35, 0.0, 0.0, 0.4, 1.2, 0.4, pants_color)


    draw_box(0.0, 1.2, 0.0, 1.2, 1.4, 0.6, shirt_color)


    draw_box(-0.8, 1.2, 0.0, 0.3, 1.2, 0.3, skin_color)
    draw_box( 0.8, 1.2, 0.0, 0.3, 1.2, 0.3, skin_color)


    draw_box(0.0, 2.6, 0.0, 0.7, 0.7, 0.7, skin_color)


    text_str = f"LVL {level}"
    draw_3d_text(0.6, 3.8, 0.0, text_str, color=(1.0, 1.0, 1.0), scale=0.007, angle=0)
    draw_3d_text(-0.6, 3.8, 0.0, text_str, color=(1.0, 1.0, 1.0), scale=0.007, angle=180)


    glPopMatrix()


def take_carz_damage(amount=1):
    global carz_health, plr_hlth, car_exploision, game_state
    carz_health = max(0, carz_health - amount)
    plr_hlth = max(0.0, plr_hlth - amount * 0.5)
    if carz_health <= 0 or plr_hlth <= 0:
        car_exploision = True
        game_state = "GAME_OVER"


def is_in_school_or_hospital_zone(cx, cz):
    ci, cj = camera_block(cx, cz)
    for bi in range(ci - 1, ci + 2):
        for bj in range(cj - 1, cj + 2):
            block = block_cache.get((bi, bj))
            if block:
                for (hx, hz, w, d, h) in block.get("hospitals", []):
                    if math.hypot(cx - hx, cz - hz) < 55.0:
                        return True
                for (sx, sz, w, d, h) in block.get("schools", []):
                    if math.hypot(cx - sx, cz - sz) < 55.0:
                        return True
    return False


def is_near_obstacle(x, z):
    ci, cj = camera_block(x, z)
    block = block_cache.get((ci, cj))
    if not block:
        return False
    for (lx, lz, angle) in block.get("street_lamps", []):
        if math.hypot(x - lx, z - lz) < 4.0:
            return True
    for (bx, bz, w, d, h, color, win_seed) in block.get("buildings", []):
        if abs(x - bx) < w/2.0 + 2.0 and abs(z - bz) < d/2.0 + 2.0:
            return True
    return False


def update_and_draw_enemies(dt):
    global enemies, bullets, score, killed_enemies, carz_z, carz_x, total_distance_travelled
    current_t = time.time()
    dist_km = total_distance_travelled / 10.0

    allowed_levels = []
    if dist_km >= 150.0:
        allowed_levels = [1, 2, 3]
    elif dist_km >= 100.0:
        allowed_levels = [3]
    elif dist_km >= 75.0:
        allowed_levels = [1, 2]
    elif dist_km >= 65.0:
        allowed_levels = [2]
    elif dist_km >= 35.0:
        allowed_levels = [1]

    target_max = 2 if allowed_levels else 0

    while len(enemies) < target_max and allowed_levels:
        spawn_lvl = random.choice(allowed_levels)

        rad_h = math.radians(carz_heading)

        forward_x = math.sin(rad_h)
        forward_z = -math.cos(rad_h)

        side_x = math.cos(rad_h)
        side_z = math.sin(rad_h)

        distance = random.uniform(60.0, 110.0)
        side_distance = random.uniform(ROAD_WIDTH / 2.0 + 2.0,
                                       ROAD_WIDTH / 2.0 + 10.0)

        spawn_x = carz_x + forward_x * distance + side_x * random.choice([-side_distance, side_distance])
        spawn_z = carz_z + forward_z * distance + side_z * random.choice([-side_distance, side_distance])

        if is_in_school_or_hospital_zone(spawn_x, spawn_z) or is_near_obstacle(spawn_x, spawn_z):
            break

        overlap = False
        for existing in enemies:
            if math.hypot(spawn_x - existing['x'], spawn_z - existing['z']) < 6.0:
                overlap = True
                break
        if overlap:
            break

        enemies.append({
            'x': spawn_x,
            'y': 0.0,
            'z': spawn_z,
            'level': spawn_lvl,
            'last_shot': current_t,
            'shot_once': False
        })

    for enemy in enemies[:]:
        lvl = enemy['level']
        cooldown = 2.0 if lvl == 1 else (1.5 if lvl == 2 else 0.8)
        bullet_speed = 35.0 if lvl == 1 else (45.0 if lvl == 2 else 60.0)

        if lvl == 1:
            if not enemy['shot_once']:
                dx = carz_x - enemy['x']
                dz = carz_z - enemy['z']
                dist = math.hypot(dx, dz)
                if dist > 0.01:
                    bullets.append({'x': enemy['x'], 'y': 1.5, 'z': enemy['z'], 'vx': (dx/dist)*bullet_speed, 'vz': (dz/dist)*bullet_speed})
                enemy['shot_once'] = True
            enemy['z'] += 5.0 * dt
        elif lvl == 2:
            dx = carz_x - enemy['x']
            dz = carz_z - enemy['z']
            dist = math.hypot(dx, dz)
            if dist > 30.0:
                enemy['z'] += 6.0 * dt
            if dist < 80.0 and (current_t - enemy['last_shot'] >= cooldown):
                if dist > 0.01:
                    bullets.append({'x': enemy['x'], 'y': 1.5, 'z': enemy['z'], 'vx': (dx/dist)*bullet_speed, 'vz': (dz/dist)*bullet_speed})
                enemy['last_shot'] = current_t
        elif lvl == 3:
            dx = carz_x - enemy['x']
            dz = carz_z - enemy['z']
            dist = math.hypot(dx, dz)
            if dist > 0.01:
                dir_x = dx / dist
                dir_z = dz / dist
                enemy['x'] += dir_x * 12.0 * dt
                enemy['z'] += dir_z * 12.0 * dt
                if current_t - enemy['last_shot'] >= cooldown:
                    bullets.append({'x': enemy['x'], 'y': 1.5, 'z': enemy['z'], 'vx': dir_x * bullet_speed, 'vz': dir_z * bullet_speed})
                    enemy['last_shot'] = current_t

        if math.hypot(carz_x - enemy['x'], carz_z - enemy['z']) < 3.0:
            kill_pts = 10 if lvl == 1 else (15 if lvl == 2 else 25)
            score += kill_pts
            killed_enemies += 1
            enemies.remove(enemy)
            take_carz_damage(1)
            continue

        if enemy['z'] > carz_z + 20.0:
            enemies.remove(enemy)
            continue

        draw_cuboid_enemy(enemy)


def update_and_draw_bullets(dt):
    global bullets, plyr_bltts, enemies, score, killed_enemies
    glColor3f(1.0, 0.8, 0.1)
    quad = gluNewQuadric()

    
    for b in bullets[:]:
        b['x'] += b['vx'] * dt
        b['z'] += b['vz'] * dt

        if math.hypot(b['x'] - carz_x, b['z'] - carz_z) < 2.5:
            take_carz_damage(1)
            bullets.remove(b)
            continue

        if math.hypot(b['x'] - carz_x, b['z'] - carz_z) > 120.0:
            bullets.remove(b)
            continue

        glPushMatrix()
        glTranslatef(b['x'], b['y'], b['z'])
        gluSphere(quad, 0.35, 8, 8)
        glPopMatrix()

    
    glColor3f(0.2, 0.9, 1.0)
    for pb in plyr_bltts[:]:
        pb['x'] += pb.get('vx', 0.0) * dt
        pb['z'] += pb.get('vz', -120.0) * dt

        hit_enemy = False
        for enemy in enemies[:]:
            if math.hypot(pb['x'] - enemy['x'], pb['z'] - enemy['z']) < 3.0:
                lvl = enemy['level']
                score += 10 if lvl == 1 else (15 if lvl == 2 else 25)
                killed_enemies += 1
                enemies.remove(enemy)
                hit_enemy = True
                break

        if hit_enemy:
            plyr_bltts.remove(pb)
            continue

        if math.hypot(pb['x'] - carz_x, pb['z'] - carz_z) > 120.0:
            plyr_bltts.remove(pb)
            continue

        glPushMatrix()
        glTranslatef(pb['x'], pb['y'], pb['z'])
        gluSphere(quad, 0.35, 8, 8)
        glPopMatrix()

    gluDeleteQuadric(quad)


def update_rain(dt):
    global is_raining, last_rain_toggle


    if time.time() - last_rain_toggle >= random.uniform(30,50):
        is_raining = not is_raining
        last_rain_toggle = time.time()


    if not is_raining:
        return


    for drop in raindrops:
        drop[1] -= drop[3] * dt


        if drop[1] < 0:
            drop[1] = random.uniform(40, 50)
            drop[0] = camra_x + random.uniform(-80, 80)
            drop[2] = camra_z + random.uniform(-80, 80)


        if abs(drop[0] - camra_x) > 80:
            drop[0] = camra_x + random.uniform(-80, 80)
        if abs(drop[2] - camra_z) > 80:
            drop[2] = camra_z + random.uniform(-80, 80)



def draw_rain():
    if not is_raining:
        return


    glDepthMask(GL_FALSE)
    glLineWidth(1.2)


    glColor4f(0.7, 0.8, 0.95, 0.4)


    glBegin(GL_LINES)
    for x, y, z, speed, length in raindrops:
        glVertex3f(x, y, z)
        glVertex3f(x - 0.1, y - length, z - 0.1)
    glEnd()


    glDepthMask(GL_TRUE)


def draw_world(ci, cj):
    for bi in range(ci - VIEW_RADIUS, ci + VIEW_RADIUS + 1):
        for bj in range(cj - VIEW_RADIUS, cj + VIEW_RADIUS + 1):
            block = block_cache.get((bi, bj))
            if not block:
                continue
            for (x, z, w, d, h) in block.get("hospitals", []):
                draw_hospital(x, z)
            for (x, z, w, d, h) in block.get("schools", []):
                draw_school(x, z)
            for (x, z, height, kind) in block["trees"]:
                draw_tree(x, z, height, kind)
            for (x, z, w, d, h, color, win_seed) in block["buildings"]:
                draw_building(x, z, w, d, h, color, win_seed)
            for (x, z) in block["lamps"]:
                draw_lamp(x, z)
            for (x, z, angle) in block["street_lamps"]:
                rad = math.radians(angle)
                light_x = x + math.sin(rad) * 4.5
                light_z = z - math.cos(rad) * 4.5
                street_lamp_radius.append((light_x, light_z))
                draw_Street_lamp(x, z, angle)
            for (x, z, rotation) in block["traffic_lights"]:
                draw_traffic_light(x, z, rotation, get_traffic_states())
            for (x, z, angle) in block["road_signs"]:
                draw_slow_sign(x, z, angle)
            for (x, z, w, d, h) in block.get("garage", []):
                draw_garage(x, z)


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(t):
    return t * t * (3 - 2 * t)


def update_sky():
    global time_of_day, day_shifting_light
    colors = [
        (0.60, 0.85, 0.9),  
        (0.89, 0.59, 0.35), 
        (0.01, 0.02, 0.06), 
        (0.3, 0.32, 0.5)    
    ]
    ambient_levels = [1.0, 0.55, 0.20, 0.55]
    segment = int(time_of_day * 4) % 4
    t = (time_of_day * 4) % 1.0


    t_eased = smoothstep(t)


    c1 = colors[segment]
    c2 = colors[(segment + 1) % 4]


    r = lerp(c1[0], c2[0], t_eased)
    g = lerp(c1[1], c2[1], t_eased)
    b = lerp(c1[2], c2[2], t_eased)


    a1 = ambient_levels[segment]
    a2 = ambient_levels[(segment + 1) % 4]
    day_shifting_light = lerp(a1, a2, t_eased)


    glClearColor(r, g, b, 1.0)
    glFogfv(GL_FOG_COLOR, (r, g, b, 1.0))


def reset_game():
    global carz_health, plr_hlth, car_exploision, wanted_busted, score, killed_enemies, star_wanted, police_active
    global carz_x, carz_z, carz_speed, carz_heading, target_carz_heading, drift_angle, total_distance_travelled, last_boost_z, last_hlth_spawner_z
    global enemies, bullets, plyr_bltts, bosts, puddles, health_bosts

    carz_health = 5
    plr_hlth = 5.0
    car_exploision = False
    wanted_busted = False
    score = 0
    killed_enemies = 0
    star_wanted = 0
    activated_police= False

    carz_x, carz_z = 0.0, 0.0
    carz_speed = 0.0
    carz_heading = 0.0
    target_carz_heading = 0.0
    drift_angle = 0.0
    total_distance_travelled = 0.0
    last_boost_z = 0.0
    last_hlth_spawner_z = 0.0

    enemies.clear()
    bullets.clear()
    plyr_bltts.clear()
    bosts.clear()
    puddles.clear()
    health_bosts.clear()

def get_aim_world_dir(x, y):
    """Convert a SCREEN-space click/cursor position into a world-space aim
    direction on the ground (XZ) plane, using the camera matrices from the
    most recently rendered frame. This is what lets bullets travel to
    wherever the player actually clicked on screen."""
    viewport = glGetIntegerv(GL_VIEWPORT)
    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)

    win_y = viewport[3] - y  

    near_pt = gluUnProject(x, win_y, 0.0, modelview, projection, viewport)
    far_pt = gluUnProject(x, win_y, 1.0, modelview, projection, viewport)

    dir_x = far_pt[0] - near_pt[0]
    dir_z = far_pt[2] - near_pt[2]
    dist = math.hypot(dir_x, dir_z)
    if dist < 1e-6:
        rad_h = math.radians(carz_heading)
        return math.sin(rad_h), -math.cos(rad_h)  
    return dir_x / dist, dir_z / dist


def mouse_motion(x, y):
    global gun_angle
    if game_state == "PLAYING":
        dir_x, dir_z = get_aim_world_dir(x, y)
        world_aim_deg = math.degrees(math.atan2(dir_x, -dir_z))
        rel_angle = (world_aim_deg - carz_heading + 180.0) % 360.0 - 180.0
        gun_angle = max(-80.0, min(80.0, rel_angle))



def mouse(button, state, x, y):
    global game_state, plyr_bltts, star_wanted, police_active, gun_angle
    if game_state == "GAME_OVER":
        if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            gl_y = SCREEN_HEIGHT - y
            if point_in_rect(x, gl_y, play_again_bttn):
                reset_game()  
                game_state = "PLAYING"
                return

            if point_in_rect(x, gl_y, game_over_qit_bttn):
                glutLeaveMainLoop()
                return
        return


    if game_state == "PAUSED":
        if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            gl_y = SCREEN_HEIGHT - y
            if point_in_rect(x, gl_y, rsm_bttn):
                game_state = "PLAYING"
            elif point_in_rect(x, gl_y, qit_bttn):
                glutLeaveMainLoop()
        return

    if game_state == "PLAYING" and button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        dir_x, dir_z = get_aim_world_dir(x, y)

        plyr_bltts.append({
            'x': carz_x + dir_x * 3.5,
            'y': 1.6,
            'z': carz_z + dir_z * 3.5,
            'vx': dir_x * 140.0,
            'vz': dir_z * 140.0
        })
        if is_in_school_or_hospital_zone(carz_x, carz_z):
            star_wanted = min(3, star_wanted + 1)
            activated_police= True



def draw_hud_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=1.0, b=1.0):
    glColor3f(r, g, b)
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))


def draw_hud_circle(cx, cy, radius, num_segments=36, fill=False, r=1.0, g=1.0, b=1.0, alpha=1.0):
    glColor4f(r, g, b, alpha)
    if fill:
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(cx, cy)
    else:
        glBegin(GL_LINE_LOOP)
    for i in range(num_segments + 1):
        ang = (2.0 * math.pi * i) / num_segments
        glVertex2f(cx + math.cos(ang) * radius, cy + math.sin(ang) * radius)
    glEnd()


def update_health_bosts():
    global health_bosts, last_hlth_spawner_z, carz_health
    if carz_health < 5:
        if abs(carz_z - last_hlth_spawner_z) >= random.uniform(50.0, 80.0) or len(health_bosts) < 1:
            rad_h = math.radians(carz_heading)
            forward_x = math.sin(rad_h)
            forward_z = -math.cos(rad_h)
            side_x = math.cos(rad_h)
            side_z = math.sin(rad_h)
            offset_side = random.choice([-5.0, 0.0, 5.0])
            spawn_x = carz_x + forward_x * random.uniform(50.0, 90.0) + side_x * offset_side
            spawn_z = carz_z + forward_z * random.uniform(50.0, 90.0) + side_z * offset_side
            health_bosts.append({'x': spawn_x, 'z': spawn_z, 'active': True})
            last_hlth_spawner_z = carz_z

    for hp in health_bosts[:]:
        dist = math.hypot(carz_x - hp['x'], carz_z - hp['z'])
        if dist > 120.0:
            health_bosts.remove(hp)
            continue
        if hp.get('active', True) and dist < 3.2:
            hp['active'] = False
            carz_health = min(5, carz_health + 1)
            health_bosts.remove(hp)


def draw_health_bosts():
    for hp in health_bosts:
        if not hp.get('active', True):
            continue
        glPushMatrix()
        glTranslatef(hp['x'], 0.7, hp['z'])
        glRotatef((time.time() * 150.0) % 360, 0, 1, 0)
        draw_box(0, 0, 0, 1.4, 1.4, 1.4, (0.0, 1.0, 0.2))
        glPopMatrix()


def update_bosts():
    global bosts, last_boost_z, carz_speed, star_wanted, police_active, consecutive_bosts
    if abs(carz_z - last_boost_z) >= random.uniform(50.0, 80.0):
        boost_x = random.choice([-5.0, 0.0, 5.0])
        bosts.append({'x': boost_x, 'z': carz_z - 120.0, 'active': True})
        last_boost_z = carz_z

    for b in bosts[:]:
        if b['z'] > carz_z + 20.0:
            bosts.remove(b)
            continue
        if b['active'] and math.hypot(carz_x - b['x'], carz_z - b['z']) < 3.0:
            b['active'] = False
            carz_speed = min(max_speed, carz_speed + 80.0)
            if star_wanted > 0:
                consecutive_bosts += 1
                if consecutive_bosts >= 2:
                    star_wanted = 0
                    activated_police= False
                    consecutive_bosts = 0
            bosts.remove(b)


def draw_bosts():
    for b in bosts:
        if not b.get('active', True):
            continue
        glPushMatrix()
        glTranslatef(b['x'], 0.6, b['z'])
        glRotatef((time.time() * 120.0) % 360, 0, 1, 0)
        draw_box(0, 0, 0, 1.2, 1.2, 1.2, (1.0, 0.85, 0.1))
        glPopMatrix()




def draw_puddles():
    if not is_raining:
        return
    glDisable(GL_FOG)
    glEnable(GL_BLEND)
    glColor4f(0.15, 0.35, 0.55, 0.65)
    for p in puddles:
        glBegin(GL_QUADS)
        glVertex3f(p['x'] - p['w']/2, 0.028, p['z'] + p['d']/2)
        glVertex3f(p['x'] + p['w']/2, 0.028, p['z'] + p['d']/2)
        glVertex3f(p['x'] + p['w']/2, 0.028, p['z'] - p['d']/2)
        glVertex3f(p['x'] - p['w']/2, 0.028, p['z'] - p['d']/2)
        glEnd()
    glEnable(GL_FOG)


def update_puddles():
    global puddles, uncontrolled_period
    if not is_raining:
        puddles.clear()
        return

    if len(puddles) < 3 and random.random() < 0.02:
        side_x = random.choice([-7.0, 7.0])
        rad_h = math.radians(carz_heading)

        forward_x = math.sin(rad_h)
        forward_z = -math.cos(rad_h)

        distance = random.uniform(50.0, 100.0)
        puddles.append({
            'x': carz_x + forward_x * distance,
            'z': carz_z + forward_z * distance,
            'w': 4.5,
            'd': 8.0
        })

    for p in puddles[:]:
        if p['z'] > carz_z + 20.0:
            puddles.remove(p)
            continue
        if abs(carz_x - p['x']) < p['w']/2.0 + 1.2 and abs(carz_z - p['z']) < p['d']/2.0 + 2.0:
            uncontrolled_period = 4.5


def update_police(dt):
    global police_pos_x, police_pos_y, police_pos_z, police_head, police_active, star_wanted, wanted_busted, game_state, activated_police
    if star_wanted == 0:
        activated_police= False
        return

    rad_h = math.radians(carz_heading)
    fx, fz = math.sin(rad_h), -math.cos(rad_h)

    if star_wanted >= 3:
        wanted_busted = True
        game_state = "GAME_OVER"
        police_pos_x = carz_x + 8.0 * fx
        police_pos_z = carz_z + 8.0 * fz
        police_head = (carz_heading + 180.0) % 360.0
        activated_police= True
        return

    if activated_police and star_wanted > 0:
        target_x = carz_x - 12.0 * fx
        target_z = carz_z - 12.0 * fz
        police_pos_x = lerp(police_pos_x, target_x, 5.0 * dt)
        police_pos_z = lerp(police_pos_z, target_z, 5.0 * dt)
        police_head = carz_heading


def draw_3d_carz(cx, cz, angle):
    global car_exploision

    light_factor = get_carz_light_factor(light_radius=16.0)
    if day_shifting_light > 0.7:
        light_factor = 0.0

    mult = 1.0 + (light_factor * 7)

    def light_color(r, g, b):
        return (
            min(1.0, r * mult),
            min(1.0, g * mult * 0.95),
            min(1.0, b * mult * 0.7)
        )
    glPushMatrix()
    glTranslatef(cx, 0.2, cz)
    glRotatef(-angle, 0, 1, 0)

    if car_exploision:
        draw_box(0, 0.5, 0, 3.2, 0.9, 5.2, (0.1, 0.1, 0.1))
        quad = gluNewQuadric()
        glColor3f(1.0, 0.3, 0.0)
        glutSolidSphere(1.8, 10, 10)
        gluDeleteQuadric(quad)
        glPopMatrix()
        return




    draw_box(0, 0.5, 0, 3.0, 0.8, 5.0, light_color(0.5, 0.05, 0.08))

    
    draw_box(0, 1.65, -1.3, 2.2, 0.15, 0.15, light_color(0.1, 0.1, 0.15))
    draw_box(-1.1, 1.35, -0.3, 0.15, 0.75, 2.0, light_color(0.1, 0.1, 0.15))
    draw_box(1.1, 1.35, -0.3, 0.15, 0.75, 2.0, light_color(0.1, 0.1, 0.15))
    draw_box(0, 1.65, 1.0, 2.2, 0.15, 0.15, light_color(0.1, 0.1, 0.15))
    
    quad = gluNewQuadric()

   
    draw_box(-0.55, 1.05, 0.1, 0.7, 0.7, 0.5, light_color(0.2, 0.35, 0.8))

   
    glPushMatrix()
    glTranslatef(-0.55, 1.55, 0.1)
    glColor3f(*light_color(0.95, 0.75, 0.6))
    gluSphere(quad, 0.32, 10, 10)
    glPopMatrix()


    glPushMatrix()
    glTranslatef(-0.55, 1.72, 0.08)
    glColor3f(*light_color(0.12, 0.12, 0.15))
    gluSphere(quad, 0.30, 8, 8)
    glPopMatrix()


    draw_box(-0.55, 1.2, -0.35, 0.55, 0.15, 0.5, light_color(0.95, 0.75, 0.6))

    glPushMatrix()
    glTranslatef(-0.55, 1.25, -0.65)
    glColor3f(0.15, 0.15, 0.18)
    gluCylinder(quad, 0.3, 0.3, 0.1, 10, 1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0.0, 1.75, -0.4)
    glRotatef(-gun_angle, 0, 1, 0)
    glColor3f(*light_color(0.2, 0.2, 0.25))
    glutSolidCube(0.4)
    glPushMatrix()
    glTranslatef(0, 0, -0.6)
    glColor3f(0.08, 0.08, 0.12)
    gluCylinder(quad, 0.12, 0.1, 0.8, 10, 1)
    glPopMatrix()
    glPopMatrix()

    draw_box(-1.0, 0.6, -2.52, 0.4, 0.3, 0.1, (1.0, 0.9, 0.2))
    draw_box(1.0, 0.6, -2.52, 0.4, 0.3, 0.1, (1.0, 0.9, 0.2))
    draw_box(-1.0, 0.6, 2.52, 0.4, 0.3, 0.1, (1.0, 0.1, 0.1))
    draw_box(1.0, 0.6, 2.52, 0.4, 0.3, 0.1, (1.0, 0.1, 0.1))

    if abs(drift_angle) > 3.0:
        glDisable(GL_FOG)
        glEnable(GL_BLEND)
        glColor4f(0.15, 0.15, 0.15, 0.7)
        for rx, rz in [(-1.1, 1.2), (1.1, 1.2)]:
            glBegin(GL_QUADS)
            glVertex3f(rx - 0.3, 0.03, rz + 1.2)
            glVertex3f(rx + 0.3, 0.03, rz + 1.2)
            glVertex3f(rx + 0.3, 0.03, rz - 0.8)
            glVertex3f(rx - 0.3, 0.03, rz - 0.8)
            glEnd()
        glEnable(GL_FOG)


    for wx, wy, wz in [(-1.5, 0.4, -1.5), (1.5, 0.4, -1.5), (-1.5, 0.4, 1.5), (1.5, 0.4, 1.5)]:
        glPushMatrix()
        glTranslatef(wx, wy, wz)
        glRotatef(90 if wx > 0 else -90, 0, 1, 0)
        glColor3f(*light_color(0.15, 0.15, 0.15))
        gluCylinder(quad, 0.45, 0.45, 0.35, 10, 1)
        glPopMatrix()

    gluDeleteQuadric(quad)
    glPopMatrix()


def draw_police_carz(cx, cz, angle):
    glPushMatrix()
    glTranslatef(cx, 0.2, cz)
    glRotatef(-angle, 0, 1, 0)

    draw_box(0, 0.5, 0, 3.0, 0.8, 5.0, (0.08, 0.08, 0.08))
    draw_box(0, 0.52, 0, 3.05, 0.76, 2.2, (0.9, 0.9, 0.9))

    draw_box(0, 1.4, -0.3, 2.2, 0.8, 2.6, (0.08, 0.08, 0.08))
    draw_box(0, 1.4, -1.6, 2.0, 0.7, 0.1, (0.7, 0.85, 0.95))

    draw_box(-0.4, 1.95, -0.3, 0.5, 0.3, 0.5, (1.0, 0.0, 0.0))
    draw_box(0.4, 1.95, -0.3, 0.5, 0.3, 0.5, (0.0, 0.2, 1.0))

    draw_3d_text(1.55, 0.5, 0.8, "POLICE", color=(0.1, 0.1, 0.1), scale=0.006, angle=90)
    draw_3d_text(-1.55, 0.5, -0.8, "POLICE", color=(0.1, 0.1, 0.1), scale=0.006, angle=270)

    quad = gluNewQuadric()
    for wx, wy, wz in [(-1.5, 0.4, -1.5), (1.5, 0.4, -1.5), (-1.5, 0.4, 1.5), (1.5, 0.4, 1.5)]:
        glPushMatrix()
        glTranslatef(wx, wy, wz)
        glRotatef(90 if wx > 0 else -90, 0, 1, 0)
        glColor3f(0.15, 0.15, 0.15)
        gluCylinder(quad, 0.45, 0.45, 0.35, 10, 1)
        glPopMatrix()
    gluDeleteQuadric(quad)
    glPopMatrix()



def draw_dashboard():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT)


    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()


    glDisable(GL_DEPTH_TEST)
    glDisable(GL_FOG)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    dash_h = SCREEN_HEIGHT * 0.38
    glColor4f(0.02, 0.02, 0.02, 0.95)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(SCREEN_WIDTH, 0)
    glVertex2f(SCREEN_WIDTH, dash_h)
    glVertex2f(0, dash_h)
    glEnd()

    glColor3f(1.0, 1.0, 0.0)
    glLineWidth(2.0)
    glBegin(GL_LINE_STRIP)
    glVertex2f(0, dash_h * 0.7)
    glVertex2f(SCREEN_WIDTH * 0.15, dash_h)
    glVertex2f(SCREEN_WIDTH * 0.85, dash_h)
    glVertex2f(SCREEN_WIDTH, dash_h * 0.7)
    glEnd()

    cx_speed = SCREEN_WIDTH * 0.28
    cy_speed = SCREEN_HEIGHT * 0.20
    R_speed = min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.17

    cx_rpm = SCREEN_WIDTH * 0.72
    cy_rpm = SCREEN_HEIGHT * 0.20
    R_rpm = R_speed

    draw_hud_circle(cx_speed, cy_speed, R_speed, fill=True, r=0.0, g=0.0, b=0.0, alpha=1.0)
    draw_hud_circle(cx_speed, cy_speed, R_speed, fill=False, r=1.0, g=1.0, b=0.0, alpha=1.0)

    for i in range(16):
        val = i * 20
        ang_deg = 225.0 - i * 18.0
        ang_rad = math.radians(ang_deg)

        tx1 = cx_speed + math.cos(ang_rad) * (R_speed * 0.84)
        ty1 = cy_speed + math.sin(ang_rad) * (R_speed * 0.84)
        tx2 = cx_speed + math.cos(ang_rad) * (R_speed * 0.96)
        ty2 = cy_speed + math.sin(ang_rad) * (R_speed * 0.96)

        glColor3f(1.0, 1.0, 0.0)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glVertex2f(tx1, ty1)
        glVertex2f(tx2, ty2)
        glEnd()


        if i < 15:
            ang_mid = math.radians(225.0 - (i + 0.5) * 18.0)
            mx1 = cx_speed + math.cos(ang_mid) * (R_speed * 0.89)
            my1 = cy_speed + math.sin(ang_mid) * (R_speed * 0.89)
            mx2 = cx_speed + math.cos(ang_mid) * (R_speed * 0.96)
            my2 = cy_speed + math.sin(ang_mid) * (R_speed * 0.96)
            glColor3f(0.8, 0.8, 0.0)
            glLineWidth(1.0)
            glBegin(GL_LINES)
            glVertex2f(mx1, my1)
            glVertex2f(mx2, my2)
            glEnd()


        text_str = str(val)
        offset_x = 12 if val >= 100 else (8 if val >= 10 else 4)
        nx = cx_speed + math.cos(ang_rad) * (R_speed * 0.68) - offset_x
        ny = cy_speed + math.sin(ang_rad) * (R_speed * 0.68) - 6
        draw_hud_text(nx, ny, text_str, font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=1.0, b=0.0)


    sp_ratio = min(300.0, max(0.0, abs(carz_speed))) / 300.0
    needle_ang = math.radians(225.0 - sp_ratio * 270.0)
    nx_sp = cx_speed + math.cos(needle_ang) * (R_speed * 0.88)
    ny_sp = cy_speed + math.sin(needle_ang) * (R_speed * 0.88)


    glColor3f(1.0, 0.0, 0.0)
    glLineWidth(4.0)
    glBegin(GL_LINES)
    glVertex2f(cx_speed, cy_speed)
    glVertex2f(nx_sp, ny_sp)
    glEnd()

    draw_hud_circle(cx_speed, cy_speed, 8, fill=True, r=0.1, g=0.1, b=0.1)
    draw_hud_circle(cx_speed, cy_speed, 5, fill=True, r=1.0, g=0.0, b=0.0)

    draw_hud_text(cx_speed - 10, cy_speed - R_speed * 0.55, "(P)", font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=1.0, b=0.0)

    draw_hud_circle(cx_rpm, cy_rpm, R_rpm, fill=True, r=0.0, g=0.0, b=0.0, alpha=1.0)
    draw_hud_circle(cx_rpm, cy_rpm, R_rpm, fill=False, r=1.0, g=1.0, b=0.0, alpha=1.0)

    for i in range(9):
        ang_deg = 210.0 - i * 30.0
        ang_rad = math.radians(ang_deg)

        tx1 = cx_rpm + math.cos(ang_rad) * (R_rpm * 0.84)
        ty1 = cy_rpm + math.sin(ang_rad) * (R_rpm * 0.84)
        tx2 = cx_rpm + math.cos(ang_rad) * (R_rpm * 0.96)
        ty2 = cy_rpm + math.sin(ang_rad) * (R_rpm * 0.96)

        glColor3f(1.0, 0.2, 0.0) if i >= 6 else glColor3f(1.0, 1.0, 0.0)
        glLineWidth(2.5 if i >= 6 else 2.0)
        glBegin(GL_LINES)
        glVertex2f(tx1, ty1)
        glVertex2f(tx2, ty2)
        glEnd()

        if i < 8:
            ang_mid = math.radians(210.0 - (i + 0.5) * 30.0)
            mx1 = cx_rpm + math.cos(ang_mid) * (R_rpm * 0.89)
            my1 = cy_rpm + math.sin(ang_mid) * (R_rpm * 0.89)
            mx2 = cx_rpm + math.cos(ang_mid) * (R_rpm * 0.96)
            my2 = cy_rpm + math.sin(ang_mid) * (R_rpm * 0.96)
            glColor3f(0.8, 0.8, 0.0)
            glLineWidth(1.0)
            glBegin(GL_LINES)
            glVertex2f(mx1, my1)
            glVertex2f(mx2, my2)
            glEnd()

        nx = cx_rpm + math.cos(ang_rad) * (R_rpm * 0.68) - 5
        ny = cy_rpm + math.sin(ang_rad) * (R_rpm * 0.68) - 6
        draw_hud_text(nx, ny, str(i), font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=1.0, b=0.0)

    rpm_ratio = min(8000.0, max(0.0, current_rpm)) / 8000.0
    needle_ang_rpm = math.radians(210.0 - rpm_ratio * 240.0)
    nx_rpm = cx_rpm + math.cos(needle_ang_rpm) * (R_rpm * 0.88)
    ny_rpm = cy_rpm + math.sin(needle_ang_rpm) * (R_rpm * 0.88)

    glColor3f(1.0, 0.0, 0.0)
    glLineWidth(4.0)
    glBegin(GL_LINES)
    glVertex2f(cx_rpm, cy_rpm)
    glVertex2f(nx_rpm, ny_rpm)
    glEnd()

    draw_hud_circle(cx_rpm, cy_rpm, 8, fill=True, r=0.1, g=0.1, b=0.1)
    draw_hud_circle(cx_rpm, cy_rpm, 5, fill=True, r=1.0, g=0.0, b=0.0)

    draw_hud_text(cx_rpm - 8, cy_rpm - R_rpm * 0.55, "(!)", font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=1.0, b=0.0)

    cx_mid = SCREEN_WIDTH * 0.5
    cy_mid = cy_speed

    glColor4f(0.8, 0.8, 0.0, 0.8)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(cx_mid - 80, cy_mid - 40)
    glVertex2f(cx_mid + 80, cy_mid - 40)
    glVertex2f(cx_mid + 80, cy_mid + 70)
    glVertex2f(cx_mid - 80, cy_mid + 70)
    glEnd()

    left_turn = key_sign['a'] or key_sign['left']
    right_turn = key_sign['d'] or key_sign['right']

    r_l, g_l, b_l = (1.0, 1.0, 0.0) if left_turn else (0.3, 0.3, 0.0)
    r_r, g_r, b_r = (1.0, 1.0, 0.0) if right_turn else (0.3, 0.3, 0.0)

    draw_hud_text(cx_mid - 65, cy_mid + 45, "<--", font=GLUT_BITMAP_HELVETICA_18, r=r_l, g=g_l, b=b_l)
    draw_hud_text(cx_mid + 40, cy_mid + 45, "-->", font=GLUT_BITMAP_HELVETICA_18, r=r_r, g=g_r, b=b_r)

    speed_text = f"{int(abs(carz_speed))} KM/H"
    gear_text = "D" if carz_speed >= 0 else "R"
    odo_text = f"165376"

    draw_hud_text(cx_mid - 35, cy_mid + 20, speed_text, font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=1.0, b=0.0)
    draw_hud_text(cx_mid - 8, cy_mid - 5, gear_text, font=GLUT_BITMAP_TIMES_ROMAN_24, r=1.0, g=0.0, b=0.0)
    draw_hud_text(cx_mid - 30, cy_mid - 30, odo_text, font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=1.0, b=0.0)

    cx_fuel = cx_speed - R_speed * 1.35
    cy_fuel = cy_speed - R_speed * 0.15
    R_sub = R_speed * 0.45

    draw_hud_circle(cx_fuel, cy_fuel, R_sub, fill=True, r=0.0, g=0.0, b=0.0, alpha=1.0)
    draw_hud_circle(cx_fuel, cy_fuel, R_sub, fill=False, r=1.0, g=1.0, b=0.0, alpha=1.0)
    draw_hud_text(cx_fuel - 14, cy_fuel - R_sub * 0.6, "FUEL", font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=1.0, b=0.0)
    glColor3f(1.0, 0.0, 0.0)
    glLineWidth(2.5)
    glBegin(GL_LINES)
    glVertex2f(cx_fuel, cy_fuel)
    glVertex2f(cx_fuel - R_sub * 0.5, cy_fuel + R_sub * 0.6)
    glEnd()

    cx_wheel = SCREEN_WIDTH * 0.5
    cy_wheel = SCREEN_HEIGHT * 0.05
    R_wheel = SCREEN_HEIGHT * 0.12

    glPushMatrix()
    glTranslatef(cx_wheel, cy_wheel, 0)
    glRotatef(steering_ngle, 0, 0, 1)

    draw_hud_circle(0, 0, R_wheel, fill=False, r=0.2, g=0.2, b=0.2, alpha=1.0)
    draw_hud_circle(0, 0, R_wheel * 0.9, fill=False, r=0.4, g=0.4, b=0.4, alpha=1.0)

    glColor3f(0.5, 0.5, 0.5)
    glLineWidth(4.0)
    glBegin(GL_LINES)
    glVertex2f(0, 0); glVertex2f(-R_wheel * 0.9, 0)
    glVertex2f(0, 0); glVertex2f(R_wheel * 0.9, 0)
    glVertex2f(0, 0); glVertex2f(0, -R_wheel * 0.9)
    glEnd()


    draw_hud_circle(0, 0, R_wheel * 0.3, fill=True, r=0.1, g=0.1, b=0.1)
    draw_hud_circle(0, 0, R_wheel * 0.3, fill=False, r=1.0, g=1.0, b=0.0)


    glPopMatrix()


    glEnable(GL_DEPTH_TEST)
    glEnable(GL_FOG)


    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_hud_triangle(x1, y1, x2, y2, x3, y3, fill=True, r=1.0, g=1.0, b=1.0):
    glColor3f(r, g, b)
    if fill:
        glBegin(GL_TRIANGLES)
        glVertex2f(x1, y1); glVertex2f(x2, y2); glVertex2f(x3, y3)
        glEnd()
    else:
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x1, y1); glVertex2f(x2, y2); glVertex2f(x3, y3)
        glEnd()


def draw_star_symbol(cx, cy, size=14, active=True):
    r, g, b = (1.0, 0.85, 0.1) if active else (0.25, 0.25, 0.25)
    draw_hud_triangle(cx, cy + size, cx - size*0.4, cy, cx + size*0.4, cy, fill=active, r=r, g=g, b=b)
    draw_hud_triangle(cx, cy - size, cx - size*0.4, cy, cx + size*0.4, cy, fill=active, r=r, g=g, b=b)
    draw_hud_triangle(cx - size, cy, cx, cy - size*0.4, cx, cy + size*0.4, fill=active, r=r, g=g, b=b)
    draw_hud_triangle(cx + size, cy, cx, cy - size*0.4, cx, cy + size*0.4, fill=active, r=r, g=g, b=b)


def draw_top_hud():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_DEPTH_TEST)
    glDisable(GL_FOG)
    glEnable(GL_BLEND)

    dist_val = total_distance_travelled / 10.0
    total_score = int(dist_val * 10) + score
    spd_val = int(abs(carz_speed))
    draw_hud_text(20, SCREEN_HEIGHT - 35, f"SPEED: {spd_val} KM/H", font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=0.5, b=0.1)
    draw_hud_text(20, SCREEN_HEIGHT - 60, f"DISTANCE: {dist_val:.1f} KM", font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=1.0, b=0.2)
    draw_hud_text(20, SCREEN_HEIGHT - 85, f"SCORE: {total_score}", font=GLUT_BITMAP_HELVETICA_18, r=0.2, g=1.0, b=0.4)
    draw_hud_text(20, SCREEN_HEIGHT - 110, f"KILLS: {killed_enemies}", font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=0.6, b=0.9)

    draw_hud_text(SCREEN_WIDTH - 280, SCREEN_HEIGHT - 30, "carz HP:", font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=0.3, b=0.3)
    for i in range(5):
        tx = SCREEN_WIDTH - 190 + i * 25
        ty = SCREEN_HEIGHT - 30
        is_active = (i < carz_health)
        col = (0.1, 0.9, 0.2) if is_active else (0.3, 0.3, 0.3)
        draw_hud_triangle(tx, ty + 12, tx - 9, ty - 6, tx + 9, ty - 6, fill=is_active, r=col[0], g=col[1], b=col[2])

    draw_hud_text(SCREEN_WIDTH - 280, SCREEN_HEIGHT - 60, "CHAR HP:", font=GLUT_BITMAP_HELVETICA_18, r=0.3, g=0.8, b=1.0)
    for i in range(5):
        tx = SCREEN_WIDTH - 190 + i * 25
        ty = SCREEN_HEIGHT - 60
        is_active = (i < int(plr_hlth + 0.01))
        col = (0.2, 0.8, 1.0) if is_active else (0.3, 0.3, 0.3)
        draw_hud_triangle(tx, ty + 12, tx - 9, ty - 6, tx + 9, ty - 6, fill=is_active, r=col[0], g=col[1], b=col[2])

    draw_hud_text(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT - 30, "WANTED:", font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=1.0, b=1.0)
    for i in range(3):
        sx = SCREEN_WIDTH // 2 + 10 + i * 36
        sy = SCREEN_HEIGHT - 22
        draw_star_symbol(sx, sy, size=12, active=(i < star_wanted))

    ci = round(carz_x / (INTERSECTION_INTERVAL * CELL_SIZE)) * INTERSECTION_INTERVAL
    cj = round(carz_z / (INTERSECTION_INTERVAL * CELL_SIZE)) * INTERSECTION_INTERVAL
    dist_to_sig = math.hypot(carz_x - ci * CELL_SIZE, carz_z - cj * CELL_SIZE)
    if 15.0 < dist_to_sig < 75.0:
        if get_traffic_states() in ("red", "yellow"):
            draw_hud_text(SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT - 90, "WARNING: Red Light Ahead!", font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=0.1, b=0.1)

    if carz_health <= 1:
        draw_hud_text(SCREEN_WIDTH // 2 - 90, SCREEN_HEIGHT - 140, "WARNING: BRAKES FAILED!", font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=0.1, b=0.1)

    if game_state == "GAME_OVER":
        msg = "BUSTED! YOU ARE ARRESTED!" if wanted_busted else "carz DESTROYED! GAME OVER!"
        draw_hud_text(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2, msg, font=GLUT_BITMAP_TIMES_ROMAN_24, r=1.0, g=0.1, b=0.1)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_FOG)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def get_carz_light_factor(light_radius=15.0):
    global  day_shifting_light, street_lamp_radius

    night_factor = max(0.0, 1.0 - (day_shifting_light - 0.2) / 0.8)
    if night_factor <= 0.01 or not street_lamp_radius:
        return 0.0

    max_illumination = 0.0
    for lx, lz in street_lamp_radius:
        dist = math.hypot(carz_x - lx, carz_z - lz)
        if dist < light_radius:
            factor = (1.0 - (dist / light_radius)) * night_factor
            if factor > max_illumination:
                max_illumination = factor

    return max_illumination


def display():
    global street_lamp_radius
    street_lamp_radius.clear()  

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    current_time = time.time()
    dt = min(current_time - last_frame_time, 0.1)

    if game_state == "GAME_OVER" :
        draw_game_over_overlay()
        glutSwapBuffers()
        return

    if game_state == "PLAYING":
        update_vehicle_physics()
        update_police(dt)
        update_rain(dt)
        update_bosts()
        update_health_bosts()
        update_puddles()

    rad_h = math.radians(carz_heading)
    fx, fz = math.sin(rad_h), -math.cos(rad_h)
    side_x, side_z = math.cos(rad_h), math.sin(rad_h)

    if camera_mode == "3rd":
        gluLookAt(carz_x - 16.0 * fx, 6.0, carz_z - 16.0 * fz,
                  carz_x + 10.0 * fx, 1.5, carz_z + 10.0 * fz,
                  0, 1, 0)
    else:
        gluLookAt(carz_x - 0.55 * side_x + 0.1 * fx, 1.65, carz_z - 0.55 * side_z + 0.1 * fz,
                  carz_x - 0.55 * side_x + 20.0 * fx, 1.6, carz_z - 0.55 * side_z + 20.0 * fz,
                  0, 1, 0)

    ci, cj = stream_world(carz_x, carz_z)
    update_sky()
    draw_ground(carz_x, carz_z)
    draw_footpaths(ci, cj)
    draw_roads(ci, cj)
    draw_world(ci, cj)

    draw_bosts()
    draw_health_bosts()
    draw_puddles()

    if activated_police and star_wanted > 0:
        draw_police_carz(police_pos_x, police_pos_z, police_head)

    if game_state == "PLAYING" or game_state == "GAME_OVER":
        update_and_draw_enemies(dt)
        update_and_draw_bullets(dt)

    draw_rain()
    if camera_mode=="3rd":
        draw_3d_carz(carz_x, carz_z, carz_heading + drift_angle)

    if camera_mode == "1st":
        draw_dashboard()

    draw_top_hud()

    if game_state == "PAUSED":
        draw_pause_overlay()
    glutSwapBuffers()


def keyboardListener(key, x, y):
    global cheat_mode,key_sign, game_state, camera_mode, star_wanted, police_active, plyr_bltts
    if key == b'\x1b':  
        game_state = "PAUSED" if game_state == "PLAYING" else "PLAYING"
        glutPostRedisplay()
        return

    if game_state != "PLAYING":
        return
    k = key.decode("utf-8").lower() if isinstance(key, bytes) else key.lower()
    if k == 'c':
        cheat_mode = not cheat_mode

        if cheat_mode:
            print("CHEAT MODE: ON")
            star_wanted = 0
            activated_police= False
            plyr_bltts.clear()
        else:
            print("CHEAT MODE: OFF")

        glutPostRedisplay()


    if k == 'v':
        camera_mode = "1st" if camera_mode == "3rd" else "3rd"
        glutPostRedisplay()
        return
    elif k == ' ':
        key_sign['space'] = True

    if k in key_sign:
        key_sign[k] = True


def keyboard_up(key, x, y):
    global key_sign
    k = key.decode('utf-8').lower() if isinstance(key, bytes) else key.lower()
    if k == ' ':
        key_sign['space'] = False
    if k in key_sign:
        key_sign[k] = False


def specialKeyListener(key, x, y):
    global key_sign, game_state
    if game_state != "PLAYING":
        return
    if key == GLUT_KEY_UP:
        key_sign['up'] = True
    elif key == GLUT_KEY_DOWN:
        key_sign['down'] = True
    elif key == GLUT_KEY_LEFT:
        key_sign['left'] = True
    elif key == GLUT_KEY_RIGHT:
        key_sign['right'] = True


def special_up(key, x, y):
    global key_sign
    if key == GLUT_KEY_UP:
        key_sign['up'] = False
    elif key == GLUT_KEY_DOWN:
        key_sign['down'] = False
    elif key == GLUT_KEY_LEFT:
        key_sign['left'] = False
    elif key == GLUT_KEY_RIGHT:
        key_sign['right'] = False


def carz_collides(test_x, test_z, test_angle):
    
    carz_half_width = 1.6
    carz_half_length = 3.1


    rad = math.radians(test_angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    local_corners = [
        (-carz_half_width, -carz_half_length),
        ( carz_half_width, -carz_half_length),
        ( carz_half_width,  carz_half_length),
        (-carz_half_width,  carz_half_length)
    ]

    carz_corners = []
    for lx, lz in local_corners:
        world_x = test_x + lx * cos_a + lz * sin_a
        world_z = test_z - lx * sin_a + lz * cos_a
        carz_corners.append((world_x, world_z))


    carz_min_x = min(p[0] for p in carz_corners)
    carz_max_x = max(p[0] for p in carz_corners)
    carz_min_z = min(p[1] for p in carz_corners)
    carz_max_z = max(p[1] for p in carz_corners)

    ci, cj = camera_block(test_x, test_z)

    POINT_OBJECT_RADII = {
        "trees": 1.2,
        "lamps": 0.6,
        "street_lamps": 0.6,
        "traffic_lights": 0.3,
        "road_signs": 0.5
    }

    BOX_OBJECT_KEYS = ["buildings", "hospitals", "schools", "garage"]

    for bi in range(ci - 1, ci + 2):
        for bj in range(cj - 1, cj + 2):
            block = block_cache.get((bi, bj))
            if block is None:
                continue

            for key in BOX_OBJECT_KEYS:
                for obj in block.get(key, []):
                
                    x, z, w, d = obj[0], obj[1], obj[2], obj[3]

                    obj_min_x = x - w / 2.0
                    obj_max_x = x + w / 2.0
                    obj_min_z = z - d / 2.0
                    obj_max_z = z + d / 2.0

                    if (
                        carz_max_x > obj_min_x and
                        carz_min_x < obj_max_x and
                        carz_max_z > obj_min_z and
                        carz_min_z < obj_max_z
                    ):
                        return True

            for key, radius in POINT_OBJECT_RADII.items():
                for obj in block.get(key, []):
                    x, z = obj[0], obj[1]  

                    if (
                        carz_max_x > x - radius and
                        carz_min_x < x + radius and
                        carz_max_z > z - radius and
                        carz_min_z < z + radius
                    ):
                        return True

    return False

def cheat_auto_shoot():
    global plyr_bltts, last_cheat_shot

    current_time = time.time()

    if current_time - last_cheat_shot < CHEAT_BULLET_COOLDOWN:
        return

    rad_h = math.radians(carz_heading)


    forward_x = math.sin(rad_h)
    forward_z = -math.cos(rad_h)

    best_enemy = None
    best_distance = float('inf')

    for enemy in enemies:

        dx = enemy['x'] - carz_x
        dz = enemy['z'] - carz_z

        distance = math.hypot(dx, dz)

        if distance < 0.01 or distance > CHEAT_VISION_DISTANCE:
            continue


        dir_x = dx / distance
        dir_z = dz / distance

 
        dot = forward_x * dir_x + forward_z * dir_z
        dot = max(-1.0, min(1.0, dot))

        angle = math.degrees(math.acos(dot))

        if angle <= CHEAT_VISION_ANGLE:


            if distance < best_distance:
                best_distance = distance
                best_enemy = enemy


    if best_enemy is None:
        return

    dx = best_enemy['x'] - carz_x
    dz = best_enemy['z'] - carz_z
    distance = math.hypot(dx, dz)

    if distance < 0.01:
        return

    dir_x = dx / distance
    dir_z = dz / distance

    plyr_bltts.append({
        'x': carz_x,
        'y': 1.5,
        'z': carz_z,
        'vx': dir_x * 120.0,
        'vz': dir_z * 120.0
    })

    last_cheat_shot = current_time



def update_vehicle_physics():
    global carz_x, carz_z, camra_x, camra_z, carz_speed, last_frame_time, current_rpm, steering_ngle
    global uncontrolled_period, star_wanted, police_active, passed_red_light_factor, zone_speed_limit, carz_health
    global target_carz_heading, carz_heading, last_turn_time, total_distance_travelled, drift_angle
    global cheat_mode,cheat_speed,cheat_turn_speed

    current_time = time.time()
    dt = current_time - last_frame_time
    last_frame_time = current_time

    dt = min(dt, 0.1)

    if cheat_mode:

        carz_speed = cheat_speed
        rad_h = math.radians(carz_heading)

        forward_x = math.sin(rad_h)
        forward_z = -math.cos(rad_h)

        world_speed = cheat_speed * 0.25

        carz_x += forward_x * world_speed * dt
        carz_z += forward_z * world_speed * dt

        total_distance_travelled += abs(world_speed) * dt

        cheat_auto_shoot()

        return

    throttle = key_sign['w'] or key_sign['up']
    brake_reverse = key_sign['s'] or key_sign['down']
    steer_left = key_sign['a'] or key_sign['left']
    steer_right = key_sign['d'] or key_sign['right']
    hard_brake = key_sign['space']

    if carz_health <= 1:
        brake_reverse = False
        hard_brake = False


    inter_i = round(carz_x / (INTERSECTION_INTERVAL * CELL_SIZE)) * INTERSECTION_INTERVAL
    inter_j = round(carz_z / (INTERSECTION_INTERVAL * CELL_SIZE)) * INTERSECTION_INTERVAL
    dist_to_intersection_center = math.hypot(carz_x - inter_i * CELL_SIZE, carz_z - inter_j * CELL_SIZE)
    at_intersection = (dist_to_intersection_center < 25.0)

    if at_intersection and (current_time - last_turn_time > 0.4):
        if carz_speed < 0:
            if steer_left:
                target_carz_heading = (target_carz_heading + 90.0) % 360.0
                last_turn_time = current_time
            elif steer_right:
                target_carz_heading = (target_carz_heading - 90.0) % 360.0
                last_turn_time = current_time
        else:
            if steer_left:
                target_carz_heading = (target_carz_heading - 90.0) % 360.0
                last_turn_time = current_time
            elif steer_right:
                target_carz_heading = (target_carz_heading + 90.0) % 360.0
                last_turn_time = current_time

    diff = (target_carz_heading - carz_heading + 180.0) % 360.0 - 180.0
    carz_heading += diff * min(1.0, 2.0 * dt)

    rad_h = math.radians(carz_heading)

    side_x = math.cos(rad_h)
    side_z = math.sin(rad_h)

    if uncontrolled_period > 0:
        uncontrolled_period -= dt
        carz_x += side_x * math.sin(time.time() * 12.0) * 18.0 * dt
        carz_z += side_z * math.sin(time.time() * 12.0) * 18.0 * dt
        steer_left = False
        steer_right = False


    speed_ratio = min(1.0, abs(carz_speed) / max_speed)
    brake_power = 135.0 - (speed_ratio * 80.0)         
    hard_brake_power = 210.0 - (speed_ratio * 100.0)   

    if hard_brake:
        if carz_speed > 0:
            carz_speed = max(0.0, carz_speed - hard_brake_power * dt)
        elif carz_speed < 0:
            carz_speed = min(0.0, carz_speed + hard_brake_power * dt)
    elif brake_reverse:
        if carz_speed > 0.0:

            carz_speed = max(0.0, carz_speed - brake_power * dt)
        else:

            carz_speed -= acceleration * dt
    elif throttle:
        if carz_speed < 0.0:

            carz_speed = min(0.0, carz_speed + brake_power * dt)
        else:

            carz_speed += acceleration * dt
    else:
        if carz_speed > 0:
            carz_speed = max(0.0, carz_speed - deceleration * dt)
        elif carz_speed < 0:
            carz_speed = min(0.0, carz_speed + deceleration * dt)

    carz_speed = max(max_reverse_speed, min(max_speed, carz_speed))


    if at_intersection and hard_brake and abs(carz_speed) > 10.0 and (steer_left or steer_right):
        target_drift = -22.0 if steer_left else 22.0
        drift_angle = lerp(drift_angle, target_drift, 12.0 * dt)
    else:
        drift_angle = lerp(drift_angle, 0.0, 10.0 * dt)



    target_steer = 0.0

    if steer_left:
        target_steer = -1.0

    if steer_right:
        target_steer = 1.0


    steer_strength = min(1.0, abs(carz_speed) / 70.0)

    steer_dir = -target_steer if carz_speed < 0 else target_steer

    if not at_intersection:
        carz_heading += steer_dir * 40.0 * steer_strength * dt
        target_carz_heading = carz_heading

    steering_ngle = lerp(steering_ngle, target_steer * 90.0, 10.0 * dt)



    world_speed = carz_speed * 0.25

    rad_h = math.radians(carz_heading)
    forward_x = math.sin(rad_h)
    forward_z = -math.cos(rad_h)


    new_x = carz_x + forward_x * world_speed * dt
    new_z = carz_z + forward_z * world_speed * dt


    if not carz_collides(new_x, new_z, carz_heading):
        carz_x = new_x
        carz_z = new_z
        total_distance_travelled += abs(world_speed) * dt
    else:
    
        carz_speed = 0.0

    ci = round(carz_x / (INTERSECTION_INTERVAL * CELL_SIZE)) * INTERSECTION_INTERVAL
    cj = round(carz_z / (INTERSECTION_INTERVAL * CELL_SIZE)) * INTERSECTION_INTERVAL
    sig_node = (ci, cj)
    dist_to_sig = math.hypot(carz_x - ci * CELL_SIZE, carz_z - cj * CELL_SIZE)
    if  dist_to_sig < 10.0 :

        light_state = get_traffic_states()
        if light_state in ("red", "yellow") and sig_node not in passed_red_light_factor:
            passed_red_light_factor.add(sig_node)
            star_wanted = min(3, star_wanted + 1)
            activated_police= True


    if is_in_school_or_hospital_zone(carz_x, carz_z) and abs(carz_speed) > 90.0:
        if not zone_speed_limit:
            star_wanted = min(3, star_wanted + 1)
            activated_police= True
            zone_speed_limit = True

    else:
        zone_speed_limit = False

    camra_x = carz_x - 16.0 * forward_x
    camra_z = carz_z - 16.0 * forward_z

    speed_ratio = abs(carz_speed) / 300.0
    gear = (speed_ratio * 4.5) % 1.0
    throttle_boost = 1800.0 if throttle else 0.0
    target_rpm = 900.0 + (gear * 4200.0) + (speed_ratio * 1500.0) + throttle_boost
    target_rpm = min(8000.0, max(800.0, target_rpm))
    current_rpm = lerp(current_rpm, target_rpm, 8.0 * dt)


def layout_pause_buttons():
    global rsm_bttn, qit_bttn
    cx = SCREEN_WIDTH // 2
    btn_w, btn_h = 220, 60
    gap = 20


    resume_y = SCREEN_HEIGHT // 2 - btn_h // 2
    quit_y   = resume_y + btn_h + gap


    rsm_bttn = (cx - btn_w // 2, resume_y, cx + btn_w // 2, resume_y + btn_h)
    qit_bttn   = (cx - btn_w // 2, quit_y,   cx + btn_w // 2, quit_y + btn_h)

    layout_game_over_buttons()


def init():
    glEnable(GL_DEPTH_TEST)


    global raindrops
    raindrops = []
    for _ in range(RAIN_COUNT):
        x = random.uniform(-100, 100)
        y = random.uniform(0, 50)
        z = random.uniform(-100, 100)
        speed = random.uniform(30.0, 50.0)
        length = random.uniform(1.2, 2.5)
        raindrops.append([x, y, z, speed, length])


    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


    glEnable(GL_FOG)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_START, 700.0)
    glFogf(GL_FOG_END, 1400.0)


    stream_world(camra_x, camra_z)


def reshape(w, h):
    global SCREEN_WIDTH, SCREEN_HEIGHT
    SCREEN_WIDTH = w
    SCREEN_HEIGHT = h
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, float(w) / float(h if h else 1), 0.1, 1500.0)
    glMatrixMode(GL_MODELVIEW)
    layout_pause_buttons()
    glutPostRedisplay()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"ROAD STRIKE")


    glEnable(GL_DEPTH_TEST)
    init()
    layout_pause_buttons()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboard_up)
    glutSpecialFunc(specialKeyListener)
    glutSpecialUpFunc(special_up)
    glutMouseFunc(mouse)
    glutMotionFunc(mouse_motion)
    glutPassiveMotionFunc(mouse_motion)
    glutTimerFunc(16, update_time, 0)
    glutIdleFunc(glutPostRedisplay)
    glutMainLoop()


if __name__ == "__main__":
    main()
