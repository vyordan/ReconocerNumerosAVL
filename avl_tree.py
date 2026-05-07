"""
Implementación de Árbol AVL para almacenar números
"""

class NodoAVL:
    def __init__(self, valor):
        self.valor = valor
        self.izquierda = None
        self.derecha = None
        self.altura = 1

class ArbolAVL:
    def __init__(self):
        self.raiz = None
        self.numeros_insertados = []
    
    def obtener_altura(self, nodo):
        """Obtiene la altura de un nodo"""
        if not nodo:
            return 0
        return nodo.altura
    
    def obtener_balance(self, nodo):
        """Calcula el factor de balance de un nodo"""
        if not nodo:
            return 0
        return self.obtener_altura(nodo.izquierda) - self.obtener_altura(nodo.derecha)
    
    def rotacion_derecha(self, y):
        """Realiza rotación simple a la derecha"""
        x = y.izquierda
        T2 = x.derecha
        
        # Realizar rotación
        x.derecha = y
        y.izquierda = T2
        
        # Actualizar alturas
        y.altura = 1 + max(self.obtener_altura(y.izquierda),
                          self.obtener_altura(y.derecha))
        x.altura = 1 + max(self.obtener_altura(x.izquierda),
                          self.obtener_altura(x.derecha))
        
        return x
    
    def rotacion_izquierda(self, x):
        """Realiza rotación simple a la izquierda"""
        y = x.derecha
        T2 = y.izquierda
        
        # Realizar rotación
        y.izquierda = x
        x.derecha = T2
        
        # Actualizar alturas
        x.altura = 1 + max(self.obtener_altura(x.izquierda),
                          self.obtener_altura(x.derecha))
        y.altura = 1 + max(self.obtener_altura(y.izquierda),
                          self.obtener_altura(y.derecha))
        
        return y
    
    def insertar(self, valor):
        """Inserta un valor en el árbol AVL"""
        self.raiz = self._insertar_recursivo(self.raiz, valor)
        self.numeros_insertados.append(valor)
        return True
    
    def _insertar_recursivo(self, nodo, valor):
        """Inserción recursiva con balanceo automático"""
        # Paso 1: Inserción BST normal
        if not nodo:
            return NodoAVL(valor)
        
        if valor < nodo.valor:
            nodo.izquierda = self._insertar_recursivo(nodo.izquierda, valor)
        elif valor > nodo.valor:
            nodo.derecha = self._insertar_recursivo(nodo.derecha, valor)
        else:
            # Valores duplicados no se insertan
            return nodo
        
        # Paso 2: Actualizar altura del nodo ancestro
        nodo.altura = 1 + max(self.obtener_altura(nodo.izquierda),
                             self.obtener_altura(nodo.derecha))
        
        # Paso 3: Obtener factor de balance
        balance = self.obtener_balance(nodo)
        
        # Paso 4: Si el nodo está desbalanceado, hay 4 casos
        
        # Caso Izquierda-Izquierda
        if balance > 1 and valor < nodo.izquierda.valor:
            return self.rotacion_derecha(nodo)
        
        # Caso Derecha-Derecha
        if balance < -1 and valor > nodo.derecha.valor:
            return self.rotacion_izquierda(nodo)
        
        # Caso Izquierda-Derecha
        if balance > 1 and valor > nodo.izquierda.valor:
            nodo.izquierda = self.rotacion_izquierda(nodo.izquierda)
            return self.rotacion_derecha(nodo)
        
        # Caso Derecha-Izquierda
        if balance < -1 and valor < nodo.derecha.valor:
            nodo.derecha = self.rotacion_derecha(nodo.derecha)
            return self.rotacion_izquierda(nodo)
        
        return nodo
    
    def buscar(self, valor):
        """Busca un valor en el árbol"""
        return self._buscar_recursivo(self.raiz, valor)
    
    def _buscar_recursivo(self, nodo, valor):
        """Búsqueda recursiva"""
        if not nodo:
            return False
        
        if valor == nodo.valor:
            return True
        elif valor < nodo.valor:
            return self._buscar_recursivo(nodo.izquierda, valor)
        else:
            return self._buscar_recursivo(nodo.derecha, valor)
    
    def recorrido_inorden(self):
        """Retorna los valores del árbol en orden"""
        valores = []
        self._inorden_recursivo(self.raiz, valores)
        return valores
    
    def _inorden_recursivo(self, nodo, valores):
        """Recorrido inorden recursivo"""
        if nodo:
            self._inorden_recursivo(nodo.izquierda, valores)
            valores.append(nodo.valor)
            self._inorden_recursivo(nodo.derecha, valores)
    
    def obtener_estructura_visual(self):
        """Obtiene la estructura del árbol para visualización"""
        if not self.raiz:
            return []
        
        niveles = []
        cola = [(self.raiz, 0, 0)]  # (nodo, nivel, posición_horizontal)
        
        while cola:
            nodo, nivel, pos = cola.pop(0)
            
            if nivel >= len(niveles):
                niveles.append([])
            
            niveles[nivel].append((nodo.valor, pos))
            
            if nodo.izquierda:
                cola.append((nodo.izquierda, nivel + 1, pos * 2))
            if nodo.derecha:
                cola.append((nodo.derecha, nivel + 1, pos * 2 + 1))
        
        return niveles
    
    def limpiar(self):
        """Limpia el árbol completamente"""
        self.raiz = None
        self.numeros_insertados = []
