"""
This displays RISK game logs so that the games can be viewed
It was modified from the RISK.pyw program included in this assignment 
which was written by John Bauman
"""

from PIL import Image
from PIL import ImageDraw
from PIL import ImageTk
import tkinter as tk
import xml.dom.minidom
import random
import io
import zipfile
import gc
import sys

import risktools

territories = {}

canvas = None
root = None
totim = None
zfile = None
statbrd = None
restart_button = None 

previous_player_names = {} 

# --- DEFINICIÓN DE COLORES INICIALES ---
INITIAL_POSSIBLE_COLORS = [
    (59, 89, 152),   # Azul apagado
    (192, 57, 43),   # Rojo granada
    (39, 174, 96),   # Verde esmeralda mate
    (142, 68, 173),  # Violeta wisteria
    (211, 84, 0),    # Naranja calabaza
    (22, 160, 133),  # Verde azulado
    (160, 64, 0),    # Marrón óxido
    (183, 149, 11),  # Amarillo Mostaza
    (41, 128, 185),  # Azul Belize
    (108, 52, 131),  # Ciruela
    (118, 20, 52),   # Rojo Vino
    (30, 132, 73),   # Verde Selva
    (44, 62, 80),    # Azul Medianoche
    (186, 74, 0),    # Siena tostado
    (31, 97, 141),   # Azul oscuro estático
    (23, 32, 42),    # Negro azulado
    (125, 60, 152),  # Orquídea oscuro
    (214, 137, 16),  # Naranja ocre
    (8, 100, 105),   # Cian oscuro profundo
]

possiblecolors = list(INITIAL_POSSIBLE_COLORS)

class Territory:
    """Contains the graphics info for a territory"""
    def __init__(self, name, x, y, w, h, cx, cy):
        self.name = str(name)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.cx = cx
        self.cy = cy

class PlayerStats:
    """This is used to display the stats for a single player"""
    def __init__(self, master, **kwargs):
        self.pframe = tk.Frame(master, **kwargs)
        self.pack = self.pframe.pack
        
        self.statlabel = tk.Label(self.pframe, width=40, anchor=tk.W)
        self.statlabel.pack(fill=tk.X)
        
        self.statlabel3 = tk.Label(self.pframe, width=40, anchor=tk.W) 
        self.statlabel3.pack(fill=tk.X)
        
    def set_id(self, id):
        self.id = id
        
    def update_stats(self, player, state):
        """Update the player stats"""
        num_armies = 0
        num_territories = 0
        for i in range(len(state.owners)):
            if state.owners[i] == player.id:
                num_territories += 1
                num_armies += state.armies[i]
             
        self.statlabel.configure(text=f"{player.name}: {num_armies} in {num_territories} territories. {player.free_armies} free", fg=playercolors[player.id], bg=backcolors[player.id])
        
        happiness = getattr(player, 'happiness', 'N/A')
        economy = getattr(player, 'economy', 'N/A')
        development = getattr(player, 'development', 'N/A')
        
        stats_text = f"Happiness: {happiness} | Econ: {economy} | Dev: {development}"
        
        self.statlabel3.configure(text=stats_text, fg=playercolors[player.id], bg=backcolors[player.id])
            
        self.pack()
            
class PlayerList:
    """Actually lists the players."""
    def __init__(self, master, **kwargs):
        """Actually initialize it."""
        self.listframe = tk.Frame(master, **kwargs)
        self.pack = self.listframe.pack
        self.pstats = []
        
    def append(self, player):
        """Append a player to this list."""
        newpstat = PlayerStats(self.listframe)
        newpstat.pack()
        newpstat.set_id(player.id)
        self.pstats.append(newpstat)
        self.pack(fill=tk.X)
        
    def updateList(self, state):
        for p in state.players:
            for ps in self.pstats:
                if p.id == ps.id:
                    ps.update_stats(p, state)
    
    def clear(self):
        for ps in self.pstats:
            ps.pframe.destroy()
        self.pstats = []
