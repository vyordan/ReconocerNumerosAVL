"""
Procesador OCR para reconocimiento de números escritos a mano
usando EasyOCR (Deep Learning)
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
                verbose=False  # No mostrar mensajes de descarga
            )
            self.modelo_cargado = True
            print("Modelo cargado exitosamente!")
        
    def preprocesar_imagen(self, frame):
        """
        Preprocesa la imagen para mejorar el reconocimiento OCR
        Maneja diferentes condiciones de iluminación y fondos
        """
        # Convertir a escala de grises
        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Aplicar ecualización adaptativa de histograma (mejora contraste)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gris = clahe.apply(gris)
        
        # Aplicar desenfoque gaussiano para reducir ruido
        blur = cv2.GaussianBlur(gris, (3, 3), 0)
        
        # Binarización adaptativa (maneja iluminación variable)
        binaria = cv2.adaptiveThreshold(
            blur, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 
            11, 2
        )
        
        # Operaciones morfológicas para limpiar la imagen
        kernel = np.ones((2, 2), np.uint8)
        binaria = cv2.morphologyEx(binaria, cv2.MORPH_CLOSE, kernel)
        binaria = cv2.morphologyEx(binaria, cv2.MORPH_OPEN, kernel)
        
        return binaria
    
    def detectar_y_recortar_roi(self, imagen):
        """
        Detecta la región de interés (ROI) donde está el número
        """
        # Encontrar contornos
        contornos, _ = cv2.findContours(
            imagen, 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        if not contornos:
            return imagen
        
        # Encontrar el contorno más grande
        contorno_mayor = max(contornos, key=cv2.contourArea)
        
        # Filtrar contornos muy pequeños (ruido)
        area = cv2.contourArea(contorno_mayor)
        if area < 100:  # Muy pequeño, probablemente ruido
            return imagen
        
        # Obtener el rectángulo delimitador
        x, y, w, h = cv2.boundingRect(contorno_mayor)
        
        # Agregar margen
        margen = 20
        x = max(0, x - margen)
        y = max(0, y - margen)
        w = min(imagen.shape[1] - x, w + 2 * margen)
        h = min(imagen.shape[0] - y, h + 2 * margen)
        
        # Recortar región de interés
        roi = imagen[y:y+h, x:x+w]
        
        return roi
    
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
        Retorna el número reconocido o None si no se detecta
        """
        # Asegurar que el modelo esté cargado
        if not self.modelo_cargado:
            return None
        
        try:
            # Preprocesar imagen
            imagen_procesada = self.preprocesar_imagen(frame)
            
            # Detectar y recortar ROI
            roi = self.detectar_y_recortar_roi(imagen_procesada)
            
            # Redimensionar si es muy pequeña
            if roi.shape[0] < 32 or roi.shape[1] < 32:
                escala = max(32 / roi.shape[0], 32 / roi.shape[1])
                nuevo_ancho = int(roi.shape[1] * escala)
                nuevo_alto = int(roi.shape[0] * escala)
                roi = cv2.resize(roi, (nuevo_ancho, nuevo_alto), 
                                interpolation=cv2.INTER_CUBIC)
            
            # Convertir imagen binaria a RGB (EasyOCR necesita 3 canales)
            roi_rgb = cv2.cvtColor(roi, cv2.COLOR_GRAY2RGB)
            
            # Usar EasyOCR para detectar texto
            # allowlist solo permite dígitos, aumenta precisión
            resultados = self.reader.readtext(
                roi_rgb,
                allowlist='0123456789',
                detail=0,  # Solo devolver el texto, no coordenadas
                paragraph=False  # No agrupar en párrafos
            )
            
            # Procesar resultados
            if resultados:
                # Concatenar todos los resultados (por si detectó números separados)
                texto_completo = ''.join(resultados)
                
                # Extraer solo dígitos
                numero_str = self.extraer_solo_digitos(texto_completo)
                
                if numero_str:
                    return int(numero_str)
            
            return None
            
        except Exception as e:
            print(f"Error en OCR: {e}")
            return None
    
    def obtener_imagen_procesada(self, frame):
        """
        Retorna la imagen preprocesada para mostrar en la interfaz
        """
        return self.preprocesar_imagen(frame)
