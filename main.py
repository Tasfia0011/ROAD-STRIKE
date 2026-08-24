from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random, math,time

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
time_of_day = 0.0  # what daytime is now? morning/noon/day
ambient_light = 1.0  # change of environment color according to day time
game_state = "PLAYING"

# Button rectangles in screen pixels (x1, y1, x2, y2) — recalculated each resize
resume_btn = (0, 0, 0, 0)
quit_btn   = (0, 0, 0, 0)
# ---------------- camera & vehicle mode ----------------
car_x, car_z = 0.0, 0.0      # car position in world space
cam_x, cam_z = 0.0, 15.0     # camera position in world space
cam_angle = 0.0              # fixed camera angle facing straight forward
camera_mode = "3rd"          # "3rd" (3rd person view) or "1st" (1st person simulator view)
current_rpm = 900.0          # Current engine RPM (800 - 8000 RPM)
steering_wheel_angle = 0.0   # Visual steering wheel angle in FPV
car_angle=0
steer=0
# ---------------- Rain System ----------------
RAIN_COUNT = 1000 #number of raindrops stored
raindrops = []
is_raining = False
# Wet weather physics multipliers
WET_FRICTION_MULT = 0.35    # 65% reduction in tire friction (coasts much further)
WET_ACCEL_MULT = 0.50       # 50% reduction in acceleration/braking grip
WET_STEER_MULT = 0.40       # 60% reduction in turn steering sharp response
last_rain_toggle = time.time() #duration between each rain

car_speed = 0.0
max_speed = 300.0         # Top forward speed (0 - 300 km/h)
max_reverse_speed = -60.0 # Top reverse speed (km/h)
acceleration = 18.0       # Acceleration build up rate
deceleration = 32.0       # Coasting friction when no drive key is held
steering_speed = 3.0     # Sideways car movement speed (units/sec)

INTERSECTION_INTERVAL = 3  # Continuous road grid on every block
ROAD_DRAW_RADIUS = 3       # Optimal road rendering radius for fast 60+ FPS performance

# Input tracking for WASD and 4 Arrow keys
key_states = {'w': False, 's': False, 'a': False, 'd': False, 'up': False, 'down': False, 'left': False, 'right': False}
last_frame_time = time.time()

# ---------------- world / road-grid data ----------------
# Instead of one straight road, the city is an infinite grid of streets and blocks
#  Every intersection is a 4-way turn, and the
# grid streams in every direction forever as the car drives around.
ROAD_WIDTH = 20.0
FOOTPATH_WIDTH = 4.0
CELL_SIZE = 150               # size of each block of buildings tree etc
BLOCK_MARGIN = ROAD_WIDTH / 2.0 + FOOTPATH_WIDTH   # gap before buildable land starts


VIEW_RADIUS = 1                 # how many blocks out (in every direction) get streamed in
PRUNE_MARGIN = VIEW_RADIUS + 2    # cached blocks further than this get droppeded

# cache of generated blocks: {(bi, bj): {"trees": [...], "buildings": [...], "lamps": [...]}}
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

#takes players position as input and returns the current block position
def camera_block(cx, cz):
    return int(math.floor(cx / CELL_SIZE)), int(math.floor(cz / CELL_SIZE))

#controls color shade according to day night
def set_env_color(r, g, b):
    glColor3f(r * ambient_light, g * ambient_light, b * ambient_light)

# each block of the world is controlled by this func & takes block num as input
def generate_block(bi, bj):

    global INTERSECTION_INTERVAL, BLOCK_MARGIN

    #ensures a particular block always has the same structure of buildings,trees
    # Even if the block is deleted ,it will generate the deleted block with same layout again
    seed = (bi * 73856093) ^ (bj * 19349663) ^ 0x9E3779B9
    rnd = random.Random(seed)

# this part determines the boundary coordinates of the block
    bx0 = bi * CELL_SIZE + BLOCK_MARGIN
    bx1 = (bi + 1) * CELL_SIZE - BLOCK_MARGIN
    bz0 = bj * CELL_SIZE + BLOCK_MARGIN
    bz1 = (bj + 1) * CELL_SIZE - BLOCK_MARGIN

#area of the block in both axis to define the usable area in block
    area_w = bx1 - bx0
    area_d = bz1 - bz0

