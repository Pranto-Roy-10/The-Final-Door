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
        # Trap attributes
        self.has_spikes = False
        self.has_hole = False

class Maze:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[Cell(x, y) for y in range(height)] for x in range(width)]
        self.goal = None
        self.start_x = -1
        self.start_y = -1
        self.main_path = set() # For intelligent trap placement
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
        parent = {}
        queue_path = deque([(sx, sy)])

        while queue_path:
            x, y = queue_path.popleft()
            c = self.grid[x][y]
            
            neighbors = []
            if not c.walls['N'] and y > 0: neighbors.append((x, y-1))
            if not c.walls['S'] and y < H-1: neighbors.append((x, y+1))
            if not c.walls['E'] and x < W-1: neighbors.append((x+1, y))
            if not c.walls['W'] and x > 0: neighbors.append((x-1, y))

            for nx, ny in neighbors:
                if dist[nx][ny] == -1:
                    dist[nx][ny] = dist[x][y] + 1
                    parent[(nx, ny)] = (x, y)
                    queue_path.append((nx, ny))

        gx, gy, md = 0, 0, -1
        for i in range(W):
            for j in range(H):
                if dist[i][j] > md: md, gx, gy = dist[i][j], i, j
        self.goal = (gx, gy)
        
        path = []
        if (gx, gy) in parent or (gx, gy) == (sx, sy):
            current = (gx, gy)
            while current != (sx, sy):
                path.append(current)
                current = parent.get(current)
                if current is None: break
            if current == (sx, sy):
                path.append((sx, sy))
        self.main_path = set(path)
        
        return gx, gy, md

    def place_traps(self, start_x, start_y):
        level_settings = LEVEL_SETTINGS[current_level]
        num_holes = level_settings['hole_traps']
        num_spikes = level_settings['spike_traps']

        trap_candidates = []
        for x in range(self.width):
            for y in range(self.height):
                if (x, y) != (start_x, start_y) and (x, y) != self.goal:
                    trap_candidates.append(self.grid[x][y])
        
        random.shuffle(trap_candidates)
        placed_trap_locations = set()

        def place_a_trap_type(num_to_place, is_hole):
            placed_count = 0
            for cell in trap_candidates:
                if placed_count >= num_to_place: break
                if (cell.x, cell.y) in placed_trap_locations: continue
                
                if is_hole: cell.has_hole = True
                else: cell.has_spikes = True
                
                placed_trap_locations.add((cell.x, cell.y))
                # Block adjacent cells to prevent clustering
                for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                    nx, ny = cell.x + dx, cell.y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        placed_trap_locations.add((nx, ny))
                placed_count += 1
        
        place_a_trap_type(num_holes, is_hole=True)
        place_a_trap_type(num_spikes, is_hole=False)

# ----------------- Bullet Class -----------------
class Bullet:
    def __init__(self, x, y, angle, is_enemy=False):
        self.x = x
        self.y = y
        self.z = 33
        self.angle = angle
        self.speed = 4
        self.active = True
        self.is_enemy = is_enemy
        self.radius = 3

    def update(self):
        if self.active:
            angle_rad = math.radians(self.angle)
            self.x += math.cos(angle_rad) * self.speed
            self.y += math.sin(angle_rad) * self.speed
            
            if check_collision(self.x, self.y):
                self.active = False
                return

            max_bound = max(MAZE_WIDTH, MAZE_HEIGHT) * CELL_SIZE
            if not (0 < self.x < max_bound and 0 < self.y < max_bound):
                self.active = False

    def draw(self):
        if self.active:
            glPushMatrix()
            glTranslatef(self.x, self.y, self.z)
            glColor3f(0.0, 1.0, 0.0) if self.is_enemy else glColor3f(1.0, 0.0, 0.0)
            glutSolidSphere(self.radius, 8, 8)
            glPopMatrix()

