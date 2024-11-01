import os
import random
import socket
import pickle

import pygame
import pygame.font
from pygame.locals import *
import tkinter
from threading import Thread
from tkinter import *
from tkinter import ttk
import sys

# Weather API imports
import datetime as dt
# import datetime
import requests
from six import print_

from game import gameWindowSize
from gamedata import *
import comm

# loads all the variables in the .env file
from dotenv import load_dotenv
import os
load_dotenv()

#/////////////////////////////////////////////////////////////////////////////////////

from PIL import Image
from io import BytesIO
import image
#/////////////////////////////////////////////////////////////////////////////////////

root = Tk()

def resource_path(relative_path):
    """
    Find the full path of a resource file.

    Pyinstaller executables place resource files (image, font, sound)
    in a temporary directory.

    This helper function determines whether the program was launched as
    an executable. If so, it prepends the path of the temporary directory
    to the parameter 'relative_path'

    If the program was not launched as an executable, the current working
    directory is prepended to 'relative_path'

    Parameters
    ----------
    relative_path (string): The relative path of the resource file

    Return
    ------
    The full path to the resource file.
    """
    try:
        # This is just a temp directory that pyinstaller uses to store assets (images, font, etc...)
        base = sys._MEIPASS
    except:
        base = os.path.abspath(".")
    return os.path.join(base, relative_path)