#things inside the block
    trees = []
    buildings = []
    hospitals = []
    schools = []
    lamps=[]
    street_lamps=[]
    traffic_lights = []
    road_signs=[]
    garage=[]

    # inward block corners
    fz0 = bj * CELL_SIZE + ROAD_WIDTH / 2.0 + FOOTPATH_WIDTH / 2.0
    fx0 = bi * CELL_SIZE + ROAD_WIDTH / 2.0 + FOOTPATH_WIDTH / 2.0
    fx1 = (bi + 1) * CELL_SIZE - ROAD_WIDTH / 2.0 - FOOTPATH_WIDTH / 2.0
    fz1 = (bj + 1) * CELL_SIZE - ROAD_WIDTH / 2.0 - FOOTPATH_WIDTH / 2.0

    #since intersection lvl=4 here so if bi,bj s position is  multiple of 4
    # ensures i get road intersection after 4 or 8 or 12 etc blocks.after every 4 blocks
    borders_road = (bi % INTERSECTION_INTERVAL == 0) or (bj % INTERSECTION_INTERVAL == 0)

    # it decides will it generate hospita or school or a block of buildings near intersection
    landmark_roll = rnd.random() if borders_road else 1.0

    if landmark_roll < 0.05:
        # Spawn a Hospital in the center of the block
        x = (bx0 + bx1) / 2.0
        z = (bz0 + bz1) / 2.0
        hospitals.append((x, z, 22.0, 22.0, 18.0))  #(x,z,width,depth,height)

        #puts the speed limit board
        road_signs.append((fx0, fz0+5, 0))
        road_signs.append((fx1, fz0+5, 0))
        road_signs.append((fx0 , fz1-5 , 0))
        road_signs.append((fx1, fz1-5, 0))

    elif landmark_roll < 0.1:
        # Spawn a School in the center of the block
        x = (bx0 + bx1) / 2.0
        z = (bz0 + bz1) / 2.0
        schools.append((x, z, 28.0, 16.0, 10.0))  # Long and low-rise structure

        #puts speed limit sign
        road_signs.append((fx0, fz0 + 5, 0))
        road_signs.append((fx1, fz0 + 5, 0))
        road_signs.append((fx0, fz1 - 5, 0))
        road_signs.append((fx1, fz1 - 5, 0))


    elif landmark_roll < 0.13:
        # Spawn a Garage in the center of the block
        x = (bx0 + bx1) / 2.0
        z = (bz0 + bz1) / 2.0
        garage.append((x, z, 28.0, 16.0, 10.0))  # Long and low-rise structure

    else:
        #divides each block in smaller blocks with rows and cols
        #each smaller blocks contains either tree/building/open space
        cols = max(1, int(area_w / 16))
        rows = max(1, int(area_d / 16))
        cw = area_w / cols
        cd = area_d / rows

        for gx in range(cols):
            for gz in range(rows):
                cx0 = bx0 + gx * cw
                cz0 = bz0 + gz * cd
                #random positions preventing everything from being perfectly aligned
                x = cx0 + rnd.uniform(cw * 0.25, cw * 0.75)
                z = cz0 + rnd.uniform(cd * 0.25, cd * 0.75)
                r = rnd.random()

                #if r<0.22 -> tree , if r <0.88 -> building else open space
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



        temp=7 #extra distance of lamps from corners
        lamps = [(fx0, fz0+temp), (fx1, fz0+temp), (fx0, fz1-temp), (fx1, fz1-temp),
                 ((fx0 + fx1) / 2.0, fz0+temp), ((fx0 + fx1) / 2.0, fz1-temp)]
        LAMP_SPACING = 35.0  # Distance between consecutive street lamps along the block
        inset = 10.0  # Distance from intersection corners to first street lamp

        #  Place lamps along North and South block edges
        z_pos = fz0 + inset
        while z_pos <= fz1 - inset:
            street_lamps.append((fx0, z_pos, 90))  # Left side footpath
            street_lamps.append((fx1, z_pos, -90))  # Right side footpath
            z_pos += LAMP_SPACING

        #  Place lamps along East and West block edges
        x_pos = fx0 + inset
        while x_pos <= fx1 - inset:
            street_lamps.append((x_pos, fz0, 0))  # Bottom side footpath
            street_lamps.append((x_pos, fz1, 180))  # Top side footpath
            x_pos += LAMP_SPACING

        # Only generate traffic lights at true road intersections
        if bi % INTERSECTION_INTERVAL == 0 and bj % INTERSECTION_INTERVAL == 0:
            x = bi * CELL_SIZE
            z = bj * CELL_SIZE
            offset = ROAD_WIDTH / 2.0 + FOOTPATH_WIDTH / 2.0  # Offset to corner of curb

            traffic_lights = [
                (x - offset, z - offset, 90),  # SW Corner facing East
                (x + offset, z - offset, 0),  # SE Corner facing North
                (x + offset, z + offset, 270),  # NE Corner facing West
                (x - offset, z + offset, 180)  # NW Corner facing South
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
    #generates the block around my current block
    for bi in range(ci - VIEW_RADIUS, ci + VIEW_RADIUS + 1):
        for bj in range(cj - VIEW_RADIUS, cj + VIEW_RADIUS + 1):
            if (bi, bj) not in block_cache:
                block_cache[(bi, bj)] = generate_block(bi, bj)
#gets rid of further blocks from the player.keeps upto 3 blocks
    stale = [key for key in block_cache
             if abs(key[0] - ci) > PRUNE_MARGIN or abs(key[1] - cj) > PRUNE_MARGIN]
    for key in stale:
        del block_cache[key]

    return ci, cj


def update_time(value):
    global time_of_day,game_state

    if game_state == "PLAYING":
        time_of_day += 0.0005

        if time_of_day >= 1.0:
            time_of_day = 0.0

    glutPostRedisplay()
    glutTimerFunc(16, update_time, 0)


def draw_button(rect, label):
    x1, y1, x2, y2 = rect #react= button coordinates
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
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_DEPTH_TEST)
    glDisable(GL_FOG)

    glEnable(GL_BLEND)
    glColor4f(0, 0, 0, 0.6)
    glBegin(GL_QUADS)
    glVertex2f(0, 0); glVertex2f(WINDOW_WIDTH, 0)
    glVertex2f(WINDOW_WIDTH, WINDOW_HEIGHT); glVertex2f(0, WINDOW_HEIGHT)
    glEnd()

    glColor3f(1, 1, 1)
    glRasterPos2f(WINDOW_WIDTH / 2 -40, WINDOW_HEIGHT / 2 + 150)
    for ch in "PAUSED":
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))

    draw_button(resume_btn, "Resume")
    draw_button(quit_btn, "Quit")

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_FOG)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def point_in_rect(px, py, rect):
    x1, y1, x2, y2 = rect
    return x1 <= px <= x2 and y1 <= py <= y2

# ---------------- ground / road / footpaths ----------------

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

    # Disable FOG so light blue fog never tints the black road
    glDisable(GL_FOG)

    # Pure 100% pitch black asphalt
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

    glEnable(GL_FOG)  # Re-enable FOG for background scenery


def draw_lane_markings(ci, cj):
    dash_len, gap_len = 4.0, 4.0
    step = dash_len + gap_len
    lo = -(ROAD_DRAW_RADIUS + 1) * CELL_SIZE
    hi = (ROAD_DRAW_RADIUS + 1) * CELL_SIZE

    # dashed centre line along every north-south road
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

    # dashed centre line along every east-west road
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

    # yellow kerb/edge lines running the length of every road
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

#make boxes with w,h and d as parameters
def draw_box(cx, base_y, cz, w, h, d, color):
    x0, x1 = cx - w / 2, cx + w / 2
    y0, y1 = base_y, base_y + h
    z0, z1 = cz - d / 2, cz + d / 2

    faces = [
        ((0, 0, 1), [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]),  # front
        ((0, 0, -1), [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)]),  # back
        ((-1, 0, 0), [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)]),  # left
        ((1, 0, 0), [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)]),  # right
        ((0, 1, 0), [(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)]),  # top
        ((0, -1, 0), [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)]),  # bottom
    ]
    set_env_color(*color)

    glBegin(GL_QUADS)
    for normal, verts in faces:
        glNormal3fv(normal)
        for v in verts:
            glVertex3fv(v)
    glEnd()

