from __future__ import annotations
import json
import datetime
import statistics
import tkinter as tk
from dataclasses import dataclass, field, asdict
from tkinter import font as tkfont
from tkinter import messagebox, ttk, filedialog
from typing import Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

COLORES = {
    "fondo": "#0F0F1A",
    "superficie": "#1A1A2E",
    "borde": "#2A2A3E",
    "principal": "#E74C3C",
    "principal_oscuro": "#C0392B",
    "acento": "#27AE60",
    "advertencia": "#F39C12",
    "peligro": "#E74C3C",
    "texto": "#E0E0E0",
    "texto_secundario": "#909090",
    "fondo_campos": "#1A1A2E",
    "texto_campos": "#E0E0E0",
    "exito": "#2ECC71",
}

COLORES_ESTADO = {
    "✅": COLORES["acento"],
    "🟡": COLORES["advertencia"],
    "🔸": COLORES["advertencia"],
    "🔶": "#D35400",
    "⚠️": COLORES["advertencia"],
    "⛔": COLORES["peligro"],
}

CONSTANTE_MOLAR_GLUCOSA = 18.01559

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

def crear_seccion(padre, titulo):
    return ttk.LabelFrame(padre, text=f"  {titulo}  ", padding=(14, 8))

def crear_fila(padre, etiqueta, fila, unidad=""):
    ttk.Label(padre, text=etiqueta, foreground=COLORES["texto_secundario"]).grid(
        row=fila, column=0, sticky="w", padx=(0, 12), pady=4)
    campo = ttk.Entry(padre, width=14)
    campo.grid(row=fila, column=1, sticky="w", pady=4)
    if unidad:
        ttk.Label(padre, text=unidad, foreground=COLORES["texto_secundario"]).grid(
            row=fila, column=2, sticky="w", padx=(4, 0))
    return campo

def crear_checkbutton(padre, etiqueta, variable, fila, columna=0):
    ttk.Checkbutton(padre, text=etiqueta, variable=variable).grid(
        row=fila, column=columna, columnspan=3, sticky="w", pady=3)

def obtener_valor(campo, valor_por_defecto=0.0):
    try:
        return float(campo.get().strip().replace(",", "."))
    except:
        return valor_por_defecto

def obtener_valor_entero(campo, valor_por_defecto=0):
    try:
        return int(campo.get().strip())
    except:
        return valor_por_defecto

