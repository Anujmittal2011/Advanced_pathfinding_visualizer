import pygame, math, sys
from queue import PriorityQueue, Queue, LifoQueue
from array import array

# ---------- Init ----------
pygame.init()
pygame.font.init()
AUDIO = True
try:
    pygame.mixer.init()
except Exception:
    AUDIO = False

INFO = pygame.display.Info()
SCREEN_W, SCREEN_H = INFO.current_w, INFO.current_h

# default layout
SCALE = 0.92          # proportion of screen taken by square grid area when fullscreen
WINDOW_SCALE = 0.8    # proportion when windowed
DEFAULT_ROWS = 40     # initial grid density (can be changed with slider)
MIN_ROWS, MAX_ROWS = 20, 80

def compute_grid_pixels(fullscreen=False, base_w=SCREEN_W, base_h=SCREEN_H):
    if fullscreen:
        limit = int(min(base_w, base_h) * SCALE)
    else:
        limit = int(min(base_w, base_h) * WINDOW_SCALE)
    # ui_h = max(int(limit * 0.12), 64)
    ui_h = max(int(limit * 0.18), 100)

    return limit, ui_h

# GRID_PIXELS, UI_HEIGHT = compute_grid_pixels(fullscreen=False)
GRID_PIXELS, UI_HEIGHT = compute_grid_pixels(fullscreen=False)
UI_HEIGHT = 140  # Increase toolbar height
GRID_PIXELS = GRID_PIXELS - 60  # Reduce grid height a bit so buttons fit


WIN = pygame.display.set_mode((GRID_PIXELS, GRID_PIXELS + UI_HEIGHT))
pygame.display.set_caption("Advanced Pathfinding Visualizer")

FONT = pygame.font.SysFont("arial", 16)
TITLE_FONT = pygame.font.SysFont("arial", 28, bold=True)
CLOCK = pygame.time.Clock()

# ---------- Colors ----------
WHITE = (255,255,255)
BLACK = (0,0,0)
GREY = (200,200,200)
PURPLE = (138,43,226)
PANEL = (238,230,245)
BORDER = (200,185,220)
START_COLOR = (255,165,0)
END_COLOR = (128,0,128)
BARRIER_COLOR = (0,0,0)
OPEN_COLOR = (0,102,255)
CLOSED_COLOR = (255,0,0)
PATH_COLOR = (255,255,0)

# ---------- Click sound ----------
def make_click_sound():
    if not AUDIO:
        return None
    try:
        sr = 44100
        dur = 40
        n = int(sr * dur / 1000)
        arr = array('h')
        amp = int(32767 * 0.2)
        freq = 800
        for i in range(n):
            t = i / sr
            arr.append(int(amp * math.sin(2*math.pi*freq*t)))
        return pygame.mixer.Sound(buffer=arr)
    except Exception:
        return None

CLICK = make_click_sound()
def click_play():
    if CLICK:
        try:
            CLICK.play()
        except:
            pass

# ---------- Node ----------
class Node:
    def __init__(self, r,c,w,total):
        self.row=r; self.col=c; self.width=w; self.total=total
        self.x = c * w
        self.y = r * w
        self.color = WHITE
        self.neighbors=[]
    def get_pos(self): return (self.row,self.col)
    def is_barrier(self): return self.color==BARRIER_COLOR
    def is_start(self): return self.color==START_COLOR
    def is_end(self): return self.color==END_COLOR
    def reset(self): self.color=WHITE
    def make_start(self): self.color=START_COLOR
    def make_end(self): self.color=END_COLOR
    def make_barrier(self): self.color=BARRIER_COLOR
    def make_open(self): self.color=OPEN_COLOR
    def make_closed(self): self.color=CLOSED_COLOR
    def make_path(self): self.color=PATH_COLOR
    def draw(self, win): pygame.draw.rect(win, self.color, (self.x, self.y, self.width, self.width))
    def update_neighbors(self, grid):
        self.neighbors=[]
        rows=self.total
        r,c = self.row, self.col
        # 4 directions
        if r < rows-1 and not grid[r+1][c].is_barrier(): self.neighbors.append(grid[r+1][c])
        if r > 0 and not grid[r-1][c].is_barrier(): self.neighbors.append(grid[r-1][c])
        if c < rows-1 and not grid[r][c+1].is_barrier(): self.neighbors.append(grid[r][c+1])
        if c > 0 and not grid[r][c-1].is_barrier(): self.neighbors.append(grid[r][c-1])
    def __lt__(self, other): return False

