# Bullet Frenzy — FPV + Cheat Spin + Camera Lock (V) — TEMPLATE-COMPLIANT
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

# ---------------- Window & Scene ----------------
WINDOW_W, WINDOW_H = 1000, 800
GRID_LENGTH = 600
GRID_SPACING = 60
WALL_HEIGHT = 150

# ---------------- FOV ----------------
TP_FOV = 50.0
FP_FOV = 110.0

# ---------------- Camera ----------------
cam_radius = 950.0
cam_theta_deg = 0.0
cam_height = 550.0
first_person = False

# FPV camera placement (slightly behind so head/shoulder can peek in sometimes)
FP_CAM_AHEAD = -6.0  # negative = a bit behind player origin

# Camera lock for FPV+cheat (toggled by V)
cheat_follow_vision = False
cam_lock_yaw_deg = 0.0

# ---------------- Player ----------------
player_x = 0.0
player_y = 0.0
player_angle_deg = 0.0
PLAYER_SPEED = 12.0
TURN_SPEED = 10.0
PLAYER_RADIUS = 28.0   # third-person collider
FP_HIT_RADIUS = 60.0   # first-person collider (bigger so hits register)

# Geometry heights (sync arms + gun)
GUN_Z = 58.0
GUN_LENGTH = 95.0

# FPV visible arms/gun geometry
FP_ARM_OFF_Y = 22.0
FP_ARM_Z     = 58.0
FP_ARM_LEN   = 50.0
FP_ARM_RAD   = 7.0
FP_HAND_RAD  = 9.0
FP_GUN_LEN   = 60.0
FP_GUN_R_OUT = 10.0
FP_GUN_R_IN  = 7.0

# ---------------- Bullets ----------------
bullets = []
BULLET_SPEED = 5.0
BULLET_SIZE = 12.0
BULLET_MAX_TRAVEL = 2600.0
FIRE_COOLDOWN_TICKS = 6
fire_cooldown = 0

# ---------------- Enemies ----------------
ENEMY_COUNT = 5
enemies = []
ENEMY_BASE_RADIUS = 38.0

# ---------------- Game State ----------------
life = 5
score = 0
bullets_missed = 0
game_over = False

# Cheat behavior
cheat_mode = False
CHEAT_SPIN_SPEED = 1.8   # deg/tick, one direction, slow
CHEAT_AIM_TOL_DEG = 4.0  # only fire when within this yaw tolerance
CHEAT_START_FRACTION = 0.92  # start bullets near barrel end to reduce misses

# --------------- Utility -----------------
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def angle_wrap_deg(a):
    return (a + 180.0) % 360.0 - 180.0