#draws text inside the slow sign
def draw_3d_text(x, y, z, text, color=(0, 0, 0), scale=0.01,angle=0):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(angle, 0, 1, 0)
    glColor3f(*color)
    glScalef(scale, scale, scale)

    for ch in text:
        glutStrokeCharacter(GLUT_STROKE_ROMAN, ord(ch))
    glPopMatrix()

#draws the max speed sign near schools and hospitals
def draw_slow_sign(cx, cz, angle=0):
    pole = (0.2, 0.2, 0.2)
    red = (0.9, 0.05, 0.05)
    white = (1.0, 1.0, 1.0)
    black = (0.05, 0.05, 0.05)

    glPushMatrix()
    glTranslatef(cx, 0, cz)
    glRotatef(angle, 0, 1, 0)

    # Pole
    draw_box(0, 0, 0, 0.8, 4, 0.2, pole)

    # Top red banner
    draw_box(0, 5.6, 0, 2.5, 0.5, 0.2, red)

    # Speed-limit sign
    draw_box(0, 3.2, 0, 4.5, 2.8, 0.2, red)

    # White inner area both front and back
    draw_box(0, 3.2, -0.12, 3.8, 2.4, 0.03, white)
    draw_box(0, 3.2, 0.12, 3.8, 2.4, 0.03, white)

    # Max Speed & 20  both front and back side
    draw_3d_text(
        1.7, 4.9, -0.25,
        "Max Speed",
        color=black,
        scale=0.005,angle=180)
    draw_3d_text(
        0.7, 3.5, -0.25,
        "80",
        color=black,
        scale=0.012,angle=180)

    glPushMatrix()
    glRotatef(180, 0, 1, 0)
    draw_3d_text(
        1.7, 4.9, -0.25,
        "Max Speed",
        color=black,
        scale=0.005,angle=180)
    draw_3d_text(
        0.7, 3.5, -0.25,
        "80",
        color=black,
        scale=0.012,angle=180)
    glPopMatrix()

    glPopMatrix()


def draw_hospital(cx, cz):
    white = (0.9, 0.9, 0.9)
    red = (0.8, 0.05, 0.05)

    glPushMatrix()

    glTranslatef(cx, 0, cz)
    glScalef(1.4, 1.4, 1.4)
    glTranslatef(-cx, 0, -cz)

    # Main building
    draw_box(cx, 0, cz, 24, 10, 16, white)

    # Upper block
    draw_box(cx, 10, cz, 14, 7, 12, white)

    # RED CROSSES - 4 SIDES

    # Front (+Z)
    draw_box(cx, 13.5, cz + 6.05, 5, 1.0, 0.1, red)
    draw_box(cx, 11.5, cz + 6.05, 1.2, 5, 0.1, red)

    # Back (-Z)
    draw_box(cx, 13.5, cz - 6.05, 5, 1.0, 0.1, red)
    draw_box(cx, 11.5, cz - 6.05, 1.2, 5, 0.1, red)

    # Right (+X)
    draw_box(cx + 7.05, 13.5, cz, 0.1, 1.0, 5, red)
    draw_box(cx + 7.05, 11.5, cz, 0.1, 5, 1.2, red)

    # Left (-X)
    draw_box(cx - 7.05, 13.5, cz, 0.1, 1.0, 5, red)
    draw_box(cx - 7.05, 11.5, cz, 0.1, 5, 1.2, red)

#writing of hospital
    # Front (+Z)
    draw_3d_text(cx, 5, cz + 8.1, "HOSPITAL", red, 0.012, 0)

    # Back (-Z)
    draw_3d_text(cx, 5, cz - 8.1, "HOSPITAL", red, 0.012, 180)

    # Right (+X)
    draw_3d_text(cx + 12.1, 5, cz, "HOSPITAL", red, 0.012, 90)

    # Left (-X)
    draw_3d_text(cx - 12.1, 5, cz, "HOSPITAL", red, 0.012, 270)
    glPopMatrix()

    # Trees
    draw_tree(cx - 50, cz - 5, 6, "round")
    draw_tree(cx + 50, cz - 5, 6, "round")
    draw_tree(cx - 50, cz + 5, 5, "round")


def draw_school(cx, cz):
    brick = (0.65, 0.3, 0.2)
    white = (0.9, 0.85, 0.7)
    blue = (0.3, 0.65, 0.85)

    glPushMatrix()

    # Scale school around its center
    glTranslatef(cx, 0, cz)
    glScalef(2.5, 2.5, 2.5)
    glTranslatef(-cx, 0, -cz)

    draw_box(cx, 0, cz, 30, 8, 14, brick)
    draw_box(cx, 8, cz, 31, 0.6, 15, white)
    draw_box(cx, 3.5, cz + 7.1, 24, 3, 0.1, blue)
    draw_box(cx, 0, cz + 7.2, 4, 4, 0.2, white)

    # Writing of SCHOOL

    # Front (+Z)
    draw_3d_text(cx, 4, cz + 7.1, "SCHOOL", white, 0.012, 0)

    # Back (-Z)
    draw_3d_text(cx, 4, cz - 7.1, "SCHOOL", white, 0.012, 180)

    # Right (+X)
    draw_3d_text(cx + 15.1, 4, cz, "SCHOOL", white, 0.012, 90)

    # Left (-X)
    draw_3d_text(cx - 15.1, 4, cz, "SCHOOL", white, 0.012, 270)
    glPopMatrix()

    # Trees
    draw_tree(cx - 50, cz - 4, 6, "round")
    draw_tree(cx + 50, cz - 4, 6, "round")
    draw_tree(cx - 50, cz + 4, 5, "round")
    draw_tree(cx + 50, cz + 4, 5, "round")

