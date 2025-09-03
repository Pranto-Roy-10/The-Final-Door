from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

# ----------------- Maze Generation Classes -----------------
class Cell:
    """
    Represents a single cell in the maze grid.
    Each cell has walls on all four sides initially.
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.walls = {'N': True, 'S': True, 'E': True, 'W': True}
        self.visited = False

class Maze:
    """
    A class to generate and hold the maze data.
    Uses a recursive backtracking algorithm.
    """
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[Cell(x, y) for y in range(height)] for x in range(width)]
        self.generate()

    def get_cell(self, x, y):
        """Gets a cell at a given coordinate."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[x][y]
        return None

    def get_neighbors(self, cell):
        """Finds all unvisited neighbors of a cell."""
        neighbors = []
        if cell.y > 0 and not self.grid[cell.x][cell.y - 1].visited:
            neighbors.append(self.grid[cell.x][cell.y - 1])
        if cell.y < self.height - 1 and not self.grid[cell.x][cell.y + 1].visited:
            neighbors.append(self.grid[cell.x][cell.y + 1])
        if cell.x < self.width - 1 and not self.grid[cell.x + 1][cell.y].visited:
            neighbors.append(self.grid[cell.x + 1][cell.y])
        if cell.x > 0 and not self.grid[cell.x - 1][cell.y].visited:
            neighbors.append(self.grid[cell.x - 1][cell.y])
        return neighbors

    def remove_walls(self, current_cell, next_cell):
        dx = current_cell.x - next_cell.x
        dy = current_cell.y - next_cell.y
        if dx == 1:
            current_cell.walls['W'], next_cell.walls['E'] = False, False
        elif dx == -1:
            current_cell.walls['E'], next_cell.walls['W'] = False, False
        if dy == 1:
            current_cell.walls['N'], next_cell.walls['S'] = False, False
        elif dy == -1:
            current_cell.walls['S'], next_cell.walls['N'] = False, False

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

# ---------------- Window & Scene ----------------
WINDOW_W, WINDOW_H = 1200, 900
game_maze = None
MAZE_WIDTH = 15
MAZE_HEIGHT = 15
CELL_SIZE = 100
WALL_HEIGHT = 150
WALL_THICKNESS = 10

# ---------------- Player ----------------
player_x, player_y = CELL_SIZE / 2, CELL_SIZE / 2
player_angle_deg = 0.0
PLAYER_SPEED = 5.0
TURN_SPEED = 4.0
PLAYER_RADIUS = 15.0

# ---------------- Camera ----------------
first_person = False
# 3rd person camera
cam_radius = 300.0 # Distance from player
cam_height = 150.0 # Height above player
# 1st person camera
FP_CAM_HEIGHT = 60.0

# ---------------- Game State ----------------
game_over = False

# --------------- Utility & Collision -----------------
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def check_collision(x, y):
    """Checks if a point (x,y) is inside a wall."""
    grid_x = int(x / CELL_SIZE)
    grid_y = int(y / CELL_SIZE)
    
    if not (0 <= grid_x < MAZE_WIDTH and 0 <= grid_y < MAZE_HEIGHT):
        return True # Out of bounds is a collision

    cell = game_maze.grid[grid_x][grid_y]
    
    # Check against the four walls of the current cell
    x_in_cell = x % CELL_SIZE
    y_in_cell = y % CELL_SIZE
    
    buffer = PLAYER_RADIUS / 2 # Add a small buffer for collision
    if cell.walls['N'] and y_in_cell < WALL_THICKNESS + buffer: return True
    if cell.walls['S'] and y_in_cell > CELL_SIZE - (WALL_THICKNESS + buffer): return True
    if cell.walls['W'] and x_in_cell < WALL_THICKNESS + buffer: return True
    if cell.walls['E'] and x_in_cell > CELL_SIZE - (WALL_THICKNESS + buffer): return True

    return False

def reset_game():
    """Resets the game state and generates a new maze."""
    global game_maze, player_x, player_y, player_angle_deg
    game_maze = Maze(MAZE_WIDTH, MAZE_HEIGHT)
    # Place player in a random open cell
    start_x = random.randint(0, MAZE_WIDTH - 1)
    start_y = random.randint(0, MAZE_HEIGHT - 1)
    player_x = start_x * CELL_SIZE + CELL_SIZE / 2
    player_y = start_y * CELL_SIZE + CELL_SIZE / 2
    player_angle_deg = 0.0
    print("New maze generated. Player reset.")

# --------------- Drawing -----------------
def draw_ground():
    glColor3f(0.55, 0.4, 0.25) # Brown color for the ground
    ground_size = 10000 # A very large number to simulate infinity
    glBegin(GL_QUADS)
    glVertex3f(-ground_size, -ground_size, 0)
    glVertex3f(ground_size, -ground_size, 0)
    glVertex3f(ground_size, ground_size, 0)
    glVertex3f(-ground_size, ground_size, 0)
    glEnd()