# ---------- Heuristic & path reconstruct ----------
def h(p1,p2):
    (r1,c1),(r2,c2)=p1,p2
    return abs(r1-r2)+abs(c1-c2)

def reconstruct_path(came_from, current, draw):
    while current in came_from:
        current = came_from[current]
        current.make_path()
        draw()

# ---------- Algorithms ----------
def a_star(draw, grid, start, end):
    count=0
    open_set = PriorityQueue()
    open_set.put((0,count,start))
    came_from={}
    g_score={node: float('inf') for row in grid for node in row}
    f_score={node: float('inf') for row in grid for node in row}
    g_score[start]=0
    f_score[start]=h(start.get_pos(), end.get_pos())
    open_hash={start}
    while not open_set.empty():
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit(); sys.exit()
        current=open_set.get()[2]
        open_hash.remove(current)
        if current==end:
            reconstruct_path(came_from, end, draw)
            end.make_end()
            return True
        for neighbor in current.neighbors:
            temp_g=g_score[current]+1
            if temp_g < g_score[neighbor]:
                came_from[neighbor]=current
                g_score[neighbor]=temp_g
                f_score[neighbor]=temp_g + h(neighbor.get_pos(), end.get_pos())
                if neighbor not in open_hash:
                    count+=1
                    open_set.put((f_score[neighbor], count, neighbor))
                    open_hash.add(neighbor)
                    neighbor.make_open()
        draw()
        if current!=start: current.make_closed()
    draw_no_path_message()
    return False

def dijkstra(draw, grid, start, end):
    pq = PriorityQueue()
    pq.put((0,start))
    dist={node: float('inf') for row in grid for node in row}
    dist[start]=0
    came_from={}
    while not pq.empty():
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit(); sys.exit()
        current = pq.get()[1]
        if current==end:
            reconstruct_path(came_from,end,draw)
            end.make_end()
            return True
        for neighbor in current.neighbors:
            temp = dist[current]+1
            if temp < dist[neighbor]:
                came_from[neighbor]=current
                dist[neighbor]=temp
                pq.put((temp,neighbor))
                neighbor.make_open()
        draw()
        if current!=start: current.make_closed()
    draw_no_path_message()
    return False

def bfs(draw, grid, start, end):
    q = Queue()
    q.put(start)
    came_from={}
    visited={start}
    while not q.empty():
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit(); sys.exit()
        current = q.get()
        if current==end:
            reconstruct_path(came_from,end,draw)
            end.make_end()
            return True
        for neighbor in current.neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                came_from[neighbor]=current
                q.put(neighbor)
                neighbor.make_open()
        draw()
        if current!=start: current.make_closed()
    draw_no_path_message()
    return False

def dfs(draw, grid, start, end):
    st = LifoQueue()
    st.put(start)
    came_from={}
    visited={start}
    while not st.empty():
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit(); sys.exit()
        current = st.get()
        if current==end:
            reconstruct_path(came_from,end,draw)
            end.make_end()
            return True
        for neighbor in current.neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                came_from[neighbor]=current
                st.put(neighbor)
                neighbor.make_open()
        draw()
        if current!=start: current.make_closed()
    draw_no_path_message()
    return False

# ---------- Grid + drawing ----------
def make_grid(rows, pixel_size):
    grid=[]
    gap = pixel_size // rows
    for r in range(rows):
        grid.append([ Node(r,c,gap,rows) for c in range(rows) ])
    return grid

def draw_grid(win, grid_pixels, rows):
    gap = grid_pixels // rows
    for i in range(rows):
        pygame.draw.line(WIN, GREY, (0, i*gap), (grid_pixels, i*gap))
        for j in range(rows):
            pygame.draw.line(WIN, GREY, (j*gap,0), (j*gap, grid_pixels))

# ---------- UI Button class ----------
class Button:
    def __init__(self, rect, text, icon=""):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.icon = icon
        self.hover=False
        self.active=False
    def draw(self, surf):
        bg = PURPLE if self.active else PANEL if not self.hover else (170,150,200)
        pygame.draw.rect(surf, bg, self.rect, border_radius=8)
        pygame.draw.rect(surf, BORDER, self.rect, 2, border_radius=8)
        txt = FONT.render(f"{self.icon} {self.text}", True, BLACK if not self.active else WHITE)
        surf.blit(txt, txt.get_rect(center=self.rect.center))
    def check_hover(self,pos): self.hover = self.rect.collidepoint(pos)
    def clicked(self): click_play()

