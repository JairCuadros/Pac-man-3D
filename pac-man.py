import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import sys  
import os
from pygame import mixer  # Sistema multicanal de alta fidelidad para mezclar música y efectos
from PIL import Image

# Inicialización de GLUT para el renderizado de fuentes Bitmap fijas
if not any(arg.startswith('--') for arg in sys.argv):
    glutInit(sys.argv)

# ==============================================================================
# 1. ARQUITECTURA DEL MAPA GIGANTE (DISEÑO ADAPTADO CON CASA DE FANTASMAS CENTRAL)
# ==============================================================================
MAPA = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], # 0
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], # 1
    [1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1], # 2
    [1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1], # 3
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], # 4
    # Fila 5: Las columnas 11, 12, 14 y 15 son muros de la casa. La columna 13 es '0' (La Puerta)
    [1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1], # 5
    # Fila 6: Columnas 12, 13 y 14 son el espacio interior hueco de la casa de fantasmas
    [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1], # 6
    # Fila 7: Columnas de la 11 a la 15 son '1' completando la pared trasera de la casa
    [1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1], # 7
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1], # 8
    [1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1], # 9
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], # 10
    [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1], # 11
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]  # 12
]

ALTO_MAPA = len(MAPA)
ANCHO_MAPA = len(MAPA[0])

# ==============================================================================
# 2. DEFINICIÓN DE LA MÁQUINA DE ESTADOS DEL JUEGO
# ==============================================================================
ESTADO_MENU = 0
ESTADO_JUEGO = 1
ESTADO_RECORDS = 2
ESTADO_GAME_OVER = 3
ESTADO_VICTORIA = 4
ESTADO_PAUSA = 5
ESTADO_MUERTE = 6 
ESTADO_INTRO = 7  

estado_actual = ESTADO_MENU
record_guardado = False

# Variables de control de audio musical y efectos
musica_actual = None
musica_juego_etapa = 1
musica_anterior_pausa = None
fx_comer = None
fx_muerte = None
fx_retorno = None
fx_pausa = None
fx_victoria = None

volumen_actual = 0.5
juego_muteado = False

total_puntos = 0

# ==============================================================================
# VARIABLES DE ESTADO GLOBAL (DENTRO DEL JUEGO)
# ==============================================================================
pacman_x = 1.5
pacman_z = 1.5
pacman_angulo_rotacion = 90.0  
pacman_vidas = 3
puntaje = 0
boca_angulo = 0.0
boca_abriendo = True
fantasmas = []
puntos = []
puntajes_fantasma = []

capsulas_poder = []
fantasmas_asustados = False
tiempo_fantasmas_asustados = 0.0
DURACION_PODER = 7.0 

en_pausa_fantasma = False
tiempo_pausa_fantasma = 0.0
DURACION_PAUSA_FANTASMA = 0.5  

tiempo_inicio_muerte = 0.0
duracion_anim_muerte = 1.8 
tiempo_inicio_intro = 0.0  
tiempo_inicio_juego = 0.0  

pacman_invulnerable = False
pacman_tiempo_invulnerable = 0.0
DURACION_INMUNIDAD = 3.0 

ventana_ancho = 1000  
ventana_alto = 700

# Dimensiones del HUD de puntuación (para plantilla y reutilización)
CUADRO_PUNTOS_ANCHO = 280
CUADRO_PUNTOS_ALTO = 70
CUADRO_PUNTOS_MARGEN = 20

# Datos de plantilla de records
PLANTILLA_PUNTUACION_ANCHO = 900
PLANTILLA_PUNTUACION_ALTO = 502
PLANTILLA_PUNTUACION_ORIG_ANCHO = 2752
PLANTILLA_PUNTUACION_ORIG_ALTO = 1536
PLANTILLA_PUNTUACION_NUMERO_X = 1997
PLANTILLA_PUNTUACION_PRIMERA_Y = 590
PLANTILLA_PUNTUACION_DY = 64

# IDs de Texturas
id_textura_muro = 0 
id_textura_piso = 0 
id_textura_arbol = 0 
id_textura_piso_exterior = 0 
id_textura_corazon = 0 
id_textura_menu = 0
id_textura_boton = 0
id_textura_boton_jugar = 0
id_textura_boton_menu_principal = 0
id_textura_boton_puntuacion = 0
id_textura_boton_reanudar = 0
id_textura_boton_salir = 0
id_textura_boton_salir_del_juego = 0
id_textura_boton_volver_a_jugar = 0
id_textura_titulo_menu = 0   
id_textura_game_over = 0    
id_textura_pausa = 0        
id_textura_cuadro_puntuacion = 0
id_textura_titulo_victoria = 0
id_textura_preparate = 0
id_textura_preparate_ancho = 0
id_textura_preparate_alto = 0

# IDs de las Listas de Visualización de OpenGL
lista_muros_id = 0
lista_bosque_id = 0
lista_moneda_id = 0 
lista_capsula_id = 0 

bosque_posiciones = []
records_lista = []

# Botones del menú principal
boton_jugar_rect    = [ventana_ancho/2 - 150, ventana_alto - 390, 300, 70]
boton_records_rect  = [ventana_ancho/2 - 150, ventana_alto - 480, 300, 70]
boton_salir_rect    = [ventana_ancho/2 - 150, ventana_alto - 570, 300, 70]

# Botones del menú de pausa
boton_reanudar_rect      = [ventana_ancho/2 - 150, ventana_alto/2 + 20,  300, 70]
boton_menu_pausa_rect    = [ventana_ancho/2 - 150, ventana_alto/2 - 70,  300, 70]
boton_salir_pausa_rect   = [ventana_ancho/2 - 150, ventana_alto/2 - 160, 300, 70]

# Botones de game over
boton_reiniciar_go_rect  = [ventana_ancho/2 - 150, ventana_alto/2 + 10, 300, 70]
boton_menu_go_rect       = [ventana_ancho/2 - 150, ventana_alto/2 - 80, 300, 70]
boton_salir_go_rect      = [ventana_ancho/2 - 150, ventana_alto/2 - 170, 300, 70]

esc_presionado_antes = False

# ==============================================================================
# ESCUCHAS DE INTERACCIÓN (GLFW CALLBACKS)
# ==============================================================================
def redimensionar_ventana_callback(window, width, height):
    global ventana_ancho, ventana_alto
    global boton_jugar_rect, boton_records_rect, boton_salir_rect
    global boton_reanudar_rect, boton_menu_pausa_rect, boton_salir_pausa_rect
    global boton_reiniciar_go_rect, boton_menu_go_rect, boton_salir_go_rect, boton_mute_rect, barra_volumen_rect
    if height == 0: height = 1
    ventana_ancho = width
    ventana_alto = height

    boton_jugar_rect    = [ventana_ancho/2 - 150, ventana_alto - 390, 300, 70]
    boton_records_rect  = [ventana_ancho/2 - 150, ventana_alto - 480, 300, 70]
    boton_salir_rect    = [ventana_ancho/2 - 150, ventana_alto - 570, 300, 70]

    boton_reanudar_rect    = [ventana_ancho/2 - 150, ventana_alto/2 + 20,  300, 70]
    boton_menu_pausa_rect  = [ventana_ancho/2 - 150, ventana_alto/2 - 70,  300, 70]
    boton_salir_pausa_rect = [ventana_ancho/2 - 150, ventana_alto/2 - 160, 300, 70]

    boton_reiniciar_go_rect = [ventana_ancho/2 - 150, ventana_alto/2 + 10, 300, 70]
    boton_menu_go_rect      = [ventana_ancho/2 - 150, ventana_alto/2 - 80, 300, 70]
    boton_salir_go_rect     = [ventana_ancho/2 - 150, ventana_alto/2 - 170, 300, 70]

    glViewport(0, 0, width, height)

def mouse_click_callback(window, button, action, mods):
    global estado_actual, records_lista, record_guardado, juego_muteado, volumen_actual, tiempo_inicio_intro

    if action == glfw.PRESS and button == glfw.MOUSE_BUTTON_LEFT:
        x, y = glfw.get_cursor_pos(window)
        y = ventana_alto - y

        if estado_actual == ESTADO_MENU:
            if punto_en_rectangulo(x, y, boton_jugar_rect):
                inicializar_juego()
                estado_actual = ESTADO_INTRO
                tiempo_inicio_intro = glfw.get_time()
            elif punto_en_rectangulo(x, y, boton_records_rect):
                records_lista = cargar_records(); estado_actual = ESTADO_RECORDS
            elif punto_en_rectangulo(x, y, boton_salir_rect):
                glfw.set_window_should_close(window, True)

        elif estado_actual == ESTADO_RECORDS:
            estado_actual = ESTADO_MENU

        elif estado_actual == ESTADO_PAUSA:
            if punto_en_rectangulo(x, y, boton_reanudar_rect):
                estado_actual = ESTADO_JUEGO
                reproducir_sonido_pausa()
            elif punto_en_rectangulo(x, y, boton_menu_pausa_rect): estado_actual = ESTADO_MENU
            elif punto_en_rectangulo(x, y, boton_salir_pausa_rect): glfw.set_window_should_close(window, True)

# CORREGIDO: Forzar el paso por la animación de introducción y sincronizar relojes
        elif estado_actual == ESTADO_GAME_OVER:
            if punto_en_rectangulo(x, y, boton_reiniciar_go_rect):
                inicializar_juego()
                estado_actual = ESTADO_INTRO
                tiempo_inicio_intro = glfw.get_time()
            elif punto_en_rectangulo(x, y, boton_menu_go_rect): estado_actual = ESTADO_MENU
            elif punto_en_rectangulo(x, y, boton_salir_go_rect): glfw.set_window_should_close(window, True)
        elif estado_actual == ESTADO_VICTORIA:
            if punto_en_rectangulo(x, y, boton_reiniciar_go_rect):
                inicializar_juego()
                estado_actual = ESTADO_INTRO
                tiempo_inicio_intro = glfw.get_time()
            elif punto_en_rectangulo(x, y, boton_menu_go_rect):
                estado_actual = ESTADO_MENU
            elif punto_en_rectangulo(x, y, boton_salir_go_rect):
                glfw.set_window_should_close(window, True)

def punto_en_rectangulo(px, py, rect):
    """ Función auxiliar de colisión de ratón (punto contra rectángulo) """
    return rect[0] <= px <= rect[0] + rect[2] and rect[1] <= py <= rect[1] + rect[3]

