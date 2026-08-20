from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random, math

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800

# ---------------- camera ----------------
cam_x, cam_z = 0.0, 15.0     # camera position (free-roam, GTA style)
cam_angle = 0.0              # left/right turn angle in degrees
move_speed = 0.6

# ---------------- world / road-grid data ----------------
# Instead of one straight road, the city is an infinite grid of streets
# (like Manhattan blocks). Every intersection is a 4-way turn, and the
# grid streams in every direction forever as the car drives around.
ROAD_WIDTH = 20.0
FOOTPATH_WIDTH = 4.0
CELL_SIZE = 100.0                 # distance between two road centerlines
BLOCK_MARGIN = ROAD_WIDTH / 2.0 + FOOTPATH_WIDTH   # gap before buildable land starts

VIEW_RADIUS = 3                   # how many blocks out (in every direction) get streamed in
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
    (0.50, 0.55, 0.60),
]


# ---------------- infinite block streaming ----------------

def camera_block(cx, cz):
    return int(math.floor(cx / CELL_SIZE)), int(math.floor(cz / CELL_SIZE))


def generate_block(bi, bj):
    """Deterministically build the contents of a single city block.
    Same (bi, bj) always produces the same block, so the world is stable
    even though it is generated on the fly, chunk by chunk."""

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

    cols = max(1, int(area_w / 13))
    rows = max(1, int(area_d / 13))
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
            # remaining chance -> empty grassy lot / small park, adds visual variety

    # lamp posts along the four footpath edges of the block
    fx0 = bi * CELL_SIZE + ROAD_WIDTH / 2.0 + FOOTPATH_WIDTH / 2.0
    fx1 = (bi + 1) * CELL_SIZE - ROAD_WIDTH / 2.0 - FOOTPATH_WIDTH / 2.0
    fz0 = bj * CELL_SIZE + ROAD_WIDTH / 2.0 + FOOTPATH_WIDTH / 2.0
    fz1 = (bj + 1) * CELL_SIZE - ROAD_WIDTH / 2.0 - FOOTPATH_WIDTH / 2.0
    lamps = [(fx0, fz0), (fx1, fz0), (fx0, fz1), (fx1, fz1),
             ((fx0 + fx1) / 2.0, fz0), ((fx0 + fx1) / 2.0, fz1)]

    return {"trees": trees, "buildings": buildings, "lamps": lamps}


def stream_world(cx, cz):
    """Make sure every block within VIEW_RADIUS of the camera exists,
    and forget blocks that are far behind us (classic open-world streaming)."""

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


# ---------------- ground / road / footpaths ----------------

def draw_ground(cx, cz):
    size = CELL_SIZE * (VIEW_RADIUS + 3)
    glColor3f(0.30, 0.55, 0.25)  # grass green
    glBegin(GL_QUADS)
    glVertex3f(cx - size, 0, cz + size)
    glVertex3f(cx + size, 0, cz + size)
    glVertex3f(cx + size, 0, cz - size)
    glVertex3f(cx - size, 0, cz - size)
    glEnd()


def draw_footpaths(ci, cj):
    half = ROAD_WIDTH / 2.0 + FOOTPATH_WIDTH
    lo = -(VIEW_RADIUS + 1) * CELL_SIZE
    hi = (VIEW_RADIUS + 1) * CELL_SIZE

    glColor3f(0.45, 0.45, 0.45)
    for i in range(ci - VIEW_RADIUS - 1, ci + VIEW_RADIUS + 2):
        x = i * CELL_SIZE
        glBegin(GL_QUADS)
        glVertex3f(x - half, 0.015, cj * CELL_SIZE + hi)
        glVertex3f(x + half, 0.015, cj * CELL_SIZE + hi)
        glVertex3f(x + half, 0.015, cj * CELL_SIZE + lo)
        glVertex3f(x - half, 0.015, cj * CELL_SIZE + lo)
        glEnd()
    for j in range(cj - VIEW_RADIUS - 1, cj + VIEW_RADIUS + 2):
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
    glColor3f(0.15, 0.15, 0.15)
    for i in range(ci - VIEW_RADIUS - 1, ci + VIEW_RADIUS + 2):
        x = i * CELL_SIZE
        glBegin(GL_QUADS)
        glVertex3f(x - half, 0.02, cj * CELL_SIZE + hi)
        glVertex3f(x + half, 0.02, cj * CELL_SIZE + hi)
        glVertex3f(x + half, 0.02, cj * CELL_SIZE + lo)
        glVertex3f(x - half, 0.02, cj * CELL_SIZE + lo)
        glEnd()
    for j in range(cj - VIEW_RADIUS - 1, cj + VIEW_RADIUS + 2):
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
        x = i * CELL_SIZE
        for side in (-1, 1):
            ex = x + side * half
            glBegin(GL_QUADS)
            glVertex3f(ex - 0.1, 0.022, cj * CELL_SIZE + hi)
            glVertex3f(ex + 0.1, 0.022, cj * CELL_SIZE + hi)
            glVertex3f(ex + 0.1, 0.022, cj * CELL_SIZE + lo)
            glVertex3f(ex - 0.1, 0.022, cj * CELL_SIZE + lo)
            glEnd()


