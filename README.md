# 🏡 Kyero-to-ImmoScout24 XML Transformer

> **EN / ES** – A Python tool to transform Kyero V3 XML feeds into ImmoScout24 format.  
> Una herramienta en Python para convertir feeds XML de Kyero V3 al formato ImmoScout24.

---

## 🌟 Características / Features
- **Lectura y procesamiento** de archivos XML (Kyero V3).  
- **Transformación automática** a la estructura de ImmoScout24.  
- **Validación de fragmentos XML** antes de exportar.  
- **Registro detallado** de errores y advertencias.  

---

## 📂 Estructura de Scripts / Script Structure
- **`main.py`** – Controla el flujo principal: lectura, transformación y validación.  
- **`utils.py`** – Funciones auxiliares para manejo de XML y utilidades.  
- **`transformer.py`** – Lógica principal de conversión Kyero → ImmoScout24.  

---

## ⚙️ Requisitos / Requirements
- Python **3.8+**
- Dependencias:
  ```bash
  pip install lxml beautifulsoup4
