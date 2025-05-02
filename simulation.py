import math
import numpy as np
import random
from scipy.spatial import Voronoi, voronoi_plot_2d
import time
import tkinter as tk

from drone import Drone
from gui import SimulationGUI
from objects import MangoTree, Station, MangoStorage


class Simulation:
    def __init__(self, master):
        self.gui = SimulationGUI(master, self.start_simulation, self.toggle_simulation)
        self.running = False
        self.drones = []
        self.mango_trees = []
        self.available_trees = []
        self.targets = {}
        self.bounding_boxes = []
        self.start_time = None
        self.total_distance_text = None
        self.time_taken_text = None
        self.groups = []

    def start_simulation(self):
        # Reset simulation state if already running
        if self.running:
            self.running = False
            self.gui.canvas.delete("all")
            self.drones = []
            self.mango_trees = []
            self.available_trees = []
            self.targets = {}
            self.bounding_boxes = []
            self.start_time = None
            self.total_distance_text = None
            self.time_taken_text = None
            self.groups = []

        params = self.gui.get_simulation_parameters()
        self.no_of_drones = params['drones']
        self.no_of_rows = params['rows']
        self.no_of_columns = params['columns']
        self.sim_type = params['sim_type']
        self.map_type = params['map_type']
        self.no_of_groups = params['groups']

        self.gui.canvas.delete("all")

        # Create stations
        station_width, station_height = 80, 80
        station_margin = 20
        station_spacing = 40
        self.home = Station(self.gui.canvas, station_margin, 50, station_width, station_height, "lightgreen", "Home/Recharge")
        self.mango_storage = MangoStorage(self.gui.canvas, station_margin, 50 + station_height + station_spacing, station_width, station_height)

        # Adjust the grid creation to start after the stations
        grid_start_x = 150
        self.mango_trees = self.create_mango_trees(self.no_of_rows, self.no_of_columns, grid_start_x)
        self.available_trees = list(self.mango_trees)
        
        self.create_drone_groups()
        self.targets = {}

        if self.sim_type == "heirarchical-box":
            self.allocate_rectangular_areas()
        elif self.sim_type == "heirarchical-voronoi":
            self.allocate_voronoi_areas()

        self.assign_tasks_to_drones()
        self.running = True
        self.start_time = time.time()

        # Create text for total distance and time taken
        canvas_width = self.gui.canvas.winfo_width()
        canvas_height = self.gui.canvas.winfo_height()
        self.total_distance_text = self.gui.canvas.create_text(
            canvas_width - 10, canvas_height - 30,
            anchor="se", text="Total Distance: 0 units", fill="black"
        )
        self.time_taken_text = self.gui.canvas.create_text(
            canvas_width - 10, canvas_height - 10,
            anchor="se", text="Time: 0 seconds", fill="black"
        )

        self.gui.master.after(50, self.update)

    def toggle_simulation(self):
        self.running = not self.running
        if self.running:
            self.gui.master.after(50, self.update)

    def update(self):
        if not self.running:
            return

        all_tasks_complete = all(tree.harvested for tree in self.mango_trees) and all(not drone.has_mango for drone in self.drones)

        for drone in self.drones:
            if all_tasks_complete and (drone.x, drone.y) != (self.home.center_x, self.home.center_y):
                drone.return_home()
            drone.move()
            self.handle_drone_actions(drone)

        if not all_tasks_complete:
            self.assign_tasks_to_drones()

        # Update total distance and time taken
        total_distance = sum(drone.distance_travelled for drone in self.drones)
        time_taken = time.time() - self.start_time

        self.gui.canvas.itemconfig(
            self.total_distance_text,
            text=f"Total Distance: {total_distance:.2f} units"
        )
        self.gui.canvas.itemconfig(
            self.time_taken_text,
            text=f"Time: {time_taken:.2f} seconds"
        )

        if all_tasks_complete and all(drone.x == self.home.center_x and drone.y == self.home.center_y for drone in self.drones):
            self.running = False
            self.gui.log_message(f"All tasks completed in {time_taken:.2f} seconds. Total distance: {total_distance:.2f} units.")
        else:
            self.gui.master.after(50, self.update)

    def handle_drone_actions(self, drone):
        if drone.waiting and not drone.has_mango:
            for tree in drone.assigned_trees:
                if (drone.x, drone.y) == (tree.x, tree.y) and not tree.harvested:
                    tree.harvest()
                    drone.has_mango = True
                    drone.move_to_mango_storage(self.mango_storage.center_x, self.mango_storage.center_y)
                    self.gui.log_message(f"Drone harvested mango at ({drone.x}, {drone.y})")
                    return

        if drone.waiting and (drone.x, drone.y) == (self.mango_storage.center_x, self.mango_storage.center_y):
            if drone.has_mango:
                drone.has_mango = False
                self.mango_storage.update_mango_count()
                self.gui.log_message("Drone dropped mango at storage")
            drone.target = None
            self.targets.pop(drone, None)

        if drone.waiting and (drone.x, drone.y) == (self.home.center_x, self.home.center_y):
            if drone.charge < 50:
                drone.charge = 50
                self.gui.log_message("Drone recharged at home")
            drone.target = None
            self.targets.pop(drone, None)

    def create_drone_groups(self):
        drones_per_group = self.no_of_drones // self.no_of_groups
        extra_drones = self.no_of_drones % self.no_of_groups

        for i in range(self.no_of_groups):
            group_color = self.get_random_color()
            group_drones = []
            group_size = drones_per_group + (1 if i < extra_drones else 0)

            for j in range(group_size):
                is_leader = (j == 0)
                drone = Drone(self.gui.canvas, self.home.center_x, self.home.center_y, self.gui.log_message, is_leader, group_color)
                if is_leader:
                    # Change the leader's outer boundary to black
                    self.gui.canvas.itemconfig(drone.shape, outline="black")
                group_drones.append(drone)
                self.drones.append(drone)

            self.groups.append(group_drones)

        # Now assign trees to groups after all drones are created
        self.assign_trees_to_groups()

    def get_random_color(self):
        return f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"

