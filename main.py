from __future__ import annotations
import json
import datetime
import statistics
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFrame, QLabel, QLineEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QCheckBox, 
    QRadioButton, QComboBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QScrollArea, QWidget
)
from PySide6.QtCore import Qt, QSize, QDateTime, QDate
from PySide6.QtGui import QFont, QFontDatabase, QColor, QPalette

# --- Constants ---
CONSTANTE_MOLAR_GLUCOSA = 18.01559

# --- Colors (Pastel Violet Theme) ---
COLORES = {
    "fondo": "#F0E6FF",
    "superficie": "#E6D9FF",
    "borde": "#D9C2FF",
    "principal": "#9D50FF",
    "principal_oscuro": "#7B2CBF",
    "acento": "#5D1A9B",
    "advertencia": "#FF9E00",
    "peligro": "#FF3D71",
    "texto": "#333333",
    "texto_secundario": "#666666",
    "fondo_campos": "#FFFFFF",
    "texto_campos": "#333333",
    "exito": "#4CAF50",
}

COLORES_ESTADO = {
    "✅": COLORES["acento"],
    "🟡": COLORES["advertencia"],
    "🔸": COLORES["advertencia"],
    "🔶": "#D35400",
    "⚠️": COLORES["advertencia"],
    "⛔": COLORES["peligro"],
}

# --- Data Classes ---
@dataclass
class LecturaGlucosa:
    valor_mgdl: float
    fecha_hora: datetime.datetime = field(default_factory=datetime.datetime.now)

    def __str__(self):
        return f"[{self.fecha_hora.strftime('%d-%m-%Y %H:%M')}]  {self.valor_mgdl:.1f} mg/dL"

    def a_diccionario(self):
        return {
            "valor_mgdl": self.valor_mgdl,
            "fecha_hora": self.fecha_hora.isoformat()
        }

@dataclass
class Paciente:
    glucosa_ayunas: float = 0.0
    glucosa_post_ogtt: float = 0.0
    hba1c: float = 0.0
    insulina_ayunas: float = 0.0
    peso: float = 0.0
    altura: float = 0.0
    cintura: float = 0.0
    sexo: str = "M"
    edad: int = 0
    ejercicio_diario: bool = False
    frutas_verduras: bool = False
    hipertension: bool = False
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
            "historial": [lectura.a_diccionario() for lectura in self.historial]
        }

# --- Utility Functions ---
def mgdl_a_mmoll(v):
    return round(v / CONSTANTE_MOLAR_GLUCOSA, 3)

def mmoll_a_mgdl(v):
    return round(v * CONSTANTE_MOLAR_GLUCOSA, 2)

def calcular_eag_mgdl(h):
    if not 3.0 <= h <= 20.0:
        raise ValueError("HbA1c fuera de rango biológico (3–20%).")
    return round(28.7 * h - 46.7, 2)

def calcular_homa_ir(g, i):
    if g <= 0 or i <= 0:
        raise ValueError("Glucosa e insulina deben ser > 0.")
    return round(i * g / 405.0, 2)

def interpretar_homa(v):
    if v < 1.9:
        return "Sensibilidad normal a la insulina"
    if v < 2.9:
        return "Resistencia a la insulina (leve)"
    return "Resistencia a la insulina (severa)"

def clasificar_glucosa_ayunas(v):
    if v < 100:
        return "Normal"
    if v <= 125:
        return "Prediabetes"
    return "Diabetes"

def clasificar_ogtt(v):
    if v < 140:
        return "Normal"
    if v <= 199:
        return "Prediabetes"
    return "Diabetes"

def clasificar_hba1c(v):
    if v < 5.7:
        return "Normal"
    if v <= 6.4:
        return "Prediabetes"
    return "Diabetes"

def calcular_imc(p, a):
    if a <= 0:
        raise ZeroDivisionError("Altura debe ser > 0.")
    if p <= 0:
        raise ValueError("Peso debe ser > 0.")
    return round(p / a ** 2, 2)

def clasificar_imc(v):
    if v < 18.5:
        return "Bajo peso"
    if v < 25.0:
        return "Peso normal"
    if v < 30.0:
        return "Sobrepeso"
    return "Obesidad"

def calcular_findrisc(paciente):
    pts = 0
    if paciente.edad < 45:
        pts += 0
    elif paciente.edad <= 54:
        pts += 2
    elif paciente.edad <= 64:
        pts += 3
    else:
        pts += 4

    try:
        imc = calcular_imc(paciente.peso, paciente.altura)
        if imc < 25:
            pts += 0
        elif imc <= 30:
            pts += 1
        else:
            pts += 3
    except:
        pts += 1

    if paciente.sexo.upper() == "M":
        if paciente.cintura < 94:
            pts += 0
        elif paciente.cintura <= 102:
            pts += 1
        else:
            pts += 3
    else:
        if paciente.cintura < 80:
            pts += 0
        elif paciente.cintura <= 88:
            pts += 1
        else:
            pts += 3

    if not paciente.ejercicio_diario:
        pts += 2
    if not paciente.frutas_verduras:
        pts += 1
    if paciente.hipertension:
        pts += 2
    if paciente.antecedentes_glucosa:
        pts += 5
    if paciente.antecedentes_familiares == 1:
        pts += 3
    elif paciente.antecedentes_familiares == 2:
        pts += 5

    return min(pts, 26)