# ----------------- Enemy Class -----------------
class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle_deg = random.randint(0, 359)
        self.radius = PLAYER_RADIUS * 1.5
        self.shoot_cooldown = random.randint(60, 120)
        self.active = True
        self.ammo = 3
        self.speed = 0.07
        self.patrol_start = (x, y)
        self.patrol_end = self.find_patrol_end()
        if self.patrol_end is None: self.patrol_end = self.patrol_start
        self.target_pos = self.patrol_end

    def find_patrol_end(self):
        start_gx, start_gy = int(self.x / CELL_SIZE), int(self.y / CELL_SIZE)
        start_cell = game_maze.grid[start_gx][start_gy]
        
        possible_directions = []
        if not start_cell.walls['N']: possible_directions.append('N')
        if not start_cell.walls['S']: possible_directions.append('S')
        if not start_cell.walls['E']: possible_directions.append('E')
        if not start_cell.walls['W']: possible_directions.append('W')
        if not possible_directions: return None

        direction = random.choice(possible_directions)
        current_x, current_y = start_gx, start_gy
        path_length = random.randint(2, 5)

        for _ in range(path_length):
            cell = game_maze.grid[current_x][current_y]
            next_x, next_y = current_x, current_y
            if direction == 'N' and not cell.walls['N'] and current_y > 0: next_y -= 1
            elif direction == 'S' and not cell.walls['S'] and current_y < MAZE_HEIGHT - 1: next_y += 1
            elif direction == 'E' and not cell.walls['E'] and current_x < MAZE_WIDTH - 1: next_x += 1
            elif direction == 'W' and not cell.walls['W'] and current_x > 0: next_x -= 1
            else: break
            current_x, current_y = next_x, next_y
        
        return (current_x * CELL_SIZE + CELL_SIZE / 2, current_y * CELL_SIZE + CELL_SIZE / 2)

    def can_see_player(self):
        dist = math.hypot(player_x - self.x, player_y - self.y)
        if dist > 450: return False
        
        dx, dy = player_x - self.x, player_y - self.y
        steps = int(dist / 20)
        if steps == 0: return True
        for i in range(1, steps + 1):
            t = i / steps
            px, py = self.x + dx * t, self.y + dy * t
            if check_collision(px, py):
                return False
        return True

    def update(self):
        if not self.active: return

        if self.can_see_player():
            dx, dy = player_x - self.x, player_y - self.y
            self.angle_deg = math.degrees(math.atan2(dy, dx))
            self.shoot_cooldown -= 1
            if self.shoot_cooldown <= 0:
                self.fire()
                self.shoot_cooldown = random.randint(100, 180)
        else:
            target_x, target_y = self.target_pos
            dist_to_target = math.hypot(target_x - self.x, target_y - self.y)

            if dist_to_target < self.speed * 2:
                self.target_pos = self.patrol_start if self.target_pos == self.patrol_end else self.patrol_end
            else:
                dx, dy = target_x - self.x, target_y - self.y
                self.angle_deg = math.degrees(math.atan2(dy, dx))
                angle_rad = math.radians(self.angle_deg)
                next_x = self.x + math.cos(angle_rad) * self.speed
                next_y = self.y + math.sin(angle_rad) * self.speed
                if not check_collision(next_x, next_y):
                    self.x, self.y = next_x, next_y

    def fire(self):
        if self.ammo <= 0: return
        self.ammo -= 1
        angle_rad = math.radians(self.angle_deg)
        bullet_x = self.x + 25 * math.cos(angle_rad)
        bullet_y = self.y + 25 * math.sin(angle_rad)
        bullets.append(Bullet(bullet_x, bullet_y, self.angle_deg, is_enemy=True))

    def draw(self):
        if not self.active: return
        glPushMatrix()
        glTranslatef(self.x, self.y, 0)
        glRotatef(self.angle_deg - 90, 0, 0, 1)
        glScalef(0.5, 0.5, 0.5)
        # Body
        glPushMatrix(); glTranslatef(0, 0, 40); glColor3f(1.0, 0.0, 0.0); glScalef(1.4, 1.0, 2.0); glutSolidCube(25); glPopMatrix()
        # Head
        glPushMatrix(); glTranslatef(0, 0, 80); glColor3f(0.0, 0.0, 0.0); gluSphere(gluNewQuadric(), 15, 16, 16); glPopMatrix()
        # Arms
        glPushMatrix(); glTranslatef(-20, 0, 55); glRotatef(-90, 1, 0, 0); glColor3f(0.96, 0.8, 0.69); gluCylinder(gluNewQuadric(), 9, 5, 30, 10, 10); glPopMatrix()
        glPushMatrix(); glTranslatef(20, 0, 55); glRotatef(-90, 1, 0, 0); glColor3f(0.96, 0.8, 0.69); gluCylinder(gluNewQuadric(), 9, 5, 30, 10, 10); glPopMatrix()
        # Gun
        glPushMatrix(); glTranslatef(0, 10, 55); glRotatef(-90, 1, 0, 0); glColor3f(0.66, 0.66, 0.66); gluCylinder(gluNewQuadric(), 8, 6, 40, 10, 10); glPopMatrix()
        # Legs
        glPushMatrix(); glTranslatef(-12, 0, 15); glRotatef(180, 1, 0, 0); glColor3f(0.0, 0.0, 0.0); gluCylinder(gluNewQuadric(), 10, 5, 50, 10, 10); glPopMatrix()
        glPushMatrix(); glTranslatef(12, 0, 15); glRotatef(180, 1, 0, 0); glColor3f(0.0, 0.0, 0.0); gluCylinder(gluNewQuadric(), 10, 5, 50, 10, 10); glPopMatrix()
        glPopMatrix()

