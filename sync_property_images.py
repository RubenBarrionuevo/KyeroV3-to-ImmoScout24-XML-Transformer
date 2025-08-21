import os
import requests
import xml.etree.ElementTree as ET
import html
import logging
import shutil

# Configuración de logs
log_file = 'descarga-imagenes.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logging.info(f"Directorio de trabajo actual: {os.getcwd()}")

# Ruta del archivo XML
xml_path = 'input/bv.xml'
logging.info(f"Intentando leer XML: {xml_path}")

if not os.path.exists(xml_path):
    logging.error(f"Error: El archivo {xml_path} no existe.")
    exit(1)

# Carpeta base donde guardar las imágenes
base_folder = 'images'
os.makedirs(base_folder, exist_ok=True)
logging.info(f"Directorio de imágenes: {os.path.abspath(base_folder)}")

# Parsear el XML
try:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    logging.info("XML parseado correctamente.")
except Exception as e:
    logging.error(f"Error al parsear el XML: {e}")
    exit(1)

# Obtener lista de IDs del XML
properties = root.findall('.//property')
xml_ids = set()
for property_node in properties:
    id_node = property_node.find('id')
    if id_node is not None and id_node.text:
        xml_ids.add(id_node.text.strip())

logging.info(f"Número total de propiedades encontradas: {len(properties)}")

# Eliminar carpetas que no tengan correspondencia en el XML
existing_folders = [f for f in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, f))]
for folder in existing_folders:
    if folder not in xml_ids:
        folder_path = os.path.join(base_folder, folder)
        try:
            shutil.rmtree(folder_path)
            logging.info(f"Carpeta eliminada por no existir en XML: {folder_path}")
        except Exception as e:
            logging.error(f"Error al eliminar carpeta {folder_path}: {e}")

valid_properties = 0
skipped_properties = 0

# Iterar por cada propiedad
for i, property_node in enumerate(properties, 1):
    id_node = property_node.find('id')
    property_id = id_node.text.strip() if id_node is not None and id_node.text else None
    logging.info(f"Propiedad #{i}: ID = {property_id}")
    
    if not property_id:
        logging.warning("Propiedad sin ID, saltando...")
        skipped_properties += 1
        logging.debug(f"Contenido de la propiedad sin ID: {ET.tostring(property_node, encoding='unicode', method='xml')[:500]}")
        continue
    
    valid_properties += 1
    property_folder = os.path.join(base_folder, property_id)
    os.makedirs(property_folder, exist_ok=True)

    images = property_node.findall('.//images/image')
    logging.info(f"Número de imágenes para propiedad {property_id}: {len(images)}")
    if not images:
        logging.warning(f"No se encontraron imágenes para la propiedad {property_id}")
        continue

    for image_node in images:
        url_node = image_node.find('url')
        if url_node is not None and url_node.text:
            image_url = html.unescape(url_node.text.strip())
            image_id = image_node.get('id', 'unknown')
            image_path = os.path.join(property_folder, f'image_{image_id}.jpg')

            # Si ya existe la imagen, no descargarla nuevamente
            if os.path.exists(image_path):
                logging.info(f"Imagen ya existe, se omite descarga: {image_path}")
                continue

            logging.info(f"Intentando descargar: {image_url}")
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(image_url, headers=headers, timeout=10)
                response.raise_for_status()

                with open(image_path, 'wb') as f:
                    f.write(response.content)
                logging.info(f'✔ Imagen guardada: {image_path}')
            except Exception as e:
                logging.error(f'✘ Error al descargar {image_url}: {e}')
        else:
            logging.warning(f"URL no válida o vacía en imagen ID: {image_node.get('id', 'sin_id')}")

logging.info(f"Resumen:")
logging.info(f"Propiedades válidas procesadas: {valid_properties}")
logging.info(f"Propiedades saltadas (sin ID): {skipped_properties}")
