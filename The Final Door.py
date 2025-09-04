from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
from collections import deque
import sys

# ----------------- Maze Generation Classes -----------------
class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.walls = {'N': True, 'S': True, 'E': True, 'W': True}
        self.visited = False
        self.wall_colors = {}

class Maze:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[Cell(x, y) for y in range(height)] for x in range(width)]
        self.goal = None
        for x in range(width):
            for y in range(height):
                cell = self.grid[x][y]
                cell.wall_colors['N'] = get_smooth_color(x, y, offset=0.1)
                cell.wall_colors['S'] = get_smooth_color(x, y, offset=0.2)
                cell.wall_colors['E'] = get_smooth_color(x, y, offset=0.3)
                cell.wall_colors['W'] = get_smooth_color(x, y, offset=0.4)
        self.generate()

    def get_neighbors(self, cell):
        neighbors = []
        if cell.y > 0 and not self.grid[cell.x][cell.y - 1].visited: neighbors.append(self.grid[cell.x][cell.y - 1])
        if cell.y < self.height - 1 and not self.grid[cell.x][cell.y + 1].visited: neighbors.append(self.grid[cell.x][cell.y + 1])
        if cell.x < self.width - 1 and not self.grid[cell.x + 1][cell.y].visited: neighbors.append(self.grid[cell.x + 1][cell.y])
        if cell.x > 0 and not self.grid[cell.x - 1][cell.y].visited: neighbors.append(self.grid[cell.x - 1][cell.y])
        return neighbors

    def remove_walls(self, current_cell, next_cell):
        dx, dy = current_cell.x - next_cell.x, current_cell.y - next_cell.y
        if dx == 1: current_cell.walls['W'], next_cell.walls['E'] = False, False
        elif dx == -1: current_cell.walls['E'], next_cell.walls['W'] = False, False
        if dy == 1: current_cell.walls['N'], next_cell.walls['S'] = False, False
        elif dy == -1: current_cell.walls['S'], next_cell.walls['N'] = False, False

    def generate(self):
        stack = []
        start_cell = self.grid[random.randint(0, self.width - 1)][random.randint(0, self.height - 1)]
        start_cell.visited = True
        stack.append(start_cell)
        while stack:
            current_cell = stack[-1]
            neighbors = self.get_neighbors(current_cell)
            if neighbors:
                next_cell = random.choice(neighbors)
                next_cell.visited = True
                self.remove_walls(current_cell, next_cell)
                stack.append(next_cell)
            else:
                stack.pop()

    def compute_goal_from_start(self, sx, sy):
        W, H = self.width, self.height
        dist = [[-1] * H for _ in range(W)]
        q = deque([(sx, sy)]); dist[sx][sy] = 0
        while q:
            x, y = q.popleft()
            c = self.grid[x][y]
            if not c.walls['N'] and y > 0 and dist[x][y-1] == -1: dist[x][y-1] = dist[x][y] + 1; q.append((x, y-1))
            if not c.walls['S'] and y < H-1 and dist[x][y+1] == -1: dist[x][y+1] = dist[x][y] + 1; q.append((x, y+1))
            if not c.walls['E'] and x < W-1 and dist[x+1][y] == -1: dist[x+1][y] = dist[x][y] + 1; q.append((x+1, y))
            if not c.walls['W'] and x > 0 and dist[x-1][y] == -1: dist[x-1][y] = dist[x][y] + 1; q.append((x-1, y))
        gx, gy, md = 0, 0, -1
        for i in range(W):
            for j in range(H):
                if dist[i][j] > md: md, gx, gy = dist[i][j], i, j
        self.goal = (gx, gy)
        return gx, gy, md

# ---------------- Window & Scene ----------------
WINDOW_W, WINDOW_H = 1200, 900
game_maze = None
CELL_SIZE = 200
WALL_HEIGHT = 150
WALL_THICKNESS = 10
demo_maze_angle = 0.0

# ---------------- Player ----------------
player_x, player_y = CELL_SIZE / 2, CELL_SIZE / 2
player_angle_deg = 0.0
PLAYER_SPEED = 7.5
TURN_SPEED = 4.0
PLAYER_RADIUS = 15.0

