# Escape del laberinto — Proyecto final de Inteligencia Artificial

Videojuego por turnos con tres laberintos de 10 × 10. El jugador humano sale de
(1, 1) hacia (10, 10) y evita al perseguidor. Cada nivel utiliza un agente distinto:

| Nivel | Agente | Archivo |
|---|---|---|
| 1 | Búsqueda A* con costo 1 y distancia Manhattan | `agentes/nivel1_astar.py` |
| 2 | Minimax con poda alfa-beta; profundidad 4 | `agentes/nivel2_alfabeta.py` |
| 3 | Guardián, patrullaje y lógica proposicional de Horn | `agentes/nivel3_guardian.py`, `agentes/motor_logico.py` |

## Requisitos e instalación

Se recomienda Python 3.10 o posterior. **Ejecuta los comandos desde la raíz del
repositorio**, es decir, desde la carpeta donde está `main.py`.

En PowerShell (Windows):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

En Linux o macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

La dependencia gráfica es `pygame-ce`, cuyo módulo se importa como `pygame`.
Los algoritmos de IA no necesitan bibliotecas externas especializadas.
Para usar **solo la consola**, no es necesario instalar PyGame.

## Cómo iniciar

```powershell
py main.py               # interfaz gráfica (requiere pygame-ce)
py main.py --consola     # interfaz ASCII
py probar_nivel3.py      # prueba manual del escenario 3 aislado
```

En el modo gráfico se juega con **W/A/S/D o flechas**. También se puede pulsar
**H** para mostrar/ocultar la última ruta A*, **L** para alternar la luz,
**R** para reiniciar el nivel, **Enter** para avanzar tras escapar y **Esc**
para salir. En consola se emplea **W/A/S/D**, y **Q** para finalizar.

## Pruebas

```powershell
py -m unittest discover -s pruebas -v
```

Pruebas incluidas: estado y motor, A*, minimax con poda, motor lógico, guardián,
y la conexión básica de los tres niveles.

## Organización

- `main.py`: ejecutable principal y configuración de niveles.
- `mapas/`: escenarios oficiales del profesor.
- `nucleo/`: representación de estados, mapas, movimientos y reglas del turno.
- `agentes/`: implementaciones de los tres agentes y el motor lógico.
- `interfaz/`: salidas ASCII y PyGame.
- `pruebas/`: pruebas automáticas y de integración.

