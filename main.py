"""
Aplicación de Reconocimiento de Números con Cámara y Árbol AVL
Interfaz gráfica con Tkinter
Usa EasyOCR para reconocimiento de números manuscritos
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import cv2
from PIL import Image, ImageTk
import threading
from avl_tree import ArbolAVL
from ocr_processor import OCRProcessor

# -------------------------------------------------------------------
#  Ventana para visualizar el árbol AVL
# -------------------------------------------------------------------
class VentanaArbol(tk.Toplevel):
    """Ventana que dibuja el árbol AVL en un canvas con scroll."""
    def __init__(self, parent, arbol_avl):
        super().__init__(parent)
        self.parent = parent
        self.arbol_avl = arbol_avl
        self.title("Arbol AVL - Visualizacion")
        self.geometry("800x600")
        self.resizable(True, True)

        # Configurar cierre de la ventana
        self.protocol("WM_DELETE_WINDOW", self.cerrar)

        # Frame para canvas con scrollbars
        frame_canvas = tk.Frame(self)
        frame_canvas.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        self.scroll_y = tk.Scrollbar(frame_canvas, orient=tk.VERTICAL)
        self.scroll_x = tk.Scrollbar(frame_canvas, orient=tk.HORIZONTAL)

        self.canvas = tk.Canvas(
            frame_canvas,
            bg='white',
            yscrollcommand=self.scroll_y.set,
            xscrollcommand=self.scroll_x.set
        )
        self.scroll_y.config(command=self.canvas.yview)
        self.scroll_x.config(command=self.canvas.xview)

        # Empaquetado
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Espaciado del dibujo
        self.h_spacing = 80      # espacio horizontal entre nodos consecutivos
        self.v_spacing = 80      # espacio vertical entre niveles
        self.margin = 40         # margen alrededor

        # Diccionario para guardar posiciones de los nodos
        self.posiciones = {}
        self.radio = 20          # radio del círculo de cada nodo

        # Dibujar el árbol actual al iniciar
        self.dibujar()

    def cerrar(self):
        """Al cerrar la ventana, informar a la aplicación principal."""
        self.parent.ventana_arbol = None
        self.destroy()

    def dibujar(self):
        """Borra el canvas y vuelve a dibujar todo el árbol."""
        self.canvas.delete("all")
        self.posiciones.clear()

        if self.arbol_avl.raiz is None:
            # Árbol vacío: mostrar mensaje
            self.canvas.create_text(
                400, 300, text="Arbol vacio", font=('Arial', 16), fill='gray'
            )
            self.canvas.config(scrollregion=(0, 0, 800, 600))
            return

        # Paso 1: asignar coordenadas lógicas (índice inorden, profundidad)
        self._asignar_ranks(self.arbol_avl.raiz, 0, [0])

        # Paso 2: convertir ranks a píxeles
        coords_pix = {}
        for id_nodo, (rank, profundidad) in self.posiciones.items():
            x = self.margin + rank * self.h_spacing
            y = self.margin + profundidad * self.v_spacing
            coords_pix[id_nodo] = (x, y)

        # Paso 3: dibujar aristas (líneas) y nodos (círculos + texto)
        self._dibujar_arbol(self.arbol_avl.raiz, coords_pix)

        # Paso 4: ajustar el scrollregion al contenido dibujado
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox(tk.ALL)
        if bbox:
            x1, y1, x2, y2 = bbox
            # Añadir un pequeño margen extra
            self.canvas.config(scrollregion=(x1-20, y1-20, x2+20, y2+20))
        else:
            self.canvas.config(scrollregion=(0, 0, 800, 600))

    def _asignar_ranks(self, nodo, profundidad, rank_counter):
        """Recorrido inorden para asignar un número de orden (rank) a cada nodo."""
        if nodo is None:
            return
        self._asignar_ranks(nodo.izquierda, profundidad + 1, rank_counter)
        # Guardar (rank, profundidad) usando la identidad del nodo como clave
        self.posiciones[id(nodo)] = (rank_counter[0], profundidad)
        rank_counter[0] += 1
        self._asignar_ranks(nodo.derecha, profundidad + 1, rank_counter)

    def _dibujar_arbol(self, nodo, coords):
        """Dibuja recursivamente líneas y círculos."""
        if nodo is None:
            return

        x, y = coords[id(nodo)]

        # Dibujar línea a hijo izquierdo
        if nodo.izquierda is not None:
            x_hijo, y_hijo = coords[id(nodo.izquierda)]
            self.canvas.create_line(x, y, x_hijo, y_hijo, fill='black', width=2)

        # Dibujar línea a hijo derecho
        if nodo.derecha is not None:
            x_hijo, y_hijo = coords[id(nodo.derecha)]
            self.canvas.create_line(x, y, x_hijo, y_hijo, fill='black', width=2)

        # Dibujar el círculo del nodo
        self.canvas.create_oval(
            x - self.radio, y - self.radio,
            x + self.radio, y + self.radio,
            fill='#2c3e50', outline='#1a252f', width=2
        )
        # Texto con el valor
        self.canvas.create_text(
            x, y, text=str(nodo.valor), font=('Arial', 12, 'bold'), fill='white'
        )

        # Dibujar hijos recursivamente
        self._dibujar_arbol(nodo.izquierda, coords)
        self._dibujar_arbol(nodo.derecha, coords)


# -------------------------------------------------------------------
#  CLASE PRINCIPAL DE LA APLICACIÓN (estética modificada)
# -------------------------------------------------------------------
class AplicacionOCRAVL:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Reconocimiento de Numeros - Arbol AVL (EasyOCR)")
        self.ventana.geometry("1200x700")
        self.ventana.configure(bg='#2c3e50')

        # Inicializar componentes
        self.arbol_avl = ArbolAVL()
        self.ocr_processor = OCRProcessor()
        self.camara = None
        self.camara_activa = False
        self.ultimo_numero = None
        self.ultima_confianza = 0.0
        self.modelo_cargado = False
        self.ultimo_frame = None

        # Atributo para la ventana de visualización del árbol
        self.ventana_arbol = None

        # Crear interfaz
        self.crear_interfaz()

        # Configurar cierre de ventana
        self.ventana.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)

    def crear_interfaz(self):
        """Crea todos los componentes de la interfaz"""

        # Frame principal dividido en 2 columnas
        frame_izquierdo = tk.Frame(self.ventana, bg='#34495e', width=700)
        frame_izquierdo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        frame_derecho = tk.Frame(self.ventana, bg='#34495e', width=500)
        frame_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ===== PANEL IZQUIERDO: CÁMARA Y CONTROLES =====

        # Título
        titulo_cam = tk.Label(
            frame_izquierdo,
            text="Captura de Numeros (EasyOCR)",
            font=('Arial', 16, 'bold'),
            bg='#34495e',
            fg='#ecf0f1'
        )
        titulo_cam.pack(pady=10)

        # Área de video
        self.label_video = tk.Label(frame_izquierdo, bg='black')
        self.label_video.pack(pady=10, padx=10)

        # Frame para imagen procesada
        frame_procesada = tk.Frame(frame_izquierdo, bg='#34495e')
        frame_procesada.pack(pady=10)

        tk.Label(
            frame_procesada,
            text="Imagen Procesada:",
            font=('Arial', 10),
            bg='#34495e',
            fg='#ecf0f1'
        ).pack()

        self.label_procesada = tk.Label(frame_procesada, bg='black')
        self.label_procesada.pack()

        # Número detectado con confianza
        self.label_numero_detectado = tk.Label(
            frame_izquierdo,
            text="Numero detectado: --",
            font=('Arial', 14, 'bold'),
            bg='#34495e',
            fg='#3498db'
        )
        self.label_numero_detectado.pack(pady=5)

        self.label_confianza = tk.Label(
            frame_izquierdo,
            text="Confianza: --%",
            font=('Arial', 10),
            bg='#34495e',
            fg='#bdc3c7'
        )
        self.label_confianza.pack(pady=2)

        # Label de estado
        self.label_estado = tk.Label(
            frame_izquierdo,
            text="",
            font=('Arial', 10, 'italic'),
            bg='#34495e',
            fg='#f39c12'
        )
        self.label_estado.pack(pady=5)

        # Botones de control
        frame_botones = tk.Frame(frame_izquierdo, bg='#34495e')
        frame_botones.pack(pady=10)

        # Estilo común de botones (paleta uniforme)
        btn_estilo = {
            'font': ('Arial', 12, 'bold'),
            'fg': 'white',
            'width': 15,
            'height': 2,
            'cursor': 'hand2',
            'bg': '#2c3e50',        # azul muy oscuro
            'activebackground': '#1a252f',
            'activeforeground': 'white',
            'borderwidth': 0
        }
        btn_estilo_ancho = {**btn_estilo, 'width': 18}

        self.btn_iniciar = tk.Button(
            frame_botones,
            text="Iniciar Camara",
            command=self.iniciar_camara,
            **btn_estilo
        )
        self.btn_iniciar.grid(row=0, column=0, padx=5)

        self.btn_capturar = tk.Button(
            frame_botones,
            text="Capturar e Insertar",
            command=self.capturar_e_insertar,
            **btn_estilo_ancho,
            state=tk.DISABLED
        )
        self.btn_capturar.grid(row=0, column=1, padx=5)

        self.btn_detener = tk.Button(
            frame_botones,
            text="Detener Camara",
            command=self.detener_camara,
            **btn_estilo,
            state=tk.DISABLED
        )
        self.btn_detener.grid(row=1, column=0, padx=5, pady=5)

        self.btn_limpiar = tk.Button(
            frame_botones,
            text="Limpiar Arbol",
            command=self.limpiar_arbol,
            **btn_estilo_ancho
        )
        self.btn_limpiar.grid(row=1, column=1, padx=5, pady=5)

        # Estilo sin ancho para el botón ancho
        btn_ver_arbol_style = {k: v for k, v in btn_estilo.items() if k != 'width'}
        self.btn_ver_arbol = tk.Button(
            frame_botones,
            text="Mostrar Arbol",
            command=self.abrir_ventana_arbol,
            width=33,  # Ocupa dos columnas
            **btn_ver_arbol_style
        )

        self.btn_ver_arbol.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky='ew')

        # ===== PANEL DERECHO: RECORRIDOS DEL ÁRBOL =====

        # Título
        titulo_arbol = tk.Label(
            frame_derecho,
            text="Arbol AVL - Recorridos",
            font=('Arial', 16, 'bold'),
            bg='#34495e',
            fg='#ecf0f1'
        )
        titulo_arbol.pack(pady=10)

        # Información del árbol
        frame_info = tk.Frame(frame_derecho, bg='#2c3e50', relief=tk.RIDGE, borderwidth=2)
        frame_info.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Cantidad de nodos
        self.label_cantidad = tk.Label(
            frame_info,
            text="Numeros en arbol: 0",
            font=('Arial', 14, 'bold'),
            bg='#2c3e50',
            fg='#ecf0f1'
        )
        self.label_cantidad.pack(pady=15)

        # Separador
        tk.Frame(frame_info, height=2, bg='#7f8c8d').pack(fill=tk.X, padx=20, pady=10)

        # Recorrido InOrden
        tk.Label(
            frame_info,
            text="Recorrido InOrden (ordenado):",
            font=('Arial', 12, 'bold'),
            bg='#2c3e50',
            fg='#3498db'
        ).pack(pady=5)

        self.text_inorden = scrolledtext.ScrolledText(
            frame_info,
            height=5,
            font=('Courier', 11),
            bg='#ecf0f1',
            fg='#2c3e50',
            wrap=tk.WORD
        )
        self.text_inorden.pack(fill=tk.X, padx=20, pady=5)

        # Recorrido PreOrden
        tk.Label(
            frame_info,
            text="Recorrido PreOrden:",
            font=('Arial', 12, 'bold'),
            bg='#2c3e50',
            fg='#e74c3c'
        ).pack(pady=5)

        self.text_preorden = scrolledtext.ScrolledText(
            frame_info,
            height=5,
            font=('Courier', 11),
            bg='#ecf0f1',
            fg='#2c3e50',
            wrap=tk.WORD
        )
        self.text_preorden.pack(fill=tk.X, padx=20, pady=5)

        # Recorrido PostOrden
        tk.Label(
            frame_info,
            text="Recorrido PostOrden:",
            font=('Arial', 12, 'bold'),
            bg='#2c3e50',
            fg='#27ae60'
        ).pack(pady=5)

        self.text_postorden = scrolledtext.ScrolledText(
            frame_info,
            height=5,
            font=('Courier', 11),
            bg='#ecf0f1',
            fg='#2c3e50',
            wrap=tk.WORD
        )
        self.text_postorden.pack(fill=tk.X, padx=20, pady=5)

        # Instrucciones
        frame_instrucciones = tk.Frame(frame_derecho, bg='#2c3e50', relief=tk.RIDGE, borderwidth=2)
        frame_instrucciones.pack(fill=tk.X, padx=10, pady=10)

        instrucciones_texto = """
        Instrucciones:
        1. Escribe un numero GRANDE (3-5cm) en papel blanco
        2. Usa marcador negro grueso o lapiz oscuro
        3. Haz clic en 'Iniciar Camara'
        4. Muestra el numero centrado en la camara
        5. Haz clic en 'Capturar e Insertar'
        6. Espera unos segundos mientras procesa
        7. El numero se insertara en el arbol

        Tips para mejor deteccion:
        - Papel blanco liso sin arrugas
        - Iluminacion uniforme (sin sombras)
        - Numero centrado y completo en camara
        - Manten el papel quieto al capturar

        Nota: El procesamiento tarda 2-5 segundos
        por captura (normal en CPU)
        """

        tk.Label(
            frame_instrucciones,
            text=instrucciones_texto,
            font=('Arial', 8),
            bg='#2c3e50',
            fg='#ecf0f1',
            justify=tk.LEFT
        ).pack(padx=10, pady=10)

    # NUEVO MÉTODO: abrir la ventana de visualización del árbol
    def abrir_ventana_arbol(self):
        """Abre (o trae al frente) la ventana que dibuja el árbol AVL."""
        if self.ventana_arbol is None or not self.ventana_arbol.winfo_exists():
            self.ventana_arbol = VentanaArbol(self.ventana, self.arbol_avl)
        else:
            self.ventana_arbol.lift()
            self.ventana_arbol.dibujar()

    def cargar_modelo_ocr(self):
        """Carga el modelo de EasyOCR en un hilo separado"""
        self.label_estado.config(
            text="Cargando modelo EasyOCR... (puede tardar unos segundos)",
            fg='#f39c12'
        )
        self.ventana.update()

        def cargar():
            self.ocr_processor.inicializar_modelo()
            self.modelo_cargado = True
            self.label_estado.config(
                text="Modelo cargado correctamente",
                fg='#2ecc71'
            )
            self.ventana.after(3000, lambda: self.label_estado.config(text=""))

        threading.Thread(target=cargar, daemon=True).start()

    def iniciar_camara(self):
        """Inicia la captura de video de la cámara"""
        try:
            if not self.modelo_cargado:
                self.cargar_modelo_ocr()

            self.camara = cv2.VideoCapture(0)
            if not self.camara.isOpened():
                messagebox.showerror("Error", "No se puede acceder a la camara")
                return

            self.camara_activa = True
            self.btn_iniciar.config(state=tk.DISABLED)
            self.btn_detener.config(state=tk.NORMAL)
            self.btn_capturar.config(state=tk.NORMAL)

            threading.Thread(target=self.actualizar_video, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Error", f"Error al iniciar camara: {str(e)}")

    def actualizar_video(self):
        """Actualiza el frame de video continuamente"""
        while self.camara_activa:
            ret, frame = self.camara.read()
            if ret:
                self.ultimo_frame = frame.copy()
                frame = cv2.resize(frame, (560, 420))
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                imagen_procesada = self.ocr_processor.obtener_imagen_procesada(frame)

                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.label_video.imgtk = imgtk
                self.label_video.configure(image=imgtk)

                procesada_small = cv2.resize(imagen_procesada, (280, 210))
                img_proc = Image.fromarray(procesada_small)
                imgtk_proc = ImageTk.PhotoImage(image=img_proc)
                self.label_procesada.imgtk = imgtk_proc
                self.label_procesada.configure(image=imgtk_proc)

    def detener_camara(self):
        """Detiene la captura de video"""
        self.camara_activa = False
        if self.camara:
            self.camara.release()

        self.btn_iniciar.config(state=tk.NORMAL)
        self.btn_detener.config(state=tk.DISABLED)
        self.btn_capturar.config(state=tk.DISABLED)

        self.label_video.config(image='')
        self.label_procesada.config(image='')
        self.label_numero_detectado.config(text="Numero detectado: --", fg='#3498db')
        self.label_confianza.config(text="Confianza: --%", fg='#bdc3c7')

    def capturar_e_insertar(self):
        """Captura el número detectado y lo inserta en el árbol AVL"""
        if not self.modelo_cargado:
            messagebox.showwarning(
                "Modelo no cargado",
                "El modelo EasyOCR aun se esta cargando. Espera unos segundos."
            )
            return

        if self.ultimo_frame is None:
            messagebox.showwarning(
                "Sin imagen",
                "No hay ninguna imagen capturada de la camara."
            )
            return

        self.label_estado.config(
            text="Procesando imagen... (puede tardar unos segundos)",
            fg='#f39c12'
        )
        self.ventana.update()

        def procesar():
            numero, confianza = self.ocr_processor.extraer_numero(self.ultimo_frame)
            self.ultimo_numero = numero
            self.ultima_confianza = confianza
            self.ventana.after(0, lambda: self.mostrar_resultado_captura(numero, confianza))

        threading.Thread(target=procesar, daemon=True).start()

    def mostrar_resultado_captura(self, numero, confianza):
        """Muestra el resultado de la captura y pregunta si insertar"""
        self.label_estado.config(text="")

        if numero is not None:
            color_confianza = '#2ecc71' if confianza > 0.5 else '#f39c12'
            self.label_numero_detectado.config(
                text=f"Numero detectado: {numero}",
                fg='#2ecc71'
            )
            self.label_confianza.config(
                text=f"Confianza: {confianza*100:.1f}%",
                fg=color_confianza
            )

            if confianza < 0.5:
                respuesta = messagebox.askyesno(
                    "Confianza baja",
                    f"La confianza es {confianza*100:.1f}%.\n"
                    f"Seguro que quieres insertar {numero}?"
                )
                if not respuesta:
                    return

            if self.arbol_avl.buscar(numero):
                messagebox.showwarning(
                    "Duplicado",
                    f"El numero {numero} ya existe en el arbol"
                )
            else:
                self.arbol_avl.insertar(numero)
                messagebox.showinfo(
                    "Exito",
                    f"Numero {numero} insertado en el arbol\n"
                    f"Confianza: {confianza*100:.1f}%"
                )
                self.actualizar_recorridos()

                if self.ventana_arbol and self.ventana_arbol.winfo_exists():
                    self.ventana_arbol.dibujar()
        else:
            self.label_numero_detectado.config(
                text="Numero detectado: --",
                fg='#e74c3c'
            )
            self.label_confianza.config(
                text="Confianza: --%",
                fg='#bdc3c7'
            )
            messagebox.showwarning(
                "Sin numero",
                "No se ha detectado ningun numero.\n"
                "Asegurate de:\n"
                "- Escribir numeros grandes y claros (3-5 cm)\n"
                "- Usar fondo blanco y marcador oscuro\n"
                "- Centrar el numero en la camara\n"
                "- Buena iluminacion sin sombras"
            )

    def actualizar_recorridos(self):
        """Actualiza todos los recorridos del árbol"""
        cantidad = len(self.arbol_avl.numeros_insertados)
        self.label_cantidad.config(text=f"Numeros en arbol: {cantidad}")

        inorden = self.arbol_avl.recorrido_inorden()
        self.text_inorden.delete(1.0, tk.END)
        self.text_inorden.insert(tk.END, str(inorden) if inorden else "[]")

        preorden = self.arbol_avl.recorrido_preorden()
        self.text_preorden.delete(1.0, tk.END)
        self.text_preorden.insert(tk.END, str(preorden) if preorden else "[]")

        postorden = self.arbol_avl.recorrido_postorden()
        self.text_postorden.delete(1.0, tk.END)
        self.text_postorden.insert(tk.END, str(postorden) if postorden else "[]")

    def limpiar_arbol(self):
        """Limpia todos los números del árbol"""
        respuesta = messagebox.askyesno(
            "Confirmar",
            "Estas seguro de que quieres eliminar todos los numeros del arbol?"
        )
        if respuesta:
            self.arbol_avl.limpiar()
            self.actualizar_recorridos()

            if self.ventana_arbol and self.ventana_arbol.winfo_exists():
                self.ventana_arbol.dibujar()

            messagebox.showinfo("Exito", "Arbol limpiado correctamente")

    def cerrar_aplicacion(self):
        """Cierra la aplicación correctamente"""
        self.camara_activa = False
        if self.camara:
            self.camara.release()
        if self.ventana_arbol and self.ventana_arbol.winfo_exists():
            self.ventana_arbol.destroy()
        self.ventana.destroy()

def main():
    """Función principal"""
    ventana = tk.Tk()
    app = AplicacionOCRAVL(ventana)
    ventana.mainloop()

if __name__ == "__main__":
    main()