# ---------------- Camera ----------------
first_person = False
cam_radius = 80.0
cam_height = 150.0
current_cam_x, current_cam_y, current_cam_h = 0, 0, 0
current_look_at_x, current_look_at_y = 0, 0
CAMERA_SMOOTH_FACTOR = 0.1
FP_CAM_HEIGHT = 60.0

# ---------------- Game State & Levels ----------------
game_state = "intro_menu" # intro_menu, level_select, playing, level_complete
current_level = 1
MAZE_WIDTH, MAZE_HEIGHT = 12, 12 # Default size for demo maze

LEVEL_SETTINGS = {
    1: {'size': (8, 8),   'name': 'The Dawn Gardens',       'sky_color': (0.6, 0.7, 0.9, 1.0)},
    2: {'size': (12, 12), 'name': 'The Sunstone Labyrinth', 'sky_color': (0.5, 0.7, 1.0, 1.0)},
    3: {'size': (15, 15), 'name': 'The Midnight Maze',      'sky_color': (0.05, 0.05, 0.2, 1.0)}
}

# --------------- Utility & Collision -----------------
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def get_smooth_color(x, y, offset=0):
    r = (math.sin(x * 0.2 + y * 0.1 + offset) + 1) / 2
    g = (math.sin(x * 0.15 + y * 0.25 + offset + 2) + 1) / 2
    return 0.3 + ((r + g) / 2) * 0.4

def check_collision(x, y):
    grid_x, grid_y = int(x / CELL_SIZE), int(y / CELL_SIZE)
    if not (0 <= grid_x < MAZE_WIDTH and 0 <= grid_y < MAZE_HEIGHT): return True
    cell = game_maze.grid[grid_x][grid_y]
    x_in_cell, y_in_cell = x % CELL_SIZE, y % CELL_SIZE
    buffer = 1.0
    if cell.walls['N'] and y_in_cell < WALL_THICKNESS - buffer: return True
    if cell.walls['S'] and y_in_cell > CELL_SIZE - (WALL_THICKNESS - buffer): return True
    if cell.walls['W'] and x_in_cell < WALL_THICKNESS - buffer: return True
    if cell.walls['E'] and x_in_cell > CELL_SIZE - (WALL_THICKNESS - buffer): return True
    return False

# ---------- Game Reset & Level Progression ----------
def start_game(level=1):
    global game_maze, player_x, player_y, player_angle_deg, game_state
    global MAZE_WIDTH, MAZE_HEIGHT, current_level
    global current_cam_x, current_cam_y, current_cam_h, current_look_at_x, current_look_at_y

    current_level = level
    level_settings = LEVEL_SETTINGS[current_level]
    MAZE_WIDTH, MAZE_HEIGHT = level_settings['size']
    
    update_lighting(current_level)
    glClearColor(*level_settings['sky_color'])
    
    game_maze = Maze(MAZE_WIDTH, MAZE_HEIGHT)
    start_x, start_y = random.randint(0, MAZE_WIDTH-1), random.randint(0, MAZE_HEIGHT-1)
    player_x, player_y = start_x * CELL_SIZE + CELL_SIZE / 2, start_y * CELL_SIZE + CELL_SIZE / 2
    player_angle_deg = 0.0
    
    current_cam_x, current_cam_y, current_cam_h = player_x, player_y, cam_height
    current_look_at_x, current_look_at_y = player_x, player_y
    game_state = "playing"

    gx, gy, d = game_maze.compute_goal_from_start(start_x, start_y)
    print(f"--- Starting {level_settings['name']} ---")
    print(f"New maze generated ({MAZE_WIDTH}x{MAZE_HEIGHT}). Start={(start_x,start_y)}, Goal={(gx, gy)}")

def initialize_intro_scene():
    global game_maze
    game_maze = Maze(MAZE_WIDTH, MAZE_HEIGHT)

# --------------- Lighting -----------------
def update_lighting(level):
    if level == 3: # Night level
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        light_pos = [0, 0, 200, 1]
        light_ambient = [0.2, 0.2, 0.3, 1.0]
        light_diffuse = [0.8, 0.8, 0.7, 1.0]
        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
    else: # Day levels
        glDisable(GL_LIGHTING)