class StatBoard:
    def __init__(self, players_master, actions_master):
        """Initialize it."""
        
        self.pstats_frame = tk.LabelFrame(players_master, text=" Player Stats", padx=5, pady=5)
        self.pstats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.pstats = PlayerList(self.pstats_frame)
        self.pstats.pack(fill=tk.X)
        
        self.turn_frame = tk.LabelFrame(actions_master, text=" Turn & Action Info", padx=5, pady=5)
        self.turn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.curturnnum = tk.Label(self.turn_frame, text="Turn Number: ", width=35, anchor=tk.W, font=('Arial', 10, 'bold'))
        self.curturnnum.pack(fill=tk.X)
        
        self.sep1 = tk.Frame(self.turn_frame, height=1, bg="black") 
        self.sep1.pack(fill=tk.X, pady=2)
        
        self.curplayer = tk.Label(self.turn_frame, text="Current Player:", width=35, anchor=tk.W, fg="green", font=('Arial', 10, 'bold'))
        self.curplayer.pack(fill=tk.X)
        
        self.turntype = tk.Label(self.turn_frame, text="Turn Type:", width=35, anchor=tk.W)
        self.turntype.pack(fill=tk.X)
        
        self.sep2 = tk.Frame(self.turn_frame, height=1, bg="black") 
        self.sep2.pack(fill=tk.X, pady=2)
        
        self.lastplayer = tk.Label(self.turn_frame, text="Last Player:", width=35, anchor=tk.W, fg="darkorange")
        self.lastplayer.pack(fill=tk.X)

        # Aumentamos un poco el wraplength por seguridad
        self.action = tk.Label(self.turn_frame, text="Last Action:", width=35, anchor=tk.W, justify=tk.LEFT, wraplength=250) 
        self.action.pack(fill=tk.X)
        
    def add_player(self, player):
        self.pstats.append(player)
        
    def update_statBoard(self, state, last_action, last_player):
        self.pstats.updateList(state)
        
        current_player_name = state.players[state.current_player].name
        
        self.curturnnum.configure(text=f"Turn # {turn_number} | State # {state_number}")
        
        cur_player_id = state.current_player 
        self.curplayer.configure(text=f"Current Player: {current_player_name}", 
                                fg=playercolors[cur_player_id], 
                                bg=backcolors[cur_player_id]) 

        self.turntype.configure(text=f"Turn Type: {state.turn_type}")
        
        if last_player is not None: 
            last_player_name = state.players[last_player].name
            last_player_id = last_player
            self.lastplayer.configure(text=f"Last Player: {last_player_name}",
                                     fg=playercolors[last_player_id], 
                                     bg=backcolors[last_player_id])
        else:
            self.lastplayer.configure(text="Last Player: N/A", fg="darkorange", bg=self.turn_frame["bg"])
            
        # Construimos el string manualmente para forzar que aparezcan los campos 
        # aunque estén vacíos.
        
        act_type = last_action.type if last_action.type else "Start/None"
        
        # Si existe valor lo ponemos, si no, dejamos cadena vacía
        val_from = last_action.from_territory if last_action.from_territory else ""
        val_to = last_action.to_territory if last_action.to_territory else ""
        
        # Verificamos si existe el atributo armies (o num) y si tiene valor
        val_num = ""
        if hasattr(last_action, 'armies') and last_action.armies is not None:
             val_num = str(last_action.armies)
        
        # Creamos el texto con saltos de línea forzados
        fixed_text = (
            f"Last Action: {act_type}\n"
            f"FROM: {val_from}\n"
            f"TO: {val_to}\n"
            f"NUM: {val_num}"
        )
        
        self.action.configure(text=fixed_text)
        
    def log_over(self):
        self.curplayer.configure(text="GAME OVER / LOG FINISHED", fg="red", bg="white")
        self.action.configure(text="End of log file reached.")

    def reset(self):
        self.pstats.clear()
        self.curturnnum.configure(text="Turn Number: 0")
        self.curplayer.configure(text="Current Player:", fg="black", bg=self.turn_frame["bg"])
        self.lastplayer.configure(text="Last Player:", fg="black", bg=self.turn_frame["bg"])
        # Reseteamos también con el formato fijo vacío
        self.action.configure(text="Last Action:\nFROM:\nTO:\nNUM:")

def opengraphic(fname):
    """Load an image from the specified zipfile."""
    stif = io.BytesIO(zfile.read(fname))
    im = Image.open(stif)
    im.load()
    stif.close()
    return im