def dist_xy(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def random_spawn_pos_away_from_player():
    r = random.uniform(260.0, GRID_LENGTH - 50.0)
    ang = random.uniform(0, 2 * math.pi)
    ex = player_x + r * math.cos(ang)
    ey = player_y + r * math.sin(ang)
    ex = clamp(ex, -GRID_LENGTH + 40.0, GRID_LENGTH - 40.0)
    ey = clamp(ey, -GRID_LENGTH + 40.0, GRID_LENGTH - 40.0)
    return ex, ey

def spawn_enemy():
    ex, ey = random_spawn_pos_away_from_player()
    return {
        'x': ex, 'y': ey, 'base_r': ENEMY_BASE_RADIUS,
        'phase': random.uniform(0, 2 * math.pi),
        'phase_speed': random.uniform(0.01, 0.02),
        'speed': random.uniform(0.01, 0.02),
    }

def reset_game():
    global player_x, player_y, player_angle_deg, life, score, bullets_missed, game_over
    global bullets, enemies, cheat_mode, fire_cooldown, first_person, cheat_follow_vision
    global cam_radius, cam_theta_deg, cam_height, cam_lock_yaw_deg

    player_x = player_y = 0.0
    player_angle_deg = 0.0
    life, score, bullets_missed = 5, 0, 0
    game_over = False
    cheat_mode = False
    cheat_follow_vision = False
    cam_lock_yaw_deg = 0.0

    fire_cooldown = 0
    bullets = []

    enemies.clear()
    for _ in range(ENEMY_COUNT):
        enemies.append(spawn_enemy())

    first_person = False
    cam_radius, cam_theta_deg, cam_height = 1050.0, 225.0, 620.0

# --------------- Rendering Helpers -----------------
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# --------------- Drawing the World -----------------
def draw_grid_and_walls():
    half = GRID_LENGTH
    tiles = int((2 * GRID_LENGTH) / GRID_SPACING)

    # Floor tiles (white / lavender)
    for i in range(tiles):
        for j in range(tiles):
            x0 = -half + i * GRID_SPACING
            y0 = -half + j * GRID_SPACING
            color = (0.78, 0.62, 0.95) if (i + j) % 2 == 0 else (1.0, 1.0, 1.0)
            glColor3f(*color)
            glBegin(GL_QUADS)
            glVertex3f(x0, y0, 0)
            glVertex3f(x0 + GRID_SPACING, y0, 0)
            glVertex3f(x0 + GRID_SPACING, y0 + GRID_SPACING, 0)
            glVertex3f(x0, y0 + GRID_SPACING, 0)
            glEnd()

    # Walls
    # North
    glColor3f(0.0, 1.0, 1.0)
    glBegin(GL_QUADS)
    glVertex3f(-half, half, 0); glVertex3f(half, half, 0)
    glVertex3f(half, half, WALL_HEIGHT); glVertex3f(-half, half, WALL_HEIGHT)
    glEnd()
    # West
    glColor3f(0.0, 0.0, 1.0)
    glBegin(GL_QUADS)
    glVertex3f(-half, -half, 0); glVertex3f(-half,  half, 0)
    glVertex3f(-half,  half, WALL_HEIGHT); glVertex3f(-half, -half, WALL_HEIGHT)
    glEnd()
    # South
    glColor3f(0.0, 1.0, 0.0)
    glBegin(GL_QUADS)
    glVertex3f(-half, -half, 0); glVertex3f( half, -half, 0)
    glVertex3f( half, -half, WALL_HEIGHT); glVertex3f(-half, -half, WALL_HEIGHT)
    glEnd()
    # East
    glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_QUADS)
    glVertex3f(half, -half, 0); glVertex3f(half,  half, 0)
    glVertex3f(half,  half, WALL_HEIGHT); glVertex3f(half, -half, WALL_HEIGHT)
    glEnd()

# ---------------- Player (3rd person only) ----------------
def draw_player():
    if first_person:
        return

    glPushMatrix()
    glTranslatef(player_x, player_y, 0.0)

    if game_over:
        glRotatef(90.0, 0.0, 1.0, 0.0)
        glTranslatef(0, 0, 25)

    glRotatef(player_angle_deg, 0.0, 0.0, 1.0)
    quad = gluNewQuadric()

    # Torso (olive cuboid)
    glColor3f(0.36, 0.46, 0.27)
    glPushMatrix()
    glTranslatef(0, 0, 46)
    glScalef(35, 25, 45)
    glutSolidCube(1)
    glPopMatrix()

    # Head (GLU sphere, template-style)
    glColor3f(0, 0, 0)
    glPushMatrix()
    glTranslatef(0, 0, 80)
    gluSphere(quad, 15, 20, 20)
    glPopMatrix()

    # Arms (cylinders)
    glColor3f(0.96, 0.87, 0.70)
    glPushMatrix()
    glTranslatef(0, -18, 58); glRotatef(90, 0, 1, 0); gluCylinder(quad, 8, 6, 50, 12, 4); glPopMatrix()
    glPushMatrix()
    glTranslatef(0,  18, 58); glRotatef(90, 0, 1, 0); gluCylinder(quad, 8, 6, 50, 12, 4); glPopMatrix()

    # Hollow gun (tube)
    glPushMatrix()
    glTranslatef(20, 0, 58); glRotatef(90, 0, 1, 0)
    glColor3f(0.15, 0.15, 0.15); gluCylinder(quad, 6, 6, 60, 24, 1)  # inner
    glColor3f(0.70, 0.70, 0.70); gluCylinder(quad, 8, 8, 60, 24, 1)  # outer
    glPopMatrix()

    # Legs (inverted taper)
    glColor3f(0.0, 0.0, 0.8)
    glPushMatrix(); glTranslatef(0, -9, 0); gluCylinder(quad, 2, 8, 35, 12, 4); glPopMatrix()
    glPushMatrix(); glTranslatef(0,  9, 0); gluCylinder(quad, 2, 8, 35, 12, 4); glPopMatrix()

    glPopMatrix()