# ---------- UI: build bottom toolbar ----------
def build_toolbar(grid_pixels, ui_h, rows):
    toolbar=[]
    pad = 12; btn_w=110; btn_h=36
    x = pad; y = grid_pixels + (ui_h - btn_h)//2
    defs = [
        ("Start","🎯","start"),
        ("End","🏁","end"),
        ("Barrier","🧱","barrier"),
        ("Erase","🧼","erase"),
        ("A*","⭐","A*"),
        ("Dijkstra","🔷","Dijkstra"),
        ("BFS","🔶","BFS"),
        ("DFS","🔺","DFS"),
        ("Run","▶️","run"),
        ("Clear","🔄","clear"),
        ("Fullscreen","⛶","fullscreen"),
    ]
    for t,icon,action in defs:
        b = Button((x,y,btn_w,btn_h), t, icon)
        toolbar.append((b,action))
        x += btn_w + pad
        if x + btn_w > grid_pixels - pad:
            x = pad
            y += btn_h + 8
    # slider area on right: show label and bar
    slider_rect = pygame.Rect(grid_pixels - 240, grid_pixels + 8, 200, 20)
    return toolbar, slider_rect

# ---------- helper ----------
def get_cell_pos(mouse_pos, grid_pixels, rows):
    x,y = mouse_pos
    if y >= grid_pixels: return None, None
    gap = grid_pixels // rows
    row = y // gap
    col = x // gap
    return row, col