def drawarmy(t, from_territory=0):
    """Draw a territory's army"""
    terr = territories[riskboard.territories[t].name]
    canvas.delete(terr.name + "-a")
    
    if current_state.owners[t] is not None:
        canvas.create_rectangle(terr.cx + terr.x - 7, terr.cy + terr.y - 7, 
                                terr.cx + terr.x + 7, terr.cy + terr.y+ 7, 
                                fill=backcolors[current_state.owners[t]], 
                                tags=(terr.name + "-a",))
        canvas.create_text(terr.cx + terr.x, terr.cy + terr.y, 
                           text=str(current_state.armies[t]), tags=(riskboard.territories[t].name + "-a",), fill=playercolors[current_state.owners[t]])
    
    else:
        canvas.create_text(terr.cx + terr.x, terr.cy + terr.y, 
                           text=str(current_state.armies[t]), tags=(terr.name + "-a",))
        

def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    ti = int(lv/3)
    return (int(value[0:ti],16), int(value[ti:2*ti],16), int(value[2*ti:lv],16), 255) 
                           

def drawterritory(t, color=None):
    """Draw an entire territory (will draw in color provided, default is owning player's color)"""
    terr = territories[str(riskboard.territories[t].name)]
    
    canvas.delete(terr.name) 
    
    final_color = None
    
    if current_state.owners[t] is not None:
        if color:
            final_color = color
        else:
            base_color = hex_to_rgb(backcolors[current_state.owners[t]])
            
            MAX_FACTOR = 0.5

            if current_state.mes >= 7 and current_state.mes <= 12:
                mes_norm = current_state.mes - 7 
                factor_raw = mes_norm / 5.0
                factor = factor_raw * MAX_FACTOR
                
            elif current_state.mes >= 1 and current_state.mes <= 6:
                mes_inv = 6 - current_state.mes
                factor_raw = mes_inv / 5.0 
                factor = factor_raw * MAX_FACTOR
                
            else:
                factor = 0.0

            final_color = blend_with_white(base_color, factor)

    elif current_state.owners[t] is None and current_state.fase!="fase_0":
        final_color = (200,200,200, 255)
        
    if final_color:
        for fp in terr.floodpoints:
            ImageDraw.floodfill(terr.photo, fp, final_color)
            
    terr.currentimage = ImageTk.PhotoImage(terr.photo)
    canvas.create_image(terr.x, terr.y, anchor=tk.NW, 
                            image=terr.currentimage, tags=(terr.name,))  
    drawarmy(t, 1)

def makeplayercolors(player):
    """Make the colors for a player"""
    colo = possiblecolors[0]
    possiblecolors.remove(colo)
    col = colo[0] * 2**16 + colo[1] * 2**8 + colo[2]
    
    back = 2**24-1
    pc = hex(col)[2:]
    pc = "0" * (6 - len(pc)) + pc
    backcolors.append("#" + pc)

    pc = hex(back)[2:]
    pc = "0" * (6 - len(pc)) + pc
    playercolors.append("#" + pc)

def change_player_color(player_id):
    """Asigna un nuevo color libre al jugador y recicla el antiguo."""
    global possiblecolors, backcolors
    
    if not possiblecolors:
        print("Warning: No more colors available to switch!")
        return

    old_hex = backcolors[player_id].lstrip('#')
    r = int(old_hex[0:2], 16)
    g = int(old_hex[2:4], 16)
    b = int(old_hex[4:6], 16)
    recycled_color = (r, g, b)
    
    new_color_tuple = possiblecolors[0]
    possiblecolors.remove(new_color_tuple)
    
    col_int = new_color_tuple[0] * 2**16 + new_color_tuple[1] * 2**8 + new_color_tuple[2]
    pc = hex(col_int)[2:]
    pc = "0" * (6 - len(pc)) + pc
    new_hex_str = "#" + pc
    
    print(f"Changing color for Player {player_id}: {backcolors[player_id]} -> {new_hex_str}")
    backcolors[player_id] = new_hex_str
    
    possiblecolors.append(recycled_color)

    
playercolors = []
backcolors = []
    
def newplayer(p):
    """Create a new player"""
    makeplayercolors(p)
    statbrd.add_player(p)
    previous_player_names[p.id] = p.name
    
                              
