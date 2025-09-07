# ----------------- Imports -----------------
from OpenGL.GL import *          # Import OpenGL functions (used for drawing)
from OpenGL.GLUT import *        # Import GLUT (used for input,shapes,text)
from OpenGL.GLU import *         # Import GLU 
import math                     
import random                    # Random numbers for maze
from collections import deque    # queue used in BFS
import sys                       # args,exit

# ----------------- Maze Generation Classes -----------------
class Cell:
    """Represents a single cell in the maze grid."""
    def __init__(self, x, y):
        self.x = x                                   # Column index in grid
        self.y = y                                   # Row index in grid
        self.walls = {'N': True, 'S': True, 'E': True, 'W': True}  # Wall flags
        self.visited = False                         # Used during maze generation
        self.wall_colors = {}                        # default color shade per wall
        # Trap attributes
        self.has_spikes = False                      # Spike trap flag
        self.has_hole = False                        # Hole trap flag
        self.spike_rotations = []                    # Random rotations for spike 

class Maze:
    """Generates and manages the maze structure using DFS."""
    def __init__(self, width, height):
        self.width = width                                          # Number of columns
        self.height = height                                        # Number of rows
        self.grid = [[Cell(x, y) for y in range(height)]            # 2D list of Cell objects
                     for x in range(width)]
        self.goal = None                                           # gx, gy of exit cell
        self.start_x = -1                                          # Start cell x (set later)
        self.start_y = -1                                          # Start cell y (set later)
        self.main_path = set()                                     # Main path cells    
        # Precalculate wall colors for visual
        for x in range(width):
            for y in range(height):
                cell = self.grid[x][y]
                cell.wall_colors['N'] = get_smooth_color(x, y, offset=0.1) # Shade north wall
                cell.wall_colors['S'] = get_smooth_color(x, y, offset=0.2) # Shade south wall
                cell.wall_colors['E'] = get_smooth_color(x, y, offset=0.3) # Shade east wall
                cell.wall_colors['W'] = get_smooth_color(x, y, offset=0.4) # Shade west wall
        self.generate()                                                    # Build the maze 

    def get_neighbors(self, cell):
        """Find unvisited neighbors for maze generation.Each cell has up to 4 possible neighbors:North (above),South (below),East (right),West (left)."""
        neighbors = []                                              
        if cell.y > 0 and not self.grid[cell.x][cell.y - 1].visited:
            neighbors.append(self.grid[cell.x][cell.y - 1])                       # Up
        if cell.y < self.height - 1 and not self.grid[cell.x][cell.y + 1].visited:
            neighbors.append(self.grid[cell.x][cell.y + 1])                  # Down
        if cell.x < self.width - 1 and not self.grid[cell.x + 1][cell.y].visited: 
            neighbors.append(self.grid[cell.x + 1][cell.y])             # Right
        if cell.x > 0 and not self.grid[cell.x - 1][cell.y].visited:
            neighbors.append(self.grid[cell.x - 1][cell.y])                      # Left
        return neighbors

    def remove_walls(self, current_cell, next_cell):
        """Remove walls between two adjacent cells."""
        dx, dy = current_cell.x - next_cell.x, current_cell.y - next_cell.y    #Direction difference
        if dx == 1:                                                # next is left of current
            current_cell.walls['W'], next_cell.walls['E'] = False, False
        elif dx == -1:                                             # next is right of current
            current_cell.walls['E'], next_cell.walls['W'] = False, False
        if dy == 1:                                                # next is above current
            current_cell.walls['N'], next_cell.walls['S'] = False, False
        elif dy == -1:                                             # next is below current
            current_cell.walls['S'], next_cell.walls['N'] = False, False

    def generate(self):
        """Recursive backtracking algorithm for maze generation."""
        stack = []                                                 # Path stack
        start_cell = self.grid[random.randint(0, self.width - 1)][random.randint(0, self.height - 1)]                                               # Random start
        start_cell.visited = True                                  # Mark visited
        stack.append(start_cell)                                   # Push start
        while stack:                                               # While we have a path
            current_cell = stack[-1]                               # Look at (current)
            neighbors = self.get_neighbors(current_cell)           # Unvisited neighbors
            if neighbors:                                          # If there is a neighbor
                next_cell = random.choice(neighbors)               # Pick one
                next_cell.visited = True                           # Visit it
                self.remove_walls(current_cell, next_cell) # Knock down wall
                stack.append(next_cell)  # Move forward
            else:
                stack.pop() # Dead end → backtrack

    def compute_goal_from_start(self, sx, sy):
        """Finds the furthest point from (sx, sy) using BFS to set as the goal."""
        W, H = self.width, self.height                          
        dist = [[-1] * H for _ in range(W)]                 # Distance grid unvisited = -1
        q = deque([(sx, sy)]); dist[sx][sy] = 0             # BFS init
        parent = {}                                         # For path reconstruction optional
        queue_path = deque([(sx, sy)])                      # Working queue

        while queue_path:                                   # BFS loop
            x, y = queue_path.popleft()
            c = self.grid[x][y]

            neighbors = []                                # Graph neighbors through open walls
            if not c.walls['N'] and y > 0: 
                neighbors.append((x, y-1))
            if not c.walls['S'] and y < H-1: 
                neighbors.append((x, y+1))
            if not c.walls['E'] and x < W-1: 
                neighbors.append((x+1, y))
            if not c.walls['W'] and x > 0: 
                neighbors.append((x-1, y))

            for nx, ny in neighbors:
                if dist[nx][ny] == -1:                  # Unvisited
                    dist[nx][ny] = dist[x][y] + 1       # Set distance
                    parent[(nx, ny)] = (x, y)           # Record parent
                    queue_path.append((nx, ny))         # Enqueue

        # Find cell with maximum distance from start
        gx, gy, md = 0, 0, -1
        for i in range(W):
            for j in range(H):
                if dist[i][j] > md:
                    md, gx, gy = dist[i][j], i, j
        self.goal = (gx, gy)                             # Save goal

        # Backtrack to find the main path optional as said parent use is optional
        path = []
        if (gx, gy) in parent or (gx, gy) == (sx, sy):
            current = (gx, gy)
            while current != (sx, sy):
                path.append(current)
                current = parent.get(current)             # Step to parent
                if current is None: break                 # Safety
            if current == (sx, sy):
                path.append((sx, sy))
        self.main_path = set(path)                        # Store as a set

        return gx, gy, md                                 # Return goal and distance

    def find_shortest_path(self, start_pos, end_pos):
        """BFS algorithm to find the shortest path between two points,used for cheat mode."""
        sx, sy = start_pos                                # Start grid coords
        ex, ey = end_pos                                  # End grid coords

        q = deque([(sx, sy)])                             # BFS queue
        parent = {(sx, sy): None}                         # Parent map for path
        visited = {(sx, sy)}                              # Visited set

        while q:
            x, y = q.popleft()
            if (x, y) == (ex, ey):                        # Reached goal
                path = []
                curr = (ex, ey)
                while curr is not None:                   # Backtrack parents
                    path.append(curr)
                    curr = parent.get(curr)
                return path[::-1]                         # Return in forward order

            c = self.grid[x][y]
            potential_neighbors = []                      # Explore through open walls
            if not c.walls['N'] and y > 0: 
                potential_neighbors.append((x, y - 1))
            if not c.walls['S'] and y < self.height - 1: 
                potential_neighbors.append((x, y + 1))
            if not c.walls['E'] and x < self.width - 1: 
                potential_neighbors.append((x + 1, y))
            if not c.walls['W'] and x > 0: 
                potential_neighbors.append((x - 1, y))

            for nx, ny in potential_neighbors:
                if (nx, ny) not in visited:               # Not seen yet
                    visited.add((nx, ny))
                    parent[(nx, ny)] = (x, y)
                    q.append((nx, ny))
        return []                                         # No path found

    def place_traps(self, start_x, start_y):
        """Distributes traps (holes and spikes) across the maze,avoiding start/goal."""
        level_settings = LEVEL_SETTINGS[current_level]              # Settings per level
        num_holes = level_settings['hole_traps']                    # How many holes
        num_spikes = level_settings['spike_traps']                  # How many spikes

        # Collect all valid locations for traps
        trap_candidates = []                                        # valid cells
        for x in range(self.width):
            for y in range(self.height):
                if (x, y) != (start_x, start_y) and (x, y) != self.goal:
                    trap_candidates.append(self.grid[x][y])         # Skip start/goal cells

        random.shuffle(trap_candidates)                             # Randomize order
        placed_trap_locations = set()                            # Avoid traps being too close

        def place_a_trap_type(num_to_place, is_hole):
            placed_count = 0
            for cell in trap_candidates:
                if placed_count >= num_to_place:
                    break                                        # Done placing
                if (cell.x, cell.y) in placed_trap_locations: 
                    continue                                     # Too close

                if is_hole:
                    cell.has_hole = True                         # Mark hole
                else:
                    cell.has_spikes = True                       # Mark spikes
                    num_small_spikes = 4                         # Decorative spikes
                    cell.spike_rotations = [random.uniform(0, 360)
                                            for _ in range(num_small_spikes)]

                # Mark current cell and neighbors as occupied to space out traps
                placed_trap_locations.add((cell.x, cell.y))
                for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                    nx, ny = cell.x + dx, cell.y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        placed_trap_locations.add((nx, ny))
                placed_count += 1

        place_a_trap_type(num_holes, is_hole=True)               # Place holes
        place_a_trap_type(num_spikes, is_hole=False)             # Place spikes

