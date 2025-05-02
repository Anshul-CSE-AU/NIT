import tkinter as tk
import random
import math
from sklearn.cluster import KMeans
import numpy as np

class DroneSimulation:
    def __init__(self, master):
        self.master = master
        self.master.title("Drone Swarm Border Patrol")
        self.running = False
        
        self.canvas_width = 800
        self.canvas_height = 600
        self.border_padding = 50
        self.drone_size = 6
        self.monkey_size = 8
        
        self.canvas = tk.Canvas(self.master, width=self.canvas_width, height=self.canvas_height, bg="lightgreen")
        self.canvas.pack(side=tk.TOP, padx=10, pady=10)

        self.control_frame = tk.Frame(self.master)
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.num_drones_label = tk.Label(self.control_frame, text="Number of Drones:")
        self.num_drones_label.grid(row=0, column=0, padx=5, pady=5)
        self.num_drones_entry = tk.Entry(self.control_frame)
        self.num_drones_entry.grid(row=0, column=1, padx=5, pady=5)
        self.num_drones_entry.insert(0, "20")

        self.num_monkeys_label = tk.Label(self.control_frame, text="Number of Monkeys:") 
        self.num_monkeys_label.grid(row=0, column=2, padx=5, pady=5)
        self.num_monkeys_entry = tk.Entry(self.control_frame)
        self.num_monkeys_entry.grid(row=0, column=3, padx=5, pady=5)
        self.num_monkeys_entry.insert(0, "30")

        self.start_button = tk.Button(self.control_frame, text="Start", command=self.start_simulation)
        self.start_button.grid(row=1, column=0, padx=5, pady=5)

        self.stop_button = tk.Button(self.control_frame, text="Stop", command=self.stop_simulation)
        self.stop_button.grid(row=1, column=1, padx=5, pady=5)

        self.restart_button = tk.Button(self.control_frame, text="Restart", command=self.restart_simulation)
        self.restart_button.grid(row=1, column=2, padx=5, pady=5)
        
        self.drones = []
        self.drone_positions = []
        self.monkeys = []
        self.monkey_positions = []
        self.swarms = []

    def start_simulation(self):
        self.running = True
        self.drones = []
        self.drone_positions = []
        self.monkeys = []
        self.monkey_positions = []
        self.swarms = []

        self.num_drones = int(self.num_drones_entry.get())
        self.num_monkeys = int(self.num_monkeys_entry.get())

        self.canvas.delete("all")
        
        self.field = self.canvas.create_rectangle(
            self.border_padding, 
            self.border_padding, 
            self.canvas_width - self.border_padding, 
            self.canvas_height - self.border_padding, 
            outline="red", width=2
        )

        for i in range(self.num_drones):
            x, y = self.get_random_position()
            color = "blue"
            drone = self.canvas.create_oval(x-self.drone_size, y-self.drone_size, 
                                            x+self.drone_size, y+self.drone_size, fill=color)
            self.drones.append(drone)
            self.drone_positions.append([x, y])

        for _ in range(self.num_monkeys):
            self.add_monkey()

        self.master.after(50, self.update_simulation)

    def add_monkey(self):
        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'top':
            x = random.randint(0, self.canvas_width)
            y = random.randint(0, self.border_padding - self.monkey_size)
        elif side == 'bottom':
            x = random.randint(0, self.canvas_width)
            y = random.randint(self.canvas_height - self.border_padding + self.monkey_size, self.canvas_height)
        elif side == 'left':
            x = random.randint(0, self.border_padding - self.monkey_size)
            y = random.randint(0, self.canvas_height)
        else:  # right
            x = random.randint(self.canvas_width - self.border_padding + self.monkey_size, self.canvas_width)
            y = random.randint(0, self.canvas_height)
        
        monkey = self.canvas.create_oval(x-self.monkey_size, y-self.monkey_size,
                                         x+self.monkey_size, y+self.monkey_size, fill="brown")
        self.monkeys.append(monkey)
        self.monkey_positions.append([x, y])

    def get_random_position(self):
        return (random.randint(self.border_padding, self.canvas_width - self.border_padding),
                random.randint(self.border_padding, self.canvas_height - self.border_padding))

    def update_simulation(self):
        if not self.running:
            return

        self.move_monkeys()
        self.analyze_monkey_clusters()
        self.move_drones()

        self.master.after(50, self.update_simulation)

    def move_monkeys(self):
        for i, monkey in enumerate(self.monkeys):
            x, y = self.monkey_positions[i]
            dx = random.randint(-5, 5)
            dy = random.randint(-5, 5)
            
            new_x = max(0, min(x + dx, self.canvas_width))
            new_y = max(0, min(y + dy, self.canvas_height))
            
            self.canvas.coords(monkey, new_x - self.monkey_size, new_y - self.monkey_size,
                               new_x + self.monkey_size, new_y + self.monkey_size)
            self.monkey_positions[i] = [new_x, new_y]

    def analyze_monkey_clusters(self):
        if len(self.monkey_positions) < 2:
            self.swarms = []
            return

        num_clusters = min(5, len(self.monkey_positions) // 2)  # Limit to 5 clusters
        kmeans = KMeans(n_clusters=num_clusters, n_init=10, random_state=0).fit(self.monkey_positions)
        self.swarms = kmeans.cluster_centers_.tolist()
        
        # Count monkeys in each cluster
        cluster_sizes = [0] * num_clusters
        for label in kmeans.labels_:
            cluster_sizes[label] += 1
        
        # Assign drones proportionally
        total_monkeys = sum(cluster_sizes)
        self.drone_assignments = [max(1, int(size / total_monkeys * self.num_drones)) for size in cluster_sizes]

    def move_drones(self):
        if not self.swarms:
            return

        drone_index = 0
        for swarm_center, num_assigned_drones in zip(self.swarms, self.drone_assignments):
            assigned_drones = self.drones[drone_index:drone_index + num_assigned_drones]
            self.form_v_formation(assigned_drones, swarm_center)
            drone_index += num_assigned_drones

        # Push monkeys out of the field
        for i, monkey_pos in enumerate(self.monkey_positions):
            if (self.border_padding < monkey_pos[0] < self.canvas_width - self.border_padding and
                self.border_padding < monkey_pos[1] < self.canvas_height - self.border_padding):
                # Monkey is inside the field, push it out
                center_x = self.canvas_width / 2
                center_y = self.canvas_height / 2
                direction = [monkey_pos[0] - center_x, monkey_pos[1] - center_y]
                distance = math.sqrt(direction[0]**2 + direction[1]**2)
                if distance > 0:
                    direction = [d * 10 / distance for d in direction]  # Increase push force
                
                new_x = max(0, min(monkey_pos[0] + direction[0], self.canvas_width))
                new_y = max(0, min(monkey_pos[1] + direction[1], self.canvas_height))
                
                self.canvas.coords(self.monkeys[i], new_x - self.monkey_size, new_y - self.monkey_size,
                                   new_x + self.monkey_size, new_y + self.monkey_size)
                self.monkey_positions[i] = [new_x, new_y]

    def form_v_formation(self, drones, center):
        num_drones = len(drones)
        if num_drones == 0:
            return
        
        v_angle = math.pi / 6  # Narrower angle for more visible V
        v_length = 120  # Longer V formation
        
        for i, drone in enumerate(drones):
            if i == 0:
                target_pos = center
                self.canvas.itemconfig(drone, fill="red")
            else:
                side = 1 if i % 2 == 0 else -1
                distance = (i + 1) // 2 * (v_length / (num_drones // 2 + 1))
                offset_x = math.cos(v_angle) * distance * side
                offset_y = math.sin(v_angle) * distance
                target_pos = [center[0] + offset_x, center[1] + offset_y]
                self.canvas.itemconfig(drone, fill="blue")
            
            self.move_drone_towards(drone, target_pos)

    def move_drone_towards(self, drone, target):
        current_pos = self.drone_positions[self.drones.index(drone)]
        direction = [target[0] - current_pos[0], target[1] - current_pos[1]]
        distance = math.sqrt(direction[0]**2 + direction[1]**2)
        if distance > 0:
            direction = [d * 5 / distance for d in direction]
        
        new_x = max(self.border_padding, min(current_pos[0] + direction[0], self.canvas_width - self.border_padding))
        new_y = max(self.border_padding, min(current_pos[1] + direction[1], self.canvas_height - self.border_padding))
        
        self.canvas.coords(drone, new_x-self.drone_size, new_y-self.drone_size, 
                           new_x+self.drone_size, new_y+self.drone_size)
        self.drone_positions[self.drones.index(drone)] = [new_x, new_y]

    def distance(self, pos1, pos2):
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

    def stop_simulation(self):
        self.running = False
    
    def restart_simulation(self):
        self.stop_simulation()
        self.start_simulation()

if __name__ == "__main__":
    root = tk.Tk()
    app = DroneSimulation(root)
    root.mainloop()