def loadterritorygraphics(xmlFile):
    """Load graphics information/graphics from a file"""
    global territories
    territories = {}
    territoryStructure = xmlFile.getElementsByTagName("territory")
    for i in territoryStructure:
        tname = i.getAttribute("name")
        grafile = i.getElementsByTagName("file")[0].childNodes[0].data
        attributes = i.getElementsByTagName("attributes")[0]
        x = int(attributes.getAttribute("x"))
        y = int(attributes.getAttribute("y"))
        w = int(attributes.getAttribute("w"))
        h = int(attributes.getAttribute("h"))
        cx = int(attributes.getAttribute("cx"))
        cy = int(attributes.getAttribute("cy"))
        floodpoints = i.getElementsByTagName("floodpoint")
        fps = []
        for fp in floodpoints:
            fpx = int(fp.getAttribute("x"))
            fpy = int(fp.getAttribute("y"))
            fps.append((fpx,fpy))
        
        shaded = opengraphic(grafile)
        
        t = Territory(tname, x, y, w, h, cx, cy)
        t.photo = shaded
        t.shadedimage = ImageTk.PhotoImage(shaded)
        t.currentimage = ImageTk.PhotoImage(t.photo.point(lambda x:1.2*x))
        territories[tname] = t
        t.floodpoints = fps
        del shaded

playing = False
        
def toggle_playing():
    global playing, play_button
    if playing:
        playing = False
        play_button.config(text="Play")
    else:
        playing = True
        play_button.config(text="Pause")
      
play_button = None

def blend_with_white(rgb_color, factor):
    """Mezcla un color RGB con blanco"""
    r, g, b, a = rgb_color 
    new_r = int(r + (255 - r) * factor)
    new_g = int(g + (255 - g) * factor)
    new_b = int(b + (255 - b) * factor)
    return (new_r, new_g, new_b, a) 

def play_log():
    global current_state
    if playing:
        nextstate()
    delay = 50
    if current_state.turn_type == 'Place':
        num_free = current_state.players[current_state.current_player].free_armies 
        if num_free > 3:
            delay = 50
        elif num_free > 1:
            delay = 250
        
    root.after(delay, play_log)

# --- LÓGICA DE REINICIO ---
def restart_game():
    global playing, logover, turn_number, state_number, possiblecolors, backcolors, playercolors, previous_player_names, current_state
    
    playing = False
    play_button.config(text="Play", state=tk.NORMAL)
    
    logover = False
    turn_number = 0
    state_number = 0
    previous_player_names = {}

    possiblecolors = list(INITIAL_POSSIBLE_COLORS)
    backcolors = []
    playercolors = []

    # Rebobinar log
    logfile.seek(0)
    logfile.readline() 

    # Resetear estado
    current_state = risktools.getInitialState(riskboard)

    # 💡 CORRECCIÓN IMPORTANTE: Recargar gráficos limpios del mapa
    # Si no hacemos esto, las imágenes en memoria siguen pintadas del juego anterior
    print("Reloading clean map graphics...")
    graphics_xml = zfile.read("territory_graphics.xml")
    graphics = xml.dom.minidom.parseString(graphics_xml)
    loadterritorygraphics(graphics)

    # Resetear GUI
    statbrd.reset() 
    restart_button.pack_forget()

    nextstate(False)