def interpretar_findrisc(pts):
    if pts <= 7:
        return "Riesgo bajo (~1% en 10 años)"
    if pts <= 11:
        return "Ligeramente elevado (~4%)"
    if pts <= 14:
        return "Moderado (~17%)"
    if pts <= 20:
        return "Alto (~33%)"
    return "Muy alto (~50%)"

def calcular_cv(lecturas):
    if len(lecturas) < 2:
        return None
    vals = [l.valor_mgdl for l in lecturas]
    mu = statistics.mean(vals)
    if mu == 0:
        return None
    return round(statistics.stdev(vals) / mu * 100, 2)

def evaluar_riesgo(paciente):
    homa = None
    if paciente.insulina_ayunas > 0 and paciente.glucosa_ayunas > 0:
        try:
            homa = calcular_homa_ir(paciente.glucosa_ayunas, paciente.insulina_ayunas)
        except:
            pass

    findrisc = calcular_findrisc(paciente)
    tiene_datos_glucosa = paciente.glucosa_ayunas > 0 or paciente.glucosa_post_ogtt > 0 or paciente.hba1c > 0

    detalle = {
        "puntaje_findrisc": findrisc,
        "interpretacion_findrisc": interpretar_findrisc(findrisc),
        "homa_ir": homa,
        "interpretacion_homa": interpretar_homa(homa) if homa else "Requiere datos de glucosa e insulina en ayunas",
        "clase_glucosa_ayunas": clasificar_glucosa_ayunas(paciente.glucosa_ayunas) if paciente.glucosa_ayunas > 0 else "No disponible",
        "clase_ogtt": clasificar_ogtt(paciente.glucosa_post_ogtt) if paciente.glucosa_post_ogtt > 0 else "No disponible",
        "clase_hba1c": clasificar_hba1c(paciente.hba1c) if paciente.hba1c > 0 else "No disponible",
        "imc": calcular_imc(paciente.peso, paciente.altura) if paciente.peso > 0 and paciente.altura > 0 else None,
        "clase_imc": clasificar_imc(calcular_imc(paciente.peso, paciente.altura)) if paciente.peso > 0 and paciente.altura > 0 else "No disponible",
        "cv": calcular_cv(paciente.historial) if len(paciente.historial) >= 2 else None,
    }

    if not tiene_datos_glucosa:
        if findrisc >= 15:
            return {"estado": "🔶 Riesgo muy alto de diabetes tipo 2", "accion": "Intervención urgente: cambia hábitos y visita a tu médico.", "detalle": detalle}
        if findrisc >= 12:
            return {"estado": "🟡 Riesgo elevado de diabetes tipo 2", "accion": "Mejora tu estilo de vida: dieta, ejercicio y controles regulares.", "detalle": detalle}
        if findrisc >= 7:
            return {"estado": "⚠️ Riesgo moderado de diabetes tipo 2", "accion": "Adopta hábitos saludables para prevenir progresión.", "detalle": detalle}
        return {"estado": "✅ Bajo riesgo de diabetes", "accion": "Mantén tus hábitos y realiza controles anuales.", "detalle": detalle}

    if (paciente.hba1c >= 6.5 and paciente.hba1c > 0) or (paciente.glucosa_ayunas >= 126 and paciente.glucosa_ayunas > 0):
        return {"estado": "⛔ Diabetes confirmada", "accion": "Consulta a tu médico de inmediato para confirmación y tratamiento.", "detalle": detalle}
    if (5.7 <= paciente.hba1c <= 6.4) or (100 <= paciente.glucosa_ayunas <= 125) or (140 <= paciente.glucosa_post_ogtt <= 199):
        return {"estado": "⚠️ Prediabetes", "accion": "Riesgo alto. Prioriza dieta, ejercicio y seguimiento médico.", "detalle": detalle}
    if findrisc >= 15:
        return {"estado": "🔶 Riesgo muy alto de diabetes tipo 2", "accion": "Intervención urgente: cambia hábitos y visita a tu médico.", "detalle": detalle}
    if findrisc >= 12:
        return {"estado": "🟡 Riesgo elevado de diabetes tipo 2", "accion": "Mejora tu estilo de vida: dieta, ejercicio y controles regulares.", "detalle": detalle}
    if homa and homa >= 2.9:
        return {"estado": "🔸 Resistencia a la insulina severa", "accion": "Optimiza dieta, ejercicio y sueño. Consulta a un endocrinólogo.", "detalle": detalle}
    if homa and homa >= 1.9:
        return {"estado": "🟡 Resistencia a la insulina (leve)", "accion": "Adopta hábitos saludables para prevenir prediabetes.", "detalle": detalle}
    return {"estado": "✅ Bajo riesgo de diabetes", "accion": "Mantén tus hábitos y realiza controles anuales.", "detalle": detalle}

