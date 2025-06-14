from tkinter import *
from PIL import ImageTk
import PIL.Image
import cv2
import os
import random

class FaceDetector:
    def __init__(self):
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            if self.face_cascade.empty():
                raise IOError("No se pudo cargar el clasificador Haar Cascade.")
        except Exception as e:
            print(f"Error al cargar el clasificador: {e}")

    def detect_faces(self, image_path):
        if not os.path.exists(image_path):
            return None, "Imagen no encontrada"

        img = cv2.imread(image_path)
        if img is None:
            return None, "No se pudo leer la imagen"

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        results = [{'box': [x, y, w, h]} for (x, y, w, h) in faces]
        return results, img

class FaceRecognition:
    @staticmethod
    def save_face(image_path, results, filename):
        if not results:
            return False

        img = cv2.imread(image_path)
        if img is None:
            return False

        x1, y1, w, h = results[0]['box']
        face_img = img[y1:y1+h, x1:x1+w]
        face_img = cv2.resize(face_img, (150, 200), interpolation=cv2.INTER_CUBIC)
        cv2.imwrite(filename, face_img)
        return True

    @staticmethod
    def compare_faces(reg_path, log_path):
        orb = cv2.ORB_create()
        
        img1 = cv2.imread(reg_path, 0)
        img2 = cv2.imread(log_path, 0)
        
        if img1 is None or img2 is None:
            return 0

        kp1, desc1 = orb.detectAndCompute(img1, None)
        kp2, desc2 = orb.detectAndCompute(img2, None)
        
        if desc1 is None or desc2 is None:
            return 0

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(desc1, desc2)
        
        if not matches:
            return 0
            
        similar = [m for m in matches if m.distance < 70]

        if len(matches) == 0:
            return 0
        return len(similar) / len(matches)

class CameraManager:
    @staticmethod
    def capture_image(window_title, temp_filename):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None, "No se pudo abrir la cámara"

        captured = None
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            cv2.imshow(window_title, frame)

            if cv2.waitKey(1) == 27:
                captured = frame
                break
        
        cap.release()
        cv2.destroyAllWindows()

        if captured is None:
            return None, "Captura cancelada"

        cv2.imwrite(temp_filename, captured)
        return temp_filename, None

class FacialRegistration:
    def __init__(self, master):
        self.master = master
        master.title("Registro Facial")
        master.geometry("300x200")
        
        self.username = StringVar()
        self.setup_ui()

    def setup_ui(self):
        Label(self.master, text="Registro Facial", font=("Arial", 14)).pack(pady=10)
        Label(self.master, text="Ingrese su nombre de usuario:").pack()
        
        self.user_entry = Entry(self.master, textvariable=self.username)
        self.user_entry.pack(pady=5)
        
        Button(self.master, text="Capturar Rostro", command=self.register_face, bg= "#C2A78B").pack(pady=15)
        
        self.message_label = Label(self.master, text="", fg="red")
        self.message_label.pack()

    def register_face(self):
        username = self.username.get()
        if not username:
            self.show_message("Debe ingresar un nombre de usuario", "red")
            return

        temp_path = f"{username}_temp.jpg"
        img_path, error = CameraManager.capture_image("Registro Facial - Presiona ESC", temp_path)
        
        if error:
            self.show_message(error, "red")
            return

        detector = FaceDetector()
        results, _ = detector.detect_faces(img_path)
        
        if not results:
            self.show_message("No se detectó ningún rostro", "red")
            os.remove(img_path)
            return
        
        if FaceRecognition.save_face(img_path, results, f"{username}.jpg"):
            self.show_message("Registro exitoso!", "green")
            self.user_entry.delete(0, END)
        else:
            self.show_message("Error al registrar", "red")
        
        os.remove(img_path)

    def show_message(self, text, color):
        self.message_label.config(text=text, fg=color)