# ----------------- Bullet Class -----------------
class Bullet:
    """Represents a bullet fired by the player or an enemy."""
    def __init__(self, x, y, angle, is_enemy=False):
        self.x = x    # Current x position
        self.y = y                               # Current y position
        self.z = 33                              # Height above ground to draw bullet
        self.angle = angle                       # Direction in degrees
        self.speed = 5.0                         # Movement speed 
        self.active = True                       # Is the bullet still flying?
        self.is_enemy = is_enemy                 # Owner type (enemy/player)
        self.radius = 1.0                        # Collision radius of bullet

    def update(self):
        """Move bullet and check for wall collisions."""
        if self.active:
            angle_rad = math.radians(self.angle)               # Convert to radians
            self.x += math.cos(angle_rad) * self.speed         # Move along x
            self.y += math.sin(angle_rad) * self.speed         # Move along y

            # Check for wall collision
            if check_collision(self.x, self.y):                # Hits a wall?
                self.active = False                            # Deactivate
                return

            # Check for out-of-bounds
            max_bound = max(MAZE_WIDTH, MAZE_HEIGHT) * CELL_SIZE
            if not (0 < self.x < max_bound and 0 < self.y < max_bound):
                self.active = False                            # Deactivate if outside maze

    def draw(self):
        """representing bullet as a small sphere."""
        if self.active:
            glPushMatrix()                                     # Save transform
            glTranslatef(self.x, self.y, self.z)               # Move to bullet position
            if self.is_enemy:
                glColor3f(0.0, 1.0, 0.0)                       # Green if enemys bullet
            else:
                glColor3f(1.0, 0.0, 0.0)                       # Red if players bullet
            glutSolidSphere(self.radius, 8, 8)                 # Draw simple sphere
            glPopMatrix()                                      # Restore transform

# ----------------- Enemy Class -----------------
ENEMY_SIGHT_RANGE = 450.0            # How far enemies can see the player 

class Enemy:
    """Represents enemy."""
    def __init__(self, x, y):
        self.x = x                                          # Current x
        self.y = y                                          # Current y
        self.angle_deg = random.randint(0, 359)             # Facing direction
        self.radius = 22.0                                  # Collision radius
        self.shoot_cooldown = random.randint(60, 120)       # cooldown until next shot
        self.active = True                                   # Alive as active flag
        self.ammo = 10                                      # Shots available
        self.speed = 0.07                                   # enemy movement speed
        # patrol means enemy jei jayga pahara dicche je player ashtese kina
        self.patrol_start = (x, y)                          # patrolstart point A
        self.patrol_end = self.find_patrol_end()            # patrolend point B
        if self.patrol_end is None:
            self.patrol_end = self.patrol_start             # Fallback
        self.target_pos = self.patrol_end                   # Current patrol target

    def find_patrol_end(self):
        """Find a nearby location for the enemy to patrol to."""
        start_gx, start_gy = int(self.x / CELL_SIZE), int(self.y / CELL_SIZE)   # Grid coords
        start_cell = game_maze.grid[start_gx][start_gy]                         # Cell object

        possible_directions = []                          # Directions with no wall
        if not start_cell.walls['N']: 
            possible_directions.append('N')
        if not start_cell.walls['S']: 
            possible_directions.append('S')
        if not start_cell.walls['E']: 
            possible_directions.append('E')
        if not start_cell.walls['W']: 
            possible_directions.append('W')
        if not possible_directions: 
            return None                                  # Nowhere to go

        direction = random.choice(possible_directions)   # Pick a direction
        current_x, current_y = start_gx, start_gy
        path_length = random.randint(2, 5)               # Patrol length in cells

        for _ in range(path_length):                     # Walk forward along chosen direction
            cell = game_maze.grid[current_x][current_y]
            next_x, next_y = current_x, current_y
            if direction == 'N' and not cell.walls['N'] and current_y > 0: 
                next_y -= 1
            elif direction == 'S' and not cell.walls['S'] and current_y < MAZE_HEIGHT - 1:     
                next_y += 1
            elif direction == 'E' and not cell.walls['E'] and current_x < MAZE_WIDTH - 1:      
                next_x += 1
            elif direction == 'W' and not cell.walls['W'] and current_x > 0: 
                next_x -= 1
            else: 
                break                                    # Stop at wall 
            current_x, current_y = next_x, next_y

        return (current_x * CELL_SIZE + CELL_SIZE / 2,     # Convert grid to wall coords
                current_y * CELL_SIZE + CELL_SIZE / 2)

    def can_see_player(self):
        """an imaginary straight line from the enemy’s position to the player’s position.basically enemy ar player er moddhe ekta imaginary line create hoy jar through te enemy player kothay ache dekhte pay, ei line ta jodi kothao block khay tar mane deyal er ei imaginary line ba ray ta blocked, and ei line er towards hatar shmoy o 20 steps kore agay and checks if the line is blocked or not"""
        dist = math.hypot(player_x - self.x, player_y - self.y)  # Distance to player
        if dist > ENEMY_SIGHT_RANGE: 
            return False                                         # Too far

        dx, dy = player_x - self.x, player_y - self.y            # Direction vector
        steps = int(dist / 20)          # checks every 20 units of the line if it is blocked or not, if blocked there is a wall , and if not no wall)
        if steps == 0: 
            return True                                          # close
        for i in range(1, steps + 1):
            t = i / steps                              # goes to player by taking small steps
            px, py = self.x + dx * t, self.y + dy * t  # Sample points on line for checking lines blocked or not
            if check_collision(px, py):                          # Wall blocks line?
                return False
        return True                                              # Clear line(no blockade)

    def update(self):
        """Update enemy state: either follow player/fire at player."""
        if not self.active: return

        if self.can_see_player():                                # Player visible?
            # --- fully on firing mood ---
            dx, dy = player_x - self.x, player_y - self.y        # Face player
            self.angle_deg = math.degrees(math.atan2(dy, dx))
            # fire Cooldown 
            self.shoot_cooldown -= 1
            if self.shoot_cooldown <= 0:
                self.fire()
                self.shoot_cooldown = random.randint(60, 120)    # Reset cooldown
        else:
            # --- here enemy moves backand fourth and guard the patrol area to check if any player comes or not, basically enemy oaharadar der moto hat te thake dekhar jonno je player ashche kina,ei path ta start to end porjonto, start to ened ekbar hate then means arrived then no co ordinates swapping, abar endpoint theke startpoint jay again arrived no swapping, ebhabe patrol area mane pahara deya path e hat te thake ar check korte thake  ---
            target_x, target_y = self.target_pos
            dist_to_target = math.hypot(target_x - self.x, target_y - self.y)

            if dist_to_target < self.speed * 2:                # Arrived means no swapping
                if self.target_pos == self.patrol_end:
                    self.target_pos = self.patrol_start 
                else:
                    self.target_pos = self.patrol_end
            else:
                # Move toward target
                dx, dy = target_x - self.x, target_y - self.y
                self.angle_deg = math.degrees(math.atan2(dy, dx))
                angle_rad = math.radians(self.angle_deg)
                next_x = self.x + math.cos(angle_rad) * self.speed
                next_y = self.y + math.sin(angle_rad) * self.speed
                if not check_collision(next_x, next_y):       # Move if no wall
                    self.x, self.y = next_x, next_y

    def fire(self):
        """Create a bullet fired from the enemy."""
        if self.ammo <= 0: return
        self.ammo -= 1
        angle_rad = math.radians(self.angle_deg)                  # Convert to radians
        bullet_x = self.x + 25 * math.cos(angle_rad)              # bullet coming out of guns
        bullet_y = self.y + 25 * math.sin(angle_rad)
        bullets.append(Bullet(bullet_x, bullet_y, self.angle_deg, is_enemy=True))# Add to list

    def draw(self):
        """Draw the enemy."""
        if not self.active: return
        glPushMatrix()                                            # Save transform
        glTranslatef(self.x, self.y, 0)                           # Move to enemy position
        glRotatef(self.angle_deg - 90, 0, 0, 1)                   # Rotate to face direction
        glScalef(0.5, 0.5, 0.5)                                   # Scale smaller
        # Body (Torso)
        glPushMatrix(); 
        glTranslatef(0, 0, 40);                             # Red torso cube
        glColor3f(1.0, 0.0, 0.0); 
        glScalef(1.4, 1.0, 2.0); 
        glutSolidCube(25); 
        glPopMatrix()  
        # Head
        glPushMatrix(); 
        glTranslatef(0, 0, 80);                              # Black head sphere 
        glColor3f(0.0, 0.0, 0.0); 
        gluSphere(gluNewQuadric(), 15, 16, 16); 
        glPopMatrix()       
        # Arms
        glPushMatrix(); 
        glTranslatef(-20, 0, 55);                           # Left arm
        glRotatef(-90, 1, 0, 0); 
        glColor3f(0.96, 0.8, 0.69); 
        gluCylinder(gluNewQuadric(), 9, 5, 30, 10, 10); 
        glPopMatrix()  
        glPushMatrix(); 
        glTranslatef(20, 0, 55);                            # Right arm 
        glRotatef(-90, 1, 0, 0); 
        glColor3f(0.96, 0.8, 0.69); 
        gluCylinder(gluNewQuadric(), 9, 5, 30, 10, 10); 
        glPopMatrix()   
        # Gun Barrel
        glPushMatrix(); 
        glTranslatef(0, 10, 55);                            # Barrel
        glRotatef(-90, 1, 0, 0); 
        glColor3f(0.66, 0.66, 0.66); 
        gluCylinder(gluNewQuadric(), 8, 6, 40, 10, 10); 
        glPopMatrix()  
        # Legs
        glPushMatrix(); 
        glTranslatef(-12, 0, 15);                              # Left leg
        glRotatef(180, 1, 0, 0); 
        glColor3f(0.0, 0.0, 0.0); 
        gluCylinder(gluNewQuadric(), 10, 5, 50, 10, 10); 
        glPopMatrix()   
        glPushMatrix(); 
        glTranslatef(12, 0, 15);                               # Right leg
        glRotatef(180, 1, 0, 0); 
        glColor3f(0.0, 0.0, 0.0); 
        gluCylinder(gluNewQuadric(), 10, 5, 50, 10, 10); 
        glPopMatrix()    
        glPopMatrix()                                           # Restore transform