def actualizar_volumen_maestro():
    vol = 0.0 if juego_muteado else volumen_actual
    mixer.music.set_volume(vol)
    if fx_comer: fx_comer.set_volume(vol)
    if fx_muerte: fx_muerte.set_volume(vol)
    if fx_retorno: fx_retorno.set_volume(vol)
    if fx_pausa: fx_pausa.set_volume(vol)


def reproducir_sonido_pausa():
    if juego_muteado or fx_pausa is None:
        return
    try:
        fx_pausa.play()
    except Exception:
        pass


def reproducir_musica_juego_etapa(etapa):
    global musica_actual, musica_juego_etapa
    if musica_actual == "juego" and musica_juego_etapa == etapa:
        return
    mixer.music.stop()
    try:
        if etapa == 1:
            mixer.music.load("sonido_juego.wav")
        elif etapa == 2:
            mixer.music.load("sonido_juego_2.wav")
        else:
            mixer.music.load("sonido_juego_3.wav")
        mixer.music.play(-1)
        musica_actual = "juego"
        musica_juego_etapa = etapa
    except Exception as e:
        print(f"Warning: no se pudo reproducir música de juego etapa {etapa}: {e}")


def reproducir_musica_fantasma_asustado():
    global musica_actual
    if musica_actual == "fantasma_asustado":
        return
    mixer.music.stop()
    try:
        mixer.music.load("sonido_fantasma_asustado.wav")
        mixer.music.play(-1)
        musica_actual = "fantasma_asustado"
    except Exception as e:
        print(f"Warning: no se pudo reproducir música de fantasma asustado: {e}")


def restablecer_musica_juego_por_progreso():
    if total_puntos <= 0:
        reproducir_musica_juego_etapa(1)
        return
    progreso = 1.0 - float(len(puntos)) / float(total_puntos)
    if progreso >= 0.80:
        reproducir_musica_juego_etapa(3)
    elif progreso >= 0.50:
        reproducir_musica_juego_etapa(2)
    else:
        reproducir_musica_juego_etapa(1)

# ==============================================================================
# SISTEMA DE CARGA DE RECURSOS Y TEXTURAS
# ==============================================================================
def cargar_textura_imagen(ruta_archivo):
    if not os.path.exists(ruta_archivo):
        print(f"Warning: El archivo de textura '{ruta_archivo}' no existe. Usando placeholder.")
        return 0
    try:
        img = Image.open(ruta_archivo)
        img = img.transpose(Image.FLIP_TOP_BOTTOM) 
        img_data = img.convert("RGBA").tobytes()
        ancho, alto = img.size
    except Exception as e:
        print(f"Error crítico al cargar la imagen de textura '{ruta_archivo}': {e}")
        sys.exit()

    textura_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, textura_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ancho, alto, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
    return textura_id

def generar_datos_bosque():
    global bosque_posiciones
    bosque_posiciones = []
    while len(bosque_posiciones) < 75:
        x = random.uniform(-7.0, float(ANCHO_MAPA) + 7.0)
        z = random.uniform(-6.0, float(ALTO_MAPA) + 6.0)
        if not (-2.2 <= x <= float(ANCHO_MAPA) + 2.2 and -2.2 <= z <= float(ALTO_MAPA) + 2.2):
            escala = random.uniform(1.2, 1.8) 
            bosque_posiciones.append([x, z, escala])

def compilar_geometria_estatica():
    global lista_muros_id, lista_bosque_id, lista_moneda_id, lista_capsula_id
    lista_bosque_id = glGenLists(1)
    glNewList(lista_bosque_id, GL_COMPILE)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, id_textura_arbol)
    glColor3f(1.0, 1.0, 1.0)
    for x, z, esc in bosque_posiciones:
        glPushMatrix(); glTranslatef(x, 0.01, z); glScalef(esc, esc, esc); glRotatef(15.0, 0.0, 1.0, 0.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex3f(-1.0, 0.0, 0.0); glTexCoord2f(1.0, 0.0); glVertex3f(1.0, 0.0, 0.0)
        glTexCoord2f(1.0, 1.0); glVertex3f(1.0, 2.0, 0.0); glTexCoord2f(0.0, 1.0); glVertex3f(-1.0, 2.0, 0.0)
        glEnd(); glPopMatrix()
    glDisable(GL_TEXTURE_2D); glEndList()
    
    lista_muros_id = glGenLists(1)
    glNewList(lista_muros_id, GL_COMPILE)
    for f in range(ALTO_MAPA):
        for c in range(ANCHO_MAPA):
            if MAPA[f][c] == 1:
                glPushMatrix(); glTranslatef(c, 0, f); draw_concrete_wall_textured(1.0, 0.75, 1.0); glPopMatrix()
    glEndList()
    
    lista_moneda_id = glGenLists(1)
    glNewList(lista_moneda_id, GL_COMPILE)
    glColor3f(1.0, 0.75, 0.0); draw_perfect_sphere(0.065, 6, 6) 
    glEndList()

    lista_capsula_id = glGenLists(1)
    glNewList(lista_capsula_id, GL_COMPILE)
    glColor3f(1.0, 0.2, 0.8) 
    draw_perfect_sphere(0.18, 12, 12) 
    glEndList()

# ==============================================================================
# 3. SISTEMA DE RÉCORDS (PERSISTENCIA DE ARCHIVOS)
# ==============================================================================
def guardar_puntaje(p):
    try:
        with open("records.txt", "a") as f: f.write(f"{p}\n")
    except Exception as e: print(f"Error guardando records: {e}")

def cargar_records():
    puntos_records = []
    if not os.path.exists("records.txt"): return []
    try:
        with open("records.txt", "r") as f:
            for line in f:
                try: puntos_records.append(int(line.strip()))
                except: pass
    except Exception as e: print(f"Error cargando records: {e}")
    puntos_records.sort(reverse=True)
    return puntos_records[:5]

def inicializar_juego():
    global pacman_x, pacman_z, pacman_angulo_rotacion, pacman_vidas, puntaje, puntos, fantasmas, pacman_invulnerable, pacman_tiempo_invulnerable, record_guardado, capsulas_poder, fantasmas_asustados, total_puntos, musica_juego_etapa, musica_anterior_pausa, puntajes_fantasma
    pacman_x, pacman_z, pacman_angulo_rotacion, pacman_vidas, puntaje = 1.5, 1.5, 90.0, 3, 0
    pacman_invulnerable, pacman_tiempo_invulnerable = False, 0.0
    record_guardado = False 
    fantasmas_asustados = False
    musica_anterior_pausa = None
    
    capsulas_poder = [
        [1.5, 3.5],   
        [25.5, 3.5],  
        [9.5, 1.5],   
        [25.5, 10.5]  
    ]
    
    puntos = []
    puntajes_fantasma = []
    for f in range(ALTO_MAPA):
        for c in range(ANCHO_MAPA):
            if MAPA[f][c] == 0 and (f != 1 or c != 1):
                es_posicion_capsula = any(abs(c+0.5 - cap[0]) < 0.1 and abs(f+0.5 - cap[1]) < 0.1 for cap in capsulas_poder)
                es_dentro_casa = (5 <= f <= 7 and 11 <= c <= 15)
                if not es_posicion_capsula and not es_dentro_casa:
                    puntos.append([c + 0.5, f + 0.5])

    total_puntos = len(puntos)
    musica_juego_etapa = 1
    
    # Estructura del Fantasma: [X, Z, DirX, DirZ, ColorRGB, CasaX, CasaZ, Es_Ojos_Regresando, Tiempo_Salida]
    fantasmas = [
        [13.5, 6.5, 0.0, -0.04, (0.9, 0.2, 0.2), 13.5, 6.5, False, 0.0],   # Blinky (Rojo)
        [13.5, 6.5, 0.0, -0.04, (1.0, 0.4, 0.6), 13.5, 6.5, False, 5.0],   # Pinky (Rosado)
        [13.5, 6.5, 0.0, -0.04, (0.2, 0.7, 0.9), 13.5, 6.5, False, 10.0],  # Inky (Cian)
        [13.5, 6.5, 0.0, -0.04, (0.9, 0.5, 0.1), 13.5, 6.5, False, 15.0]   # Clyde (Naranja)
    ]

# ==============================================================================
# 4. RENDERIZADO GEOMETRÍA 3D Y DETECCIÓN DE COLISIONES
# ==============================================================================
def draw_jungle_background():
    glCallList(lista_bosque_id)

def draw_floor_textured():
    glColor3f(1.0, 1.0, 1.0); glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, id_textura_piso)
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0); glVertex3f(0.0, -0.01, 0.0); glTexCoord2f(float(ANCHO_MAPA), 0.0); glVertex3f(float(ANCHO_MAPA), -0.01, 0.0)
    glTexCoord2f(float(ANCHO_MAPA), float(ALTO_MAPA)); glVertex3f(float(ANCHO_MAPA), -0.01, float(ALTO_MAPA)); glTexCoord2f(0.0, float(ALTO_MAPA)); glVertex3f(0.0, -0.01, float(ALTO_MAPA))
    glEnd()
    glBindTexture(GL_TEXTURE_2D, id_textura_piso_exterior)
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0); glVertex3f(-80.0, -0.02, -80.0); glTexCoord2f(35.0, 0.0); glVertex3f(110.0, -0.02, -80.0)
    glTexCoord2f(35.0, 35.0); glVertex3f(110.0, -0.02, 90.0); glTexCoord2f(0.0, 35.0); glVertex3f(-80.0, -0.02, 90.0)
    glEnd(); glDisable(GL_TEXTURE_2D)