# ---------------- Window & Scene Globals ----------------
WINDOW_W, WINDOW_H = 1200, 900
game_maze = None
CELL_SIZE = 200
WALL_HEIGHT = 150
WALL_THICKNESS = 10
demo_maze_angle = 0.0

# ---------------- Player Globals ----------------
player_x, player_y = CELL_SIZE / 2, CELL_SIZE / 2
player_angle_deg = 0.0
PLAYER_SPEED = 9.0
TURN_SPEED = 4.0
PLAYER_RADIUS = 9.0
player_z = PLAYER_RADIUS

# ---------------- Game Object Globals ----------------
bullets = []
enemies = []

# ---------------- Camera Globals ----------------
first_person = False
cam_radius = 80.0
cam_height = 150.0
current_cam_x, current_cam_y, current_cam_h = 0, 0, 0
current_look_at_x, current_look_at_y = 0, 0
CAMERA_SMOOTH_FACTOR = 0.1
FP_CAM_HEIGHT = 60.0

# ---------------- Game State & Levels ----------------
game_state = "intro_menu" 
game_over_message = "You were defeated!"
current_level = 1
MAZE_WIDTH, MAZE_HEIGHT = 12, 12 
MAX_ACTIVE_ENEMIES = 5
enemies_to_spawn_count = 0

LEVEL_SETTINGS = {
    1: {'size': (8, 8),   'name': 'The Dawn Gardens',       'sky_color': (0.6, 0.7, 0.9, 1.0), 'total_enemies': 10, 'hole_traps': 2, 'spike_traps': 4},
    2: {'size': (12, 12), 'name': 'The Sunstone Labyrinth', 'sky_color': (0.5, 0.7, 1.0, 1.0), 'total_enemies': 20, 'hole_traps': 5, 'spike_traps': 8},
    3: {'size': (15, 15), 'name': 'The Midnight Maze',      'sky_color': (0.05, 0.05, 0.2, 1.0), 'total_enemies': 30, 'hole_traps': 8, 'spike_traps': 12}
}

# --------------- Utility & Collision -----------------
HOLE_RADIUS = CELL_SIZE / 5
SPIKE_RADIUS = CELL_SIZE / 5

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
    buffer = PLAYER_RADIUS 
    if cell.walls['N'] and y_in_cell < WALL_THICKNESS + buffer: return True
    if cell.walls['S'] and y_in_cell > CELL_SIZE - (WALL_THICKNESS + buffer): return True
    if cell.walls['W'] and x_in_cell < WALL_THICKNESS + buffer: return True
    if cell.walls['E'] and x_in_cell > CELL_SIZE - (WALL_THICKNESS + buffer): return True
    return False

def get_random_position():
    while True:
        gx, gy = random.randint(0, MAZE_WIDTH - 1), random.randint(0, MAZE_HEIGHT - 1)
        if (gx, gy) == (game_maze.start_x, game_maze.start_y) or (gx, gy) == game_maze.goal: continue
        px, py = gx * CELL_SIZE + CELL_SIZE / 2, gy * CELL_SIZE + CELL_SIZE / 2
        if math.hypot(px - player_x, py - player_y) > CELL_SIZE * 3:
            return px, py

def check_traps():
    global game_state, game_over_message
    grid_x, grid_y = int(player_x / CELL_SIZE), int(player_y / CELL_SIZE)
    if not (0 <= grid_x < MAZE_WIDTH and 0 <= grid_y < MAZE_HEIGHT): return
    cell = game_maze.grid[grid_x][grid_y]
    
    cx, cy = grid_x * CELL_SIZE + CELL_SIZE/2, grid_y * CELL_SIZE + CELL_SIZE/2
    dist_from_center = math.hypot(player_x - cx, player_y - cy)

    if cell.has_hole and dist_from_center < HOLE_RADIUS - PLAYER_RADIUS:
        game_over_message, game_state = "You fell into a hole!", "game_over"
    
    if cell.has_spikes and dist_from_center < SPIKE_RADIUS - PLAYER_RADIUS:
        game_over_message, game_state = "You ran into the spikes!", "game_over"

