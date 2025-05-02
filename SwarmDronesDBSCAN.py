import tkinter as tk
import random
import math
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

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
            x, y = self.get_boundary_position()
            color = "blue"
            drone = self.canvas.create_oval(x-self.drone_size, y-self.drone_size, 
                                            x+self.drone_size, y+self.drone_size, fill=color)
            self.drones.append(drone)
            self.drone_positions.append([x, y])

        for _ in range(self.num_monkeys):
            self.add_monkey()

        self.master.after(50, self.update_simulation)

    def get_boundary_position(self):
        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'top':
            return random.randint(self.border_padding, self.canvas_width - self.border_padding), self.border_padding
        elif side == 'bottom':
            return random.randint(self.border_padding, self.canvas_width - self.border_padding), self.canvas_height - self.border_padding
        elif side == 'left':
            return self.border_padding, random.randint(self.border_padding, self.canvas_height - self.border_padding)
        else:  # right
            return self.canvas_width - self.border_padding, random.randint(self.border_padding, self.canvas_height - self.border_padding)

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
            self.drone_assignments = []
            return

        # Normalize the data
        X = StandardScaler().fit_transform(self.monkey_positions)

        # Perform DBSCAN clustering with adjusted parameters
        dbscan = DBSCAN(eps=0.5, min_samples=2)
        dbscan_labels = dbscan.fit_predict(X)

        # Count the number of clusters (excluding noise points labeled as -1)
        n_clusters = len(set(dbscan_labels)) - (1 if -1 in dbscan_labels else 0)

        # If no clusters found, treat all points as one cluster
        if n_clusters == 0:
            self.swarms = [np.mean(self.monkey_positions, axis=0).tolist()]
            self.drone_assignments = [self.num_drones]
            return

        # Calculate cluster centers and sizes
        clusters = []
        for i in range(n_clusters):
            cluster_points = np.array([p for p, l in zip(self.monkey_positions, dbscan_labels) if l == i])
            center = np.mean(cluster_points, axis=0)
            size = len(cluster_points)
            clusters.append((center.tolist(), size))

        # Assign unclustered monkeys to the nearest cluster
        unclustered = np.array([p for p, l in zip(self.monkey_positions, dbscan_labels) if l == -1])
        for point in unclustered:
            nearest_cluster = min(clusters, key=lambda c: self.distance(point, c[0]))
            nearest_cluster_index = clusters.index(nearest_cluster)
            new_center = ((np.array(clusters[nearest_cluster_index][0]) * clusters[nearest_cluster_index][1] + point) / (clusters[nearest_cluster_index][1] + 1)).tolist()
            clusters[nearest_cluster_index] = (new_center, clusters[nearest_cluster_index][1] + 1)

        # Sort clusters by size (descending) and select top 5 from different areas
        clusters.sort(key=lambda x: x[1], reverse=True)
        selected_clusters = []
        for center, size in clusters:
            if not any(self.distance(center, c[0]) < 100 for c in selected_clusters):
                selected_clusters.append((center, size))
                if len(selected_clusters) == 5:
                    break

        self.swarms = [center for center, _ in selected_clusters]
        
        # Assign drones proportionally
        total_monkeys = sum(size for _, size in selected_clusters)
        self.drone_assignments = [max(1, int(size / total_monkeys * self.num_drones)) for _, size in selected_clusters]

        # Assign any remaining drones to the largest cluster
        remaining_drones = self.num_drones - sum(self.drone_assignments)
        if remaining_drones > 0:
            self.drone_assignments[0] += remaining_drones

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
