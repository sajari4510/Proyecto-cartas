from tkinter import *
from PIL import Image, ImageTk
import random
import time
import os

class Ficha:
    def __init__(self, imagen_path, id=None, visible=False, emparejada=False, imagen_oculta_path=r"C:\Users\Usuario\Desktop\proyecto 2\imagenes\dorso_carta.png"):
        self.id = id
        self.imagen_path = imagen_path 
        self.imagen_oculta_path = imagen_oculta_path  
        self.visible = visible  
        self.emparejada = emparejada 
        self.imagen_tk = None 
        self.imagen_oculta_tk = None 

    def cargar_imagenes(self, size=(80, 100)):
        try:
            if os.path.exists(self.imagen_path):
                img = Image.open(self.imagen_path)
                img = img.resize(size, Image.LANCZOS)
                self.imagen_tk = ImageTk.PhotoImage(img)
            
            if os.path.exists(self.imagen_oculta_path):
                img_oculta = Image.open(self.imagen_oculta_path)
                img_oculta = img_oculta.resize(size, Image.LANCZOS)
                self.imagen_oculta_tk = ImageTk.PhotoImage(img_oculta)
        except Exception as e:
            print(f"Error al cargar imágenes: {e}")

class Tablero:
    def __init__(self, filas=6, columnas=6):
        self.filas = filas
        self.columnas = columnas
        self.matriz = [[None for _ in range(columnas)] for _ in range(filas)]
        
    def inicializar(self, fichas):
        fichas_mezcladas = fichas.copy()
        random.shuffle(fichas_mezcladas)
        
        index = 0
        for i in range(self.filas):
            for j in range(self.columnas):
                self.matriz[i][j] = fichas_mezcladas[index]
                index += 1

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

class Juego_Memoria:
    def __init__(self):
        self.jugadores = []
        self.tiempo_turno = 10000000
        self.turno_actual = 0
        self.fichas_maestras = []  
        self.fichas_seleccionadas = []  
        self.posiciones_seleccionadas = []  
        
    def agregar_jugador(self, nombre):
        self.jugadores.append(Jugador(nombre))
        
    def crear_fichas(self, cantidad_pares, imagenes_paths):
        self.fichas_maestras = []
        if len(imagenes_paths) < cantidad_pares:
            raise ValueError("No hay suficientes rutas de imágenes para los pares requeridos")
            
        for id in range(cantidad_pares):
            ficha1 = Ficha(imagen_path=imagenes_paths[id], id=id)
            ficha2 = Ficha(imagen_path=imagenes_paths[id], id=id)
            self.fichas_maestras.extend([ficha1, ficha2])
    
    def iniciar_juego(self, imagenes_paths):
        self.crear_fichas(18, imagenes_paths)
        
        for jugador in self.jugadores:
            fichas_copia = [Ficha(f.imagen_path, f.id, f.visible, f.emparejada) for f in self.fichas_maestras]
            jugador.tablero.inicializar(fichas_copia)

    def cambiar_turno(self):
        self.turno_actual = (self.turno_actual + 1) % len(self.jugadores)
        self.fichas_seleccionadas = []
        self.posiciones_seleccionadas = []
        
    def verificar_emparejamiento(self):
        if len(self.fichas_seleccionadas) == 2:
            return self.fichas_seleccionadas[0].id == self.fichas_seleccionadas[1].id
        return False