# ---------- Game Logic ----------
def fire_bullet():
    if game_state == "playing":
        angle_rad = math.radians(player_angle_deg)
        bullet_x = player_x + 12 * math.cos(angle_rad)
        bullet_y = player_y + 12 * math.sin(angle_rad)
        bullets.append(Bullet(bullet_x, bullet_y, player_angle_deg))

def spawn_enemy():
    global enemies_to_spawn_count
    if enemies_to_spawn_count <= 0: return
    ex, ey = get_random_position()
    enemies.append(Enemy(ex, ey))
    enemies_to_spawn_count -= 1

def update_game_logic():
    global bullets, enemies, game_state, game_over_message

    for bullet in bullets: bullet.update()
    bullets[:] = [b for b in bullets if b.active]

    for enemy in enemies: enemy.update()

    for bullet in list(bullets):
        if not bullet.active: continue
        if not bullet.is_enemy:
            for enemy in enemies:
                if enemy.active and math.hypot(bullet.x - enemy.x, bullet.y - enemy.y) < enemy.radius:
                    enemy.active = False
                    bullet.active = False
                    break
        else:
            if math.hypot(bullet.x - player_x, bullet.y - player_y) < PLAYER_RADIUS:
                game_over_message, game_state = "You were shot by an enemy!", "game_over"
                bullet.active = False
                return

    for enemy in enemies:
        if enemy.active and math.hypot(player_x - enemy.x, player_y - enemy.y) < PLAYER_RADIUS + enemy.radius:
            game_over_message, game_state = "You ran into an enemy!", "game_over"
            return

    check_traps()
    if game_state == 'game_over': return

    active_enemy_count = sum(1 for e in enemies if e.active)
    if active_enemy_count < MAX_ACTIVE_ENEMIES and enemies_to_spawn_count > 0:
        spawn_enemy()

# ---------- Game Reset & Level Progression ----------
def start_game(level=1):
    global game_maze, player_x, player_y, player_angle_deg, game_state, player_z
    global MAZE_WIDTH, MAZE_HEIGHT, current_level, bullets, enemies, enemies_to_spawn_count
    global current_cam_x, current_cam_y, current_cam_h, current_look_at_x, current_look_at_y

    current_level = level
    level_settings = LEVEL_SETTINGS[current_level]
    MAZE_WIDTH, MAZE_HEIGHT = level_settings['size']
    
    update_lighting(current_level)
    glClearColor(*level_settings['sky_color'])
    
    game_maze = Maze(MAZE_WIDTH, MAZE_HEIGHT)
    start_x, start_y = random.randint(0, MAZE_WIDTH-1), random.randint(0, MAZE_HEIGHT-1)
    game_maze.start_x, game_maze.start_y = start_x, start_y

    player_x, player_y = start_x * CELL_SIZE + CELL_SIZE/2, start_y * CELL_SIZE + CELL_SIZE/2
    player_z, player_angle_deg = PLAYER_RADIUS, 0.0
    
    bullets.clear(); enemies.clear()

    enemies_to_spawn_count = level_settings['total_enemies']
    for _ in range(min(enemies_to_spawn_count, MAX_ACTIVE_ENEMIES)):
        spawn_enemy()
    
    gx, gy, d = game_maze.compute_goal_from_start(start_x, start_y)
    game_maze.place_traps(start_x, start_y)

    current_cam_x, current_cam_y, current_cam_h = player_x, player_y, cam_height
    current_look_at_x, current_look_at_y = player_x, player_y
    game_state = "playing"
    
    print(f"--- Starting {level_settings['name']} ---")
    print(f"Total enemies for level: {level_settings['total_enemies']}")
    print(f"New maze generated ({MAZE_WIDTH}x{MAZE_HEIGHT}). Start={(start_x,start_y)}, Goal={(gx, gy)}")

def initialize_intro_scene():
    global game_maze
    game_maze = Maze(MAZE_WIDTH, MAZE_HEIGHT)

# --------------- Lighting -----------------
def update_lighting(level):
    if level == 3:
        glEnable(GL_LIGHTING); glEnable(GL_LIGHT0)
        light_pos = [0, 0, 200, 1]
        light_ambient = [0.2, 0.2, 0.3, 1.0]
        light_diffuse = [0.8, 0.8, 0.7, 1.0]
        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
    else:
        glDisable(GL_LIGHTING)

