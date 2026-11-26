"""Interfaz gráfica con PyGame. Temática: Las minas de Moria.

Usa el motor del juego (nucleo/): no tiene reglas propias, solo lee el estado
del MotorJuego y envía las acciones del jugador. Sirve para los 3 niveles.

El tablero se dibuja por código y admite sprites PNG opcionales:
  #  muro de piedra       .  piso de losas       E  puerta con luz
  P  Gandalf (mago)                               G  Balrog (agente)
Los sprites son visuales: P/G siguen indicando posiciones del motor.
Los finales de derrota y victoria usan escenas pixel art opcionales.
El lienzo se adapta a la ventana; las letras se rasterizan a tamaño real
para que no se borren al escalar.

Ejecutar desde la raíz del repo:  py main.py
La interfaz cambia de distribución según el ancho disponible: panel lateral
para ventanas anchas y panel inferior para ventanas estrechas.
"""

import math
import random
from pathlib import Path

import pygame

from nucleo.estado import movimientos_validos
from nucleo.mapa import ANCHO as TAM
from nucleo.motor import MotorJuego, ResultadoNivel

CELDA = 56
MARGEN_X = 40
TOP = 110
ANCHO = MARGEN_X * 2 + CELDA * TAM
ALTO = TOP + CELDA * TAM + 175
# Dos lienzos lógicos; el mapa conserva siempre las mismas coordenadas.
ANCHO_LATERAL = 1005
ALTO_LATERAL = 710

FONDO = (14, 12, 10)
ORO = (214, 176, 86)
ORO_OSC = (120, 96, 44)
PERGAMINO = (226, 208, 166)
ROJO_OJOS = (255, 40, 30)
AZUL_CAPA = (96, 130, 182)

OSCURIDAD = 80  # 0 = sin oscuridad, 255 = negro total


def _mascara_luz(radio, maximo):
    """Círculo cuyo valor alfa baja desde el centro; se resta a la oscuridad."""
    s = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
    for i in range(radio, 0, -3):
        a = int(maximo * (1 - i / radio) ** 0.8)
        pygame.draw.circle(s, (255, 255, 255, a), (radio, radio), i)
    return s


def _brillo(radio, color):
    """Resplandor cálido para mezclar de forma aditiva."""
    s = pygame.Surface((radio * 2, radio * 2))
    s.fill((0, 0, 0))
    for i in range(radio, 0, -3):
        k = (1 - i / radio) ** 1.6
        pygame.draw.circle(s, tuple(int(c * k) for c in color), (radio, radio), i)
    return s