# Tree creation
    def create_mango_trees(self, rows, cols, start_x):
        if self.map_type == "grid":
            return self.create_grid_mango_trees(rows, cols, start_x)
        elif self.map_type == "random":
            return self.create_random_mango_trees(rows, cols, start_x)

    def create_grid_mango_trees(self, rows, cols, start_x):
        trees = []
        margin_y = 50
        tree_size = 30
        gap = 20  # Gap between trees
        total_width = cols * (tree_size + gap) - gap
        total_height = rows * (tree_size + gap) - gap
        
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * (tree_size + gap) + tree_size / 2
                y = margin_y + row * (tree_size + gap) + tree_size / 2
                trees.append(MangoTree(self.gui.canvas, x, y, tree_size))

        self.gui.canvas.configure(scrollregion=(0, 0, start_x + total_width, margin_y + total_height))
        return trees

    def create_random_mango_trees(self, rows, cols, start_x):
        trees = []
        margin_y = 50
        tree_size = 30
        gap = 20  # Gap between trees

        # Calculate the total area used by the grid method
        total_width = cols * (tree_size + gap) - gap
        total_height = rows * (tree_size + gap) - gap

        # Calculate the number of trees to be plotted randomly
        num_trees = int(0.5 * rows * cols)

        # Create trees with random positions
        for _ in range(num_trees):
            attempts = 0
            while attempts < 100:  # Limit attempts to avoid infinite loop
                x = start_x + random.uniform(0, total_width)
                y = margin_y + random.uniform(0, total_height)
                
                # Check for overlap with existing trees
                overlap = any(
                    math.sqrt((tree.x - x)**2 + (tree.y - y)**2) < tree_size
                    for tree in trees
                )
                
                if not overlap:
                    trees.append(MangoTree(self.gui.canvas, x, y, tree_size))
                    break
                
                attempts += 1

        self.gui.canvas.configure(scrollregion=(0, 0, start_x + total_width, margin_y + total_height))
        return trees