# --------------- Drawing (Scene) -----------------
def draw_3d_scene():
    draw_ground()
    if game_maze:
        draw_maze()
        if game_state in ["playing", "level_complete", "game_over"]:
            draw_goal(); draw_player(); draw_traps()
            for enemy in enemies: enemy.draw()
            for bullet in bullets: bullet.draw()

def draw_ground():
    glColor3f(0.55, 0.4, 0.25)
    ground_size = 10000
    glBegin(GL_QUADS); glVertex3f(-ground_size, -ground_size, -0.1); glVertex3f(ground_size, -ground_size, -0.1); glVertex3f(ground_size, ground_size, -0.1); glVertex3f(-ground_size, ground_size, -0.1); glEnd()

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

def draw_traps():
    if not game_maze: return
    for x in range(MAZE_WIDTH):
        for y in range(MAZE_HEIGHT):
            cell = game_maze.grid[x][y]
            cx, cy = x*CELL_SIZE + CELL_SIZE/2, y*CELL_SIZE + CELL_SIZE/2
            
            if cell.has_hole:
                #The ground is at z=-0.1, so this places the hole on top.
                glPushMatrix(); glColor3f(0.1, 0.1, 0.1); glTranslatef(cx, cy, 0.1)
                glBegin(GL_TRIANGLE_FAN)
                glVertex3f(0, 0, 0)
                for i in range(21):
                    angle = 2 * math.pi * i / 20
                    glVertex3f(math.cos(angle) * HOLE_RADIUS, math.sin(angle) * HOLE_RADIUS, 0)
                glEnd(); glPopMatrix()

            if cell.has_spikes:
                glPushMatrix(); glColor3f(0.5, 0.5, 0.55); glTranslatef(cx, cy, 0)
                spike_positions = [(0,0), (15,15), (-15,15), (15,-15), (-15,-15), (25,0), (-25,0), (0,25), (0,-25)]
                for sx, sy in spike_positions:
                    if math.hypot(sx, sy) < SPIKE_RADIUS:
                        glPushMatrix(); glTranslatef(sx, sy, 0); glRotatef(-90, 1, 0, 0)
                        glutSolidCone(6, 30, 8, 8); glPopMatrix()
                glPopMatrix()

def draw_player():
    if first_person: return
    glPushMatrix()
    if game_state == "game_over": glTranslatef(player_x, player_y, 0); glRotatef(90, 0, 1, 0)
    else: glTranslatef(player_x, player_y, 0); glRotatef(player_angle_deg, 0, 0, 1)

    glRotatef(-90, 0, 0, 1); glScalef(0.6, 0.6, 0.6)
    # Body
    glPushMatrix(); glTranslatef(0, 0, 40); glColor3f(0.0, 0.6, 0.6); glScalef(1.4, 1.0, 2.0); glutSolidCube(25); glPopMatrix()
    # Head
    glPushMatrix(); glTranslatef(0, 0, 80); glColor3f(0.0, 0.0, 0.0); gluSphere(gluNewQuadric(), 15, 16, 16); glPopMatrix()
    # Arms
    glPushMatrix(); glTranslatef(-20, 0, 55); glRotatef(-90, 1, 0, 0); glColor3f(0.96, 0.8, 0.69); gluCylinder(gluNewQuadric(), 9, 5, 30, 10, 10); glPopMatrix()
    glPushMatrix(); glTranslatef(20, 0, 55); glRotatef(-90, 1, 0, 0); glColor3f(0.96, 0.8, 0.69); gluCylinder(gluNewQuadric(), 9, 5, 30, 10, 10); glPopMatrix()
    # Gun
    glPushMatrix(); glTranslatef(0, 10, 55); glRotatef(-90, 1, 0, 0); glColor3f(0.66, 0.66, 0.66); gluCylinder(gluNewQuadric(), 8, 6, 40, 10, 10); glPopMatrix()
    # Legs
    glPushMatrix(); glTranslatef(-12, 0, 15); glRotatef(180, 1, 0, 0); glColor3f(0.8, 0.7, 0.6); gluCylinder(gluNewQuadric(), 10, 5, 50, 10, 10); glPopMatrix()
    glPushMatrix(); glTranslatef(12, 0, 15); glRotatef(180, 1, 0, 0); glColor3f(0.8, 0.7, 0.6); gluCylinder(gluNewQuadric(), 10, 5, 50, 10, 10); glPopMatrix()
    glPopMatrix()