# --------------- Drawing (3D Scene) -----------------
def draw_3d_scene():
    draw_ground()
    if game_maze:
        draw_maze()
        if game_state == "playing" or game_state == "level_complete":
            draw_goal()
            draw_player()

def draw_ground():
    glColor3f(0.55, 0.4, 0.25)
    ground_size = 10000
    glBegin(GL_QUADS)
    glVertex3f(-ground_size, -ground_size, -0.1); glVertex3f(ground_size, -ground_size, -0.1)
    glVertex3f(ground_size, ground_size, -0.1); glVertex3f(-ground_size, ground_size, -0.1)
    glEnd()

def draw_wall(x1, y1, x2, y2, green_shade):
    glColor3f(0.1, green_shade, 0.1)
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    length = math.hypot(x2 - x1, y2 - y1)
    glPushMatrix(); glTranslatef(mid_x, mid_y, WALL_HEIGHT / 2)
    if abs(x1 - x2) > abs(y1 - y2): glScalef(length + WALL_THICKNESS, WALL_THICKNESS, WALL_HEIGHT)
    else: glScalef(WALL_THICKNESS, length + WALL_THICKNESS, WALL_HEIGHT)
    glutSolidCube(1); glPopMatrix()

def draw_maze():
    if not game_maze: return
    for x in range(MAZE_WIDTH):
        for y in range(MAZE_HEIGHT):
            cell = game_maze.grid[x][y]
            x_pos, y_pos = x * CELL_SIZE, y * CELL_SIZE
            if cell.walls['N']: draw_wall(x_pos, y_pos, x_pos + CELL_SIZE, y_pos, cell.wall_colors['N'])
            if cell.walls['W']: draw_wall(x_pos, y_pos, x_pos, y_pos + CELL_SIZE, cell.wall_colors['W'])
    for x in range(MAZE_WIDTH):
        color = game_maze.grid[x][MAZE_HEIGHT - 1].wall_colors['S']
        draw_wall(x*CELL_SIZE, MAZE_HEIGHT*CELL_SIZE, (x+1)*CELL_SIZE, MAZE_HEIGHT*CELL_SIZE, color)
    for y in range(MAZE_HEIGHT):
        color = game_maze.grid[MAZE_WIDTH - 1][y].wall_colors['E']
        draw_wall(MAZE_WIDTH*CELL_SIZE, y*CELL_SIZE, MAZE_WIDTH*CELL_SIZE, (y+1)*CELL_SIZE, color)

def draw_player():
    if first_person: return
    glPushMatrix(); glTranslatef(player_x, player_y, PLAYER_RADIUS); glRotatef(player_angle_deg, 0, 0, 1)
    glColor3f(0.9, 0.1, 0.1); glutSolidSphere(PLAYER_RADIUS, 20, 20)
    glColor3f(0.1, 0.9, 0.1); glTranslatef(PLAYER_RADIUS, 0, 0); glutSolidCube(PLAYER_RADIUS/2)
    glPopMatrix()

def draw_goal():
    if not game_maze or not game_maze.goal: return
    gx, gy = game_maze.goal
    cx, cy = gx * CELL_SIZE + CELL_SIZE / 2, gy * CELL_SIZE + CELL_SIZE / 2
    glPushMatrix(); glTranslatef(cx, cy, 0)
    glColor3f(0.95, 0.85, 0.2); glPushMatrix(); glTranslatef(0, 0, 6); glScalef(40, 40, 12); glutSolidCube(1); glPopMatrix()
    glColor3f(0.2, 0.8, 0.2); glPushMatrix(); glTranslatef(-16, 0, 70); glScalef(12, 12, 140); glutSolidCube(1); glPopMatrix()
    glPushMatrix(); glTranslatef(16, 0, 70); glScalef(12, 12, 140); glutSolidCube(1); glPopMatrix()
    glColor3f(0.2, 0.6, 0.9); glPushMatrix(); glTranslatef(0, 0, 140); glScalef(44, 12, 12); glutSolidCube(1); glPopMatrix()
    glPopMatrix()

# --------------- Drawing (2D UI Menus) -----------------
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(font, ord(char))