# ---------------- FPV: visible arms + hollow gun ----------------
def draw_player_fpv_parts():
    glPushMatrix()
    glTranslatef(player_x, player_y, 0.0)
    glRotatef(player_angle_deg, 0.0, 0.0, 1.0)

    quad = gluNewQuadric()

    # small torso pad
    glColor3f(0.36, 0.46, 0.27)
    glPushMatrix()
    glTranslatef(-8, 0, FP_ARM_Z - 6)
    glScalef(18, 26, 14)
    glutSolidCube(1)
    glPopMatrix()

    # Left forearm + hand (hand sphere via GLU)
    glColor3f(0.96, 0.87, 0.70)
    glPushMatrix()
    glTranslatef(0, -FP_ARM_OFF_Y, FP_ARM_Z)
    glRotatef(90, 0, 1, 0)
    gluCylinder(quad, FP_ARM_RAD, FP_ARM_RAD, FP_ARM_LEN, 16, 2)
    glTranslatef(FP_ARM_LEN, 0, 0)
    gluSphere(quad, FP_HAND_RAD, 16, 12)
    glPopMatrix()

    # Right forearm + hand (hand sphere via GLU)
    glColor3f(0.96, 0.87, 0.70)
    glPushMatrix()
    glTranslatef(0,  FP_ARM_OFF_Y, FP_ARM_Z)
    glRotatef(90, 0, 1, 0)
    gluCylinder(quad, FP_ARM_RAD, FP_ARM_RAD, FP_ARM_LEN, 16, 2)
    glTranslatef(FP_ARM_LEN, 0, 0)
    gluSphere(quad, FP_HAND_RAD, 16, 12)
    glPopMatrix()

    # Hollow gun barrel (tube)
    glPushMatrix()
    glTranslatef(0, 0, FP_ARM_Z)
    glRotatef(90, 0, 1, 0)
    glColor3f(0.15, 0.15, 0.15); gluCylinder(quad, FP_GUN_R_IN, FP_GUN_R_IN, FP_GUN_LEN, 24, 1)
    glColor3f(0.70, 0.70, 0.70); gluCylinder(quad, FP_GUN_R_OUT, FP_GUN_R_OUT, FP_GUN_LEN, 24, 1)
    glPopMatrix()

    glPopMatrix()

# --------------- Camera -----------------
def setupCamera():
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(FP_FOV if first_person else TP_FOV,
                   WINDOW_W / float(WINDOW_H), 1.0, 4000.0)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()

    if first_person:
        # base direction is player_angle
        player_ang = math.radians(player_angle_deg)
        cam_x = player_x + math.cos(player_ang) * FP_CAM_AHEAD
        cam_y = player_y + math.sin(player_ang) * FP_CAM_AHEAD
        cam_z = GUN_Z + 30.0

        if cheat_mode and cheat_follow_vision:
            lock_ang = math.radians(cam_lock_yaw_deg)
            look_x = cam_x + math.cos(lock_ang) * 100.0
            look_y = cam_y + math.sin(lock_ang) * 100.0
        else:
            look_x = cam_x + math.cos(player_ang) * 100.0
            look_y = cam_y + math.sin(player_ang) * 100.0

        gluLookAt(cam_x, cam_y, cam_z, look_x, look_y, cam_z, 0, 0, 1)
    else:
        ang = math.radians(cam_theta_deg)
        cam_x = cam_radius * math.cos(ang)
        cam_y = cam_radius * math.sin(ang)
        cam_z = cam_height
        gluLookAt(cam_x, cam_y, cam_z, 0, 0, 0, 0, 0, 1)

