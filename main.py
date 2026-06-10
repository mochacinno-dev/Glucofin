"""
Glucofin — Detector de riesgo de diabetes
UI rediseñada: tipografía Inter/sistema, tema violeta claro, tarjetas con sombra,
secciones bien espaciadas y fuente cargada correctamente desde el sistema.
"""
from __future__ import annotations
import json
import datetime
import statistics
import sys
import os
from dataclasses import dataclass, field
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFrame, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QCheckBox,
    QRadioButton, QComboBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QScrollArea, QWidget,
    QSizePolicy, QSpacerItem, QStackedWidget, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import (
    QFont, QFontDatabase, QColor, QPalette, QPixmap, QPainter,
    QLinearGradient, QBrush, QPen, QIcon, QFontMetrics
)

CONSTANTE_MOLAR_GLUCOSA = 18.01559

C = {
    "bg":          "#F4EEFF",   # fondo general
    "surface":     "#FDFAFF",   # tarjetas / fondos blancos
    "surface2":    "#EFE5FF",   # superficies secundarias
    "border":      "#D9C2FF",   # bordes sutiles
    "border2":     "#C4A8F5",   # bordes en hover / foco
    "primary":     "#7B2FBE",   # violeta principal
    "primary_l":   "#9D50FF",   # violeta claro (accents)
    "primary_d":   "#5A189A",   # violeta oscuro
    "accent":      "#C77DFF",   # lila suave
    "warn":        "#F77F00",   # naranja advertencia
    "danger":      "#E63946",   # rojo peligro
    "ok":          "#2A9D5C",   # verde éxito
    "text":        "#1E1E2E",   # texto principal
    "text2":       "#6E6A85",   # texto secundario
    "text_inv":    "#FFFFFF",   # texto sobre fondo oscuro
    "tab_sel":     "#7B2FBE",   # tab seleccionado
    "input_bg":    "#FFFFFF",
    "header_grad1":"#6A0DAD",
    "header_grad2":"#9D50FF",
    "shadow":      "#7B2FBE",
}

def setup_fonts() -> dict[str, QFont]:
    """
    Carga Inter desde el sistema si está disponible,
    de lo contrario usa la mejor fuente sans-serif del sistema.
    Retorna un dict de QFont para los distintos roles tipográficos.
    """
    available = QFontDatabase.families()

    # Preferencia de fuentes sans-serif, en orden
    candidates = ["Inter", "Inter Display", "Noto Sans", "Liberation Sans",
                  "DejaVu Sans", "Roboto", "Open Sans", "Ubuntu", "Cantarell",
                  "Segoe UI", "Helvetica Neue", "Arial", "Montserrat"]

    chosen = "Arial"  # fallback universal
    for name in candidates:
        if name in available:
            chosen = name
            break

    mono_candidates = ["JetBrains Mono", "Fira Code", "Fira Mono",
                       "Source Code Pro", "Noto Mono", "Liberation Mono",
                       "DejaVu Sans Mono", "Courier New"]
    chosen_mono = "Courier New"
    for name in mono_candidates:
        if name in available:
            chosen_mono = name
            break

    def f(size: int, weight=QFont.Normal, italic=False, family=chosen) -> QFont:
        font = QFont(family, size)
        font.setWeight(weight)
        font.setItalic(italic)
        font.setHintingPreference(QFont.PreferFullHinting)
        return font

    return {
        "family":  chosen,
        "mono":    chosen_mono,
        "display": f(22, QFont.Bold),
        "h1":      f(16, QFont.Bold),
        "h2":      f(13, QFont.DemiBold),
        "h3":      f(11, QFont.DemiBold),
        "body":    f(10),
        "body_m":  f(10, QFont.Medium),
        "small":   f(9),
        "small_m": f(9, QFont.Medium),
        "label":   f(9, QFont.DemiBold),
        "mono_f":  f(10, family=chosen_mono),
        "caption": f(8, italic=True),
    }


@dataclass
class LecturaGlucosa:
    valor_mgdl: float
    fecha_hora: datetime.datetime = field(default_factory=datetime.datetime.now)

    def a_diccionario(self):
        return {"valor_mgdl": self.valor_mgdl,
                "fecha_hora": self.fecha_hora.isoformat()}

@dataclass
class Paciente:
    glucosa_ayunas:     float = 0.0
    glucosa_post_ogtt:  float = 0.0
    hba1c:              float = 0.0
    insulina_ayunas:    float = 0.0
    peso:               float = 0.0
    altura:             float = 0.0
    cintura:            float = 0.0
    sexo:               str   = "M"
    edad:               int   = 0
    ejercicio_diario:   bool  = False
    frutas_verduras:    bool  = False
    hipertension:       bool  = False
    antecedentes_glucosa: bool = False
    antecedentes_familiares: int = 0
    historial: list[LecturaGlucosa] = field(default_factory=list)

    def a_diccionario(self):
        return {
            "glucosa_ayunas": self.glucosa_ayunas,
            "glucosa_post_ogtt": self.glucosa_post_ogtt,
            "hba1c": self.hba1c,
            "insulina_ayunas": self.insulina_ayunas,
            "peso": self.peso,
            "altura": self.altura,
            "cintura": self.cintura,
            "sexo": self.sexo,
            "edad": self.edad,
            "ejercicio_diario": self.ejercicio_diario,
            "frutas_verduras": self.frutas_verduras,
            "hipertension": self.hipertension,
            "antecedentes_glucosa": self.antecedentes_glucosa,
            "antecedentes_familiares": self.antecedentes_familiares,
            "historial": [l.a_diccionario() for l in self.historial],
        }


def mgdl_a_mmoll(v): return round(v / CONSTANTE_MOLAR_GLUCOSA, 3)
def mmoll_a_mgdl(v): return round(v * CONSTANTE_MOLAR_GLUCOSA, 2)

def calcular_eag_mgdl(h):
    if not 3.0 <= h <= 20.0:
        raise ValueError("HbA1c fuera de rango biológico (3–20%).")
    return round(28.7 * h - 46.7, 2)

def calcular_homa_ir(g, i):
    if g <= 0 or i <= 0:
        raise ValueError("Glucosa e insulina deben ser > 0.")
    return round(i * g / 405.0, 2)