# ---------------- Window & Scene info ----------------
WINDOW_W, WINDOW_H = 1200, 900                 # Window width/height in pixels
game_maze = None                               # Active Maze object
CELL_SIZE = 200                                # Size of one cell in units
WALL_HEIGHT = 150                              # Height of walls
WALL_THICKNESS = 10                            # Thickness of walls
demo_maze_angle = 0.0                          # Camera rotation for intro screen

# ---------------- Player info----------------
player_x, player_y = CELL_SIZE / 2, CELL_SIZE / 2   # Start at center of cell (0,0)
player_angle_deg = 0.0                              # Facing angle
PLAYER_SPEED = 9.0                                  # Movement speed
TURN_SPEED = 4.0                                    # Turn speed (degrees per press)
PLAYER_RADIUS = 9.0                                 # Player collision radius
player_z = PLAYER_RADIUS                            # Player base height
max_health = 150                                    # Max HP
player_health = max_health                          # Current HP
killed_enemies = 0                                  # Kill count
spike_cooldown = 0                                  # Cooldown to avoid repeat spike damage

# ---------------- Game Objects info ----------------
bullets = []                                        # List of Bullet objects
enemies = []                                        # List of Enemy objects

# ---------------- Camera info ----------------
first_person = False                                # View mode flag
cam_radius = 80.0                                   # Third person camera distance
cam_height = 50.0                                   # Third person camera height
current_cam_x, current_cam_y, current_cam_h = 0, 0, 0    # Smoothed camera position/height
current_look_at_x, current_look_at_y = 0, 0              # Smoothed look-at point
CAMERA_SMOOTH_FACTOR = 0.1                          # Smoothing factor for camera
FP_CAM_HEIGHT = 60.0                                 # First person camera height

# ---------------- Game State & Levels ----------------
game_state = "intro_menu"                           # Current state
game_over_message = "You were defeated!"            # Shown when dead
current_level = 1                                   # Level index (1 to 3)
MAZE_WIDTH, MAZE_HEIGHT = 12, 12                    # Default maze size 
MAX_ACTIVE_ENEMIES = 5                              # Max enemies active together
enemies_to_spawn_count = 0                          # Remaining enemies(suppose level 2 te 20 ta enemy thake, but active thake 5 ta kore,jokhon ekta enemy ke mari tokhon remaining enemy theke arekjon active hoy, it's like khelar mathe player out hole arekjon name khelte)

LEVEL_SETTINGS = {                                  # Per-level 
    1: {'size': (8, 8),   'name': 'The Dawn Gardens',       'sky_color': (0.6, 0.7, 0.9, 1.0), 'total_enemies': 10, 'hole_traps': 2, 'spike_traps': 4},
    2: {'size': (12, 12), 'name': 'The Sunstone Labyrinth', 'sky_color': (0.5, 0.7, 1.0, 1.0), 'total_enemies': 20, 'hole_traps': 5, 'spike_traps': 8},
    3: {'size': (15, 15), 'name': 'The Midnight Maze',      'sky_color': (0.05, 0.05, 0.2, 1.0), 'total_enemies': 30, 'hole_traps': 8, 'spike_traps': 12}
}

# --------------- Cheat Mode info -----------------
cheat_mode_active = False                           # Is cheat mode on?
cheat_path = []                                     # Shortest path list for guidance
last_player_grid_pos = (-1, -1)   #player move korle bfs chole to calculate path from player to enemy, ejonno player er last fgrid ta save rakha hoy, jodi dekha jay, last grid same ase it means player move korenai so bfs cholena, but last grid change hoile means player move korse, tokhon bfs chole.
# --------------- Collision -----------------
HOLE_RADIUS = CELL_SIZE / 3.5                       # radius for hole trap
SPIKE_RADIUS = CELL_SIZE / 3.0                      # radius for spikes

def clamp(v, lo, hi):
    """Restricts a value between a minimum and maximum."""
    return max(lo, min(hi, v))                      # value v ranged within 0 to 1

def get_smooth_color(x, y, offset=0):
    """Generates a color based on coordinates for wall variety."""
    r = (math.sin(x * 0.2 + y * 0.1 + offset) + 1) / 2    # 0 to 1 based on sin
    g = (math.sin(x * 0.15 + y * 0.25 + offset + 2) + 1) / 2
    # Bias towards green but with variation
    return 0.3 + ((r + g) / 2) * 0.4                      # Final shade 

def check_collision(x, y):
    """Checks if a point (x, y) collides with a maze wall."""
    grid_x, grid_y = int(x / CELL_SIZE), int(y / CELL_SIZE)         # Convert position to grid
    if not (0 <= grid_x < MAZE_WIDTH and 0 <= grid_y < MAZE_HEIGHT):  # Outside maze?
        return True
    cell = game_maze.grid[grid_x][grid_y]                              # Current cell
    x_in_cell, y_in_cell = x % CELL_SIZE, y % CELL_SIZE                # Local position
    buffer = PLAYER_RADIUS                    # Buffer(a safe distance from walls) from walls
    if cell.walls['N'] and y_in_cell < WALL_THICKNESS + buffer: 
        return True
    if cell.walls['S'] and y_in_cell > CELL_SIZE - (WALL_THICKNESS + buffer): 
        return True
    if cell.walls['W'] and x_in_cell < WALL_THICKNESS + buffer: 
        return True
    if cell.walls['E'] and x_in_cell > CELL_SIZE - (WALL_THICKNESS + buffer): 
        return True
    return False                                                       # Free space