def draw_concrete_wall_textured(size_x, size_y, size_z):
    glColor3f(1.0, 1.0, 1.0); glEnable(GL_TEXTURE_2D); glBindTexture(GL_TEXTURE_2D, id_textura_muro)
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0); glVertex3f(0, 0, size_z); glTexCoord2f(1.0, 0.0); glVertex3f(size_x, 0, size_z); glTexCoord2f(1.0, 1.0); glVertex3f(size_x, size_y, size_z); glTexCoord2f(0.0, 1.0); glVertex3f(0, size_y, size_z)
    glTexCoord2f(1.0, 0.0); glVertex3f(0, 0, 0); glTexCoord2f(1.0, 1.0); glVertex3f(0, size_y, 0); glTexCoord2f(0.0, 1.0); glVertex3f(size_x, size_y, 0); glTexCoord2f(0.0, 0.0); glVertex3f(size_x, 0, 0)
    glTexCoord2f(0.0, 0.0); glVertex3f(0, 0, 0); glTexCoord2f(1.0, 0.0); glVertex3f(0, 0, size_z); glTexCoord2f(1.0, 1.0); glVertex3f(0, size_y, size_z); glTexCoord2f(0.0, 1.0); glVertex3f(0, size_y, 0)
    glTexCoord2f(1.0, 0.0); glVertex3f(size_x, 0, 0); glTexCoord2f(1.0, 1.0); glVertex3f(size_x, size_y, 0); glTexCoord2f(0.0, 1.0); glVertex3f(size_x, size_y, size_z); glTexCoord2f(0.0, 0.0); glVertex3f(size_x, 0, size_z)
    glTexCoord2f(0.0, 1.0); glVertex3f(0, size_y, 0); glTexCoord2f(0.0, 0.0); glVertex3f(0, size_y, size_z); glTexCoord2f(1.0, 0.0); glVertex3f(size_x, size_y, size_z); glTexCoord2f(1.0, 1.0); glVertex3f(size_x, size_y, 0)
    glEnd(); glDisable(GL_TEXTURE_2D) 

def draw_perfect_sphere(radius, lats, longs):
    for i in range(lats + 1):
        get_lat0 = math.pi * (-0.5 + float(i - 1) / lats); y0 = math.sin(get_lat0) * radius; r0 = math.cos(get_lat0) * radius
        get_lat1 = math.pi * (-0.5 + float(i) / lats); y1 = math.sin(get_lat1) * radius; r1 = math.cos(get_lat1) * radius
        glBegin(GL_QUAD_STRIP)
        for j in range(longs + 1):
            lng = 2.0 * math.pi * float(j - 1) / longs
            glVertex3f(math.cos(lng) * r0, y0, math.sin(lng) * r0); glVertex3f(math.cos(lng) * r1, y1, math.sin(lng) * r1)
        glEnd()

def draw_pacman_final(radius, angle_apertura):
    lats, longs = 32, 32 
    glColor3f(1.0, 0.82, 0.0)
    for i in range(lats + 1):
        get_lat0 = math.pi * (-0.5 + float(i - 1) / lats); y0 = math.sin(get_lat0) * radius; r0 = math.cos(get_lat0) * radius
        get_lat1 = math.pi * (-0.5 + float(i) / lats); y1 = math.sin(get_lat1) * radius; r1 = math.cos(get_lat1) * radius
        glBegin(GL_QUAD_STRIP)
        for j in range(longs + 1):
            lng = 2.0 * math.pi * float(j) / longs
            es_frente_horizontal = (lng < math.pi / 4.0 or lng > (2.0 * math.pi - math.pi / 4.0))
            es_boca_vertical = es_frente_horizontal and (get_lat0 > -angle_apertura and get_lat0 < angle_apertura)
            if not es_boca_vertical:
                glVertex3f(math.sin(lng) * r0, y0, math.cos(lng) * r0); glVertex3f(math.sin(lng) * r1, y1, math.cos(lng) * r1)
        glEnd()
    glColor3f(0.0, 0.0, 0.0); lng_izq, lng_der = math.pi / 4.0, 2.0 * math.pi - math.pi / 4.0
    y_sup, r_sup = math.sin(angle_apertura) * radius, math.cos(angle_apertura) * radius
    y_inf, r_inf = math.sin(-angle_apertura) * radius, math.cos(-angle_apertura) * radius
    glBegin(GL_TRIANGLES)
    glVertex3f(0.0, 0.0, 0.0); glVertex3f(math.sin(lng_izq) * r_sup, y_sup, math.cos(lng_izq) * r_sup); glVertex3f(math.sin(lng_izq) * r_inf, y_inf, math.cos(lng_izq) * r_inf)
    glVertex3f(0.0, 0.0, 0.0); glVertex3f(math.sin(lng_der) * r_inf, y_inf, math.cos(lng_der) * r_inf); glVertex3f(math.sin(lng_der) * r_sup, y_sup, math.cos(lng_der) * r_sup)
    glEnd()
    glBegin(GL_QUADS)
    glVertex3f(0.0, 0.0, 0.0); glVertex3f(math.sin(lng_izq) * r_sup, y_sup, math.cos(lng_izq) * r_sup); glVertex3f(0.0, y_sup, radius); glVertex3f(math.sin(lng_der) * r_sup, y_sup, math.cos(lng_der) * r_sup)
    glVertex3f(0.0, 0.0, 0.0); glVertex3f(math.sin(lng_der) * r_inf, y_inf, math.cos(lng_der) * r_inf); glVertex3f(0.0, y_inf, radius); glVertex3f(math.sin(lng_izq) * r_inf, y_inf, math.cos(lng_izq) * r_inf)
    glEnd()
    glColor3f(0.01, 0.01, 0.01) 
    for lado in [-1, 1]:
        glPushMatrix(); glTranslatef(0.16 * lado, 0.23, 0.08); draw_perfect_sphere(0.032, 8, 8); glPopMatrix()

def draw_ghost(r, g, b, solo_ojos=False):
    if not solo_ojos:
        glColor3f(r, g, b)
        glPushMatrix(); glTranslatef(0.0, 0.1, 0.0); draw_perfect_sphere(0.26, 16, 16); glPopMatrix()
        glBegin(GL_QUAD_STRIP)
        for j in range(14):
            lng = 2.0 * math.pi * float(j) / 13.0; x, z = math.cos(lng) * 0.26, math.sin(lng) * 0.26
            glVertex3f(x, 0.1, z); glVertex3f(x, -0.18 + (0.03 * math.cos(lng * 6.0)), z)
        glEnd()
        
    for lado in [-1, 1]:
        glColor3f(1.0, 1.0, 1.0); glPushMatrix(); glTranslatef(0.09 * lado, 0.12, 0.20); draw_perfect_sphere(0.05, 8, 8)
        glColor3f(0.0, 0.1, 0.7); glTranslatef(0.0, 0.0, 0.015); draw_perfect_sphere(0.024, 6, 6); glPopMatrix()

# AGREGADO: Restauradas de forma estricta las funciones lógicas de detección de colisión y re-direccionamiento
def verificar_colision(nx, nz):
    radio_colision = 0.32
    for dx in [-radio_colision, radio_colision]:
        for dz in [-radio_colision, radio_colision]:
            cx, cz = int(nx + dx), int(nz + dz)
            if 0 <= cx < ANCHO_MAPA and 0 <= cz < ALTO_MAPA and MAPA[cz][cx] == 1: return True
    return False

def obtener_direcciones_libres(fx, fz):
    pasillos_libres = []
    v = 0.04
    direcciones_prueba = [(0.0, -v), (0.0, v), (-v, 0.0), (v, 0.0)]
    random.shuffle(direcciones_prueba)
    for dx, dz in direcciones_prueba:
        if not verificar_colision(fx + dx * 4, fz + dz * 4): pasillos_libres.append((dx, dz))
    return pasillos_libres


def obtener_siguiente_direccion_retorno(fx, fz, vel_actual):
    from collections import deque
    start = (int(fx), int(fz))
    objetivo = (13, 6)
    if start == objetivo:
        return 0.0, 0.0

    cola = deque([start])
    anterior = {start: None}
    while cola:
        x, z = cola.popleft()
        for dx, dz in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, nz = x + dx, z + dz
            if 0 <= nx < ANCHO_MAPA and 0 <= nz < ALTO_MAPA and MAPA[nz][nx] == 0 and (nx, nz) not in anterior:
                anterior[(nx, nz)] = (x, z)
                if (nx, nz) == objetivo:
                    cola.clear()
                    break
                cola.append((nx, nz))

    if objetivo not in anterior:
        return 0.0, 0.0

    paso = objetivo
    while anterior[paso] != start:
        paso = anterior[paso]
        if paso is None:
            return 0.0, 0.0

    dir_x = paso[0] - start[0]
    dir_z = paso[1] - start[1]
    return math.copysign(vel_actual, dir_x) if dir_x != 0 else 0.0, math.copysign(vel_actual, dir_z) if dir_z != 0 else 0.0

# ==============================================================================
# 5. RENDERIZADO INTERFAZ 2D (HUD, MENÚS Y RÉCORDS)
# ==============================================================================
def render_bitmap_string(x, y, font, text_string):
    glWindowPos2i(int(x), int(y))
    for char in text_string:
        glutBitmapCharacter(font, ord(char))


def proyectar_a_pantalla(x, y, z):
    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)
    viewport = glGetIntegerv(GL_VIEWPORT)
    win = gluProject(x, y, z, modelview, projection, viewport)
    if win is None:
        return 0.0, 0.0, 0.0
    return win[0], win[1], win[2]


def agregar_popup_puntaje_fantasma(x, z, texto):
    puntajes_fantasma.append({
        'x': x,
        'z': z,
        'texto': texto,
        'inicio': glfw.get_time(),
        'duracion': 1.2,
        'offset_x': random.uniform(-0.35, 0.35),
        'offset_y': random.uniform(0.15, 0.35)
    })


def dibujar_popups_puntaje_fantasma():
    if not puntajes_fantasma:
        return
    current_time = glfw.get_time()
    for popup in puntajes_fantasma[:]:
        elapsed = current_time - popup['inicio']
        if elapsed > popup['duracion']:
            puntajes_fantasma.remove(popup)
            continue
        progress = elapsed / popup['duracion']
        alpha = max(0.0, 1.0 - progress)
        world_y = 0.60 + popup['offset_y'] + progress * 0.25
        screen_x, screen_y, _ = proyectar_a_pantalla(popup['x'] + popup['offset_x'], world_y, popup['z'])
        if 0 <= screen_x <= ventana_ancho and 0 <= screen_y <= ventana_alto:
            shadow_y = screen_y - 2
            glColor4f(0.0, 0.0, 0.0, alpha)
            render_bitmap_string(screen_x - 14, shadow_y - 1, GLUT_BITMAP_TIMES_ROMAN_24, popup['texto'])
            glColor4f(1.0, 1.0, 0.2, alpha)
            render_bitmap_string(screen_x - 15, screen_y, GLUT_BITMAP_TIMES_ROMAN_24, popup['texto'])