def draw_goal():
    if not game_maze or not game_maze.goal: return
    gx, gy = game_maze.goal
    cx, cy = gx*CELL_SIZE + CELL_SIZE/2, gy*CELL_SIZE + CELL_SIZE/2
    glPushMatrix(); glTranslatef(cx, cy, 0)
    glColor3f(0.95, 0.85, 0.2); glPushMatrix(); glTranslatef(0, 0, 6); glScalef(40, 40, 12); glutSolidCube(1); glPopMatrix()
    glColor3f(0.2, 0.8, 0.2); glPushMatrix(); glTranslatef(-16, 0, 70); glScalef(12, 12, 140); glutSolidCube(1); glPopMatrix()
    glPushMatrix(); glTranslatef(16, 0, 70); glScalef(12, 12, 140); glutSolidCube(1); glPopMatrix()
    glColor3f(0.2, 0.6, 0.9); glPushMatrix(); glTranslatef(0, 0, 140); glScalef(44, 12, 12); glutSolidCube(1); glPopMatrix()
    glPopMatrix()

# --------------- Drawing (UI Menus) -----------------
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glRasterPos2f(x, y)
    for char in text: glutBitmapCharacter(font, ord(char))

def draw_ui_overlay(draw_content_func):
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity(); glDisable(GL_DEPTH_TEST)
    
    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0, 0, 0, 0.6); glBegin(GL_QUADS); glVertex2f(0,0); glVertex2f(WINDOW_W,0); glVertex2f(WINDOW_W,WINDOW_H); glVertex2f(0,WINDOW_H); glEnd()
    glDisable(GL_BLEND)
    draw_content_func()
    glEnable(GL_DEPTH_TEST); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW); glPopMatrix()

def draw_styled_button(x, y, w, h, text, font=GLUT_BITMAP_HELVETICA_18):
    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.15, 0.15, 0.18, 0.75); glBegin(GL_QUADS); glVertex2f(x,y); glVertex2f(x+w,y); glVertex2f(x+w,y+h); glVertex2f(x,y+h); glEnd()
    glDisable(GL_BLEND)
    glColor3f(0.6, 0.7, 0.8); glLineWidth(2.0); glBegin(GL_LINE_LOOP); glVertex2f(x,y); glVertex2f(x+w,y); glVertex2f(x+w,y+h); glVertex2f(x,y+h); glEnd(); glLineWidth(1.0)
    text_width = sum(glutBitmapWidth(font, ord(c)) for c in text)
    glColor3f(1, 1, 1); draw_text(x + (w - text_width)/2, y + (h - 18)/2 + 5, text, font)

def draw_intro_menu():
    def content():
        title_font = GLUT_BITMAP_TIMES_ROMAN_24
        title = "THE FINAL DOOR"; tw = sum(glutBitmapWidth(title_font, ord(c)) for c in title)
        glColor3f(0.95,0.85,0.2); draw_text(WINDOW_W/2 - tw/2, WINDOW_H - 150, title, title_font)
        sub = "An Amazing Maze Adventure"; sw = sum(glutBitmapWidth(GLUT_BITMAP_HELVETICA_18, ord(c)) for c in sub)
        glColor3f(0.8,0.8,0.8); draw_text(WINDOW_W/2 - sw/2, WINDOW_H - 185, sub)
        btn_y, btn_w, btn_h, btn_x = WINDOW_H/2 + 30, 250, 50, WINDOW_W/2 - 125
        draw_styled_button(btn_x, btn_y, btn_w, btn_h, "Play Game")
        draw_styled_button(btn_x, btn_y - 70, btn_w, btn_h, "Select Level")
        draw_styled_button(btn_x, btn_y - 140, btn_w, btn_h, "Quit")
    draw_ui_overlay(content)

def draw_level_select_menu():
    def content():
        glColor3f(1, 0.9, 0.2); draw_text(WINDOW_W/2-90, WINDOW_H-150, "SELECT LEVEL", GLUT_BITMAP_TIMES_ROMAN_24)
        btn_y = WINDOW_H/2 + 50
        buttons = [
            (WINDOW_W/2-150, btn_y, 300, 50, LEVEL_SETTINGS[1]['name']),
            (WINDOW_W/2-150, btn_y-70, 300, 50, LEVEL_SETTINGS[2]['name']),
            (WINDOW_W/2-150, btn_y-140, 300, 50, LEVEL_SETTINGS[3]['name']),
            (WINDOW_W/2-150, btn_y-210, 300, 50, "Back")
        ]
        for x, y, w, h, text in buttons: draw_styled_button(x, y, w, h, text)
    draw_ui_overlay(content)