def draw_ui_overlay(draw_content_func):
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity(); glDisable(GL_DEPTH_TEST)
    
    glEnable(GL_BLEND) # Enable blending for transparency
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.0, 0.6); glBegin(GL_QUADS); glVertex2f(0, 0); glVertex2f(WINDOW_W, 0); glVertex2f(WINDOW_W, WINDOW_H); glVertex2f(0, WINDOW_H); glEnd()
    glDisable(GL_BLEND)

    draw_content_func()
    
    glEnable(GL_DEPTH_TEST); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW); glPopMatrix()

def draw_styled_button(x, y, w, h, text, font=GLUT_BITMAP_HELVETICA_18):
    # Button background with transparency
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.15, 0.15, 0.18, 0.75)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()
    glDisable(GL_BLEND)

    # Button outline
    glColor3f(0.6, 0.7, 0.8)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()
    glLineWidth(1.0)

    # Calculate text width to center it
    text_width = sum(glutBitmapWidth(font, ord(c)) for c in text)
    text_x = x + (w - text_width) / 2
    text_y = y + (h - 18) / 2 + 5 # Adjust for vertical centering
    glColor3f(1.0, 1.0, 1.0)
    draw_text(text_x, text_y, text, font)


def draw_intro_menu():
    def content():
        # --- Title ---
        title_text = "THE FINAL DOOR"
        title_font = GLUT_BITMAP_TIMES_ROMAN_24
        title_width = sum(glutBitmapWidth(title_font, ord(c)) for c in title_text)
        glColor3f(0.95, 0.85, 0.2) # Golden yellow color
        draw_text(WINDOW_W / 2 - title_width / 2, WINDOW_H - 150, title_text, title_font)

        # --- Subtitle ---
        subtitle_text = "An Amazing Maze Adventure"
        subtitle_font = GLUT_BITMAP_HELVETICA_18
        subtitle_width = sum(glutBitmapWidth(subtitle_font, ord(c)) for c in subtitle_text)
        glColor3f(0.8, 0.8, 0.8) # Light grey
        draw_text(WINDOW_W / 2 - subtitle_width / 2, WINDOW_H - 185, subtitle_text, subtitle_font)

        # --- Buttons ---
        btn_y = WINDOW_H / 2 + 30
        btn_w, btn_h = 250, 50
        btn_x = WINDOW_W / 2 - btn_w / 2
        
        draw_styled_button(btn_x, btn_y, btn_w, btn_h, "Play Game")
        draw_styled_button(btn_x, btn_y - 70, btn_w, btn_h, "Select Level")
        draw_styled_button(btn_x, btn_y - 140, btn_w, btn_h, "Quit")

    draw_ui_overlay(content)

def draw_level_select_menu():
    def content():
        glColor3f(1.0, 0.9, 0.2); draw_text(WINDOW_W/2 - 90, WINDOW_H - 150, "SELECT LEVEL", GLUT_BITMAP_TIMES_ROMAN_24)
        btn_y = WINDOW_H / 2 + 50
        buttons = [
            [WINDOW_W/2 - 150, btn_y, 300, 50, LEVEL_SETTINGS[1]['name']],
            [WINDOW_W/2 - 150, btn_y - 70, 300, 50, LEVEL_SETTINGS[2]['name']],
            [WINDOW_W/2 - 150, btn_y - 140, 300, 50, LEVEL_SETTINGS[3]['name']],
            [WINDOW_W/2 - 150, btn_y - 210, 300, 50, "Back"]
        ]
        for x, y, w, h, text in buttons:
            glColor3f(0.2, 0.4, 0.7); glBegin(GL_QUADS); glVertex2f(x, y); glVertex2f(x+w, y); glVertex2f(x+w, y+h); glVertex2f(x, y+h); glEnd()
            glColor3f(1.0, 1.0, 1.0); draw_text(x + 30, y + 18, text)
    draw_ui_overlay(content)