def setup_ortho():
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, ventana_ancho, 0, ventana_alto)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity(); glDisable(GL_DEPTH_TEST)

def restore_perspective():
    glEnable(GL_DEPTH_TEST); glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)


def hay_texturas_pendientes():
    comprobadas = ['id_textura_menu','id_textura_boton','id_textura_titulo_menu','id_textura_corazon','id_textura_game_over','id_textura_pausa']
    for k in comprobadas:
        if k in globals() and globals()[k] == 0:
            return True
    return False

def draw_styled_button(rect, texture_id, text, r, g, b):
    if texture_id and texture_id != 0:
        glEnable(GL_TEXTURE_2D); glBindTexture(GL_TEXTURE_2D, texture_id); glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex2f(rect[0], rect[1])
        glTexCoord2f(1.0, 0.0); glVertex2f(rect[0] + rect[2], rect[1])
        glTexCoord2f(1.0, 1.0); glVertex2f(rect[0] + rect[2], rect[1] + rect[3])
        glTexCoord2f(0.0, 1.0); glVertex2f(rect[0], rect[1] + rect[3])
        glEnd(); glDisable(GL_TEXTURE_2D)
    else:
        glDisable(GL_TEXTURE_2D)
        glColor3f(0.05, 0.4, 0.9)
        glBegin(GL_QUADS)
        glVertex2f(rect[0], rect[1]); glVertex2f(rect[0] + rect[2], rect[1]); glVertex2f(rect[0] + rect[2], rect[1] + rect[3]); glVertex2f(rect[0], rect[1] + rect[3])
        glEnd()
        glColor4f(0.0, 0.0, 0.0, 0.25)
        glBegin(GL_QUADS)
        glVertex2f(rect[0] + 4, rect[1] + 4); glVertex2f(rect[0] + rect[2] - 4, rect[1] + 4)
        glVertex2f(rect[0] + rect[2] - 4, rect[1] + rect[3] - 4); glVertex2f(rect[0] + 4, rect[1] + rect[3] - 4)
        glEnd()

    glLineWidth(4.0); glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(rect[0], rect[1]); glVertex2f(rect[0] + rect[2], rect[1])
    glVertex2f(rect[0] + rect[2], rect[1] + rect[3]); glVertex2f(rect[0], rect[1] + rect[3])
    glEnd()

    glColor3f(r, g, b)
    ancho_texto_aprox = len(text) * 10
    tx = rect[0] + (rect[2] / 2) - (ancho_texto_aprox / 2)
    ty = rect[1] + (rect[3] / 2) - 7
    render_bitmap_string(tx, ty, GLUT_BITMAP_HELVETICA_18, text)


def draw_button_texture(rect, texture_id):
    if texture_id and texture_id != 0:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex2f(rect[0], rect[1])
        glTexCoord2f(1.0, 0.0); glVertex2f(rect[0] + rect[2], rect[1])
        glTexCoord2f(1.0, 1.0); glVertex2f(rect[0] + rect[2], rect[1] + rect[3])
        glTexCoord2f(0.0, 1.0); glVertex2f(rect[0], rect[1] + rect[3])
        glEnd(); glDisable(GL_TEXTURE_2D)
    else:
        draw_styled_button(rect, 0, "", 1.0, 1.0, 1.0)


def dibujar_minimapa():
    minimapa_w = 220
    minimapa_h = 120
    margen = 18
    x0 = margen
    y0 = margen
    cell_w = minimapa_w / ANCHO_MAPA
    cell_h = minimapa_h / ALTO_MAPA

    glColor4f(0.0, 0.0, 0.0, 0.60)
    glBegin(GL_QUADS)
    glVertex2f(x0, y0)
    glVertex2f(x0 + minimapa_w, y0)
    glVertex2f(x0 + minimapa_w, y0 + minimapa_h)
    glVertex2f(x0, y0 + minimapa_h)
    glEnd()

    glLineWidth(2.0); glColor3f(0.0, 0.85, 1.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x0, y0)
    glVertex2f(x0 + minimapa_w, y0)
    glVertex2f(x0 + minimapa_w, y0 + minimapa_h)
    glVertex2f(x0, y0 + minimapa_h)
    glEnd()

    for f in range(ALTO_MAPA):
        for c in range(ANCHO_MAPA):
            if MAPA[f][c] == 1:
                glColor3f(0.15, 0.15, 0.15)
                px = x0 + c * cell_w
                py = y0 + minimapa_h - (f + 1) * cell_h
                glBegin(GL_QUADS)
                glVertex2f(px, py)
                glVertex2f(px + cell_w, py)
                glVertex2f(px + cell_w, py + cell_h)
                glVertex2f(px, py + cell_h)
                glEnd()

    glColor3f(1.0, 0.4, 0.8)
    capsula_radio = min(cell_w, cell_h) * 0.14
    for cap in capsulas_poder:
        cap_x = x0 + cap[0] * cell_w
        cap_y = y0 + minimapa_h - cap[1] * cell_h
        glBegin(GL_QUADS)
        glVertex2f(cap_x - capsula_radio, cap_y - capsula_radio)
        glVertex2f(cap_x + capsula_radio, cap_y - capsula_radio)
        glVertex2f(cap_x + capsula_radio, cap_y + capsula_radio)
        glVertex2f(cap_x - capsula_radio, cap_y + capsula_radio)
        glEnd()

    glColor3f(1.0, 1.0, 0.0)
    punto_radio = min(cell_w, cell_h) * 0.10
    for p in puntos:
        dot_x = x0 + p[0] * cell_w
        dot_y = y0 + minimapa_h - p[1] * cell_h
        glBegin(GL_QUADS)
        glVertex2f(dot_x - punto_radio, dot_y - punto_radio)
        glVertex2f(dot_x + punto_radio, dot_y - punto_radio)
        glVertex2f(dot_x + punto_radio, dot_y + punto_radio)
        glVertex2f(dot_x - punto_radio, dot_y + punto_radio)
        glEnd()

    glColor3f(1.0, 1.0, 0.0)
    pac_x = x0 + pacman_x * cell_w
    pac_y = y0 + minimapa_h - pacman_z * cell_h
    glBegin(GL_TRIANGLES)
    glVertex2f(pac_x, pac_y + punto_radio * 1.6)
    glVertex2f(pac_x - punto_radio * 1.2, pac_y - punto_radio * 1.0)
    glVertex2f(pac_x + punto_radio * 1.2, pac_y - punto_radio * 1.0)
    glEnd()

    for f in fantasmas:
        ghost_color = (0.0, 0.0, 0.0) if (f[7] and estado_actual == ESTADO_JUEGO) else ((0.1, 0.2, 0.9) if fantasmas_asustados else f[4])
        glColor3f(ghost_color[0], ghost_color[1], ghost_color[2])
        ghost_x = x0 + f[0] * cell_w
        ghost_y = y0 + minimapa_h - f[1] * cell_h
        ghost_size = punto_radio * 1.5
        glBegin(GL_QUADS)
        glVertex2f(ghost_x - ghost_size, ghost_y - ghost_size)
        glVertex2f(ghost_x + ghost_size, ghost_y - ghost_size)
        glVertex2f(ghost_x + ghost_size, ghost_y + ghost_size)
        glVertex2f(ghost_x - ghost_size, ghost_y + ghost_size)
        glEnd()

def renderizar_menu_principal():
    setup_ortho()
    # Background (textured if available, fallback solid if not)
    if 'id_textura_menu' in globals() and id_textura_menu and id_textura_menu != 0:
        glEnable(GL_TEXTURE_2D); glBindTexture(GL_TEXTURE_2D, id_textura_menu); glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex2f(0, 0); glTexCoord2f(1.0, 0.0); glVertex2f(ventana_ancho, 0)
        glTexCoord2f(1.0, 1.0); glVertex2f(ventana_ancho, ventana_alto); glTexCoord2f(0.0, 1.0); glVertex2f(0, ventana_alto)
        glEnd(); glDisable(GL_TEXTURE_2D)
    else:
        glColor3f(0.03, 0.03, 0.04); glBegin(GL_QUADS)
        glVertex2f(0, 0); glVertex2f(ventana_ancho, 0); glVertex2f(ventana_ancho, ventana_alto); glVertex2f(0, ventana_alto)
        glEnd()

    titulo_w = 600; titulo_h = 200
    titulo_x = ventana_ancho / 2 - titulo_w / 2
    titulo_y = ventana_alto - 80 - titulo_h
    if 'id_textura_titulo_menu' in globals() and id_textura_titulo_menu and id_textura_titulo_menu != 0:
        glEnable(GL_TEXTURE_2D); glBindTexture(GL_TEXTURE_2D, id_textura_titulo_menu); glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex2f(titulo_x, titulo_y)
        glTexCoord2f(1.0, 0.0); glVertex2f(titulo_x + titulo_w, titulo_y)
        glTexCoord2f(1.0, 1.0); glVertex2f(titulo_x + titulo_w, titulo_y + titulo_h)
        glTexCoord2f(0.0, 1.0); glVertex2f(titulo_x, titulo_y + titulo_h)
        glEnd(); glDisable(GL_TEXTURE_2D)
    else:
        glColor3f(1.0, 1.0, 0.0)
        render_bitmap_string(ventana_ancho/2 - 220, titulo_y + titulo_h/2 - 24, GLUT_BITMAP_TIMES_ROMAN_24, "PAC-MAN (MENU)")

    draw_button_texture(boton_jugar_rect, id_textura_boton_jugar)
    draw_button_texture(boton_records_rect, id_textura_boton_puntuacion)
    draw_button_texture(boton_salir_rect, id_textura_boton_salir)

    if hay_texturas_pendientes():
        glColor3f(1.0, 0.9, 0.0)
        render_bitmap_string(ventana_ancho/2 - 120, 40, GLUT_BITMAP_HELVETICA_18, "Recargando recursos...")

    restore_perspective()