def interpretar_homa(v):
    if v < 1.9: return "Sensibilidad normal a la insulina"
    if v < 2.9: return "Resistencia leve a la insulina"
    return "Resistencia severa a la insulina"

def clasificar_glucosa_ayunas(v):
    if v < 100: return "Normal"
    if v <= 125: return "Prediabetes"
    return "Diabetes"

def clasificar_ogtt(v):
    if v < 140: return "Normal"
    if v <= 199: return "Prediabetes"
    return "Diabetes"

def clasificar_hba1c(v):
    if v < 5.7: return "Normal"
    if v <= 6.4: return "Prediabetes"
    return "Diabetes"

def calcular_imc(p, a):
    if a <= 0: raise ZeroDivisionError("Altura debe ser > 0.")
    if p <= 0: raise ValueError("Peso debe ser > 0.")
    return round(p / a ** 2, 2)

def clasificar_imc(v):
    if v < 18.5: return "Bajo peso"
    if v < 25.0: return "Normal"
    if v < 30.0: return "Sobrepeso"
    return "Obesidad"

def calcular_findrisc(p):
    pts = 0
    if p.edad < 45: pts += 0
    elif p.edad <= 54: pts += 2
    elif p.edad <= 64: pts += 3
    else: pts += 4
    try:
        imc = calcular_imc(p.peso, p.altura)
        if imc < 25: pts += 0
        elif imc <= 30: pts += 1
        else: pts += 3
    except: pts += 1
    if p.sexo.upper() == "M":
        if p.cintura < 94: pts += 0
        elif p.cintura <= 102: pts += 1
        else: pts += 3
    else:
        if p.cintura < 80: pts += 0
        elif p.cintura <= 88: pts += 1
        else: pts += 3
    if not p.ejercicio_diario: pts += 2
    if not p.frutas_verduras: pts += 1
    if p.hipertension: pts += 2
    if p.antecedentes_glucosa: pts += 5
    if p.antecedentes_familiares == 1: pts += 3
    elif p.antecedentes_familiares == 2: pts += 5
    return min(pts, 26)

def interpretar_findrisc(pts):
    if pts <= 7:  return "Riesgo bajo (~1% en 10 años)"
    if pts <= 11: return "Ligeramente elevado (~4%)"
    if pts <= 14: return "Moderado (~17%)"
    if pts <= 20: return "Alto (~33%)"
    return "Muy alto (~50%)"

def calcular_cv(lecturas):
    if len(lecturas) < 2: return None
    vals = [l.valor_mgdl for l in lecturas]
    mu = statistics.mean(vals)
    if mu == 0: return None
    return round(statistics.stdev(vals) / mu * 100, 2)

def evaluar_riesgo(paciente):
    homa = None
    if paciente.insulina_ayunas > 0 and paciente.glucosa_ayunas > 0:
        try: homa = calcular_homa_ir(paciente.glucosa_ayunas, paciente.insulina_ayunas)
        except: pass
    findrisc = calcular_findrisc(paciente)
    tiene_glucosa = any([paciente.glucosa_ayunas > 0,
                         paciente.glucosa_post_ogtt > 0,
                         paciente.hba1c > 0])
    detalle = {
        "puntaje_findrisc":         findrisc,
        "interpretacion_findrisc":  interpretar_findrisc(findrisc),
        "homa_ir":                  homa,
        "interpretacion_homa":      interpretar_homa(homa) if homa else "Requiere glucosa e insulina en ayunas",
        "clase_glucosa_ayunas":     clasificar_glucosa_ayunas(paciente.glucosa_ayunas) if paciente.glucosa_ayunas > 0 else "—",
        "clase_ogtt":               clasificar_ogtt(paciente.glucosa_post_ogtt) if paciente.glucosa_post_ogtt > 0 else "—",
        "clase_hba1c":              clasificar_hba1c(paciente.hba1c) if paciente.hba1c > 0 else "—",
        "imc":                      calcular_imc(paciente.peso, paciente.altura) if paciente.peso > 0 and paciente.altura > 0 else None,
        "clase_imc":                clasificar_imc(calcular_imc(paciente.peso, paciente.altura)) if paciente.peso > 0 and paciente.altura > 0 else "—",
        "cv":                       calcular_cv(paciente.historial) if len(paciente.historial) >= 2 else None,
    }
    if not tiene_glucosa:
        if findrisc >= 15: return {"nivel": "muy_alto", "estado": "Riesgo muy alto de diabetes tipo 2",  "accion": "Intervención urgente: cambia hábitos y visita a tu médico.", "detalle": detalle}
        if findrisc >= 12: return {"nivel": "alto",     "estado": "Riesgo elevado de diabetes tipo 2",   "accion": "Mejora tu estilo de vida: dieta, ejercicio y controles.", "detalle": detalle}
        if findrisc >= 7:  return {"nivel": "moderado", "estado": "Riesgo moderado de diabetes tipo 2",  "accion": "Adopta hábitos saludables para prevenir progresión.", "detalle": detalle}
        return               {"nivel": "bajo",      "estado": "Bajo riesgo de diabetes",            "accion": "Mantén tus hábitos y realiza controles anuales.", "detalle": detalle}
    if (paciente.hba1c >= 6.5 and paciente.hba1c > 0) or (paciente.glucosa_ayunas >= 126 and paciente.glucosa_ayunas > 0):
        return {"nivel": "diabetes",  "estado": "Diabetes confirmada",                "accion": "Consulta a tu médico de inmediato para confirmación y tratamiento.", "detalle": detalle}
    if (5.7 <= paciente.hba1c <= 6.4) or (100 <= paciente.glucosa_ayunas <= 125) or (140 <= paciente.glucosa_post_ogtt <= 199):
        return {"nivel": "prediabetes","estado": "Prediabetes detectada",             "accion": "Riesgo alto. Prioriza dieta, ejercicio y seguimiento médico.", "detalle": detalle}
    if findrisc >= 15: return {"nivel": "muy_alto",  "estado": "Riesgo muy alto de diabetes tipo 2",  "accion": "Intervención urgente: cambia hábitos y visita a tu médico.", "detalle": detalle}
    if findrisc >= 12: return {"nivel": "alto",      "estado": "Riesgo elevado de diabetes tipo 2",   "accion": "Mejora tu estilo de vida: dieta, ejercicio y controles.", "detalle": detalle}
    if homa and homa >= 2.9: return {"nivel": "insulina_severa", "estado": "Resistencia severa a la insulina", "accion": "Optimiza dieta, ejercicio y sueño. Consulta a un endocrinólogo.", "detalle": detalle}
    if homa and homa >= 1.9: return {"nivel": "insulina_leve",  "estado": "Resistencia leve a la insulina",   "accion": "Adopta hábitos saludables para prevenir prediabetes.", "detalle": detalle}
    return {"nivel": "bajo", "estado": "Bajo riesgo de diabetes", "accion": "Mantén tus hábitos y realiza controles anuales.", "detalle": detalle}