# --- Helper Functions ---
def obtener_valor(campo, valor_por_defecto=0.0):
    try:
        return float(campo.text().strip().replace(",", "."))
    except:
        return valor_por_defecto

def obtener_valor_entero(campo, valor_por_defecto=0):
    try:
        return int(campo.text().strip())
    except:
        return valor_por_defecto

# --- Main Application ---
class AplicacionGlucofin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Glucofin — Detección de Riesgo de Diabetes")
        self.setMinimumSize(800, 600)
        self.paciente = Paciente()
        self.setup_fonts()
        self.setup_ui()

    def setup_fonts(self):
        # Load Montserrat font
        font_id = QFontDatabase.addApplicationFont(":/fonts/Montserrat-Regular.ttf")
        if font_id != -1:
            QFontDatabase.addApplicationFont(":/fonts/Montserrat-Bold.ttf")
            QFontDatabase.addApplicationFont(":/fonts/Montserrat-SemiBold.ttf")
            QFontDatabase.addApplicationFont(":/fonts/Montserrat-Light.ttf")
        else:
            # Fallback to system fonts
            pass

    def setup_ui(self):
        # Set palette for pastel violet theme
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(COLORES["fondo"]))
        palette.setColor(QPalette.WindowText, QColor(COLORES["texto"]))
        palette.setColor(QPalette.Base, QColor(COLORES["fondo_campos"]))
        palette.setColor(QPalette.AlternateBase, QColor(COLORES["superficie"]))
        palette.setColor(QPalette.ToolTipBase, QColor(COLORES["fondo"]))
        palette.setColor(QPalette.ToolTipText, QColor(COLORES["texto"]))
        palette.setColor(QPalette.Text, QColor(COLORES["texto"]))
        palette.setColor(QPalette.Button, QColor(COLORES["principal"]))
        palette.setColor(QPalette.ButtonText, QColor("white"))
        palette.setColor(QPalette.BrightText, QColor("white"))
        palette.setColor(QPalette.Highlight, QColor(COLORES["principal"]))
        palette.setColor(QPalette.HighlightedText, QColor("white"))
        self.setPalette(palette)

        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet(f"background-color: {COLORES['principal']};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 14, 20, 14)

        title_label = QLabel("Glucofin")
        title_label.setStyleSheet("color: white;")
        title_font = QFont("Montserrat", 20, QFont.Bold)
        title_label.setFont(title_font)

        subtitle_label = QLabel("Detección de riesgo de diabetes")
        subtitle_label.setStyleSheet("color: #F5C6C6;")
        subtitle_font = QFont("Montserrat", 10)
        subtitle_label.setFont(subtitle_font)

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        header_layout.addStretch()

        # Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(
            f"QTabWidget::pane {{ border: 1px solid {COLORES['borde']}; }}"
            f"QTabBar::tab {{ background: {COLORES['superficie']}; color: {COLORES['texto_secundario']}; padding: 8px 16px; }}"
            f"QTabBar::tab:selected {{ background: {COLORES['fondo']}; color: {COLORES['principal']}; }}"
        )

        # Create tabs
        self.pestana_datos_personales()
        self.pestana_laboratorio()
        self.pestana_historial()
        self.pestana_reporte()
        self.pestana_herramientas()

        # Footer
        footer = QLabel(
            "⚕ Glucofin usa el cuestionario FINDRISC (validado por la OMS) para evaluar el riesgo de diabetes tipo 2."
        )
        footer.setStyleSheet(f"color: {COLORES['texto_secundario']};")
        footer.setFont(QFont("Montserrat", 8, QFont.Italic))
        footer.setWordWrap(True)
        footer.setMaximumWidth(800)

        # Add widgets to main layout
        main_layout.addWidget(header)
        main_layout.addWidget(self.tab_widget)
        main_layout.addWidget(footer, alignment=Qt.AlignCenter)

    def pestana_datos_personales(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        # Medidas Corporales
        grupo_medidas = QGroupBox("📏 Medidas Corporales")
        grupo_medidas.setStyleSheet(f"QGroupBox {{ border: 1px solid {COLORES['borde']}; border-radius: 5px; }}")
        grupo_medidas_layout = QGridLayout(grupo_medidas)

        self.entrada_edad = self.crear_fila(grupo_medidas_layout, "Edad", 0, "años")
        self.entrada_peso = self.crear_fila(grupo_medidas_layout, "Peso", 1, "kg")
        self.entrada_altura = self.crear_fila(grupo_medidas_layout, "Altura", 2, "m (ej: 1.72)")
        self.entrada_cintura = self.crear_fila(grupo_medidas_layout, "Cintura", 3, "cm")

        # Sexo
        sexo_layout = QHBoxLayout()
        sexo_label = QLabel("Sexo biológico:")
        sexo_label.setStyleSheet(f"color: {COLORES['texto_secundario']};")
        self.variable_sexo = QComboBox()
        self.variable_sexo.addItems(["M — Masculino", "F — Femenino"])
        self.variable_sexo.setCurrentIndex(0)
        sexo_layout.addWidget(sexo_label)
        sexo_layout.addWidget(self.variable_sexo)
        grupo_medidas_layout.addLayout(sexo_layout, 4, 0, 1, 2)

        # Hábitos y Antecedentes
        grupo_habitos = QGroupBox("🏃‍♂️ Hábitos y Antecedentes")
        grupo_habitos.setStyleSheet(f"QGroupBox {{ border: 1px solid {COLORES['borde']}; border-radius: 5px; }}")
        grupo_habitos_layout = QVBoxLayout(grupo_habitos)

        self.variable_ejercicio = self.crear_checkbutton(grupo_habitos_layout, "Realiza ejercicio ≥ 30 min al día")
        self.variable_frutas = self.crear_checkbutton(grupo_habitos_layout, "Consume frutas o verduras a diario")
        self.variable_hipertension = self.crear_checkbutton(grupo_habitos_layout, "Toma medicación para hipertensión")
        self.variable_glucosa_alta = self.crear_checkbutton(grupo_habitos_layout, "Alguna vez le diagnosticaron glucosa alta")

        # Antecedentes familiares
        antecedentes_layout = QVBoxLayout()
        antecedentes_label = QLabel("Antecedentes familiares de diabetes:")
        antecedentes_label.setStyleSheet(f"color: {COLORES['texto_secundario']};")
        antecedentes_layout.addWidget(antecedentes_label)

        self.variable_familiares = QRadioButton("Ninguno")
        self.variable_familiares.setChecked(True)
        self.radio_2grado = QRadioButton("Familiares de 2° grado (abuelos, tíos…)")
        self.radio_1grado = QRadioButton("Familiares de 1° grado (padres, hermanos…)")

        antecedentes_layout.addWidget(self.variable_familiares)
        antecedentes_layout.addWidget(self.radio_2grado)
        antecedentes_layout.addWidget(self.radio_1grado)
        grupo_habitos_layout.addLayout(antecedentes_layout)

        # Buttons
        botones_layout = QHBoxLayout()
        boton_generar = QPushButton("🔄 Generar Evaluación de Riesgo")
        boton_generar.setStyleSheet(
            f"QPushButton {{ background-color: {COLORES['principal']}; color: white; padding: 7px 14px; border: none; border-radius: 4px; }}"
            f"QPushButton:hover {{ background-color: {COLORES['principal_oscuro']}; }}"
        )
        boton_generar.clicked.connect(self.guardar_datos_personales)
        botones_layout.addWidget(boton_generar)

        # IMC Label
        self.etiqueta_imc = QLabel()
        self.etiqueta_imc.setStyleSheet(f"color: {COLORES['acento']}; font-weight: bold;")

        # Info Label
        self.etiqueta_info = QLabel("📊 Ve a la pestaña 'Reporte de Riesgo' para ver tu evaluación completa.")
        self.etiqueta_info.setStyleSheet(f"color: {COLORES['texto_secundario']}; font-style: italic;")
        self.etiqueta_info.setWordWrap(True)

        # Add to layout
        layout.addWidget(grupo_medidas)
        layout.addWidget(grupo_habitos)
        layout.addLayout(botones_layout)
        layout.addWidget(self.etiqueta_imc)
        layout.addWidget(self.etiqueta_info)

        self.tab_widget.addTab(tab, "👤  Datos Personales")

    def pestana_laboratorio(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        grupo_lab = QGroupBox("Resultados de análisis de sangre")
        grupo_lab.setStyleSheet(f"QGroupBox {{ border: 1px solid {COLORES['borde']}; border-radius: 5px; }}")
        grupo_lab_layout = QGridLayout(grupo_lab)

        info_label = QLabel("Deja en blanco los campos que no tengas.")
        info_label.setStyleSheet(f"color: {COLORES['texto_secundario']}; font-style: italic;")
        grupo_lab_layout.addWidget(info_label, 0, 0, 1, 3)

        self.entrada_glucosa_ayunas = self.crear_fila(grupo_lab_layout, "Glucosa en ayunas", 1, "mg/dL")
        self.entrada_ogtt = self.crear_fila(grupo_lab_layout, "Glucosa post-OGTT (2h)", 2, "mg/dL")
        self.entrada_hba1c = self.crear_fila(grupo_lab_layout, "HbA1c", 3, "%")
        self.entrada_insulina = self.crear_fila(grupo_lab_layout, "Insulina en ayunas", 4, "µIU/mL")

        boton_guardar = QPushButton("Guardar análisis clínicos  ✓")
        boton_guardar.setStyleSheet(
            f"QPushButton {{ background-color: {COLORES['principal']}; color: white; padding: 7px 14px; border: none; border-radius: 4px; }}"
            f"QPushButton:hover {{ background-color: {COLORES['principal_oscuro']}; }}"
        )
        boton_guardar.clicked.connect(self.guardar_laboratorio)

        self.etiqueta_lab = QLabel()
        self.etiqueta_lab.setWordWrap(True)
        self.etiqueta_lab.setStyleSheet(f"color: {COLORES['principal']};")

        layout.addWidget(grupo_lab)
        layout.addWidget(boton_guardar)
        layout.addWidget(self.etiqueta_lab)

        self.tab_widget.addTab(tab, "🧪  Análisis Clínicos")

    def pestana_historial(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        # Nueva lectura
        nueva_lectura_layout = QHBoxLayout()
        nueva_lectura_label = QLabel("Nueva lectura (mg/dL):")
        nueva_lectura_label.setStyleSheet(f"color: {COLORES['texto_secundario']};")
        self.entrada_lectura = QLineEdit()
        self.entrada_lectura.setMaximumWidth(80)
        boton_agregar = QPushButton("Agregar  +")
        boton_agregar.setStyleSheet(
            f"QPushButton {{ background-color: {COLORES['acento']}; color: white; padding: 7px 14px; border: none; border-radius: 4px; }}"
        )
        boton_agregar.clicked.connect(self.agregar_lectura)

        nueva_lectura_layout.addWidget(nueva_lectura_label)
        nueva_lectura_layout.addWidget(self.entrada_lectura)
        nueva_lectura_layout.addWidget(boton_agregar)

        # Tabla de historial
        self.tabla_historial = QTableWidget()
        self.tabla_historial.setColumnCount(3)
        self.tabla_historial.setHorizontalHeaderLabels(["Fecha/hora", "mg/dL", "mmol/L"])
        self.tabla_historial.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_historial.setStyleSheet(
            f"QTableWidget {{ background-color: {COLORES['superficie']}; color: {COLORES['texto']}; }}"
            f"QHeaderView::section {{ background-color: {COLORES['principal']}; color: white; }}"
        )

        # CV Label
        self.etiqueta_cv = QLabel()
        self.etiqueta_cv.setStyleSheet(f"font-weight: bold;")

        layout.addLayout(nueva_lectura_layout)
        layout.addWidget(self.tabla_historial)
        layout.addWidget(self.etiqueta_cv)

        self.tab_widget.addTab(tab, "📈  Historial Glucémico")

    def pestana_reporte(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        # Buttons
        botones_layout = QHBoxLayout()
        boton_generar = QPushButton("🔄 Generar Reporte")
        boton_generar.setStyleSheet(
            f"QPushButton {{ background-color: {COLORES['principal']}; color: white; padding: 7px 14px; border: none; border-radius: 4px; }}"
        )
        boton_generar.clicked.connect(self.generar_reporte)

        boton_pdf = QPushButton("📄 Exportar a PDF")
        boton_pdf.setStyleSheet(
            f"QPushButton {{ background-color: {COLORES['acento']}; color: white; padding: 7px 14px; border: none; border-radius: 4px; }}"
        )
        boton_pdf.clicked.connect(self.exportar_pdf)

        boton_json = QPushButton("💾 Exportar a JSON")
        boton_json.setStyleSheet(
            f"QPushButton {{ background-color: {COLORES['principal']}; color: white; padding: 7px 14px; border: none; border-radius: 4px; }}"
        )
        boton_json.clicked.connect(self.exportar_json)

        botones_layout.addWidget(boton_generar)
        botones_layout.addWidget(boton_pdf)
        botones_layout.addWidget(boton_json)

        # Banner
        self.marco_banner = QFrame()
        self.marco_banner.setStyleSheet(f"background-color: {COLORES['fondo']};")
        banner_layout = QVBoxLayout(self.marco_banner)

        self.variable_estado = ""
        self.variable_accion = ""
        self.etiqueta_estado = QLabel()
        self.etiqueta_estado.setFont(QFont("Montserrat", 16, QFont.Bold))
        self.etiqueta_estado.setWordWrap(True)

        self.etiqueta_accion = QLabel()
        self.etiqueta_accion.setFont(QFont("Montserrat", 10))
        self.etiqueta_accion.setWordWrap(True)
        self.etiqueta_accion.setStyleSheet(f"color: {COLORES['texto_secundario']};")

        banner_layout.addWidget(self.etiqueta_estado)
        banner_layout.addWidget(self.etiqueta_accion)

        # Detalle
        marco_detalle = QGroupBox()
        marco_detalle.setStyleSheet(f"QGroupBox {{ border: 1px solid {COLORES['borde']}; border-radius: 5px; }}")
        detalle_layout = QGridLayout(marco_detalle)

        etiquetas = [
            "Puntaje FINDRISC", "Interpretación FINDRISC",
            "HOMA-IR", "Interpretación HOMA-IR",
            "Glucosa en ayunas", "OGTT (2h)", "HbA1c",
            "IMC", "Clasificación IMC"
        ]
        self.variables_detalle = {k: QLabel("—") for k in etiquetas}

        for i, k in enumerate(etiquetas):
            label = QLabel(f"{k}:")
            label.setStyleSheet(f"color: {COLORES['texto_secundario']};")
            detalle_layout.addWidget(label, i, 0)
            detalle_layout.addWidget(self.variables_detalle[k], i, 1)

        # Footer
        footer_label = QLabel("⚕ Glucofin usa el cuestionario FINDRISC (validado por la OMS).")
        footer_label.setStyleSheet(f"color: {COLORES['texto_secundario']}; font-style: italic;")
        footer_label.setWordWrap(True)

        layout.addLayout(botones_layout)
        layout.addWidget(self.marco_banner)
        layout.addWidget(marco_detalle)
        layout.addWidget(footer_label)

        self.tab_widget.addTab(tab, "📋  Reporte de Riesgo")

    def pestana_herramientas(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        # Conversión de Unidades
        grupo_conversion = QGroupBox("🔄 Conversión de Unidades")
        grupo_conversion.setStyleSheet(f"QGroupBox {{ border: 1px solid {COLORES['borde']}; border-radius: 5px; }}")
        conversion_layout = QGridLayout(grupo_conversion)

        conversion_label = QLabel("Valor:")
        conversion_label.setStyleSheet(f"color: {COLORES['texto_secundario']};")
        self.entrada_conversion = QLineEdit()
        self.entrada_conversion.setMaximumWidth(100)

        self.variable_direccion = "mgdl_mmol"
        radio_mgdl = QRadioButton("mg/dL  →  mmol/L")
        radio_mmol = QRadioButton("mmol/L  →  mg/dL")
        radio_mgdl.setChecked(True)

        boton_convertir = QPushButton("Convertir")
        boton_convertir.setStyleSheet(
            f"QPushButton {{ background-color: {COLORES['principal']}; color: white; padding: 7px 14px; border: none; border-radius: 4px; }}"
        )
        boton_convertir.clicked.connect(self.convertir)

        self.etiqueta_resultado_conversion = QLabel()
        self.etiqueta_resultado_conversion.setStyleSheet(f"color: {COLORES['acento']}; font-weight: bold;")

        conversion_layout.addWidget(conversion_label, 0, 0)
        conversion_layout.addWidget(self.entrada_conversion, 0, 1)
        conversion_layout.addWidget(radio_mgdl, 1, 0, 1, 2)
        conversion_layout.addWidget(radio_mmol, 2, 0, 1, 2)
        conversion_layout.addWidget(boton_convertir, 3, 0, 1, 2)
        conversion_layout.addWidget(self.etiqueta_resultado_conversion, 4, 0, 1, 2)

        # eAG
        grupo_eag = QGroupBox("📊 Glucosa Promedio Estimada (eAG) desde HbA1c")
        grupo_eag.setStyleSheet(f"QGroupBox {{ border: 1px solid {COLORES['borde']}; border-radius: 5px; }}")
        eag_layout = QGridLayout(grupo_eag)

        self.entrada_eag = self.crear_fila(eag_layout, "HbA1c", 0, "%")
        boton_eag = QPushButton("Calcular eAG")
        boton_eag.setStyleSheet(
            f"QPushButton {{ background-color: {COLORES['acento']}; color: white; padding: 7px 14px; border: none; border-radius: 4px; }}"
        )
        boton_eag.clicked.connect(self.calcular_eag)

        self.etiqueta_resultado_eag = QLabel()
        self.etiqueta_resultado_eag.setStyleSheet(f"color: {COLORES['acento']}; font-weight: bold;")

        eag_layout.addWidget(boton_eag, 1, 0, 1, 3)
        eag_layout.addWidget(self.etiqueta_resultado_eag, 2, 0, 1, 3)

        layout.addWidget(grupo_conversion)
        layout.addWidget(grupo_eag)

        self.tab_widget.addTab(tab, "🔧  Herramientas")

    def crear_fila(self, layout, etiqueta, fila, unidad=""):
        label = QLabel(etiqueta)
        label.setStyleSheet(f"color: {COLORES['texto_secundario']};")
        campo = QLineEdit()
        campo.setMaximumWidth(100)
        layout.addWidget(label, fila, 0)
        layout.addWidget(campo, fila, 1)
        if unidad:
            unidad_label = QLabel(unidad)
            unidad_label.setStyleSheet(f"color: {COLORES['texto_secundario']};")
            layout.addWidget(unidad_label, fila, 2)
        return campo

    def crear_checkbutton(self, layout, texto):
        checkbox = QCheckBox(texto)
        checkbox.setStyleSheet(f"color: {COLORES['texto']};")
        layout.addWidget(checkbox)
        return checkbox

    def guardar_datos_personales(self):
        p = self.paciente
        p.edad = obtener_valor_entero(self.entrada_edad)
        p.peso = obtener_valor(self.entrada_peso)
        p.altura = obtener_valor(self.entrada_altura)
        p.cintura = obtener_valor(self.entrada_cintura)
        p.sexo = self.variable_sexo.currentText()[0]
        p.ejercicio_diario = self.variable_ejercicio.isChecked()
        p.frutas_verduras = self.variable_frutas.isChecked()
        p.hipertension = self.variable_hipertension.isChecked()
        p.antecedentes_glucosa = self.variable_glucosa_alta.isChecked()
        p.antecedentes_familiares = 0
        if self.radio_2grado.isChecked():
            p.antecedentes_familiares = 1
        elif self.radio_1grado.isChecked():
            p.antecedentes_familiares = 2

        try:
            imc = calcular_imc(p.peso, p.altura)
            findrisc = calcular_findrisc(p)
            self.etiqueta_imc.setText(
                f"IMC: {imc} (→ {clasificar_imc(imc)}) | "
                f"FINDRISC: {findrisc} pts (→ {interpretar_findrisc(findrisc)})"
            )
            self.etiqueta_imc.setStyleSheet(f"color: {COLORES['exito']};")
        except Exception as ex:
            self.etiqueta_imc.setText(f"⚠ {ex}")
            self.etiqueta_imc.setStyleSheet(f"color: {COLORES['advertencia']};")

        QMessageBox.information(self, "Glucofin", 
            "Datos guardados. ¡Tu evaluación de riesgo está lista!\n\n"
            "Puedes verla en la pestaña 'Reporte de Riesgo'."
        )

    def guardar_laboratorio(self):
        p = self.paciente
        p.glucosa_ayunas = obtener_valor(self.entrada_glucosa_ayunas)
        p.glucosa_post_ogtt = obtener_valor(self.entrada_ogtt)
        p.hba1c = obtener_valor(self.entrada_hba1c)
        p.insulina_ayunas = obtener_valor(self.entrada_insulina)

        lineas = []
        if p.glucosa_ayunas > 0:
            lineas.append(f"Glucosa en ayunas: {clasificar_glucosa_ayunas(p.glucosa_ayunas)}")
        if p.glucosa_post_ogtt > 0:
            lineas.append(f"OGTT (2h): {clasificar_ogtt(p.glucosa_post_ogtt)}")
        if p.hba1c > 0:
            eag = calcular_eag_mgdl(p.hba1c)
            lineas.append(f"HbA1c: {clasificar_hba1c(p.hba1c)}  |  eAG estimado: {eag} mg/dL")
        if p.insulina_ayunas > 0 and p.glucosa_ayunas > 0:
            h = calcular_homa_ir(p.glucosa_ayunas, p.insulina_ayunas)
            lineas.append(f"HOMA-IR: {h}  →  {interpretar_homa(h)}")

        self.etiqueta_lab.setText("\n".join(lineas) if lineas else "No hay datos de laboratorio registrados.")
        QMessageBox.information(self, "Glucofin", "Datos de laboratorio guardados.")

    def agregar_lectura(self):
        valor = obtener_valor(self.entrada_lectura)
        if valor <= 0:
            QMessageBox.warning(self, "Glucofin", "Ingresa un valor de glucosa válido.")
            return
        lectura = LecturaGlucosa(valor_mgdl=valor)
        self.paciente.historial.append(lectura)

        row = self.tabla_historial.rowCount()
        self.tabla_historial.insertRow(row)
        self.tabla_historial.setItem(row, 0, QTableWidgetItem(lectura.fecha_hora.strftime("%d-%m-%Y %H:%M")))
        self.tabla_historial.setItem(row, 1, QTableWidgetItem(f"{valor:.1f}"))
        self.tabla_historial.setItem(row, 2, QTableWidgetItem(f"{mgdl_a_mmoll(valor):.3f}"))

        self.entrada_lectura.clear()

        cv = calcular_cv(self.paciente.historial)
        if cv is not None:
            estable = cv <= 36
            color = COLORES["acento"] if estable else COLORES["advertencia"]
            self.etiqueta_cv.setText(
                f"Coeficiente de variación: {cv}%  →  {'Estable ✓' if estable else 'Alta variabilidad ⚠'}"
            )
            self.etiqueta_cv.setStyleSheet(f"color: {color}; font-weight: bold;")

    def generar_reporte(self):
        try:
            resultado = evaluar_riesgo(self.paciente)
        except Exception as ex:
            QMessageBox.critical(self, "Glucofin", f"Error al calcular: {ex}")
            return

        estado = resultado["estado"]
        emoji = estado[:2].strip()
        color = COLORES_ESTADO.get(emoji, COLORES["principal"])

        self.etiqueta_estado.setText(estado)
        self.etiqueta_estado.setStyleSheet(f"color: {color};")
        self.etiqueta_accion.setText(resultado["accion"])

        detalle = resultado["detalle"]
        self.variables_detalle["Puntaje FINDRISC"].setText(f"{detalle['puntaje_findrisc']} pts")
        self.variables_detalle["Interpretación FINDRISC"].setText(detalle["interpretacion_findrisc"])
        self.variables_detalle["HOMA-IR"].setText(str(detalle["homa_ir"]) if detalle["homa_ir"] else "No disponible")
        self.variables_detalle["Interpretación HOMA-IR"].setText(detalle["interpretacion_homa"])
        self.variables_detalle["Glucosa en ayunas"].setText(detalle["clase_glucosa_ayunas"])
        self.variables_detalle["OGTT (2h)"].setText(detalle["clase_ogtt"])
        self.variables_detalle["HbA1c"].setText(detalle["clase_hba1c"])

        imc = detalle["imc"]
        if imc:
            self.variables_detalle["IMC"].setText(f"{imc}")
            self.variables_detalle["Clasificación IMC"].setText(detalle["clase_imc"])
        else:
            self.variables_detalle["IMC"].setText("No disponible")
            self.variables_detalle["Clasificación IMC"].setText("No disponible")

        self.tab_widget.setCurrentIndex(3)

    def exportar_pdf(self):
        # Placeholder for PDF export (requires reportlab)
        QMessageBox.information(self, "Glucofin", "Funcionalidad de exportación a PDF no implementada en esta versión.")

    def exportar_json(self):
        ruta_archivo, _ = QFileDialog.getSaveFileName(
            self, "Guardar datos como JSON", "", "JSON files (*.json)"
        )
        if not ruta_archivo:
            return

        try:
            datos = self.paciente.a_diccionario()
            datos["metadatos"] = {
                "fecha_creacion": datetime.datetime.now().isoformat(),
                "version": "1.0",
                "herramienta": "Glucofin"
            }
            try:
                resultado = evaluar_riesgo(self.paciente)
                datos["evaluacion_riesgo"] = {
                    "estado": resultado["estado"],
                    "accion": resultado["accion"],
                    "detalle": resultado["detalle"]
                }
            except:
                datos["evaluacion_riesgo"] = None

            with open(ruta_archivo, 'w', encoding='utf-8') as archivo:
                json.dump(datos, archivo, indent=4, ensure_ascii=False)

            QMessageBox.information(self, "Glucofin", f"Datos guardados en JSON:\n{ruta_archivo}")
        except Exception as ex:
            QMessageBox.critical(self, "Glucofin", f"Error al exportar a JSON: {ex}")

    def convertir(self):
        valor = obtener_valor(self.entrada_conversion)
        if valor < 0:
            self.etiqueta_resultado_conversion.setText("Valor inválido.")
            self.etiqueta_resultado_conversion.setStyleSheet(f"color: {COLORES['peligro']};")
            return
        if self.variable_direccion == "mgdl_mmol":
            resultado = mgdl_a_mmoll(valor)
            self.etiqueta_resultado_conversion.setText(f"{valor} mg/dL  =  {resultado} mmol/L")
        else:
            resultado = mmoll_a_mgdl(valor)
            self.etiqueta_resultado_conversion.setText(f"{valor} mmol/L  =  {resultado} mg/dL")
        self.etiqueta_resultado_conversion.setStyleSheet(f"color: {COLORES['acento']};")

    def calcular_eag(self):
        h = obtener_valor(self.entrada_eag)
        try:
            mgdl = calcular_eag_mgdl(h)
            mmoll = round(mgdl / CONSTANTE_MOLAR_GLUCOSA, 3)
            self.etiqueta_resultado_eag.setText(f"eAG: {mgdl} mg/dL  /  {mmoll} mmol/L")
            self.etiqueta_resultado_eag.setStyleSheet(f"color: {COLORES['acento']};")
        except ValueError as ex:
            self.etiqueta_resultado_eag.setText(str(ex))
            self.etiqueta_resultado_eag.setStyleSheet(f"color: {COLORES['peligro']};")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AplicacionGlucofin()
    window.show()
    sys.exit(app.exec())