def renderizar_pantalla_records():
    setup_ortho()
    glColor3f(0.05, 0.1, 0.05); glBegin(GL_QUADS); glVertex2f(0, 0); glVertex2f(ventana_ancho, 0); glVertex2f(ventana_ancho, ventana_alto); glVertex2f(0, ventana_alto); glEnd()
    glLineWidth(4.0); glColor3f(0.0, 0.85, 1.0); glBegin(GL_LINE_LOOP); glVertex2f(50, 50); glVertex2f(ventana_ancho - 50, 50); glVertex2f(ventana_ancho - 50, ventana_alto - 50); glVertex2f(50, ventana_alto - 50); glEnd()

    if 'id_textura_plantilla_puntuacion' in globals() and id_textura_plantilla_puntuacion and id_textura_plantilla_puntuacion != 0:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, id_textura_plantilla_puntuacion)
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex2f(0, 0)
        glTexCoord2f(1.0, 0.0); glVertex2f(ventana_ancho, 0)
        glTexCoord2f(1.0, 1.0); glVertex2f(ventana_ancho, ventana_alto)
        glTexCoord2f(0.0, 1.0); glVertex2f(0, ventana_alto)
        glEnd(); glDisable(GL_TEXTURE_2D)

        glColor3f(1.0, 1.0, 1.0)
        if not records_lista:
            mensaje_x = ventana_ancho / 2 - 220
            mensaje_y = ventana_alto / 2 - 10
            render_bitmap_string(mensaje_x, mensaje_y, GLUT_BITMAP_TIMES_ROMAN_24, "Aun no hay puntajes registrados.")
        else:
            escala_x = ventana_ancho / float(PLANTILLA_PUNTUACION_ORIG_ANCHO)
            escala_y = ventana_alto / float(PLANTILLA_PUNTUACION_ORIG_ALTO)
            x_num = PLANTILLA_PUNTUACION_NUMERO_X * escala_x
            for i, puntaje_rec in enumerate(records_lista[:5]):
                y_num = ventana_alto - (PLANTILLA_PUNTUACION_PRIMERA_Y + i * PLANTILLA_PUNTUACION_DY) * escala_y
                texto_score = f"{puntaje_rec:05d}"
                ancho_texto = len(texto_score) * 10
                render_bitmap_string(x_num - ancho_texto, y_num, GLUT_BITMAP_TIMES_ROMAN_24, texto_score)
    else:
        glColor3f(0.05, 0.1, 0.05); glBegin(GL_QUADS); glVertex2f(0, 0); glVertex2f(ventana_ancho, 0); glVertex2f(ventana_ancho, ventana_alto); glVertex2f(0, ventana_alto); glEnd()
        glLineWidth(4.0); glColor3f(0.0, 0.85, 1.0); glBegin(GL_LINE_LOOP); glVertex2f(50, 50); glVertex2f(ventana_ancho - 50, 50); glVertex2f(ventana_ancho - 50, ventana_alto - 50); glVertex2f(50, ventana_alto - 50); glEnd()
        glColor3f(1.0, 1.0, 0.0)
        render_bitmap_string(ventana_ancho/2 - 120, ventana_alto - 120, GLUT_BITMAP_TIMES_ROMAN_24, "MEJORES PUNTUACIONES")

        glColor3f(1.0, 1.0, 1.0)
        if not records_lista:
            render_bitmap_string(ventana_ancho/2 - 150, ventana_alto - 250, GLUT_BITMAP_TIMES_ROMAN_24, "Aun no hay puntajes registrados.")
        else:
            for i, puntaje_rec in enumerate(records_lista):
                render_bitmap_string(ventana_ancho/2 - 160, ventana_alto - 220 - (i * 60), GLUT_BITMAP_TIMES_ROMAN_24, f"TOP {i+1}:    {puntaje_rec:05d} puntos")

    glColor3f(0.6, 0.6, 0.6)
    render_bitmap_string(ventana_ancho/2 - 190, 100, GLUT_BITMAP_9_BY_15, "CLIC EN CUALQUIER LUGAR O PRESIONA ESC PARA VOLVER AL MENU")
    restore_perspective()

def renderizar_hud_interfaz():
    setup_ortho()
    
    if estado_actual in (ESTADO_JUEGO, ESTADO_MUERTE, ESTADO_INTRO):
        if 'id_textura_corazon' in globals() and id_textura_corazon and id_textura_corazon != 0:
            glEnable(GL_TEXTURE_2D); glBindTexture(GL_TEXTURE_2D, id_textura_corazon); glColor3f(1.0, 1.0, 1.0)
            for i in range(pacman_vidas):
                glPushMatrix(); glTranslatef(30 + (45 * i), ventana_alto - 50, 0); glBegin(GL_QUADS)
                glTexCoord2f(0.0, 0.0); glVertex2f(0, 0); glTexCoord2f(1.0, 0.0); glVertex2f(32, 0)
                glTexCoord2f(1.0, 1.0); glVertex2f(32, 32); glTexCoord2f(0.0, 1.0); glVertex2f(0, 32)
                glEnd(); glPopMatrix()
            glDisable(GL_TEXTURE_2D)
        else:
            glColor3f(1.0, 0.6, 0.0)
            for i in range(pacman_vidas):
                x = 30 + (45 * i)
                y = ventana_alto - 50
                glBegin(GL_TRIANGLES)
                glVertex2f(x + 16, y + 24)
                glVertex2f(x + 4, y + 6)
                glVertex2f(x + 28, y + 6)
                glEnd()
        
        # Caja Score - usando textura de cuadro_puntuacion en la esquina superior derecha
        cuadro_w = CUADRO_PUNTOS_ANCHO
        cuadro_h = CUADRO_PUNTOS_ALTO
        cuadro_x = ventana_ancho - cuadro_w - CUADRO_PUNTOS_MARGEN
        cuadro_y = ventana_alto - cuadro_h - CUADRO_PUNTOS_MARGEN
        if 'id_textura_cuadro_puntuacion' in globals() and id_textura_cuadro_puntuacion and id_textura_cuadro_puntuacion != 0:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, id_textura_cuadro_puntuacion)
            glColor3f(1.0, 1.0, 1.0)
            glBegin(GL_QUADS)
            glTexCoord2f(0.0, 0.0); glVertex2f(cuadro_x, cuadro_y)
            glTexCoord2f(1.0, 0.0); glVertex2f(cuadro_x + cuadro_w, cuadro_y)
            glTexCoord2f(1.0, 1.0); glVertex2f(cuadro_x + cuadro_w, cuadro_y + cuadro_h)
            glTexCoord2f(0.0, 1.0); glVertex2f(cuadro_x, cuadro_y + cuadro_h)
            glEnd(); glDisable(GL_TEXTURE_2D)
        else:
            glColor4f(0.0, 0.0, 0.0, 0.75); glBegin(GL_QUADS); glVertex2f(cuadro_x, cuadro_y); glVertex2f(cuadro_x + cuadro_w, cuadro_y); glVertex2f(cuadro_x + cuadro_w, cuadro_y + cuadro_h); glVertex2f(cuadro_x, cuadro_y + cuadro_h); glEnd()

        texto_label = "PUNTOS :"
        texto_score = f"{puntaje:05d}"
        label_width = len(texto_label) * 10
        score_width = len(texto_score) * 12
        espacio_texto = 18
        total_width = label_width + espacio_texto + score_width
        base_x = cuadro_x + cuadro_w / 2
        label_x = base_x - (total_width / 2)
        score_x = label_x + label_width + espacio_texto
        linea_y = cuadro_y + cuadro_h / 2 - 6

        glColor4f(0.0, 0.0, 0.0, 0.85)
        render_bitmap_string(label_x + 2, linea_y - 2, GLUT_BITMAP_HELVETICA_18, texto_label)
        render_bitmap_string(score_x + 3, linea_y - 3, GLUT_BITMAP_TIMES_ROMAN_24, texto_score)
        glColor3f(1.0, 0.95, 0.4)
        render_bitmap_string(label_x, linea_y, GLUT_BITMAP_HELVETICA_18, texto_label)
        render_bitmap_string(score_x, linea_y, GLUT_BITMAP_TIMES_ROMAN_24, texto_score)

        dibujar_minimapa()

        if fantasmas_asustados:
            pass
        
        if estado_actual == ESTADO_INTRO:
            if 'id_textura_preparate' in globals() and id_textura_preparate and id_textura_preparate != 0:
                if id_textura_preparate_ancho > 0 and id_textura_preparate_alto > 0:
                    aspect = float(id_textura_preparate_ancho) / float(id_textura_preparate_alto)
                else:
                    aspect = 4.5
                max_h = min(260.0, ventana_alto * 0.55)
                quad_h = max_h
                quad_w = quad_h * aspect * 0.85
                max_w = ventana_ancho * 4
                if quad_w > max_w:
                    quad_w = max_w
                    quad_h = quad_w / (aspect * 0.85)
                quad_x = ventana_ancho / 2 - quad_w / 2
                quad_y = ventana_alto / 2 - quad_h / 2
                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, id_textura_preparate)
                glColor3f(1.0, 1.0, 1.0)
                glBegin(GL_QUADS)
                glTexCoord2f(0.0, 0.0); glVertex2f(quad_x, quad_y)
                glTexCoord2f(1.0, 0.0); glVertex2f(quad_x + quad_w, quad_y)
                glTexCoord2f(1.0, 1.0); glVertex2f(quad_x + quad_w, quad_y + quad_h)
                glTexCoord2f(0.0, 1.0); glVertex2f(quad_x, quad_y + quad_h)
                glEnd(); glDisable(GL_TEXTURE_2D)
            else:
                glColor3f(1.0, 1.0, 0.0)
                render_bitmap_string(int(ventana_ancho/2) - 80, int(ventana_alto/2), GLUT_BITMAP_TIMES_ROMAN_24, "¡PREPARATE!")

    elif estado_actual == ESTADO_PAUSA:
        glColor4f(0.0, 0.0, 0.0, 0.75); glBegin(GL_QUADS); glVertex2f(0, 0); glVertex2f(ventana_ancho, 0); glVertex2f(ventana_ancho, ventana_alto); glVertex2f(0, ventana_alto); glEnd()
        if id_textura_pausa and id_textura_pausa != 0:
            pausa_w = 420
            pausa_h = 144
            pausa_x = ventana_ancho / 2 - pausa_w / 2
            pausa_y = ventana_alto / 2 + 120
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, id_textura_pausa)
            glColor3f(1.0, 1.0, 1.0)
            glBegin(GL_QUADS)
            glTexCoord2f(0.0, 0.0); glVertex2f(pausa_x, pausa_y)
            glTexCoord2f(1.0, 0.0); glVertex2f(pausa_x + pausa_w, pausa_y)
            glTexCoord2f(1.0, 1.0); glVertex2f(pausa_x + pausa_w, pausa_y + pausa_h)
            glTexCoord2f(0.0, 1.0); glVertex2f(pausa_x, pausa_y + pausa_h)
            glEnd(); glDisable(GL_TEXTURE_2D)
        else:
            glColor3f(1.0, 1.0, 0.0); render_bitmap_string(int(ventana_ancho/2) - 60, int(ventana_alto/2) + 120, GLUT_BITMAP_TIMES_ROMAN_24, "PAUSA")
        draw_button_texture(boton_reanudar_rect, id_textura_boton_reanudar)
        draw_button_texture(boton_menu_pausa_rect, id_textura_boton_menu_principal)
        draw_button_texture(boton_salir_pausa_rect, id_textura_boton_salir_del_juego)

    elif estado_actual == ESTADO_GAME_OVER:
        glColor4f(0.0, 0.0, 0.0, 0.80); glBegin(GL_QUADS); glVertex2f(0, 0); glVertex2f(ventana_ancho, 0); glVertex2f(ventana_ancho, ventana_alto); glVertex2f(0, ventana_alto); glEnd()
        img_go_w = 600; img_go_h = 220; img_go_x = ventana_ancho / 2 - img_go_w / 2; img_go_y = ventana_alto / 2 + 80
        glEnable(GL_TEXTURE_2D); glBindTexture(GL_TEXTURE_2D, id_textura_game_over); glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex2f(img_go_x, img_go_y); glTexCoord2f(1.0, 0.0); glVertex2f(img_go_x + img_go_w, img_go_y)
        glTexCoord2f(1.0, 1.0); glVertex2f(img_go_x + img_go_w, img_go_y + img_go_h); glTexCoord2f(0.0, 1.0); glVertex2f(img_go_x, img_go_y + img_go_h)
        glEnd(); glDisable(GL_TEXTURE_2D)
        draw_button_texture(boton_reiniciar_go_rect, id_textura_boton_volver_a_jugar)
        draw_button_texture(boton_menu_go_rect,      id_textura_boton_menu_principal)
        draw_button_texture(boton_salir_go_rect,     id_textura_boton_salir_del_juego)

    elif estado_actual == ESTADO_VICTORIA:
        glColor4f(0.0, 0.0, 0.0, 0.80); glBegin(GL_QUADS); glVertex2f(0, 0); glVertex2f(ventana_ancho, 0); glVertex2f(ventana_ancho, ventana_alto); glVertex2f(0, ventana_alto); glEnd()
        

        # Escalar y posicionar logo de victoria ligeramente más pequeño y dejar espacio para el puntaje
        br_y = boton_reiniciar_go_rect[1]
        br_h = boton_reiniciar_go_rect[3]
        img_h = 140
        img_w = int(img_h * (600.0 / 220.0))
        img_x = ventana_ancho / 2 - img_w / 2
        img_y = br_y + br_h + 40

        if 'id_textura_titulo_victoria' in globals() and id_textura_titulo_victoria and id_textura_titulo_victoria != 0:
            glEnable(GL_TEXTURE_2D); glBindTexture(GL_TEXTURE_2D, id_textura_titulo_victoria); glColor3f(1.0, 1.0, 1.0)
            glBegin(GL_QUADS)
            glTexCoord2f(0.0, 0.0); glVertex2f(img_x, img_y)
            glTexCoord2f(1.0, 0.0); glVertex2f(img_x + img_w, img_y)
            glTexCoord2f(1.0, 1.0); glVertex2f(img_x + img_w, img_y + img_h)
            glTexCoord2f(0.0, 1.0); glVertex2f(img_x, img_y + img_h)
            glEnd(); glDisable(GL_TEXTURE_2D)
        else:
            glLineWidth(4.0); glColor3f(0.0, 0.85, 1.0); glBegin(GL_LINE_LOOP); glVertex2f(ventana_ancho/2 - 280, ventana_alto/2 - 120); glVertex2f(ventana_ancho/2 + 280, ventana_alto/2 - 120); glVertex2f(ventana_ancho/2 + 280, ventana_alto/2 + 120); glVertex2f(ventana_ancho/2 - 280, ventana_alto/2 + 120); glEnd()

        # Puntaje final: colocarlo entre el logo y los botones
        score_y = br_y + br_h + 12
        score_text = f"PUNTAJE FINAL: {puntaje:05d}"
        score_x = int(ventana_ancho/2) - (len(score_text) * 6)
        glColor4f(0.0, 0.0, 0.0, 0.85)
        render_bitmap_string(score_x + 2, int(score_y) - 2, GLUT_BITMAP_TIMES_ROMAN_24, score_text)
        glColor3f(1.0, 1.0, 1.0)
        render_bitmap_string(score_x, int(score_y), GLUT_BITMAP_TIMES_ROMAN_24, score_text)

        # Reusar botones existentes: volver a jugar, menu principal, salir del juego
        draw_button_texture(boton_reiniciar_go_rect, id_textura_boton_volver_a_jugar)
        draw_button_texture(boton_menu_go_rect,      id_textura_boton_menu_principal)
        draw_button_texture(boton_salir_go_rect,     id_textura_boton_salir_del_juego)

    restore_perspective()