class FacialLogin:
    def __init__(self, master):
        self.master = master
        master.title("Login Facial")
        master.geometry("300x200")
        
        self.username = StringVar()
        self.setup_ui()

    def setup_ui(self):
        Label(self.master, text="Login Facial", font=("Arial", 14)).pack(pady=10)
        Label(self.master, text="Ingrese su nombre de usuario:").pack()
        
        self.user_entry = Entry(self.master, textvariable=self.username)
        self.user_entry.pack(pady=5)
        
        Button(self.master, text="Identificarse", command=self.authenticate, bg= "#C2A78B").pack(pady=15)
        
        self.message_label = Label(self.master, text="", fg="red")
        self.message_label.pack()

    def authenticate(self):
        username = self.username.get()
        if not username:
            self.show_message("Debe ingresar un nombre de usuario", "red")
            return

        registered_face_path = f"{username}.jpg"
        if not os.path.exists(registered_face_path):
            self.show_message("Usuario no registrado", "red")
            return

        temp_path = f"{username}_login_temp.jpg"
        img_path, error = CameraManager.capture_image("Login Facial - Presiona ESC", temp_path)
        
        if error:
            self.show_message(error, "red")
            return

        detector = FaceDetector()
        results, _ = detector.detect_faces(img_path)
        
        if not results:
            self.show_message("No se detectó ningún rostro", "red")
            os.remove(img_path)
            return
        
        login_img_path = f"{username}_login.jpg"
        if not FaceRecognition.save_face(img_path, results, login_img_path):
            self.show_message("Error en autenticación", "red")
            os.remove(img_path)
            return
        
        os.remove(img_path)

        similarity = FaceRecognition.compare_faces(registered_face_path, login_img_path)
        os.remove(login_img_path)

        if similarity >= 0.70:
            self.show_message(f"Bienvenido {username}!", "green")
            print(f"Compatibilidad: {similarity:.2f}")
            global login_successful
            login_successful = True
            self.master.destroy()
        else:
            self.show_message("Autenticación fallida", "red")
            print(f"Compatibilidad: {similarity:.2f}")
            self.user_entry.delete(0, END)

    def show_message(self, text, color):
        self.message_label.config(text=text, fg=color)

login_successful = False

class AuthApp:
    def __init__(self):
        self.root = Tk()
        self.root.title("Sistema de Autenticación Facial")
        self.root.geometry("400x300")
        
        self.setup_ui()

    def setup_ui(self):
        Label(self.root, text="Autenticación Facial", font=("Arial", 16)).pack(pady=30)
        
        Button(self.root, text="Registrarse", height=2, width=20,
               command=self.open_registration, bg= "#C2A78B").pack(pady=10)
        
        Button(self.root, text="Iniciar Sesión", height=2, width=20,
               command=self.open_login, bg= "#C2A78B").pack(pady=10)

    def open_registration(self):
        reg_window = Toplevel(self.root)
        FacialRegistration(reg_window)

    def open_login(self):
        login_window = Toplevel(self.root)
        FacialLogin(login_window)
        self.root.wait_window(login_window)
        
        if login_successful:
            self.root.destroy()
            mostrar_pantalla_intermedia()
            
    def run(self):
        self.root.mainloop()

def mostrar_pantalla_intermedia():
    inter_root = Tk()
    inter_root.title("Acceso Concedido")
    inter_root.geometry("800x400")
    inter_root.configure(bg="#9BC1BC")

    def iniciar_juego_directamente():
        inter_root.destroy()
        iniciar_cartas.main2()

    Label(inter_root, text="¡Login Exitoso!", font=("Arial", 18, "bold"), bg="#9BC1BC").pack(pady=30)
    Button(inter_root, text="Continuar al Juego de Cartas", command=iniciar_juego_directamente, height=2, width=25, font=("Arial", 12), bg= "#C2A78B").pack(pady=20)
    Button(inter_root, text="Continuar al Juego de Patrones", command=None, height=2, width=25, font=("Arial", 12), bg= "#C2A78B").pack(pady=20)
    Button(inter_root, text="Continuar a la tienda", command=None, height=2, width=25, font=("Arial", 12), bg= "#C2A78B").pack(pady=20)
    inter_root.mainloop()

