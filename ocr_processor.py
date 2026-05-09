"""
Procesador OCR para reconocimiento de números escritos a mano
usando EasyOCR (Deep Learning) - Versión mejorada con mayor precisión
"""

import cv2
import numpy as np
import easyocr
import re

class OCRProcessor:
    def __init__(self):
        # EasyOCR reader se inicializa de forma lazy (cuando se necesita)
        self.reader = None
        self.modelo_cargado = False
        
    def inicializar_modelo(self):
        """
        Inicializa el modelo de EasyOCR (solo se ejecuta una vez)
        Esto puede tardar unos segundos la primera vez
        """
        if not self.modelo_cargado:
            print("Cargando modelo EasyOCR... (puede tardar unos segundos)")
            # Configuración optimizada para CPU y solo dígitos
            self.reader = easyocr.Reader(
                ['en'],  # Idioma inglés (suficiente para números)
                gpu=False,  # Forzar uso de CPU
                verbose=True  # Mostrar progreso de descarga
            )
            self.modelo_cargado = True
            print("Modelo cargado exitosamente!")
        
    def preprocesar_imagen(self, frame):
        """
        Preprocesamiento LIGERO - menos agresivo para no perder información
        """
        # Convertir a escala de grises
        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Solo ecualización adaptativa (mejora contraste)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        gris = clahe.apply(gris)
        
        # Desenfoque MUY suave solo para reducir ruido
        blur = cv2.GaussianBlur(gris, (3, 3), 0)
        
        return blur
    
    def preprocesar_para_visualizacion(self, frame):
        """
        Preprocesamiento más agresivo solo para visualización
        """
        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gris = clahe.apply(gris)
        
        blur = cv2.GaussianBlur(gris, (5, 5), 0)
        
        # Binarización adaptativa
        binaria = cv2.adaptiveThreshold(
            blur, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 
            11, 2
        )
        
        # Operaciones morfológicas
        kernel = np.ones((2, 2), np.uint8)
        binaria = cv2.morphologyEx(binaria, cv2.MORPH_CLOSE, kernel)
        
        return binaria
    
    def extraer_solo_digitos(self, texto):
        """
        Extrae solo los dígitos de un texto
        """
        # Eliminar todo lo que no sea dígito
        digitos = re.sub(r'[^0-9]', '', texto)
        return digitos if digitos else None
    
    def extraer_numero(self, frame):
        """
        Extrae y reconoce el número de un frame de video usando EasyOCR
        Retorna (número, confianza) o (None, 0.0) si no se detecta
        """
        # Asegurar que el modelo esté cargado
        if not self.modelo_cargado:
            return None, 0.0
        
        try:
            # Preprocesar imagen LIGERAMENTE
            imagen_procesada = self.preprocesar_imagen(frame)
            
            # Redimensionar para mejorar detección (más grande = mejor)
            alto, ancho = imagen_procesada.shape
            escala = 2.0  # Aumentar x2
            nuevo_ancho = int(ancho * escala)
            nuevo_alto = int(alto * escala)
            imagen_grande = cv2.resize(
                imagen_procesada, 
                (nuevo_ancho, nuevo_alto), 
                interpolation=cv2.INTER_CUBIC
            )
            
            # Convertir a RGB (EasyOCR necesita 3 canales)
            imagen_rgb = cv2.cvtColor(imagen_grande, cv2.COLOR_GRAY2RGB)
            
            # Usar EasyOCR con configuración MEJORADA
            resultados = self.reader.readtext(
                imagen_rgb,
                allowlist='0123456789',  # Solo dígitos
                detail=1,  # Retornar coordenadas y confianza
                paragraph=False,  # No agrupar
                min_size=10,  # Tamaño mínimo de detección (menos restrictivo)
                text_threshold=0.4,  # Umbral de confianza de texto (más permisivo)
                low_text=0.3,  # Umbral bajo de texto (más permisivo)
                link_threshold=0.3,  # Umbral de enlace (más permisivo)
                canvas_size=2560,  # Tamaño de canvas grande
                mag_ratio=1.5  # Ratio de magnificación
            )
            
            # Procesar resultados
            if resultados:
                # EasyOCR retorna: (bbox, texto, confianza)
                # Tomar el resultado con mayor confianza
                mejor_resultado = max(resultados, key=lambda x: x[2])
                bbox, texto, confianza = mejor_resultado
                
                # Extraer solo dígitos
                numero_str = self.extraer_solo_digitos(texto)
                
                if numero_str:
                    return int(numero_str), confianza
            
            return None, 0.0
            
        except Exception as e:
            print(f"Error en OCR: {e}")
            return None, 0.0
    
    def obtener_imagen_procesada(self, frame):
        """
        Retorna la imagen preprocesada para mostrar en la interfaz
        (versión agresiva solo para visualización)
        """
        return self.preprocesar_para_visualizacion(frame)