def draw_level_complete_menu():
    def content():
        title = "LEVEL COMPLETE!" if current_level<3 else "CONGRATULATIONS!"
        sub = "You found the exit!" if current_level<3 else "You have escaped the labyrinth!"
        glColor3f(1,0.9,0.2); draw_text(WINDOW_W/2 - 100, WINDOW_H - 200, title, GLUT_BITMAP_TIMES_ROMAN_24)
        glColor3f(0.9,0.9,0.9); draw_text(WINDOW_W/2 - 80, WINDOW_H - 240, sub)
        btn_y = WINDOW_H/2 - 50
        if current_level < 3: draw_styled_button(WINDOW_W/2-100, btn_y, 200, 50, "Next Level")
        else: draw_styled_button(WINDOW_W/2-100, btn_y, 200, 50, "Play Again?")
        draw_styled_button(WINDOW_W/2-100, btn_y-70, 200, 50, "Back to Main Menu")
    draw_ui_overlay(content)

def draw_game_over_menu():
    def content():
        glColor3f(1,0.2,0.2); draw_text(WINDOW_W/2-80, WINDOW_H-200, "GAME OVER!", GLUT_BITMAP_TIMES_ROMAN_24)
        msg_w = sum(glutBitmapWidth(GLUT_BITMAP_HELVETICA_18, ord(c)) for c in game_over_message)
        glColor3f(0.9,0.9,0.9); draw_text(WINDOW_W/2-msg_w/2, WINDOW_H-240, game_over_message)
        btn_y = WINDOW_H/2 - 50
        draw_styled_button(WINDOW_W/2-100, btn_y, 200, 50, "Restart Level")
        draw_styled_button(WINDOW_W/2-100, btn_y-70, 200, 50, "Back to Main Menu")
        draw_styled_button(WINDOW_W/2-100, btn_y-140, 200, 50, "Quit Game")
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
        ideal_cam_x, ideal_cam_y = player_x - cam_radius*math.cos(angle_rad), player_y - cam_radius*math.sin(angle_rad)
        target_cam_x, target_cam_y = ideal_cam_x, ideal_cam_y
        for i in range(1, 21):
            t = i / 20.0
            check_x, check_y = player_x*(1-t) + ideal_cam_x*t, player_y*(1-t) + ideal_cam_y*t
            if check_collision(check_x, check_y):
                t_safe = (i - 1) / 20.0
                target_cam_x, target_cam_y = player_x*(1-t_safe) + ideal_cam_x*t_safe, player_y*(1-t_safe) + ideal_cam_y*t_safe
                break
        current_cam_x += (target_cam_x - current_cam_x) * CAMERA_SMOOTH_FACTOR
        current_cam_y += (target_cam_y - current_cam_y) * CAMERA_SMOOTH_FACTOR
        current_cam_h += (cam_height - current_cam_h) * CAMERA_SMOOTH_FACTOR
        current_look_at_x += (player_x - current_look_at_x) * CAMERA_SMOOTH_FACTOR
        current_look_at_y += (player_y - current_look_at_y) * CAMERA_SMOOTH_FACTOR
        gluLookAt(current_cam_x, current_cam_y, current_cam_h, current_look_at_x, current_look_at_y, PLAYER_RADIUS + 20, 0, 0, 1)

def setup_demo_camera():
    center_x, center_y = (MAZE_WIDTH*CELL_SIZE)/2, (MAZE_HEIGHT*CELL_SIZE)/2
    radius = (MAZE_WIDTH * CELL_SIZE) * 0.8
    cam_x = center_x + radius * math.cos(math.radians(demo_maze_angle))
    cam_y = center_y + radius * math.sin(math.radians(demo_maze_angle))
    gluLookAt(cam_x, cam_y, WALL_HEIGHT*4, center_x, center_y, 0, 0, 0, 1)

# --------------- Input & Game Logic -----------------
def keyboardListener(key, x, y):
    global player_x, player_y, player_angle_deg
    if key == b'r': start_game(current_level); return
    if game_state != "playing": return

    angle_rad = math.radians(player_angle_deg)
    next_x, next_y = player_x, player_y
    if key == b'w': next_x += math.cos(angle_rad)*PLAYER_SPEED; next_y += math.sin(angle_rad)*PLAYER_SPEED
    elif key == b's': next_x -= math.cos(angle_rad)*PLAYER_SPEED; next_y -= math.sin(angle_rad)*PLAYER_SPEED
    elif key == b'a': player_angle_deg += TURN_SPEED
    elif key == b'd': player_angle_deg -= TURN_SPEED
    
    if not check_collision(next_x, next_y): player_x, player_y = next_x, next_y

