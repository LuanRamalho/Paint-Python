"""
Paint Clone - Clone do Microsoft Paint em Python
Desenvolvido com Tkinter + Pillow
Ferramentas: lápis, caneta, giz de cera, spray, texto, borracha,
             rolo de tinta, linha, e múltiplos polígonos.
"""

import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
import math
import random
from PIL import Image, ImageDraw, ImageTk, ImageFont

# ──────────────────────────────────────────────────────────────────────────────
# Constantes de layout
# ──────────────────────────────────────────────────────────────────────────────
CANVAS_W = 1400
CANVAS_H = 800
TOOL_BTN_W = 7
HISTORY_LIMIT = 30

TOOLS = [
    ("✏  Lápis",        "pencil"),
    ("🖊  Caneta",       "pen"),
    ("🖍  Giz de Cera",  "crayon"),
    ("💨  Spray",        "spray"),
    ("T   Texto",        "text"),
    ("⬜  Borracha",     "eraser"),
    ("🪣  Rolo/Balde",   "fill"),
    ("╱   Linha",        "line"),
    ("▭   Retângulo",    "rectangle"),
    ("■   Quadrado",     "square"),
    ("△   Triângulo",    "triangle"),
    ("▷   Seta →",       "arrow_right"),
    ("◁   Seta ←",       "arrow_left"),
    ("△   Seta ↑",       "arrow_up"),
    ("▽   Seta ↓",       "arrow_down"),
    ("◇   Diamante",     "diamond"),
    ("⬠   Pentágono",    "pentagon"),
    ("⬡   Hexágono",     "hexagon"),
    ("⯃   Octógono",     "octagon"),
    ("★   Estrela 5pts", "star5"),
    ("✡   Estrela 6pts", "star6"),
    ("☁   Nuvem",        "cloud"),
    ("♥   Coração",      "heart"),
]

PALETTE = [
    "#000000","#3c3c3c","#7f7f7f","#c3c3c3","#ffffff",
    "#880015","#b5122e","#ed1c24","#ff7f27","#ffc90e",
    "#efe4b0","#22b14c","#00a2e8","#3f48cc","#a349a4",
    "#ff00ff","#ff006e","#99d9ea","#b97a57","#c8bfe7",
    "#ffaec9","#ffd966","#b5e61d","#00e0ff","#7092be",
    "#99004c","#4d004d","#004d00","#004080","#7f3300",
]


class PaintApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Paint — Clone Completo")
        try:
            self.root.state("zoomed")
        except Exception:
            self.root.attributes("-zoomed", True)

        # ── Estado da aplicação ──────────────────────────────────────────────
        self.current_tool   = "pencil"
        self.current_color  = "#000000"
        self.brush_size     = 3
        self.fill_shapes    = tk.BooleanVar(value=False)
        self.font_size_var  = tk.IntVar(value=18)
        self.size_var       = tk.IntVar(value=3)

        # Controle de mouse
        self.drawing  = False
        self.start_x  = 0
        self.start_y  = 0
        self.last_x   = 0
        self.last_y   = 0
        self.temp_id  = None   # item temporário de preview

        # Texto
        self.text_entry   = None
        self.text_win_id  = None
        self.text_pos     = (0, 0)

        # PIL – imagem de trabalho
        self.image = Image.new("RGB", (CANVAS_W, CANVAS_H), "white")
        self.draw  = ImageDraw.Draw(self.image)

        # Histórico de desfazer
        self.history: list[Image.Image] = []

        # Referência ao PhotoImage atual (evita garbage collection)
        self._tk_img: ImageTk.PhotoImage | None = None

        self._build_ui()
        self._refresh_display()   # mostra o canvas branco inicial

    # ══════════════════════════════════════════════════════════════════════════
    # Construção da interface
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        self._build_menu()

        # Frame raiz
        root_frame = tk.Frame(self.root, bg="#d4d0c8")
        root_frame.pack(fill=tk.BOTH, expand=True)

        self._build_top_toolbar(root_frame)

        content = tk.Frame(root_frame, bg="#808080")
        content.pack(fill=tk.BOTH, expand=True)

        self._build_tools_panel(content)
        self._build_canvas_area(content)
        self._build_color_palette(root_frame)
        self._build_statusbar(root_frame)

    # ── Menu ─────────────────────────────────────────────────────────────────

    def _build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Novo          Ctrl+N", command=self._new_canvas)
        file_menu.add_separator()
        file_menu.add_command(label="Salvar como…  Ctrl+S", command=self._save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)
        menubar.add_cascade(label="Arquivo", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Desfazer  Ctrl+Z", command=self._undo)
        edit_menu.add_command(label="Limpar tudo",      command=self._clear_canvas)
        menubar.add_cascade(label="Editar", menu=edit_menu)

        self.root.config(menu=menubar)
        self.root.bind("<Control-z>", lambda e: self._undo())
        self.root.bind("<Control-n>", lambda e: self._new_canvas())
        self.root.bind("<Control-s>", lambda e: self._save_file())

    # ── Barra de ferramentas superior ─────────────────────────────────────────

    def _build_top_toolbar(self, parent):
        bar = tk.Frame(parent, bg="#d4d0c8", relief=tk.RAISED, bd=2, height=48)
        bar.pack(side=tk.TOP, fill=tk.X, pady=(2, 0))
        bar.pack_propagate(False)

        # Tamanho do pincel
        tk.Label(bar, text="Tamanho:", bg="#d4d0c8").pack(side=tk.LEFT, padx=(8, 2))
        size_scale = ttk.Scale(bar, from_=1, to=60, variable=self.size_var,
                               orient=tk.HORIZONTAL, length=120,
                               command=self._on_size_change)
        size_scale.pack(side=tk.LEFT, padx=2)
        self.size_lbl = tk.Label(bar, text=" 3px", bg="#d4d0c8", width=5, anchor="w")
        self.size_lbl.pack(side=tk.LEFT)

        tk.Label(bar, text="│", bg="#d4d0c8", fg="#888").pack(side=tk.LEFT, padx=4)

        # Preenchimento
        ttk.Checkbutton(bar, text="Preencher formas", variable=self.fill_shapes).pack(side=tk.LEFT, padx=6)

        tk.Label(bar, text="│", bg="#d4d0c8", fg="#888").pack(side=tk.LEFT, padx=4)

        # Tamanho da fonte
        tk.Label(bar, text="Fonte:", bg="#d4d0c8").pack(side=tk.LEFT, padx=2)
        ttk.Spinbox(bar, from_=8, to=96, textvariable=self.font_size_var, width=4).pack(side=tk.LEFT, padx=2)

        tk.Label(bar, text="│", bg="#d4d0c8", fg="#888").pack(side=tk.LEFT, padx=4)

        # Cor atual
        tk.Label(bar, text="Cor:", bg="#d4d0c8").pack(side=tk.LEFT, padx=2)
        self.color_box = tk.Label(bar, bg=self.current_color, width=4, height=1,
                                  relief=tk.RAISED, bd=2, cursor="hand2")
        self.color_box.pack(side=tk.LEFT, padx=4)
        self.color_box.bind("<Button-1>", self._choose_color)

        tk.Button(bar, text="Escolher Cor…", command=self._choose_color,
                  relief=tk.RAISED, padx=4).pack(side=tk.LEFT, padx=4)

        # Botões rápidos (direita)
        tk.Button(bar, text="💾 Salvar", bg="#4a9e4a", fg="white",
                  command=self._save_file, padx=6, relief=tk.RAISED).pack(side=tk.RIGHT, padx=6)
        tk.Button(bar, text="↩ Desfazer", bg="#5b9bd5", fg="white",
                  command=self._undo, padx=6, relief=tk.RAISED).pack(side=tk.RIGHT, padx=4)
        tk.Button(bar, text="🗑 Limpar", bg="#c0392b", fg="white",
                  command=self._clear_canvas, padx=6, relief=tk.RAISED).pack(side=tk.RIGHT, padx=4)

    # ── Painel de ferramentas (lateral esquerda) ───────────────────────────────

    def _build_tools_panel(self, parent):
        panel = tk.Frame(parent, bg="#d4d0c8", width=120, relief=tk.RAISED, bd=2)
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=(4, 2), pady=4)
        panel.pack_propagate(False)

        tk.Label(panel, text="Ferramentas", bg="#d4d0c8",
                 font=("Arial", 8, "bold")).pack(pady=(6, 2))
        ttk.Separator(panel, orient="horizontal").pack(fill=tk.X, padx=4)

        self.tool_buttons: dict[str, tk.Button] = {}
        for label, name in TOOLS:
            btn = tk.Button(
                panel, text=label,
                anchor="w", padx=4,
                font=("Arial", 9),
                bg="#d4d0c8", relief=tk.RAISED,
                width=TOOL_BTN_W,
                command=lambda n=name: self._select_tool(n),
            )
            btn.pack(fill=tk.X, padx=4, pady=1)
            self.tool_buttons[name] = btn

        self._select_tool("pencil")

    # ── Área do canvas ────────────────────────────────────────────────────────

    def _build_canvas_area(self, parent):
        frame = tk.Frame(parent, bg="#696969")
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)

        h_scroll = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        v_scroll = tk.Scrollbar(frame, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = tk.Canvas(
            frame,
            width=CANVAS_W, height=CANVAS_H,
            bg="white",
            cursor="crosshair",
            xscrollcommand=h_scroll.set,
            yscrollcommand=v_scroll.set,
            scrollregion=(0, 0, CANVAS_W, CANVAS_H),
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        h_scroll.config(command=self.canvas.xview)
        v_scroll.config(command=self.canvas.yview)

        # Tag da imagem de fundo (sempre embaixo)
        self.bg_img_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=None, tags="bg")

        # Eventos do mouse
        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",        self._on_drag)
        self.canvas.bind("<ButtonRelease-1>",  self._on_release)
        self.canvas.bind("<Motion>",           self._on_move)

    # ── Paleta de cores ───────────────────────────────────────────────────────

    def _build_color_palette(self, parent):
        pal_frame = tk.Frame(parent, bg="#d4d0c8", relief=tk.RAISED, bd=2, height=50)
        pal_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=4, pady=(0, 2))
        pal_frame.pack_propagate(False)

        # Cor atual grande
        left = tk.Frame(pal_frame, bg="#d4d0c8")
        left.pack(side=tk.LEFT, padx=8, pady=4)
        tk.Label(left, text="Cor:", bg="#d4d0c8", font=("Arial", 8)).pack()
        self.pal_preview = tk.Label(left, bg=self.current_color,
                                    width=5, height=1,
                                    relief=tk.SUNKEN, bd=2, cursor="hand2")
        self.pal_preview.pack()
        self.pal_preview.bind("<Button-1>", self._choose_color)

        # Grid de cores
        colors_frame = tk.Frame(pal_frame, bg="#d4d0c8")
        colors_frame.pack(side=tk.LEFT, pady=4)
        for i, color in enumerate(PALETTE):
            lbl = tk.Label(colors_frame, bg=color, width=2, height=1,
                           relief=tk.RAISED, bd=1, cursor="hand2")
            lbl.grid(row=i // 15, column=i % 15, padx=1, pady=1)
            lbl.bind("<Button-1>", lambda e, c=color: self._set_color(c))

    # ── Status bar ────────────────────────────────────────────────────────────

    def _build_statusbar(self, parent):
        self.status_var = tk.StringVar(value="Pronto  |  Lápis")
        bar = tk.Label(parent, textvariable=self.status_var,
                       bd=1, relief=tk.SUNKEN, anchor=tk.W,
                       bg="#d4d0c8", font=("Arial", 8))
        bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ══════════════════════════════════════════════════════════════════════════
    # Helpers de coordenadas / display
    # ══════════════════════════════════════════════════════════════════════════

    def _canvas_xy(self, event) -> tuple[float, float]:
        return self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

    def _refresh_display(self):
        """Atualiza a imagem exibida no canvas a partir do PIL."""
        self._tk_img = ImageTk.PhotoImage(self.image)
        self.canvas.itemconfig(self.bg_img_id, image=self._tk_img)
        self.canvas.tag_lower("bg")

    def _push_history(self):
        if len(self.history) >= HISTORY_LIMIT:
            self.history.pop(0)
        self.history.append(self.image.copy())

    # ══════════════════════════════════════════════════════════════════════════
    # Seleção de ferramenta / cor / tamanho
    # ══════════════════════════════════════════════════════════════════════════

    def _select_tool(self, name: str):
        # Cancelar texto em edição se trocar de ferramenta
        if self.current_tool == "text" and name != "text":
            self._commit_text()

        self.current_tool = name
        for n, btn in self.tool_buttons.items():
            btn.config(relief=tk.SUNKEN if n == name else tk.RAISED,
                       bg="#b0b0b0" if n == name else "#d4d0c8")

        cursors = {"eraser": "dotbox", "fill": "spraycan", "text": "xterm"}
        if hasattr(self, "canvas"):
            self.canvas.config(cursor=cursors.get(name, "crosshair"))
        if hasattr(self, "status_var"):
            self.status_var.set(f"Ferramenta: {name}")

    def _on_size_change(self, _=None):
        self.brush_size = self.size_var.get()
        self.size_lbl.config(text=f"{self.brush_size}px")

    def _choose_color(self, _=None):
        result = colorchooser.askcolor(color=self.current_color, title="Escolher Cor")
        if result and result[1]:
            self._set_color(result[1])

    def _set_color(self, color: str):
        self.current_color = color
        self.color_box.config(bg=color)
        self.pal_preview.config(bg=color)

    # ══════════════════════════════════════════════════════════════════════════
    # Eventos do mouse
    # ══════════════════════════════════════════════════════════════════════════

    def _on_press(self, event):
        x, y = self._canvas_xy(event)
        self.start_x, self.start_y = x, y
        self.last_x,  self.last_y  = x, y
        self.drawing = True

        tool = self.current_tool
        if tool == "fill":
            self._push_history()
            self._flood_fill(int(x), int(y))
        elif tool == "text":
            self._start_text(x, y)
        elif tool == "spray":
            self._push_history()
            self._do_spray(x, y)
        elif tool in ("pencil", "pen", "crayon", "eraser"):
            self._push_history()

    def _on_drag(self, event):
        if not self.drawing:
            return
        x, y = self._canvas_xy(event)

        tool = self.current_tool
        if tool in ("pencil", "pen", "crayon"):
            self._freehand(x, y)
        elif tool == "eraser":
            self._do_erase(x, y)
        elif tool == "spray":
            self._do_spray(x, y)
        elif tool in self._shape_tools():
            self._preview_shape(x, y)

        self.last_x, self.last_y = x, y

    def _on_release(self, event):
        if not self.drawing:
            return
        x, y = self._canvas_xy(event)

        tool = self.current_tool
        if tool in self._shape_tools():
            self._push_history()
            self._finalize_shape(x, y)

        # Apagar preview temporário
        if self.temp_id is not None:
            self.canvas.delete(self.temp_id)
            self.temp_id = None

        # Atualizar display para ferramentas freehand
        if tool in ("pencil", "pen", "crayon", "eraser", "spray"):
            self._refresh_display()

        self.drawing = False

    def _on_move(self, event):
        x, y = self._canvas_xy(event)
        self.status_var.set(
            f"X: {int(x)}  Y: {int(y)}   |   Ferramenta: {self.current_tool}   |   "
            f"Tamanho: {self.brush_size}px"
        )

    @staticmethod
    def _shape_tools():
        return {"line", "rectangle", "square", "triangle",
                "arrow_right", "arrow_left", "arrow_up", "arrow_down",
                "diamond", "pentagon", "hexagon", "octagon",
                "star5", "star6", "cloud", "heart"}

    # ══════════════════════════════════════════════════════════════════════════
    # Ferramentas de desenho livre
    # ══════════════════════════════════════════════════════════════════════════

    def _freehand(self, x, y):
        tool  = self.current_tool
        color = self.current_color
        size  = max(1, self.brush_size)

        if tool == "pencil":
            self.canvas.create_line(self.last_x, self.last_y, x, y,
                                    fill=color, width=size,
                                    capstyle=tk.ROUND, smooth=True)
            self.draw.line([self.last_x, self.last_y, x, y],
                           fill=color, width=size)

        elif tool == "pen":
            w = max(1, int(size * 1.8))
            self.canvas.create_line(self.last_x, self.last_y, x, y,
                                    fill=color, width=w,
                                    capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True)
            self.draw.line([self.last_x, self.last_y, x, y],
                           fill=color, width=w)

        elif tool == "crayon":
            # Efeito de textura com múltiplos traços levemente deslocados
            for _ in range(max(2, size)):
                ox = random.randint(-max(1, size // 2), max(1, size // 2))
                oy = random.randint(-max(1, size // 2), max(1, size // 2))
                self.canvas.create_line(
                    self.last_x + ox, self.last_y + oy, x + ox, y + oy,
                    fill=color, width=1, capstyle=tk.ROUND)
                self.draw.line(
                    [self.last_x + ox, self.last_y + oy, x + ox, y + oy],
                    fill=color, width=1)

    def _do_erase(self, x, y):
        s = max(4, self.brush_size * 3)
        x0, y0, x1, y1 = x - s, y - s, x + s, y + s
        self.canvas.create_rectangle(x0, y0, x1, y1, fill="white", outline="white")
        self.draw.rectangle([x0, y0, x1, y1], fill="white")

    def _do_spray(self, x, y):
        color  = self.current_color
        radius = max(8, self.brush_size * 4)
        dots   = max(10, self.brush_size * 5)
        for _ in range(dots):
            angle = random.uniform(0, 2 * math.pi)
            r     = random.uniform(0, radius)
            px    = x + r * math.cos(angle)
            py    = y + r * math.sin(angle)
            self.canvas.create_oval(px - 1, py - 1, px + 1, py + 1,
                                    fill=color, outline=color)
            self.draw.ellipse([px - 1, py - 1, px + 1, py + 1], fill=color)

    # ══════════════════════════════════════════════════════════════════════════
    # Formas geométricas
    # ══════════════════════════════════════════════════════════════════════════

    def _get_shape(self, tool, x0, y0, x1, y1):
        """Retorna (pontos, tipo) para o tool selecionado."""
        cx   = (x0 + x1) / 2
        cy   = (y0 + y1) / 2
        rx   = abs(x1 - x0) / 2
        ry   = abs(y1 - y0) / 2
        r    = min(rx, ry)

        if tool == "line":
            return [x0, y0, x1, y1], "line"

        if tool == "rectangle":
            return [x0, y0, x1, y1], "rectangle"

        if tool == "square":
            side = min(abs(x1 - x0), abs(y1 - y0))
            sx   = x0 + (side if x1 >= x0 else -side)
            sy   = y0 + (side if y1 >= y0 else -side)
            return [x0, y0, sx, sy], "rectangle"

        if tool == "triangle":
            return [cx, y0, x0, y1, x1, y1], "polygon"

        if tool == "diamond":
            return [cx, y0, x1, cy, cx, y1, x0, cy], "polygon"

        if tool == "pentagon":
            return self._reg_polygon(5, cx, cy, r, -math.pi / 2), "polygon"

        if tool == "hexagon":
            return self._reg_polygon(6, cx, cy, r, 0), "polygon"

        if tool == "octagon":
            return self._reg_polygon(8, cx, cy, r, math.pi / 8), "polygon"

        if tool == "star5":
            return self._star_polygon(5, cx, cy, r, r * 0.4), "polygon"

        if tool == "star6":
            return self._star_polygon(6, cx, cy, r, r * 0.5), "polygon"

        if tool == "arrow_right":
            return self._arrow_right(x0, y0, x1, y1), "polygon"

        if tool == "arrow_left":
            return self._arrow_left(x0, y0, x1, y1), "polygon"

        if tool == "arrow_up":
            return self._arrow_up(x0, y0, x1, y1), "polygon"

        if tool == "arrow_down":
            return self._arrow_down(x0, y0, x1, y1), "polygon"

        if tool == "cloud":
            return self._cloud_points(x0, y0, x1, y1), "polygon"

        if tool == "heart":
            return self._heart_points(cx, cy, r), "polygon"

        return [x0, y0, x1, y1], "rectangle"

    @staticmethod
    def _reg_polygon(n, cx, cy, r, start):
        pts = []
        for i in range(n):
            a = start + 2 * math.pi * i / n
            pts.extend([cx + r * math.cos(a), cy + r * math.sin(a)])
        return pts

    @staticmethod
    def _star_polygon(n, cx, cy, outer, inner):
        pts = []
        for i in range(n * 2):
            a = -math.pi / 2 + math.pi * i / n
            r = outer if i % 2 == 0 else inner
            pts.extend([cx + r * math.cos(a), cy + r * math.sin(a)])
        return pts

    @staticmethod
    def _arrow_right(x0, y0, x1, y1):
        cy      = (y0 + y1) / 2
        w       = x1 - x0 or 1
        h       = y1 - y0 or 1
        head_l  = abs(w) * 0.35
        head_hw = abs(h) * 0.48
        shaft_h = abs(h) * 0.22
        return [
            x0,           cy - shaft_h,
            x1 - head_l,  cy - shaft_h,
            x1 - head_l,  cy - head_hw,
            x1,           cy,
            x1 - head_l,  cy + head_hw,
            x1 - head_l,  cy + shaft_h,
            x0,           cy + shaft_h,
        ]

    @staticmethod
    def _arrow_left(x0, y0, x1, y1):
        cy      = (y0 + y1) / 2
        w       = x1 - x0 or 1
        h       = y1 - y0 or 1
        head_l  = abs(w) * 0.35
        head_hw = abs(h) * 0.48
        shaft_h = abs(h) * 0.22
        return [
            x1,           cy - shaft_h,
            x0 + head_l,  cy - shaft_h,
            x0 + head_l,  cy - head_hw,
            x0,           cy,
            x0 + head_l,  cy + head_hw,
            x0 + head_l,  cy + shaft_h,
            x1,           cy + shaft_h,
        ]

    @staticmethod
    def _arrow_up(x0, y0, x1, y1):
        cx      = (x0 + x1) / 2
        w       = x1 - x0 or 1
        h       = y1 - y0 or 1
        head_h  = abs(h) * 0.35
        head_hw = abs(w) * 0.48
        shaft_w = abs(w) * 0.22
        return [
            cx - shaft_w,  y1,
            cx - shaft_w,  y0 + head_h,
            cx - head_hw,  y0 + head_h,
            cx,            y0,
            cx + head_hw,  y0 + head_h,
            cx + shaft_w,  y0 + head_h,
            cx + shaft_w,  y1,
        ]

    @staticmethod
    def _arrow_down(x0, y0, x1, y1):
        cx      = (x0 + x1) / 2
        w       = x1 - x0 or 1
        h       = y1 - y0 or 1
        head_h  = abs(h) * 0.35
        head_hw = abs(w) * 0.48
        shaft_w = abs(w) * 0.22
        return [
            cx - shaft_w,  y0,
            cx - shaft_w,  y1 - head_h,
            cx - head_hw,  y1 - head_h,
            cx,            y1,
            cx + head_hw,  y1 - head_h,
            cx + shaft_w,  y1 - head_h,
            cx + shaft_w,  y0,
        ]

    @staticmethod
    def _cloud_points(x0, y0, x1, y1):
        """Polígono aproximado de nuvem com muitos lados (círculos sobrepostos)."""
        pts = []
        w   = (x1 - x0) or 1
        h   = (y1 - y0) or 1
        cx  = (x0 + x1) / 2
        cy  = (y0 + y1) / 2
        # Série de círculos na borda superior + base reta
        bumps = 6
        for i in range(bumps):
            angle_start = math.pi + math.pi * i / bumps
            angle_end   = math.pi + math.pi * (i + 1) / bumps
            bx = x0 + w * (i + 0.5) / bumps
            by = y0 + h * 0.35
            br = (w / bumps) * 0.65
            for step in range(10):
                a = angle_start + (angle_end - angle_start) * step / 9
                pts.extend([bx + br * math.cos(a), by + br * math.sin(a)])
        # Base reta
        pts.extend([x1, y1, x0, y1])
        return pts

    @staticmethod
    def _heart_points(cx, cy, r):
        pts = []
        steps = 60
        for i in range(steps):
            t = 2 * math.pi * i / steps - math.pi / 2
            hx = cx + r * 16 * math.sin(t) ** 3 / 17
            hy = cy - r * (13 * math.cos(t) - 5 * math.cos(2 * t)
                           - 2 * math.cos(3 * t) - math.cos(4 * t)) / 17
            pts.extend([hx, hy])
        return pts

    # ── Preview e finalização ─────────────────────────────────────────────────

    def _preview_shape(self, x, y):
        if self.temp_id is not None:
            self.canvas.delete(self.temp_id)
            self.temp_id = None

        pts, stype = self._get_shape(self.current_tool, self.start_x, self.start_y, x, y)
        color = self.current_color
        fill  = color if self.fill_shapes.get() else ""
        size  = max(1, self.brush_size)

        if stype == "line":
            self.temp_id = self.canvas.create_line(*pts, fill=color, width=size, dash=(4, 2))
        elif stype == "rectangle":
            self.temp_id = self.canvas.create_rectangle(*pts, outline=color, fill=fill, width=size, dash=(4, 2))
        elif stype == "polygon":
            self.temp_id = self.canvas.create_polygon(pts, outline=color, fill=fill, width=size)

    def _finalize_shape(self, x, y):
        pts, stype = self._get_shape(self.current_tool, self.start_x, self.start_y, x, y)
        color     = self.current_color
        fill_c    = color if self.fill_shapes.get() else None
        size      = max(1, self.brush_size)

        if stype == "line":
            self.canvas.create_line(*pts, fill=color, width=size, capstyle=tk.ROUND)
            self.draw.line(pts, fill=color, width=size)

        elif stype == "rectangle":
            x0, y0, x1, y1 = pts
            self.canvas.create_rectangle(x0, y0, x1, y1,
                                         outline=color, fill=fill_c or "", width=size)
            self.draw.rectangle([x0, y0, x1, y1],
                                outline=color, fill=fill_c, width=size)

        elif stype == "polygon":
            self.canvas.create_polygon(pts, outline=color,
                                       fill=fill_c or "", width=size)
            pairs = [(pts[i], pts[i + 1]) for i in range(0, len(pts), 2)]
            self.draw.polygon(pairs, outline=color, fill=fill_c)

        self._refresh_display()

    # ══════════════════════════════════════════════════════════════════════════
    # Ferramenta de texto
    # ══════════════════════════════════════════════════════════════════════════

    def _start_text(self, x, y):
        self._commit_text()   # confirma qualquer texto anterior
        self.text_pos = (x, y)

        entry = tk.Entry(
            self.canvas,
            font=("Arial", self.font_size_var.get()),
            fg=self.current_color,
            bg="white",
            bd=1,
            relief=tk.SOLID,
            insertbackground=self.current_color,
            width=22,
        )
        self.text_win_id = self.canvas.create_window(x, y, window=entry,
                                                     anchor="nw", tags="text_win")
        entry.focus_set()
        entry.bind("<Return>",  lambda _: self._commit_text())
        entry.bind("<Escape>",  lambda _: self._cancel_text())
        self.text_entry = entry

    def _commit_text(self):
        if self.text_entry is None:
            return
        text = self.text_entry.get().strip()
        x, y = self.text_pos
        if text:
            fs    = self.font_size_var.get()
            color = self.current_color
            self._push_history()
            try:
                pil_font = ImageFont.truetype("arial.ttf", fs)
            except Exception:
                try:
                    pil_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", fs)
                except Exception:
                    pil_font = ImageFont.load_default()
            self.draw.text((x, y), text, fill=color, font=pil_font)
            self._refresh_display()
        self._cancel_text()

    def _cancel_text(self):
        if self.text_win_id is not None:
            self.canvas.delete(self.text_win_id)
            self.text_win_id = None
        if self.text_entry is not None:
            self.text_entry.destroy()
            self.text_entry = None

    # ══════════════════════════════════════════════════════════════════════════
    # Rolo / balde de tinta (flood fill)
    # ══════════════════════════════════════════════════════════════════════════

    def _flood_fill(self, x: int, y: int):
        if not (0 <= x < CANVAS_W and 0 <= y < CANVAS_H):
            return
        fill_rgb = self._hex2rgb(self.current_color)
        try:
            from PIL import ImageDraw as _ID
            _ID.floodfill(self.image, (x, y), fill_rgb, thresh=20)
            self.draw = ImageDraw.Draw(self.image)
        except Exception:
            # fallback BFS manual
            target = self.image.getpixel((x, y))[:3]
            if target == fill_rgb:
                return
            self._bfs_fill(x, y, target, fill_rgb)
        self._refresh_display()

    def _bfs_fill(self, sx, sy, target, replacement):
        from collections import deque
        pixels = self.image.load()
        queue  = deque([(sx, sy)])
        visited: set[tuple[int, int]] = set()

        while queue:
            cx, cy = queue.popleft()
            if (cx, cy) in visited:
                continue
            if not (0 <= cx < CANVAS_W and 0 <= cy < CANVAS_H):
                continue
            if pixels[cx, cy][:3] != target:
                continue
            visited.add((cx, cy))
            pixels[cx, cy] = replacement
            queue.extend([(cx + 1, cy), (cx - 1, cy),
                           (cx, cy + 1), (cx, cy - 1)])

    # ══════════════════════════════════════════════════════════════════════════
    # Operações de canvas
    # ══════════════════════════════════════════════════════════════════════════

    def _new_canvas(self):
        if messagebox.askyesno("Novo canvas",
                               "Criar um novo canvas?\nO conteúdo atual será perdido."):
            self._clear_canvas(confirm=False)

    def _clear_canvas(self, confirm=True):
        if confirm and not messagebox.askyesno("Limpar tudo", "Apagar tudo do canvas?"):
            return
        self._push_history()
        self.canvas.delete("all")
        self.image = Image.new("RGB", (CANVAS_W, CANVAS_H), "white")
        self.draw  = ImageDraw.Draw(self.image)
        self.bg_img_id = self.canvas.create_image(0, 0, anchor=tk.NW,
                                                  image=None, tags="bg")
        self._cancel_text()
        self._refresh_display()

    def _undo(self):
        if not self.history:
            messagebox.showinfo("Desfazer", "Nenhuma ação para desfazer.")
            return
        self._cancel_text()
        self.image = self.history.pop()
        self.draw  = ImageDraw.Draw(self.image)
        self.canvas.delete("all")
        self.bg_img_id = self.canvas.create_image(0, 0, anchor=tk.NW,
                                                  image=None, tags="bg")
        self._refresh_display()

    # ══════════════════════════════════════════════════════════════════════════
    # Salvar arquivo
    # ══════════════════════════════════════════════════════════════════════════

    def _save_file(self):
        self._commit_text()
        filetypes = [
            ("PNG Image",    "*.png"),
            ("JPEG Image",   "*.jpg *.jpeg"),
            ("Bitmap",       "*.bmp"),
        ]
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=filetypes,
            title="Salvar imagem como…",
        )
        if not path:
            return
        ext = path.rsplit(".", 1)[-1].lower()
        try:
            if ext in ("jpg", "jpeg"):
                self.image.save(path, "JPEG", quality=95)
            elif ext == "bmp":
                self.image.save(path, "BMP")
            else:
                self.image.save(path, "PNG")
            messagebox.showinfo("Salvo!", f"Imagem salva com sucesso em:\n{path}")
        except Exception as exc:
            messagebox.showerror("Erro ao salvar", str(exc))

    # ══════════════════════════════════════════════════════════════════════════
    # Utilitários
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _hex2rgb(hex_color: str) -> tuple[int, int, int]:
        h = hex_color.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# ──────────────────────────────────────────────────────────────────────────────
# Ponto de entrada
# ──────────────────────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    root.minsize(900, 600)

    # Ícone (ignora se não encontrar)
    try:
        root.iconbitmap("paint_icon.ico")
    except Exception:
        pass

    app = PaintApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
