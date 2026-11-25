"""Punto de entrada con interfaz gráfica (PyGame). Temática: Las minas de Moria.

Usa exactamente el mismo motor y los mismos agentes que main.py; solo cambia
la interfaz. Ejecutar desde la raíz del repositorio:

    python main_grafico.py
"""

from interfaz.pygame_moria import ejecutar_en_pygame
from main import construir_motor

if __name__ == "__main__":
    ejecutar_en_pygame(construir_motor())