class Client():
    """
    Represents a client. Allows connection to a server of choice.

    Attributes
    ----------
    socket (socket.socket):
        A TCP socket

    addr (tuple[str, int]):
        A tuple that holds an IP address and port number of the server to connect to

    Methods
    -------
    input_addr()
    connect()
    """
    def __init__(self):
        """Initialize a TCP socket"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr = None

    def input_addr(self):
        """Get user input for IP and port. Store in a tuple."""
        server_ip = input("Enter server IP: ")
        server_port = input("Enter server port: ")
        self.addr = (server_ip, int(server_port))

    def connect(self):
        """
        Connect to the currently stored address

        Return
        ------
        True if connection succeeded, False otherwise.
        """
        try:
            self.socket.connect(self.addr)
            return True
        except:
            print('Connection failed')
            return False

class PauseMenu:
    """
    Menu that is displayed upon startup.

    This menu allows the player to select a name and receive
    validation from the server.

    Upon selecting a valid name, the player can enter the game.

    The player could also quit.

    Attributes
    ----------
    game (Game):
        A reference to the game object

    current_name (tkinter.StringVar):
        Keeps track of the current name entered by user

    Methods
    -------
    receive_name_feedback()
    send_name()
    quit()
    populate()
    """

    def __init__(self, game):
        """Create the menu"""
        #self.root = Tk()
        #root.geometry('275x125')
        root.geometry('750x750')
        self.game = game
        self.current_name = StringVar()
        self.populate()
        root.mainloop()

    def receive_name_feedback(self):
        """
        Receive feedback on chosen name from server.

        If the name is valid, destroy the menu and start the game.
        If the name is invalid, prompt the user to select another name.

        Return
        ------
        None
        """
        socket = self.game.client.socket

        feedback_size_bytes = comm.receive_data(socket, comm.MSG_LEN)
        feedback_size = comm.to_int(feedback_size_bytes)
        feedback = pickle.loads(comm.receive_data(socket, feedback_size))

        if feedback == comm.Message.NAME_OK:
            root.destroy()
        elif feedback == comm.Message.NAME_TOO_LONG:
            size_bytes = comm.receive_data(socket, comm.MSG_LEN)
            size = comm.to_int(size_bytes)
            max_name_length = pickle.loads(comm.receive_data(socket, size))
            self.name_feedback.config(text=f"Max name length is {max_name_length} characters.")
        elif feedback == comm.Message.NAME_USED:
            self.name_feedback.config(text=f"Name taken, please select another name.")

    def send_name(self):
        """
        Send the current entered name to the server.

        Returns
        -------
        None
        """
        socket = self.game.client.socket

        name = pickle.dumps(self.current_name.get())
        size = comm.size_as_bytes(name)
        comm.send_data(socket, size)
        comm.send_data(socket, name)

        self.receive_name_feedback()

    def quit(self):
        """
        Send a message to server indicating the intention to quit and then quit.

        Returns
        -------
        None
        """
        self.game.running = False

        socket = self.game.client.socket
        quit_msg = pickle.dumps(comm.Message.QUIT)
        size = comm.size_as_bytes(quit_msg)
        comm.send_data(socket, size)
        comm.send_data(socket, quit_msg)

        root.destroy()

    def populate(self):
        """
        Create the menu and its widgets

        Return
        ------
        None
        """
        frame = ttk.Frame(root, padding=10)
        frame.pack()

        naming_frame = ttk.Frame(frame)
        naming_frame.pack()
        ttk.Label(naming_frame, text = "Display Name: ").pack(side=tkinter.LEFT)
        naming_entry = Entry(naming_frame, width=25, textvariable=self.current_name)
        naming_entry.pack(side=tkinter.LEFT)

        self.name_feedback = ttk.Label(frame, text = "")
        self.name_feedback.pack(pady=10)

        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(pady=5)
        ttk.Button(buttons_frame, text='Play', command=self.send_name).pack(side=tkinter.LEFT, padx=3)
        ttk.Button(buttons_frame, text='Quit', command=self.quit).pack(side=tkinter.LEFT, padx=3)

class Game():
    """
    Represents the client's view of the game.

    Attributes
    ----------
    gameWindowSize (tuple[int, int]):
        The width and height of the player's gameWindowSize

    board (tuple[int, int]):
        The width and height of the playing field

    client (Client):
        The connection to the server

    running (Boolean):
        Whether the game is running or not

    radio (MusicPlayer):
        Allows for audio playback

    leaderboard_font (pygame.font.Font):
        Font style and size

    Methods
    -------
    start()
    show_leaderboard(leaderboard)
    render_bounds(head)
    draw_eyes(head, rect)
    render(game_data)
    get_direction()
    game_loop()
    """

    def __init__(self, client, radio, weather_condition,city):
        """Initialize the game"""
        pygame.init()
        # I added this environment variable to be pulled from on location instead of hardcoding magic numbers -Shafiq.
        # I renamed camera to gameWindowSize for ease of readability -Shafiq.
        # Original code : self.camera = gameWindowSize(1000, 1000) -Shafiq.
        # self.gameWindowSize = (os.getenv('GAME_WINDOW_WIDTH'),os.getenv('GAME_WINDOW_HEIGHT'))
        self.weather_condition = weather_condition # Store the weather condition ///////////////////
        self.sky_patterns = [] # for clouds or sun etc. ///////////////////////
        self.camera = (500, 500)
        self.board = (1000, 1000)
        self.client = client
        self.running = True
        self.is_foggy = False
        self.radio = radio
        self.leaderboard_font = pygame.font.Font(resource_path('./fonts/arial_bold.ttf'), 10)
        self.last_direction = (0, 0)
        self.drops = []
        self.city_name = city # May need to re-think if needed or not.
        self.sky_cloud = load_weather_pattern(city)
        # self.city_name = Game.player_city(self) junk code

        # Get all weather data
        # Added by Shafiq for the scoreboard
        weather_data = get_weather_data(city)
        current_temperature = weather_data["main"]["temp"]
        weather = weather_data["weather"][0]["main"]
        temp_celsius, temp_fahrenheit = kelvin_to_celsius_fahrenheit(current_temperature)
        self.temperature_C = round(temp_celsius)

        if self.weather_condition == "rain":
            self.create_drops(100)
        if self.weather_condition == "snow":
            self.create_drops(100)
        if self.weather_condition == "clouds":
            self.create_weather_condition(6) # Create some weather patterns

    # returns the player city name for the score board.
    # returns local weather for player
    def player_city(self):
        return self.city_name

    def player_temperature(self):
        return self.temperature_C


    def start(self):
        """Create the game window."""
        pygame.event.set_allowed([QUIT, KEYDOWN, KEYUP])
        flags = DOUBLEBUF
        self.window = pygame.display.set_mode(self.camera, flags, 16)

    #/////////////////////////// modified by shafiq
    def show_leaderboard(self, leaderboard):
        """
        Display the leaderboard.
        Parameters
        ----------
        leaderboard (list):
        A list of LeaderboardEntry objects. Used to display the leaderboard.
        Return
        ------
        None
        """
        city = Game.player_city(self)
        temperature = Game.player_temperature(self)

        top = 25   # Move the score board down by 50 pixels to make room for the weather above Shafiq
        for i, entry in enumerate(leaderboard):
            record_string = f'{i + 1}. Name: {entry.name}  SCORE: {entry.score}  CITY: {city}  Temperature: {temperature}°C '
            record = self.leaderboard_font.render(record_string, True, (255, 255, 255))
            record_rect = record.get_rect()
            record_rect.topleft = (8, top)
            self.window.blit(record, record_rect)
            top += 13

    """
    def show_weather(self, weather_condition):
        print("TESTING WEATHER " + weather_condition)
        
        Display the leaderboard.
        Parameters
        ----------
        leaderboard (list):
        A list of LeaderboardEntry objects. Used to display the leaderboard.
        Return
        ------
        None
        
        weather_top = 8
        #record_string = f'{i + 1}.   {entry.name}   {entry.score}'
        record_string = weather_condition
        #        record_string = f'{'SHAFIQ'}.{'COLD'} {'Warm'}'
        record = self.leaderboard_font.render(record_string, True, (255, 255, 255))
        record_rect = record.get_rect()
        record_rect.topleft = (8, weather_top)
        self.window.blit(record, record_rect)
        
    """
    # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

    def render_bounds(self, head):
        """
        Show unreachable area in a different color.

        This only occurs if the unreachable area is viewable in the player's gameWindowSize.
        The head is used as a basis to determine the thickness of the rendered unreachable area.
        The closer the head is to the area, the thicker the rendered area will be.

        Parameters
        ----------
        head (CellData):
            A minimal representation of the head object in the server

        Return
        ------
        None
        """
        if head.position[0] + self.camera[0]/2 > self.board[0]:
            off_map_width = (head.position[0] + self.camera[0]/2 - self.board[0])
            off_map_rect = (self.camera[0] - off_map_width, 0, off_map_width, self.camera[1])
            pygame.draw.rect(self.window, (255, 0, 0), off_map_rect)
        elif head.position[0] - self.camera[0]/2 < 0:
            off_map_width = -(head.position[0] - self.camera[0]/2)
            off_map_rect = (0, 0, off_map_width, self.camera[1])
            pygame.draw.rect(self.window, (255, 0, 0), off_map_rect)
        if head.position[1] + self.camera[1]/2 > self.board[1]:
            off_map_width = (head.position[1] + self.camera[1]/2 - self.board[1])
            off_map_rect = (0, self.camera[0] - off_map_width, self.camera[0], off_map_width)
            pygame.draw.rect(self.window, (255, 0, 0), off_map_rect)
        elif head.position[1] - self.camera[1]/2 < 0:
            off_map_width = -(head.position[1] - self.camera[1]/2)
            off_map_rect = (0, 0, self.camera[0], off_map_width)
            pygame.draw.rect(self.window, (255, 0, 0), off_map_rect)

    def draw_eyes(self, head, rect):
        """
        Draw a pair of eyes for a snake

        Parameters
        ----------
        head (CellData):
            A minimal representation of head object
        rect (tuple[int, int, int, int]):
            A tuple with x position, y position, x width,
            and y width respectively. Represents the
            position of the head according to the client's
            point of view (not the true position).

        Return
        ------
        None
        """
        color = (255,0,0)
        x = rect[0]
        y = rect[1]
        w = rect[2] -3
        h = rect[3] -3
        left_eye = right_eye = None
        if head.direction[0] == 0:  #parallel to y axis
            if head.direction[1] == 1:  #going down
                left_eye = (x + w, y + h-3, 2, 4)
                right_eye = (x + 1, y + h-3, 2, 4)
            else:                       #going up
                left_eye = (x + 1 , y + 1, 2, 4)
                right_eye = (x + w, y + 1, 2, 4)

        if head.direction[1] == 0:  #parallel to x axis
            if head.direction[0] == 1:  #going right
                left_eye = (x + w -2, y + 1, 4, 2)
                right_eye = (x + w-2, y + h, 4, 2)
            else:                       #going left
                left_eye = (x + 1 , y + h, 4, 2)
                right_eye = (x + 1, y + 1, 4, 2)

        pygame.draw.rect(self.window, color, left_eye)
        pygame.draw.rect(self.window, color, right_eye)

    def render(self, game_data):
        """
        Render all objects viewable in the player's gameWindowSize.

        Parameters
        ----------
        game_data (GameData):
            Minimal representation of the data needed to render the current frame

        Return
        ------
        None
        """
        def make_rect(headRect, headPos, objPos, objWidth):
            left = headRect[0] + objPos[0] - headPos[0]
            top = headRect[1] + objPos[1] - headPos[1]
            return (left, top, objWidth-2, objWidth-2)
        snake = game_data.snake
        snakes = game_data.snakes
        pellets = game_data.pellets

        self.window.fill((0, 0, 0))
        my_head = snake[0]

        self.render_bounds(my_head)
        head_rect = (self.camera[0] / 2, self.camera[1] / 2, my_head.width - 2, my_head.width - 2)

        for pellet in pellets:
            pygame.draw.rect(self.window, pellet.color, make_rect(head_rect, my_head.position, pellet.position, pellet.width))
        for this_snake in snakes:
            for body_part in this_snake:
                rect = make_rect(head_rect, my_head.position, body_part.position, body_part.width)
                pygame.draw.rect(self.window, body_part.color, rect)
                if body_part.direction is not None:
                    self.draw_eyes(body_part, rect)
        pygame.draw.rect(self.window, my_head.color, head_rect)
        self.draw_eyes(my_head, head_rect)
        for body_part in snake[1:]:
            pygame.draw.rect(self.window, body_part.color, make_rect(head_rect, my_head.position, body_part.position, body_part.width))
        self.show_leaderboard(game_data.leaderboard)


        # Apply fog effect
        # Implemented by Ethan Ung
        if self.weather_condition == "fog":
            radius = 255
            clear_radius = 10
            self.apply_fog(radius, clear_radius)

        # Apply rain effect
        # Implemented by Ethan Ung
        if self.weather_condition == "rain":
            self.apply_rain()

        if self.weather_condition == "snow":
            self.apply_snow()

        # Apply weather effect
        # Adding clouds, sun, lightning etc. by Shafiq Rahman
        if self.weather_condition == "clouds":
            self.apply_weather_condition(self.sky_cloud)

        pygame.display.flip()

    def apply_snow(self):
        """
        Apply a snow animation around the player to simulate snowy conditions
        Implemented by Ethan Ung
        :return:
        """
        snow_color = (255, 255, 255)  # Color of snowdrops (white)
        drop_width = 2
        drop_height = 2
        window_width = self.window.get_width()
        window_height = self.window.get_height()

        # Get the current direction of the user
        direction = self.get_direction()

        # Determine the slant based on the last user direction
        horizontal_direction = self.last_direction[0]
        if horizontal_direction == 1:  # Moving right
            slant = 5  # Slant right
        elif horizontal_direction == -1:  # Moving left
            slant = -5  # Slant left
        else:
            slant = 0  # No horizontal movement

        # Updates the raindrops position
        for drop in self.drops:
            drop[1] += 3  # Move the raindrop downwards
            drop[0] += slant  # Apply slant based on last input

            # Prevents raindrops from being lost
            if drop[1] > window_height:  # If Y position of a drop goes greater screen height
                drop[1] = 0  # Reset above
                drop[0] = random.randint(0, window_width)  # Randomize x position

            # If the X position goes beyond the screen width, reset to left
            if drop[0] > window_width:
                drop[0] = 0

            # If the x position goes beyond the screen width, reset to right
            if drop[0] < 0:  # Handles user going left when raining
                drop[0] = window_width  # Reset to right side if it goes off screen left

        # Draws the raindrops
        for drop in self.drops:
            pygame.draw.rect(self.window, snow_color, (drop[0], drop[1], drop_width, drop_height))

    def create_drops(self, num_drops):
        """
        Creates the raindrops for the rain animation
        Implemented by Ethan Ung
        :param num_drops:
        :return:
        """
        # Run specific number of times
        for _ in range(num_drops):
            drop_x = random.randint(0, self.camera[0])
            drop_y = random.randint(0, self.camera[1])
            self.drops.append([drop_x, drop_y])  # Store raindrop as [x, y]

    def apply_rain(self):
        """
        Apply a rain animation around the player to simulate rainy conditions
        Implemented by Ethan Ung
        :return:
        """
        rain_color = (0, 0, 255)  # Color of raindrops (blue)
        drop_width = 2
        drop_height = 10
        window_width = self.window.get_width()
        window_height = self.window.get_height()

        # Get the current direction of the user
        direction = self.get_direction()

        # Determine the slant based on the last user direction
        horizontal_direction = self.last_direction[0]
        if horizontal_direction == 1:  # Moving right
            slant = 5  # Slant right
        elif horizontal_direction == -1:  # Moving left
            slant = -5  # Slant left
        else:
            slant = 0  # No horizontal movement

        # Updates the raindrops position
        for drop in self.drops:
            drop[1] += 5  # Move the raindrop downwards
            drop[0] += slant  # Apply slant based on last input

            # Prevents raindrops from being lost
            if drop[1] > window_height:  # If Y position of a drop goes greater screen height
                drop[1] = 0  # Reset above
                drop[0] = random.randint(0, window_width)  # Randomize x position

            # If the X position goes beyond the screen width, reset to left
            if drop[0] > window_width:
                drop[0] = 0

            # If the x position goes beyond the screen width, reset to right
            if drop[0] < 0:  # Handles user going left when raining
                drop[0] = window_width  # Reset to right side if it goes off screen left

        # Draws the raindrops
        for drop in self.drops:
            pygame.draw.rect(self.window, rain_color, (drop[0], drop[1], drop_width, drop_height))

    def apply_fog(self, radius, clear_radius):
        """
        Apply a fog around the player to simulate foggy conditions
        Implemented by Ethan Ung

        :param radius:
        :param clear_radius:
        :return:
        """
        # Ensures the create_fog_texture function is only called once (if fog_texture does not exist run)
        # Patched this bug (if statement is gone, game requires too many resources to run coherently)
        if not hasattr(self, 'fog_texture'):
            self.fog_texture = self.create_fog_texture(radius, clear_radius)

        # Get the center position of the screen
        center_position = (self.window.get_width() // 2, self.window.get_height() // 2)

        # Blit the fog texture at the center position
        fog_rect = self.fog_texture.get_rect(center=center_position)
        self.window.blit(self.fog_texture, fog_rect.topleft)

    def create_fog_texture(self, radius, clear_radius):
        """
        Creates a fog texture for the apply_fog function
        Implemented by Ethan Ung

        :param radius:
        :param clear_radius:
        :return:
        """
        fog_texture = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

        for y in range(fog_texture.get_height()):
            for x in range(fog_texture.get_width()):
                distance = ((x - radius) ** 2 + (y - radius) ** 2) ** 0.5

                if distance < clear_radius:
                    alpha = 0  # Fully transparent in the center of the camera
                elif distance < radius:
                    # Calculate alpha for the fog within the radius
                    alpha = min(255, int(255 * ((distance - clear_radius) / (radius - clear_radius))))
                else:
                    alpha = 255  # Fully opaque at the edges

                fog_texture.set_at((x, y), (255, 255, 255, alpha))  # White fog
        return fog_texture

    # ////////////////////////////////////////////////////////////////////////////////////////////////////////////

    def apply_weather_condition(self, sky_cloud):
        """
        Apply the clouds in the sky based on the collection created by create_weather_condition
        NOTE: The round filed circle picture is the actual pic from https://openweathermap.org/weather-conditions
        which represents clear skies. It is their default picture and not a game error.
        :return:
        """

        for pattern in self.sky_patterns:
            pattern[0] += 1
            if pattern[0] > self.camera[1]:
                pattern[0] = 0
                pattern[1] = random.randint(0, self.camera[1])
        for pattern in self.sky_patterns:
            self.window.blit(sky_cloud,(pattern[0],pattern[1]))

    def create_weather_condition(self,num_clouds):
        """
        Creates a collection of clouds with top 1/4 of the screen with random coordinates and random direction
        for each cloud.
        Implemented by Shafiq Rahman using Ethan's rain drop method
        :param num_clouds
        :return:
        """
        cloud_direction = ['left','right']
        for _ in range(num_clouds):
            rand_direction = random.choice(cloud_direction)
            cloud_x = random.randint(0, self.camera[0])
            cloud_y = random.randint(0, int(self.camera[1] / 4))
            self.sky_patterns.append([cloud_x, cloud_y, cloud_direction]) # The clouds are stored as [x, y, direction]
    """
    def load_weather_pattern(self, weather_condition):
        # Based on the weather_condition we can load other pictures for future enhancements
        try:
            weather_image = pygame.image.load('weather_API_images/cloudy_no_rain.png')
            if weather_condition == "Clouds":
                weather_image = pygame.image.load('weather_API_images/cloudy_no_rain.png')
            return weather_image
        except pygame.error as e:
            print(f"Failed to load image: {e}")
            return None
    """

    # ////////////////////////////////////////////////////////////////////////////////////////////////////////////

    def get_direction(self):
        """
        Get the direction based on user input.

        Direction is represented as a tuple of two ints.
        Each int has a value of either -1, 0, or 1.

        -1 means left in the first tuple element and up in the second.
        1 means right in the first tuple element and down in the second.
        0 means no horizontal movement in the first tuple element.
        0 means no vertical movement in the second tuple element.

        Return
        ------
        Tuple[int, int] with the first element representing horizontal direction
        and the second element representing vertical direction.
        """
        direction = None
        keys = pygame.key.get_pressed()
        new_direction = (0, 0)
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]):
            new_direction = (-1, 0)
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            new_direction = (1, 0)
        if (keys[pygame.K_UP] or keys[pygame.K_w]):
            new_direction = (0, -1)
        if (keys[pygame.K_DOWN] or keys[pygame.K_s]):
            new_direction = (0, 1)

        # Only update last_direction if there's new input
        if new_direction != (0, 0):
            self.last_direction = new_direction

        return self.last_direction

    def game_loop(self):
        """
        Game loop.

        Note that the actual game loop occurs on the server side.
        This loop only detects input (such as movement and quitting),
        communicates with server, renders the game, and plays sound.

        Return
        ------
        None
        """
        while self.running:
            msg = None
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    msg = pickle.dumps(comm.Message.QUIT)
                    self.running = False

            # Send input or quit signal to server

            if msg == None:
                msg = pickle.dumps(self.get_direction())
            comm.send_data(self.client.socket, comm.size_as_bytes(msg))
            comm.send_data(self.client.socket, msg)

            # If the player decided to quit, exit the game loop after notifying server
            if not self.running:
                break

            # Receive game data from server, use it to render
            # If an exception occurs it is likely that the server has shut down, in which case
            # we exit the client.
            try:
                size_as_bytes = comm.receive_data(self.client.socket, comm.MSG_LEN)
                length = comm.to_int(size_as_bytes)
                game_data = pickle.loads(comm.receive_data(self.client.socket, length))
            except:
                break

            if game_data == comm.Message.SERVER_SHUTDOWN:
                print("Server shutting down")
                break

            self.render(game_data)

            if game_data.sound is not None:
                self.radio.play_sound(game_data.sound)

        pygame.quit()

class MusicPlayer():
    """
    A class that allows for audio playback.

    Attributes
    ----------
    pellet_sound (pygame.mixer.Sound):
        Sound for food pellet collision

    self_collision (pygame.mixer.Sound):
        Sound for collision with self or other snakes
    """

    def __init__(self, song):
        """
        Start a thread to play background music.

        Parameters
        ----------
        song (str):
            Filename of the music to be played

        Return
        ------
        None
        """
        pygame.mixer.init()

        self.pellet_sound = pygame.mixer.Sound(resource_path("sound/pellet_sound.mp3"))
        self.self_collision = pygame.mixer.Sound(resource_path("sound/self_collision.mp3"))
        Thread(target=self.play_song, args=(song,)).start()

    def play_song(self, song):
        """
        Play background music indefinitely.

        Parameters
        ----------
        song (str):
            Filename of the music to be played

        Return
        ------
        None
        """
        pygame.mixer.music.load(song)
        pygame.mixer.music.play(-1)

    def play_sound(self, sound):
        """
        Play a sound once.

        Parameters
        ----------
        sound (comm.Message):
            An indicator of the type of sound to play

        Return
        ------
        None
        """
        if sound == comm.Message.PELLET_EATEN:
            self.pellet_sound.play()
        elif sound == comm.Message.SELF_COLLISION or sound == comm.Message.OTHER_COLLISION:
            self.self_collision.play()

# functions added by Shafiq for the LAB assignment.

def kelvin_to_celsius_fahrenheit(kelvin):
    celsius = kelvin - 273.15
    fahrenheit = celsius * (9/5) + 32
    return celsius, fahrenheit

def get_description(location):
    """
    Fetch weather information for a given location.
    Implemented by Ethan Ung
    :param location: The name of the location to fetch weather data for.
    :return: A dictionary containing weather information.
    """
    API_KEY = 'ea7462c3a327d8e268193e6ac9137887'
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()

    if response.status_code == 200:
        weather = data['weather'][0]['main']
        temperature = data['main']['temp']
        wind_speed = data['wind']['speed']
        humidity = data['main']['humidity']

        return {
            'weather': weather,
            'temperature': temperature,
            'wind_speed': wind_speed,
            'humidity': humidity
        }
    else:
        return None

# We can consolidate this or hide this key later for futrue projects.
def get_API_key():
    API_KEY = 'ea7462c3a327d8e268193e6ac9137887'
    return API_KEY


def load_weather_pattern(city_name):
    # Based on the city we can load fresh information from OpenWeatherMap.org
    weather_data = get_weather_data(city_name)
    icon_code = weather_data['weather'][0]['icon']  # Extract the icon code
    icon_image = fetch_weather_icon(icon_code)
    return icon_image


# Fetch weather data from OpenWeatherMap
def get_weather_data(city_name):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={get_API_key()}"
    response = requests.get(url)
    data = response.json()
    return data
"""
# Extract icon code from weather data and fetch the icon image
def fetch_weather_icon(icon_code):
    icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
    response = requests.get(icon_url)
    img = Image.open(BytesIO(response.content))
    return img
