from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random, math,time

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
time_of_day = 0.0  # what daytime is now? morning/noon/day
ambient_light = 1.0  # change of environment color according to day time

# ---------------- camera ----------------
cam_x, cam_z = 0.0, 15.0     # camera position
cam_angle = 0.0              # left/right turn angle in degrees

# ---------------- Rain System ----------------
RAIN_COUNT = 1000 #number of raindrops stored
raindrops = []
is_raining = False
last_rain_toggle = time.time() #duration between each rain

car_speed = 0.0
max_speed = 40.0         # Top forward speed (units/sec)
max_reverse_speed = -15.0 # Top reverse speed (units/sec)
acceleration = 30.0      # How fast speed builds up (units/sec^2)
deceleration = 10.0      # Coasting friction when no key is held
steering_speed = 50.0    # Turn rate (degrees/sec)

INTERSECTION_INTERVAL = 4  # Road intersections every 4 blocks

# Input tracking
key_states = {'w': False, 's': False, 'a': False, 'd': False} #keeps track of which movement buttons are being pressed
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
PRUNE_MARGIN = VIEW_RADIUS + 2    # cached blocks further than this get dropped

# cache of generated blocks: {(bi, bj): {"trees": [...], "buildings": [...], "lamps": [...]}}
block_cache = {}

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
    global time_of_day

    time_of_day += 0.0005

    if time_of_day >= 1.0:
        time_of_day = 0.0

    glutPostRedisplay()
    glutTimerFunc(16, update_time, 0)



# ---------------- ground / road / footpaths ----------------

def draw_ground(cx, cz):
    size = CELL_SIZE * (VIEW_RADIUS + 3)
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
    lo = -(VIEW_RADIUS + 1) * CELL_SIZE
    hi = (VIEW_RADIUS + 1) * CELL_SIZE

    set_env_color(0.45, 0.45, 0.45)

    for i in range(ci - VIEW_RADIUS - 1, ci + VIEW_RADIUS + 2):
        if i % INTERSECTION_INTERVAL == 0:
            x = i * CELL_SIZE
            glBegin(GL_QUADS)
            glVertex3f(x - half, 0.015, cj * CELL_SIZE + hi)
            glVertex3f(x + half, 0.015, cj * CELL_SIZE + hi)
            glVertex3f(x + half, 0.015, cj * CELL_SIZE + lo)
            glVertex3f(x - half, 0.015, cj * CELL_SIZE + lo)
            glEnd()
    for j in range(cj - VIEW_RADIUS - 1, cj + VIEW_RADIUS + 2):
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
    lo = -(VIEW_RADIUS + 1) * CELL_SIZE
    hi = (VIEW_RADIUS + 1) * CELL_SIZE

    # asphalt strips: every road running north-south (varying x) and
    # every road running east-west (varying z) -- together they form a
    # full grid of 4-way intersections, i.e. turns everywhere you look.
    set_env_color(0.15, 0.15, 0.15)
    for i in range(ci - VIEW_RADIUS - 1, ci + VIEW_RADIUS + 2):
        if i % INTERSECTION_INTERVAL == 0:
            x = i * CELL_SIZE
            glBegin(GL_QUADS)
            glVertex3f(x - half, 0.02, cj * CELL_SIZE + hi)
            glVertex3f(x + half, 0.02, cj * CELL_SIZE + hi)
            glVertex3f(x + half, 0.02, cj * CELL_SIZE + lo)
            glVertex3f(x - half, 0.02, cj * CELL_SIZE + lo)
            glEnd()
    for j in range(cj - VIEW_RADIUS - 1, cj + VIEW_RADIUS + 2):
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


