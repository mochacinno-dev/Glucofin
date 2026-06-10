<div align="center">

<img src="logo.png" width="250" alt="Glucofin — gota de sangre"/>

**Detección de riesgo de diabetes sin glucómetro**

[![Python](https://img.shields.io/badge/Python-3.10%2B-C0392B?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6.x-922B21?style=flat-square&logo=qt&logoColor=white)](https://doc.qt.io/qtforpython/)
[![Licencia MIT](https://img.shields.io/badge/Licencia-MIT-E74C3C?style=flat-square)](LICENSE)

</div>

---

Glucofin estima tu riesgo de desarrollar diabetes tipo 2 combinando el cuestionario clínico **FINDRISC** (validado por la OMS) con datos opcionales de laboratorio. No necesitas glucómetro para la evaluación inicial.

> Glucofin es una herramienta de orientación. No reemplaza el diagnóstico médico.

---

## Funciones

| | Módulo | Descripción |
|---|---|---|
| 👤 | **Datos personales** | IMC, cintura, edad, hábitos y antecedentes familiares |
| 🧪 | **Análisis clínicos** | Glucosa en ayunas, OGTT 2h, HbA1c e insulina |
| 📈 | **Historial glucémico** | Registro de lecturas con coeficiente de variación (CV) |
| 📋 | **Reporte de riesgo** | Clasificación FINDRISC + código de color por nivel |
| 🔧 | **Herramientas** | Conversor mg/dL ↔ mmol/L y cálculo de eAG desde HbA1c |

---

## Dependencias — Arch Linux

```bash
# Dependencias
sudo pacman -S python python-pip

# Fuente recomendada para la UI (opcional)
yay -S ttf-inter
yay -S ttf-montserrat

# PySide6
pip install PySide6 --user

# Clonar y correr
git clone https://github.com/mochacinno-dev/glucofin.git
cd glucofin
python main.py
```

Sin fuentes adicionales, Glucofin detecta automáticamente la mejor sans-serif del sistema (Noto Sans, DejaVu Sans, etc.).

---

## Métricas calculadas

- **FINDRISC** — 0 a 26 pts, cinco niveles de riesgo
- **HOMA-IR** — índice de resistencia a la insulina
- **IMC** — clasificación OMS (bajo peso → obesidad)
- **eAG** — glucosa promedio estimada desde HbA1c (fórmula ADA)
- **CV glucémico** — variabilidad del historial de lecturas

---

<div align="center">
<sub>Cuestionario FINDRISC © Finnish Diabetes Association
</div>