def check_camera_collision(x, y):
    """Checks camera collision with walls, using a smaller buffer for safe movement."""
    grid_x, grid_y = int(x / CELL_SIZE), int(y / CELL_SIZE)
    if not (0 <= grid_x < MAZE_WIDTH and 0 <= grid_y < MAZE_HEIGHT): 
        return True
    cell = game_maze.grid[grid_x][grid_y]
    x_in_cell, y_in_cell = x % CELL_SIZE, y % CELL_SIZE
    buffer = 5.0                                                       
    if cell.walls['N'] and y_in_cell < WALL_THICKNESS + buffer: 
        return True
    if cell.walls['S'] and y_in_cell > CELL_SIZE - (WALL_THICKNESS + buffer): 
        return True
    if cell.walls['W'] and x_in_cell < WALL_THICKNESS + buffer: 
        return True
    if cell.walls['E'] and x_in_cell > CELL_SIZE - (WALL_THICKNESS + buffer): 
        return True
    return False

def get_random_position():
    """Finds a valid unoccupied grid cell far from the player for enemies."""
    while True:
        gx, gy = random.randint(0, MAZE_WIDTH - 1), random.randint(0, MAZE_HEIGHT - 1) # Random cell
        # Avoid start/goal cells for enemy
        if (gx, gy) == (game_maze.start_x, game_maze.start_y) or (gx, gy) == game_maze.goal: continue
        px, py = gx * CELL_SIZE + CELL_SIZE / 2, gy * CELL_SIZE + CELL_SIZE / 2 # Center of cell
        # Ensure enemy location is reasonably far from player
        if math.hypot(px - player_x, py - player_y) > CELL_SIZE * 3:
            return px, py                                    # right spot for enemies

def check_traps():
    """Checks if the player is over a trap cell and applies damage/effects."""
    global game_state, game_over_message, player_health, spike_cooldown
    if cheat_mode_active:
        return                                              # Ignore traps in cheat mode

    grid_x, grid_y = int(player_x / CELL_SIZE), int(player_y / CELL_SIZE) #Player gridposition
    if not (0 <= grid_x < MAZE_WIDTH and 0 <= grid_y < MAZE_HEIGHT): 
        return
    cell = game_maze.grid[grid_x][grid_y]                             # Current cell

    # Calculate distance to make sure trap is within maze/cell center
    cx, cy = grid_x * CELL_SIZE + CELL_SIZE/2, grid_y * CELL_SIZE + CELL_SIZE/2  # Cell center
    dist_from_center = math.hypot(player_x - cx, player_y - cy)       # Distance to center

    # Hole trap check (instant death)
    if cell.has_hole and dist_from_center < HOLE_RADIUS - PLAYER_RADIUS:
        player_health = 0
        game_over_message, game_state = "You fell into a hole!", "game_over"

    # Spike trap check (instant damage in health )
    if cell.has_spikes and dist_from_center < SPIKE_RADIUS - PLAYER_RADIUS and spike_cooldown <= 0:
        player_health -= 15
        player_health = max(0, player_health)
        spike_cooldown = 30                                         
        if player_health == 0:
            game_over_message, game_state = "You ran into the spikes!", "game_over"

# ---------- Game Logic ----------
def fire_bullet():
    """Fires a bullet from the player's position and angle."""
    if game_state == "playing":
        angle_rad = math.radians(player_angle_deg)                  # Player facing radians
        bullet_x = player_x + 12 * math.cos(angle_rad)              # Start slightly forward
        bullet_y = player_y + 12 * math.sin(angle_rad)
        bullets.append(Bullet(bullet_x, bullet_y, player_angle_deg))  # Add to list

def spawn_enemy():
    """Spawns a new enemy at a random valid location."""
    global enemies_to_spawn_count
    if enemies_to_spawn_count <= 0: 
        return                          # No more enemies in waiting list
    ex, ey = get_random_position()                                  # Get spawn spot
    enemies.append(Enemy(ex, ey))                                   # Create enemy
    enemies_to_spawn_count -= 1     #when an enemy dies, Reduce enemy queue/ waiting list

def update_cheat_mode():
    """Recalculates the shortest path for cheat mode guidance."""
    global last_player_grid_pos, cheat_path
    current_grid_pos = (int(player_x / CELL_SIZE), int(player_y / CELL_SIZE))  # Where player is now
    # Only update path if player moves to a new cell 
    if current_grid_pos != last_player_grid_pos:
        if game_maze and game_maze.goal:
            cheat_path = game_maze.find_shortest_path(current_grid_pos, game_maze.goal) # BFS path
        last_player_grid_pos = current_grid_pos

def update_game_logic():
    """Main update cycle for all game entities and collision checks."""
    global bullets, enemies, game_state, game_over_message, killed_enemies, player_health, spike_cooldown

    if cheat_mode_active:
        update_cheat_mode()                                    # Refresh guidance path

    if spike_cooldown > 0:
        spike_cooldown -= 1                                    # make sure no dying

    # Update bullets and remove inactive ones
    for bullet in bullets: bullet.update()                           # Move bullets
    bullets[:] = [b for b in bullets if b.active]                    # Drop inactive

    # Update enemies
    for enemy in enemies: 
        enemy.update()                            

    # Process bullet collisions
    for bullet in list(bullets):                                     
        if not bullet.active: 
            continue
        if not bullet.is_enemy:
            # Player bullet hits enemy
            for enemy in enemies:
                if enemy.active and math.hypot(bullet.x - enemy.x, bullet.y - enemy.y) < enemy.radius + bullet.radius:
                    enemy.active = False                             # Kill enemy
                    bullet.active = False                            # Remove bullet
                    killed_enemies += 1                              # Count kill
                    break
        else:
            # Enemy bullet hits player
            if not cheat_mode_active and math.hypot(bullet.x - player_x, bullet.y - player_y) < PLAYER_RADIUS + bullet.radius:
                player_health -= 10                                  # Damage
                player_health = max(0, player_health)
                bullet.active = False
                if player_health <= 0:                               # Death
                    game_over_message, game_state = "You were shot by an enemy!", "game_over"
                    return

    # Process player collision with active enemies
    for enemy in enemies:
        if not cheat_mode_active and enemy.active and math.hypot(player_x - enemy.x, player_y - enemy.y) < PLAYER_RADIUS + enemy.radius:
            game_over_message, game_state = "You ran into an enemy!", "game_over"
            player_health = 0
            return

    # Process trap collisions
    check_traps()
    if game_state == 'game_over': 
        return

    # when reached max level for calling out enemies from waiting queues
    active_enemy_count = sum(1 for e in enemies if e.active)
    if active_enemy_count < MAX_ACTIVE_ENEMIES and enemies_to_spawn_count > 0:
        spawn_enemy()

# ---------- Game Reset & Level Progression ----------
def start_game(level=1):
    """Initializes all variables for starting a new level."""
    global game_maze, player_x, player_y, player_angle_deg, game_state, player_z
    global MAZE_WIDTH, MAZE_HEIGHT, current_level, bullets, enemies, enemies_to_spawn_count
    global current_cam_x, current_cam_y, current_cam_h, current_look_at_x, current_look_at_y
    global player_health, killed_enemies, spike_cooldown

    current_level = level                                      # Set current level
    level_settings = LEVEL_SETTINGS[current_level]             # Load settings
    MAZE_WIDTH, MAZE_HEIGHT = level_settings['size']           # Override maze size

    # Set lighting and sky color for the level theme
    update_lighting(current_level)                              # Enable/disable lighting
    glClearColor(*level_settings['sky_color'])                  # Background color

    # Generate maze and place player at start position
    game_maze = Maze(MAZE_WIDTH, MAZE_HEIGHT)                   # Build maze
    start_x, start_y = random.randint(0, MAZE_WIDTH-1), random.randint(0, MAZE_HEIGHT-1)  # Random start cell
    game_maze.start_x, game_maze.start_y = start_x, start_y
    player_x, player_y = start_x * CELL_SIZE + CELL_SIZE/2, start_y * CELL_SIZE + CELL_SIZE/2  # Start pos
    player_z, player_angle_deg = PLAYER_RADIUS, 0.0             # Reset height/angle

    # Clear old game objects and prepare enemy spawning queue
    bullets.clear(); 
    enemies.clear()                            # Reset lists
    enemies_to_spawn_count = level_settings['total_enemies']    # Queue enemies
    for _ in range(min(enemies_to_spawn_count, MAX_ACTIVE_ENEMIES)):
        spawn_enemy()                                           # Spawn up to max

    # Calculate goal and place traps
    gx, gy, d = game_maze.compute_goal_from_start(start_x, start_y)  # Furthest as goal
    game_maze.place_traps(start_x, start_y)                          # Put traps

    # Reset camera position and player state
    current_cam_x, current_cam_y, current_cam_h = player_x, player_y, cam_height  # Camera near player
    current_look_at_x, current_look_at_y = player_x, player_y                     # Look at player
    game_state = "playing"                                       # Switch to playing
    player_health = max_health                                   # Full health
    killed_enemies = 0                                           # Reset kills
    spike_cooldown = 0                                           # Reset cooldown

    print(f"--- Starting {level_settings['name']} ---")          # Debug info
    print(f"Total enemies for level: {level_settings['total_enemies']}")
    print(f"New maze generated ({MAZE_WIDTH}x{MAZE_HEIGHT}). Start={(start_x,start_y)}, Goal={(gx, gy)}")