def draw_intersections(ci, cj):
    """Zebra crossings + stop lines on every approach of every visible
    intersection -- this is where the 'four turns' happen (straight,
    left, right or a U-turn) at every single junction in the grid."""

    stripe_w, stripe_len, gap = 0.6, ROAD_WIDTH - 2.0, 0.6
    inset = ROAD_WIDTH / 2.0 + 0.6

    glColor3f(0.95, 0.95, 0.9)
    for i in range(ci - VIEW_RADIUS, ci + VIEW_RADIUS + 1):
        for j in range(cj - VIEW_RADIUS, cj + VIEW_RADIUS + 1):
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


# ---------------- scenery ----------------

def draw_tree(x, z, height, kind):
    glPushMatrix()
    glTranslatef(x, 0, z)

    glColor3f(0.45, 0.28, 0.13)
    quad = gluNewQuadric()
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quad, 0.5, 0.4, height * 0.5, 8, 1)
    glPopMatrix()

    if kind == 'pine':
        glColor3f(0.08, 0.4, 0.18)
        for i, scale in enumerate((1.0, 0.7, 0.42)):
            glPushMatrix()
            glTranslatef(0, height * 0.5 + i * height * 0.28, 0)
            glRotatef(-90, 1, 0, 0)
            gluCylinder(quad, height * 0.32 * scale, 0.0, height * 0.4, 10, 1)
            glPopMatrix()
    else:
        glColor3f(0.1, 0.5, 0.15)
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
    hw, hd = w / 2.0, d / 2.0

    glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex3f(-hw, 0, hd); glVertex3f(hw, 0, hd); glVertex3f(hw, h, hd); glVertex3f(-hw, h, hd)
    glVertex3f(hw, 0, -hd); glVertex3f(-hw, 0, -hd); glVertex3f(-hw, h, -hd); glVertex3f(hw, h, -hd)
    glVertex3f(-hw, 0, -hd); glVertex3f(-hw, 0, hd); glVertex3f(-hw, h, hd); glVertex3f(-hw, h, -hd)
    glVertex3f(hw, 0, hd); glVertex3f(hw, 0, -hd); glVertex3f(hw, h, -hd); glVertex3f(hw, h, hd)
    glEnd()

    roof_color = tuple(min(1.0, c * 0.75) for c in color)
    glColor3f(*roof_color)
    glBegin(GL_QUADS)
    glVertex3f(-hw, h, -hd); glVertex3f(hw, h, -hd); glVertex3f(hw, h, hd); glVertex3f(-hw, h, hd)
    glEnd()

    draw_windows(hw, hd, h, win_seed)
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


def draw_world(ci, cj):
    for bi in range(ci - VIEW_RADIUS, ci + VIEW_RADIUS + 1):
        for bj in range(cj - VIEW_RADIUS, cj + VIEW_RADIUS + 1):
            block = block_cache.get((bi, bj))
            if not block:
                continue
            for (x, z, height, kind) in block["trees"]:
                draw_tree(x, z, height, kind)
            for (x, z, w, d, h, color, win_seed) in block["buildings"]:
                draw_building(x, z, w, d, h, color, win_seed)
            for (x, z) in block["lamps"]:
                draw_lamp(x, z)


# ---------------- render loop ----------------

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    look_x = cam_x + math.sin(math.radians(cam_angle)) * 10
    look_z = cam_z - math.cos(math.radians(cam_angle)) * 10
    gluLookAt(cam_x, 3.5, cam_z,
              look_x, 2.0, look_z,
              0, 1, 0)

    ci, cj = stream_world(cam_x, cam_z)

    draw_ground(cam_x, cam_z)
    draw_footpaths(ci, cj)
    draw_roads(ci, cj)
    draw_world(ci, cj)

    glutSwapBuffers()


def keyboard(key, x, y):
    global cam_x, cam_z, cam_angle
    rad = math.radians(cam_angle)
    if key == b'w':          # drive forward
        cam_x += math.sin(rad) * move_speed
        cam_z -= math.cos(rad) * move_speed
    elif key == b's':        # reverse
        cam_x -= math.sin(rad) * move_speed
        cam_z += math.cos(rad) * move_speed
    elif key == b'a':        # turn left
        cam_angle -= 3
    elif key == b'd':        # turn right
        cam_angle += 3
    elif key == b'\x1b':     # ESC to quit
        glutLeaveMainLoop()
    glutPostRedisplay()


def init():
    glEnable(GL_DEPTH_TEST)
    sky = (0.53, 0.81, 0.92, 1.0)
    glClearColor(*sky)

    # distance fog hides the streaming edge and sells the "endless city" feel
    glEnable(GL_FOG)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogfv(GL_FOG_COLOR, sky)
    glFogf(GL_FOG_START, CELL_SIZE * (VIEW_RADIUS - 1.5))
    glFogf(GL_FOG_END, CELL_SIZE * (VIEW_RADIUS + 1))

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
    glutKeyboardFunc(keyboard)
    glutIdleFunc(glutPostRedisplay)
    glutMainLoop()


if __name__ == "__main__":
    main()