def procesar_teclado_navegacion(window):
    global pacman_x, pacman_z, pacman_angulo_rotacion, estado_actual, esc_presionado_antes

    esc_ahora = glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS

    if estado_actual in (ESTADO_RECORDS, ESTADO_VICTORIA, ESTADO_GAME_OVER):
        if esc_ahora and not esc_presionado_antes: estado_actual = ESTADO_MENU
        esc_presionado_antes = esc_ahora; return

    if estado_actual == ESTADO_PAUSA:
        if esc_ahora and not esc_presionado_antes:
            estado_actual = ESTADO_JUEGO
            reproducir_sonido_pausa()
        esc_presionado_antes = esc_ahora; return

    if estado_actual == ESTADO_JUEGO:
        if esc_ahora and not esc_presionado_antes:
            estado_actual = ESTADO_PAUSA
            reproducir_sonido_pausa()
            esc_presionado_antes = True; return
        esc_presionado_antes = esc_ahora

        if en_pausa_fantasma: return

        speed = 0.05; dx, dz = 0, 0
        if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:    dz = -speed; pacman_angulo_rotacion = 180.0
        if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:  dz = speed;  pacman_angulo_rotacion = 0.0
        if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:  dx = -speed; pacman_angulo_rotacion = 270.0
        if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS: dx = speed;  pacman_angulo_rotacion = 90.0
        if dx != 0 and not verificar_colision(pacman_x + dx, pacman_z): pacman_x += dx
        if dz != 0 and not verificar_colision(pacman_x, pacman_z + dz): pacman_z += dz