def initialize_intro_scene():
    """Generates a maze purely for background visuals on the main menu."""
    global game_maze
    game_maze = Maze(MAZE_WIDTH, MAZE_HEIGHT)                    # Build maze for menu

# --------------- Lighting -----------------
def update_lighting(level):
    """Sets up lighting conditions based on the level theme."""
    if level == 3:                                               # Only level 3 uses lighting
        glEnable(GL_LIGHTING); 
        glEnable(GL_LIGHT0)               # Turn on lighting and light
        light_pos = [0, 0, 200, 1]                               # positional light
        light_ambient = [0.2, 0.2, 0.3, 1.0]                     # Soft ambient color
        light_diffuse = [0.8, 0.8, 0.7, 1.0]                     # Diffuse color
        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)             # Apply position
        glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)          # Apply ambient
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)          # Apply diffuse
    else:                                                        # Levels 1 and 2 are bright (no lighting)
        glDisable(GL_LIGHTING)

# --------------- Drawing (Scene) -----------------
def draw_pyramid():
    """Helper function to draw a simple pyramid that is used for spike traps."""
    base = 10                                      # Half width of base square
    height = 40                                    # Height of pyramid
    glBegin(GL_TRIANGLE_FAN)                       # Fan from apex to base vertices
    glVertex3f(0, 0, height)                       # Apex
    glVertex3f(-base, -base, 0)                    # Base corner 1
    glVertex3f(base, -base, 0)                     # Base corner 2
    glVertex3f(base, base, 0)                      # Base corner 3
    glVertex3f(-base, base, 0)                     # Base corner 4
    glVertex3f(-base, -base, 0)                    # Close fan back to first base corner
    glEnd()

def draw_cheat_path():
    """Draws the precalculated shortest path line on the ground for cheat mode."""
    if not cheat_path: 
        return                       # Nothing to draw

    was_lit = glIsEnabled(GL_LIGHTING)              # Remember if lighting was on
    if was_lit: 
        glDisable(GL_LIGHTING)                      # Disable for solid color line

    glColor3f(0.0, 1.0, 1.0)                        # Cyan color
    glLineWidth(5.0)                                # Thicker line for visibility

    glBegin(GL_LINE_STRIP)                          # Connect points in order
    for (gx, gy) in cheat_path:
        glVertex3f(gx * CELL_SIZE + CELL_SIZE/2,gy * CELL_SIZE + CELL_SIZE/2,
        2.0)                             
    glEnd()
    glLineWidth(1.0)                                # Reset line width
    if was_lit: 
        glEnable(GL_LIGHTING)                       # Restore lighting if it was on

def draw_3d_scene():
    """drawing function for 3D elements."""
    draw_ground()                                   # Ground plane
    if game_maze:
        draw_maze()                                 # Maze walls
        if game_state in ["playing", "level_complete", "game_over"]:
            if cheat_mode_active:
                draw_cheat_path()                   # Path overlay
            draw_goal(); 
            draw_player(); 
            draw_traps()                            # Portal/player/traps
            for enemy in enemies: 
                enemy.draw()      # Enemies
            for bullet in bullets: 
                bullet.draw()    # Bullets

def draw_ground():
    """Draws a large ground."""
    glColor3f(0.55, 0.4, 0.25)                       # Brown dirt color
    ground_size = 10000                              
    glBegin(GL_QUADS)
    glVertex3f(-ground_size, -ground_size, -0.1)    
    glVertex3f( ground_size, -ground_size, -0.1)
    glVertex3f( ground_size,  ground_size, -0.1)
    glVertex3f(-ground_size,  ground_size, -0.1)
    glEnd()

def draw_wall(x1, y1, x2, y2, green_shade):
    """Draws a single wall segment as a scaled cube."""
    glColor3f(0.1, green_shade, 0.1)                # Wall color 
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2     # Segment midpoint
    length = math.hypot(x2 - x1, y2 - y1)           # Segment length
    glPushMatrix(); 
    glTranslatef(mid_x, mid_y, WALL_HEIGHT / 2)   # Move to center,raise by half height
    if abs(x1 - x2) > abs(y1 - y2):                 # Horizontal wall
        glScalef(length + WALL_THICKNESS, WALL_THICKNESS, WALL_HEIGHT)  # Scale X by length
    else:                                           # Vertical wall
        glScalef(WALL_THICKNESS, length + WALL_THICKNESS, WALL_HEIGHT)  # Scale Y by length
    glutSolidCube(1); 
    glPopMatrix()                 

def draw_maze():
    """Iterates through maze cells and draws all existing walls."""
    if not game_maze: 
        return
    for x in range(MAZE_WIDTH):
        for y in range(MAZE_HEIGHT):
            cell = game_maze.grid[x][y]                       # Current cell
            x_pos, y_pos = x * CELL_SIZE, y * CELL_SIZE       # base coords
            if cell.walls['N']:                               # North edge
                draw_wall(x_pos, y_pos, x_pos + CELL_SIZE, y_pos, cell.wall_colors['N'])
            if cell.walls['W']:                               # West edge
                draw_wall(x_pos, y_pos, x_pos, y_pos + CELL_SIZE, cell.wall_colors['W'])
    # Draw outer boundary walls to ensure maze is enclosed
    for x in range(MAZE_WIDTH):
        color = game_maze.grid[x][MAZE_HEIGHT - 1].wall_colors['S']     # Bottom edge color
        draw_wall(x*CELL_SIZE, MAZE_HEIGHT*CELL_SIZE, (x+1)*CELL_SIZE, MAZE_HEIGHT*CELL_SIZE, color)
    for y in range(MAZE_HEIGHT):
        color = game_maze.grid[MAZE_WIDTH - 1][y].wall_colors['E']       # Right edge color
        draw_wall(MAZE_WIDTH*CELL_SIZE, y*CELL_SIZE, MAZE_WIDTH*CELL_SIZE, (y+1)*CELL_SIZE, color)

def draw_traps():
    """Draws hole and spike traps."""
    if not game_maze: 
        return
    for x in range(MAZE_WIDTH):
        for y in range(MAZE_HEIGHT):
            cell = game_maze.grid[x][y]
            cx, cy = x*CELL_SIZE + CELL_SIZE/2, y*CELL_SIZE + CELL_SIZE/2  # Cell center

            if cell.has_hole:
                # Draw hole as a dark circle on the ground
                glPushMatrix(); 
                glColor3f(0.1, 0.1, 0.1); 
                glTranslatef(cx, cy, 0.1)
                glBegin(GL_TRIANGLE_FAN)
                glVertex3f(0, 0, 0)                            # Center
                for i in range(21):                            # 20 segments circle
                    angle = 2 * math.pi * i / 20
                    glVertex3f(math.cos(angle) * HOLE_RADIUS,
                               math.sin(angle) * HOLE_RADIUS, 0)
                glEnd(); 
                glPopMatrix()

            if cell.has_spikes:
                # Draw spikes using pyramids
                glPushMatrix()
                glTranslatef(cx, cy, 0)

                # Large central spike
                glPushMatrix()
                glColor3f(0.6, 0.6, 0.7)                      # grey color
                glScalef(1.1, 1.1, 1.3)                       
                draw_pyramid()
                glPopMatrix()

                # Smaller surrounding spikes with random rotations
                glColor3f(0.5, 0.5, 0.55)                     # darker gray
                small_spike_positions = [(25, 20), (-25, 25), (15, -25), (-20, -15)]
                if len(cell.spike_rotations) == len(small_spike_positions):
                    for i, (sx, sy) in enumerate(small_spike_positions):
                        glPushMatrix()
                        glTranslatef(sx, sy, 0)                      # Offset position
                        glRotatef(cell.spike_rotations[i], 0, 0, 1)  # Random rotation
                        draw_pyramid()
                        glPopMatrix()
                glPopMatrix()