class Interfaz:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Escape del laberinto - Las minas de Moria")
        # Seleccionamos primero la distribución que mejor aprovecha el escritorio.
        # Los tamaños de los elementos del laberinto no cambian: se escala el lienzo
        # completo al final, conservando las proporciones.
        info = pygame.display.Info()
        escritorio_w, escritorio_h = info.current_w, info.current_h
        espacio_w = max(1, int(escritorio_w * 0.90))
        espacio_h = max(1, int(escritorio_h * 0.84))
        usar_lateral = escritorio_w >= 980 and escritorio_w / max(1, escritorio_h) >= 1.28
        base_w, base_h = (ANCHO_LATERAL, ALTO_LATERAL) if usar_lateral else (ANCHO, ALTO)
        factor = min(1.0, espacio_w / base_w, espacio_h / base_h)
        tam_ventana = (max(1, int(base_w * factor)), max(1, int(base_h * factor)))
        self.ventana = pygame.display.set_mode(tam_ventana, pygame.RESIZABLE)
        self.modo_panel = "lateral" if usar_lateral else "inferior"
        self.ancho_logico, self.alto_logico = base_w, base_h
        self.pantalla = pygame.Surface((base_w, base_h)).convert()
        self.f_titulo = pygame.font.SysFont("georgia", 34, bold=True)
        self.f_texto = pygame.font.SysFont("georgia", 20, bold=True)
        self.f_peq = pygame.font.SysFont("georgia", 15, bold=True)
        self.luz_activa = True
        self.sprite_jugador = self._cargar_sprite_jugador()
        self.sprite_agente = self._cargar_sprite_agente()
        self.escena_derrota = self._cargar_escena_final("derrota.png")
        self.escena_victoria = self._cargar_escena_final("victoria.png")
        self._mostrar_final = False
        # El juego sigue usando un lienzo lógico para el tablero, pero el texto
        # se pinta después directamente sobre la ventana a su resolución real.
        self._textos_pendientes = []
        self._fuentes_resolucion = {}

        self._clave = None
        self.fondo = None
        self.antorchas = []

        # efectos de luz precalculados
        self.luz_jugador = [_mascara_luz(r, OSCURIDAD) for r in (190, 200, 212)]
        self.luz_salida = _mascara_luz(120, int(OSCURIDAD * 0.85))
        self.luz_antorcha = _mascara_luz(78, int(OSCURIDAD * 0.7))
        self.brillo_jugador = _brillo(150, (70, 38, 10))
        self.brillo_salida = _brillo(90, (90, 66, 20))
        self.brillo_antorcha = _brillo(56, (60, 32, 8))

    def _actualizar_disposicion(self):
        """Cambia el panel de lado a abajo al estrechar la ventana y viceversa."""
        self.ventana = pygame.display.get_surface()
        w, h = self.ventana.get_size()
        # Umbral de ancho y proporción: evita un panel lateral diminuto.
        lateral = w >= 720 and w / max(h, 1) >= 1.23
        nuevo = "lateral" if lateral else "inferior"
        if nuevo == self.modo_panel:
            return
        self.modo_panel = nuevo
        self.ancho_logico, self.alto_logico = ((ANCHO_LATERAL, ALTO_LATERAL)
                                                if lateral else (ANCHO, ALTO))
        self.pantalla = pygame.Surface((self.ancho_logico, self.alto_logico)).convert()
        self._clave = None  # reconstruir fondo para el nuevo lienzo

    # ---- coordenadas: (1,1) abajo a la izquierda ---------------------
    def rect(self, celda):
        x, y = celda
        return pygame.Rect(MARGEN_X + (x - 1) * CELDA,
                           TOP + (TAM - y) * CELDA, CELDA, CELDA)

    # ---- piezas de arte estáticas ------------------------------------
    @staticmethod
    def _piso(s, r, rng):
        v = rng.randint(-8, 8)
        base = (44 + v, 40 + v, 36 + v)
        pygame.draw.rect(s, base, r)
        pygame.draw.line(s, (60 + v, 55 + v, 49 + v), (r.left + 1, r.top + 1), (r.right - 2, r.top + 1))
        pygame.draw.line(s, (60 + v, 55 + v, 49 + v), (r.left + 1, r.top + 1), (r.left + 1, r.bottom - 2))
        pygame.draw.rect(s, (30, 27, 23), r, 1)
        for _ in range(7):
            px, py = rng.randint(r.left + 3, r.right - 4), rng.randint(r.top + 3, r.bottom - 4)
            d = rng.choice((-14, 10))
            pygame.draw.rect(s, (base[0] + d, base[1] + d, base[2] + d), (px, py, 2, 2))
        if rng.random() < 0.2:
            x0, y0 = rng.randint(r.left + 8, r.right - 8), rng.randint(r.top + 8, r.bottom - 8)
            pts = [(x0, y0), (x0 + rng.randint(-8, 8), y0 + rng.randint(4, 10)),
                   (x0 + rng.randint(-12, 12), y0 + rng.randint(12, 20))]
            pygame.draw.lines(s, (28, 25, 21), False, pts, 1)

    @staticmethod
    def _muro(s, r, rng):
        w, h = r.width, r.height // 2
        filas = [[(0, w // 2), (w // 2, w)],
                 [(0, w // 4), (w // 4, 3 * w // 4), (3 * w // 4, w)]]
        for i, ladrillos in enumerate(filas):
            for x0, x1 in ladrillos:
                v = rng.randint(-10, 10)
                b = pygame.Rect(r.left + x0, r.top + i * h, x1 - x0, h)
                pygame.draw.rect(s, (116 + v, 108 + v, 96 + v), b)
                pygame.draw.line(s, (158 + v, 150 + v, 134 + v), b.topleft, (b.right - 1, b.top))
                pygame.draw.line(s, (158 + v, 150 + v, 134 + v), b.topleft, (b.left, b.bottom - 1))
                pygame.draw.line(s, (44, 40, 35), (b.left, b.bottom - 1), (b.right - 1, b.bottom - 1))
                pygame.draw.line(s, (44, 40, 35), (b.right - 1, b.top), (b.right - 1, b.bottom - 1))
        pygame.draw.rect(s, (22, 19, 16), r, 1)
        if rng.random() < 0.5:  # musgo
            for _ in range(5):
                pygame.draw.rect(s, (62, 86, 46), (rng.randint(r.left + 2, r.right - 4),
                                                    rng.randint(r.bottom - 14, r.bottom - 3), 3, 2))

    @staticmethod
    def _puerta(s, r):
        cx, cy = r.center
        marco = pygame.Rect(0, 0, 36, 44)
        marco.midbottom = (cx, r.bottom - 4)
        arco = pygame.Rect(marco.left, marco.top - 4, 36, 36)
        pygame.draw.rect(s, (150, 140, 120), marco.inflate(8, 0))
        pygame.draw.ellipse(s, (150, 140, 120), arco.inflate(8, 8))
        pygame.draw.rect(s, (255, 214, 130), marco)
        pygame.draw.ellipse(s, (255, 214, 130), arco)
        pygame.draw.rect(s, (255, 244, 205), marco.inflate(-18, -8).move(0, 4))
        pygame.draw.rect(s, (96, 88, 74), marco.inflate(8, 0), 2)

    def _construir_fondo(self, lab):
        s = pygame.Surface((self.ancho_logico, self.alto_logico))
        for y in range(self.alto_logico):  # fondo con degradado vertical
            k = 1 - 0.5 * y / self.alto_logico
            pygame.draw.line(s, (int(22 * k), int(19 * k), int(16 * k)), (0, y), (self.ancho_logico, y))

        tablero = pygame.Rect(MARGEN_X, TOP, CELDA * TAM, CELDA * TAM)
        s.set_clip(tablero)
        for x in range(1, TAM + 1):
            for y in range(1, TAM + 1):
                self._piso(s, self.rect((x, y)), random.Random(x * 131 + y * 17))
        sombra = pygame.Surface((CELDA, CELDA), pygame.SRCALPHA)
        sombra.fill((0, 0, 0, 95))
        for celda in lab.obstaculos:
            s.blit(sombra, self.rect(celda).move(5, 5))
        for celda in lab.obstaculos:
            self._muro(s, self.rect(celda), random.Random(celda[0] * 53 + celda[1] * 7))
        s.set_clip(None)

        self._puerta(s, self.rect(lab.salida))

        # antorchas de pared en algunos muros
        self.antorchas = []
        for (x, y) in sorted(lab.obstaculos):
            if (x * 7 + y * 3) % 11 == 0 and len(self.antorchas) < 6:
                c = self.rect((x, y)).center
                pygame.draw.rect(s, (40, 30, 20), (c[0] - 3, c[1] - 2, 6, 12))
                self.antorchas.append((c[0], c[1] - 6))

        # marco de piedra alrededor del tablero
        pygame.draw.rect(s, (70, 64, 56), tablero.inflate(26, 26), 13)
        pygame.draw.rect(s, (28, 25, 21), tablero.inflate(26, 26), 2)
        pygame.draw.rect(s, ORO_OSC, tablero.inflate(2, 2), 2)

        # El título se pinta en cada fotograma directamente a la resolución
        # real de la ventana (no queda almacenado borroso en este fondo).
        return s

    @staticmethod
    def _cargar_escena_final(nombre):
        """Arte opcional para las pantallas de derrota y victoria."""
        ruta = Path(__file__).resolve().parent.parent / "assets" / "finales" / nombre
        try:
            return pygame.image.load(str(ruta)).convert()
        except (OSError, pygame.error):
            return None

    @staticmethod
    def _dibujar_arte_escena(destino, imagen, area, recortar=False):
        """Muestra el arte sin deformarlo ni tapar los controles."""
        iw, ih = imagen.get_size()
        if recortar:
            factor = max(area.width / iw, area.height / ih)
        else:
            factor = min(area.width / iw, area.height / ih)
        dw, dh = max(1, round(iw * factor)), max(1, round(ih * factor))
        arte = pygame.transform.scale(imagen, (dw, dh))  # píxeles nítidos (pixel art)
        rect = arte.get_rect(center=area.center)
        anterior = destino.get_clip()
        destino.set_clip(area)
        destino.blit(arte, rect)
        destino.set_clip(anterior)

    def _pantalla_cinematografica(self, motor, resultado):
        """Presenta los finales pixel art sin alterar el estado del motor.

        Se utilizan imágenes sin botones, así los controles siguen siendo
        texto real del juego, no zonas clicables ficticias. Escala con aspecto
        preservado en ventanas anchas o estrechas.
        """
        p = self.pantalla
        w, h = self.ancho_logico, self.alto_logico
        p.fill(FONDO)
        perdio = resultado == ResultadoNivel.CAPTURA_AGENTE
        final_juego = (motor.indice_nivel + 1) == motor.total_niveles
        escena = self.escena_derrota if perdio else self.escena_victoria

        if escena is not None:
            # Fondo tenue para rellenar las franjas si cambia la proporción.
            # La ilustración principal nunca se deforma ni se recorta.
            fondo_tenue = pygame.transform.scale(escena, (w, h))
            fondo_tenue.set_alpha(55)
            p.blit(fondo_tenue, (0, 0))
            area_arte = pygame.Rect(15, 18, w - 30, max(1, h - 144))
            self._dibujar_arte_escena(p, escena, area_arte, recortar=False)
        else:
            # Respaldo en caso de que no se hayan copiado los PNG.
            pygame.draw.rect(p, (37, 28, 23),
                             pygame.Rect(15, 18, w - 30, h - 144))
            texto = "GAME OVER" if perdio else "¡NO PASARÁS!"
            self._texto(self.f_titulo, texto, ORO,
                        centro=(w // 2, h // 2 - 60))

        # Barra de controles real: permanece legible en las dos disposiciones.
        barra = pygame.Rect(12, h - 119, w - 24, 106)
        pygame.draw.rect(p, (18, 14, 12), barra, border_radius=8)
        pygame.draw.rect(p, ORO_OSC, barra, 2, border_radius=8)

        if perdio:
            estado_texto = f"Nivel {motor.nivel_actual} · Has sido capturado"
            controles = "R: reintentar nivel    |    Esc: salir"
        elif final_juego:
            estado_texto = "¡Has superado los tres niveles!"
            controles = "R: repetir último nivel    |    Esc: salir"
        else:
            estado_texto = f"Nivel {motor.nivel_actual} superado"
            controles = "Enter: siguiente nivel    |    R: reintentar    |    Esc: salir"
        self._texto(self.f_texto, estado_texto, PERGAMINO,
                    centro=(w // 2, h - 91))
        self._texto(self.f_peq, controles, ORO,
                    centro=(w // 2, h - 57))
        self._texto(self.f_peq, "LAS MINAS DE MORIA", ORO_OSC,
                    centro=(w // 2, h - 29))

    # ---- personajes --------------------------------------------------
    @staticmethod
    def _llama(p, x, y, t, escala=1.0, fase=0):
        f = math.sin(t / 90 + fase)
        h = (10 + 2 * f) * escala
        w = 5 * escala
        pygame.draw.polygon(p, (255, 140, 30), [(x - w, y), (x, y - h), (x + w, y), (x, y + 3 * escala)])
        pygame.draw.polygon(p, (255, 220, 110), [(x - w / 2, y), (x, y - h * 0.6), (x + w / 2, y), (x, y + 2 * escala)])

    @staticmethod
    def _cargar_sprite_jugador():
        """Carga el sprite desde la raíz del repositorio; no depende del cwd.

        Si falta el archivo o PyGame no puede leerlo, se usa el dibujo
        original del explorador para que el juego siga funcionando.
        """
        ruta = Path(__file__).resolve().parent.parent / "assets" / "personajes" / "gandalf.png"
        try:
            sprite = pygame.image.load(str(ruta)).convert_alpha()
            return pygame.transform.smoothscale(sprite, (58, 58))
        except (OSError, pygame.error):
            return None

    @staticmethod
    def _cargar_sprite_agente():
        """Balrog opcional; si falta el recurso se conserva el trasgo original."""
        ruta = Path(__file__).resolve().parent.parent / "assets" / "personajes" / "balrog.png"
        try:
            sprite = pygame.image.load(str(ruta)).convert_alpha()
            return pygame.transform.smoothscale(sprite, (58, 58))
        except (OSError, pygame.error):
            return None

    def _dibujar_agente(self, p, centro):
        """La figura no afecta el movimiento ni el algoritmo del agente."""
        if self.sprite_agente is None:
            self._trasgo(p, centro)
        else:
            destino = self.sprite_agente.get_rect(center=(centro[0], centro[1] - 3))
            p.blit(self.sprite_agente, destino)

    def _dibujar_jugador(self, p, centro, t):
        """Dibuja a Gandalf si el recurso existe, o al explorador original."""
        if self.sprite_jugador is None:
            self._explorador(p, centro, t)
        else:
            destino = self.sprite_jugador.get_rect(center=(centro[0], centro[1] - 2))
            p.blit(self.sprite_jugador, destino)

    def _explorador(self, p, centro, t):
        cx, cy = centro
        pygame.draw.ellipse(p, AZUL_CAPA, (cx - 19, cy - 11, 38, 25))
        pygame.draw.ellipse(p, (24, 36, 60), (cx - 19, cy - 11, 38, 25), 3)
        pygame.draw.circle(p, (70, 98, 146), (cx, cy - 2), 11)
        pygame.draw.circle(p, (226, 190, 152), (cx, cy - 3), 6)
        pygame.draw.circle(p, (24, 36, 60), (cx, cy - 2), 11, 2)
        pygame.draw.line(p, (96, 64, 30), (cx + 12, cy - 2), (cx + 15, cy - 14), 3)  # antorcha
        self._llama(p, cx + 15, cy - 15, t)

    @staticmethod
    def _trasgo(p, centro, solo_ojos=False):
        cx, cy = centro
        if not solo_ojos:
            verde = (86, 112, 62)
            pygame.draw.polygon(p, verde, [(cx - 12, cy - 4), (cx - 25, cy - 12), (cx - 11, cy + 4)])
            pygame.draw.polygon(p, verde, [(cx + 12, cy - 4), (cx + 25, cy - 12), (cx + 11, cy + 4)])
            pygame.draw.circle(p, verde, (cx, cy), 15)
            pygame.draw.circle(p, (40, 56, 28), (cx, cy), 15, 2)
            pygame.draw.polygon(p, (40, 56, 28), [(cx - 9, cy - 8), (cx - 2, cy - 5), (cx - 9, cy - 4)])
            pygame.draw.polygon(p, (40, 56, 28), [(cx + 9, cy - 8), (cx + 2, cy - 5), (cx + 9, cy - 4)])
            pygame.draw.polygon(p, (230, 230, 210), [(cx - 6, cy + 6), (cx - 3, cy + 11), (cx, cy + 6)])
            pygame.draw.polygon(p, (230, 230, 210), [(cx + 6, cy + 6), (cx + 3, cy + 11), (cx, cy + 6)])
        pygame.draw.circle(p, (120, 10, 8), (cx - 6, cy - 2), 5)
        pygame.draw.circle(p, (120, 10, 8), (cx + 6, cy - 2), 5)
        pygame.draw.circle(p, ROJO_OJOS, (cx - 6, cy - 2), 3)
        pygame.draw.circle(p, ROJO_OJOS, (cx + 6, cy - 2), 3)

    # ---- texto -------------------------------------------------------
    def _texto(self, fuente, texto, color, centro=None, izq=None):
        """Registra el texto para dibujarlo nítido sobre la ventana real.

        Conserva las coordenadas del diseño lógico: se transforman justo al
        presentar el fotograma. Esto evita escalar los glifos como píxeles.
        """
        if centro is None and izq is None:
            return
        if fuente is self.f_titulo:
            tam = 34
        elif fuente is self.f_texto:
            tam = 20
        else:
            tam = 15
        self._textos_pendientes.append((tam, str(texto), color, centro, izq))

    # ---- dibujo por cuadro -------------------------------------------
    def dibujar(self, motor, mensaje, mostrar_ruta=False):
        self._actualizar_disposicion()
        self._textos_pendientes.clear()
        estado = motor.estado
        lab = estado.laberinto
        resultado = motor.evaluar_resultado()
        self._mostrar_final = resultado != ResultadoNivel.EN_CURSO
        if self._mostrar_final:
            self._pantalla_cinematografica(motor, resultado)
            self._presentar_escalado()
            return
        clave = (lab.obstaculos, lab.salida)
        if clave != self._clave:
            self.fondo = self._construir_fondo(lab)
            self._clave = clave

        t = pygame.time.get_ticks()
        p = self.pantalla
        p.blit(self.fondo, (0, 0))
        self._texto(self.f_titulo, "LAS MINAS DE MORIA", (0, 0, 0),
                    centro=(ANCHO // 2 + 2, 36))
        self._texto(self.f_titulo, "LAS MINAS DE MORIA", ORO,
                    centro=(ANCHO // 2, 34))
        self._texto(self.f_texto, lab.nombre, PERGAMINO,
                    centro=(ANCHO // 2, 76))

        # ruta que calculó el agente en su último turno (si la expone): brasas
        if mostrar_ruta:
            ruta = getattr(motor.agente_actual, "ultima_ruta", None) or []
            for celda in ruta:
                if celda in (estado.pos_agente, estado.pos_jugador):
                    continue
                c = self.rect(celda).center
                pygame.draw.circle(p, (120, 80, 20), c, 7)
                pygame.draw.circle(p, (255, 200, 80), c, 4)

        # personajes y llamas de pared
        for (ax, ay) in self.antorchas:
            self._llama(p, ax, ay, t, 0.9, ax)
        pc = self.rect(estado.pos_jugador).center
        ac = self.rect(estado.pos_agente).center
        self._dibujar_agente(p, ac)
        self._dibujar_jugador(p, pc, t)

        # luz y oscuridad solo sobre el tablero
        if self.luz_activa:
            tablero = pygame.Rect(MARGEN_X, TOP, CELDA * TAM, CELDA * TAM)
            osc = pygame.Surface(tablero.size, pygame.SRCALPHA)
            osc.fill((0, 0, 0, OSCURIDAD))
            fuentes = [(self.rect(lab.salida).center, self.luz_salida)]
            fuentes += [(a, self.luz_antorcha) for a in self.antorchas]
            idx = (0, 1, 2, 1)[(t // 120) % 4]
            fuentes.append((pc, self.luz_jugador[idx]))
            for (cx, cy), mascara in fuentes:
                r = mascara.get_rect(center=(cx - tablero.left, cy - tablero.top))
                osc.blit(mascara, r, special_flags=pygame.BLEND_RGBA_SUB)
            p.blit(osc, tablero.topleft)

            p.set_clip(tablero)
            for (cx, cy), brillo in ([(self.rect(lab.salida).center, self.brillo_salida)]
                                     + [(a, self.brillo_antorcha) for a in self.antorchas]
                                     + [(pc, self.brillo_jugador)]):
                p.blit(brillo, brillo.get_rect(center=(cx, cy)), special_flags=pygame.BLEND_RGB_ADD)
            p.set_clip(None)
            # Conservamos los ojos del dibujo clásico solo en modo de respaldo:
            # no se superponen sobre la cara del sprite del Balrog.
            if self.sprite_agente is None:
                self._trasgo(p, ac, solo_ojos=True)
            if self.sprite_jugador is None:
                self._llama(p, pc[0] + 15, pc[1] - 15, t)
            else:
                # Destello sutil en el bastón de Gandalf.
                pygame.draw.circle(p, (255, 224, 140),
                                   (pc[0] + 19, pc[1] - 18), 3)

        # etiquetas de la convención del enunciado: P, G, E
        self._texto(self.f_peq, "P", (200, 220, 255), centro=(pc[0] - 17, pc[1] + 20))
        self._texto(self.f_peq, "G", (255, 150, 130), centro=(ac[0] - 17, ac[1] + 20))
        er = self.rect(lab.salida)
        self._texto(self.f_peq, "E", (60, 40, 10), centro=(er.centerx, er.bottom - 16))

        self._hud(motor, mensaje)
        self._presentar_escalado()

    def _presentar_escalado(self):
        """Escala el escenario pero dibuja los textos al tamaño nativo real."""
        # PyGame 2 actualiza la superficie real al redimensionar la ventana.
        self.ventana = pygame.display.get_surface()
        w, h = self.ventana.get_size()
        factor = min(w / self.ancho_logico, h / self.alto_logico)
        ancho = max(1, round(self.ancho_logico * factor))
        alto = max(1, round(self.alto_logico * factor))
        x, y = (w - ancho) // 2, (h - alto) // 2
        self.ventana.fill(FONDO)
        imagen = (self.pantalla if (ancho, alto) == (self.ancho_logico, self.alto_logico)
                  else pygame.transform.smoothscale(self.pantalla, (ancho, alto)))
        self.ventana.blit(imagen, (x, y))

        # Los bordes de las celdas se dibujan a resolución física, incluso al
        # maximizar, para compensar el suavizado de las texturas del tablero.
        if factor >= 0.65 and not self._mostrar_final:
            izq = x + round(MARGEN_X * factor)
            arriba = y + round(TOP * factor)
            der = x + round((MARGEN_X + TAM * CELDA) * factor)
            abajo = y + round((TOP + TAM * CELDA) * factor)
            for i in range(1, TAM):
                gx = x + round((MARGEN_X + i * CELDA) * factor)
                gy = y + round((TOP + i * CELDA) * factor)
                pygame.draw.line(self.ventana, (30, 27, 24), (gx, arriba), (gx, abajo))
                pygame.draw.line(self.ventana, (30, 27, 24), (izq, gy), (der, gy))
            pygame.draw.rect(self.ventana, ORO_OSC,
                             pygame.Rect(izq, arriba, der - izq, abajo - arriba),
                             max(1, round(2 * factor)))

        # Fuentes recreadas al tamaño final: título, panel, coordenadas y P/G/E.
        # Se cachean para no recrearlas a 30 fotogramas por segundo.
        for tam, texto, color, centro, izq in self._textos_pendientes:
            puntos = max(1, round(tam * factor))
            if puntos not in self._fuentes_resolucion:
                self._fuentes_resolucion[puntos] = pygame.font.SysFont(
                    "georgia", puntos, bold=True)
            fuente = self._fuentes_resolucion[puntos]
            imagen_texto = fuente.render(texto, True, color)
            rect = imagen_texto.get_rect()
            if centro is not None:
                rect.center = (x + round(centro[0] * factor),
                               y + round(centro[1] * factor))
            if izq is not None:
                rect.midleft = (x + round(izq[0] * factor),
                                y + round(izq[1] * factor))
            self.ventana.blit(imagen_texto, rect)
        pygame.display.flip()

    def _hud(self, motor, mensaje):
        if self.modo_panel == "lateral":
            self._hud_lateral(motor, mensaje)
            return
        estado = motor.estado
        agente = motor.agente_actual
        y0 = TOP + CELDA * TAM + 30
        p = self.pantalla
        panel = pygame.Rect(MARGEN_X - 6, y0 - 12, CELDA * TAM + 12, 138)
        pygame.draw.rect(p, (34, 30, 26), panel)
        pygame.draw.rect(p, (70, 64, 56), panel, 4)
        pygame.draw.rect(p, ORO_OSC, panel.inflate(-10, -10), 1)
        x = MARGEN_X + 10
        self._texto(self.f_texto, f"NIVEL {motor.nivel_actual}/{motor.total_niveles}   TURNO {estado.numero_turno}",
                    ORO, izq=(x, y0 + 8))
        self._texto(self.f_texto, f"P {estado.pos_jugador}   G {estado.pos_agente}", PERGAMINO,
                    izq=(x + 300, y0 + 8))
        self._texto(self.f_texto, mensaje, PERGAMINO, izq=(x, y0 + 36))

        # métricas del agente (nodos explorados, modo, etc.), si las reporta
        stats = agente.obtener_estadisticas()
        detalle = ", ".join(f"{k}: {v}" for k, v in stats.items())
        linea = f"{agente.nombre}" + (f"  |  {detalle}" if detalle else "")
        if len(linea) > 68:
            linea = linea[:67] + "..."
        self._texto(self.f_peq, linea, ORO, izq=(x, y0 + 64))
        self._texto(self.f_peq, "P Gandalf   G Balrog (agente)   E salida   # muro", ORO_OSC, izq=(x, y0 + 86))
        self._texto(self.f_peq, "WASD/flechas mover  H ruta  L luz  R reintentar  Esc salir", ORO_OSC,
                    izq=(x, y0 + 106))

    def _texto_envuelto(self, texto, x, y, ancho, max_lineas=2, color=PERGAMINO):
        """Dibuja texto en un área estrecha sin que se salga del panel lateral."""
        fuente = self.f_peq
        palabras = str(texto).split()
        if not palabras:
            return y
        lineas, linea = [], ""
        for palabra in palabras:
            propuesta = f"{linea} {palabra}".strip()
            if fuente.size(propuesta)[0] <= ancho:
                linea = propuesta
            else:
                if linea:
                    lineas.append(linea)
                linea = palabra
        if linea:
            lineas.append(linea)
        if len(lineas) > max_lineas:
            lineas = lineas[:max_lineas]
            ultima = lineas[-1]
            while ultima and fuente.size(ultima + "...")[0] > ancho:
                ultima = ultima[:-1]
            lineas[-1] = ultima + "..."
        for item in lineas:
            self._texto(fuente, item, color, izq=(x, y))
            y += 22
        return y

    def _hud_lateral(self, motor, mensaje):
        """Bitácora lateral para ventanas anchas; no altera el motor del juego."""
        estado = motor.estado
        agente = motor.agente_actual
        p = self.pantalla
        panel = pygame.Rect(630, 110, 348, 560)
        pygame.draw.rect(p, (34, 30, 26), panel, border_radius=5)
        pygame.draw.rect(p, (70, 64, 56), panel, 4, border_radius=5)
        pygame.draw.rect(p, ORO_OSC, panel.inflate(-12, -12), 1, border_radius=4)
        x, ancho = 649, 308

        self._texto(self.f_texto, "BITÁCORA", ORO, izq=(x, 142))
        pygame.draw.line(p, ORO_OSC, (x, 163), (x + ancho, 163), 1)
        self._texto(self.f_peq, f"NIVEL {motor.nivel_actual}/{motor.total_niveles}", ORO,
                    izq=(x, 187))
        self._texto(self.f_peq, f"TURNO {estado.numero_turno}", PERGAMINO,
                    izq=(x, 211))
        pygame.draw.line(p, (65, 58, 45), (x, 230), (x + ancho, 230), 1)

        self._texto(self.f_peq, "GANDALF (P)", ORO, izq=(x, 251))
        self._texto(self.f_texto, str(estado.pos_jugador), PERGAMINO, izq=(x, 275))
        self._texto(self.f_peq, "BALROG (G)", ORO, izq=(x + 171, 251))
        self._texto(self.f_texto, str(estado.pos_agente), PERGAMINO, izq=(x + 171, 275))
        pygame.draw.line(p, (65, 58, 45), (x, 298), (x + ancho, 298), 1)

        self._texto(self.f_peq, "ÚLTIMO MOVIMIENTO", ORO, izq=(x, 317))
        self._texto_envuelto(mensaje, x, 342, ancho, max_lineas=2)
        pygame.draw.line(p, (65, 58, 45), (x, 377), (x + ancho, 377), 1)

        self._texto(self.f_peq, "INTELIGENCIA ARTIFICIAL", ORO, izq=(x, 398))
        self._texto_envuelto(agente.nombre, x, 420, ancho, max_lineas=2)
        stats = agente.obtener_estadisticas()
        lineas_stats = []
        for clave, etiqueta in (("modo", "Modo"), ("nodos_explorados", "Nodos explorados"),
                               ("pasos_ruta", "Pasos de ruta"), ("consultas", "Consultas"),
                               ("accion", "Acción")):
            if clave in stats and stats[clave] is not None:
                lineas_stats.append(f"{etiqueta}: {stats[clave]}")
        for i, linea in enumerate(lineas_stats[:2]):
            self._texto_envuelto(linea, x, 466 + i * 21, ancho, max_lineas=1,
                                color=ORO)
        pygame.draw.line(p, (65, 58, 45), (x, 519), (x + ancho, 519), 1)

        self._texto(self.f_peq, "CONTROLES", ORO, izq=(x, 540))
        self._texto(self.f_peq, "WASD / flechas: moverse", PERGAMINO, izq=(x, 563))
        self._texto(self.f_peq, "H: ruta     L: luz", PERGAMINO, izq=(x, 586))
        self._texto(self.f_peq, "R: reintentar   Esc: salir", PERGAMINO, izq=(x, 609))
        self._texto(self.f_peq, "P Gandalf · G Balrog · E salida", ORO_OSC,
                    izq=(x, 640))



# ======================================================================
# Ciclo principal: conecta teclado -> MotorJuego -> dibujo
# ======================================================================
RETARDO_AGENTE_MS = 350  # pausa para que se vea cada turno del agente

TECLAS = {
    pygame.K_UP: "ARRIBA", pygame.K_w: "ARRIBA",
    pygame.K_DOWN: "ABAJO", pygame.K_s: "ABAJO",
    pygame.K_LEFT: "IZQUIERDA", pygame.K_a: "IZQUIERDA",
    pygame.K_RIGHT: "DERECHA", pygame.K_d: "DERECHA",
}


def ejecutar_en_pygame(motor: MotorJuego) -> None:
    """Equivalente gráfico de interfaz.consola_basica.ejecutar_en_consola."""
    interfaz = Interfaz()
    reloj = pygame.time.Clock()
    mostrar_ruta = False
    mensaje = "Tu turno."
    mover_agente_en = None  # instante (ms) en que el agente ejecuta su turno

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                return
            if evento.type == pygame.VIDEORESIZE:
                # Los movimientos no dependen del tamaño de la ventana.
                # En el siguiente dibujo se vuelve a encajar el lienzo.
                continue
            if evento.type != pygame.KEYDOWN:
                continue

            if evento.key == pygame.K_ESCAPE:
                pygame.quit()
                return
            elif evento.key == pygame.K_h:
                mostrar_ruta = not mostrar_ruta
            elif evento.key == pygame.K_l:
                interfaz.luz_activa = not interfaz.luz_activa
            elif evento.key == pygame.K_r:
                motor.iniciar_nivel(motor.indice_nivel)
                mover_agente_en = None
                mensaje = "Nivel reiniciado. Tu turno."
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                if motor.evaluar_resultado() == ResultadoNivel.VICTORIA_HUMANO and motor.avanzar_nivel():
                    mensaje = "Nuevo nivel. Tu turno."
            elif evento.key in TECLAS:
                en_curso = motor.evaluar_resultado() == ResultadoNivel.EN_CURSO
                if not en_curso or mover_agente_en is not None or motor.estado.turno != "HUMANO":
                    continue
                accion = TECLAS[evento.key]
                if accion not in movimientos_validos(motor.estado, actor="HUMANO"):
                    mensaje = "Movimiento no permitido."
                    continue
                resultado = motor.ejecutar_turno_humano(accion)
                mensaje = f"Jugador -> {accion} {motor.estado.pos_jugador}"
                if resultado == ResultadoNivel.EN_CURSO:
                    mover_agente_en = pygame.time.get_ticks() + RETARDO_AGENTE_MS

        # turno del agente después de la pausa
        if mover_agente_en is not None and pygame.time.get_ticks() >= mover_agente_en:
            accion, resultado = motor.ejecutar_turno_agente()
            mensaje = f"Agente -> {accion} {motor.estado.pos_agente}"
            mover_agente_en = None

        interfaz.dibujar(motor, mensaje, mostrar_ruta)
        reloj.tick(30)
