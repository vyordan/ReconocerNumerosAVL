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
        self.ultima_confianza = 0.0
        self.modelo_cargado = False
        
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
        
        # Número detectado con confianza
        self.label_numero_detectado = tk.Label(
            frame_izquierdo,
            text="Número detectado: --",
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
        
        # ===== PANEL DERECHO: RECORRIDOS DEL ÁRBOL =====
        
        # Título
        titulo_arbol = tk.Label(
            frame_derecho,
            text="🌲 ÁRBOL AVL - RECORRIDOS",
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
            text="Números en árbol: 0",
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
            text="📊 Recorrido InOrden (ordenado):",
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
            text="🔽 Recorrido PreOrden:",
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
            text="🔼 Recorrido PostOrden:",
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
        📝 INSTRUCCIONES:
        1. Escribe un número GRANDE en papel blanco
        2. Usa marcador negro o lápiz oscuro
        3. Haz clic en 'Iniciar Cámara'
        4. Muestra el número centrado a la cámara
        5. Espera a ver confianza > 50%
        6. Haz clic en 'Capturar e Insertar'
        
        💡 Tips para mejor detección:
        • Números de 3-5 cm de alto
        • Fondo blanco liso (papel/pizarra)
        • Buena iluminación uniforme
        • Centra el número en la cámara
        • Mantén el papel quieto 2 segundos
        """
        
        tk.Label(
            frame_instrucciones,
            text=instrucciones_texto,
            font=('Arial', 8),
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
                frame = cv2.resize(frame, (560, 420))
                
                # Convertir BGR a RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Procesar imagen para OCR
                imagen_procesada = self.ocr_processor.obtener_imagen_procesada(frame)
                
                # Intentar detectar número (solo si el modelo está cargado)
                if self.modelo_cargado:
                    numero, confianza = self.ocr_processor.extraer_numero(frame)
                    self.ultimo_numero = numero
                    self.ultima_confianza = confianza
                    
                    # Actualizar label de número detectado
                    if numero is not None:
                        color_confianza = '#2ecc71' if confianza > 0.5 else '#f39c12'
                        self.label_numero_detectado.config(
                            text=f"Número detectado: {numero}",
                            fg='#2ecc71'
                        )
                        self.label_confianza.config(
                            text=f"Confianza: {confianza*100:.1f}%",
                            fg=color_confianza
                        )
                    else:
                        self.label_numero_detectado.config(
                            text="Número detectado: --",
                            fg='#e74c3c'
                        )
                        self.label_confianza.config(
                            text="Confianza: --%",
                            fg='#bdc3c7'
                        )
                
                # Mostrar video original
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.label_video.imgtk = imgtk
                self.label_video.configure(image=imgtk)
                
                # Mostrar imagen procesada (más pequeña)
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
        
        # Limpiar pantallas
        self.label_video.config(image='')
        self.label_procesada.config(image='')
        self.label_numero_detectado.config(text="Número detectado: --", fg='#3498db')
        self.label_confianza.config(text="Confianza: --%", fg='#bdc3c7')
    
    def capturar_e_insertar(self):
        """Captura el número detectado y lo inserta en el árbol AVL"""
        if not self.modelo_cargado:
            messagebox.showwarning(
                "Modelo no cargado",
                "El modelo EasyOCR aún se está cargando. Espera unos segundos."
            )
            return
        
        if self.ultimo_numero is not None:
            # Advertir si la confianza es baja
            if self.ultima_confianza < 0.5:
                respuesta = messagebox.askyesno(
                    "Confianza baja",
                    f"La confianza es {self.ultima_confianza*100:.1f}%.\n"
                    f"¿Seguro que quieres insertar {self.ultimo_numero}?"
                )
                if not respuesta:
                    return
            
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
                    f"Número {self.ultimo_numero} insertado en el árbol\n"
                    f"Confianza: {self.ultima_confianza*100:.1f}%"
                )
                self.actualizar_recorridos()
        else:
            messagebox.showwarning(
                "Sin número", 
                "No se ha detectado ningún número.\n"
                "Asegúrate de:\n"
                "• Escribir números grandes y claros\n"
                "• Usar fondo blanco y marcador oscuro\n"
                "• Centrar el número en la cámara\n"
                "• Mantener el papel quieto"
            )
    
    def actualizar_recorridos(self):
        """Actualiza todos los recorridos del árbol"""
        cantidad = len(self.arbol_avl.numeros_insertados)
        self.label_cantidad.config(text=f"Números en árbol: {cantidad}")
        
        # Recorrido InOrden
        inorden = self.arbol_avl.recorrido_inorden()
        self.text_inorden.delete(1.0, tk.END)
        self.text_inorden.insert(tk.END, str(inorden) if inorden else "[]")
        
        # Recorrido PreOrden
        preorden = self.arbol_avl.recorrido_preorden()
        self.text_preorden.delete(1.0, tk.END)
        self.text_preorden.insert(tk.END, str(preorden) if preorden else "[]")
        
        # Recorrido PostOrden
        postorden = self.arbol_avl.recorrido_postorden()
        self.text_postorden.delete(1.0, tk.END)
        self.text_postorden.insert(tk.END, str(postorden) if postorden else "[]")
    
    def limpiar_arbol(self):
        """Limpia todos los números del árbol"""
        respuesta = messagebox.askyesno(
            "Confirmar", 
            "¿Estás seguro de que quieres eliminar todos los números del árbol?"
        )
        if respuesta:
            self.arbol_avl.limpiar()
            self.actualizar_recorridos()
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