def draw_level_complete_menu():
    def content():
        title_text = "LEVEL COMPLETE!" if current_level < 3 else "CONGRATULATIONS!"
        subtitle_text = "You found the exit!" if current_level < 3 else "You have escaped the labyrinth!"
        glColor3f(1.0, 0.9, 0.2); draw_text(WINDOW_W/2 - 100, WINDOW_H - 200, title_text, GLUT_BITMAP_TIMES_ROMAN_24)
        glColor3f(0.9, 0.9, 0.9); draw_text(WINDOW_W/2 - 80, WINDOW_H - 240, subtitle_text)
        btn_y = WINDOW_H / 2 - 50
        buttons = []
        if current_level < 3: buttons.append([WINDOW_W/2-100, btn_y, 200, 50, "Next Level"])
        else: buttons.append([WINDOW_W/2-100, btn_y, 200, 50, "Play Again?"])
        buttons.append([WINDOW_W/2-100, btn_y-70, 200, 50, "Restart Game"])
        buttons.append([WINDOW_W/2-100, btn_y-140, 200, 50, "Quit Game"])
        for x, y, w, h, text in buttons:
            glColor3f(0.2, 0.4, 0.7); glBegin(GL_QUADS); glVertex2f(x, y); glVertex2f(x+w, y); glVertex2f(x+w, y+h); glVertex2f(x, y+h); glEnd()
            glColor3f(1.0, 1.0, 1.0); draw_text(x + 55, y + 18, text)
    draw_ui_overlay(content)
    
# --------------- Camera -----------------
def setup_player_camera():
    global current_cam_x, current_cam_y, current_cam_h, current_look_at_x, current_look_at_y
    if first_person:
        look_x = player_x + 100 * math.cos(math.radians(player_angle_deg))
        look_y = player_y + 100 * math.sin(math.radians(player_angle_deg))
        gluLookAt(player_x, player_y, FP_CAM_HEIGHT, look_x, look_y, FP_CAM_HEIGHT, 0, 0, 1)
    else:
        angle_rad = math.radians(player_angle_deg)
        ideal_cam_x = player_x - cam_radius * math.cos(angle_rad)
        ideal_cam_y = player_y - cam_radius * math.sin(angle_rad)
        target_cam_x, target_cam_y = ideal_cam_x, ideal_cam_y
        for i in range(1, 21):
            t = i / 20.0
            check_x = player_x * (1.0 - t) + ideal_cam_x * t
            check_y = player_y * (1.0 - t) + ideal_cam_y * t
            if check_collision(check_x, check_y):
                t_safe = (i - 1) / 20.0
                target_cam_x = player_x * (1.0 - t_safe) + ideal_cam_x * t_safe
                target_cam_y = player_y * (1.0 - t_safe) + ideal_cam_y * t_safe
                break
        current_cam_x += (target_cam_x - current_cam_x) * CAMERA_SMOOTH_FACTOR
        current_cam_y += (target_cam_y - current_cam_y) * CAMERA_SMOOTH_FACTOR
        current_cam_h += (cam_height - current_cam_h) * CAMERA_SMOOTH_FACTOR
        current_look_at_x += (player_x - current_look_at_x) * CAMERA_SMOOTH_FACTOR
        current_look_at_y += (player_y - current_look_at_y) * CAMERA_SMOOTH_FACTOR
        gluLookAt(current_cam_x, current_cam_y, current_cam_h, 
                  current_look_at_x, current_look_at_y, PLAYER_RADIUS + 20, 0, 0, 1)

def setup_demo_camera():
    center_x = (MAZE_WIDTH * CELL_SIZE) / 2
    center_y = (MAZE_HEIGHT * CELL_SIZE) / 2
    radius = (MAZE_WIDTH * CELL_SIZE) * 0.8
    cam_x = center_x + radius * math.cos(math.radians(demo_maze_angle))
    cam_y = center_y + radius * math.sin(math.radians(demo_maze_angle))
    gluLookAt(cam_x, cam_y, WALL_HEIGHT * 4, center_x, center_y, 0, 0, 0, 1)

# --------------- Input & Game Logic -----------------
def keyboardListener(key, x, y):
    global player_x, player_y, player_angle_deg
    if game_state != "playing": return
    if key == b'r': start_game(current_level); return
    angle_rad = math.radians(player_angle_deg)
    next_x, next_y = player_x, player_y
    if key == b'w': next_x += math.cos(angle_rad) * PLAYER_SPEED; next_y += math.sin(angle_rad) * PLAYER_SPEED
    elif key == b's': next_x -= math.cos(angle_rad) * PLAYER_SPEED; next_y -= math.sin(angle_rad) * PLAYER_SPEED
    elif key == b'a': player_angle_deg += TURN_SPEED
    elif key == b'd': player_angle_deg -= TURN_SPEED
    collided = any(check_collision(next_x + PLAYER_RADIUS*math.cos(math.radians(a)), next_y + PLAYER_RADIUS*math.sin(math.radians(a))) for a in range(0, 360, 90))
    if not collided: player_x, player_y = next_x, next_y