def draw_player():
    """Draws the player in third person view."""
    if first_person: 
        return                                            # Hidden in 1st person
    glPushMatrix()
    # If game over, make player fall over
    if game_state == "game_over":
        glTranslatef(player_x, player_y, 0)                # Move to player position
        glRotatef(90, 0, 1, 0)                             # Tip over on side
    else:
        glTranslatef(player_x, player_y, 0)                # Normal position
        glRotatef(player_angle_deg, 0, 0, 1)               # Face facing direction

    glRotatef(-90, 0, 0, 1); 
    glScalef(0.6, 0.6, 0.6)       # Adjust base size
    # Body (Torso) 
    glPushMatrix(); 
    glTranslatef(0, 0, 40); 
    glColor3f(0.0, 0.0, 0.50); 
    glScalef(1.4, 1.0, 2.0); 
    glutSolidCube(25); 
    glPopMatrix()
    # Head
    glPushMatrix(); 
    glTranslatef(0, 0, 80); 
    glColor3f(0.0, 0.0, 0.0); 
    gluSphere(gluNewQuadric(), 15, 16, 16); 
    glPopMatrix()
    # Arms
    glPushMatrix(); 
    glTranslatef(-20, 0, 55); 
    glRotatef(-90, 1, 0, 0); 
    glColor3f(0.96, 0.8, 0.69); 
    gluCylinder(gluNewQuadric(), 9, 5, 30, 10, 10); 
    glPopMatrix()
    glPushMatrix(); 
    glTranslatef(20, 0, 55); 
    glRotatef(-90, 1, 0, 0); 
    glColor3f(0.96, 0.8, 0.69); 
    gluCylinder(gluNewQuadric(), 9, 5, 30, 10, 10); 
    glPopMatrix()
    # Gun Barrel
    glPushMatrix(); 
    glTranslatef(0, 10, 55); 
    glRotatef(-90, 1, 0, 0); 
    glColor3f(0.66, 0.66, 0.66); 
    gluCylinder(gluNewQuadric(), 8, 6, 40, 10, 10); 
    glPopMatrix()
    # Legs
    glPushMatrix(); 
    glTranslatef(-12, 0, 15); 
    glRotatef(180, 1, 0, 0); 
    glColor3f(0.0, 0.0, 0.0); 
    gluCylinder(gluNewQuadric(), 8, 5, 50, 10, 10); 
    glPopMatrix()
    glPushMatrix(); 
    glTranslatef(12, 0, 15); 
    glRotatef(180, 1, 0, 0); 
    glColor3f(0.0, 0.0, 0.0); 
    gluCylinder(gluNewQuadric(), 8, 5, 50, 10, 10); 
    glPopMatrix()
    glPopMatrix()

def draw_goal():
    """Draws the exit structure."""
    if not game_maze or not game_maze.goal: 
        return
    gx, gy = game_maze.goal                                 # Goal grid coords
    cx, cy = gx*CELL_SIZE + CELL_SIZE/2, gy*CELL_SIZE + CELL_SIZE/2  # Center of goal cell
    glPushMatrix(); 
    glTranslatef(cx, cy, 0)                 # Move to goal

    # Base platform
    glColor3f(0.95, 0.85, 0.2); 
    glPushMatrix(); 
    glTranslatef(0, 0, 6); 
    glScalef(40, 40, 12); 
    glutSolidCube(1); 
    glPopMatrix()
    # Arch uprights
    glColor3f(0.2, 0.8, 0.2); 
    glPushMatrix(); 
    glTranslatef(-16, 0, 70); 
    glScalef(12, 12, 140); 
    glutSolidCube(1); 
    glPopMatrix()
    glPushMatrix(); 
    glTranslatef(16, 0, 70); 
    glScalef(12, 12, 140); 
    glutSolidCube(1); 
    glPopMatrix()
    # Arch top beam
    glColor3f(0.2, 0.6, 0.9); 
    glPushMatrix(); 
    glTranslatef(0, 0, 140); 
    glScalef(44, 12, 12); 
    glutSolidCube(1); 
    glPopMatrix()
    glPopMatrix()

# --------------- Drawing (UI Menus) -----------------
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    """text at specified 2D screen coordinates."""
    glRasterPos2f(x, y)                                   # Set start position
    for char in text: 
        glutBitmapCharacter(font, ord(char))  # Draw each char

def draw_ui_overlay(draw_content_func):
    """Sets up 2D ortho projection and draws a semi-transparent background for menus."""
    glMatrixMode(GL_PROJECTION); 
    glPushMatrix(); 
    glLoadIdentity()   
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)                            # 2D screen coords
    glMatrixMode(GL_MODELVIEW); 
    glPushMatrix(); 
    glLoadIdentity(); 
    glDisable(GL_DEPTH_TEST)  

    # Dark overlay background
    glEnable(GL_BLEND); 
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)              # Enable transparency
    glColor4f(0, 0, 0, 0.6);                                         # Black with alpha
    glBegin(GL_QUADS); 
    glVertex2f(0,0); 
    glVertex2f(WINDOW_W,0); 
    glVertex2f(WINDOW_W,WINDOW_H); 
    glVertex2f(0,WINDOW_H); 
    glEnd()  
    glDisable(GL_BLEND)                                            # Turn off blending

    # Draw specific menu content
    draw_content_func()                                            # Call provided drawer

    # Restore 3D projection settings
    glEnable(GL_DEPTH_TEST); 
    glMatrixMode(GL_PROJECTION); 
    glPopMatrix(); 
    glMatrixMode(GL_MODELVIEW); 
    glPopMatrix()  

def draw_styled_button(x, y, w, h, text, font=GLUT_BITMAP_HELVETICA_18):
    """Draws a standard UI button with background, border, and centered text."""
    # Button fill
    glEnable(GL_BLEND); 
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)  # Transparency for fill
    glColor4f(0.15, 0.15, 0.18, 0.75); 
    glBegin(GL_QUADS); 
    glVertex2f(x,y); 
    glVertex2f(x+w,y); 
    glVertex2f(x+w,y+h); 
    glVertex2f(x,y+h); 
    glEnd()
    glDisable(GL_BLEND)
    # Button border
    glColor3f(0.6, 0.7, 0.8); 
    glLineWidth(2.0); 
    glBegin(GL_LINE_LOOP); 
    glVertex2f(x,y); 
    glVertex2f(x+w,y); 
    glVertex2f(x+w,y+h); 
    glVertex2f(x,y+h); 
    glEnd(); 
    glLineWidth(1.0)
    # Button text (centered)
    text_width = sum(glutBitmapWidth(font, ord(c)) for c in text) # text width
    glColor3f(1, 1, 1); 
    draw_text(x + (w - text_width)/2, y + (h - 18)/2 + 5, text, font)  # Centered draw

def draw_intro_menu():
    """Content for the main menu screen."""
    def content():
        title_font = GLUT_BITMAP_TIMES_ROMAN_24
        title = "THE FINAL DOOR"; tw = sum(glutBitmapWidth(title_font, ord(c)) for c in title)  # Title width
        glColor3f(0.95,0.85,0.2); 
        draw_text(WINDOW_W/2 - tw/2, WINDOW_H - 150, title, title_font)  # Center title
        sub = "An Amazing Maze Adventure"; 
        sw = sum(glutBitmapWidth(GLUT_BITMAP_HELVETICA_18, ord(c)) for c in sub)  # Subtitle width
        glColor3f(0.8,0.8,0.8); 
        draw_text(WINDOW_W/2 - sw/2, WINDOW_H - 185, sub)                 # Center subtitle

        btn_y, btn_w, btn_h, btn_x = WINDOW_H/2 + 30, 250, 50, WINDOW_W/2 - 125                   
        draw_styled_button(btn_x, btn_y, btn_w, btn_h, "Play Game")
        draw_styled_button(btn_x, btn_y - 70, btn_w, btn_h, "Select Level")
        draw_styled_button(btn_x, btn_y - 140, btn_w, btn_h, "Quit")
    draw_ui_overlay(content)                                                                  # Draw overlay + content

def draw_level_select_menu():
    """Content for the level selection screen."""
    def content():
        glColor3f(1, 0.9, 0.2); draw_text(WINDOW_W/2-90, WINDOW_H-150, "SELECT LEVEL", GLUT_BITMAP_TIMES_ROMAN_24)  # Title
        btn_y = WINDOW_H/2 + 50
        buttons = [                                                                          
            (WINDOW_W/2-150, btn_y, 300, 50, LEVEL_SETTINGS[1]['name']),
            (WINDOW_W/2-150, btn_y-70, 300, 50, LEVEL_SETTINGS[2]['name']),
            (WINDOW_W/2-150, btn_y-140, 300, 50, LEVEL_SETTINGS[3]['name']), # Level buttons
            (WINDOW_W/2-150, btn_y-210, 300, 50, "Back")
        ]
        for x, y, w, h, text in buttons: 
            draw_styled_button(x, y, w, h, text)                       # Draw each button
    draw_ui_overlay(content)