class AplicacionGlucofin(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Glucofin — Detección de Riesgo de Diabetes")
        self.configure(bg=COLORES["fondo"])
        self.resizable(True, True)
        self.minsize(800, 600)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.paciente = Paciente()
        self.configurar_estilos()
        self.construir_interfaz()

    def configurar_estilos(self):
        estilo = ttk.Style(self)
        estilo.theme_use("clam")

        estilo.configure(".",
            background=COLORES["fondo"], foreground=COLORES["texto"],
            font=("Segoe UI", 10) if self.fuente_existe("Segoe UI") else ("DejaVu Sans", 10))

        estilo.configure("TFrame", background=COLORES["fondo"])
        estilo.configure("TLabel", background=COLORES["fondo"], foreground=COLORES["texto"])
        estilo.configure("TLabelframe",
            background=COLORES["fondo"], relief="solid",
            borderwidth=1, bordercolor=COLORES["borde"])
        estilo.configure("TLabelframe.Label",
            background=COLORES["fondo"], foreground=COLORES["principal"],
            font=(None, 10, "bold"))

        estilo.configure("TEntry",
            fieldbackground=COLORES["fondo_campos"],
            foreground=COLORES["texto_campos"],
            relief="flat", borderwidth=1)
        estilo.configure("TSpinbox",
            fieldbackground=COLORES["fondo_campos"],
            foreground=COLORES["texto_campos"])
        estilo.configure("TCombobox",
            fieldbackground=COLORES["fondo_campos"],
            foreground=COLORES["texto_campos"],
            selectbackground=COLORES["principal"],
            selectforeground="white")

        estilo.configure("TNotebook", background=COLORES["fondo"], tabposition="n")
        estilo.configure("TNotebook.Tab",
            padding=(16, 8),
            background=COLORES["superficie"],
            foreground=COLORES["texto_secundario"])
        estilo.map("TNotebook.Tab",
            background=[("selected", COLORES["fondo"]), ("active", COLORES["superficie"])],
            foreground=[("selected", COLORES["principal"])])

        estilo.configure("Primary.TButton",
            background=COLORES["principal"],
            foreground="white",
            font=(None, 10, "bold"),
            padding=(14, 7),
            relief="flat",
            bordercolor=COLORES["principal"])
        estilo.map("Primary.TButton",
            background=[("active", COLORES["principal_oscuro"]), ("pressed", COLORES["principal_oscuro"])],
            foreground=[("active", "white")])

        estilo.configure("Accent.TButton",
            background=COLORES["acento"],
            foreground="white",
            font=(None, 10, "bold"),
            padding=(14, 7),
            relief="flat")
        estilo.map("Accent.TButton",
            background=[("active", "#1E8449"), ("pressed", "#1E8449")],
            foreground=[("active", "white")])

        estilo.configure("Treeview",
            background=COLORES["superficie"],
            foreground=COLORES["texto"],
            fieldbackground=COLORES["superficie"],
            bordercolor=COLORES["borde"])
        estilo.configure("Treeview.Heading",
            background=COLORES["principal"],
            foreground="white",
            font=(None, 10, "bold"))
        estilo.map("Treeview",
            background=[("selected", COLORES["principal_oscuro"])],
            foreground=[("selected", "white")])

        estilo.configure("TCheckbutton",
            background=COLORES["fondo"],
            foreground=COLORES["texto"])
        estilo.configure("TRadiobutton",
            background=COLORES["fondo"],
            foreground=COLORES["texto"])
        estilo.map("TCheckbutton",
            background=[("active", COLORES["superficie"])],
            foreground=[("active", COLORES["texto"])])
        estilo.map("TRadiobutton",
            background=[("active", COLORES["superficie"])],
            foreground=[("active", COLORES["texto"])])

    def fuente_existe(self, nombre):
        return nombre in tkfont.families()

    def construir_interfaz(self):
        marco_principal = tk.Frame(self, bg=COLORES["fondo"])
        marco_principal.pack(fill="both", expand=True, padx=0, pady=0)
        marco_principal.grid_rowconfigure(1, weight=1)
        marco_principal.grid_columnconfigure(0, weight=1)

        encabezado = tk.Frame(marco_principal, bg=COLORES["principal"], pady=14)
        encabezado.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        encabezado.grid_columnconfigure(0, weight=1)

        tk.Label(encabezado, text="Glucofin",
            bg=COLORES["principal"], fg="white",
            font=(None, 20, "bold")).pack(side="left", padx=20)
        tk.Label(encabezado, text="Detección de riesgo de diabetes",
            bg=COLORES["principal"], fg="#F5C6C6",
            font=(None, 10)).pack(side="left", padx=4)

        self.cuaderno = ttk.Notebook(marco_principal)
        self.cuaderno.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)

        self.pestana_datos_personales()
        self.pestana_laboratorio()
        self.pestana_historial()
        self.pestana_reporte()
        self.pestana_herramientas()

        pie = tk.Frame(marco_principal, bg=COLORES["fondo"], pady=8)
        pie.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 0))
        tk.Label(
            pie,
            text="⚕ Glucofin usa el cuestionario FINDRISC (validado por la OMS) para evaluar el riesgo de diabetes tipo 2.",
            bg=COLORES["fondo"],
            fg=COLORES["texto_secundario"],
            font=(None, 8, "italic"),
            wraplength=800
        ).pack()

    def pestana_datos_personales(self):
        pestana = ttk.Frame(self.cuaderno)
        self.cuaderno.add(pestana, text="👤  Datos Personales")
        pestana.grid_columnconfigure(0, weight=1)
        pestana.grid_columnconfigure(1, weight=1)
        pestana.grid_rowconfigure(1, weight=1)

        seccion_medidas = crear_seccion(pestana, "📏 Medidas Corporales")
        seccion_medidas.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=8)
        seccion_medidas.grid_columnconfigure(0, weight=1)

        self.entrada_edad = crear_fila(seccion_medidas, "Edad", 0, "años")
        self.entrada_peso = crear_fila(seccion_medidas, "Peso", 1, "kg")
        self.entrada_altura = crear_fila(seccion_medidas, "Altura", 2, "m  (ej: 1.72)")
        self.entrada_cintura = crear_fila(seccion_medidas, "Cintura", 3, "cm")

        ttk.Label(seccion_medidas, text="Sexo biológico", foreground=COLORES["texto_secundario"]).grid(
            row=4, column=0, sticky="w", pady=4)
        self.variable_sexo = tk.StringVar(value="M")
        combo_sexo = ttk.Combobox(seccion_medidas, textvariable=self.variable_sexo,
            values=["M — Masculino", "F — Femenino"], width=16, state="readonly")
        combo_sexo.grid(row=4, column=1, sticky="w", pady=4)

        seccion_habitos = crear_seccion(pestana, "🏃‍♂️ Hábitos y Antecedentes")
        seccion_habitos.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=8)
        seccion_habitos.grid_columnconfigure(0, weight=1)

        self.variable_ejercicio = tk.BooleanVar()
        self.variable_frutas = tk.BooleanVar()
        self.variable_hipertension = tk.BooleanVar()
        self.variable_glucosa_alta = tk.BooleanVar()

        crear_checkbutton(seccion_habitos, "Realiza ejercicio ≥ 30 min al día", self.variable_ejercicio, 0)
        crear_checkbutton(seccion_habitos, "Consume frutas o verduras a diario", self.variable_frutas, 1)
        crear_checkbutton(seccion_habitos, "Toma medicación para hipertensión", self.variable_hipertension, 2)
        crear_checkbutton(seccion_habitos, "Alguna vez le diagnosticaron glucosa alta", self.variable_glucosa_alta, 3)

        ttk.Label(seccion_habitos, text="Antecedentes familiares de diabetes",
            foreground=COLORES["texto_secundario"]).grid(row=4, column=0, columnspan=3,
            sticky="w", pady=(12, 2))
        self.variable_familiares = tk.IntVar(value=0)
        opciones = [
            ("Ninguno", 0),
            ("Familiares de 2° grado (abuelos, tíos…)", 1),
            ("Familiares de 1° grado (padres, hermanos…)", 2),
        ]
        for i, (texto, valor) in enumerate(opciones):
            ttk.Radiobutton(seccion_habitos, text=texto, variable=self.variable_familiares,
                value=valor, style="TRadiobutton").grid(row=5+i, column=0, columnspan=3,
                sticky="w", padx=12)

        marco_botones = ttk.Frame(pestana)
        marco_botones.grid(row=1, column=0, columnspan=2, pady=(12, 0))
        marco_botones.grid_columnconfigure(0, weight=1)
        ttk.Button(marco_botones, text="🔄 Generar Evaluación de Riesgo",
            style="Primary.TButton",
            command=self.guardar_datos_personales).pack()

        self.etiqueta_imc = ttk.Label(pestana, text="", foreground=COLORES["acento"],
            font=(None, 11, "bold"))
        self.etiqueta_imc.grid(row=2, column=0, columnspan=2, pady=6)

        self.etiqueta_info = ttk.Label(
            pestana,
            text="📊 Ve a la pestaña 'Reporte de Riesgo' para ver tu evaluación completa.",
            foreground=COLORES["texto_secundario"],
            font=(None, 9, "italic"),
            wraplength=700
        )
        self.etiqueta_info.grid(row=3, column=0, columnspan=2, pady=(0, 8))

    def guardar_datos_personales(self):
        p = self.paciente
        p.edad = obtener_valor_entero(self.entrada_edad)
        p.peso = obtener_valor(self.entrada_peso)
        p.altura = obtener_valor(self.entrada_altura)
        p.cintura = obtener_valor(self.entrada_cintura)
        p.sexo = self.variable_sexo.get()[0]
        p.ejercicio_diario = self.variable_ejercicio.get()
        p.frutas_verduras = self.variable_frutas.get()
        p.hipertension = self.variable_hipertension.get()
        p.antecedentes_glucosa = self.variable_glucosa_alta.get()
        p.antecedentes_familiares = self.variable_familiares.get()

        try:
            imc = calcular_imc(p.peso, p.altura)
            findrisc = calcular_findrisc(p)
            self.etiqueta_imc.config(
                text=f"IMC: {imc} (→ {clasificar_imc(imc)}) | "
                     f"FINDRISC: {findrisc} pts (→ {interpretar_findrisc(findrisc)})"
            )
            self.etiqueta_imc.config(foreground=COLORES["exito"])
        except Exception as ex:
            self.etiqueta_imc.config(text=f"⚠ {ex}", foreground=COLORES["advertencia"])
        messagebox.showinfo(
            "Glucofin",
            "Datos guardados. ¡Tu evaluación de riesgo está lista!\n\n"
            "Puedes verla en la pestaña 'Reporte de Riesgo'."
        )

    def pestana_laboratorio(self):
        pestana = ttk.Frame(self.cuaderno)
        self.cuaderno.add(pestana, text="🧪  Análisis Clínicos")

        seccion_lab = crear_seccion(pestana, "Resultados de análisis de sangre")
        seccion_lab.pack(padx=20, pady=12, fill="x")

        ttk.Label(seccion_lab, text="Deja en blanco los campos que no tengas.",
            foreground=COLORES["texto_secundario"], font=(None, 9, "italic")
            ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        self.entrada_glucosa_ayunas = crear_fila(seccion_lab, "Glucosa en ayunas", 1, "mg/dL")
        self.entrada_ogtt = crear_fila(seccion_lab, "Glucosa post-OGTT (2h)", 2, "mg/dL")
        self.entrada_hba1c = crear_fila(seccion_lab, "HbA1c", 3, "%")
        self.entrada_insulina = crear_fila(seccion_lab, "Insulina en ayunas", 4, "µIU/mL")

        ttk.Button(pestana, text="Guardar análisis clínicos  ✓",
            style="Primary.TButton",
            command=self.guardar_laboratorio).pack(pady=(12, 12))

        self.etiqueta_lab = ttk.Label(pestana, text="", wraplength=480,
            justify="left", foreground=COLORES["principal"])
        self.etiqueta_lab.pack(padx=20)

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

        self.etiqueta_lab.config(text="\n".join(lineas) if lineas else "No hay datos de laboratorio registrados.")
        messagebox.showinfo("Glucofin", "Datos de laboratorio guardados.")

    def pestana_historial(self):
        pestana = ttk.Frame(self.cuaderno)
        self.cuaderno.add(pestana, text="📈  Historial Glucémico")

        marco_superior = ttk.Frame(pestana)
        marco_superior.pack(fill="x", padx=20, pady=12)

        ttk.Label(marco_superior, text="Nueva lectura (mg/dL):",
            foreground=COLORES["texto_secundario"]).pack(side="left")
        self.entrada_lectura = ttk.Entry(marco_superior, width=10)
        self.entrada_lectura.pack(side="left", padx=8)
        ttk.Button(marco_superior, text="Agregar  +",
            style="Accent.TButton",
            command=self.agregar_lectura).pack(side="left")

        contenedor = ttk.Frame(pestana)
        contenedor.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        columnas = ("Fecha/hora", "mg/dL", "mmol/L")
        self.tabla_historial = ttk.Treeview(contenedor, columns=columnas, show="headings", height=10)
        for c in columnas:
            self.tabla_historial.heading(c, text=c)
            self.tabla_historial.column(c, anchor="center", width=160, stretch=True)
        self.tabla_historial.pack(side="left", fill="both", expand=True)

        barra_deslizante = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla_historial.yview)
        barra_deslizante.pack(side="right", fill="y")
        self.tabla_historial.configure(yscrollcommand=barra_deslizante.set)

        self.etiqueta_cv = ttk.Label(pestana, text="", foreground=COLORES["principal"],
            font=(None, 10, "bold"))
        self.etiqueta_cv.pack(pady=8)

    def agregar_lectura(self):
        valor = obtener_valor(self.entrada_lectura)
        if valor <= 0:
            messagebox.showwarning("Glucofin", "Ingresa un valor de glucosa válido.")
            return
        lectura = LecturaGlucosa(valor_mgdl=valor)
        self.paciente.historial.append(lectura)
        self.tabla_historial.insert("", "end", values=(
            lectura.fecha_hora.strftime("%d-%m-%Y %H:%M"),
            f"{valor:.1f}",
            f"{mgdl_a_mmoll(valor):.3f}",
        ))
        self.entrada_lectura.delete(0, "end")
        cv = calcular_cv(self.paciente.historial)
        if cv is not None:
            estable = cv <= 36
            self.etiqueta_cv.config(
                text=f"Coeficiente de variación: {cv}%  →  "
                     f"{'Estable ✓' if estable else 'Alta variabilidad ⚠'}",
                foreground=COLORES["acento"] if estable else COLORES["advertencia"])

    def pestana_reporte(self):
        pestana = ttk.Frame(self.cuaderno)
        self.cuaderno.add(pestana, text="📋  Reporte de Riesgo")
        pestana.grid_columnconfigure(0, weight=1)
        pestana.grid_rowconfigure(1, weight=1)

        marco_botones = ttk.Frame(pestana)
        marco_botones.grid(row=0, column=0, sticky="ew", padx=20, pady=(12, 12))
        marco_botones.grid_columnconfigure(0, weight=1)
        marco_botones.grid_columnconfigure(1, weight=1)
        marco_botones.grid_columnconfigure(2, weight=1)

        ttk.Button(marco_botones, text="🔄 Generar Reporte",
            style="Primary.TButton",
            command=self.generar_reporte).grid(row=0, column=0, padx=5)

        ttk.Button(marco_botones, text="📄 Exportar a PDF",
            style="Accent.TButton",
            command=self.exportar_pdf).grid(row=0, column=1, padx=5)

        ttk.Button(marco_botones, text="💾 Exportar a JSON",
            style="Primary.TButton",
            command=self.exportar_json).grid(row=0, column=2, padx=5)

        self.marco_banner = tk.Frame(pestana, bg=COLORES["fondo"])
        self.marco_banner.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 12))

        self.variable_estado = tk.StringVar(value="")
        self.variable_accion = tk.StringVar(value="")
        self.etiqueta_estado = tk.Label(self.marco_banner,
            textvariable=self.variable_estado,
            font=(None, 16, "bold"),
            bg=COLORES["fondo"], fg=COLORES["texto"], anchor="w")
        self.etiqueta_estado.pack(fill="x")

        self.etiqueta_accion = tk.Label(self.marco_banner,
            textvariable=self.variable_accion,
            font=(None, 10), wraplength=700,
            bg=COLORES["fondo"], fg=COLORES["texto_secundario"], anchor="w", justify="left")
        self.etiqueta_accion.pack(fill="x", pady=(0, 0))

        separador = ttk.Separator(pestana, orient="horizontal")
        separador.grid(row=2, column=0, sticky="ew", padx=20, pady=4)

        marco_detalle = ttk.Frame(pestana)
        marco_detalle.grid(row=3, column=0, sticky="nsew", padx=20, pady=8)
        marco_detalle.grid_columnconfigure(1, weight=1)

        etiquetas = [
            "Puntaje FINDRISC", "Interpretación FINDRISC",
            "HOMA-IR", "Interpretación HOMA-IR",
            "Glucosa en ayunas", "OGTT (2h)", "HbA1c",
            "IMC", "Clasificación IMC"
        ]
        self.variables_detalle = {k: tk.StringVar(value="—") for k in etiquetas}

        for i, k in enumerate(etiquetas):
            ttk.Label(marco_detalle, text=k + ":", foreground=COLORES["texto_secundario"],
                font=(None, 9)).grid(row=i, column=0, sticky="w",
                padx=(0, 16), pady=3)
            ttk.Label(marco_detalle, textvariable=self.variables_detalle[k],
                foreground=COLORES["texto"], font=(None, 9, "bold")
                ).grid(row=i, column=1, sticky="w", pady=3)

        ttk.Label(pestana,
            text="⚕ Glucofin usa el cuestionario FINDRISC (validado por la OMS).",
            foreground=COLORES["texto_secundario"], font=(None, 8, "italic"),
            wraplength=700).grid(row=4, column=0, sticky="ew", padx=20, pady=(12, 0))

    def generar_reporte(self):
        try:
            resultado = evaluar_riesgo(self.paciente)
        except Exception as ex:
            messagebox.showerror("Glucofin", f"Error al calcular: {ex}")
            return

        estado = resultado["estado"]
        emoji = estado[:2].strip()
        color = COLORES_ESTADO.get(emoji, COLORES["principal"])

        self.variable_estado.set(estado)
        self.variable_accion.set(resultado["accion"])
        self.etiqueta_estado.config(fg=color)

        detalle = resultado["detalle"]
        self.variables_detalle["Puntaje FINDRISC"].set(f"{detalle['puntaje_findrisc']} pts")
        self.variables_detalle["Interpretación FINDRISC"].set(detalle["interpretacion_findrisc"])
        self.variables_detalle["HOMA-IR"].set(str(detalle["homa_ir"]) if detalle["homa_ir"] else "No disponible")
        self.variables_detalle["Interpretación HOMA-IR"].set(detalle["interpretacion_homa"])
        self.variables_detalle["Glucosa en ayunas"].set(detalle["clase_glucosa_ayunas"])
        self.variables_detalle["OGTT (2h)"].set(detalle["clase_ogtt"])
        self.variables_detalle["HbA1c"].set(detalle["clase_hba1c"])

        imc = detalle["imc"]
        if imc:
            self.variables_detalle["IMC"].set(f"{imc}")
            self.variables_detalle["Clasificación IMC"].set(detalle["clase_imc"])
        else:
            self.variables_detalle["IMC"].set("No disponible")
            self.variables_detalle["Clasificación IMC"].set("No disponible")

        self.cuaderno.select(3)

    def exportar_pdf(self):
        try:
            resultado = evaluar_riesgo(self.paciente)
            detalle = resultado["detalle"]
            paciente = self.paciente
        except Exception as ex:
            messagebox.showerror("Glucofin", f"Error al generar PDF: {ex}")
            return

        ruta_archivo = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Guardar reporte como PDF"
        )

        if not ruta_archivo:
            return

        try:
            doc = SimpleDocTemplate(
                ruta_archivo,
                pagesize=letter,
                leftMargin=0.5*inch,
                rightMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )

            estilos = getSampleStyleSheet()

            estilos_personalizados = {
                "TituloGlucofin": ParagraphStyle(
                    name="TituloGlucofin",
                    parent=estilos["Heading1"],
                    fontSize=18,
                    leading=22,
                    textColor=colors.HexColor(COLORES["principal"]),
                    alignment=TA_CENTER,
                    spaceAfter=20
                ),
                "TituloSeccionGlucofin": ParagraphStyle(
                    name="TituloSeccionGlucofin",
                    parent=estilos["Heading2"],
                    fontSize=14,
                    leading=18,
                    textColor=colors.HexColor(COLORES["acento"]),
                    spaceBefore=12,
                    spaceAfter=6
                ),
                "EstadoGlucofin": ParagraphStyle(
                    name="EstadoGlucofin",
                    parent=estilos["Normal"],
                    fontSize=14,
                    leading=18,
                    textColor=colors.HexColor(COLORES_ESTADO.get(resultado["estado"][:2].strip(), COLORES["principal"])),
                    spaceAfter=12,
                    alignment=TA_LEFT
                ),
                "TextoGlucofin": ParagraphStyle(
                    name="TextoGlucofin",
                    parent=estilos["Normal"],
                    fontSize=10,
                    leading=14,
                    textColor=colors.HexColor(COLORES["texto"]),
                    spaceAfter=6
                )
            }

            for nombre_estilo, estilo_obj in estilos_personalizados.items():
                estilos.add(estilo_obj)

            contenido = []

            contenido.append(Paragraph("Glucofin - Reporte de Riesgo de Diabetes", estilos["TituloGlucofin"]))
            contenido.append(Paragraph(f"Generado el: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}", estilos["TextoGlucofin"]))
            contenido.append(Spacer(1, 0.2*inch))

            contenido.append(Paragraph("📋 Resumen", estilos["TituloSeccionGlucofin"]))
            contenido.append(Paragraph(resultado["estado"], estilos["EstadoGlucofin"]))
            contenido.append(Paragraph(resultado["accion"], estilos["TextoGlucofin"]))
            contenido.append(Spacer(1, 0.2*inch))

            contenido.append(Paragraph("👤 Datos Personales", estilos["TituloSeccionGlucofin"]))
            datos_personales = [
                ["Edad:", f"{paciente.edad} años"],
                ["Sexo:", "Masculino" if paciente.sexo == "M" else "Femenino"],
                ["Peso:", f"{paciente.peso} kg"],
                ["Altura:", f"{paciente.altura} m"],
                ["Cintura:", f"{paciente.cintura} cm"],
                ["IMC:", f"{detalle['imc']} ({detalle['clase_imc']})" if detalle['imc'] else "No disponible"]
            ]
            tabla_personales = Table(datos_personales, colWidths=[1.5*inch, 3*inch])
            tabla_personales.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORES["principal"])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor(COLORES["superficie"])),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor(COLORES["texto"])),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor(COLORES["borde"]))
            ]))
            contenido.append(tabla_personales)
            contenido.append(Spacer(1, 0.2*inch))

            contenido.append(Paragraph("🏃‍♂️ Hábitos y Antecedentes", estilos["TituloSeccionGlucofin"]))
            datos_habitos = [
                ["Ejercicio diario:", "Sí" if paciente.ejercicio_diario else "No"],
                ["Consume frutas/verduras:", "Sí" if paciente.frutas_verduras else "No"],
                ["Hipertensión:", "Sí" if paciente.hipertension else "No"],
                ["Antecedentes de glucosa alta:", "Sí" if paciente.antecedentes_glucosa else "No"],
                ["Antecedentes familiares:", ["Ninguno", "2° grado", "1° grado"][paciente.antecedentes_familiares]]
            ]
            tabla_habitos = Table(datos_habitos, colWidths=[2*inch, 3*inch])
            tabla_habitos.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORES["principal"])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor(COLORES["superficie"])),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor(COLORES["texto"])),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor(COLORES["borde"]))
            ]))
            contenido.append(tabla_habitos)
            contenido.append(Spacer(1, 0.2*inch))

            contenido.append(Paragraph("🧪 Análisis Clínicos", estilos["TituloSeccionGlucofin"]))
            datos_lab = [
                ["Glucosa en ayunas:", f"{detalle['clase_glucosa_ayunas']} ({paciente.glucosa_ayunas} mg/dL)" if paciente.glucosa_ayunas > 0 else "No disponible"],
                ["OGTT (2h):", f"{detalle['clase_ogtt']} ({paciente.glucosa_post_ogtt} mg/dL)" if paciente.glucosa_post_ogtt > 0 else "No disponible"],
                ["HbA1c:", f"{detalle['clase_hba1c']} ({paciente.hba1c}%)" if paciente.hba1c > 0 else "No disponible"],
                ["HOMA-IR:", f"{detalle['homa_ir']} → {detalle['interpretacion_homa']}" if detalle['homa_ir'] else "No disponible"]
            ]
            tabla_lab = Table(datos_lab, colWidths=[2*inch, 3*inch])
            tabla_lab.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORES["principal"])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor(COLORES["superficie"])),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor(COLORES["texto"])),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor(COLORES["borde"]))
            ]))
            contenido.append(tabla_lab)
            contenido.append(Spacer(1, 0.2*inch))

            contenido.append(Paragraph("🔍 Evaluación de Riesgo", estilos["TituloSeccionGlucofin"]))
            datos_riesgo = [
                ["Puntaje FINDRISC:", f"{detalle['puntaje_findrisc']} pts"],
                ["Interpretación:", detalle["interpretacion_findrisc"]]
            ]
            tabla_riesgo = Table(datos_riesgo, colWidths=[2*inch, 3*inch])
            tabla_riesgo.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORES["principal"])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor(COLORES["superficie"])),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor(COLORES["texto"])),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor(COLORES["borde"]))
            ]))
            contenido.append(tabla_riesgo)

            if paciente.historial:
                contenido.append(Spacer(1, 0.2*inch))
                contenido.append(Paragraph("📈 Historial Glucémico", estilos["TituloSeccionGlucofin"]))
                datos_historial = [["Fecha/hora", "mg/dL", "mmol/L"]]
                for lectura in paciente.historial:
                    datos_historial.append([
                        lectura.fecha_hora.strftime("%d-%m-%Y %H:%M"),
                        f"{lectura.valor_mgdl:.1f}",
                        f"{mgdl_a_mmoll(lectura.valor_mgdl):.3f}"
                    ])
                tabla_historial = Table(datos_historial, colWidths=[2*inch, 1.5*inch, 1.5*inch])
                tabla_historial.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORES["principal"])),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor(COLORES["superficie"])),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor(COLORES["texto"])),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor(COLORES["borde"]))
                ]))
                contenido.append(tabla_historial)

            if detalle["cv"] is not None:
                texto_cv = f"Coeficiente de variación: {detalle['cv']}%"
                contenido.append(Spacer(1, 0.1*inch))
                contenido.append(Paragraph(texto_cv, estilos["TextoGlucofin"]))

            contenido.append(Spacer(1, 0.3*inch))
            contenido.append(Paragraph(
                "⚕ Glucofin es una herramienta de cribado informativo. No reemplaza el diagnóstico médico.",
                estilos["TextoGlucofin"]
            ))

            doc.build(contenido)
            messagebox.showinfo("Glucofin", f"Reporte PDF guardado en:\n{ruta_archivo}")
        except Exception as e:
            messagebox.showerror("Glucofin", f"Error al generar el PDF: {e}")

    def exportar_json(self):
        ruta_archivo = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Guardar datos como JSON"
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

            messagebox.showinfo("Glucofin", f"Datos guardados en JSON:\n{ruta_archivo}")
        except Exception as ex:
            messagebox.showerror("Glucofin", f"Error al exportar a JSON: {ex}")

    def pestana_herramientas(self):
        pestana = ttk.Frame(self.cuaderno)
        self.cuaderno.add(pestana, text="🔧  Herramientas")
        pestana.grid_columnconfigure(0, weight=1)

        seccion_conversion = crear_seccion(pestana, "🔄 Conversión de Unidades")
        seccion_conversion.pack(padx=20, pady=20, fill="x")

        ttk.Label(seccion_conversion, text="Valor:", foreground=COLORES["texto_secundario"]).grid(
            row=0, column=0, sticky="w")
        self.entrada_conversion = ttk.Entry(seccion_conversion, width=12)
        self.entrada_conversion.grid(row=0, column=1, padx=8)

        self.variable_direccion = tk.StringVar(value="mgdl_mmol")
        ttk.Radiobutton(seccion_conversion, text="mg/dL  →  mmol/L",
            variable=self.variable_direccion, value="mgdl_mmol", style="TRadiobutton").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Radiobutton(seccion_conversion, text="mmol/L  →  mg/dL",
            variable=self.variable_direccion, value="mmol_mgdl", style="TRadiobutton").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=2)

        ttk.Button(seccion_conversion, text="Convertir",
            style="Primary.TButton",
            command=self.convertir).grid(row=3, column=0,
            columnspan=2, pady=8, sticky="w")

        self.etiqueta_resultado_conversion = ttk.Label(seccion_conversion, text="", foreground=COLORES["acento"],
            font=(None, 12, "bold"))
        self.etiqueta_resultado_conversion.grid(row=4, column=0, columnspan=3, sticky="w")

        seccion_eag = crear_seccion(pestana, "📊 Glucosa Promedio Estimada (eAG) desde HbA1c")
        seccion_eag.pack(padx=20, pady=(0, 20), fill="x")

        self.entrada_eag = crear_fila(seccion_eag, "HbA1c", 0, "%")
        ttk.Button(seccion_eag, text="Calcular eAG",
            style="Accent.TButton",
            command=self.calcular_eag).grid(row=1, column=0,
            columnspan=3, pady=8, sticky="w")

        self.etiqueta_resultado_eag = ttk.Label(seccion_eag, text="", foreground=COLORES["acento"],
            font=(None, 12, "bold"))
        self.etiqueta_resultado_eag.grid(row=2, column=0, columnspan=3, sticky="w")

    def convertir(self):
        valor = obtener_valor(self.entrada_conversion)
        if valor < 0:
            self.etiqueta_resultado_conversion.config(text="Valor inválido.", foreground=COLORES["peligro"])
            return
        if self.variable_direccion.get() == "mgdl_mmol":
            resultado = mgdl_a_mmoll(valor)
            self.etiqueta_resultado_conversion.config(
                text=f"{valor} mg/dL  =  {resultado} mmol/L", foreground=COLORES["acento"])
        else:
            resultado = mmoll_a_mgdl(valor)
            self.etiqueta_resultado_conversion.config(
                text=f"{valor} mmol/L  =  {resultado} mg/dL", foreground=COLORES["acento"])

    def calcular_eag(self):
        h = obtener_valor(self.entrada_eag)
        try:
            mgdl = calcular_eag_mgdl(h)
            mmoll = round(mgdl / CONSTANTE_MOLAR_GLUCOSA, 3)
            self.etiqueta_resultado_eag.config(
                text=f"eAG: {mgdl} mg/dL  /  {mmoll} mmol/L",
                foreground=COLORES["acento"])
        except ValueError as ex:
            self.etiqueta_resultado_eag.config(text=str(ex), foreground=COLORES["peligro"])

if __name__ == "__main__":
    app = AplicacionGlucofin()
    app.mainloop()