#garage
def draw_garage(cx, cz):
    gray = (0.35, 0.35, 0.35)
    dark_gray = (0.15, 0.15, 0.15)
    white = (0.9, 0.9, 0.9)
    yellow = (0.9, 0.7, 0.05)

    glPushMatrix()

    # Scale garage around its center
    glTranslatef(cx, 0, cz)
    glScalef(2.0, 2.0, 2.0)
    glTranslatef(-cx, 0, -cz)

    # Main garage
    draw_box(cx, 0, cz, 24, 10, 18, gray)

    # Roof
    draw_box(cx, 10, cz, 26, 1, 20, dark_gray)

    # Front garage door (+Z)
    draw_box(cx, 5, cz + 9.1, 16, 8, 0.2, dark_gray)

    # Garage door horizontal lines
    for y in [2, 4, 6, 8]:
        draw_box(cx, y, cz + 9.25, 15.5, 0.15, 0.1, white)

    # GARAGE text - 4 sides
    # Front (+Z)
    draw_3d_text(cx - 4, 6.5, cz + 9.2,"GARAGE", yellow, 0.016, 0)

    # Back (-Z)
    draw_3d_text(cx + 4, 6.5, cz - 9.2,"GARAGE", yellow, 0.016, 180)

    # Right (+X)
    draw_3d_text(cx + 12.1, 6.5, cz + 4,"GARAGE", yellow, 0.016, 90)

    # Left (-X)
    draw_3d_text(cx - 12.1, 6.5, cz - 4,"GARAGE", yellow, 0.016, 270)
    glPopMatrix()

    draw_tree(cx - 50, cz - 4, 6, "round")
    draw_tree(cx + 50, cz - 4, 6, "round")
    draw_tree(cx - 50, cz + 4, 5, "round")
    draw_tree(cx + 50, cz + 4, 5, "round")

#lines on roads
def draw_intersections(ci, cj):
    #Zebra crossings + stop lines on every approach of every visible intersection of roads

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

#if the trafficlight is green red or yellow
def get_traffic_states():
    TRAFFIC_GREEN_TIME = 6
    TRAFFIC_YELLOW_TIME = 3
    TRAFFIC_RED_TIME = 6
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


def draw_windows(hw, hd, h, seed):
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

    # Main building body
    draw_box(0, 0, 0, w, h, d, color)

    # Roof
    roof_color = tuple(min(1.0, c * 0.75) for c in color)
    set_env_color(*roof_color)

    glBegin(GL_QUADS)
    glVertex3f(-w/2, h, -d/2)
    glVertex3f(w/2, h, -d/2)
    glVertex3f(w/2, h, d/2)
    glVertex3f(-w/2, h, d/2)
    glEnd()

    # Windows
    draw_windows(w/2, d/2, h, win_seed)

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
    global ambient_light
    night_factor = max(0.0, 1.0 - (ambient_light - 0.2) / 0.8)
    if night_factor <= 0.01:
        return


    glDepthMask(GL_FALSE)
    glBegin(GL_TRIANGLE_FAN)

    # Bright warm center
    glColor4f(1.0, 0.85, 0.3, 0.45 * night_factor)
    glVertex3f(0.0, 0.03, 0.0)

    # Soft edge falloff
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

    glScalef(1.5, 1.5, 1.5)  # Makes the entire lamp 1.5x bigger

    quad = gluNewQuadric()

    # 1. Main Vertical Pole
    glColor3f(0.25, 0.25, 0.28)
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quad, 0.22, 0.16, 8.0, 10, 1)
    glPopMatrix()

    # 2. Arm extending forward toward the road (+X direction)
    glPushMatrix()
    glTranslatef(0, 8.0, 0)
    glRotatef(180, 0, 1, 0)
    gluCylinder(quad, 0.15, 0.10, 3.0, 10, 1)
    glPopMatrix()

    # 3. Lamp head at end of arm
    glPushMatrix()
    glRotatef(90, 0, 1, 0)
    glTranslatef(3.0, 8.0, 0)

    # Housing
    glColor3f(0.15, 0.15, 0.17)
    glPushMatrix()
    glScalef(1.4, 0.25, 0.7)
    glutSolidCube(1)
    glPopMatrix()

    # Bottom Glowing Light Pad
    glColor3f(1.0, 0.9, 0.6)
    glBegin(GL_QUADS)
    glVertex3f(-0.6, -0.13, -0.3)
    glVertex3f(0.6, -0.13, -0.3)
    glVertex3f(0.6, -0.13, 0.3)
    glVertex3f(-0.6, -0.13, 0.3)
    glEnd()

    glPopMatrix()
    gluDeleteQuadric(quad)

    # --- 4. GROUND LIGHT POOL (Local Coordinates) ---
    # In unscaled local space, the arm projects 4.5 units along +X.
    # We draw the pool directly on the road surface underneath the lamp head:
    glPushMatrix()
    glTranslatef(0, 0, -4.0)
    draw_lamp_glow(radius=8.0)
    glPopMatrix()


    glPopMatrix()


def draw_traffic_light(x, z,rotation, state):
    glPushMatrix()
    glTranslatef(x, 0, z)
    glRotatef(rotation, 0, 1, 0)
    glScalef(2.5, 1.5, 2.5)
    # Pole
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

    # Traffic light box
    glColor3f(0.03, 0.03, 0.03)
    glPushMatrix()
    glTranslatef(0, 5, 0)
    glScalef(0.8, 2.0, 0.5)
    glutSolidCube(1)
    glPopMatrix()

    # Red
    if state == "red":
        glColor3f(1, 0, 0)
    else:
        glColor3f(0.15, 0, 0)
    glPushMatrix()
    glTranslatef(0, 5.45, -0.26)
    glutSolidSphere(0.18, 12, 12)
    glPopMatrix()

    # Yellow
    if state == "yellow":
        glColor3f(1, 1, 0)
    else:
        glColor3f(0.15, 0.15, 0)
    glPushMatrix()
    glTranslatef(0, 5, -0.26)
    glutSolidSphere(0.18, 12, 12)
    glPopMatrix()

    # Green
    if state == "green":
        glColor3f(0, 1, 0)
    else:
        glColor3f(0, 0.15, 0)
    glPushMatrix()
    glTranslatef(0, 4.55, -0.26)
    glutSolidSphere(0.18, 12, 12)
    glPopMatrix()

    glPopMatrix()