# ==============================================================================
# LOOP PRINCIPAL
# ==============================================================================
def main():
    global puntaje, pacman_vidas, pacman_x, pacman_z, estado_actual, puntos, fantasmas, capsulas_poder, fantasmas_asustados, tiempo_fantasmas_asustados, tiempo_inicio_muerte, tiempo_inicio_intro, tiempo_inicio_juego
    global boca_angulo, boca_abriendo, id_textura_muro, id_textura_piso, id_textura_arbol, id_textura_piso_exterior, id_textura_corazon, id_textura_menu, id_textura_boton, id_textura_boton_jugar, id_textura_boton_menu_principal, id_textura_boton_puntuacion, id_textura_boton_reanudar, id_textura_boton_salir, id_textura_boton_salir_del_juego, id_textura_boton_volver_a_jugar, id_textura_titulo_menu, id_textura_game_over, id_textura_pausa, id_textura_cuadro_puntuacion, id_textura_titulo_victoria, id_textura_preparate, id_textura_plantilla_puntuacion, pacman_invulnerable, pacman_tiempo_invulnerable, record_guardado
    global musica_actual, fx_comer, fx_muerte, fx_retorno, fx_pausa, fx_victoria, en_pausa_fantasma, tiempo_pausa_fantasma
    
    if not glfw.init(): return
    window = glfw.create_window(ventana_ancho, ventana_alto, "Pac-Man 3D", None, None)
    if not window: glfw.terminate(); return
        
    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, redimensionar_ventana_callback)
    glfw.set_mouse_button_callback(window, mouse_click_callback)
    
    glEnable(GL_DEPTH_TEST); glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA) 
    glEnable(GL_ALPHA_TEST); glAlphaFunc(GL_GREATER, 0.5); glClearColor(0.01, 0.03, 0.01, 1.0) 

    generar_datos_bosque() 
    
    id_textura_muro          = cargar_textura_imagen("textura_muro.png")
    id_textura_piso          = cargar_textura_imagen("textura_piso.png")
    id_textura_arbol         = cargar_textura_imagen("textura_arbol.png")
    id_textura_piso_exterior   = cargar_textura_imagen("textura_piso_exterior.png") 
    id_textura_corazon         = cargar_textura_imagen("textura_corazon.png") 
    id_textura_menu                    = cargar_textura_imagen("textura_menu.png")
    id_textura_boton                   = cargar_textura_imagen("textura_boton.png")
    id_textura_boton_jugar             = cargar_textura_imagen("boton_jugar.png")
    id_textura_boton_menu_principal    = cargar_textura_imagen("boton_menuPrincipal.png")
    id_textura_boton_puntuacion        = cargar_textura_imagen("boton_puntuacion.png")
    id_textura_boton_reanudar          = cargar_textura_imagen("boton_reanudar.png")
    id_textura_boton_salir             = cargar_textura_imagen("boton_salir.png")
    id_textura_boton_salir_del_juego   = cargar_textura_imagen("boton_salirDelJuego.png")
    id_textura_boton_volver_a_jugar    = cargar_textura_imagen("boton_volverAjugar.png")
    id_textura_titulo_menu             = cargar_textura_imagen("titulo_menu.png")
    id_textura_game_over               = cargar_textura_imagen("game_over.png")
    id_textura_pausa                   = cargar_textura_imagen("pausa.png")
    id_textura_cuadro_puntuacion       = cargar_textura_imagen("cuadro_puntuacion.png")
    id_textura_titulo_victoria         = cargar_textura_imagen("titulo_victoria.png")
    id_textura_preparate               = cargar_textura_imagen("imagen_preparate.png")
    id_textura_plantilla_puntuacion    = cargar_textura_imagen("plantilla_puntuacion.png")
    if os.path.exists("imagen_preparate.png"):
        try:
            img = Image.open("imagen_preparate.png")
            id_textura_preparate_ancho, id_textura_preparate_alto = img.size
        except Exception:
            id_textura_preparate_ancho, id_textura_preparate_alto = 520, 120
    if id_textura_pausa == 0:
        print("Warning: no se pudo cargar pausa.png, se usará texto de fallback en PAUSA")

    compilar_geometria_estatica()

    mixer.init()
    try:
        fx_comer = mixer.Sound("sonido_comer.wav")    
        fx_muerte = mixer.Sound("sonido_muerte.wav")  
        fx_retorno = mixer.Sound("sonido_retorno.wav") 
        fx_pausa = mixer.Sound("sonido_pausa.wav")
        try:
            fx_victoria = mixer.Sound("sonido_victoria.wav")
        except Exception:
            fx_victoria = None
    except Exception as e:
        print(f"Aviso de Audio Opcional: {e}")

    actualizar_volumen_maestro()

    while not glfw.window_should_close(window):
        tiempo_actual = glfw.get_time()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if estado_actual == ESTADO_MENU:
            if musica_actual != "menu":
                mixer.music.stop()
                try:
                    mixer.music.load("sonido_menu.mp3") 
                    mixer.music.play(-1) 
                except Exception as e:
                    print(f"Warning: no se pudo cargar 'sonido_menu.mp3': {e}")
                musica_actual = "menu"
            renderizar_menu_principal(); procesar_teclado_navegacion(window)
            
        elif estado_actual == ESTADO_RECORDS:
            renderizar_pantalla_records(); procesar_teclado_navegacion(window)

        elif estado_actual in (ESTADO_JUEGO, ESTADO_PAUSA, ESTADO_GAME_OVER, ESTADO_VICTORIA, ESTADO_MUERTE, ESTADO_INTRO):
            
            if estado_actual == ESTADO_INTRO:
                if musica_actual != "intro":
                    mixer.music.stop()
                    try:
                        mixer.music.load("sonido_intro.mp3") 
                        mixer.music.play(0) 
                    except Exception as e:
                        print(f"Warning: no se pudo cargar 'sonido_intro.mp3': {e}")
                    musica_actual = "intro"
                if tiempo_actual - tiempo_inicio_intro > 4.2:
                    estado_actual = ESTADO_JUEGO
                    tiempo_inicio_juego = tiempo_actual

            elif estado_actual == ESTADO_JUEGO:
                if musica_actual == "pausa":
                    mixer.music.unpause()
                    musica_actual = musica_anterior_pausa or "juego"
                    musica_anterior_pausa = None
                elif musica_actual not in ("juego", "fantasma_asustado"):
                    reproducir_musica_juego_etapa(1)

                if fantasmas_asustados:
                    reproducir_musica_fantasma_asustado()
                else:
                    restablecer_musica_juego_por_progreso()
            elif estado_actual == ESTADO_PAUSA:
                if musica_actual in ("juego", "fantasma_asustado"):
                    mixer.music.pause()
                    musica_anterior_pausa = musica_actual
                    musica_actual = "pausa"
            elif estado_actual == ESTADO_MUERTE:
                if musica_actual in ("juego", "fantasma_asustado"):
                    mixer.music.stop()
                    try: fx_muerte.play()
                    except: pass
                    musica_actual = "muerte"
            elif estado_actual == ESTADO_GAME_OVER:
                if musica_actual != "game_over":
                    mixer.music.stop()
                    try:
                        mixer.music.load("sonido_gameover.mp3") 
                        mixer.music.play(0)
                    except: pass
                    musica_actual = "game_over"
            elif estado_actual == ESTADO_VICTORIA:
                if musica_actual != "victoria":
                    mixer.music.stop()
                    try:
                        if fx_victoria:
                            fx_victoria.play()
                        else:
                            mixer.music.load("sonido_victoria.mp3")
                            mixer.music.play(0)
                    except Exception:
                        pass
                    musica_actual = "victoria"

            glMatrixMode(GL_PROJECTION); glLoadIdentity()
            gluPerspective(60, float(ventana_ancho)/float(ventana_alto), 0.1, 100.0)
            glMatrixMode(GL_MODELVIEW); glLoadIdentity()
            
            cam_x = pacman_x if estado_actual in (ESTADO_JUEGO, ESTADO_MUERTE, ESTADO_INTRO, ESTADO_PAUSA) else 1.5
            cam_z = pacman_z if estado_actual in (ESTADO_JUEGO, ESTADO_MUERTE, ESTADO_INTRO, ESTADO_PAUSA) else 1.5
            gluLookAt(cam_x, 6.2, cam_z + 4.8, cam_x, 0.2, cam_z, 0.0, 1.0, 0.0)

            draw_floor_textured(); draw_jungle_background(); glCallList(lista_muros_id)

            if fantasmas_asustados and (tiempo_actual - tiempo_fantasmas_asustados > DURACION_PODER):
                fantasmas_asustados = False

            if pacman_invulnerable and (tiempo_actual - pacman_tiempo_invulnerable > DURACION_INMUNIDAD):
                pacman_invulnerable = False

            for cap in capsulas_poder:
                glPushMatrix()
                glWithEfecto = 0.15 + 0.04 * math.sin(tiempo_actual * 5)
                glTranslatef(cap[0], glWithEfecto, cap[1])
                glCallList(lista_capsula_id)
                glPopMatrix()

            if estado_actual in (ESTADO_JUEGO, ESTADO_INTRO):
                procesar_teclado_navegacion(window)

                if en_pausa_fantasma:
                    if tiempo_actual - tiempo_pausa_fantasma > DURACION_PAUSA_FANTASMA:
                        en_pausa_fantasma = False 
                    
                if boca_abriendo and not en_pausa_fantasma and estado_actual == ESTADO_JUEGO:
                    boca_angulo += 0.05
                    if boca_angulo >= 0.65: boca_abriendo = False
                elif not en_pausa_fantasma and estado_actual == ESTADO_JUEGO:
                    boca_angulo -= 0.05
                    if boca_angulo <= 0.0: boca_abriendo = True

                if estado_actual == ESTADO_JUEGO and not en_pausa_fantasma:
                    for p in puntos[:]:
                        if math.sqrt((pacman_x - p[0])**2 + (pacman_z - p[1])**2) < 0.4:
                            puntos.remove(p); puntaje += 10
                            try: fx_comer.play() 
                            except: pass
                        glPushMatrix(); glTranslatef(p[0], 0.15, p[1]); glCallList(lista_moneda_id); glPopMatrix()

                    for cap in capsulas_poder[:]:
                        if math.sqrt((pacman_x - cap[0])**2 + (pacman_z - cap[1])**2) < 0.45:
                            capsulas_poder.remove(cap); puntaje += 50
                            fantasmas_asustados = True; tiempo_fantasmas_asustados = tiempo_actual
                            try: fx_comer.play() 
                            except: pass
                else:
                    for p in puntos:
                        glPushMatrix(); glTranslatef(p[0], 0.15, p[1]); glCallList(lista_moneda_id); glPopMatrix()