# --------------- Input -----------------
def keyboardListener(key, x, y):
    global player_angle_deg, player_x, player_y, cheat_mode, cheat_follow_vision, cam_lock_yaw_deg
    if game_over and key != b'r': return

    if key == b'a':
        player_angle_deg += TURN_SPEED
    elif key == b'd':
        player_angle_deg -= TURN_SPEED
    elif key == b'c':
        cheat_mode = not cheat_mode
        if not cheat_mode:
            cheat_follow_vision = False
    elif key == b'v':
        # Lock camera only in FPV + cheat
        if first_person and cheat_mode:
            cheat_follow_vision = not cheat_follow_vision
            if cheat_follow_vision:
                cam_lock_yaw_deg = player_angle_deg
        else:
            cheat_follow_vision = False
    elif key == b'r':
        reset_game()
    else:
        ang = math.radians(player_angle_deg)
        move_x = move_y = 0
        if key == b'w':
            move_x += math.cos(ang) * PLAYER_SPEED
            move_y += math.sin(ang) * PLAYER_SPEED
        elif key == b's':
            move_x -= math.cos(ang) * PLAYER_SPEED
            move_y -= math.sin(ang) * PLAYER_SPEED
        player_x = clamp(player_x + move_x, -GRID_LENGTH + 35.0, GRID_LENGTH - 35.0)
        player_y = clamp(player_y + move_y, -GRID_LENGTH + 35.0, GRID_LENGTH - 35.0)

def specialKeyListener(key, x, y):
    global cam_theta_deg, cam_height
    if key == GLUT_KEY_LEFT:   cam_theta_deg -= 4.0
    elif key == GLUT_KEY_RIGHT: cam_theta_deg += 4.0
    elif key == GLUT_KEY_UP:     cam_height = clamp(cam_height + 15.0, 320.0, 800.0)
    elif key == GLUT_KEY_DOWN:   cam_height = clamp(cam_height - 15.0, 320.0, 800.0)

def mouseListener(button, state, x, y):
    global first_person, cheat_follow_vision
    if state == GLUT_DOWN:
        if button == GLUT_LEFT_BUTTON and not game_over:
            fire_bullet()
        elif button == GLUT_RIGHT_BUTTON:
            first_person = not first_person
            if not first_person:
                cheat_follow_vision = False

# --------------- Game Logic -----------------
def fire_bullet():
    global fire_cooldown
    if fire_cooldown > 0: return

    ang = math.radians(player_angle_deg)
    fwdx, fwdy = math.cos(ang), math.sin(ang)

    if first_person:
        # start near the visible barrel end to reduce misses at close range
        start_x = player_x + fwdx * (GUN_LENGTH * CHEAT_START_FRACTION)
        start_y = player_y + fwdy * (GUN_LENGTH * CHEAT_START_FRACTION)
        start_z = GUN_Z
    else:
        start_x = player_x + fwdx * (30.0 + GUN_LENGTH)
        start_y = player_y + fwdy * (30.0 + GUN_LENGTH)
        start_z = GUN_Z

    bullets.append({'x': start_x, 'y': start_y, 'z': start_z,
                    'dx': fwdx, 'dy': fwdy, 'dist': 0.0})
    fire_cooldown = FIRE_COOLDOWN_TICKS
    print("Player Bullet Fired!")

def enemy_current_radius(e):
    return e['base_r'] * (0.8 + 0.2 * math.sin(e['phase']))