def update_rain(dt):
    global is_raining, last_rain_toggle

    #toggle rain after random time
    if time.time() - last_rain_toggle >= random.uniform(30,50):
        is_raining = not is_raining
        last_rain_toggle = time.time()

    if not is_raining:
        return

    # Update particle positions and wrap them around the moving camera
    for drop in raindrops:
        drop[1] -= drop[3] * dt  # Fall vertically down

        # Respawn drop at the top if it hits the ground
        if drop[1] < 0:
            drop[1] = random.uniform(40, 50)
            drop[0] = cam_x + random.uniform(-80, 80)
            drop[z_idx := 2] = cam_z + random.uniform(-80, 80)

        # Keep rain box centered dynamically around the camera position
        if abs(drop[0] - cam_x) > 80:
            drop[0] = cam_x + random.uniform(-80, 80)
        if abs(drop[2] - cam_z) > 80:
            drop[2] = cam_z + random.uniform(-80, 80)


def draw_rain():
    if not is_raining:
        return

    glDepthMask(GL_FALSE)  # Disable depth writes for clean alpha blending
    glLineWidth(1.2)

    # Semi-transparent translucent light blue/white rain strands
    glColor4f(0.7, 0.8, 0.95, 0.4)

    glBegin(GL_LINES)
    for x, y, z, speed, length in raindrops:
        glVertex3f(x, y, z)
        # Slight slant in movement to simulate realistic wind drop streak
        glVertex3f(x - 0.1, y - length, z - 0.1)
    glEnd()

    glDepthMask(GL_TRUE)


def draw_world(ci, cj):
    for bi in range(ci - VIEW_RADIUS, ci + VIEW_RADIUS + 1):
        for bj in range(cj - VIEW_RADIUS, cj + VIEW_RADIUS + 1):
            block = block_cache.get((bi, bj))
            if not block:
                continue
            # Draw unique landmark buildings
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
                draw_Street_lamp(x, z, angle)
            for (x, z,rotation )in block["traffic_lights"]:
                draw_traffic_light(x,z,rotation,get_traffic_states())
            for (x, z, angle) in block["road_signs"]:
                draw_slow_sign(x, z, angle)
            for (x, z, w, d, h) in block.get("garage", []):
                draw_garage(x, z)


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(t):
    # Smooth ease-in / ease-out curve
    return t * t * (3 - 2 * t)


def update_sky():
    global time_of_day,ambient_light
    colors = [
        (0.60, 0.85, 0.9),  # DAY: Vibrant sky blue
        (0.89, 0.59, 0.35),  # DUSK: Deep fiery orange/crimson
        (0.01, 0.02, 0.06),  # NIGHT: Near black indigo
        (0.3, 0.32, 0.5)  # DAWN: Warm peach/amber
    ]
    ambient_levels = [1.0, 0.55, 0.20, 0.55]
    # Determine segment index (0 to 3) and local parameter t
    segment = int(time_of_day * 4) % 4
    t = (time_of_day * 4) % 1.0

    # Apply non-linear easing to 't' for a natural rate of transition
    t_eased = smoothstep(t)

    # Get start and end colors for current phase
    c1 = colors[segment]
    c2 = colors[(segment + 1) % 4]

    # Interpolate each channel
    r = lerp(c1[0], c2[0], t_eased)
    g = lerp(c1[1], c2[1], t_eased)
    b = lerp(c1[2], c2[2], t_eased)

    # Interpolate ambient lighting factor
    a1 = ambient_levels[segment]
    a2 = ambient_levels[(segment + 1) % 4]
    ambient_light = lerp(a1, a2, t_eased)

    # update sky
    glClearColor(r, g, b, 1.0)
    #  Update fog color to match the sky!
    glFogfv(GL_FOG_COLOR, (r, g, b, 1.0))


def mouse(button, state, x, y):
    global game_state
    if game_state != "PAUSED" or button != GLUT_LEFT_BUTTON or state != GLUT_DOWN:
        return
    gl_y = WINDOW_HEIGHT - y
    if point_in_rect(x, gl_y, resume_btn):
        game_state = "PLAYING"
    elif point_in_rect(x, gl_y, quit_btn):
        glutLeaveMainLoop()

# ---------------- HUD & Dashboard Helper Functions ----------------

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


# ---------------- 3D Car Model ----------------