# Area allocation
    def assign_trees_to_groups(self):
        trees_per_group = len(self.mango_trees) // self.no_of_groups
        extra_trees = len(self.mango_trees) % self.no_of_groups

        start_index = 0
        for i, group in enumerate(self.groups):
            end_index = start_index + trees_per_group + (1 if i < extra_trees else 0)
            group_trees = self.mango_trees[start_index:end_index]
            
            # Assign trees to the group
            for drone in group:
                drone.assigned_trees = group_trees.copy()  # Make a copy of the trees list for each drone

            start_index = end_index

    def allocate_rectangular_areas(self):
        trees_per_group = len(self.mango_trees) // self.no_of_groups
        extra_trees = len(self.mango_trees) % self.no_of_groups

        start_index = 0
        for i, group in enumerate(self.groups):
            end_index = start_index + trees_per_group + (1 if i < extra_trees else 0)
            allocated_trees = self.mango_trees[start_index:end_index]
            
            if allocated_trees:
                min_x = min(tree.x for tree in allocated_trees)
                min_y = min(tree.y for tree in allocated_trees)
                max_x = max(tree.x for tree in allocated_trees)
                max_y = max(tree.y for tree in allocated_trees)
                
                # Add some padding
                padding = 10
                bbox = self.gui.canvas.create_rectangle(
                    min_x - padding, min_y - padding,
                    max_x + padding, max_y + padding,
                    outline=group[0].color, width=2
                )
                self.bounding_boxes.append((group, bbox, allocated_trees))
                
                # Add group number to the bounding box
                self.gui.canvas.create_text(
                    (min_x + max_x) / 2,
                    min_y - 20,
                    text=f"Group {i+1}",
                    fill=group[0].color
                )

            # Assign trees to all drones in the group
            for drone in group:
                drone.assigned_trees = allocated_trees

            start_index = end_index

    def allocate_voronoi_areas(self):
        # Get tree positions
        tree_positions = np.array([(tree.x, tree.y) for tree in self.mango_trees])

        # Generate random points for Voronoi diagram
        num_points = min(self.no_of_groups, len(self.mango_trees))
        points = tree_positions[np.random.choice(len(tree_positions), num_points, replace=False)]

        # Compute Voronoi diagram
        vor = Voronoi(points)

        # Assign trees to regions
        tree_regions = [[] for _ in range(num_points)]
        for tree in self.mango_trees:
            distances = np.sqrt(np.sum((points - [tree.x, tree.y])**2, axis=1))
            closest_point = np.argmin(distances)
            tree_regions[closest_point].append(tree)

        # Create irregular bounding boxes
        for i, (group, region_trees) in enumerate(zip(self.groups, tree_regions)):
            if region_trees:
                hull = self.compute_convex_hull([(tree.x, tree.y) for tree in region_trees])
                
                # Create polygon on canvas
                polygon = self.gui.canvas.create_polygon(hull, outline=group[0].color, fill='', width=2)
                self.bounding_boxes.append((group, polygon, region_trees))
                
                # Add group number to the bounding box
                centroid = np.mean(hull, axis=0)
                self.gui.canvas.create_text(
                    centroid[0], centroid[1],
                    text=f"Group {i+1}",
                    fill=group[0].color
                )

                # Assign trees to all drones in the group
                for drone in group:
                    drone.assigned_trees = region_trees

    def compute_convex_hull(self, points):
        # Graham scan algorithm for convex hull
        def orientation(p, q, r):
            return (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])

        points = sorted(set(points))  # Remove duplicates and sort
        if len(points) <= 1:
            return points

        lower = []
        for p in points:
            while len(lower) >= 2 and orientation(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)

        upper = []
        for p in reversed(points):
            while len(upper) >= 2 and orientation(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)

        return lower[:-1] + upper[:-1]

# Task allocation
    def assign_tasks_to_drones(self):
        if self.sim_type == "heirarchical-box":
            self.assign_tasks_box()
        elif self.sim_type == "heirarchical-voronoi":
            self.assign_tasks_box()

    def assign_tasks_box(self):
        all_tasks_complete = all(tree.harvested for tree in self.mango_trees)

        for group, bbox, allocated_trees in self.bounding_boxes:
            unharvested_trees = [tree for tree in allocated_trees if not tree.harvested]

            for drone in group:
                if drone.target or drone.waiting or drone.has_mango:
                    continue

                if drone.charge <= 30:
                    drone.set_target(self.home.center_x, self.home.center_y)
                elif unharvested_trees:
                    available_trees = [tree for tree in unharvested_trees if not self.is_tree_targeted(tree)]
                    if available_trees:
                        target_tree = min(available_trees, key=lambda tree: ((drone.x - tree.x)**2 + (drone.y - tree.y)**2)**0.5)
                        drone.set_target(target_tree.x, target_tree.y)
                        self.targets[drone] = target_tree
                        unharvested_trees.remove(target_tree)
                elif all_tasks_complete and (drone.x, drone.y) != (self.home.center_x, self.home.center_y):
                    drone.return_home()

    def assign_tasks_voronoi(self):
        # Ensure Voronoi areas are allocated
        self.allocate_voronoi_areas()

        # Assign trees to drones within each Voronoi region
        for group, _, region_trees in self.bounding_boxes:
            for drone in group:
                drone.assigned_trees = region_trees

        # No need to draw Voronoi diagram again as it's already done in allocate_voronoi_areas
        print("Tasks assigned to drones based on Voronoi areas.")

    def is_tree_targeted(self, tree):
        return any(tree == target for target in self.targets.values())





if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1150x600")  # Set initial window size
    sim = Simulation(root)
    root.mainloop()