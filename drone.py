import math
import time
import random

class Drone:
    def __init__(self, canvas, home_x, home_y, log_callback, is_leader=False, group_color=None):
        self.canvas = canvas
        self.home_x = home_x
        self.home_y = home_y
        self.x = home_x
        self.y = home_y
        self.size = 15
        self.speed = 5
        self.charge = 50
        self.target = None
        self.color = group_color if group_color else self.get_random_color()
        self.is_leader = is_leader
        self.shape = canvas.create_oval(self.x-self.size/2, self.y-self.size/2, self.x+self.size/2, self.y+self.size/2, fill=self.color, outline="white", width=2) if self.is_leader else canvas.create_oval(self.x-self.size/2, self.y-self.size/2, self.x+self.size/2, self.y+self.size/2, fill=self.color, outline="white", width=2)
        self.waiting = False
        self.wait_start_time = None
        self.wait_duration = 0
        self.has_mango = False
        self.log_callback = log_callback
        self.distance_travelled = 0
        self.assigned_trees = []  # Initialize assigned_trees as an empty list

    def get_random_color(self):
        return f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"

    def move(self):
        if self.waiting:
            if time.time() - self.wait_start_time >= self.wait_duration:
                self.waiting = False
                return
            return

        if self.target:
            dx = self.target[0] - self.x
            dy = self.target[1] - self.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance < self.speed:
                self.x, self.y = self.target
                self.target = None
                self.start_waiting()
            else:
                move_x = (dx / distance) * self.speed
                move_y = (dy / distance) * self.speed
                self.x += move_x
                self.y += move_y
                self.charge -= 0.1
                self.canvas.move(self.shape, move_x, move_y)

            self.distance_travelled += distance
        
        # Constrain within canvas boundaries
        max_x = self.canvas.winfo_width()
        max_y = self.canvas.winfo_height()
        self.x = max(0, min(self.x, max_x))
        self.y = max(0, min(self.y, max_y))
        self.canvas.coords(self.shape, self.x-self.size/2, self.y-self.size/2, self.x+self.size/2, self.y+self.size/2)

    def set_target(self, x, y):
        self.target = (x, y)
        self.log_callback(f"Drone set target to ({x}, {y})")

    def start_waiting(self):
        self.waiting = True
        self.wait_start_time = time.time()
        self.wait_duration = random.uniform(2, 7)  # Set a random wait time between 2 and 7 seconds

    def move_to_mango_storage(self, storage_x, storage_y):
        self.set_target(storage_x, storage_y)

    def return_home(self):
        self.set_target(self.home_x, self.home_y)