def draw_level_complete_menu():
    """Content for the victory screen."""
    def content():
        if current_level<3:
            title = "LEVEL COMPLETE!" 
        else:
            "CONGRATULATIONS!"                         # Title changes after last level
        if current_level<3:
            sub = "You found the exit!" 
        else:
            "You have escaped the labyrinth!"
        glColor3f(1,0.9,0.2); 
        draw_text(WINDOW_W/2 - 100, WINDOW_H - 200, title, GLUT_BITMAP_TIMES_ROMAN_24)
        glColor3f(0.9,0.9,0.9); 
        draw_text(WINDOW_W/2 - 80, WINDOW_H - 240, sub)

        btn_y = WINDOW_H/2 - 50
        if current_level < 3: 
            draw_styled_button(WINDOW_W/2-100, btn_y, 200, 50, "Next Level")
        else: 
            draw_styled_button(WINDOW_W/2-100, btn_y, 200, 50, "Play Again?")
        draw_styled_button(WINDOW_W/2-100, btn_y-70, 200, 50, "Back to Main Menu")
    draw_ui_overlay(content)

def draw_game_over_menu():
    """Content for the game over screen."""
    def content():
        glColor3f(1,0.2,0.2); 
        draw_text(WINDOW_W/2-80, WINDOW_H-200, "GAME OVER!", GLUT_BITMAP_TIMES_ROMAN_24)  # Red title
        msg_w = sum(glutBitmapWidth(GLUT_BITMAP_HELVETICA_18, ord(c)) for c in game_over_message)               # Center message
        glColor3f(0.9,0.9,0.9); 
        draw_text(WINDOW_W/2-msg_w/2, WINDOW_H-240, game_over_message)

        btn_y = WINDOW_H/2 - 50
        draw_styled_button(WINDOW_W/2-100, btn_y, 200, 50, "Restart Level")
        draw_styled_button(WINDOW_W/2-100, btn_y-70, 200, 50, "Back to Main Menu")
        draw_styled_button(WINDOW_W/2-100, btn_y-140, 200, 50, "Quit Game")
    draw_ui_overlay(content)

def draw_hud():
    """Draws in game elements like health bar and crosshair."""
    glMatrixMode(GL_PROJECTION)                                  # Switch to projection
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)                         # Set 2D screen coordinates
    glMatrixMode(GL_MODELVIEW)                                   # Switch to modelview
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)                                     

    # Health text
    glColor3f(1, 1, 1)
    draw_text(20, WINDOW_H - 30, "Health:")                      # Label

    # Health bar properties
    bar_x = 100; bar_y = WINDOW_H - 35; bar_w = 200; bar_h = 20  

    # Health bar outline
    glColor3f(1, 1, 1)
    glBegin(GL_LINE_LOOP)                                        # Rectangle outline
    glVertex2f(bar_x, bar_y)
    glVertex2f(bar_x + bar_w, bar_y)
    glVertex2f(bar_x + bar_w, bar_y + bar_h)
    glVertex2f(bar_x, bar_y + bar_h)
    glEnd()

    # Health bar fill (color changes based on health percentage)
    if player_health > 0:
        fill_w = (player_health / max_health) * bar_w         # Fill width proportional to HP
        if player_health > (max_health * 0.66):
            glColor3f(0, 1, 0)                                   # green
        elif player_health > (max_health * 0.33):
            glColor3f(1, 1, 0)                                   # yellow
        else:
            glColor3f(1, 0, 0)                                   # red
        glBegin(GL_QUADS)                                        # Filled bar
        glVertex2f(bar_x, bar_y)
        glVertex2f(bar_x + fill_w, bar_y)
        glVertex2f(bar_x + fill_w, bar_y + bar_h)
        glVertex2f(bar_x, bar_y + bar_h)
        glEnd()

    # Enemies killed counter
    glColor3f(1, 1, 1)
    draw_text(20, WINDOW_H - 60, f"Enemies Killed: {killed_enemies}")  # Show kills

    # --- Crosshair Drawing ---
    # Draw crosshair only in first person mode and when actively playing.
    if first_person and game_state == "playing":
        crosshair_vertical_offset = 30                     # Adjust crosshair position
        center_x = WINDOW_W / 2
        center_y = (WINDOW_H / 2.2) - crosshair_vertical_offset  
        crosshair_size = 12                                # Half length of lines

        glColor3f(1.0, 1.0, 1.0)                           # White color
        glLineWidth(2.0)
        # Horizontal line
        glBegin(GL_LINES)
        glVertex2f(center_x - crosshair_size, center_y)
        glVertex2f(center_x + crosshair_size, center_y)
        glEnd()
        # Vertical line
        glBegin(GL_LINES)
        glVertex2f(center_x, center_y - crosshair_size)
        glVertex2f(center_x, center_y + crosshair_size)
        glEnd()
        glLineWidth(1.0)                                   # Reset line width

    # Restore OpenGL state
    glEnable(GL_DEPTH_TEST)                                
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

# --------------- Camera -----------------
def setup_player_camera():
    """Configures the camera based on first person or third person view."""
    global current_cam_x, current_cam_y, current_cam_h, current_look_at_x, current_look_at_y
    if first_person:
        # --- First Person Camera ---
        look_x = player_x + 100 * math.cos(math.radians(player_angle_deg))  # Look point x
        look_y = player_y + 100 * math.sin(math.radians(player_angle_deg))  # Look point y
        gluLookAt(player_x, player_y, FP_CAM_HEIGHT,                        # Eye position
                  look_x, look_y, FP_CAM_HEIGHT,                            # Center/look-at
                  0, 0, 1)                                                  
    else:
        # --- Third Person Camera ---
        angle_rad = math.radians(player_angle_deg)                          # Player angle
        ideal_cam_x = player_x - cam_radius * math.cos(angle_rad)           # Target cam pos (behind player)
        ideal_cam_y = player_y - cam_radius * math.sin(angle_rad)
        target_cam_x, target_cam_y = ideal_cam_x, ideal_cam_y               # Defaults

        # Camera collision detection: 
        for i in range(1, 21):
            t = i / 20.0                                                    
            check_x = player_x * (1 - t) + ideal_cam_x * t                  # Step along line
            check_y = player_y * (1 - t) + ideal_cam_y * t

            if check_camera_collision(check_x, check_y):                    # Hits wall?
                # Collision detected, move camera to safe position just before collision point
                t_safe = (i - 1) / 20.0
                min_dist_factor = 0.2                            # Keep minimum distance
                if t_safe < min_dist_factor: 
                    t_safe = min_dist_factor
                target_cam_x = player_x * (1 - t_safe) + ideal_cam_x * t_safe
                target_cam_y = player_y * (1 - t_safe) + ideal_cam_y * t_safe
                break

        # Apply smoothing to camera movement for a less blend feel
        current_cam_x += (target_cam_x - current_cam_x) * CAMERA_SMOOTH_FACTOR
        current_cam_y += (target_cam_y - current_cam_y) * CAMERA_SMOOTH_FACTOR
        current_cam_h += (cam_height - current_cam_h) * CAMERA_SMOOTH_FACTOR
        current_look_at_x += (player_x - current_look_at_x) * CAMERA_SMOOTH_FACTOR
        current_look_at_y += (player_y - current_look_at_y) * CAMERA_SMOOTH_FACTOR
        gluLookAt(current_cam_x, current_cam_y, current_cam_h,              # Smoothed eye
                  current_look_at_x, current_look_at_y, PLAYER_RADIUS + 20, # Smoothed center
                  0, 0, 1)                                                  # Up vector

def setup_demo_camera():
    """Configures a rotating overhead camera for the main menu screen."""
    center_x, center_y = (MAZE_WIDTH*CELL_SIZE)/2, (MAZE_HEIGHT*CELL_SIZE)/2   # Maze center
    radius = (MAZE_WIDTH * CELL_SIZE) * 0.8                                    # Orbit radius
    cam_x = center_x + radius * math.cos(math.radians(demo_maze_angle))  # Camera x on circle
    cam_y = center_y + radius * math.sin(math.radians(demo_maze_angle))  # Camera y on circle
    gluLookAt(cam_x, cam_y, WALL_HEIGHT*4,                               # High overhead eye
              center_x, center_y, 0,                                     # Look at center
              0, 0, 1)                                                   # Up vector