def draw_3d_car(cx, cz, angle):
    glPushMatrix()
    glTranslatef(cx, 0.2, cz)
    glRotatef(angle, 0, 1, 0)

    # 1. Main Chassis / Body (Glossy Red / Crimson)
    draw_box(0, 0.4, 0, 3.2, 0.9, 6.0, (0.85, 0.1, 0.15))

    # 2. Lower skirts / Front & Rear Bumper
    draw_box(0, 0.15, 0, 3.3, 0.35, 6.2, (0.15, 0.15, 0.15))

    # 3. Upper Cabin Roof Pillars & Open Frame (Glass removed)
    draw_box(0, 1.65, -1.3, 2.5, 0.2, 0.2, (0.1, 0.1, 0.15))   # Front windshield top frame bar
    draw_box(-1.25, 1.35, -0.4, 0.15, 0.8, 2.0, (0.1, 0.1, 0.15)) # Left side door frame
    draw_box(1.25, 1.35, -0.4, 0.15, 0.8, 2.0, (0.1, 0.1, 0.15))  # Right side door frame
    draw_box(0, 1.65, 1.2, 2.5, 0.2, 0.2, (0.1, 0.1, 0.15))    # Rear top frame bar

    # 4. 3D Driver / Player Character inside Car (Driver seat left side)
    quad = gluNewQuadric()

    # Driver Seat & Torso (Blue sports jacket)
    draw_box(-0.55, 1.05, 0.1, 0.7, 0.7, 0.5, (0.2, 0.35, 0.8))

    # Driver Head (Skin tone)
    glPushMatrix()
    glTranslatef(-0.55, 1.55, 0.1)
    glColor3f(0.95, 0.75, 0.6)
    gluSphere(quad, 0.32, 10, 10)
    glPopMatrix()

    # Driver Cap / Hair (Dark cap)
    glPushMatrix()
    glTranslatef(-0.55, 1.72, 0.08)
    glColor3f(0.12, 0.12, 0.15)
    gluSphere(quad, 0.30, 8, 8)
    glPopMatrix()

    # Driver Arms (Skin tone extending forward to steering wheel)
    draw_box(-0.55, 1.2, -0.35, 0.55, 0.15, 0.5, (0.95, 0.75, 0.6))

    # Interior 3D Steering Wheel
    glPushMatrix()
    glTranslatef(-0.55, 1.25, -0.65)
    glColor3f(0.15, 0.15, 0.18)
    gluCylinder(quad, 0.3, 0.3, 0.1, 10, 1)
    glPopMatrix()

    # Side Mirrors (towards front -Z)
    draw_box(-1.6, 1.25, -0.8, 0.35, 0.2, 0.4, (0.1, 0.1, 0.12))
    draw_box(1.6, 1.25, -0.8, 0.35, 0.2, 0.4, (0.1, 0.1, 0.12))

    # 5. Front Headlights (facing -Z, bright white/yellow)
    glColor3f(1.0, 1.0, 0.85)
    for side in (-1.1, 1.1):
        glPushMatrix()
        glTranslatef(side, 0.65, -3.01)
        glutSolidCube(0.4)
        glPopMatrix()

    # 6. Rear Taillights (facing +Z, glowing red)
    glColor3f(1.0, 0.05, 0.05)
    for side in (-1.1, 1.1):
        glPushMatrix()
        glTranslatef(side, 0.65, 3.01)
        glutSolidCube(0.4)
        glPopMatrix()

    # 7. Wheels (4 Corners)
    wheel_pos = [(-1.6, 0.45, -1.8), (1.6, 0.45, -1.8), (-1.6, 0.45, 1.8), (1.6, 0.45, 1.8)]
    for wx, wy, wz in wheel_pos:
        glPushMatrix()
        glTranslatef(wx, wy, wz)
        glRotatef(90 if wx > 0 else -90, 0, 1, 0)
        glColor3f(0.12, 0.12, 0.14)
        gluCylinder(quad, 0.5, 0.5, 0.4, 14, 1)
        # Wheel Rim Cap
        glColor3f(0.7, 0.7, 0.75)
        gluSphere(quad, 0.3, 10, 10)
        glPopMatrix()

    gluDeleteQuadric(quad)
    glPopMatrix()


# ---------------- Simulator Car Dashboard Overlay ----------------