# Colores por nivel de riesgo
NIVEL_COLORES = {
    "bajo":            (C["ok"],      "#E8F8EF", "✅"),
    "moderado":        (C["warn"],    "#FFF4E5", "⚠️"),
    "alto":            ("#D4760A",    "#FFF0D6", "🟠"),
    "muy_alto":        (C["danger"],  "#FFF0F0", "🔶"),
    "prediabetes":     ("#B45309",    "#FFF3CD", "⚠️"),
    "diabetes":        (C["danger"],  "#FFE8E8", "⛔"),
    "insulina_leve":   (C["warn"],    "#FFF4E5", "🟡"),
    "insulina_severa": ("#D4760A",    "#FFF0D6", "🔸"),
}


def v(campo, default=0.0):
    try: return float(campo.text().strip().replace(",", "."))
    except: return default

def vi(campo, default=0):
    try: return int(campo.text().strip())
    except: return default

def shadow(widget, color=C["shadow"], radius=18, dx=0, dy=3, alpha=35):
    eff = QGraphicsDropShadowEffect()
    eff.setBlurRadius(radius)
    eff.setOffset(dx, dy)
    col = QColor(color)
    col.setAlpha(alpha)
    eff.setColor(col)
    widget.setGraphicsEffect(eff)
    return eff


class Card(QFrame):
    """Tarjeta con borde redondeado y sombra sutil."""
    def __init__(self, parent=None, padding=16):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setStyleSheet(f"""
            QFrame#Card {{
                background-color: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 12px;
            }}
        """)
        shadow(self)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(padding, padding, padding, padding)
        self._layout.setSpacing(10)

    def add(self, widget): self._layout.addWidget(widget)
    def addLayout(self, layout): self._layout.addLayout(layout)
    def layout(self): return self._layout


class SectionTitle(QLabel):
    """Título de sección con línea de color."""
    def __init__(self, text: str, fonts: dict, emoji="", parent=None):
        label = f"{emoji}  {text}" if emoji else text
        super().__init__(label, parent)
        self.setFont(fonts["h2"])
        self.setStyleSheet(f"""
            color: {C['primary_d']};
            padding-bottom: 6px;
            border-bottom: 2px solid {C['accent']};
            margin-bottom: 4px;
        """)


class FieldLabel(QLabel):
    def __init__(self, text, fonts, parent=None):
        super().__init__(text, parent)
        self.setFont(fonts["label"])
        self.setStyleSheet(f"color: {C['text2']}; letter-spacing: 0.4px;")


class ValueLabel(QLabel):
    def __init__(self, text="—", fonts=None, parent=None):
        super().__init__(text, parent)
        if fonts:
            self.setFont(fonts["body_m"])
        self.setStyleSheet(f"color: {C['text']};")


class StyledInput(QLineEdit):
    def __init__(self, placeholder="", width=110, parent=None):
        super().__init__(parent)
        if placeholder:
            self.setPlaceholderText(placeholder)
        self.setFixedWidth(width)
        self.setStyleSheet(f"""
            QLineEdit {{
                background: {C['input_bg']};
                border: 1.5px solid {C['border']};
                border-radius: 7px;
                padding: 5px 10px;
                color: {C['text']};
                selection-background-color: {C['accent']};
            }}
            QLineEdit:focus {{
                border-color: {C['primary_l']};
                background: #FEFCFF;
            }}
            QLineEdit:hover {{
                border-color: {C['border2']};
            }}
        """)


class PrimaryButton(QPushButton):
    def __init__(self, text, icon_txt="", parent=None):
        super().__init__(f"{icon_txt}  {text}" if icon_txt else text, parent)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {C['primary']};
                color: {C['text_inv']};
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }}
            QPushButton:hover {{
                background-color: {C['primary_d']};
            }}
            QPushButton:pressed {{
                background-color: {C['primary_d']};
                padding: 9px 19px 7px 21px;
            }}
        """)


class SecondaryButton(QPushButton):
    def __init__(self, text, icon_txt="", parent=None):
        super().__init__(f"{icon_txt}  {text}" if icon_txt else text, parent)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {C['primary']};
                border: 1.5px solid {C['primary_l']};
                border-radius: 8px;
                padding: 7px 18px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {C['surface2']};
            }}
        """)


class StyledCheck(QCheckBox):
    def __init__(self, text, fonts, parent=None):
        super().__init__(text, parent)
        self.setFont(fonts["body"])
        self.setStyleSheet(f"""
            QCheckBox {{
                color: {C['text']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border: 1.5px solid {C['border2']};
                border-radius: 5px;
                background: {C['input_bg']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {C['primary']};
                border-color: {C['primary']};
                image: none;
            }}
            QCheckBox::indicator:hover {{
                border-color: {C['primary_l']};
            }}
        """)


class StyledRadio(QRadioButton):
    def __init__(self, text, fonts, parent=None):
        super().__init__(text, parent)
        self.setFont(fonts["body"])
        self.setStyleSheet(f"""
            QRadioButton {{
                color: {C['text']};
                spacing: 8px;
            }}
            QRadioButton::indicator {{
                width: 16px; height: 16px;
                border: 1.5px solid {C['border2']};
                border-radius: 8px;
                background: {C['input_bg']};
            }}
            QRadioButton::indicator:checked {{
                background-color: {C['primary']};
                border-color: {C['primary']};
                border-width: 3px;
            }}
        """)