class Ficha:
    def __init__(self, imagen_path, id=None, visible=False, emparejada=False, imagen_oculta_path=r"imagenes\dorso_carta.png"):
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
                img = PIL.Image.open(self.imagen_path)
                img = img.resize(size, PIL.Image.LANCZOS)
                self.imagen_tk = ImageTk.PhotoImage(img)
            
            if os.path.exists(self.imagen_oculta_path):
                img_oculta = PIL.Image.open(self.imagen_oculta_path)
                img_oculta = img_oculta.resize(size, PIL.Image.LANCZOS)
                self.imagen_oculta_tk = ImageTk.PhotoImage(img_oculta)
        except Exception as e:
            print(f"Error al cargar imágenes: {e}. Ruta: {self.imagen_path}")

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
        self.tiempo_turno = 10
        self.tiempo_restante = 10
        self.turno_actual = 0
        self.fichas_maestras = []
        self.fichas_seleccionadas = []
        self.posiciones_seleccionadas = []
        
    def agregar_jugador(self, nombre):
        self.jugadores.append(Jugador(nombre))
        
    def crear_fichas(self, cantidad_pares, imagenes_paths):
        self.fichas_maestras = []
        for id_ficha in range(cantidad_pares):
            ficha1 = Ficha(imagen_path=imagenes_paths[id_ficha], id=id_ficha)
            ficha2 = Ficha(imagen_path=imagenes_paths[id_ficha], id=id_ficha)
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
        self.tiempo_restante = self.tiempo_turno
        
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
        self.temporizador_id = None
        self.configurar_interfaz()
    
    def verificar_victoria(self):
        jugador_actual = self.juego.jugadores[self.juego.turno_actual]
        total_pares = len(self.juego.fichas_maestras) // 2
        
        if jugador_actual.puntos == total_pares:
            self.mostrar_animacion_ganador(jugador_actual.nombre)
            return True
        return False
    
    def mostrar_animacion_ganador(self, nombre_ganador):
        if self.temporizador_id:
            self.root.after_cancel(self.temporizador_id)
        
        ventana_ganador = Toplevel(self.root)
        ventana_ganador.title("¡Felicidades!")
        ventana_ganador.geometry("600x400")
        ventana_ganador.configure(bg="black")
        
        mensaje = Label(ventana_ganador, text=f"¡{nombre_ganador} ha ganado!", font=("Arial", 24, "bold"),bg="black")
        mensaje.place(relx=0.5, rely=0.4, anchor=CENTER)
        
        colores = ["red", "yellow", "green", "blue", "purple", "orange", "white"]
        
        def animar_mensaje(contador=0):
            color = colores[contador % len(colores)]
            mensaje.config(fg=color)
            if ventana_ganador.winfo_exists():
                ventana_ganador.after(200, animar_mensaje, contador + 1)
        
        animar_mensaje()
        
        btn_cerrar = Button(ventana_ganador, text="Cerrar", command=ventana_ganador.destroy,font=("Arial", 14),bg="#34495e", fg="white")
        btn_cerrar.place(relx=0.5, rely=0.8, anchor=CENTER)
        
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
        
        self.lbl_temporizador = Label(self.info_frame, text="Tiempo: 10s", font=("Arial", 14), bg="#34495e", fg="white")
        self.lbl_temporizador.pack(side=RIGHT, padx=20)
                
    def mostrar_tablero(self, jugador_idx):
        jugador = self.juego.jugadores[jugador_idx]
        self.botones = []
        self.imagenes_referencias = []
        
        self.lbl_jugador.config(text=f"Turno: {jugador.nombre}")
        self.lbl_puntos.config(text=f"Puntos: {jugador.puntos}")
        
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        for i in range(jugador.tablero.filas):
            fila_botones = []
            for j in range(jugador.tablero.columnas):
                ficha = jugador.tablero.matriz[i][j]
                ficha.cargar_imagenes()
                self.imagenes_referencias.append(ficha.imagen_tk)
                self.imagenes_referencias.append(ficha.imagen_oculta_tk)
                
                btn = Button(self.main_frame)
                
                if ficha.emparejada:
                    btn.config(image=ficha.imagen_tk, state=DISABLED)
                elif ficha.visible:
                    btn.config(image=ficha.imagen_tk)
                else:
                    btn.config(image=ficha.imagen_oculta_tk)
                
                btn.config(command=lambda x=i, y=j: self.clic_ficha(x, y), width=80, height=100, bg="#ffffff", relief=FLAT)
                btn.grid(row=i, column=j, padx=5, pady=5)
                fila_botones.append(btn)
            self.botones.append(fila_botones)
        
        self.iniciar_temporizador()

    def iniciar_temporizador(self):
        if self.temporizador_id:
            self.root.after_cancel(self.temporizador_id)
        
        if self.juego.tiempo_restante < 0:
             self.juego.tiempo_restante = 0
             
        self.lbl_temporizador.config(text=f"Tiempo: {self.juego.tiempo_restante}s")
        
        if self.juego.tiempo_restante <= 0:
            self.tiempo_agotado()
        else:
            self.juego.tiempo_restante -= 1
            self.temporizador_id = self.root.after(1000, self.iniciar_temporizador)
    
    def tiempo_agotado(self):
        self.ocultar_fichas_no_emparejadas()
    
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
                self.juego.tiempo_restante += 7
                self.lbl_temporizador.config(text=f"Tiempo: {self.juego.tiempo_restante}s")
                
                jugador_actual.incrementar_puntos()
                for f in self.juego.fichas_seleccionadas:
                    f.emparejada = True
                
                self.lbl_puntos.config(text=f"Puntos: {jugador_actual.puntos}")
                
                if self.verificar_victoria():
                    return
                
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
        self.mostrar_tablero(0)
        self.root.mainloop()

class iniciar_cartas:
    @staticmethod
    def main2():
        try:
            ruta_imagenes = "C:\\Users\\Usuario\\Desktop\\proyecto 2\\imagenes"
            imagenes_paths = [os.path.join(ruta_imagenes, f"imagen_{i+1}.png") for i in range(18)]
            
            juego = Juego_Memoria()
            juego.agregar_jugador("Jugador 1")
            juego.agregar_jugador("Jugador 2")
            juego.iniciar_juego(imagenes_paths)
            
            interfaz = InterfazJuego(juego)
            interfaz.iniciar()
        except Exception as e:
            print(f"No se pudo iniciar el juego. Error: {e}")
            print("Verifica que las rutas de las imágenes sean correctas.")

if __name__ == "__main__":
    app = AuthApp()
    app.run()