# --- CONTROLADOR MAESTRO DE LOS 4 FANTASMAS (IA DE MOVIMIENTO CORREGIDA) ---
                tiempo_de_juego = tiempo_actual - tiempo_inicio_juego
                for idx, f in enumerate(fantasmas):
                    if f[7]:
                        vel_actual = 0.10  # Velocidad express para el retorno de los ojos
                    elif fantasmas_asustados:
                        vel_actual = 0.04  # Mitad de velocidad en estado de huida (bola rosa)
                    else:
                        vel_actual = 0.04  # Velocidad estándar de persecución

                    # 1. Espera inicial escalonada dentro de la casa central
                    if estado_actual == ESTADO_JUEGO and tiempo_de_juego < f[8] and not f[7]:
                        if f[3] == 0.0 or abs(f[3]) != 0.02: f[3] = 0.02
                        if f[1] > 6.65: f[3] = -0.02
                        elif f[1] < 6.35: f[3] = 0.02
                        f[1] += f[3]
                        f[2] = 0.0
                    
                    # 2. Lógica de salida guiada obligatoria hacia la puerta central
                    elif 5.0 <= f[1] <= 7.2 and 11.0 <= f[0] <= 15.0 and not f[7] and not en_pausa_fantasma and estado_actual == ESTADO_JUEGO:
                        if abs(f[0] - 13.5) > 0.05:
                            f[2] = 0.04 if f[0] < 13.5 else -0.04
                            f[3] = 0.0
                            f[0] += f[2]
                        else:
                            f[0] = 13.5
                            f[2] = 0.0
                            f[3] = -0.04
                            f[1] += f[3]

                    # 3. LÓGICA DE MOVIMIENTO MATRICIAL POR PASILLOS (INTERPOLACIÓN DE INTERSECCIONES)
                    elif not en_pausa_fantasma and estado_actual == ESTADO_JUEGO:
                        centro_x = int(f[0]) + 0.5
                        centro_z = int(f[1]) + 0.5
                        
                        # Corrección matemática: Evaluamos si el fantasma cruzará o alcanzará el centro de la baldosa en este frame
                        llego_al_centro = False
                        if f[2] > 0 and f[0] <= centro_x and f[0] + f[2] >= centro_x: llego_al_centro = True
                        elif f[2] < 0 and f[0] >= centro_x and f[0] + f[2] <= centro_x: llego_al_centro = True
                        elif f[3] > 0 and f[1] <= centro_z and f[1] + f[3] >= centro_z: llego_al_centro = True
                        elif f[3] < 0 and f[1] >= centro_z and f[1] + f[3] <= centro_z: llego_al_centro = True
                        
                        f_dx = math.copysign(vel_actual, f[2]) if f[2] != 0 else 0.0
                        f_dz = math.copysign(vel_actual, f[3]) if f[3] != 0 else 0.0
                        
                        # Si choca contra un muro o llega al centro geométrico de la celda, decide nuevo rumbo
                        if verificar_colision(f[0] + f_dx, f[1] + f_dz) or llego_al_centro:
                            f[0] = centro_x
                            f[1] = centro_z
                            
                            tx, tz = int(f[0]), int(f[1])
                            caminos_libres = []
                            direcciones_posibles = [
                                (0.0, -1.0, 0, -1), # Arriba
                                (0.0, 1.0, 0, 1),   # Abajo
                                (-1.0, 0.0, -1, 0), # Izquierda
                                (1.0, 0.0, 1, 0)    # Derecha
                            ]
                            
                            for dx_p, dz_p, cx_off, cz_off in direcciones_posibles:
                                # Filtro estricto de 180° comparando solo signos vectoriales
                                if f[2] != 0 and dx_p == -math.copysign(1.0, f[2]): continue
                                if f[3] != 0 and dz_p == -math.copysign(1.0, f[3]): continue
                                
                                nx_cell = tx + cx_off
                                nz_cell = tz + cz_off
                                if 0 <= nx_cell < ANCHO_MAPA and 0 <= nz_cell < ALTO_MAPA:
                                    if MAPA[nz_cell][nx_cell] == 0:
                                        caminos_libres.append((dx_p * vel_actual, dz_p * vel_actual, nx_cell, nz_cell))
                            
                            # Fallback si entra en un callejón sin salida
                            if not caminos_libres:
                                for dx_p, dz_p, cx_off, cz_off in direcciones_posibles:
                                    nx_cell = tx + cx_off
                                    nz_cell = tz + cz_off
                                    if 0 <= nx_cell < ANCHO_MAPA and 0 <= nz_cell < ALTO_MAPA:
                                        if MAPA[nz_cell][nx_cell] == 0:
                                            caminos_libres.append((dx_p * vel_actual, dz_p * vel_actual, nx_cell, nz_cell))
                                            
                            if caminos_libres:
                                mejor_opcion = caminos_libres[0]
                                if f[7]:
                                    # CASO OJOS: Priorizar paso directo hacia la base (13.5,6.5), fallback a BFS si está bloqueado
                                    dir_x = 13.5 - f[0]
                                    dir_z = 6.5 - f[1]
                                    prefer_x = abs(dir_x) >= abs(dir_z)
                                    step_x = math.copysign(vel_actual, dir_x) if dir_x != 0 and prefer_x else 0.0
                                    step_z = math.copysign(vel_actual, dir_z) if dir_z != 0 and not prefer_x else 0.0
                                    elegido = False
                                    for dx, dz, cx, cz in caminos_libres:
                                        if step_x != 0 and dx != 0 and math.copysign(1.0, dx) == math.copysign(1.0, step_x):
                                            mejor_opcion = (dx, dz); elegido = True; break
                                        if step_z != 0 and dz != 0 and math.copysign(1.0, dz) == math.copysign(1.0, step_z):
                                            mejor_opcion = (dx, dz); elegido = True; break
                                    if not elegido:
                                        dir_retorno = obtener_siguiente_direccion_retorno(f[0], f[1], vel_actual)
                                        if dir_retorno != (0.0, 0.0):
                                            mejor_opcion = dir_retorno
                                        else:
                                            min_distancia = float('inf')
                                            for dx, dz, cx, cz in caminos_libres:
                                                dist = (cx + 0.5 - 13.5)**2 + (cz + 0.5 - 6.5)**2
                                                if dist < min_distancia:
                                                    min_distancia = dist
                                                    mejor_opcion = (dx, dz)
                                elif fantasmas_asustados:
                                    # CASO BOLA ROSA: Maximizar la distancia euclidiana respecto a Pac-Man (Huida real)
                                    max_distancia = -1.0
                                    for dx, dz, cx, cz in caminos_libres:
                                        dist = (cx + 0.5 - pacman_x)**2 + (cz + 0.5 - pacman_z)**2
                                        if dist > max_distancia:
                                            max_distancia = dist
                                            mejor_opcion = (dx, dz)
                                else:
                                    # CASO PERSECUCIÓN: ¡SISTEMA DE PERSONALIDADES ACTIVO!
                                    t_x, t_z = pacman_x, pacman_z
                                    
                                    if idx == 1: # Pinky (Rosado): Emboscada. Intenta ganar el paso 3 celdas adelante
                                        if pacman_angulo_rotacion == 90.0: t_x += 3.0
                                        elif pacman_angulo_rotacion == 270.0: t_x -= 3.0
                                        elif pacman_angulo_rotacion == 180.0: t_z -= 3.0
                                        elif pacman_angulo_rotacion == 0.0: t_z += 3.0
                                        
                                    elif idx == 2: # Inky (Cian): Flanqueo. Busca una ruta paralela desviándose lateralmente
                                        if pacman_angulo_rotacion in (90.0, 270.0): t_z += 2.0
                                        else: t_x += 2.0
                                        
                                    elif idx == 3: # Clyde (Naranja): Distraído. Si se acerca mucho, huye a su esquina
                                        dist_cuadrada = (f[0] - pacman_x)**2 + (f[1] - pacman_z)**2
                                        if dist_cuadrada < 25.0: 
                                            t_x, t_z = 1.5, 11.5 
                                    
                                    min_distancia = float('inf')
                                    for dx, dz, cx, cz in caminos_libres:
                                        dist = (cx + 0.5 - t_x)**2 + (cz + 0.5 - t_z)**2
                                        if dist < min_distancia:
                                            min_distancia = dist
                                            mejor_opcion = (dx, dz)
                                            
                                f[2], f[3] = mejor_opcion[0], mejor_opcion[1]

                            if f[7] and abs(f[0] - 13.5) < 0.25 and abs(f[1] - 6.5) < 0.25:
                                f[0], f[1] = 13.5, 6.5
                                f[7] = False

                        # UNICO DESPLAZAMIENTO FÍSICO REAL (Fuera del bloque IF de arriba)
                        f_dx = math.copysign(vel_actual, f[2]) if f[2] != 0 else 0.0
                        f_dz = math.copysign(vel_actual, f[3]) if f[3] != 0 else 0.0
                        if not verificar_colision(f[0] + f_dx, f[1] + f_dz):
                            f[0] += f_dx
                            f[1] += f_dz

                        # Al llegar por el camino al centro exacto de la base, los ojos resucitan de inmediato
                        if f[7] and abs(f[0] - 13.5) < 0.20 and abs(f[1] - 6.5) < 0.20:
                            f[0], f[1] = 13.5, 6.5
                            f[7] = False

                    # Procesar impactos y capturas contra Pac-Man
                    if estado_actual == ESTADO_JUEGO and not en_pausa_fantasma and not f[7] and tiempo_de_juego >= f[8]:
                        distancia_letal = math.sqrt((pacman_x - f[0])**2 + (pacman_z - f[1])**2)
                        if distancia_letal < 0.42:
                            if fantasmas_asustados:
                                puntaje += 100
                                agregar_popup_puntaje_fantasma(f[0], f[1], "100")
                                f[7] = True 
                                en_pausa_fantasma = True
                                tiempo_pausa_fantasma = tiempo_actual
                                try: fx_comer.play() 
                                except: pass
                            elif not pacman_invulnerable:
                                estado_actual = ESTADO_MUERTE
                                tiempo_inicio_muerte = tiempo_actual
                                break

                    glPushMatrix(); glTranslatef(f[0], 0.22, f[1])
                    if f[7]: draw_ghost(0, 0, 0, solo_ojos=True) 
                    elif fantasmas_asustados: draw_ghost(0.1, 0.2, 0.9) 
                    else: draw_ghost(f[4][0], f[4][1], f[4][2])
                    glPopMatrix()

                if any(fant[7] for fant in fantasmas) and estado_actual == ESTADO_JUEGO:
                    if not mixer.Channel(2).get_busy():
                        try: mixer.Channel(2).play(fx_retorno, loops=-1)
                        except: pass
                else:
                    mixer.Channel(2).stop()

                dibujar_pacman = not (pacman_invulnerable and int((tiempo_actual - pacman_tiempo_invulnerable) / 0.15) % 2 == 0)
                if dibujar_pacman:
                    glPushMatrix(); glTranslatef(pacman_x, 0.22, pacman_z)
                    glRotatef(pacman_angulo_rotacion, 0.0, 1.0, 0.0); draw_pacman_final(0.30, boca_angulo); glPopMatrix()

                if len(puntos) == 0:
                    estado_actual = ESTADO_VICTORIA
                    if not record_guardado: guardar_puntaje(puntaje); record_guardado = True

            elif estado_actual == ESTADO_MUERTE:
                tiempo_muerto = tiempo_actual - tiempo_inicio_muerte
                for p in puntos:
                    glPushMatrix(); glTranslatef(p[0], 0.15, p[1]); glCallList(lista_moneda_id); glPopMatrix()
                for f in fantasmas:
                    glPushMatrix(); glTranslatef(f[0], 0.22, f[1]); draw_ghost(f[4][0], f[4][1], f[4][2], solo_ojos=f[7]); glPopMatrix()

                if tiempo_muerto < duracion_anim_muerte:
                    porcentaje_anim = tiempo_muerto / duracion_anim_muerte
                    escala_actual = 0.30 * (1.0 - porcentaje_anim)
                    giro_muerte = tiempo_muerto * 720.0
                    glPushMatrix()
                    glTranslatef(pacman_x, 0.22, pacman_z)
                    glRotatef(giro_muerte, 0.0, 1.0, 0.0)
                    draw_pacman_final(escala_actual, 0.0)
                    glPopMatrix()
                else:
                    pacman_vidas -= 1; pacman_x, pacman_z = 1.5, 1.5
                    if pacman_vidas <= 0:
                        estado_actual = ESTADO_GAME_OVER
                        if not record_guardado: guardar_puntaje(puntaje); record_guardado = True
                    else:
                        estado_actual = ESTADO_JUEGO
                        pacman_invulnerable = True; pacman_tiempo_invulnerable = tiempo_actual

            elif estado_actual == ESTADO_PAUSA:
                procesar_teclado_navegacion(window)
                for p in puntos:
                    glPushMatrix(); glTranslatef(p[0], 0.15, p[1]); glCallList(lista_moneda_id); glPopMatrix()
                for f in fantasmas:
                    glPushMatrix(); glTranslatef(f[0], 0.22, f[1]); draw_ghost(f[4][0], f[4][1], f[4][2], solo_ojos=f[7]); glPopMatrix()
                glPushMatrix(); glTranslatef(pacman_x, 0.22, pacman_z)
                glRotatef(pacman_angulo_rotacion, 0.0, 1.0, 0.0); draw_pacman_final(0.30, 0.3); glPopMatrix()

            elif estado_actual in (ESTADO_GAME_OVER, ESTADO_VICTORIA):
                procesar_teclado_navegacion(window)

            dibujar_popups_puntaje_fantasma()
            renderizar_hud_interfaz()

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()