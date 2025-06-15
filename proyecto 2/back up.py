import cv2
import os
import random
import csv
from datetime import datetime
import PIL.Image
from PIL import ImageTk
from tkinter import Tk, Label, Button, Entry, Toplevel, StringVar, END, LEFT, RIGHT, X, Frame, CENTER, FLAT, DISABLED, NORMAL, BooleanVar
import tkinter.ttk as ttk
import requests
from datetime import datetime
import xml.etree.ElementTree as ET
import time
import pygame as py

py.mixer.init(frequency=44100, size=-16, channels=32, buffer=4096)  
py.mixer.set_num_channels(8)

tamaño_pantallas= "700x500"
color_boton= "#D9B189"
color_fondo = "#34495e"
PUNTUACIONES_FILE = "puntuaciones_memoria.csv"
inicio_sesion_exitoso = False
usuario_logueado = None
root = None

musica_general = True
sonido_botones = True
efectos_de_sonido=True

"""
==========================================================================================
Registro facial
==========================================================================================
"""
class DetectorRostros:
    def __init__(self):
        self.cascada_rostros = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def detectar_rostros(self, ruta_imagen):
        imagen = cv2.imread(ruta_imagen)
        if imagen is None:
            return None, "No se pudo leer la imagen"
        gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        rostros = self.cascada_rostros.detectMultiScale(gris, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        resultados = [{'caja': [x, y, w, h]} for (x, y, w, h) in rostros]
        return resultados, imagen

class ReconocimientoFacial:
    @staticmethod
    def guardar_rostro(ruta_imagen, resultados, nombre_archivo):
        if not resultados:
            return False
        imagen = cv2.imread(ruta_imagen)
        if imagen is None:
            return False
        x1, y1, w, h = resultados[0]['caja']
        rostro_imagen = imagen[y1:y1+h, x1:x1+w]
        rostro_imagen = cv2.resize(rostro_imagen, (150, 200), interpolation=cv2.INTER_CUBIC)
        cv2.imwrite(nombre_archivo, rostro_imagen)
        return True

    @staticmethod
    def comparar_rostros(ruta_registro, ruta_login):
        detector = cv2.ORB_create()
        imagen1 = cv2.imread(ruta_registro, 0)
        imagen2 = cv2.imread(ruta_login, 0)
        if imagen1 is None or imagen2 is None:
            return 0
        puntos_clave1, descriptores1 = detector.detectAndCompute(imagen1, None)
        puntos_clave2, descriptores2 = detector.detectAndCompute(imagen2, None)
        if descriptores1 is None or descriptores2 is None:
            return 0
        emparejador = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        coincidencias = emparejador.match(descriptores1, descriptores2)
        if not coincidencias:
            return 0
        similares = [m for m in coincidencias if m.distance < 70]
        if len(coincidencias) == 0:
            return 0
        return len(similares) / len(coincidencias)

class GestorCamara:
    @staticmethod
    def capturar_imagen(titulo_ventana, nombre_temp):
        camara = cv2.VideoCapture(0)
        if not camara.isOpened():
            return None, "No se pudo abrir la cámara"
        capturado = None
        while True:
            ok, fotograma = camara.read()
            if not ok:
                break
            cv2.imshow(titulo_ventana, fotograma)
            if cv2.waitKey(1) == 27:  
                capturado = fotograma
                break
        camara.release()
        cv2.destroyAllWindows()
        if capturado is None:
            return None, "Captura cancelada"
        cv2.imwrite(nombre_temp, capturado)
        return nombre_temp, None

class RegistroFacial:
    def __init__(self, root):
        self.root = root
        root.title("Registro Facial")
        root.geometry(tamaño_pantallas)
        root.configure(bg=color_fondo)
        self.nombre_usuario = StringVar()
        self.configurar_ui()

    def configurar_ui(self):
        Label(self.root, text="Registro Facial", font=("Arial", 14), bg= color_fondo).pack(pady=10)
        Label(self.root, text="Ingrese su nombre de usuario:", bg= color_fondo).pack()
        self.entrada_usuario = Entry(self.root, textvariable=self.nombre_usuario)
        self.entrada_usuario.pack(pady=5)
        Button(self.root, text="Capturar Rostro", command=con_click(self.registrar_rostro), bg= color_boton).pack(pady=15)
        self.etiqueta_mensaje = Label(self.root, text="", fg="red", bg= color_fondo)
        self.etiqueta_mensaje.pack()
        Button(self.root, text="Volver", command=con_click(self.root.destroy), bg=color_boton, font=("Arial", 12)).pack(pady=10)

    def registrar_rostro(self):
        nombre_usuario = self.nombre_usuario.get()
        if not nombre_usuario:
            self.mostrar_mensaje("Debe ingresar un nombre de usuario", "red")
            return
        ruta_temp = f"{nombre_usuario}_temp.jpg"
        ruta_imagen, error = GestorCamara.capturar_imagen("Registro Facial - Presiona ESC", ruta_temp)
        if error:
            self.mostrar_mensaje(error, "red")
            return
        detector_rostros = DetectorRostros()
        resultados, _ = detector_rostros.detectar_rostros(ruta_imagen)
        if not resultados:
            self.mostrar_mensaje("No se detectó ningún rostro", "red")
            os.remove(ruta_imagen)
            return
        if ReconocimientoFacial.guardar_rostro(ruta_imagen, resultados, f"{nombre_usuario}.jpg"):
            self.mostrar_mensaje("Registro exitoso!", "green")
            self.entrada_usuario.delete(0, END)
        else:
            self.mostrar_mensaje("Error al registrar", "red")
        os.remove(ruta_imagen)

    def mostrar_mensaje(self, texto, color_texto):
        self.etiqueta_mensaje.config(text=texto, fg=color_texto)

class InicioSesionFacial:
    def __init__(self, root):
        self.root = root
        root.title("Login Facial")
        root.geometry(tamaño_pantallas)
        root.configure(bg=color_fondo)
        self.nombre_usuario = StringVar()
        self.configurar_ui()

    def configurar_ui(self):
        Label(self.root, text="Login Facial", font=("Arial", 14), bg= color_fondo).pack(pady=10)
        Label(self.root, text="Ingrese su nombre de usuario:", bg= color_fondo).pack()
        self.entrada_usuario = Entry(self.root, textvariable=self.nombre_usuario)
        self.entrada_usuario.pack(pady=5)
        Button(self.root, text="Identificarse", command=con_click(self.autenticar), bg= color_boton).pack(pady=15)
        self.etiqueta_mensaje = Label(self.root, text="", fg="red", bg= color_fondo)
        self.etiqueta_mensaje.pack()
        Button(self.root, text="Volver", command=con_click(self.root.destroy), bg=color_boton, font=("Arial", 12)).pack(pady=10)

    def autenticar(self):
        global inicio_sesion_exitoso, usuario_logueado
        nombre_usuario = self.nombre_usuario.get()
        if not nombre_usuario:
            self.mostrar_mensaje("Debe ingresar un nombre de usuario", "red")
            return
        ruta_rostro_registrado = f"{nombre_usuario}.jpg"
        if not os.path.exists(ruta_rostro_registrado):
            self.mostrar_mensaje("Usuario no registrado", "red")
            return
        ruta_temp = f"{nombre_usuario}_login_temp.jpg"
        ruta_imagen, error = GestorCamara.capturar_imagen("Login Facial - Presiona ESC", ruta_temp)
        if error:
            self.mostrar_mensaje(error, "red")
            return
        detector_rostros = DetectorRostros()
        resultados, _ = detector_rostros.detectar_rostros(ruta_imagen)
        if not resultados:
            self.mostrar_mensaje("No se detectó ningún rostro", "red")
            os.remove(ruta_imagen)
            return
        ruta_imagen_login = f"{nombre_usuario}_login.jpg"
        if not ReconocimientoFacial.guardar_rostro(ruta_imagen, resultados, ruta_imagen_login):
            self.mostrar_mensaje("Error en autenticación", "red")
            os.remove(ruta_imagen)
            return
        os.remove(ruta_imagen)
        similitud = ReconocimientoFacial.comparar_rostros(ruta_rostro_registrado, ruta_imagen_login)
        os.remove(ruta_imagen_login)
        if similitud >= 0.70:
            self.mostrar_mensaje(f"Bienvenido {nombre_usuario}!", "green")
            inicio_sesion_exitoso = True
            usuario_logueado = nombre_usuario
            self.root.destroy()
        else:
            self.mostrar_mensaje("Autenticación fallida", "red")
            self.entrada_usuario.delete(0, END)

    def mostrar_mensaje(self, texto, color_texto):
        self.etiqueta_mensaje.config(text=texto, fg=color_texto)

class AppAutenticacion:
    def __init__(self):
        self.ventana_principal = Tk()
        self.ventana_principal.title("Sistema de Autenticación Facial")
        self.ventana_principal.geometry("400x300")
        self.configurar_ui()

    def configurar_ui(self):
        self.ventana_principal.config(bg= color_fondo)
        self.ventana_principal.geometry(tamaño_pantallas)
        Label(self.ventana_principal, text="Autenticación Facial", font=("Arial", 16), bg= color_fondo).pack(pady=30)
        Button(self.ventana_principal, text="Registrarse", height=2, width=20,command=con_click(self.abrir_registro), bg= color_boton).pack(pady=10)
        Button(self.ventana_principal, text="Iniciar Sesión", height=2, width=20,command=con_click(self.abrir_inicio_sesion), bg= color_boton).pack(pady=10)
        Button(self.ventana_principal, text="Volver", command=con_click(self.ventana_principal.destroy), bg=color_boton, font=("Arial", 12)).pack(pady=10)

    def abrir_registro(self):
        ventana_registro = Toplevel(self.ventana_principal)
        RegistroFacial(ventana_registro)

    def abrir_inicio_sesion(self):
        ventana_login = Toplevel(self.ventana_principal)
        InicioSesionFacial(ventana_login)
        self.ventana_principal.wait_window(ventana_login)
        if inicio_sesion_exitoso:
            self.ventana_principal.destroy()
            mostrar_pantalla_intermedia()

    def ejecutar(self):
        self.ventana_principal.mainloop()

"""
Configuraciones generales
"""
def mostrar_pantalla_intermedia():
    root_intermedia = Tk()
    root_intermedia.title("Acceso Concedido")
    root_intermedia.geometry(tamaño_pantallas)
    root_intermedia.configure(bg=color_fondo)

    if musica_general:
        musica_lob()

    def iniciar_juego_memoria():
        root_intermedia.destroy()
        IniciadorCartas.ejecutar_juego(usuario_logueado)

    def iniciar_juego_de_patrones():
        root_intermedia.destroy()
        JuegoPatrones.ejecutar(on_game_end=lambda score: guardar_en_txt(usuario_logueado, score))

    def abrir_ventana_premios():
        gestor_premios = GestorPremios()
        ventana_premios = Toplevel(root_intermedia)
        VentanaPremios(ventana_premios, gestor_premios)
    
    def abrir_ventana_sonidos():
        ventana_sonidos = Toplevel()
        ConfiguracionPantalla(ventana_sonidos)


    Label(root_intermedia, text="¡Login Exitoso!", font=("Arial", 18, "bold"), bg=color_fondo).pack(pady=30)
    Button(root_intermedia, text="Continuar al Juego de Memoria", command=con_click(iniciar_juego_memoria), height=2, width=25, font=("Arial", 12), bg= color_boton).pack(pady=20)
    Button(root_intermedia, text="Continuar al Juego de Patrones", command=con_click(iniciar_juego_de_patrones), height=2, width=25, font=("Arial", 12), bg= color_boton).pack(pady=20)
    Button(root_intermedia, text="Continuar a la tienda", command=con_click(abrir_ventana_premios), height=2, width=25, font=("Arial", 12), bg= color_boton).pack(pady=20)
    Button(root_intermedia, text="configurar sonidos", command=con_click(abrir_ventana_sonidos), height=2, width=25, font=("Arial", 12), bg= color_boton).pack(pady=20)
    Button(root_intermedia, text="Volver", command=con_click(root_intermedia.destroy), bg=color_boton, font=("Arial", 12)).pack(pady=10)
    root_intermedia.mainloop()

class IniciadorCartas:
    @staticmethod
    def ejecutar_juego(usuario_logueado):
        ruta_base_imagenes = "C:\\Users\\Usuario\\Desktop\\proyecto 2\\imagenes"
        rutas_imagenes = [os.path.join(ruta_base_imagenes, f"imagen_{i+1}.png") for i in range(18)]
        for ruta in rutas_imagenes:
            if not os.path.exists(ruta):
                print(f"Advertencia: La imagen no existe en la ruta: {ruta}. Asegúrate de que el path sea correcto.")
        juego_memoria = Juego_Memoria()
        juego_memoria.agregar_jugador(f"{usuario_logueado} (Jugador 1)") 
        juego_memoria.agregar_jugador(f"{usuario_logueado} (Jugador 2)") 
        juego_memoria.iniciar_juego(rutas_imagenes)
        interfaz_juego = InterfazJuego(juego_memoria, usuario_logueado)
        interfaz_juego.iniciar()
"""
=====================================================================================================
Ventana de premios/ obtencion de el dolar
=====================================================================================================
"""

def obtener_cambio():
    url = "https://gee.bccr.fi.cr/Indicadores/Suscripciones/WS/wsindicadoreseconomicos.asmx/ObtenerIndicadoresEconomicos"
    token = "AARANAMO0I"  
    correo = "joseandreschava09@gmail.com"  
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    params = {
        "Token": token,
        "Indicador": "317",  
        "Nombre": "Tipo de cambio de compra",  
        "SubNiveles": "N",
        "CorreoElectronico": correo,
        "FechaInicio": fecha_actual,
        "FechaFinal": fecha_actual
    }
    response = requests.post(url, data=params, timeout=10)
    response.raise_for_status() 
    root = ET.fromstring(response.text)
    valor_element = root.find('.//NUM_VALOR')
    tipo_cambio_compra = float(valor_element.text)
    print(f"cambio = {tipo_cambio_compra}")
    return tipo_cambio_compra 


def guardar_en_txt(nombre, puntos):
    txt_path = 'C:\\Users\\Usuario\\Desktop\\proyecto 2\\Premios.txt'
    os.makedirs(os.path.dirname(txt_path), exist_ok=True)

    datos_existentes = []
    if os.path.exists(txt_path):
        with open(txt_path, 'r') as txt_file:
            lineas = txt_file.read().splitlines()
            for linea in lineas:
                if linea.strip():
                    try:
                        nombre_existente, kills_existentes_str = linea.strip().split(',')
                        datos_existentes.append([nombre_existente, int(kills_existentes_str)])
                    except ValueError:
                        continue

    encontrado = False
    for i, (n, k) in enumerate(datos_existentes):
        if n == nombre:
            datos_existentes[i][1] = max(k, puntos)
            encontrado = True
            break
    if not encontrado:
        datos_existentes.append([nombre, puntos])

    datos_existentes = sorted(datos_existentes, key=lambda x: x[1], reverse=True)[:5]

    with open(txt_path, 'w') as txt_file:
        for jugador in datos_existentes:
            txt_file.write(f"{jugador[0]},{jugador[1]}\n")

def Top():
    global root
    if root:
        root.destroy()
    root = Tk()
    root.title("Top Jugadores")
    root.configure(bg=color_fondo)
    root.geometry(tamaño_pantallas)

    main_frame = Frame(root, bg=color_fondo)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    Label(main_frame, text="TOP JUGADORES", font=("Arial", 24, "bold"), bg=color_fondo, fg="#333333").pack(pady=5)

    tables_frame = Frame(main_frame, bg=color_fondo)
    tables_frame.pack(fill="both", expand=True)

    style = ttk.Style()
    style.configure("Treeview", font=("Arial", 12), rowheight=25)
    style.configure("Treeview.Heading", font=("Arial", 14, "bold"))

    columns = ("posicion", "nombre", "kills")

    def crear_tabla(parent, title, filepath, height=8):
        frame = Frame(parent, bg=color_fondo)
        frame.pack(fill="both", expand=True, pady=(0, 20))
        Label(frame, text=title, font=("Arial", 16, "bold"), bg=color_fondo, fg="#333333").pack(pady=(0, 10))
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=height)
        tree.pack(fill="both", expand=True, padx=10)

        tree.heading("posicion", text="POSICIÓN")
        tree.heading("nombre", text="NOMBRE")
        tree.heading("kills", text="PUNTUACIÓN")

        tree.column("posicion", width=100, anchor="center")
        tree.column("nombre", width=400, anchor="center")
        tree.column("kills", width=150, anchor="center")
        return tree

    def insertar_datos_top(tree, filepath):
        if not os.path.exists(filepath):
            tree.insert("", "end", values=("", "No hay datos", ""))
            return

        try:
            with open(filepath, 'r') as file:
                datos = []
                for linea in file:
                    if linea.strip():
                        try:
                            nombre, kills_str = linea.strip().split(',')
                            datos.append([nombre, int(kills_str)])
                        except ValueError:
                            continue 
                
                datos_ordenados = sorted(datos, key=lambda x: x[1], reverse=True)[:5]
                for i, (nombre, kills) in enumerate(datos_ordenados):
                    tree.insert("", "end", values=(i + 1, nombre, kills))
        except Exception:
            tree.insert("", "end", values=("", "Error al leer", ""))

    tree1 = crear_tabla(tables_frame, "Puntuaciones del Juego de Patrones", r"C:\Users\Usuario\Desktop\proyecto 2\Premios.txt")
    insertar_datos_top(tree1, r"C:\Users\Usuario\Desktop\proyecto 2\Premios.txt")

    root.mainloop()