class UnitTag(QLabel):
    """Etiqueta de unidad pequeña junto a un input."""
    def __init__(self, text, fonts, parent=None):
        super().__init__(text, parent)
        self.setFont(fonts["small"])
        self.setStyleSheet(f"""
            color: {C['text2']};
            background: {C['surface2']};
            border: 1px solid {C['border']};
            border-radius: 5px;
            padding: 3px 7px;
        """)


class StatusBanner(QFrame):
    """Banner de resultado de evaluación con color dinámico."""
    def __init__(self, fonts, parent=None):
        super().__init__(parent)
        self.setObjectName("StatusBanner")
        self.fonts = fonts
        self._setup()

    def _setup(self):
        shadow(self, radius=22, alpha=40)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(8)

        top = QHBoxLayout()
        self.emoji_lbl = QLabel("—")
        self.emoji_lbl.setFont(QFont(self.fonts["family"], 28))
        self.estado_lbl = QLabel("Genera tu evaluación")
        self.estado_lbl.setFont(self.fonts["h1"])
        self.estado_lbl.setWordWrap(True)
        top.addWidget(self.emoji_lbl)
        top.addWidget(self.estado_lbl, 1)

        self.accion_lbl = QLabel("")
        self.accion_lbl.setFont(self.fonts["body"])
        self.accion_lbl.setWordWrap(True)

        lay.addLayout(top)
        lay.addWidget(self.accion_lbl)

    def update(self, nivel: str, estado: str, accion: str):
        color, bg, emoji = NIVEL_COLORES.get(nivel, (C["primary"], C["surface2"], "ℹ️"))
        self.setStyleSheet(f"""
            QFrame#StatusBanner {{
                background-color: {bg};
                border: 1.5px solid {color};
                border-radius: 12px;
                border-left: 5px solid {color};
            }}
        """)
        self.emoji_lbl.setText(emoji)
        self.estado_lbl.setText(estado)
        self.estado_lbl.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.accion_lbl.setText(accion)
        self.accion_lbl.setStyleSheet(f"color: {C['text2']};")


class GlucofinApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.paciente = Paciente()
        self.fonts = setup_fonts()

        self.setWindowTitle("Glucofin — Detección de Riesgo de Diabetes")
        self.setMinimumSize(860, 640)
        self.resize(960, 720)

        self._apply_global_style()
        self._build_ui()

    def _apply_global_style(self):
        f = self.fonts
        QApplication.setFont(f["body"])

        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {C['bg']};
                color: {C['text']};
                font-family: "{f['family']}";
            }}
            QTabWidget::pane {{
                background: {C['bg']};
                border: none;
            }}
            QTabBar {{
                background: {C['surface']};
            }}
            QTabBar::tab {{
                background: {C['surface']};
                color: {C['text2']};
                padding: 10px 18px;
                border: none;
                border-bottom: 2px solid transparent;
                font-family: "{f['family']}";
                font-size: 10pt;
                font-weight: 500;
                min-width: 100px;
            }}
            QTabBar::tab:selected {{
                color: {C['primary']};
                border-bottom: 2px solid {C['primary']};
                background: {C['bg']};
            }}
            QTabBar::tab:hover:!selected {{
                color: {C['primary_l']};
                background: {C['surface2']};
            }}
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: {C['surface2']};
                width: 7px;
                border-radius: 3px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {C['accent']};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QGroupBox {{
                font-family: "{f['family']}";
                font-weight: 600;
                color: {C['primary_d']};
                border: 1.5px solid {C['border']};
                border-radius: 10px;
                margin-top: 14px;
                padding-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                background: {C['bg']};
            }}
            QTableWidget {{
                background: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 8px;
                gridline-color: {C['border']};
                color: {C['text']};
                selection-background-color: {C['surface2']};
                selection-color: {C['primary_d']};
            }}
            QTableWidget::item {{
                padding: 5px 8px;
            }}
            QHeaderView::section {{
                background-color: {C['surface2']};
                color: {C['primary_d']};
                font-weight: 600;
                font-size: 9pt;
                padding: 6px 10px;
                border: none;
                border-right: 1px solid {C['border']};
                border-bottom: 1px solid {C['border2']};
            }}
            QComboBox {{
                background: {C['input_bg']};
                border: 1.5px solid {C['border']};
                border-radius: 7px;
                padding: 5px 10px;
                color: {C['text']};
                min-width: 160px;
            }}
            QComboBox:focus {{
                border-color: {C['primary_l']};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background: {C['surface']};
                border: 1px solid {C['border2']};
                selection-background-color: {C['surface2']};
                color: {C['text']};
            }}
            QMessageBox {{
                background: {C['surface']};
                color: {C['text']};
            }}
        """)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_lay = QVBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        root_lay.addWidget(self._make_header())

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        root_lay.addWidget(self.tabs, 1)

        self._tab_personal()
        self._tab_laboratorio()
        self._tab_historial()
        self._tab_reporte()
        self._tab_herramientas()

        root_lay.addWidget(self._make_footer())

    def _make_header(self):
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet(f"""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {C['header_grad1']},
                stop:1 {C['header_grad2']}
            );
        """)
        lay = QHBoxLayout(header)
        lay.setContentsMargins(24, 0, 24, 0)

        dot = QLabel("●")
        dot.setFont(QFont(self.fonts["family"], 10))
        dot.setStyleSheet("color: rgba(255,255,255,0.5); letter-spacing: 2px;")

        title = QLabel("Glucofin")
        title.setFont(self.fonts["display"])
        title.setStyleSheet("color: white; letter-spacing: -0.5px;")

        sep = QLabel("·")
        sep.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 18pt; margin: 0 8px;")

        sub = QLabel("Detección de riesgo de diabetes")
        sub.setFont(self.fonts["body"])
        sub.setStyleSheet("color: rgba(255,255,255,0.75);")

        badge = QLabel("FINDRISC · OMS")
        badge.setFont(self.fonts["caption"])
        badge.setStyleSheet(f"""
            color: rgba(255,255,255,0.9);
            background: rgba(255,255,255,0.18);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 10px;
            padding: 2px 10px;
        """)

        lay.addWidget(dot)
        lay.addWidget(title)
        lay.addWidget(sep)
        lay.addWidget(sub)
        lay.addStretch()
        lay.addWidget(badge)
        return header

    def _make_footer(self):
        footer = QFrame()
        footer.setFixedHeight(32)
        footer.setStyleSheet(f"background: {C['surface']}; border-top: 1px solid {C['border']};")
        lay = QHBoxLayout(footer)
        lay.setContentsMargins(16, 0, 16, 0)

        lbl = QLabel(
            "⚕  Glucofin utiliza el cuestionario FINDRISC validado por la OMS. "
            "No reemplaza el diagnóstico médico."
        )
        lbl.setFont(self.fonts["caption"])
        lbl.setStyleSheet(f"color: {C['text2']};")
        lay.addWidget(lbl)
        lay.addStretch()

        ver = QLabel("v2.0")
        ver.setFont(self.fonts["caption"])
        ver.setStyleSheet(f"color: {C['accent']};")
        lay.addWidget(ver)
        return footer

    def _field_row(self, grid, row, label_txt, unit_txt="", placeholder="", width=110):
        lbl = FieldLabel(label_txt, self.fonts)
        inp = StyledInput(placeholder, width)
        grid.addWidget(lbl, row, 0, Qt.AlignVCenter)
        grid.addWidget(inp, row, 1, Qt.AlignVCenter)
        if unit_txt:
            utag = UnitTag(unit_txt, self.fonts)
            grid.addWidget(utag, row, 2, Qt.AlignVCenter)
        return inp

    def _tab_personal(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        scroll.setWidget(inner)
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(16)

        card_med = Card()
        card_med.add(SectionTitle("Medidas corporales", self.fonts, "📏"))

        g = QGridLayout()
        g.setColumnStretch(3, 1)
        g.setHorizontalSpacing(12)
        g.setVerticalSpacing(10)

        self.e_edad    = self._field_row(g, 0, "Edad",    "años",       "ej: 42", 90)
        self.e_peso    = self._field_row(g, 1, "Peso",    "kg",         "ej: 75", 90)
        self.e_altura  = self._field_row(g, 2, "Altura",  "m",          "ej: 1.72", 90)
        self.e_cintura = self._field_row(g, 3, "Cintura", "cm",         "ej: 88", 90)

        sexo_lbl = FieldLabel("Sexo biológico", self.fonts)
        self.cb_sexo = QComboBox()
        self.cb_sexo.addItems(["M — Masculino", "F — Femenino"])
        g.addWidget(sexo_lbl, 4, 0, Qt.AlignVCenter)
        g.addWidget(self.cb_sexo, 4, 1, 1, 2, Qt.AlignVCenter)

        card_med.addLayout(g)

        self.lbl_imc_preview = QLabel("")
        self.lbl_imc_preview.setFont(self.fonts["small_m"])
        self.lbl_imc_preview.setStyleSheet(f"color: {C['ok']}; padding: 4px 0;")
        for inp in [self.e_peso, self.e_altura]:
            inp.textChanged.connect(self._preview_imc)
        card_med.add(self.lbl_imc_preview)
        lay.addWidget(card_med)

        card_hab = Card()
        card_hab.add(SectionTitle("Hábitos y antecedentes", self.fonts, "🏃"))

        self.chk_ejercicio  = StyledCheck("Realiza ejercicio ≥ 30 min al día",               self.fonts)
        self.chk_frutas     = StyledCheck("Consume frutas o verduras a diario",               self.fonts)
        self.chk_hipertension = StyledCheck("Toma medicación para la hipertensión",           self.fonts)
        self.chk_glucosa_alta = StyledCheck("Alguna vez le diagnosticaron glucosa elevada",    self.fonts)

        for chk in [self.chk_ejercicio, self.chk_frutas,
                    self.chk_hipertension, self.chk_glucosa_alta]:
            card_hab.add(chk)

        fam_lbl = FieldLabel("Antecedentes familiares de diabetes:", self.fonts)
        self.rad_fam0 = StyledRadio("Ninguno",                                       self.fonts)
        self.rad_fam1 = StyledRadio("Familiares de 2.° grado (abuelos, tíos…)",      self.fonts)
        self.rad_fam2 = StyledRadio("Familiares de 1.° grado (padres, hermanos…)",   self.fonts)
        self.rad_fam0.setChecked(True)

        card_hab.add(fam_lbl)
        for r in [self.rad_fam0, self.rad_fam1, self.rad_fam2]:
            card_hab.add(r)
        lay.addWidget(card_hab)

        btn_row = QHBoxLayout()
        btn = PrimaryButton("Guardar y calcular FINDRISC", "🔄")
        btn.clicked.connect(self._guardar_personal)
        btn_row.addStretch()
        btn_row.addWidget(btn)
        lay.addLayout(btn_row)

        self.lbl_personal_status = QLabel("")
        self.lbl_personal_status.setFont(self.fonts["small_m"])
        self.lbl_personal_status.setWordWrap(True)
        lay.addWidget(self.lbl_personal_status)
        lay.addStretch()

        self.tabs.addTab(scroll, "👤  Personal")

    def _tab_laboratorio(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        scroll.setWidget(inner)
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(16)

        # Nota informativa
        nota = QLabel("  Deja en blanco los campos que no tengas disponibles.")
        nota.setFont(self.fonts["small"])
        nota.setStyleSheet(f"""
            background: {C['surface2']};
            border-left: 3px solid {C['accent']};
            border-radius: 4px;
            padding: 8px 12px;
            color: {C['text2']};
        """)
        lay.addWidget(nota)

        card = Card()
        card.add(SectionTitle("Resultados de sangre", self.fonts, "🧪"))
        g = QGridLayout()
        g.setColumnStretch(3, 1)
        g.setHorizontalSpacing(12)
        g.setVerticalSpacing(10)

        self.e_gl_ayunas = self._field_row(g, 0, "Glucosa en ayunas",    "mg/dL", "70–125")
        self.e_ogtt      = self._field_row(g, 1, "Glucosa post-OGTT (2h)","mg/dL", "< 140")
        self.e_hba1c     = self._field_row(g, 2, "HbA1c",                "%",     "4.0–6.4")
        self.e_insulina  = self._field_row(g, 3, "Insulina en ayunas",   "µIU/mL","2–25")

        card.addLayout(g)
        lay.addWidget(card)

        # Resultado en tiempo real
        self.card_lab_result = Card()
        self.card_lab_result.add(SectionTitle("Clasificación", self.fonts, "📊"))
        self.lbl_lab_detalle = QLabel("—  Guarda los datos para ver la clasificación.")
        self.lbl_lab_detalle.setFont(self.fonts["body"])
        self.lbl_lab_detalle.setStyleSheet(f"color: {C['text2']};")
        self.lbl_lab_detalle.setWordWrap(True)
        self.card_lab_result.add(self.lbl_lab_detalle)
        lay.addWidget(self.card_lab_result)

        btn_row = QHBoxLayout()
        btn = PrimaryButton("Guardar análisis clínicos", "✓")
        btn.clicked.connect(self._guardar_lab)
        btn_row.addStretch()
        btn_row.addWidget(btn)
        lay.addLayout(btn_row)
        lay.addStretch()

        self.tabs.addTab(scroll, "🧪  Clínicos")

    def _tab_historial(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        scroll.setWidget(inner)
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(16)

        # Agregar lectura
        card_add = Card()
        card_add.add(SectionTitle("Nueva lectura", self.fonts, "➕"))
        row = QHBoxLayout()
        lbl = FieldLabel("Glucosa (mg/dL):", self.fonts)
        self.e_lectura = StyledInput("ej: 105", 100)
        btn_add = PrimaryButton("Registrar lectura")
        btn_add.clicked.connect(self._agregar_lectura)
        row.addWidget(lbl)
        row.addWidget(self.e_lectura)
        row.addSpacing(8)
        row.addWidget(btn_add)
        row.addStretch()
        card_add.addLayout(row)
        lay.addWidget(card_add)

        # Tabla
        card_tabla = Card()
        card_tabla.add(SectionTitle("Registro de mediciones", self.fonts, "📈"))
        self.tabla = QTableWidget(0, 3)
        self.tabla.setHorizontalHeaderLabels(["Fecha y hora", "mg/dL", "mmol/L"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setMinimumHeight(200)
        card_tabla.add(self.tabla)

        self.lbl_cv = QLabel("")
        self.lbl_cv.setFont(self.fonts["body_m"])
        card_tabla.add(self.lbl_cv)
        lay.addWidget(card_tabla)
        lay.addStretch()

        self.tabs.addTab(scroll, "📈  Historial")

    def _tab_reporte(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        scroll.setWidget(inner)
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(16)

        # Botones de acción
        btn_row = QHBoxLayout()
        btn_gen  = PrimaryButton("Generar reporte", "🔄")
        btn_json = SecondaryButton("Exportar JSON", "💾")
        btn_pdf  = SecondaryButton("Exportar PDF", "📄")
        btn_gen.clicked.connect(self._generar_reporte)
        btn_json.clicked.connect(self._exportar_json)
        btn_pdf.clicked.connect(self._exportar_pdf)
        btn_row.addWidget(btn_gen)
        btn_row.addSpacing(8)
        btn_row.addWidget(btn_json)
        btn_row.addWidget(btn_pdf)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        # Banner de estado
        self.banner = StatusBanner(self.fonts)
        lay.addWidget(self.banner)

        # Detalle de métricas
        card_det = Card()
        card_det.add(SectionTitle("Detalle de métricas", self.fonts, "🔬"))

        self._det_vars = {}
        det_grid = QGridLayout()
        det_grid.setColumnStretch(1, 1)
        det_grid.setHorizontalSpacing(20)
        det_grid.setVerticalSpacing(8)

        metricas = [
            ("FINDRISC",               "Puntaje FINDRISC"),
            ("Interp. FINDRISC",       "Interpretación FINDRISC"),
            ("HOMA-IR",                "HOMA-IR"),
            ("Interp. HOMA-IR",        "Interpretación HOMA-IR"),
            ("Glucosa en ayunas",      "Clase glucosa ayunas"),
            ("OGTT 2h",               "Clase OGTT"),
            ("HbA1c",                 "Clase HbA1c"),
            ("IMC",                   "IMC"),
            ("Clase IMC",             "Clase IMC"),
        ]
        for i, (key, display) in enumerate(metricas):
            fl = FieldLabel(display + ":", self.fonts)
            vl = ValueLabel("—", self.fonts)
            self._det_vars[key] = vl
            det_grid.addWidget(fl, i, 0, Qt.AlignTop)
            det_grid.addWidget(vl, i, 1, Qt.AlignTop)

        card_det.addLayout(det_grid)
        lay.addWidget(card_det)
        lay.addStretch()

        self.tabs.addTab(scroll, "📋  Reporte")

    def _tab_herramientas(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        scroll.setWidget(inner)
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(16)

        card_conv = Card()
        card_conv.add(SectionTitle("Conversión de unidades", self.fonts, "🔄"))

        g1 = QGridLayout()
        g1.setColumnStretch(3, 1)
        g1.setHorizontalSpacing(12)
        g1.setVerticalSpacing(10)

        lbl_v = FieldLabel("Valor:", self.fonts)
        self.e_conv = StyledInput("", 100)
        g1.addWidget(lbl_v, 0, 0)
        g1.addWidget(self.e_conv, 0, 1)

        self.rad_mgdl   = StyledRadio("mg/dL  →  mmol/L", self.fonts)
        self.rad_mmoll  = StyledRadio("mmol/L  →  mg/dL", self.fonts)
        self.rad_mgdl.setChecked(True)
        g1.addWidget(self.rad_mgdl,  1, 0, 1, 2)
        g1.addWidget(self.rad_mmoll, 2, 0, 1, 2)

        card_conv.addLayout(g1)

        self.lbl_conv_result = QLabel("")
        self.lbl_conv_result.setFont(self.fonts["h3"])
        self.lbl_conv_result.setStyleSheet(f"color: {C['primary_d']}; padding: 4px 0;")
        card_conv.add(self.lbl_conv_result)

        btn_conv = PrimaryButton("Convertir")
        btn_conv.clicked.connect(self._convertir)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn_conv)
        card_conv.addLayout(btn_row)
        lay.addWidget(card_conv)

        card_eag = Card()
        card_eag.add(SectionTitle("Glucosa promedio estimada (eAG)", self.fonts, "📊"))

        nota_eag = QLabel("Calcula la glucosa promedio en sangre a partir del valor de HbA1c.")
        nota_eag.setFont(self.fonts["small"])
        nota_eag.setStyleSheet(f"color: {C['text2']}; font-style: italic;")
        nota_eag.setWordWrap(True)
        card_eag.add(nota_eag)

        g2 = QGridLayout()
        g2.setColumnStretch(3, 1)
        g2.setHorizontalSpacing(12)
        g2.setVerticalSpacing(10)
        self.e_eag = self._field_row(g2, 0, "HbA1c:", "%", "3.0–20.0")
        card_eag.addLayout(g2)

        self.lbl_eag_result = QLabel("")
        self.lbl_eag_result.setFont(self.fonts["h3"])
        self.lbl_eag_result.setStyleSheet(f"color: {C['primary_d']}; padding: 4px 0;")
        card_eag.add(self.lbl_eag_result)

        btn_eag = PrimaryButton("Calcular eAG")
        btn_eag.clicked.connect(self._calcular_eag)
        btn_row2 = QHBoxLayout()
        btn_row2.addStretch()
        btn_row2.addWidget(btn_eag)
        card_eag.addLayout(btn_row2)
        lay.addWidget(card_eag)
        lay.addStretch()

        self.tabs.addTab(scroll, "🔧  Herramientas")

    def _preview_imc(self):
        try:
            imc = calcular_imc(v(self.e_peso), v(self.e_altura))
            self.lbl_imc_preview.setText(
                f"IMC calculado: {imc}  →  {clasificar_imc(imc)}"
            )
            self.lbl_imc_preview.setStyleSheet(f"color: {C['ok']}; padding: 4px 0;")
        except:
            self.lbl_imc_preview.setText("")

    def _guardar_personal(self):
        p = self.paciente
        p.edad    = vi(self.e_edad)
        p.peso    = v(self.e_peso)
        p.altura  = v(self.e_altura)
        p.cintura = v(self.e_cintura)
        p.sexo    = self.cb_sexo.currentText()[0]
        p.ejercicio_diario    = self.chk_ejercicio.isChecked()
        p.frutas_verduras     = self.chk_frutas.isChecked()
        p.hipertension        = self.chk_hipertension.isChecked()
        p.antecedentes_glucosa = self.chk_glucosa_alta.isChecked()
        p.antecedentes_familiares = (
            1 if self.rad_fam1.isChecked() else
            2 if self.rad_fam2.isChecked() else 0
        )
        try:
            imc = calcular_imc(p.peso, p.altura)
            fs  = calcular_findrisc(p)
            msg = (
                f"✓  IMC: {imc}  ({clasificar_imc(imc)})   ·   "
                f"FINDRISC: {fs} pts  ({interpretar_findrisc(fs)})"
            )
            self.lbl_personal_status.setText(msg)
            self.lbl_personal_status.setStyleSheet(
                f"color: {C['ok']}; background: #E8F8EF; border-radius: 6px; padding: 6px 10px;"
            )
            QMessageBox.information(self, "Glucofin",
                f"Datos guardados correctamente.\n\n"
                f"IMC: {imc}  →  {clasificar_imc(imc)}\n"
                f"FINDRISC: {fs} pts  →  {interpretar_findrisc(fs)}\n\n"
                f"Ve a la pestaña «Reporte» para ver la evaluación completa."
            )
        except Exception as e:
            self.lbl_personal_status.setText(f"⚠  {e}")
            self.lbl_personal_status.setStyleSheet(
                f"color: {C['warn']}; background: #FFF4E5; border-radius: 6px; padding: 6px 10px;"
            )

    def _guardar_lab(self):
        p = self.paciente
        p.glucosa_ayunas    = v(self.e_gl_ayunas)
        p.glucosa_post_ogtt = v(self.e_ogtt)
        p.hba1c             = v(self.e_hba1c)
        p.insulina_ayunas   = v(self.e_insulina)

        lineas = []
        if p.glucosa_ayunas > 0:
            cls = clasificar_glucosa_ayunas(p.glucosa_ayunas)
            color = C["ok"] if cls == "Normal" else C["warn"] if cls == "Prediabetes" else C["danger"]
            lineas.append(f'<span style="color:{color}">■</span>  '
                          f'Glucosa en ayunas: <b>{p.glucosa_ayunas} mg/dL</b> — {cls}')
        if p.glucosa_post_ogtt > 0:
            cls = clasificar_ogtt(p.glucosa_post_ogtt)
            color = C["ok"] if cls == "Normal" else C["warn"] if cls == "Prediabetes" else C["danger"]
            lineas.append(f'<span style="color:{color}">■</span>  '
                          f'OGTT (2h): <b>{p.glucosa_post_ogtt} mg/dL</b> — {cls}')
        if p.hba1c > 0:
            try:
                eag  = calcular_eag_mgdl(p.hba1c)
                eag_mmol = round(eag / CONSTANTE_MOLAR_GLUCOSA, 2)
                cls  = clasificar_hba1c(p.hba1c)
                color = C["ok"] if cls == "Normal" else C["warn"] if cls == "Prediabetes" else C["danger"]
                lineas.append(f'<span style="color:{color}">■</span>  '
                              f'HbA1c: <b>{p.hba1c}%</b> — {cls} '
                              f'<span style="color:{C["text2"]}">(eAG: {eag} mg/dL / {eag_mmol} mmol/L)</span>')
            except Exception as e:
                lineas.append(f'HbA1c: error — {e}')
        if p.insulina_ayunas > 0 and p.glucosa_ayunas > 0:
            try:
                h = calcular_homa_ir(p.glucosa_ayunas, p.insulina_ayunas)
                interp = interpretar_homa(h)
                color = C["ok"] if h < 1.9 else C["warn"] if h < 2.9 else C["danger"]
                lineas.append(f'<span style="color:{color}">■</span>  '
                              f'HOMA-IR: <b>{h}</b> — {interp}')
            except Exception as e:
                lineas.append(f'HOMA-IR: error — {e}')

        if lineas:
            self.lbl_lab_detalle.setText("<br>".join(lineas))
            self.lbl_lab_detalle.setTextFormat(Qt.RichText)
            self.lbl_lab_detalle.setStyleSheet(f"color: {C['text']}; line-height: 160%;")
        else:
            self.lbl_lab_detalle.setText("No se ingresaron datos de laboratorio.")

        QMessageBox.information(self, "Glucofin", "Datos de laboratorio guardados.")

    def _agregar_lectura(self):
        val = v(self.e_lectura)
        if val <= 0:
            QMessageBox.warning(self, "Glucofin", "Ingresa un valor de glucosa válido (> 0).")
            return
        lectura = LecturaGlucosa(valor_mgdl=val)
        self.paciente.historial.append(lectura)
        row = self.tabla.rowCount()
        self.tabla.insertRow(row)

        item_fecha = QTableWidgetItem(lectura.fecha_hora.strftime("%d/%m/%Y  %H:%M"))
        item_mgdl  = QTableWidgetItem(f"{val:.1f}")
        item_mmol  = QTableWidgetItem(f"{mgdl_a_mmoll(val):.3f}")
        for item in [item_fecha, item_mgdl, item_mmol]:
            item.setTextAlignment(Qt.AlignCenter)
        self.tabla.setItem(row, 0, item_fecha)
        self.tabla.setItem(row, 1, item_mgdl)
        self.tabla.setItem(row, 2, item_mmol)
        self.tabla.scrollToBottom()
        self.e_lectura.clear()

        cv = calcular_cv(self.paciente.historial)
        if cv is not None:
            estable = cv <= 36
            color   = C["ok"] if estable else C["warn"]
            icon    = "✓  Glucemia estable" if estable else "⚠  Alta variabilidad glucémica"
            self.lbl_cv.setText(f"{icon}    CV = {cv}%")
            self.lbl_cv.setStyleSheet(f"color: {color};")

    def _generar_reporte(self):
        try:
            res = evaluar_riesgo(self.paciente)
        except Exception as e:
            QMessageBox.critical(self, "Glucofin", f"Error al calcular: {e}")
            return

        self.banner.update(res["nivel"], res["estado"], res["accion"])
        d = res["detalle"]

        def set_d(key, txt, color=None):
            lbl = self._det_vars[key]
            lbl.setText(str(txt))
            if color:
                lbl.setStyleSheet(f"color: {color}; font-weight: 600;")
            else:
                lbl.setStyleSheet(f"color: {C['text']};")

        set_d("FINDRISC", f"{d['puntaje_findrisc']} pts")
        set_d("Interp. FINDRISC", d["interpretacion_findrisc"])
        set_d("HOMA-IR",
              str(d["homa_ir"]) if d["homa_ir"] else "—  (requiere glucosa + insulina)")
        set_d("Interp. HOMA-IR", d["interpretacion_homa"])

        cls_color = lambda c: (
            C["ok"] if c == "Normal" else
            C["warn"] if "Pre" in c else
            C["danger"] if c == "Diabetes" else C["text2"]
        )
        for key, field in [("Glucosa en ayunas", "clase_glucosa_ayunas"),
                            ("OGTT 2h",           "clase_ogtt"),
                            ("HbA1c",             "clase_hba1c")]:
            val = d[field]
            set_d(key, val, cls_color(val))

        if d["imc"]:
            imc_color = (
                C["ok"] if d["clase_imc"] == "Normal" else
                C["warn"] if "peso" in d["clase_imc"].lower() or "Sobrepeso" == d["clase_imc"] else
                C["danger"]
            )
            set_d("IMC",      f"{d['imc']}", imc_color)
            set_d("Clase IMC", d["clase_imc"], imc_color)
        else:
            set_d("IMC",       "—")
            set_d("Clase IMC", "—")

        self.tabs.setCurrentIndex(3)

    def _exportar_pdf(self):
        QMessageBox.information(
            self, "Glucofin",
            "Exportación a PDF no disponible en esta versión.\n"
            "Instala 'reportlab' y agrega la función de exportación."
        )

    def _exportar_json(self):
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar datos", "glucofin_datos.json", "JSON (*.json)"
        )
        if not ruta:
            return
        try:
            datos = self.paciente.a_diccionario()
            datos["_meta"] = {
                "generado":  datetime.datetime.now().isoformat(),
                "version":   "2.0",
                "herramienta": "Glucofin"
            }
            try:
                res = evaluar_riesgo(self.paciente)
                datos["evaluacion"] = {"estado": res["estado"],
                                       "accion": res["accion"],
                                       "detalle": res["detalle"]}
            except: datos["evaluacion"] = None

            with open(ruta, "w", encoding="utf-8") as f_:
                json.dump(datos, f_, indent=2, ensure_ascii=False, default=str)
            QMessageBox.information(self, "Glucofin", f"Datos exportados:\n{ruta}")
        except Exception as e:
            QMessageBox.critical(self, "Glucofin", f"Error al exportar: {e}")

    def _convertir(self):
        val = v(self.e_conv)
        if val < 0:
            self.lbl_conv_result.setText("⚠  Valor inválido")
            self.lbl_conv_result.setStyleSheet(f"color: {C['danger']};")
            return
        if self.rad_mgdl.isChecked():
            res = mgdl_a_mmoll(val)
            self.lbl_conv_result.setText(f"{val} mg/dL  =  {res} mmol/L")
        else:
            res = mmoll_a_mgdl(val)
            self.lbl_conv_result.setText(f"{val} mmol/L  =  {res} mg/dL")
        self.lbl_conv_result.setStyleSheet(f"color: {C['primary_d']}; font-weight: bold;")

    def _calcular_eag(self):
        val = v(self.e_eag)
        try:
            mgdl  = calcular_eag_mgdl(val)
            mmoll = round(mgdl / CONSTANTE_MOLAR_GLUCOSA, 3)
            self.lbl_eag_result.setText(f"eAG: {mgdl} mg/dL  /  {mmoll} mmol/L")
            self.lbl_eag_result.setStyleSheet(f"color: {C['primary_d']}; font-weight: bold;")
        except ValueError as e:
            self.lbl_eag_result.setText(f"⚠  {e}")
            self.lbl_eag_result.setStyleSheet(f"color: {C['danger']};")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Glucofin")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Glucofin")

    win = GlucofinApp()
    win.show()
    sys.exit(app.exec())