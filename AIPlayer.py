
# implementation of the AI logic:
import random

class AIPlayer():
    def __init__(self, name, snake):
        self.name = name
        self.snake = snake

    def update_direction(self):
        # Randomly change direction every few moves
        if random.choice(['up', 'down', 'left', 'right']) == 'up' and self.snake.head.ydir != 1:
            self.snake.change_direction_manual(0, -1)  # Up
        elif random.choice(['up', 'down', 'left', 'right']) == 'down' and self.snake.head.ydir != -1:
            self.snake.change_direction_manual(0, 1)   # Down
        elif random.choice(['up', 'down', 'left', 'right']) == 'left' and self.snake.head.xdir != 1:
            self.snake.change_direction_manual(-1, 0)  # Left
        elif random.choice(['up', 'down', 'left', 'right']) == 'right' and self.snake.head.xdir != -1:
            self.snake.change_direction_manual(1, 0)   # Right

NOTES:


class Game():
    def __init__(self):
        pygame.init()
        self.field_dimensions = BOARD
        self.world_dimensions = BEYOND_BOARD
        self.camera_dimensions = (500, 500)
        self.win = pygame.display.set_mode(self.camera_dimensions)
        self.world = pygame.Surface(self.world_dimensions)

        self.title_font = pygame.font.Font('freesansbold.ttf', 32)
        self.leaderboard_font = pygame.font.Font('freesansbold.ttf', 10)
        self.title_text = self.title_font.render('Snake Hunt', True, (255, 255, 255))
        self.title_rect = self.title_text.get_rect()

        #self.players = []
        #initial_pos = (25, 25)
        #snakeAI = Snake(initial_pos, 10, 1, 0, self.field_dimensions, self.world_dimensions)
        #self.players.append(PlayerSnake('AI Snake', snakeAI))

        self.players = []
        initial_pos = (250, 250)
        snake = Snake(initial_pos, 1, 1, 0, self.field_dimensions, self.world_dimensions)
        self.players.append(HumanPlayer('Anonymous', snake))

        # by Shafiq Rahman
        # Add AI multiple player snakes
        for i in range(len(AISnakes)):
            ai_snake: AISnakes = Snake((randint(0, COLS) * CELL, randint(0, ROWS) * CELL), 1, 1, 0, self.field_dimensions, self.world_dimensions)
            self.players.append(AIPlayer(AISnakes[i], ai_snake))

        # Camera & rendering setup
        self.camera = Camera(ai_snake, self.camera_dimensions)
        self.title_rect.center = (self.camera_dimensions[0] // 2, self.camera_dimensions[1] // 2)

        self.pellets = RandomPellets(25, self.world)
        self.clock = pygame.time.Clock()
        self.running = False

        self.camera = Camera(snake, self.camera_dimensions)
        self.title_rect.center = (self.camera_dimensions[0] // 2, self.camera_dimensions[1] // 2)

        self.pellets = RandomPellets(25, self.world)
        self.clock = pygame.time.Clock()
        self.running = False

    def render(self):
        # Following modified and changed by Shafiq Rahman
        self.world.fill((20,30,20))
        pygame.draw.rect(self.world, (130,100,130),(BEYOND_BOARD[0]/4, BEYOND_BOARD[1]/4, BOARD[0], BOARD[1]))

        self.players[0].snake.render(self.world)
        # self.players[1].snake.render(self.world)

        self.pellets.render(self.world)
        self.camera.render(self.win, self.world)
        self.show_leaderboard()

        pygame.display.flip()
