class MangoTree:
    def __init__(self, canvas, x, y, size=30):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.size = size
        self.harvested = False
        self.shape = canvas.create_rectangle(x-size/2, y-size/2, x+size/2, y+size/2, fill="green")

    def harvest(self):
        if not self.harvested:
            self.harvested = True
            self.canvas.itemconfig(self.shape, fill="brown")

class Station:
    def __init__(self, canvas, x, y, width, height, color, label):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.center_x = x + width / 2
        self.center_y = y + height / 2
        self.shape = canvas.create_rectangle(x, y, x+width, y+height, fill=color)
        self.label = canvas.create_text(x + width / 2, y + height / 2, text=label)

class MangoStorage(Station):
    def __init__(self, canvas, x, y, width, height):
        super().__init__(canvas, x, y, width, height, "yellow", "Mango Storage")
        self.mango_count = 0
        self.mango_count_display = canvas.create_text(x + width / 2, y + height / 2 + 15, text=f"Mangoes: {self.mango_count}")

    def update_mango_count(self):
        self.mango_count += 1
        self.canvas.itemconfig(self.mango_count_display, text=f"Mangoes: {self.mango_count}")