"""

def fetch_weather_icon(icon_code):
    icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
    response = requests.get(icon_url)
    img = Image.open(BytesIO(response.content))
    # Convert the PIL Image to a format pygame can use
    img_data = img.tobytes()  # Obtain raw image data from the PIL image
    img_mode = img.mode  # Get the mode ('RGB', 'RGBA')
    img_size = img.size  # Get image size as (width, height)
    # Create a Surface from the raw image data
    return pygame.image.fromstring(img_data, img_size, img_mode)

# ////////////////////////////////////////////////////////////////////////////////////////////////////////////

def main():
    """
    User can input their location and then print description; weather, temperature, wind_speed, humidity
    Implemented by Ethan Ung
    :return:
    """
    location = input("Enter your location: ")
    location_description = get_description(location)
    print(location_description)
    if location_description:
        print(f"Weather: {location_description['weather']}")
        print(f"Temperature: {location_description['temperature']}°C")
        print(f"Wind Speed: {location_description['wind_speed']} m/s")
        print(f"Humidity: {location_description['humidity']}%")
    else:
        print("Couldn't retrieve weather data.")

    #print("This is a test to access the weather by Shafiq Rahman")

    #API_KEY = open('OpenWeather_API_key.py','r').read()
    #API_KEY = "ea7462c3a327d8e268193e6ac9137887"
    #BASE_URL = f"https://api.openweathermap.org/data/2.5/weather?"
    #CITY = "Philadelphia"
    #url = BASE_URL + "appid=" + API_KEY + "&q=" + CITY
    #response = requests.get(url).json()
    #temp_kelvin = requests.get(url).json()
    #temp_kelvin = response['main']['temp']
    #temp_celsius, temp_fahrenheit = kelvin_to_celsius_fahrenheit(temp_kelvin)
    #feels_like_kelvin = response['main']['feels_like']
    #feels_like_celsius, feels_like_fahrenheit = kelvin_to_celsius_fahrenheit(feels_like_kelvin)
    #humidity = response['main']['humidity']
    #description = response['weather'][0]['description']
    #wind_speed = response['wind']['speed']
    # sunrise_time = dt.datetime.utcfromtimestamp(response['sys']['sunrise'] + response['timezone'])
    #sunrise_time = dt.datetime.fromtimestamp(response['sys']['sunrise'], dt.timezone.utc)
    # sunset_time = dt.datetime.utcfromtimestamp(response['sys']['sunset'] + response['timezone'])
    #sunset_time = dt.datetime.fromtimestamp(response['sys']['sunset'], dt.timezone.utc)

    #print(f"Temperature in {CITY}: {temp_fahrenheit} °F")
    #print(f"Temperature in {CITY}: {temp_celsius} °C")
    #print(f"Wind speed in {CITY}: {wind_speed} mph.")
    #print(f"humidity in {CITY}: {humidity} .")
    #print(f"description in {CITY}: {description}.")

    print(f"-----------------------------")
    weather_condition = input("Enter desired weather condition (Clear, Clouds, Rain, Wind, Fog): ").strip().lower()

    # Process the condition
    check_weather(weather_condition)

    #weather_condition = location_description['weather'] if location_description else "Clear"
    #check_weather(weather_condition.lower())

    client = Client()
    client.input_addr()
    if not client.connect():
        return

    radio = MusicPlayer(resource_path("sound/snake_hunt.mp3"))
    # weather_condition = get_weather(CITY, API_KEY)
    game = Game(client, radio, weather_condition.lower(), location)
    PauseMenu(game)

    game.start()
    game.game_loop()

def check_weather(condition):
    """
    Function to check the weather from user input
    Implemented by Ethan Ung
    :param condition:
    :return:
    """
    weather_data = {
        "fog": "Visibility is low due to fog.",
        "clear": "No significant weather conditions.",
        "clouds": "Cloudy skies are seen.",
        "rain": "Light rain is expected.",
        "drizzle": "Light rain is falling.",
        "thunderstorm": "Thunderstorms are occurring.",
        "snow": "It is looking a lot like christmas",
    }

    if condition in weather_data:
        print(weather_data[condition])
    else:
        print(f"No data available for condition: {condition}")

if __name__ == '__main__':
    main()