class VentanaPremios:
    def __init__(self, root, gestor_premios):
        self.root = root
        self.gestor_premios = gestor_premios
        self.root.title("Tienda de Premios")
        self.root.geometry(tamaño_pantallas)
        self.root.configure(bg=color_fondo)
        self.configurar_ui()

    def configurar_ui(self):
        Label(self.root, text="Tienda de Premios", font=("Arial", 16, "bold"), bg=color_fondo).pack(pady=20)

        top_players_frame = Frame(self.root, bg=color_fondo)
        top_players_frame.pack(pady=10)

        Label(top_players_frame, text="Top Jugadores (Puntuaciones más altas):", font=("Arial", 12, "bold"), bg=color_fondo).pack()

        for i, (nombre, kills) in enumerate(self.gestor_premios.obtener_top_jugadores()):
            Label(top_players_frame, text=f"{i+1}. {nombre}: {kills}", font=("Arial", 10), bg=color_fondo).pack()

        Button(self.root, text="Volver", command=con_click(self.root.destroy), bg=color_boton, font=("Arial", 12)).pack(pady=10)

class GestorPremios:
    def __init__(self):
        self.archivo_premios = 'C:\\Users\\Usuario\\Desktop\\proyecto 2\\Premios.txt'
        self.premios = self.cargar_premios()

    def cargar_premios(self):
        if not os.path.exists(self.archivo_premios):
            return {}
        premios = {}
        with open(self.archivo_premios, 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 2:
                    nombre, kills_str = parts
                    try:
                        kills = int(kills_str)
                        premios[nombre] = kills
                    except ValueError:
                        print(f"Advertencia: Saltando línea inválida en Premios.txt: {line.strip()}")
        return premios

    def actualizar_premio(self, nombre, kills):
        guardar_en_txt(nombre, kills)
        self.premios = self.cargar_premios() 

    def obtener_top_jugadores(self, limit=5):
        sorted_players = sorted(self.premios.items(), key=lambda item: item[1], reverse=True)
        return sorted_players[:limit]
    
"""
============================================================================================================
Juego de parejas
============================================================================================================
"""

class Ficha:
    def __init__(self, ruta_imagen, id=None, visible=False, emparejada=False, ruta_imagen_oculta=None):
        self.id = id
        self.ruta_imagen = ruta_imagen
        self.ruta_imagen_oculta = ruta_imagen_oculta or os.path.join("imagenes", "dorso_carta.png")
        self.visible = visible
        self.emparejada = emparejada
        self._imagen_tk_visible = None
        self._imagen_tk_oculta = None
        self._referencias = []  # Mantiene referencias a las imágenes

    @property
    def imagen_tk_visible(self):
        if self._imagen_tk_visible is None:
            self.cargar_imagenes()
        return self._imagen_tk_visible

    @property
    def imagen_tk_oculta(self):
        if self._imagen_tk_oculta is None:
            self.cargar_imagenes()
        return self._imagen_tk_oculta

    def cargar_imagenes(self, tamano=(80, 100)):
        # Cargar imagen frontal
        try:
            img = PIL.Image.open(self.ruta_imagen)
            img = img.resize(tamano, PIL.Image.LANCZOS)
            self._imagen_tk_visible = ImageTk.PhotoImage(img)
            self._referencias.append(self._imagen_tk_visible)
        except Exception as e:
            print(f"Error cargando {self.ruta_imagen}: {e}")
            img = PIL.Image.new('RGB', tamano, 'blue')
            self._imagen_tk_visible = ImageTk.PhotoImage(img)
            self._referencias.append(self._imagen_tk_visible)

        # Cargar imagen oculta
        try:
            img = PIL.Image.open(self.ruta_imagen_oculta)
            img = img.resize(tamano, PIL.Image.LANCZOS)
            self._imagen_tk_oculta = ImageTk.PhotoImage(img)
            self._referencias.append(self._imagen_tk_oculta)
        except Exception as e:
            print(f"Error cargando {self.ruta_imagen_oculta}: {e}")
            img = PIL.Image.new('RGB', tamano, 'gray')
            self._imagen_tk_oculta = ImageTk.PhotoImage(img)
            self._referencias.append(self._imagen_tk_oculta)

class Tablero:
    def __init__(self, filas=6, columnas=6):
        self.filas = filas
        self.columnas = columnas
        self.matriz = [[None for _ in range(columnas)] for _ in range(filas)]

    def inicializar(self, fichas):
        fichas_barajadas = fichas.copy()
        random.shuffle(fichas_barajadas)
        indice = 0
        for i in range(self.filas):
            for j in range(self.columnas):
                self.matriz[i][j] = fichas_barajadas[indice]
                indice += 1

class Jugador:
    def __init__(self, nombre):
        self.nombre = nombre
        self.puntos = 0
        self.intentos = 0
        self.tablero = Tablero() 

    def incrementar_puntos(self):
        self.puntos += 1

    def incrementar_intentos(self):
        self.intentos += 1
    
    def get_intentos(self):
        return self.intentos

class Juego_Memoria:
    def __init__(self):
        self.jugadores = []
        self.tiempo_turno = 10
        self.tiempo_restante = 10
        self.turno_actual = 0
        self.fichas_base = []
        self.fichas_elegidas = []
        self.posiciones_elegidas = []

    def agregar_jugador(self, nombre):
        self.jugadores.append(Jugador(nombre))

    def crear_fichas_juego(self, num_pares, rutas_imagenes):
        self.fichas_base = []
        for id_ficha in range(num_pares):
            carta1 = Ficha(ruta_imagen=rutas_imagenes[id_ficha], id=id_ficha)
            carta2 = Ficha(ruta_imagen=rutas_imagenes[id_ficha], id=id_ficha)
            self.fichas_base.extend([carta1, carta2])

    def iniciar_juego(self, rutas_imagenes):
        self.crear_fichas_juego(18, rutas_imagenes)
        for jugador in self.jugadores:
            copia_fichas = [Ficha(f.ruta_imagen, f.id, f.visible, f.emparejada) for f in self.fichas_base]
            jugador.tablero.inicializar(copia_fichas)

    def cambiar_turno(self):
        self.turno_actual = (self.turno_actual + 1) % len(self.jugadores)
        self.fichas_elegidas = []
        self.posiciones_elegidas = []
        self.tiempo_restante = self.tiempo_turno

    def verificar_emparejamiento(self):
        if len(self.fichas_elegidas) == 2:
            return self.fichas_elegidas[0].id == self.fichas_elegidas[1].id
        return False

    def guardar_puntaje(self, nombre_jugador, intentos):
        try:
            with open(PUNTUACIONES_FILE, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([nombre_jugador, intentos, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        except Exception as e:
            print(f"Error al guardar el puntaje: {e}")

class InterfazJuego:
    def __init__(self, juego, usuario_logueado):
        self.juego = juego
        self.usuario_logueado = usuario_logueado
        self.ventana_juego = Tk()
        self.ventana_juego.title("Juego de Memoria")
        self.botones_cartas = []
        self.referencias_imagenes = []
        self.id_temporizador = None
        self.configurar_interfaz()

    def comprobar_victoria(self):
        total_pares = len(self.juego.fichas_base) // 2

        jugador_actual = self.juego.jugadores[self.juego.turno_actual]
        if jugador_actual.puntos == total_pares:
            self.mostrar_animacion_ganador(jugador_actual.nombre, jugador_actual.intentos)
            return True

        return False

    def mostrar_animacion_ganador(self, ganador, intentos_ganador):
        if self.id_temporizador:
            self.ventana_juego.after_cancel(self.id_temporizador)
        
        jugador_ganador_obj = None
        for jugador in self.juego.jugadores:
            if jugador.nombre == ganador:
                jugador_ganador_obj = jugador
                break

        if jugador_ganador_obj:
            self.juego.guardar_puntaje(ganador, jugador_ganador_obj.puntos)

        ventana_victoria = Toplevel(self.ventana_juego)
        ventana_victoria.title("¡Felicidades!")
        ventana_victoria.geometry(tamaño_pantallas)
        ventana_victoria.configure(bg="black")
        
        mensaje_ganador = f"¡{ganador} ha ganado en {intentos_ganador} intentos y con {jugador_ganador_obj.puntos} pares!" if len(self.juego.jugadores) > 1 else f"¡Has ganado en {intentos_ganador} intentos y con {jugador_ganador_obj.puntos} pares!"
        
        etiqueta_mensaje = Label(ventana_victoria, text=mensaje_ganador, font=("Arial", 24, "bold"),bg="black")
        etiqueta_mensaje.place(relx=0.5, rely=0.4, anchor=CENTER)
        colores_animacion = ["red", "yellow", "green", "blue", "purple", "orange", "white"]

        def animar_texto(contador=0):
            color = colores_animacion[contador % len(colores_animacion)]
            etiqueta_mensaje.config(fg=color)
            if ventana_victoria.winfo_exists():
                ventana_victoria.after(200, animar_texto, contador + 1)
        animar_texto()
        boton_cerrar = Button(ventana_victoria, text="Cerrar", command=lambda: [ventana_victoria.destroy(), self.ventana_juego.destroy()],font=("Arial", 14),bg="#34495e", fg="white")
        boton_cerrar.place(relx=0.5, rely=0.8, anchor=CENTER)

    def configurar_interfaz(self):
        self.ventana_juego.configure(bg=color_fondo)
        self.ventana_juego.minsize(width=800, height=600)
        self.marco_principal = Frame(self.ventana_juego, bg=color_fondo)
        self.marco_principal.pack(expand=True)
        self.marco_info = Frame(self.ventana_juego, bg=color_fondo, padx=10, pady=10)
        self.marco_info.pack(fill=X)
        self.etiqueta_jugador = Label(self.marco_info, text="", font=("Arial", 14), bg=color_fondo, fg="white")
        self.etiqueta_jugador.pack(side=LEFT)
        self.etiqueta_puntos_j1 = Label(self.marco_info, text="J1 Pares: 0", font=("Arial", 14), bg=color_fondo, fg="white")
        self.etiqueta_puntos_j1.pack(side=LEFT, padx=10)
        self.etiqueta_intentos_j1 = Label(self.marco_info, text="J1 Intentos: 0", font=("Arial", 14), bg=color_fondo, fg="white")
        self.etiqueta_intentos_j1.pack(side=LEFT, padx=10)

        self.etiqueta_puntos_j2 = Label(self.marco_info, text="J2 Pares: 0", font=("Arial", 14), bg=color_fondo, fg="white")
        self.etiqueta_puntos_j2.pack(side=RIGHT, padx=10)
        self.etiqueta_intentos_j2 = Label(self.marco_info, text="J2 Intentos: 0", font=("Arial", 14), bg=color_fondo, fg="white")
        self.etiqueta_intentos_j2.pack(side=RIGHT, padx=10)
        self.etiqueta_temporizador = Label(self.marco_info, text="Tiempo: 10s", font=("Arial", 14), bg=color_fondo, fg="white")
        self.etiqueta_temporizador.pack(side=RIGHT, padx=20)


    def mostrar_tablero(self, indice_jugador):
        jugador_actual = self.juego.jugadores[indice_jugador]
        
        self.botones_cartas = []
        self.referencias_imagenes = []
        self.etiqueta_jugador.config(text=f"Turno: {jugador_actual.nombre}")
        
        self.etiqueta_puntos_j1.config(text=f"{self.juego.jugadores[0].nombre} Pares: {self.juego.jugadores[0].puntos}")
        self.etiqueta_intentos_j1.config(text=f"{self.juego.jugadores[0].nombre} Intentos: {self.juego.jugadores[0].intentos}")
        self.etiqueta_puntos_j2.config(text=f"{self.juego.jugadores[1].nombre} Pares: {self.juego.jugadores[1].puntos}")
        self.etiqueta_intentos_j2.config(text=f"{self.juego.jugadores[1].nombre} Intentos: {self.juego.jugadores[1].intentos}")

        for widget in self.marco_principal.winfo_children():
            widget.destroy()
        
        for i in range(jugador_actual.tablero.filas):
            botones_fila = []
            for j in range(jugador_actual.tablero.columnas):
                ficha = jugador_actual.tablero.matriz[i][j]
                ficha.cargar_imagenes()
                self.referencias_imagenes.append(ficha.imagen_tk_visible)
                self.referencias_imagenes.append(ficha.imagen_tk_oculta)
                boton_carta = Button(self.marco_principal)
                if ficha.emparejada:
                    boton_carta.config(image=ficha.imagen_tk_visible, state=DISABLED)
                elif ficha.visible:
                    boton_carta.config(image=ficha.imagen_tk_visible)
                else:
                    boton_carta.config(image=ficha.imagen_tk_oculta)
                boton_carta.config(command=lambda x=i, y=j:self.clic_ficha(x, y), width=80, height=100, bg="#ffffff", relief=FLAT)
                boton_carta.grid(row=i, column=j, padx=5, pady=5)
                botones_fila.append(boton_carta)
            self.botones_cartas.append(botones_fila)
        self.iniciar_temporizador()

    def iniciar_temporizador(self):
        if self.id_temporizador:
            self.ventana_juego.after_cancel(self.id_temporizador)
        if self.juego.tiempo_restante < 0:
            self.juego.tiempo_restante = 0
        self.etiqueta_temporizador.config(text=f"Tiempo: {self.juego.tiempo_restante}s")
        if self.juego.tiempo_restante <= 0:
            self.tiempo_agotado()
        else:
            self.juego.tiempo_restante -= 1
            self.id_temporizador = self.ventana_juego.after(1000, self.iniciar_temporizador)

    def tiempo_agotado(self):
        self.ocultar_fichas_no_emparejadas()

    def clic_ficha(self, fila, columna):
        jugador_actual = self.juego.jugadores[self.juego.turno_actual]
        carta = jugador_actual.tablero.matriz[fila][columna]
        if carta.emparejada or carta.visible or len(self.juego.fichas_elegidas) >= 2:
            return
        carta.visible = True
        self.botones_cartas[fila][columna].config(image=carta.imagen_tk_visible)
        self.juego.fichas_elegidas.append(carta)
        self.juego.posiciones_elegidas.append((fila, columna))
        if len(self.juego.fichas_elegidas) == 2:
            jugador_actual.incrementar_intentos()
            
            if jugador_actual.nombre == self.juego.jugadores[0].nombre:
                self.etiqueta_intentos_j1.config(text=f"{jugador_actual.nombre} Intentos: {jugador_actual.intentos}")
            else:
                self.etiqueta_intentos_j2.config(text=f"{jugador_actual.nombre} Intentos: {jugador_actual.intentos}")

            if self.juego.verificar_emparejamiento():
                self.juego.tiempo_restante += 7
                self.etiqueta_temporizador.config(text=f"Tiempo: {self.juego.tiempo_restante}s")
                jugador_actual.incrementar_puntos()
                for f in self.juego.fichas_elegidas:
                    f.emparejada = True
                
                if jugador_actual.nombre == self.juego.jugadores[0].nombre:
                    self.etiqueta_puntos_j1.config(text=f"{jugador_actual.nombre} Pares: {jugador_actual.puntos}")
                else:
                    self.etiqueta_puntos_j2.config(text=f"{jugador_actual.nombre} Pares: {jugador_actual.puntos}")
                
                if self.comprobar_victoria():
                    cambio = obtener_cambio()
                    guardar_en_txt(usuario_logueado,int((1/jugador_actual.get_intentos())*100*cambio))
                    return
                self.juego.fichas_elegidas = []
                self.juego.posiciones_elegidas = []
            else:
                self.ventana_juego.after(1000, self.ocultar_fichas_no_emparejadas)

    def ocultar_fichas_no_emparejadas(self):
        jugador_actual = self.juego.jugadores[self.juego.turno_actual]
        for fila, columna in self.juego.posiciones_elegidas:
            ficha = jugador_actual.tablero.matriz[fila][columna]
            if not ficha.emparejada:
                ficha.visible = False
                self.botones_cartas[fila][columna].config(image=ficha.imagen_tk_oculta)
        self.juego.fichas_elegidas = []
        self.juego.posiciones_elegidas = []
        self.juego.cambiar_turno()
        self.mostrar_tablero(self.juego.turno_actual)

    def iniciar(self):
        self.mostrar_tablero(0)
        self.ventana_juego.mainloop()
"""
=================================================================================================
Juego de patrones
=================================================================================================
"""
class JuegoPatrones:
    def __init__(self, root):
        self.root = root
        self.root.title("Juego de Patrones")
        self.root.geometry(tamaño_pantallas)
        self.root.configure(bg=color_fondo)
        
        # Configuración del juego
        self.filas_patron = 4
        self.columnas_patron = 4
        self.total_cartas_patron = self.filas_patron * self.columnas_patron
        
        # Estado del juego
        self.patron = []
        self.secuencia_usuario = []
        self.nivel = 1
        self.puntuacion = 0
        self.juego_activo = False
        self.mostrando_patron = False
        self.puede_clicar = False
        
        # Temporizador
        self.tiempo_ultimo_clic = 0
        self.tiempo_inicio_turno = 0
        self.tiempo_restante = 0
        
        # Imágenes
        self._imagen_referencias = []  # Mantiene todas las referencias de imágenes
        self.ruta_base_imagenes = "imagenes"
        self.ruta_carta_oculta = os.path.join(self.ruta_base_imagenes, "dorso_carta.png")
        
        # Cargar imágenes antes de crear la UI
        self._cargar_imagenes_base()
        self.configurar_ui()

    def _cargar_imagenes_base(self):
        """Carga todas las imágenes necesarias al inicio"""
        # Imagen oculta
        try:
            img = PIL.Image.open(self.ruta_carta_oculta)
            img = img.resize((80, 100), PIL.Image.LANCZOS)
            self.imagen_carta_oculta = ImageTk.PhotoImage(img)
            self._imagen_referencias.append(self.imagen_carta_oculta)
        except Exception as e:
            print(f"Error cargando imagen oculta: {e}")
            img = PIL.Image.new('RGB', (80, 100), 'gray')
            self.imagen_carta_oculta = ImageTk.PhotoImage(img)
            self._imagen_referencias.append(self.imagen_carta_oculta)
        
        # Imágenes frontales
        self.todas_imagenes_frontales = []
        for i in range(18):  # Asumiendo 18 imágenes diferentes
            ruta = os.path.join(self.ruta_base_imagenes, f"imagen_{i+1}.png")
            try:
                img = PIL.Image.open(ruta)
                img = img.resize((80, 100), PIL.Image.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
                self.todas_imagenes_frontales.append(img_tk)
                self._imagen_referencias.append(img_tk)
            except Exception as e:
                print(f"Error cargando {ruta}: {e}")
                img = PIL.Image.new('RGB', (80, 100), 'purple')
                img_tk = ImageTk.PhotoImage(img)
                self.todas_imagenes_frontales.append(img_tk)
                self._imagen_referencias.append(img_tk)

    def configurar_ui(self):
        self.etiqueta_titulo = Label(self.root, text="Juego de Patrones", font=("Arial", 20, "bold"), bg=color_fondo, fg="white")
        self.etiqueta_titulo.pack(pady=20)
        self.etiqueta_puntuacion = Label(self.root, text=f"Puntuación: {self.puntuacion} | Nivel: {self.nivel}", font=("Arial", 14), bg=color_fondo, fg="white")
        self.etiqueta_puntuacion.pack(pady=10)
        self.marco_juego = Frame(self.root, bg=color_fondo)
        self.marco_juego.pack(pady=20, expand=True)
        self.botones_cartas = []
        id_boton = 0
        for r in range(self.filas_patron):
            botones_fila = []
            for c in range(self.columnas_patron):
                boton_carta = Button(self.marco_juego, image=self.imagen_carta_oculta,
                                   command=lambda id=id_boton: self.carta_clicada(id),
                                   width=80, height=100, bg="#ffffff", relief=FLAT, state=DISABLED)
                boton_carta.grid(row=r, column=c, padx=5, pady=5)
                botones_fila.append(boton_carta)
                id_boton += 1
            self.botones_cartas.extend(botones_fila)

        self.etiqueta_mensaje = Label(self.root, text="", font=("Arial", 12), bg=color_fondo, fg="yellow")
        self.etiqueta_mensaje.pack(pady=10)
        self.boton_inicio = Button(self.root, text="Iniciar Juego", command=con_click(self.iniciar_juego), font=("Arial", 14), bg=color_boton)
        self.boton_inicio.pack(pady=20)
        self.etiqueta_temporizador = Label(self.root, text="Tiempo: 12s", font=("Arial", 14), bg=color_fondo, fg="white")
        self.etiqueta_temporizador.pack(pady=10)
        Button(self.root, text="Volver", command=self.root.destroy, bg=color_boton, font=("Arial", 12)).pack(pady=10)

    def iniciar_juego(self):
        self.juego_activo = True
        self.nivel = 1
        self.puntuacion = 0
        self.secuencia_usuario = []
        self.actualizar_etiqueta_puntuacion()
        self.boton_inicio.config(state=DISABLED)
        self.generar_y_mostrar_patron()

    def generar_y_mostrar_patron(self):
        self.mostrando_patron = True
        self.puede_clicar = False
        longitud_patron = min(self.nivel + 2, self.total_cartas_patron)
        self.etiqueta_mensaje.config(text=f"Memoriza el patrón de {longitud_patron} casillas...", fg="yellow")
        self.patron = random.sample(range(self.total_cartas_patron), k=longitud_patron)
        self.secuencia_usuario = []
        
        for i in range(self.total_cartas_patron):
            self.botones_cartas[i].config(image=self.imagen_carta_oculta)
            self.botones_cartas[i].config(state=DISABLED)
            
        self.mostrar_paso_patron(0)

    def mostrar_paso_patron(self, index):
        if index < len(self.patron):
            id_carta = self.patron[index]
            imagen_a_mostrar = self.todas_imagenes_frontales[id_carta % len(self.todas_imagenes_frontales)]
            self.botones_cartas[id_carta].config(image=imagen_a_mostrar)
            self.root.after(1000, lambda: self.ocultar_carta_y_continuar(id_carta, index + 1))
        else:
            self.root.after(500, self.turno_usuario)

    def ocultar_carta_y_continuar(self, id_carta, siguiente_indice):
        self.botones_cartas[id_carta].config(image=self.imagen_carta_oculta)
        self.root.after(300, lambda: self.mostrar_paso_patron(siguiente_indice))

    def turno_usuario(self):
        self.mostrando_patron = False
        self.puede_clicar = True
        self.tiempo_inicio_turno = time.time()
        self.tiempo_ultimo_clic = self.tiempo_inicio_turno
        self.tiempo_restante = 12 
        self.actualizar_temporizador()
        self.etiqueta_mensaje.config(text=f"¡Ahora repite el patrón!", fg="green")
        for btn in self.botones_cartas:
            btn.config(state=NORMAL)

    def actualizar_temporizador(self):
        if self.puede_clicar and self.tiempo_restante > 0:
            self.etiqueta_temporizador.config(text=f"Tiempo: {self.tiempo_restante}s")
            self.tiempo_restante -= 1
            self.root.after(1000, self.actualizar_temporizador)
        elif self.tiempo_restante <= 0:
            self.etiqueta_temporizador.config(text="Tiempo: 0s")
            self.verificar_tiempo_excedido()

    def verificar_tiempo_excedido(self):
        if self.puede_clicar and len(self.secuencia_usuario) < len(self.patron):
            self.etiqueta_mensaje.config(text="¡Tiempo agotado! Juego terminado.", fg="red")
            self.finalizar_juego()


    def carta_clicada(self, id_carta):
        if not self.puede_clicar:
            return
        if efectos_de_sonido:
            reproducir_sonido("carta")
        tiempo_actual = time.time()
        tiempo_transcurrido = tiempo_actual - self.tiempo_inicio_turno
        tiempo_entre_clics = tiempo_actual - self.tiempo_ultimo_clic
        
        if len(self.secuencia_usuario) > 0 and tiempo_entre_clics > 2:
            self.etiqueta_mensaje.config(text="¡Demasiado lento entre clics! Juego terminado.", fg="red")
            self.finalizar_juego()
            return
            
        self.tiempo_ultimo_clic = tiempo_actual
        
        if id_carta in self.secuencia_usuario and self.secuencia_usuario.count(id_carta) == self.patron.count(id_carta):
            return
            
        self.secuencia_usuario.append(id_carta)
        imagen_a_mostrar = self.todas_imagenes_frontales[id_carta % len(self.todas_imagenes_frontales)]
        self.botones_cartas[id_carta].config(image=imagen_a_mostrar)
        
        if len(self.secuencia_usuario) == len(self.patron):
            self.puede_clicar = False
            self.root.after(500, self.comprobar_patron)

    def comprobar_patron(self):
        correcto = True
        if len(self.secuencia_usuario) != len(self.patron):
            correcto = False
        else:
            for i in range(len(self.patron)):
                if self.patron[i] != self.secuencia_usuario[i]:
                    correcto = False
                    break
                    
        if correcto:
            self.puntuacion += 10 * self.nivel
            self.nivel += 1
            self.actualizar_etiqueta_puntuacion()
            self.etiqueta_mensaje.config(text="¡Correcto! Siguiente nivel...", fg="blue")
            self.root.after(1000, self.reiniciar_cartas)
            self.root.after(1500, self.generar_y_mostrar_patron)
        else:
            self.etiqueta_mensaje.config(text="¡Incorrecto! Juego Terminado.", fg="red")
            self.finalizar_juego()

    def finalizar_juego(self):
        self.juego_activo = False
        self.puede_clicar = False
        self.etiqueta_temporizador.config(text="Tiempo: 0s")
        self.boton_inicio.config(state=NORMAL)
        self.etiqueta_mensaje.config(text=f"¡Juego terminado! Puntuación final: {self.puntuacion}", fg="red")
        self.root.after(1000, self.reiniciar_cartas)
        if hasattr(self, 'on_game_end_callback') and self.on_game_end_callback:
            self.on_game_end_callback(self.puntuacion)

    def reiniciar_cartas(self):
        for i in range(self.total_cartas_patron):
            self.botones_cartas[i].config(image=self.imagen_carta_oculta)
            self.botones_cartas[i].config(state=DISABLED)

    def actualizar_etiqueta_puntuacion(self):
        self.etiqueta_puntuacion.config(text=f"Puntuación: {self.puntuacion} | Nivel: {self.nivel}")

    @staticmethod
    def ejecutar(on_game_end=None):
        root = Tk()
        juego = JuegoPatrones(root)
        juego.on_game_end_callback = on_game_end
        root.mainloop()

"""
=======================================================================
Musica
=======================================================================
"""
def con_click(func):
    def wrapper():
        global sonido_botones
        if sonido_botones:
            reproducir_sonido("click")
        func()
    return wrapper

def reproducir_sonido(tipo):
    sound = None
    ruta = ""
    volumen = 0.5
    if tipo == "click":  
        ruta = r"C:\Users\Usuario\Desktop\proyecto\sonidos\mouse-click-331781.mp3"
    if tipo == "carta":  
        ruta = r"C:\Users\Usuario\Desktop\proyecto\sonidos\mouse-click-331781.mp3"
    sound = py.mixer.Sound(ruta)
    channel = py.mixer.find_channel(force=True) 
    if channel:
        channel.set_volume(volumen) 
        channel.play(sound)

def musica_lob():
    py.mixer.music.load(r"C:\Users\Usuario\Desktop\proyecto\sonidos\musica_3.mp3")
    py.mixer.music.set_volume(0.4) 
    py.mixer.music.play(-1, 0.0)

class ConfiguracionPantalla:
    def __init__(self, root):
        self.root = root
        self.root.title("Configuración de Sonido")
        self.root.geometry(tamaño_pantallas)
        self.root.configure(bg=color_fondo)
        
        self.musica_general_check = BooleanVar(value=True)
        self.sonido_botones_check = BooleanVar(value=True)
        self.efectos_sonido_check = BooleanVar(value=True)
        
        self.crear_interfaz()
    
    def crear_interfaz(self):
        marco_principal = Frame(self.root, bg= color_fondo, padx=20, pady=20)
        marco_principal.pack(expand=True, fill='both')
        
        titulo = Label(
            marco_principal, 
            text="Configuración de Sonido", 
            font=('Arial', 16, 'bold'), 
            bg=color_fondo,
            fg='#333333'
        )
        titulo.pack(pady=(0, 20))
        
        chk_musica = ttk.Checkbutton(
            marco_principal,
            text="Música General",
            variable=self.musica_general_check,
            style='Custom.TCheckbutton'
        )
        chk_musica.pack(pady=10, anchor='w')
        
        chk_botones = ttk.Checkbutton(
            marco_principal,
            text="Sonido de Botones",
            variable=self.sonido_botones_check,
            style='Custom.TCheckbutton'
        )
        chk_botones.pack(pady=10, anchor='w')
        
        chk_efectos = ttk.Checkbutton(
            marco_principal,
            text="Efectos de Sonido",
            variable=self.efectos_sonido_check,
            style='Custom.TCheckbutton'
        )
        chk_efectos.pack(pady=10, anchor='w')
        
        btn_volver = Button(
            marco_principal,
            text="Volver",
            command=con_click(self.volver),
            bg=color_boton,
            fg='white',
            font=('Arial', 12),
            padx=20,
            pady=5,
            relief='flat',
            bd=0
        )
        btn_volver.pack(pady=(30, 10), ipadx=10)
        
        estilo = ttk.Style()
        estilo.configure(
            'Custom.TCheckbutton',
            background='#f0f0f0',
            font=('Arial', 12),
            foreground='#333333'
        )
    
    def volver(self):
        global musica_general, sonido_botones, efectos_de_sonido
        print("Configuraciones guardadas:")
        print(f"Música General: {self.musica_general_check.get()}")
        print(f"Sonido Botones: {self.sonido_botones_check.get()}")
        print(f"Efectos Sonido: {self.efectos_sonido_check.get()}")

        if not self.musica_general_check.get():
            musica_general=False
        if not self.sonido_botones_check.get():
            sonido_botones = False
        if not self.efectos_sonido_check.get():
            efectos_de_sonido = False
        self.root.destroy()

"""
=======================================================================
Iniciar
======================================================================
"""
if __name__ == "__main__":
    app = AppAutenticacion()
    app.ejecutar()