def setupdata():
    """Start the game"""
    global territories, canvas, root, gameMenu, playerMenu
    global totim, zfile, statbrd, play_button, restart_button
    
    root = tk.Tk()
    root.title("PyRiskGameViewer")
    
    zfile = zipfile.ZipFile("world.zip")
    graphics = xml.dom.minidom.parseString(zfile.read("territory_graphics.xml"))
    loadterritorygraphics(graphics)   
    
    map_width = int(graphics.childNodes[0].getAttribute("width"))
    map_height = int(graphics.childNodes[0].getAttribute("height"))
    
    LEFT_PANEL_WIDTH = 260
    RIGHT_PANEL_WIDTH = 300 
    
    total_width = LEFT_PANEL_WIDTH + map_width + RIGHT_PANEL_WIDTH
    
    root.geometry(f"{total_width}x{map_height + 5}")
    root.resizable(False, False) 
    
    totalframe = tk.Frame(root)
    
    # 1. Panel Izquierdo
    left_panel = tk.Frame(totalframe, width=LEFT_PANEL_WIDTH, height=map_height)
    left_panel.pack_propagate(False) 
    left_panel.pack(side=tk.LEFT, fill=tk.Y)
    
    # 2. Panel Derecho
    right_panel = tk.Frame(totalframe, width=RIGHT_PANEL_WIDTH, height=map_height)
    right_panel.pack_propagate(False)
    right_panel.pack(side=tk.RIGHT, fill=tk.Y)
    
    # 3. Mapa
    canvas = tk.Canvas(totalframe, 
                            height=map_height, 
                            width=map_width, 
                            bg="#AEC6CF")
    canvas.pack(side=tk.LEFT, expand=tk.YES, fill=tk.BOTH)

    statbrd = StatBoard(players_master=right_panel, actions_master=left_panel)
    
    tk.Button(left_panel, text="Next State", width=20,
                   command = nextstate).pack(padx=15,pady=20)
    
    global play_button
    play_button = tk.Button(left_panel, text="Play", command = toggle_playing, width=20)
    play_button.pack(padx=15,pady=5)
    
    # --- BOTÓN REINICIAR ---
    restart_button = tk.Button(left_panel, text="↺ RESTART LOG", command=restart_game, width=20, bg="#ffdddd", fg="red")
    
    totalframe.pack(expand=tk.YES, fill=tk.BOTH)
    
    gc.collect()
    play_log()
    
logfile = None
current_state = None
riskboard = None
turn_number = 0
state_number = 0

HIGHLIGHT_COLOR = (255, 255, 0, 255) 

def display_current_state(last_action):
    global previous_player, previous_player_names
    
    if len(backcolors) == 0 or len(backcolors)!=len(current_state.players):
        for p in current_state.players:
            newplayer(p)

    # --- DETECTAR CAMBIO DE NOMBRE Y CAMBIAR COLOR ---
    for p in current_state.players:
        if p.id not in previous_player_names:
            previous_player_names[p.id] = p.name
        elif previous_player_names[p.id] != p.name:
            print(f"DETECTED NAME CHANGE: ID {p.id} went from '{previous_player_names[p.id]}' to '{p.name}'")
            previous_player_names[p.id] = p.name
            change_player_color(p.id)
    # -------------------------------------------------

    statbrd.update_statBoard(current_state, last_action, previous_player)

    territories_to_highlight = []
    
    if last_action.type == 'Attack': 
        from_name = last_action.from_territory
        to_name = last_action.to_territory
        
        if from_name is not None and to_name is not None:
            try:
                tidx_from = riskboard.territory_to_id[from_name]
                tidx_to = riskboard.territory_to_id[to_name]
                territories_to_highlight.append(tidx_from)
                territories_to_highlight.append(tidx_to)
            except KeyError:
                pass

    for tidx in range(len(riskboard.territories)):
        if tidx in territories_to_highlight:
            drawterritory(tidx, color=HIGHLIGHT_COLOR)
        else:
            drawterritory(tidx)
    
def nextstate(read_action=True):
    global current_state, logover, previous_action, previous_player, playing, turn_number, state_number

    if logover:
        print('LOG IS OVER NOW!')
        statbrd.log_over()
        playing = False
        
        restart_button.pack(padx=15, pady=20)
        return
        
    last_action = risktools.RiskAction(None,None,None,None)
    if logfile is not None:
        if read_action:
            newline = logfile.readline()
            splitline = newline.split('|')
            if not newline or splitline[0] == 'RISKRESULT':
                print('We have reached the end of the logfile')
                print(newline)
                logover = True
            else:
                last_action.from_string(newline) 
        if not logover:
            current_state.from_string(logfile.readline(),riskboard)
    if not logover:
        display_current_state(last_action)
    previous_action = last_action
    if current_state.current_player != previous_player:
        turn_number += 1
    state_number += 1
    previous_player = current_state.current_player

    if not logover and current_state.turn_type == 'GameOver':
        logover = True
        if logfile is not None:
            newline = logfile.readline()
            print('GAME OVER:  RESULT:')
            print(newline)
        
previous_action = None        
logover = False
previous_player = None
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Requires logfile!')
        sys.exit()

    logfile = open(sys.argv[1]) 
    l1 = logfile.readline() 
    riskboard = risktools.loadBoard('world.zip')
    current_state = risktools.getInitialState(riskboard)
    setupdata()
    nextstate(False)
    root.mainloop()