# --------------- Input & Game Logic -----------------
def keyboardListener(key, x, y):
    """Handles standard keyboard input for movement and cheats."""
    global player_x, player_y, player_angle_deg, cheat_mode_active, last_player_grid_pos

    if key == b'c':
        cheat_mode_active = not cheat_mode_active                           # Toggle cheat
        if cheat_mode_active:
            print("CHEAT MODE: ACTIVATED (Infinite Health, Path Guidance)")
            last_player_grid_pos = (-1, -1)                                 # Force update
            update_cheat_mode()
        else:
            print("CHEAT MODE: DEACTIVATED")
            cheat_path.clear()                                              # Clear guidance
        return

    if key == b'r':
        start_game(current_level)                                           # Restart level
        return

    if game_state != "playing":
        return                                          # Ignore inputs in menus while playing

    angle_rad = math.radians(player_angle_deg)                            # Facing angle
    next_x, next_y = player_x, player_y                                   # Candidate pos

    # Calculate movement direction based on key press
    if key == b'w':                                                       # Forward
        next_x += math.cos(angle_rad) * PLAYER_SPEED
        next_y += math.sin(angle_rad) * PLAYER_SPEED
    elif key == b's':                                                     # Backward
        next_x -= math.cos(angle_rad) * PLAYER_SPEED
        next_y -= math.sin(angle_rad) * PLAYER_SPEED

    if key == b'a':                                                       # Turn left
        player_angle_deg += TURN_SPEED
    elif key == b'd':                                                     # Turn right
        player_angle_deg -= TURN_SPEED

    # Apply movement only if collision check passes
    if not check_collision(next_x, next_y):
        player_x, player_y = next_x, next_y                               # Commit move

def specialKeyListener(key, x, y):
    """Handles special key input (arrow keys) for camera zoom/height adjustment."""
    global cam_height, cam_radius

    # ----Only allow special keys if cheat mode is active ---
    if not cheat_mode_active:
        return                              # Do nothing if cheat mode is off

    # Existing logic to prevent camera controls in certain states
    if game_state != "playing" or first_person: 
        return

    # Camera control logic (only reachable if cheat_mode_active is True)
    if key == GLUT_KEY_UP: 
        cam_height = clamp(cam_height + 10, 50, 800)        # Raise camera
    elif key == GLUT_KEY_DOWN: 
        cam_height = clamp(cam_height - 10, 50, 800)    # Lower camera
    elif key == GLUT_KEY_LEFT: 
        cam_radius = clamp(cam_radius + 20, 80, 1200)   # Zoom out
    elif key == GLUT_KEY_RIGHT: 
        cam_radius = clamp(cam_radius - 20, 80, 1200)  # Zoom in


def mouseListener(button, state, x, y):
    """Handles mouse input for firing,camera toggle,and menu interaction."""
    global first_person, game_state

    # --- In-Game Actions ---
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and game_state == "playing":
        fire_bullet()                                              # Shoot
        return
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN and game_state == "playing":
        first_person = not first_person                            # Toggle 1st/3rd person
        return

    # --- Menu Button Clicks ---
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        gl_y = WINDOW_H - y                                        # Convert to OpenGL Y

        if game_state == "intro_menu":
            btn_y, btn_w, btn_h, btn_x = WINDOW_H/2+30, 250, 50, WINDOW_W/2-125
            if btn_x < x < btn_x+btn_w:
                if btn_y < gl_y < btn_y+btn_h: 
                    start_game(1)                    # Play Game
                elif btn_y-70 < gl_y < btn_y-70+btn_h: 
                    game_state = "level_select" #Select Level
                elif btn_y-140 < gl_y < btn_y-140+btn_h: 
                    glutLeaveMainLoop()    # Quit

        elif game_state == "level_select":
            btn_y = WINDOW_H/2 + 50
            if WINDOW_W/2-150 < x < WINDOW_W/2+150:
                if btn_y < gl_y < btn_y+50: 
                    start_game(1)                       # Level 1
                elif btn_y-70 < gl_y < btn_y-20: 
                    start_game(2)                  # Level 2
                elif btn_y-140 < gl_y < btn_y-90: 
                    start_game(3)                 # Level 3
                elif btn_y-210 < gl_y < btn_y-160: 
                    game_state = "intro_menu"    # Back

        elif game_state == "level_complete":
            btn_y = WINDOW_H/2 - 50
            if WINDOW_W/2-100 < x < WINDOW_W/2+100:
                if current_level<3 and btn_y < gl_y < btn_y+50: 
                    start_game(current_level+1)     # Next Level
                elif current_level==3 and btn_y < gl_y < btn_y+50: 
                    start_game(1)                # Play Again?
                if btn_y-70 < gl_y < btn_y-20: 
                    initialize_intro_scene(); 
                    game_state = "intro_menu" # Back

        elif game_state == "game_over":
            btn_y = WINDOW_H/2 - 50
            if WINDOW_W/2-100 < x < WINDOW_W/2+100:
                if btn_y < gl_y < btn_y+50: 
                    start_game(current_level)            # Restart Level
                elif btn_y-70 < gl_y < btn_y-20: 
                    initialize_intro_scene(); 
                    game_state = "intro_menu" # Back
                elif btn_y-140 < gl_y < btn_y-90: 
                    glutLeaveMainLoop()            # Quit Game

def check_win_condition():
    """Checks if the player has reached the goal cell."""
    global game_state
    if game_state != "playing" or not game_maze.goal: 
        return                    # Only during play
    gx, gy = game_maze.goal
    goal_pos_x, goal_pos_y = gx*CELL_SIZE + CELL_SIZE/2, gy*CELL_SIZE + CELL_SIZE/2  # Goal center
    distance = math.hypot(player_x - goal_pos_x, player_y - goal_pos_y)    # Distance to goal

    if distance < PLAYER_RADIUS + 20:                               # Close enough?
        game_state = "level_complete"                               # Win!
        print("Level Complete!")

# --------------- Main Loop -----------------
def showScreen():
    """Main  callback function."""
    global demo_maze_angle
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)          # Clear frame + depth

    # Setup 3D perspective projection
    glMatrixMode(GL_PROJECTION); 
    glLoadIdentity()               # Reset projection
    gluPerspective(60.0, WINDOW_W / float(WINDOW_H), 1.0, 20000.0)  
    glMatrixMode(GL_MODELVIEW); 
    glLoadIdentity()                # Reset modelview

    # State machine for rendering logic
    if game_state == "playing":
        update_game_logic()                                     # Update entities & collisions
        check_win_condition()                                   # Check goal
        setup_player_camera()                                   # Position camera
        draw_3d_scene()                                         # Draw scene
    elif game_state == "level_complete":
        setup_player_camera(); 
        draw_3d_scene(); 
        draw_level_complete_menu()  
    elif game_state == "game_over":
        setup_player_camera(); 
        draw_3d_scene(); 
        draw_game_over_menu()       
    else: # Menu states (intro_menu, level_select)
        demo_maze_angle += 0.05                                 # Slowly rotate camera
        setup_demo_camera(); 
        draw_3d_scene()                    # Show maze game in background
        if game_state == "intro_menu": 
            draw_intro_menu()        # Main menu
        elif game_state == "level_select": 
            draw_level_select_menu()  # Level pick

    # Draw HUD overlay on top of game scene when playing or game ended
    if game_state in ["playing", "level_complete", "game_over"]:
        draw_hud()                                              # Health, crosshair, kills

    glutSwapBuffers()                                           # Display the frame

def main():
    """Initialization and entry point for the application."""
    glutInit(sys.argv)                                          
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)    # Double buffer, color, depth
    glutInitWindowSize(WINDOW_W, WINDOW_H)                      # Window size
    glutCreateWindow(b"The Final Door - Maze Adventure")        # Create window with title

    # Basic OpenGL setup
    glClearColor(*LEVEL_SETTINGS[1]['sky_color'])               # Default sky color
    glEnable(GL_COLOR_MATERIAL)                                 # Enable color in objects
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)  # Use color for ambient+diffuse
    glEnable(GL_DEPTH_TEST)                                     # Enable depth buffer

    # Generate initial maze for menu background before starting game loop
    initialize_intro_scene()                                    # Build menu maze

    # Register callbacks
    glutDisplayFunc(showScreen)                                 # Draw callback
    glutIdleFunc(showScreen)                                    # Continuous redraw
    glutKeyboardFunc(keyboardListener)                          # Keyboard input
    glutSpecialFunc(specialKeyListener)                         # Arrow keys
    glutMouseFunc(mouseListener)                                # Mouse input

    # Start the application loop
    glutMainLoop()                                              # Hand over to GLUT

if __name__ == "__main__":
    main()                                                      # Run the game