def specialKeyListener(key, x, y):
    global cam_height, cam_radius
    if game_state != "playing" or first_person: return
    if key == GLUT_KEY_UP: cam_height = clamp(cam_height + 10, 50, 800)
    elif key == GLUT_KEY_DOWN: cam_height = clamp(cam_height - 10, 50, 800)
    elif key == GLUT_KEY_LEFT: cam_radius = clamp(cam_radius + 20, 80, 1200)
    elif key == GLUT_KEY_RIGHT: cam_radius = clamp(cam_radius - 20, 80, 1200)

def mouseListener(button, state, x, y):
    global first_person, game_state
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN and game_state == "playing":
        first_person = not first_person; return
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        gl_y = WINDOW_H - y
        if game_state == "intro_menu":
            btn_y = WINDOW_H / 2 + 30
            btn_w, btn_h = 250, 50
            btn_x = WINDOW_W / 2 - btn_w / 2
            
            if btn_x < x < btn_x + btn_w:
                if btn_y < gl_y < btn_y + btn_h:
                    start_game(1)
                elif btn_y - 70 < gl_y < btn_y - 70 + btn_h:
                    game_state = "level_select"
                elif btn_y - 140 < gl_y < btn_y - 140 + btn_h:
                    glutLeaveMainLoop()
        elif game_state == "level_select":
            btn_y = WINDOW_H / 2 + 50
            if WINDOW_W/2-150 < x < WINDOW_W/2+150:
                if btn_y < gl_y < btn_y+50: start_game(1)
                elif btn_y-70 < gl_y < btn_y-20: start_game(2)
                elif btn_y-140 < gl_y < btn_y-90: start_game(3)
                elif btn_y-210 < gl_y < btn_y-160: game_state = "intro_menu"
        elif game_state == "level_complete":
            btn_y = WINDOW_H / 2 - 50
            if WINDOW_W/2-100 < x < WINDOW_W/2+100:
                if current_level < 3 and btn_y < gl_y < btn_y+50: start_game(current_level + 1)
                elif current_level == 3 and btn_y < gl_y < btn_y+50: start_game(1)
                if btn_y-70 < gl_y < btn_y-20: start_game(1)
                if btn_y-140 < gl_y < btn_y-90: glutLeaveMainLoop()

def check_win_condition():
    global game_state
    if game_state != "playing" or not game_maze.goal: return
    gx, gy = game_maze.goal
    goal_pos_x, goal_pos_y = gx * CELL_SIZE + CELL_SIZE / 2, gy * CELL_SIZE + CELL_SIZE / 2
    distance = math.hypot(player_x - goal_pos_x, player_y - goal_pos_y)
    if distance < PLAYER_RADIUS + 20:
        game_state = "level_complete"; print("Level Complete!")

# --------------- Main Loop -----------------
def showScreen():
    global demo_maze_angle
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # Set up the base 3D projection
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(60.0, WINDOW_W / float(WINDOW_H), 1.0, 20000.0)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()

    if game_state == "playing" or game_state == "level_complete":
        check_win_condition()
        setup_player_camera()
        draw_3d_scene()
        if game_state == "level_complete":
            draw_level_complete_menu()
    else: # intro_menu or level_select
        demo_maze_angle += 0.05
        setup_demo_camera()
        draw_3d_scene()
        if game_state == "intro_menu":
            draw_intro_menu()
        elif game_state == "level_select":
            draw_level_select_menu()
            
    glutSwapBuffers()

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutCreateWindow(b"The Final Door - Maze Adventure")
    
    glClearColor(*LEVEL_SETTINGS[2]['sky_color']) 
    
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    initialize_intro_scene()
    
    glutDisplayFunc(showScreen)
    glutIdleFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glEnable(GL_DEPTH_TEST)
    glutMainLoop()

if __name__ == "__main__":
    main()