def draw_dashboard():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_DEPTH_TEST)
    glDisable(GL_FOG)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # 1. Main Dashboard Base Housing
    dash_h = WINDOW_HEIGHT * 0.38
    glColor4f(0.02, 0.02, 0.02, 0.95)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(WINDOW_WIDTH, 0)
    glVertex2f(WINDOW_WIDTH, dash_h)
    glVertex2f(0, dash_h)
    glEnd()

    # Top Frame Line in Yellow
    glColor3f(1.0, 1.0, 0.0)
    glLineWidth(2.0)
    glBegin(GL_LINE_STRIP)
    glVertex2f(0, dash_h * 0.7)
    glVertex2f(WINDOW_WIDTH * 0.15, dash_h)
    glVertex2f(WINDOW_WIDTH * 0.85, dash_h)
    glVertex2f(WINDOW_WIDTH, dash_h * 0.7)
    glEnd()

    cx_speed = WINDOW_WIDTH * 0.28
    cy_speed = WINDOW_HEIGHT * 0.20
    R_speed = min(WINDOW_WIDTH, WINDOW_HEIGHT) * 0.17

    cx_rpm = WINDOW_WIDTH * 0.72
    cy_rpm = WINDOW_HEIGHT * 0.20
    R_rpm = R_speed

    # 2. SPEEDOMETER DIAL (LEFT)
    # Solid Black Circle Background with Yellow Outline
    draw_hud_circle(cx_speed, cy_speed, R_speed, fill=True, r=0.0, g=0.0, b=0.0, alpha=1.0)
    draw_hud_circle(cx_speed, cy_speed, R_speed, fill=False, r=1.0, g=1.0, b=0.0, alpha=1.0)

    # Speedometer Scale: Exactly 16 numbers starting from 0 to 300 (gap of 20) in YELLOW
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
        # YELLOW Colored Numbers
        draw_hud_text(nx, ny, text_str, font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=1.0, b=0.0)

    # Speedometer RED Indicator Pointer Stick
    sp_ratio = min(300.0, max(0.0, abs(car_speed))) / 300.0
    needle_ang = math.radians(225.0 - sp_ratio * 270.0)
    nx_sp = cx_speed + math.cos(needle_ang) * (R_speed * 0.88)
    ny_sp = cy_speed + math.sin(needle_ang) * (R_speed * 0.88)

    # Bright RED Pointer Stick
    glColor3f(1.0, 0.0, 0.0)
    glLineWidth(4.0)
    glBegin(GL_LINES)
    glVertex2f(cx_speed, cy_speed)
    glVertex2f(nx_sp, ny_sp)
    glEnd()

    draw_hud_circle(cx_speed, cy_speed, 8, fill=True, r=0.1, g=0.1, b=0.1)
    draw_hud_circle(cx_speed, cy_speed, 5, fill=True, r=1.0, g=0.0, b=0.0)

    # Parking Indicator (P) in Yellow
    draw_hud_text(cx_speed - 10, cy_speed - R_speed * 0.55, "(P)", font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=1.0, b=0.0)


    # 3. WORKING TACHOMETER / RPM METER DIAL (RIGHT)
    # Solid Black Circle Background with Yellow Outline
    draw_hud_circle(cx_rpm, cy_rpm, R_rpm, fill=True, r=0.0, g=0.0, b=0.0, alpha=1.0)
    draw_hud_circle(cx_rpm, cy_rpm, R_rpm, fill=False, r=1.0, g=1.0, b=0.0, alpha=1.0)

    # RPM Scale: 0 to 8 (x1000 RPM) in YELLOW
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

        # YELLOW Colored Numbers (0 to 8)
        nx = cx_rpm + math.cos(ang_rad) * (R_rpm * 0.68) - 5
        ny = cy_rpm + math.sin(ang_rad) * (R_rpm * 0.68) - 6
        draw_hud_text(nx, ny, str(i), font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=1.0, b=0.0)

    # RPM Working RED Indicator Pointer Stick
    rpm_ratio = min(8000.0, max(0.0, current_rpm)) / 8000.0
    needle_ang_rpm = math.radians(210.0 - rpm_ratio * 240.0)
    nx_rpm = cx_rpm + math.cos(needle_ang_rpm) * (R_rpm * 0.88)
    ny_rpm = cy_rpm + math.sin(needle_ang_rpm) * (R_rpm * 0.88)

    # Bright RED Pointer Stick
    glColor3f(1.0, 0.0, 0.0)
    glLineWidth(4.0)
    glBegin(GL_LINES)
    glVertex2f(cx_rpm, cy_rpm)
    glVertex2f(nx_rpm, ny_rpm)
    glEnd()

    draw_hud_circle(cx_rpm, cy_rpm, 8, fill=True, r=0.1, g=0.1, b=0.1)
    draw_hud_circle(cx_rpm, cy_rpm, 5, fill=True, r=1.0, g=0.0, b=0.0)

    # Warning Icon (!) in Yellow
    draw_hud_text(cx_rpm - 8, cy_rpm - R_rpm * 0.55, "(!)", font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=1.0, b=0.0)


    # 4. CENTER DIGITAL DISPLAY & TURN INDICATORS
    cx_mid = WINDOW_WIDTH * 0.5
    cy_mid = cy_speed

    glColor4f(0.8, 0.8, 0.0, 0.8)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(cx_mid - 80, cy_mid - 40)
    glVertex2f(cx_mid + 80, cy_mid - 40)
    glVertex2f(cx_mid + 80, cy_mid + 70)
    glVertex2f(cx_mid - 80, cy_mid + 70)
    glEnd()

    left_turn = key_states['a'] or key_states['left']
    right_turn = key_states['d'] or key_states['right']

    r_l, g_l, b_l = (1.0, 1.0, 0.0) if left_turn else (0.3, 0.3, 0.0)
    r_r, g_r, b_r = (1.0, 1.0, 0.0) if right_turn else (0.3, 0.3, 0.0)

    draw_hud_text(cx_mid - 65, cy_mid + 45, "<--", font=GLUT_BITMAP_HELVETICA_18, r=r_l, g=g_l, b=b_l)
    draw_hud_text(cx_mid + 40, cy_mid + 45, "-->", font=GLUT_BITMAP_HELVETICA_18, r=r_r, g=g_r, b=b_r)

    speed_text = f"{int(abs(car_speed))} KM/H"
    gear_text = "D" if car_speed >= 0 else "R"
    odo_text = f"165376"

    draw_hud_text(cx_mid - 35, cy_mid + 20, speed_text, font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=1.0, b=0.0)
    draw_hud_text(cx_mid - 8, cy_mid - 5, gear_text, font=GLUT_BITMAP_TIMES_ROMAN_24, r=1.0, g=0.0, b=0.0)
    draw_hud_text(cx_mid - 30, cy_mid - 30, odo_text, font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=1.0, b=0.0)


    # 5. AUXILIARY FUEL GAUGE (TEMP GAUGE REMOVED)
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


    # 6. INTERACTIVE STEERING WHEEL
    cx_wheel = WINDOW_WIDTH * 0.5
    cy_wheel = WINDOW_HEIGHT * 0.05
    R_wheel = WINDOW_HEIGHT * 0.12

    glPushMatrix()
    glTranslatef(cx_wheel, cy_wheel, 0)
    glRotatef(steering_wheel_angle, 0, 0, 1)

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


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    current_time = time.time()
    dt = min(current_time - last_frame_time, 0.1)

    if game_state == "PLAYING":
        update_vehicle_physics()
        update_rain(dt)

    if camera_mode == "3rd":
        # 3rd Person View
        rad = math.radians(car_angle)
        forward_x = -math.sin(rad)
        forward_z = -math.cos(rad)

        cam_x = car_x - forward_x * 16.0
        cam_z = car_z - forward_z * 16.0

        gluLookAt(cam_x, 6.0, cam_z,
                  car_x, 1.5, car_z,
                  0, 1, 0)
    else:
        # 1st Person Cockpit View (FIXED)
        rad = math.radians(car_angle)
        forward_x = -math.sin(rad)
        forward_z = -math.cos(rad)

        # Look target points 20 units straight out of the car's windshield
        look_target_x = car_x + forward_x * 20.0
        look_target_z = car_z + forward_z * 20.0

        gluLookAt(car_x, 2.2, car_z,
                  look_target_x, 2.0, look_target_z,
                  0, 1, 0)

    ci, cj = stream_world(car_x, car_z)
    update_sky()
    draw_ground(car_x, car_z)
    draw_footpaths(ci, cj)
    draw_roads(ci, cj)
    draw_world(ci, cj)
    draw_rain()

    # Draw 3D Car Model facing forward (-Z)

    draw_3d_car(car_x, car_z, car_angle)

    # In 1st Person View, render simulator car dashboard overlay
    if camera_mode == "1st":
        draw_dashboard()

    if game_state == "PAUSED":
        draw_pause_overlay()
    glutSwapBuffers()



# keyboard & special input handlers

def keyboard_down(key, x, y):
    global key_states, game_state, camera_mode
    if key == b'\x1b':  # ESC
        game_state = "PAUSED" if game_state == "PLAYING" else "PLAYING"
        glutPostRedisplay()
        return

    if game_state != "PLAYING":
        return  # ignore movement/other keys while paused

    k = key.decode('utf-8').lower() if isinstance(key, bytes) else key.lower()
    if k == 'v':
        camera_mode = "1st" if camera_mode == "3rd" else "3rd"
        glutPostRedisplay()
        return

    if k in key_states:
        key_states[k] = True


def keyboard_up(key, x, y):
    global key_states
    k = key.decode('utf-8').lower() if isinstance(key, bytes) else key.lower()
    if k in key_states:
        key_states[k] = False