def update_state():
    global fire_cooldown, life, game_over, score, bullets_missed, player_angle_deg, first_person
    if game_over: return

    if fire_cooldown > 0: fire_cooldown -= 1

    # Enemies move toward player
    for i, e in enumerate(enemies):
        e['phase'] += e['phase_speed']
        dx, dy = player_x - e['x'], player_y - e['y']
        d = math.hypot(dx, dy) + 1e-6
        e['x'] += e['speed'] * (dx / d)
        e['y'] += e['speed'] * (dy / d)
        player_hit_r = FP_HIT_RADIUS if first_person else PLAYER_RADIUS
        if dist_xy(e['x'], e['y'], player_x, player_y) < (enemy_current_radius(e) + player_hit_r):
            life -= 1
            print(f"Remaining Player Life: {life}")
            enemies[i] = spawn_enemy()
            if life <= 0:
                game_over = True
                first_person = False
                glutPostRedisplay()
                return

    # Bullets update & collisions
    rm = []
    for i, b in enumerate(bullets):
        b['x'] += b['dx'] * BULLET_SPEED
        b['y'] += b['dy'] * BULLET_SPEED
        b['dist'] += BULLET_SPEED
        if b['dist'] > BULLET_MAX_TRAVEL:
            rm.append(i); bullets_missed += 1; print(f"Bullet missed: {bullets_missed}"); continue
        for ei, e in enumerate(enemies):
            if dist_xy(b['x'], b['y'], e['x'], e['y']) < (enemy_current_radius(e) + BULLET_SIZE * 0.6):
                rm.append(i); score += 1; enemies[ei] = spawn_enemy(); break
    for i in sorted(set(rm), reverse=True): bullets.pop(i)

    if bullets_missed >= 10:
        game_over = True
        first_person = False
        glutPostRedisplay()
        return

    # Cheat: slow, one-direction spin, auto-fire only when aligned
    if cheat_mode:
        player_angle_deg -= CHEAT_SPIN_SPEED  # always same direction
        # find nearest enemy
        nearest, ndmin = None, float('inf')
        for e in enemies:
            d = dist_xy(player_x, player_y, e['x'], e['y'])
            if d < ndmin: ndmin, nearest = d, e
        if nearest:
            ang_to_enemy = math.degrees(math.atan2(nearest['y'] - player_y, nearest['x'] - player_x))
            yaw_err = abs(angle_wrap_deg(ang_to_enemy - player_angle_deg))
            if yaw_err < CHEAT_AIM_TOL_DEG:
                fire_bullet()

    glutPostRedisplay()

# --------------- Bullets & Enemies draw -----------------
def draw_bullets():
    glColor3f(1.0, 0.0, 0.0)
    for b in bullets:
        glPushMatrix(); glTranslatef(b['x'], b['y'], b['z']); glutSolidCube(BULLET_SIZE); glPopMatrix()

def draw_enemy(e):
    scale = 0.8 + 0.2 * math.sin(e['phase'])
    glPushMatrix()
    glTranslatef(e['x'], e['y'], e['base_r'] * scale)
    glScalef(scale, scale, scale)

    quad = gluNewQuadric()
    glColor3f(1.0, 0.0, 0.0)
    gluSphere(quad, e['base_r'], 20, 20)

    glColor3f(0.0, 0.0, 0.0)
    glPushMatrix()
    glTranslatef(0, 0, e['base_r'] * 1.4)
    gluSphere(quad, e['base_r'] * 0.5, 10, 10)
    glPopMatrix()

    glPopMatrix()

# --------------- Main Display -----------------
def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    setupCamera()

    draw_grid_and_walls()
    for e in enemies: draw_enemy(e)
    draw_player()
    draw_bullets()

    if first_person:
        draw_player_fpv_parts()

    # Game Over message (centered)
    if game_over:
        draw_text(10, WINDOW_H - 30, f"Game is Over. Your Score is {score}.")
        draw_text(10, WINDOW_H - 55, 'Press "R" to RESTART the Game.')
        print(f"Game is Over. Your Score is {score}.")
        print('Press "R" to RESTART the Game.')
    else:
        draw_text(10, WINDOW_H - 30, f"Player Life Remaining: {life}")
        draw_text(10, WINDOW_H - 55, f"Game Score: {score}")
        draw_text(10, WINDOW_H - 80, f"Player Bullets Missed: {bullets_missed}")

    glutSwapBuffers()

# --------------- Main -----------------
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"Bullet Frenzy - A 3D Game with Player Movement, Shooting, & Cheat Modes")

    reset_game()

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(update_state)

    glutMainLoop()

if __name__ == "__main__":
    main()
