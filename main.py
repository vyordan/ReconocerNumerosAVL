"""
Aplicación de Reconocimiento de Números con Cámara y Árbol AVL
Interfaz gráfica con Tkinter
Usa EasyOCR para reconocimiento de números manuscritos
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading
from avl_tree import ArbolAVL
from ocr_processor import OCRProcessor

class AplicacionOCRAVL:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Reconocimiento de Números - Árbol AVL (EasyOCR)")
        self.ventana.geometry("1200x700")
        self.ventana.configure(bg='#2c3e50')
        
        # Inicializar componentes
        self.arbol_avl = ArbolAVL()
        self.ocr_processor = OCRProcessor()
        self.camara = None
        self.camara_activa = False
        self.ultimo_numero = None
        self.modelo_cargado = False
        
        # Crear interfaz
        self.crear_interfaz()
        
        # Configurar cierre de ventana
        self.ventana.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)
    
    def crear_interfaz(self):
        """Crea todos los componentes de la interfaz"""
        
        # Frame principal dividido en 2 columnas
        frame_izquierdo = tk.Frame(self.ventana, bg='#34495e', width=600)
        frame_izquierdo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        frame_derecho = tk.Frame(self.ventana, bg='#34495e', width=600)
        frame_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ===== PANEL IZQUIERDO: CÁMARA Y CONTROLES =====
        
        # Título
        titulo_cam = tk.Label(
            frame_izquierdo, 
            text="📷 CAPTURA DE NÚMEROS (EasyOCR)", 
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
        
        # Número detectado
        self.label_numero_detectado = tk.Label(
            frame_izquierdo,
            text="Número detectado: --",
            font=('Arial', 14, 'bold'),
            bg='#34495e',
            fg='#3498db'
        )
        self.label_numero_detectado.pack(pady=10)
        
        # Label de estado (para mostrar "Cargando modelo...")
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
        
        self.btn_iniciar = tk.Button(
            frame_botones,
            text="▶ Iniciar Cámara",
            command=self.iniciar_camara,
            font=('Arial', 12, 'bold'),
            bg='#27ae60',
            fg='white',
            width=15,
            height=2,
            cursor='hand2'
        )
        self.btn_iniciar.grid(row=0, column=0, padx=5)
        
        self.btn_capturar = tk.Button(
            frame_botones,
            text="📸 Capturar e Insertar",
            command=self.capturar_e_insertar,
            font=('Arial', 12, 'bold'),
            bg='#3498db',
            fg='white',
            width=18,
            height=2,
            cursor='hand2',
            state=tk.DISABLED
        )
        self.btn_capturar.grid(row=0, column=1, padx=5)
        
        self.btn_detener = tk.Button(
            frame_botones,
            text="⏹ Detener Cámara",
            command=self.detener_camara,
            font=('Arial', 12, 'bold'),
            bg='#e74c3c',
            fg='white',
            width=15,
            height=2,
            cursor='hand2',
            state=tk.DISABLED
        )
        self.btn_detener.grid(row=1, column=0, padx=5, pady=5)
        
        self.btn_limpiar = tk.Button(
            frame_botones,
            text="🗑 Limpiar Árbol",
            command=self.limpiar_arbol,
            font=('Arial', 12, 'bold'),
            bg='#95a5a6',
            fg='white',
            width=18,
            height=2,
            cursor='hand2'
        )
        self.btn_limpiar.grid(row=1, column=1, padx=5, pady=5)
        
        # ===== PANEL DERECHO: ÁRBOL AVL =====
        
        # Título
        titulo_arbol = tk.Label(
            frame_derecho,
            text="ÁRBOL AVL",
            font=('Arial', 16, 'bold'),
            bg='#34495e',
            fg='#ecf0f1'
        )
        titulo_arbol.pack(pady=10)
        
        # Canvas para dibujar el árbol
        canvas_frame = tk.Frame(frame_derecho, bg='white')
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas_arbol = tk.Canvas(
            canvas_frame,
            bg='white',
            highlightthickness=1,
            highlightbackground='#7f8c8d'
        )
        self.canvas_arbol.pack(fill=tk.BOTH, expand=True)
        
        # Información del árbol
        frame_info = tk.Frame(frame_derecho, bg='#34495e')
        frame_info.pack(pady=10)
        
        self.label_cantidad = tk.Label(
            frame_info,
            text="Números en árbol: 0",
            font=('Arial', 12),
            bg='#34495e',
            fg='#ecf0f1'
        )
        self.label_cantidad.pack()
        
        self.label_recorrido = tk.Label(
            frame_info,
            text="Recorrido InOrden: []",
            font=('Arial', 10),
            bg='#34495e',
            fg='#bdc3c7',
            wraplength=500
        )
        self.label_recorrido.pack(pady=5)
        
        # Instrucciones
        frame_instrucciones = tk.Frame(frame_derecho, bg='#2c3e50', relief=tk.RIDGE, borderwidth=2)
        frame_instrucciones.pack(fill=tk.X, padx=10, pady=10)
        
        instrucciones_texto = """
        📝 INSTRUCCIONES:
        1. Escribe un número en papel o pizarra
        2. Haz clic en 'Iniciar Cámara'
        3. Muestra el número a la cámara
        4. Haz clic en 'Capturar e Insertar'
        5. El número se agregará al árbol AVL
        
        💡 Consejos:
        • Escribe números grandes y claros
        • Usa fondo de contraste (papel blanco/pizarra)
        • Buena iluminación ayuda al reconocimiento
        • EasyOCR funciona muy bien con escritura a mano
        
        ⚠️ Primera vez:
        • El modelo se carga al iniciar la cámara
        • Puede tardar 5-10 segundos la primera vez
        """
        
        tk.Label(
            frame_instrucciones,
            text=instrucciones_texto,
            font=('Arial', 9),
            bg='#2c3e50',
            fg='#ecf0f1',
            justify=tk.LEFT
        ).pack(padx=10, pady=10)
    
    def cargar_modelo_ocr(self):
        """Carga el modelo de EasyOCR en un hilo separado"""
        self.label_estado.config(
            text="⏳ Cargando modelo EasyOCR... (puede tardar unos segundos)",
            fg='#f39c12'
        )
        self.ventana.update()
        
        # Cargar modelo en segundo plano
        def cargar():
            self.ocr_processor.inicializar_modelo()
            self.modelo_cargado = True
            self.label_estado.config(
                text="✓ Modelo cargado correctamente",
                fg='#2ecc71'
            )
            # Limpiar mensaje después de 3 segundos
            self.ventana.after(3000, lambda: self.label_estado.config(text=""))
        
        threading.Thread(target=cargar, daemon=True).start()
    
    def iniciar_camara(self):
        """Inicia la captura de video de la cámara"""
        try:
            # Cargar modelo si no está cargado
            if not self.modelo_cargado:
                self.cargar_modelo_ocr()
            
            self.camara = cv2.VideoCapture(0)
            if not self.camara.isOpened():
                messagebox.showerror("Error", "No se puede acceder a la cámara")
                return
            
            self.camara_activa = True
            self.btn_iniciar.config(state=tk.DISABLED)
            self.btn_detener.config(state=tk.NORMAL)
            self.btn_capturar.config(state=tk.NORMAL)
            
            # Iniciar hilo para actualizar video
            threading.Thread(target=self.actualizar_video, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al iniciar cámara: {str(e)}")
    
    def actualizar_video(self):
        """Actualiza el frame de video continuamente"""
        while self.camara_activa:
            ret, frame = self.camara.read()
            if ret:
                # Redimensionar frame
                frame = cv2.resize(frame, (480, 360))
                
                # Convertir BGR a RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Procesar imagen para OCR
                imagen_procesada = self.ocr_processor.obtener_imagen_procesada(frame)
                
                # Intentar detectar número (solo si el modelo está cargado)
                if self.modelo_cargado:
                    numero = self.ocr_processor.extraer_numero(frame)
                    self.ultimo_numero = numero
                    
                    # Actualizar label de número detectado
                    if numero is not None:
                        self.label_numero_detectado.config(
                            text=f"Número detectado: {numero}",
                            fg='#2ecc71'
                        )
                    else:
                        self.label_numero_detectado.config(
                            text="Número detectado: --",
                            fg='#e74c3c'
                        )
                
                # Mostrar video original
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.label_video.imgtk = imgtk
                self.label_video.configure(image=imgtk)
                
                # Mostrar imagen procesada (más pequeña)
                procesada_small = cv2.resize(imagen_procesada, (240, 180))
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
        
        # Limpiar pantallas
        self.label_video.config(image='')
        self.label_procesada.config(image='')
        self.label_numero_detectado.config(text="Número detectado: --", fg='#3498db')
    
    def capturar_e_insertar(self):
        """Captura el número detectado y lo inserta en el árbol AVL"""
        if not self.modelo_cargado:
            messagebox.showwarning(
                "Modelo no cargado",
                "El modelo EasyOCR aún se está cargando. Espera unos segundos."
            )
            return
        
        if self.ultimo_numero is not None:
            # Verificar si ya existe
            if self.arbol_avl.buscar(self.ultimo_numero):
                messagebox.showwarning(
                    "Duplicado", 
                    f"El número {self.ultimo_numero} ya existe en el árbol"
                )
            else:
                # Insertar en árbol
                self.arbol_avl.insertar(self.ultimo_numero)
                messagebox.showinfo(
                    "Éxito", 
                    f"Número {self.ultimo_numero} insertado en el árbol"
                )
                self.dibujar_arbol()
                self.actualizar_info_arbol()
        else:
            messagebox.showwarning(
                "Sin número", 
                "No se ha detectado ningún número.\nAsegúrate de mostrar un número claro a la cámara."
            )
    
    def dibujar_arbol(self):
        """Dibuja el árbol AVL en el canvas"""
        self.canvas_arbol.delete("all")
        
        if not self.arbol_avl.raiz:
            self.canvas_arbol.create_text(
                self.canvas_arbol.winfo_width() // 2,
                self.canvas_arbol.winfo_height() // 2,
                text="Árbol vacío",
                font=('Arial', 14),
                fill='gray'
            )
            return
        
        # Obtener estructura del árbol
        niveles = self.arbol_avl.obtener_estructura_visual()
        
        # Configuración de dibujo
        ancho_canvas = self.canvas_arbol.winfo_width()
        alto_canvas = self.canvas_arbol.winfo_height()
        
        if ancho_canvas <= 1:
            ancho_canvas = 500
        if alto_canvas <= 1:
            alto_canvas = 400
        
        radio_nodo = 25
        espacio_vertical = alto_canvas // (len(niveles) + 1)
        
        # Dibujar nodos y conexiones
        nodos_coords = {}
        
        for nivel_idx, nivel in enumerate(niveles):
            y = (nivel_idx + 1) * espacio_vertical
            num_nodos = len(nivel)
            espacio_horizontal = ancho_canvas // (num_nodos + 1)
            
            for idx, (valor, pos) in enumerate(nivel):
                x = (idx + 1) * espacio_horizontal
                nodos_coords[(nivel_idx, pos)] = (x, y)
                
                # Dibujar círculo del nodo
                self.canvas_arbol.create_oval(
                    x - radio_nodo, y - radio_nodo,
                    x + radio_nodo, y + radio_nodo,
                    fill='#3498db',
                    outline='#2980b9',
                    width=3
                )
                
                # Dibujar valor
                self.canvas_arbol.create_text(
                    x, y,
                    text=str(valor),
                    font=('Arial', 12, 'bold'),
                    fill='white'
                )
                
                # Dibujar líneas a hijos
                if nivel_idx < len(niveles) - 1:
                    # Buscar hijos
                    for valor_hijo, pos_hijo in niveles[nivel_idx + 1]:
                        if pos_hijo == pos * 2 or pos_hijo == pos * 2 + 1:
                            if (nivel_idx + 1, pos_hijo) in nodos_coords:
                                x2, y2 = nodos_coords[(nivel_idx + 1, pos_hijo)]
                                self.canvas_arbol.create_line(
                                    x, y + radio_nodo,
                                    x2, y2 - radio_nodo,
                                    fill='#7f8c8d',
                                    width=2
                                )
    
    def actualizar_info_arbol(self):
        """Actualiza la información del árbol"""
        cantidad = len(self.arbol_avl.numeros_insertados)
        self.label_cantidad.config(text=f"Números en árbol: {cantidad}")
        
        recorrido = self.arbol_avl.recorrido_inorden()
        self.label_recorrido.config(text=f"Recorrido InOrden: {recorrido}")
    
    def limpiar_arbol(self):
        """Limpia todos los números del árbol"""
        respuesta = messagebox.askyesno(
            "Confirmar", 
            "¿Estás seguro de que quieres eliminar todos los números del árbol?"
        )
        if respuesta:
            self.arbol_avl.limpiar()
            self.dibujar_arbol()
            self.actualizar_info_arbol()
            messagebox.showinfo("Éxito", "Árbol limpiado correctamente")
    
    def cerrar_aplicacion(self):
        """Cierra la aplicación correctamente"""
        self.camara_activa = False
        if self.camara:
            self.camara.release()
        self.ventana.destroy()

def main():
    """Función principal"""
    ventana = tk.Tk()
    app = AplicacionOCRAVL(ventana)
    ventana.mainloop()

if __name__ == "__main__":
    main()