def draw_lane_markings(ci, cj):
    dash_len, gap_len = 2.0, 2.0
    step = dash_len + gap_len
    lo = -(VIEW_RADIUS + 1) * CELL_SIZE
    hi = (VIEW_RADIUS + 1) * CELL_SIZE

    # dashed centre line along every north-south road
    glColor3f(1.0, 1.0, 1.0)
    for i in range(ci - VIEW_RADIUS - 1, ci + VIEW_RADIUS + 2):
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
    for j in range(cj - VIEW_RADIUS - 1, cj + VIEW_RADIUS + 2):
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
    for i in range(ci - VIEW_RADIUS - 1, ci + VIEW_RADIUS + 2):
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
        "20",
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
        "20",
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
    for i in range(ci - VIEW_RADIUS, ci + VIEW_RADIUS + 1):
        if i % INTERSECTION_INTERVAL != 0:
            continue
        for j in range(cj - VIEW_RADIUS, cj + VIEW_RADIUS + 1):
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
# ---------------- render loop ----------------


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # Pass delta time to vehicle and rain updates
    current_time = time.time()
    dt = min(current_time - last_frame_time, 0.1)

    update_vehicle_physics()
    update_rain(dt)  # Updates rain timer & particle movement

    look_x = cam_x + math.sin(math.radians(cam_angle)) * 10
    look_z = cam_z - math.cos(math.radians(cam_angle)) * 10
    gluLookAt(cam_x, 3.5, cam_z,
              look_x, 2.0, look_z,
              0, 1, 0)

    ci, cj = stream_world(cam_x, cam_z)
    update_sky()
    draw_ground(cam_x, cam_z)
    draw_footpaths(ci, cj)
    draw_roads(ci, cj)
    draw_world(ci, cj)
    draw_rain()

    glutSwapBuffers()


# ---------------- updated keyboard handlers ----------------

def keyboard_down(key, x, y):
    global key_states
    k = key.decode('utf-8').lower() if isinstance(key, bytes) else key.lower()
    if k in key_states:
        key_states[k] = True
    elif key == b'\x1b':  # ESC
        glutLeaveMainLoop()


def keyboard_up(key, x, y):
    global key_states
    k = key.decode('utf-8').lower() if isinstance(key, bytes) else key.lower()
    if k in key_states:
        key_states[k] = False

# ---------------- smooth physics update ----------------

def update_vehicle_physics():
    global cam_x, cam_z, cam_angle, car_speed, last_frame_time

    current_time = time.time()
    dt = current_time - last_frame_time
    last_frame_time = current_time

    # Cap delta time to avoid physics jumps on high latency frame drops
    dt = min(dt, 0.1)

    # 1. Acceleration & Braking / Reverse
    if key_states['w']:
        car_speed += acceleration * dt
    elif key_states['s']:
        car_speed -= acceleration * dt
    else:
        # Natural coasting deceleration when no drive keys are pressed
        if car_speed > 0:
            car_speed = max(0.0, car_speed - deceleration * dt)
        elif car_speed < 0:
            car_speed = min(0.0, car_speed + deceleration * dt)

    # Clamp top speeds
    car_speed = max(max_reverse_speed, min(max_speed, car_speed))

    # 2. Steering (Only turns when the vehicle is actively moving)
    if abs(car_speed) > 0.1:
        # Reverse steering direction when reversing
        dir_factor = 1.0 if car_speed >= 0 else -1.0

        if key_states['a']:
            cam_angle -= steering_speed * dt * dir_factor
        if key_states['d']:
            cam_angle += steering_speed * dt * dir_factor

    # 3. Position Translation
    rad = math.radians(cam_angle)
    cam_x += math.sin(rad) * car_speed * dt
    cam_z -= math.cos(rad) * car_speed * dt


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

    # Distance fog configuration
    glEnable(GL_FOG)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_START, CELL_SIZE * (VIEW_RADIUS - 1))
    glFogf(GL_FOG_END, CELL_SIZE * (VIEW_RADIUS + 0.8))

    stream_world(cam_x, cam_z)


def reshape(w, h):
    global WINDOW_WIDTH, WINDOW_HEIGHT
    WINDOW_WIDTH = w
    WINDOW_HEIGHT = h
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, float(w) / float(h if h else 1), 0.1, 500.0)
    glMatrixMode(GL_MODELVIEW)
    glutPostRedisplay()


def main():
    glutInit()

    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"ROAD STRIKE")

    glEnable(GL_DEPTH_TEST)
    init()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard_down)
    glutKeyboardUpFunc(keyboard_up)
    glutTimerFunc(16, update_time, 0)
    glutIdleFunc(glutPostRedisplay)
    glutMainLoop()


if __name__ == "__main__":

    main()