def draw_wall(x1, y1, x2, y2):
    # Use wall position to seed random for consistent but varied color
    random.seed(x1 * 100 + y1)
    green_shade = 0.3 + random.random() * 0.3 # Varies from 0.3 to 0.6
    glColor3f(0.1, green_shade, 0.1) # Shades of green
    
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    length = math.hypot(x2 - x1, y2 - y1)
    glPushMatrix()
    glTranslatef(mid_x, mid_y, WALL_HEIGHT / 2)
    if abs(x1 - x2) > abs(y1 - y2):
        glScalef(length + WALL_THICKNESS, WALL_THICKNESS, WALL_HEIGHT)
    else:
        glScalef(WALL_THICKNESS, length + WALL_THICKNESS, WALL_HEIGHT)
    glutSolidCube(1)
    glPopMatrix()

def draw_maze():
    if not game_maze: return
    for x in range(MAZE_WIDTH):
        for y in range(MAZE_HEIGHT):
            cell = game_maze.grid[x][y]
            x_pos, y_pos = x * CELL_SIZE, y * CELL_SIZE
            if cell.walls['N']:
                draw_wall(x_pos, y_pos, x_pos + CELL_SIZE, y_pos)
            if cell.walls['W']:
                draw_wall(x_pos, y_pos, x_pos, y_pos + CELL_SIZE)
    # Draw outer boundary walls
    for x in range(MAZE_WIDTH):
        draw_wall(x * CELL_SIZE, MAZE_HEIGHT * CELL_SIZE, (x + 1) * CELL_SIZE, MAZE_HEIGHT * CELL_SIZE)
    for y in range(MAZE_HEIGHT):
        draw_wall(MAZE_WIDTH * CELL_SIZE, y * CELL_SIZE, MAZE_WIDTH * CELL_SIZE, (y + 1) * CELL_SIZE)

def draw_player():
    if first_person: return
    glPushMatrix()
    glTranslatef(player_x, player_y, PLAYER_RADIUS)
    glRotatef(player_angle_deg, 0.0, 0.0, 1.0)
    glColor3f(0.9, 0.1, 0.1)
    glutSolidSphere(PLAYER_RADIUS, 20, 20)
    # Draw a small cube to indicate forward direction
    glColor3f(0.1, 0.9, 0.1)
    glTranslatef(PLAYER_RADIUS, 0, 0)
    glutSolidCube(PLAYER_RADIUS/2)
    glPopMatrix()

# --------------- Camera -----------------
def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, WINDOW_W / float(WINDOW_H), 1.0, 20000.0) # Increased far clipping plane for the ground
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if first_person:
        look_x = player_x + 100 * math.cos(math.radians(player_angle_deg))
        look_y = player_y + 100 * math.sin(math.radians(player_angle_deg))
        gluLookAt(player_x, player_y, FP_CAM_HEIGHT, look_x, look_y, FP_CAM_HEIGHT, 0, 0, 1)
    else:
        # 3rd person camera logic
        angle_rad = math.radians(player_angle_deg)
        # Position camera behind the player
        cam_x = player_x - cam_radius * math.cos(angle_rad)
        cam_y = player_y - cam_radius * math.sin(angle_rad)
        # Look at a point slightly above the player's base
        look_at_z = PLAYER_RADIUS + 20
        gluLookAt(cam_x, cam_y, cam_height, player_x, player_y, look_at_z, 0, 0, 1)

# --------------- Input -----------------
def keyboardListener(key, x, y):
    global player_x, player_y, player_angle_deg
    if key == b'r':
        reset_game()
        return

    angle_rad = math.radians(player_angle_deg)
    
    # Tentative next position
    next_x, next_y = player_x, player_y

    if key == b'w':
        next_x += math.cos(angle_rad) * PLAYER_SPEED
        next_y += math.sin(angle_rad) * PLAYER_SPEED
    elif key == b's':
        next_x -= math.cos(angle_rad) * PLAYER_SPEED
        next_y -= math.sin(angle_rad) * PLAYER_SPEED
    elif key == b'a':
        player_angle_deg += TURN_SPEED
    elif key == b'd':
        player_angle_deg -= TURN_SPEED
    
    # Check collision for the four corners of a bounding box around the player
    collided = False
    for angle in range(0, 360, 90):
        check_rad = math.radians(angle)
        check_x = next_x + PLAYER_RADIUS * math.cos(check_rad)
        check_y = next_y + PLAYER_RADIUS * math.sin(check_rad)
        if check_collision(check_x, check_y):
            collided = True
            break

    if not collided:
        player_x, player_y = next_x, next_y


def specialKeyListener(key, x, y):
    global cam_height, cam_radius
    if first_person: return
    # Use up/down to adjust camera height, left/right to zoom
    if key == GLUT_KEY_UP:
        cam_height = clamp(cam_height + 10, 50, 800)
    elif key == GLUT_KEY_DOWN:
        cam_height = clamp(cam_height - 10, 50, 800)
    elif key == GLUT_KEY_LEFT: # Zoom out
        cam_radius = clamp(cam_radius + 20, 150, 1000)
    elif key == GLUT_KEY_RIGHT: # Zoom in
        cam_radius = clamp(cam_radius - 20, 150, 1000)

def mouseListener(button, state, x, y):
    global first_person
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person = not first_person

# --------------- Main Loop -----------------
def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    setupCamera()
    draw_ground()
    draw_maze()
    draw_player()
    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"The Final Door")
    
    glClearColor(0.5, 0.7, 1.0, 1.0) # Set sky blue background
    
    reset_game()
    glutDisplayFunc(showScreen)
    glutIdleFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glEnable(GL_DEPTH_TEST)
    glutMainLoop()

if __name__ == "__main__":
    main()

