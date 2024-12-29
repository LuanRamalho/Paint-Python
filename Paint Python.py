import tkinter as tk
from tkinter.colorchooser import askcolor
from tkinter import filedialog
from PIL import Image, ImageDraw
import math


class PaintApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Paint App")

        # Configuração inicial
        self.brush_size = 5
        self.brush_color = "black"
        self.current_tool = "pencil"

        # Configuração do canvas para salvar
        self.image = Image.new("RGB", (800, 600), "white")
        self.draw = ImageDraw.Draw(self.image)

        # Interface de ferramentas
        self.create_tool_buttons()

        # Tela de desenho
        self.canvas = tk.Canvas(self.root, bg="white", width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

        # Botão de salvar
        self.save_button = tk.Button(
            self.root, text="Salvar como JPG", command=self.save_as_jpg
        )
        self.save_button.pack(side=tk.BOTTOM, pady=10)

        # Variáveis auxiliares
        self.start_x, self.start_y = None, None
        self.current_shape = None

    def create_tool_buttons(self):
        frame = tk.Frame(self.root, bg="lightgray", height=50)
        frame.pack(side=tk.TOP, fill=tk.X)

        # Botões de ferramentas
        tools = [
            ("Pincel", self.use_brush),
            ("Lápis", self.use_pencil),
            ("Rolo", self.fill_shape),
            ("Selecionar Cor", self.choose_color),
            ("Círculo", lambda: self.set_tool("circle")),
            ("Retângulo", lambda: self.set_tool("rectangle")),
            ("Triângulo", lambda: self.set_tool("triangle")),
            ("Quadrado", lambda: self.set_tool("square")),
            ("Estrela", lambda: self.set_tool("star")),
            ("Linha", lambda: self.set_tool("line")),
            ("Borracha", self.use_eraser),
        ]

        for text, command in tools:
            button = tk.Button(frame, text=text, command=command, width=10)
            button.pack(side=tk.LEFT, padx=2, pady=2)

    def use_brush(self):
        self.current_tool = "brush"

    def use_pencil(self):
        self.current_tool = "pencil"

    def use_eraser(self):
        self.current_tool = "eraser"
        self.brush_color = "white"

    def fill_shape(self):
        if self.current_tool == "fill":
            # Preenche toda a tela
            self.canvas.create_rectangle(
                0, 0, self.canvas.winfo_width(), self.canvas.winfo_height(),
                outline=self.brush_color,
                fill=self.brush_color
            )
            self.draw.rectangle(
                [0, 0, self.image.width, self.image.height],
                fill=self.brush_color
            )
        elif self.current_shape in ["circle", "rectangle", "triangle", "square", "star"]:
            # Preenche o último polígono desenhado
            if self.current_shape:
                self.canvas.itemconfig(self.current_shape, fill=self.brush_color)
        else:
            # Caso nenhum polígono seja desenhado
            self.canvas.create_rectangle(
                0, 0, self.canvas.winfo_width(), self.canvas.winfo_height(),
                outline=self.brush_color,
                fill=self.brush_color
            )
            self.draw.rectangle(
                [0, 0, self.image.width, self.image.height],
                fill=self.brush_color
            )


    def choose_color(self):
        color = askcolor()[1]
        if color:
            self.brush_color = color

    def set_tool(self, tool_name):
        self.current_tool = tool_name

    def start_draw(self, event):
        self.start_x, self.start_y = event.x, event.y
        if self.current_tool in ["circle", "rectangle", "triangle", "square", "line", "star"]:
            self.current_shape = None

    def stop_draw(self, event):
        if self.current_tool == "triangle":
            points = [
                (self.start_x, self.start_y),
                (event.x, event.y),
                ((self.start_x + event.x) // 2, self.start_y - abs(event.x - self.start_x)),
            ]
            self.current_shape = self.canvas.create_polygon(points, outline=self.brush_color, fill=self.brush_color)
            self.draw.polygon(points, outline=self.brush_color, fill=self.brush_color)
        elif self.current_tool == "circle":
            self.current_shape = self.canvas.create_oval(
                self.start_x, self.start_y, event.x, event.y, outline=self.brush_color, fill=self.brush_color
            )
            self.draw.ellipse(
                [self.start_x, self.start_y, event.x, event.y],
                outline=self.brush_color,
                fill=self.brush_color,
            )
        elif self.current_tool == "rectangle":
            self.current_shape = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y, outline=self.brush_color, fill=self.brush_color
            )
            self.draw.rectangle(
                [self.start_x, self.start_y, event.x, event.y],
                outline=self.brush_color,
                fill=self.brush_color,
            )
        elif self.current_tool == "square":
            side = min(abs(event.x - self.start_x), abs(event.y - self.start_y))
            x1, y1 = self.start_x, self.start_y
            x2, y2 = (x1 + side, y1 + side) if event.x > x1 else (x1 - side, y1 - side)
            self.current_shape = self.canvas.create_rectangle(x1, y1, x2, y2, outline=self.brush_color, fill=self.brush_color)
            self.draw.rectangle([x1, y1, x2, y2], outline=self.brush_color, fill=self.brush_color)
        elif self.current_tool == "star":
            cx, cy = (self.start_x + event.x) // 2, (self.start_y + event.y) // 2
            radius = min(abs(event.x - self.start_x), abs(event.y - self.start_y)) // 2
            points = []
            for i in range(10):
                angle = math.pi / 5 * i
                r = radius if i % 2 == 0 else radius // 2
                x = cx + r * math.cos(angle)
                y = cy - r * math.sin(angle)
                points.append((x, y))
            self.current_shape = self.canvas.create_polygon(points, outline=self.brush_color, fill=self.brush_color)
            self.draw.polygon(points, outline=self.brush_color, fill=self.brush_color)
        elif self.current_tool == "line":
            self.current_shape = self.canvas.create_line(
                self.start_x, self.start_y, event.x, event.y, fill=self.brush_color, width=self.brush_size
            )
            self.draw.line(
                [self.start_x, self.start_y, event.x, event.y],
                fill=self.brush_color,
                width=self.brush_size,
            )
        else:
            pass


    def paint(self, event):
        if self.current_tool == "brush":
            self.canvas.create_oval(
                event.x - self.brush_size,
                event.y - self.brush_size,
                event.x + self.brush_size,
                event.y + self.brush_size,
                fill=self.brush_color,
                outline=self.brush_color,
            )
            self.draw.ellipse(
                [
                    event.x - self.brush_size,
                    event.y - self.brush_size,
                    event.x + self.brush_size,
                    event.y + self.brush_size,
                ],
                fill=self.brush_color,
                outline=self.brush_color,
            )
        elif self.current_tool == "pencil":
            self.canvas.create_line(
                self.start_x, self.start_y, event.x, event.y, fill=self.brush_color, width=1
            )
            self.draw.line(
                [self.start_x, self.start_y, event.x, event.y],
                fill=self.brush_color,
                width=1,
            )
            self.start_x, self.start_y = event.x, event.y
        elif self.current_tool == "eraser":
            self.canvas.create_rectangle(
                event.x - self.brush_size,
                event.y - self.brush_size,
                event.x + self.brush_size,
                event.y + self.brush_size,
                fill="white",
                outline="white",
            )
            self.draw.rectangle(
                [
                    event.x - self.brush_size,
                    event.y - self.brush_size,
                    event.x + self.brush_size,
                    event.y + self.brush_size,
                ],
                fill="white",
                outline="white",
            )


    def save_as_jpg(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG files", "*.jpg"), ("All files", "*.*")],
        )
        if file_path:
            self.image.save(file_path, "JPEG")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = PaintApp(root)
    app.run()
