"""Interfaz gráfica con PyGame. Temática: Las minas de Moria.

Usa el motor del juego (nucleo/): no tiene reglas propias, solo lee el estado
del MotorJuego y envía las acciones del jugador. Sirve para los 3 niveles.

Todo el arte se dibuja por código (sin imágenes externas):
  #  muro de piedra       .  piso de losas       E  puerta con luz
  P  explorador con antorcha                      G  trasgo (agente)

Ejecutar desde la raíz del repo:  python main_grafico.py
"""

import math
import random

import pygame

from nucleo.estado import movimientos_validos
from nucleo.mapa import ANCHO as TAM
from nucleo.motor import MotorJuego, ResultadoNivel

CELDA = 56
MARGEN_X = 40
TOP = 110
ANCHO = MARGEN_X * 2 + CELDA * TAM
ALTO = TOP + CELDA * TAM + 175

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
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        self.f_titulo = pygame.font.SysFont("georgia", 34, bold=True)
        self.f_texto = pygame.font.SysFont("georgia", 20, bold=True)
        self.f_peq = pygame.font.SysFont("georgia", 15, bold=True)
        self.luz_activa = True

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
        s = pygame.Surface((ANCHO, ALTO))
        for y in range(ALTO):  # fondo con degradado vertical
            k = 1 - 0.5 * y / ALTO
            pygame.draw.line(s, (int(22 * k), int(19 * k), int(16 * k)), (0, y), (ANCHO, y))

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

        # título
        for dx, dy, col in ((2, 2, (0, 0, 0)), (0, 0, ORO)):
            img = self.f_titulo.render("LAS MINAS DE MORIA", True, col)
            s.blit(img, img.get_rect(center=(ANCHO // 2 + dx, 34 + dy)))
        return s

    # ---- personajes --------------------------------------------------
    @staticmethod
    def _llama(p, x, y, t, escala=1.0, fase=0):
        f = math.sin(t / 90 + fase)
        h = (10 + 2 * f) * escala
        w = 5 * escala
        pygame.draw.polygon(p, (255, 140, 30), [(x - w, y), (x, y - h), (x + w, y), (x, y + 3 * escala)])
        pygame.draw.polygon(p, (255, 220, 110), [(x - w / 2, y), (x, y - h * 0.6), (x + w / 2, y), (x, y + 2 * escala)])

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
        img = fuente.render(texto, True, color)
        r = img.get_rect()
        if centro:
            r.center = centro
        if izq:
            r.midleft = izq
        self.pantalla.blit(img, r)

    # ---- dibujo por cuadro -------------------------------------------
    def dibujar(self, motor, mensaje, mostrar_ruta=False):
        estado = motor.estado
        lab = estado.laberinto
        resultado = motor.evaluar_resultado()
        clave = (lab.obstaculos, lab.salida)
        if clave != self._clave:
            self.fondo = self._construir_fondo(lab)
            self._clave = clave

        t = pygame.time.get_ticks()
        p = self.pantalla
        p.blit(self.fondo, (0, 0))
        self._texto(self.f_texto, lab.nombre, PERGAMINO, centro=(ANCHO // 2, 76))

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
        self._trasgo(p, ac)
        self._explorador(p, pc, t)

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
            self._trasgo(p, ac, solo_ojos=True)   # los ojos se ven aun en la oscuridad
            self._llama(p, pc[0] + 15, pc[1] - 15, t)

        # etiquetas de la convención del enunciado: P, G, E
        self._texto(self.f_peq, "P", (200, 220, 255), centro=(pc[0] - 17, pc[1] + 20))
        self._texto(self.f_peq, "G", (255, 150, 130), centro=(ac[0] - 17, ac[1] + 20))
        er = self.rect(lab.salida)
        self._texto(self.f_peq, "E", (60, 40, 10), centro=(er.centerx, er.bottom - 16))

        self._hud(motor, mensaje)
        if resultado != ResultadoNivel.EN_CURSO:
            self._final(motor, resultado)
        pygame.display.flip()

    def _hud(self, motor, mensaje):
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
        self._texto(self.f_peq, "P explorador   G trasgo (agente)   E salida   # muro", ORO_OSC, izq=(x, y0 + 86))
        self._texto(self.f_peq, "WASD/flechas mover  H ruta  L luz  R reintentar  Esc salir", ORO_OSC,
                    izq=(x, y0 + 106))

    def _final(self, motor, resultado):
        p = self.pantalla
        cy = TOP + CELDA * TAM // 2
        velo = pygame.Surface((ANCHO, 150))
        velo.set_alpha(215)
        velo.fill((8, 6, 4))
        p.blit(velo, (0, cy - 75))
        pygame.draw.line(p, ORO_OSC, (MARGEN_X, cy - 75), (ANCHO - MARGEN_X, cy - 75), 2)
        pygame.draw.line(p, ORO_OSC, (MARGEN_X, cy + 75), (ANCHO - MARGEN_X, cy + 75), 2)
        if resultado == ResultadoNivel.CAPTURA_AGENTE:
            self._texto(self.f_titulo, "TE ATRAPARON", (230, 70, 55), centro=(ANCHO // 2, cy - 18))
            self._texto(self.f_texto, "R: reintentar el nivel", PERGAMINO, centro=(ANCHO // 2, cy + 30))
        elif motor.indice_nivel + 1 < motor.total_niveles:
            self._texto(self.f_titulo, "NIVEL SUPERADO", ORO, centro=(ANCHO // 2, cy - 18))
            self._texto(self.f_texto, "ENTER: siguiente nivel", PERGAMINO, centro=(ANCHO // 2, cy + 30))
        else:
            self._texto(self.f_titulo, "HAS ESCAPADO DE MORIA", ORO, centro=(ANCHO // 2, cy - 18))
            self._texto(self.f_texto, "Completaste los 3 niveles   (R: repetir este nivel, Esc: salir)",
                        PERGAMINO, centro=(ANCHO // 2, cy + 30))


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