# ---------- main ----------
def main():
    global WIN, GRID_PIXELS, UI_HEIGHT
    rows = DEFAULT_ROWS
    grid_pixels = GRID_PIXELS
    ui_h = UI_HEIGHT
    grid = make_grid(rows, grid_pixels)
    start = None
    end = None
    mode = "barrier"
    algo = "A*"

    toolbar, slider_rect = build_toolbar(grid_pixels, ui_h, rows)

    dragging_slider = False
    run_in_progress = False

    while True:
        mouse = pygame.mouse.get_pos()
        for b,_ in toolbar:
            b.check_hover(mouse)

        # Draw main area
        WIN.fill(WHITE)
        # nodes
        for row in grid:
            for node in row: node.draw(WIN)
        draw_grid(WIN, grid_pixels, rows)
        # Title
        t = TITLE_FONT.render("Pathfinding Visualizer", True, PURPLE)
        WIN.blit(t, (grid_pixels//2 - t.get_width()//2, 8))
        # top-left algorithm label
        label = FONT.render(f"Algorithm: {algo}", True, BLACK)
        WIN.blit(label, (8, 44))
        # legend small
        lx,ly = 8,70
        pygame.draw.rect(WIN, PANEL, (lx-6, ly-6, 150, 170), border_radius=8)
        pygame.draw.rect(WIN, BORDER, (lx-6, ly-6, 150, 170), 2, border_radius=8)
        legend_items = [("Start",START_COLOR),("End",END_COLOR),("Barrier",BARRIER_COLOR),("Open Set",OPEN_COLOR),("Closed Set",CLOSED_COLOR),("Path",PATH_COLOR),("Empty",WHITE)]
        for i,(lab,col) in enumerate(legend_items):
            pygame.draw.rect(WIN, col, (lx, ly + i*24, 16,16))
            pygame.draw.rect(WIN, BLACK, (lx, ly + i*24, 16,16),1)
            WIN.blit(FONT.render(lab, True, BLACK), (lx+22, ly + i*24 -1))

        # bottom toolbar background
        pygame.draw.rect(WIN, PANEL, (0, grid_pixels, grid_pixels, ui_h))
        pygame.draw.rect(WIN, BORDER, (0, grid_pixels, grid_pixels, ui_h), 2)

        # draw toolbar buttons
        for b,act in toolbar:
            b.draw(WIN)

        # draw slider
        pygame.draw.rect(WIN, (230,230,230), slider_rect, border_radius=6)
        pygame.draw.rect(WIN, BORDER, slider_rect, 2, border_radius=6)
        # slider handle position based on rows
        ratio = (rows - MIN_ROWS) / (MAX_ROWS - MIN_ROWS)
        handle_x = int(slider_rect.x + 6 + ratio * (slider_rect.width - 12))
        handle_rect = pygame.Rect(handle_x-6, slider_rect.y-6, 12, slider_rect.height+12)
        pygame.draw.rect(WIN, PURPLE, handle_rect, border_radius=6)
        WIN.blit(FONT.render(f"Grid: {rows} x {rows}", True, BLACK), (slider_rect.x - 110, slider_rect.y -2))

        pygame.display.update()

        # Events
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type==pygame.MOUSEBUTTONDOWN:
                if event.button==1:
                    # check toolbar clicks
                    for b,act in toolbar:
                        if b.rect.collidepoint(event.pos):
                            b.clicked()
                            click_play()
                            # reset active flags for modes & algos
                            if act in ("start","end","barrier","erase"):
                                mode = act
                                for bb,_ in toolbar: bb.active=False
                                b.active = True
                            elif act in ("A*","Dijkstra","BFS","DFS"):
                                algo = act
                                for bb,_ in toolbar: bb.active=False
                                b.active = True
                            elif act == "run":
                                # run algorithm if start and end exist
                                if start and end:
                                    # prepare neighbors
                                    for r in grid:
                                        for node in r: node.update_neighbors(grid)
                                    # call selected algo
                                    if algo=="A*": a_star(lambda: draw_frame(WIN, grid, grid_pixels, rows, toolbar, slider_rect, algo), grid, start, end)
                                    elif algo=="Dijkstra": dijkstra(lambda: draw_frame(WIN, grid, grid_pixels, rows, toolbar, slider_rect, algo), grid, start, end)
                                    elif algo=="BFS": bfs(lambda: draw_frame(WIN, grid, grid_pixels, rows, toolbar, slider_rect, algo), grid, start, end)
                                    elif algo=="DFS": dfs(lambda: draw_frame(WIN, grid, grid_pixels, rows, toolbar, slider_rect, algo), grid, start, end)
                            elif act=="clear":
                                start=None; end=None; grid = make_grid(rows, grid_pixels)
                            elif act=="fullscreen":
                                # toggle fullscreen: rebuild display and grid size
                                # if currently windowed => go fullscreen
                                if WIN.get_flags() & pygame.FULLSCREEN:
                                    GRID, UI = compute_grid_pixels(fullscreen=False)
                                    WIN = pygame.display.set_mode((GRID, GRID + UI))
                                else:
                                    GRID, UI = compute_grid_pixels(fullscreen=True)
                                    WIN = pygame.display.set_mode((GRID, GRID + UI), pygame.FULLSCREEN)
                                # update globals used
                                grid_pixels = GRID
                                ui_h = UI
                                GRID_PIXELS_local = grid_pixels
                                # rebuild grid with same rows but adapt cell sizes
                                grid = make_grid(rows, grid_pixels)
                                # reposition toolbar & slider
                                toolbar, slider_rect = build_toolbar(grid_pixels, ui_h, rows)
                            break
                    else:
                        # not toolbar: handle grid placement
                        r,c = get_cell_pos(event.pos, grid_pixels, rows)
                        if r is not None:
                            node = grid[r][c]
                            if mode=="start":
                                if start: start.reset()
                                start = node; start.make_start()
                            elif mode=="end":
                                if end: end.reset()
                                end=node; end.make_end()
                            elif mode=="barrier":
                                if node!=start and node!=end: node.make_barrier()
                            elif mode=="erase":
                                if node==start: start=None
                                if node==end: end=None
                                node.reset()
                elif event.button==3:
                    # right-click = erase
                    r,c = get_cell_pos(event.pos, grid_pixels, rows)
                    if r is not None:
                        node = grid[r][c]
                        if node==start: start=None
                        if node==end: end=None
                        node.reset()

            if event.type==pygame.MOUSEBUTTONUP:
                dragging_slider = False

            if event.type==pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]:
                    # drawing while dragging
                    mx,my = event.pos
                    r,c = get_cell_pos((mx,my), grid_pixels, rows)
                    if r is not None:
                        node = grid[r][c]
                        if mode=="barrier":
                            if node!=start and node!=end: node.make_barrier()
                        elif mode=="erase":
                            if node==start: start=None
                            if node==end: end=None
                            node.reset()
                # slider drag start if clicking handle area
                if event.buttons[0]:
                    if slider_rect.collidepoint(event.pos):
                        dragging_slider = True
                if dragging_slider:
                    # compute new rows from mouse x inside slider_rect
                    mx = event.pos[0]
                    rel = max(0, min(1, (mx - slider_rect.x) / slider_rect.width))
                    new_rows = int(MIN_ROWS + rel * (MAX_ROWS - MIN_ROWS))
                    if new_rows != rows:
                        rows = new_rows
                        grid = make_grid(rows, grid_pixels)
                        start=None; end=None
                        # rebuild toolbar positions to fit new width
                        toolbar, slider_rect = build_toolbar(grid_pixels, ui_h, rows)

            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    if WIN.get_flags() & pygame.FULLSCREEN:
                        # exit fullscreen
                        GRID, UI = compute_grid_pixels(fullscreen=False)
                        WIN = pygame.display.set_mode((GRID, GRID + UI))
                        grid_pixels = GRID; ui_h = UI
                        grid = make_grid(rows, grid_pixels)
                        toolbar, slider_rect = build_toolbar(grid_pixels, ui_h, rows)
                    else:
                        pygame.quit(); sys.exit()
                if event.key==pygame.K_F11:
                    # toggle fullscreen same as button
                    if WIN.get_flags() & pygame.FULLSCREEN:
                        GRID, UI = compute_grid_pixels(fullscreen=False)
                        WIN = pygame.display.set_mode((GRID, GRID + UI))
                    else:
                        GRID, UI = compute_grid_pixels(fullscreen=True)
                        WIN = pygame.display.set_mode((GRID, GRID + UI), pygame.FULLSCREEN)
                    grid_pixels = GRID; ui_h = UI
                    grid = make_grid(rows, grid_pixels)
                    toolbar, slider_rect = build_toolbar(grid_pixels, ui_h, rows)

                # keyboard alternatives kept
                if event.key==pygame.K_1:
                    algo="A*"
                    for b,act in toolbar:
                        b.active = (act=="A*")
                if event.key==pygame.K_2:
                    algo="Dijkstra"
                    for b,act in toolbar:
                        b.active = (act=="Dijkstra")
                if event.key==pygame.K_3:
                    algo="BFS"
                    for b,act in toolbar:
                        b.active = (act=="BFS")
                if event.key==pygame.K_4:
                    algo="DFS"
                    for b,act in toolbar:
                        b.active = (act=="DFS")
                if event.key==pygame.K_SPACE:
                    if start and end:
                        for r in grid:
                            for n in r: n.update_neighbors(grid)
                        if algo=="A*": a_star(lambda: draw_frame(WIN, grid, grid_pixels, rows, toolbar, slider_rect, algo), grid, start, end)
                        elif algo=="Dijkstra": dijkstra(lambda: draw_frame(WIN, grid, grid_pixels, rows, toolbar, slider_rect, algo), grid, start, end)
                        elif algo=="BFS": bfs(lambda: draw_frame(WIN, grid, grid_pixels, rows, toolbar, slider_rect, algo), grid, start, end)
                        elif algo=="DFS": dfs(lambda: draw_frame(WIN, grid, grid_pixels, rows, toolbar, slider_rect, algo), grid, start, end)

        CLOCK.tick(60)

# small helper used by algos to redraw while running
def draw_frame(win, grid, grid_pixels, rows, toolbar, slider_rect, algo_name):
    # draw nodes and UI minimal to keep animation visible
    win.fill(WHITE)
    for row in grid:
        for node in row: node.draw(win)
    draw_grid(win, grid_pixels, rows)
    t = TITLE_FONT.render("Pathfinding Visualizer", True, PURPLE)
    win.blit(t, (grid_pixels//2 - t.get_width()//2, 8))
    lbl = FONT.render(f"Algorithm: {algo_name}", True, BLACK)
    win.blit(lbl, (8,44))
    # draw bottom panel (simple)
    pygame.draw.rect(win, PANEL, (0, grid_pixels, grid_pixels, slider_rect.height + 48))
    for b,_ in toolbar: b.draw(win)
    pygame.display.update()
    CLOCK.tick(120)

def draw_no_path_message():
    text = TITLE_FONT.render("No Path Found!", True, (255, 50, 50))
    sub = FONT.render("Try clearing some barriers and run again.", True, (80, 0, 0))
    WIN.blit(text, (GRID_PIXELS // 2 - text.get_width() // 2, GRID_PIXELS // 2 - 20))
    WIN.blit(sub, (GRID_PIXELS // 2 - sub.get_width() // 2, GRID_PIXELS // 2 + 20))
    pygame.display.update()
    if AUDIO:
        try:
            freq = 400
            dur = 300
            sr = 44100
            n = int(sr * dur / 1000)
            arr = array('h')
            amp = int(32767 * 0.3)
            for i in range(n):
                t = i / sr
                arr.append(int(amp * math.sin(2 * math.pi * freq * t)))
            snd = pygame.mixer.Sound(buffer=arr)
            snd.play()
        except:
            pass
    pygame.time.delay(2000)  # pause 2 seconds to let the user see it


if __name__ == "__main__":
    main()