def specialKeyListener(key, x, y):
    global cam_height, cam_radius
    if game_state != "playing" or first_person: return
    if key == GLUT_KEY_UP: cam_height = clamp(cam_height + 10, 50, 800)
    elif key == GLUT_KEY_DOWN: cam_height = clamp(cam_height - 10, 50, 800)
    elif key == GLUT_KEY_LEFT: cam_radius = clamp(cam_radius + 20, 80, 1200)
    elif key == GLUT_KEY_RIGHT: cam_radius = clamp(cam_radius - 20, 80, 1200)

def mouseListener(button, state, x, y):
    global first_person, game_state
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and game_state == "playing": fire_bullet(); return
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN and game_state == "playing": first_person = not first_person; return
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        gl_y = WINDOW_H - y
        if game_state == "intro_menu":
            btn_y, btn_w, btn_h, btn_x = WINDOW_H/2+30, 250, 50, WINDOW_W/2-125
            if btn_x < x < btn_x+btn_w:
                if btn_y < gl_y < btn_y+btn_h: start_game(1)
                elif btn_y-70 < gl_y < btn_y-70+btn_h: game_state = "level_select"
                elif btn_y-140 < gl_y < btn_y-140+btn_h: glutLeaveMainLoop()
        elif game_state == "level_select":
            btn_y = WINDOW_H/2 + 50
            if WINDOW_W/2-150 < x < WINDOW_W/2+150:
                if btn_y < gl_y < btn_y+50: start_game(1)
                elif btn_y-70 < gl_y < btn_y-20: start_game(2)
                elif btn_y-140 < gl_y < btn_y-90: start_game(3)
                elif btn_y-210 < gl_y < btn_y-160: game_state = "intro_menu"
        elif game_state == "level_complete":
            btn_y = WINDOW_H/2 - 50
            if WINDOW_W/2-100 < x < WINDOW_W/2+100:
                if current_level<3 and btn_y < gl_y < btn_y+50: start_game(current_level+1)
                elif current_level==3 and btn_y < gl_y < btn_y+50: start_game(1)
                if btn_y-70 < gl_y < btn_y-20: initialize_intro_scene(); game_state = "intro_menu"
        elif game_state == "game_over":
            btn_y = WINDOW_H/2 - 50
            if WINDOW_W/2-100 < x < WINDOW_W/2+100:
                if btn_y < gl_y < btn_y+50: start_game(current_level)
                elif btn_y-70 < gl_y < btn_y-20: initialize_intro_scene(); game_state = "intro_menu"
                elif btn_y-140 < gl_y < btn_y-90: glutLeaveMainLoop()

def check_win_condition():
    global game_state
    if game_state != "playing" or not game_maze.goal: return
    gx, gy = game_maze.goal
    goal_pos_x, goal_pos_y = gx*CELL_SIZE + CELL_SIZE/2, gy*CELL_SIZE + CELL_SIZE/2
    distance = math.hypot(player_x - goal_pos_x, player_y - goal_pos_y)
    
    all_enemies_defeated = enemies_to_spawn_count == 0 and all(not enemy.active for enemy in enemies)
    
    if distance < PLAYER_RADIUS + 20 and all_enemies_defeated:
        game_state = "level_complete"
        print("Level Complete!")

# --------------- Main Loop -----------------
def showScreen():
    global demo_maze_angle
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(60.0, WINDOW_W / float(WINDOW_H), 1.0, 20000.0)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()

    if game_state == "playing":
        update_game_logic()
        check_win_condition()
        setup_player_camera()
        draw_3d_scene()
    elif game_state == "level_complete":
        setup_player_camera(); draw_3d_scene(); draw_level_complete_menu()
    elif game_state == "game_over":
        setup_player_camera(); draw_3d_scene(); draw_game_over_menu()
    else:
        demo_maze_angle += 0.05
        setup_demo_camera(); draw_3d_scene()
        if game_state == "intro_menu": draw_intro_menu()
        elif game_state == "level_select": draw_level_select_menu()
            
    glutSwapBuffers()

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutCreateWindow(b"The Final Door - Maze Adventure")
    
    glClearColor(*LEVEL_SETTINGS[1]['sky_color'])
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    initialize_intro_scene()
    
    glutDisplayFunc(showScreen); glutIdleFunc(showScreen)
    glutKeyboardFunc(keyboardListener); glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glEnable(GL_DEPTH_TEST)
    glutMainLoop()

if __name__ == "__main__":
    main()