# 🏡 Kyero-to-ImmoScout24 XML Transformer

> **EN / ES** – A Python tool to transform Kyero V3 XML feeds into ImmoScout24 format.  
> Una herramienta en Python para convertir feeds XML de Kyero V3 al formato ImmoScout24.

---

## 🌟 Características / Features
- **Lectura y procesamiento** de archivos XML (Kyero V3).  
- **Transformación automática** a la estructura de ImmoScout24.  
- **Validación de fragmentos XML** antes de exportar.  
- **Descarga y gestión de imágenes**: elimina carpetas de imágenes que no corresponden al XML y evita descargar imágenes duplicadas.  
- **Registro detallado (logging)** de errores, advertencias y eventos en `descarga-imagenes.log`.

---

## 📂 Estructura de Scripts / Script Structure
- **`main.py`** – Controla el flujo principal: lectura, transformación y validación.  
- **`utils.py`** – Funciones auxiliares para manejo de XML y utilidades.  
- **`transformer.py`** – Lógica principal de conversión Kyero → ImmoScout24.  
- **`property_image_manager.py`** – Descarga y gestiona imágenes de propiedades desde el XML:  
  - Crea carpetas por ID de propiedad y descarga imágenes correspondientes.  
  - Elimina carpetas que ya no existen en el XML.  
  - Evita re-descargar imágenes que ya existen.  
  - Genera un log completo de todo el proceso en `descarga-imagenes.log`.

---

## ⚙️ Requisitos / Requirements
- Python **3.8+**
- Dependencias:
  ```bash
  pip install lxml beautifulsoup4 requests
  ```