def special_down(key, x, y):
    global key_states, game_state
    if game_state != "PLAYING":
        return
    if key == GLUT_KEY_UP:
        key_states['up'] = True
    elif key == GLUT_KEY_DOWN:
        key_states['down'] = True
    elif key == GLUT_KEY_LEFT:
        key_states['left'] = True
    elif key == GLUT_KEY_RIGHT:
        key_states['right'] = True


def special_up(key, x, y):
    global key_states
    if key == GLUT_KEY_UP:
        key_states['up'] = False
    elif key == GLUT_KEY_DOWN:
        key_states['down'] = False
    elif key == GLUT_KEY_LEFT:
        key_states['left'] = False
    elif key == GLUT_KEY_RIGHT:
        key_states['right'] = False


def update_vehicle_physics():
    global car_x, car_z, cam_x, cam_z, car_speed, last_frame_time, current_rpm, steering_wheel_angle,car_angle,car_tilt

    current_time = time.time()
    dt = current_time - last_frame_time
    last_frame_time = current_time

    # Cap delta time to avoid physics jumps
    dt = min(dt, 0.1)

    throttle = key_states['w'] or key_states['up']
    brake_reverse = key_states['s'] or key_states['down']
    steer_l = key_states['a'] or key_states['left']
    steer_r = key_states['d'] or key_states['right']

    #  Dynamic Rain Surface Physics Scaling
    if is_raining:
        effective_accel = acceleration * WET_ACCEL_MULT
        effective_decel = deceleration * WET_FRICTION_MULT  # Low friction = slides longer
        effective_turn_rate = 90.0 * WET_STEER_MULT  # Sluggish turning response
    else:
        effective_accel = acceleration
        effective_decel = deceleration
        effective_turn_rate = 90.0

    # 1. Acceleration & Braking / Reverse
    if throttle:
        car_speed += acceleration * dt
    elif brake_reverse:
        car_speed -= acceleration * dt
    else:
        # Coasting deceleration
        if car_speed > 0:
            car_speed = max(0.0, car_speed - deceleration * dt)
        elif car_speed < 0:
            car_speed = min(0.0, car_speed + deceleration * dt)

    # Clamp top speeds
    car_speed = max(max_reverse_speed, min(max_speed, car_speed))


    # 2. Smooth Arcade Lane Transition (Realistic Car Turning)
    target_steer = 0.0
    steer_input = 0.0

    if steer_l:
        steer_input = 1.0
        target_steer = 1.0
    elif steer_r:
        steer_input = -1.0
        target_steer = -1.0

        # Continuously rotate car_angle as long as A or D is held down
    turn_rate = 90.0  # Degrees per second (increase for faster turns)

    # Only allow turning if the car is moving (realistic driving feel)
    if abs(car_speed) > 0.1:
        # Reverses steering direction when backing up
        dir_factor = 1.0 if car_speed >= 0 else -1.0
        car_angle += steer_input * turn_rate * dt * dir_factor

    # Keep angle bound within 0 to 360 degrees
    car_angle %= 360.0



   #controls steering wheels movement
    steering_wheel_angle = lerp(steering_wheel_angle, target_steer * 90.0, 10.0 * dt)


    # 3. Forward Movement along car's facing direction (car_angle)
    world_speed = car_speed * 0.25
    rad = math.radians(car_angle)

    # Calculate 2D direction vectors based on facing angle
    forward_x = -math.sin(rad)
    forward_z = -math.cos(rad)

    # Move along the calculated directional vectors
    car_x += forward_x * world_speed * dt
    car_z += forward_z * world_speed * dt

    # Keep camera aligned behind the car's dynamic heading
    cam_x = car_x - forward_x * 16.0
    cam_z = car_z - forward_z * 16.0



    # 4. Engine RPM Calculation
    speed_ratio = abs(car_speed) / 300.0
    gear_cycle = (speed_ratio * 4.5) % 1.0
    throttle_boost = 1800.0 if throttle else 0.0
    target_rpm = 900.0 + (gear_cycle * 4200.0) + (speed_ratio * 1500.0) + throttle_boost
    target_rpm = min(8000.0, max(800.0, target_rpm))
    current_rpm = lerp(current_rpm, target_rpm, 8.0 * dt)


def layout_pause_buttons():
    global resume_btn, quit_btn
    cx = WINDOW_WIDTH // 2
    btn_w, btn_h = 220, 60
    gap = 20

    resume_y = WINDOW_HEIGHT // 2 - btn_h // 2
    quit_y   = resume_y + btn_h + gap

    resume_btn = (cx - btn_w // 2, resume_y, cx + btn_w // 2, resume_y + btn_h)
    quit_btn   = (cx - btn_w // 2, quit_y,   cx + btn_w // 2, quit_y + btn_h)

def init():
    glEnable(GL_DEPTH_TEST)

#controls raindrops
    global raindrops
    raindrops = []
    for _ in range(RAIN_COUNT):
        # Spawn drops within a box centered around the starting camera
        x = random.uniform(-100, 100)
        y = random.uniform(0, 50)
        z = random.uniform(-100, 100)
        speed = random.uniform(30.0, 50.0)
        length = random.uniform(1.2, 2.5)
        raindrops.append([x, y, z, speed, length])

    # Enable Alpha Blending for light glows
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # Distance fog configuration (pushed far to horizon so roads remain solid black)
    glEnable(GL_FOG)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_START, 700.0)
    glFogf(GL_FOG_END, 1400.0)

    stream_world(cam_x, cam_z)


def reshape(w, h):
    global WINDOW_WIDTH, WINDOW_HEIGHT
    WINDOW_WIDTH = w
    WINDOW_HEIGHT = h
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
    glutKeyboardFunc(keyboard_down)
    glutKeyboardUpFunc(keyboard_up)
    glutSpecialFunc(special_down)
    glutSpecialUpFunc(special_up)
    glutMouseFunc(mouse)
    glutTimerFunc(16, update_time, 0)
    glutIdleFunc(glutPostRedisplay)
    glutMainLoop()


if __name__ == "__main__":

    main()