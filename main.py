from transformer import transformar_xml
from sender import enviar_xml
from utils import dict_a_xml
from lxml import etree
import logging
import os
import time

# Ruta del archivo log
log_file = os.path.join(os.path.dirname(__file__), 'app.log')

# Configurar logging para guardar en archivo
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w', encoding='utf-8'),
        logging.StreamHandler()  # Opcional: muestra también por consola
    ]
)

logger = logging.getLogger(__name__)

def main():
    ruta_entrada = 'input/bv.xml'
    ruta_salida_base = 'output/transformado'

    # Crear directorio de salida si no existe
    os.makedirs(ruta_salida_base, exist_ok=True)

    # Log del XML de entrada
    try:
        tree = etree.parse(ruta_entrada)
        logger.debug(f"XML de entrada:\n{etree.tostring(tree, pretty_print=True).decode()}")
    except Exception as e:
        logger.error(f"Error al leer el XML de entrada: {str(e)}")
        print(f"Error al leer el XML de entrada: {str(e)}")
        return

    # Obtener lista de diccionarios de propiedades
    properties = transformar_xml(ruta_entrada)
    if not properties:
        logger.error("No se encontraron propiedades válidas en el archivo XML.")
        print("⚠️ No se encontraron propiedades válidas. No se genera XML.")
        return

    # Procesar cada propiedad
    generated_properties = 0
    sent_properties = 0
    for prop_dict in properties:
        external_id = prop_dict.get('externalId', 'desconocido')
        try:
            logger.debug(f"Procesando propiedad: {external_id}")
            xml_transformado = dict_a_xml(prop_dict)
            if xml_transformado:
                # Guardar XML individual
                ruta_salida = os.path.join(ruta_salida_base, f"transformado_{external_id}.xml")
                with open(ruta_salida, 'wb') as f:
                    f.write(xml_transformado.encode('utf-8'))
                logger.info(f"XML guardado en {ruta_salida}")
                generated_properties += 1

                # Validar XML antes de enviarlo
                try:
                    etree.fromstring(xml_transformado)
                    logger.debug(f"XML válido para {external_id}")
                except etree.XMLSyntaxError as e:
                    logger.error(f"XML inválido para {external_id}: {str(e)}")
                    print(f"XML inválido para {external_id}: {str(e)}")
                    continue

                # Enviar XML
                try:
                    #respuesta = enviar_xml(xml_transformado)
                    logger.info(f"Propiedad {external_id} - Código de respuesta: {respuesta.status_code}")
                    logger.info(f"Propiedad {external_id} - Respuesta: {respuesta.text}")
                    print(f"Propiedad {external_id} - Código de respuesta: {respuesta.status_code}")
                    print(f"Propiedad {external_id} - Respuesta: {respuesta.text}")
                    sent_properties += 1
                except Exception as e:
                    logger.error(f"Error al enviar XML para {external_id}: {str(e)}")
                    print(f"Error al enviar XML para {external_id}: {str(e)}")
                
                # Retraso para evitar límites de la API
                time.sleep(1)
            else:
                logger.warning(f"Propiedad {external_id} omitida por tipo no válido.")
                print(f"Propiedad {external_id} omitida por tipo no válido.")
        except Exception as e:
            logger.error(f"Error al procesar propiedad {external_id}: {str(e)}")
            print(f"Error al procesar propiedad {external_id}: {str(e)}")

    if generated_properties == 0:
        logger.error("No se generó XML para ninguna propiedad.")
        print("⚠️ No se generó XML para ninguna propiedad.")
        return

    logger.info(f"Se generaron {generated_properties} XMLs válidos.")
    logger.info(f"Se enviaron {sent_properties} propiedades a la API.")
    print(f"Se generaron {generated_properties} XMLs válidos.")
    print(f"Se enviaron {sent_properties} propiedades a la API.")

if __name__ == '__main__':
    main()