class InterfazJuego:
    def __init__(self, juego):
        self.juego = juego
        self.root = Tk()
        self.root.title("Juego de Memoria")
        self.botones = []
        self.imagenes_referencias = []  
        self.configurar_interfaz()
        
    def configurar_interfaz(self):
        self.root.configure(bg="#2c3e50")
        self.root.minsize(width=800, height=600)
        self.main_frame = Frame(self.root, bg="#2c3e50")
        self.main_frame.pack(expand=True)
        
        self.info_frame = Frame(self.root, bg="#34495e", padx=10, pady=10)
        self.info_frame.pack(fill=X)
        
        self.lbl_jugador = Label(self.info_frame, text="", font=("Arial", 14), bg="#34495e", fg="white")
        self.lbl_jugador.pack(side=LEFT)
        
        self.lbl_puntos = Label(self.info_frame, text="Puntos: 0", font=("Arial", 14), bg="#34495e", fg="white")
        self.lbl_puntos.pack(side=RIGHT)
                
    def mostrar_tablero(self, jugador_idx):
        jugador = self.juego.jugadores[jugador_idx]
        self.botones = []
        self.imagenes_referencias = []  
        
        self.lbl_jugador.config(text=f"Turno: {jugador.nombre}")
        self.lbl_puntos.config(text=f"Puntos: {jugador.puntos}")
        
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        for i in range(jugador.tablero.filas):
            for j in range(jugador.tablero.columnas):
                ficha = jugador.tablero.matriz[i][j]
                ficha.cargar_imagenes()
                self.imagenes_referencias.append(ficha.imagen_tk)
                self.imagenes_referencias.append(ficha.imagen_oculta_tk)
        
        for i in range(jugador.tablero.filas):
            fila_botones = []
            for j in range(jugador.tablero.columnas):
                ficha = jugador.tablero.matriz[i][j]
                btn = Button(self.main_frame)
                
                if ficha.emparejada:
                    btn.config(image=ficha.imagen_tk, state=DISABLED)
                elif ficha.visible:
                    btn.config(image=ficha.imagen_tk)
                else:
                    btn.config(image=ficha.imagen_oculta_tk)
                
                btn.config(
                    command=lambda x=i, y=j: self.clic_ficha(x, y),
                    width=80, 
                    height=100,
                    bg="#ffffff",
                    relief=FLAT
                )
                btn.grid(row=i, column=j, padx=5, pady=5)
                fila_botones.append(btn)
            self.botones.append(fila_botones)

    def clic_ficha(self, fila, columna):
        jugador_actual = self.juego.jugadores[self.juego.turno_actual]
        ficha = jugador_actual.tablero.matriz[fila][columna]
        
        if ficha.emparejada or ficha.visible or len(self.juego.fichas_seleccionadas) >= 2:
            return
            
        ficha.visible = True
        self.botones[fila][columna].config(image=ficha.imagen_tk)
        self.juego.fichas_seleccionadas.append(ficha)
        self.juego.posiciones_seleccionadas.append((fila, columna))

        if len(self.juego.fichas_seleccionadas) == 2:
            jugador_actual.incrementar_intentos()
            
            if self.juego.verificar_emparejamiento():
                jugador_actual.incrementar_puntos()
                for f in self.juego.fichas_seleccionadas:
                    f.emparejada = True
                
                self.lbl_puntos.config(text=f"Puntos: {jugador_actual.puntos}")
                
                self.juego.fichas_seleccionadas = []
                self.juego.posiciones_seleccionadas = []
            else:
                self.root.after(1000, self.ocultar_fichas_no_emparejadas)
    
    def ocultar_fichas_no_emparejadas(self):
        jugador_actual = self.juego.jugadores[self.juego.turno_actual]
        
        for fila, col in self.juego.posiciones_seleccionadas:
            ficha = jugador_actual.tablero.matriz[fila][col]
            if not ficha.emparejada:
                ficha.visible = False
                self.botones[fila][col].config(image=ficha.imagen_oculta_tk)
        
        self.juego.fichas_seleccionadas = []
        self.juego.posiciones_seleccionadas = []
        self.juego.cambiar_turno()
        
        self.mostrar_tablero(self.juego.turno_actual)
        
    def iniciar(self):
        self.debug()
        self.mostrar_tablero(0)
        self.root.mainloop()
    
    def debug(self):
        print("\n=== DEBUG - MATRICES DE CARTAS ===")
        
        for i, jugador in enumerate(self.juego.jugadores, 1):
            print(f"\nJugador {i} ({jugador.nombre}):")
            print(f"Puntos: {jugador.puntos} - Intentos: {jugador.intentos}")
            
            print("    " + " ".join(f"{col:4}" for col in range(jugador.tablero.columnas)))
            print("  +" + "----" * jugador.tablero.columnas + "+")
            
            for fila in range(jugador.tablero.filas):
                print(f"{fila:2}|", end=" ")
                for col in range(jugador.tablero.columnas):
                    ficha = jugador.tablero.matriz[fila][col]
                    estado = ""
                    if ficha.emparejada:
                        estado = "*"
                    print(f"{ficha.id:2}{estado:1}", end="  ")
                print("|")
            
            print("  +" + "----" * jugador.tablero.columnas + "+")
            print("   * = carta emparejada")
        
            print("\n=== FIN DEBUG ===\n")

def main():
    imagenes_paths = [f"C:\\Users\\Usuario\\Desktop\\proyecto 2\\imagenes\\imagen_{i+1}.png" for i in range(18)]
    
    juego = Juego_Memoria()
    juego.agregar_jugador("Jugador 1")
    juego.agregar_jugador("Jugador 2")
    juego.iniciar_juego(imagenes_paths)
        
    interfaz = InterfazJuego(juego)
    interfaz.iniciar()

main()