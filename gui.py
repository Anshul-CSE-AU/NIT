import tkinter as tk
from tkinter import ttk

class SimulationGUI:
    def __init__(self, master, start_callback, toggle_callback):
        self.master = master
        self.master.title("Mango Harvesting Simulation")

        # Create main frame
        main_frame = tk.Frame(master)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create canvas frame (left side)
        canvas_frame = tk.Frame(main_frame, width=1200, height=600)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create canvas with scrollbars
        self.canvas = tk.Canvas(canvas_frame, width=800, height=600, bg="lightgrey")
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create control panel frame (right side)
        control_frame = tk.Frame(main_frame, width=500, padx=10, pady=10)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Add controls to the control panel
        tk.Label(control_frame, text="Simulation Controls", font=("Arial", 14, "bold")).pack(pady=(0, 10))

        # Create a sub-frame for number of drones, rows, and columns
        entry_frame = tk.Frame(control_frame)
        entry_frame.pack(pady=(0, 10))

        # Number of Drones
        tk.Label(entry_frame, text="Drones:").grid(row=0, column=0, padx=(0, 10))
        self.entry_drones = tk.Entry(entry_frame, width=5)
        self.entry_drones.grid(row=0, column=1, padx=(0, 10))
        self.entry_drones.insert(0, "20")

        # Rows
        tk.Label(entry_frame, text="Rows:").grid(row=0, column=2, padx=(0, 10))
        self.entry_rows = tk.Entry(entry_frame, width=5)
        self.entry_rows.grid(row=0, column=3, padx=(0, 10))
        self.entry_rows.insert(0, "10")

        # Columns
        tk.Label(entry_frame, text="Columns:").grid(row=0, column=4, padx=(0, 10))
        self.entry_cols = tk.Entry(entry_frame, width=5)
        self.entry_cols.grid(row=0, column=5)
        self.entry_cols.insert(0, "10")

        # Create frames for simulation type and map type
        sim_map_frame = tk.Frame(control_frame)
        sim_map_frame.pack(pady=(10, 0), fill=tk.X)

        sim_type_frame = tk.Frame(sim_map_frame)
        sim_type_frame.pack(side=tk.LEFT, fill=tk.Y)

        map_type_frame = tk.Frame(sim_map_frame)
        map_type_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(20, 0))

        # Add radio buttons for drone simulation type
        self.sim_type = tk.StringVar(value="centralized-nearest")
        self.map_type = tk.StringVar(value="grid")

        tk.Label(sim_type_frame, text="Simulation Type:", font=("Arial", 12, "bold")).pack(pady=(10, 5), anchor=tk.W)
        tk.Radiobutton(sim_type_frame, text="Centralized - Nearest", variable=self.sim_type, value="centralized-nearest", command=self.update_map_options).pack(anchor=tk.W)
        self.allocate_1_radio = tk.Radiobutton(sim_type_frame, text="Centralized - Allocate 1", variable=self.sim_type, value="centralized-allocate-box", command=self.update_map_options)
        self.allocate_1_radio.pack(anchor=tk.W)
        tk.Radiobutton(sim_type_frame, text="Centralized - Allocate 2", variable=self.sim_type, value="centralized-allocate-voronoi", command=self.update_map_options).pack(anchor=tk.W)

        # Add radio buttons for map type
        tk.Label(map_type_frame, text="Map Type:", font=("Arial", 12, "bold")).pack(pady=(10, 5), anchor=tk.W)
        self.grid_radio = tk.Radiobutton(map_type_frame, text="Grid", variable=self.map_type, value="grid", command=self.update_sim_options)
        self.grid_radio.pack(anchor=tk.W)
        self.random_radio = tk.Radiobutton(map_type_frame, text="Random", variable=self.map_type, value="random", command=self.update_sim_options)
        self.random_radio.pack(anchor=tk.W)

        tk.Button(control_frame, text="Start", command=start_callback).pack(pady=(10, 0))
        tk.Button(control_frame, text="Stop/Continue", command=toggle_callback).pack(pady=(5, 0))

        # Message log panel
        tk.Label(control_frame, text="Message Log", font=("Arial", 12, "bold")).pack(pady=(20, 10))
        self.message_log = tk.Text(control_frame, width=30, height=15, state=tk.DISABLED)
        self.message_log.pack()

        # Initialize radio button states
        self.update_map_options()
        self.update_sim_options()

    def update_map_options(self):
        if self.sim_type.get() == "centralized-allocate-box":
            self.map_type.set("grid")
            self.random_radio.config(state=tk.DISABLED)
        else:
            self.random_radio.config(state=tk.NORMAL)

    def update_sim_options(self):
        if self.map_type.get() == "random":
            self.allocate_1_radio.config(state=tk.DISABLED)
        else:
            self.allocate_1_radio.config(state=tk.NORMAL)

    def log_message(self, message):
        self.message_log.config(state=tk.NORMAL)
        self.message_log.insert(tk.END, message + "\n")
        self.message_log.config(state=tk.DISABLED)
        self.message_log.yview(tk.END)  # Auto-scroll to the latest message

    def get_simulation_parameters(self):
        return {
            'drones': int(self.entry_drones.get()),
            'rows': int(self.entry_rows.get()),
            'columns': int(self.entry_cols.get()),
            'sim_type': self.sim_type.get(),
            'map_type': self.map_type.get()
        }