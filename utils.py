from lxml import etree
import logging
import html
import re
from abc import ABC, abstractmethod

# Configurar logging
logger = logging.getLogger(__name__)

NSMAP = {
    'realestates': 'http://rest.immobilienscout24.de/schema/offer/realestates/1.0',
    'xlink': 'http://www.w3.org/1999/xlink',
    'common': 'http://rest.immobilienscout24.de/schema/common/1.0'
}

# Tipos de propiedades soportados para listados internacionales
SUPPORTED_PROPERTY_TYPES = {'houseBuy', 'apartmentBuy', 'livingBuySite', 'tradeSite'}

# Valores válidos para listedOnlyOnIs24
VALID_LISTED_ONLY_VALUES = ['YES', 'NO', 'NOT_APPLICABLE']

# Valores válidos para utilizationTradeSite (asumidos, pendiente de confirmación)
VALID_UTILIZATION_TRADE_TYPES = ['AGRICULTURE_FORESTRY', 'LEISURE', 'NO_INFORMATION']

# Valores válidos para commercializationType
VALID_COMMERCIALIZATION_TYPES = ['BUY', 'LEASE']

def crear_root(tipo_propiedad_tag):
    """Crea el elemento raíz con el prefijo realestates y el namespace.

    Args:
        tipo_propiedad_tag (str): Etiqueta del elemento raíz (e.g., 'houseBuy', 'tradeSite').

    Returns:
        lxml.etree.Element: Elemento raíz con el namespace configurado.

    Raises:
        ValueError: Si tipo_propiedad_tag no es una cadena válida o no está soportado.
    """
    if not isinstance(tipo_propiedad_tag, str) or not tipo_propiedad_tag:
        logger.error(f"tipo_propiedad_tag inválido: '{tipo_propiedad_tag}'")
        raise ValueError("tipo_propiedad_tag debe ser una cadena no vacía")
    if tipo_propiedad_tag not in SUPPORTED_PROPERTY_TYPES:
        logger.error(f"Tipo de propiedad no soportado: '{tipo_propiedad_tag}'. Tipos soportados: {SUPPORTED_PROPERTY_TYPES}")
        raise ValueError(f"Tipo de propiedad no soportado: '{tipo_propiedad_tag}'")
    root = etree.Element(f"{{http://rest.immobilienscout24.de/schema/offer/realestates/1.0}}{tipo_propiedad_tag}", nsmap=NSMAP)
    return root

def add_element(parent, tag, text, namespace=None):
    """Añade un elemento hijo al elemento padre con el texto proporcionado.

    Args:
        parent (lxml.etree.Element): Elemento padre al que se añadirá el hijo.
        tag (str): Nombre de la etiqueta del elemento hijo.
        text: Contenido del elemento (se convierte a cadena).
        namespace (str, optional): Namespace del elemento (e.g., 'common').

    Returns:
        lxml.etree.Element or None: Elemento creado o None si text es None.
    """
    if text is None:
        return None
    if namespace:
        elem = etree.SubElement(parent, f"{{{NSMAP[namespace]}}}{tag}")
    else:
        elem = etree.SubElement(parent, tag)
    
    # Manejar valores específicos para asegurar valores válidos
    if tag == 'listedOnlyOnIs24':
        if isinstance(text, bool):
            text = 'YES' if text else 'NO'
        elif text not in VALID_LISTED_ONLY_VALUES:
            logger.warning(f"Valor inválido para {tag}: '{text}', usando 'NO'")
            text = 'NO'
    elif tag == 'utilizationTradeSite':
        if text not in VALID_UTILIZATION_TRADE_TYPES:
            logger.warning(f"Valor inválido para {tag}: '{text}', usando 'NO_INFORMATION'")
            text = 'NO_INFORMATION'
    elif tag == 'commercializationType':
        if text not in VALID_COMMERCIALIZATION_TYPES:
            logger.warning(f"Valor inválido para {tag}: '{text}', usando 'BUY'")
            text = 'BUY'
    elif isinstance(text, bool):
        text = str(text).lower()
    
    # Envolver descriptionNote, furnishingNote, locationNote, otherNote en CDATA
    if tag in ('descriptionNote', 'furnishingNote', 'locationNote', 'otherNote'):
        elem.text = etree.CDATA(str(text))
    else:
        elem.text = str(text)
    return elem

def clean_description(text):
    """Limpia el texto de descriptionNote para asegurar que sea un xs:string válido, manteniendo saltos de línea."""
    if not text:
        return "No description provided"

    # 1. Desescapar entidades HTML (como &nbsp;, &euro;)
    text = html.unescape(text)

    # 2. Reemplazar &#13; por salto de línea explícito
    text = text.replace('&#13;', '\n')

    try:
        # 3. Parsear HTML con lxml
        from lxml import html as lxml_html
        tree = lxml_html.fromstring(text)

        # 4. Reemplazar <p>, <br> por saltos de línea
        for el in tree.iter():
            if el.tag in ('p', 'br'):
                el.tail = (el.tail or '') + '\n'

        # 5. Obtener solo el texto, incluyendo los saltos generados
        text = ''.join(tree.itertext())
    except Exception:
        pass

    # 6. Normalizar múltiples saltos seguidos
    text = re.sub(r'\n{2,}', '\n\n', text)

    # 7. Eliminar espacios extra por línea
    lines = [line.strip() for line in text.splitlines()]
    text = '\n'.join(lines).strip()

    return text

class PropertyXMLBuilder(ABC):
    """Clase abstracta para construir esquemas XML de propiedades."""
    
    @abstractmethod
    def build_xml(self, data):
        """Convierte un diccionario de datos en un XML para un tipo de propiedad específico.

        Args:
            data (dict): Diccionario con los datos de la propiedad.

        Returns:
            str or None: Cadena XML generada o None si la propiedad no es válida.

        Raises:
            ValueError: Si faltan campos obligatorios o los datos son inválidos.
        """
        pass

    def validate_required_fields(self, data, required_fields):
        """Valida que todos los campos requeridos estén presentes y no sean None."""
        for field in required_fields:
            if field not in data or data[field] is None:
                logger.error(f"El campo requerido '{field}' está ausente o es None para externalId {data.get('externalId', 'desconocido')}")
                raise ValueError(f"El campo requerido '{field}' está ausente o es None")

    def add_common_elements(self, root, data):
        """Añade elementos comunes a todos los tipos de propiedades.

        Incluye internationalCountryRegion para todas las propiedades, ya que todas son internacionales.
        """
        add_element(root, 'externalId', data.get('externalId'))
        add_element(root, 'title', data.get('title'))
        add_element(root, 'creationDate', data.get('creationDate'))
        add_element(root, 'lastModificationDate', data.get('lastModificationDate'))
        
        address = etree.SubElement(root, 'address')
        add_element(address, 'street', data.get('street'))
        add_element(address, 'houseNumber', data.get('houseNumber', '0'))
        # Usar solo el código postal numérico, sin el sufijo del país
        postcode = data.get('postcode', '29000')
        if ' ' in postcode:
            postcode = postcode.split(' ')[0]  # Ejemplo: "29000 ESP" -> "29000"
        add_element(address, 'postcode', postcode)
        add_element(address, 'city', data.get('city').capitalize() if data.get('city') else None)
        
        # Incluir internationalCountryRegion para todas las propiedades
        internacional = etree.SubElement(address, 'internationalCountryRegion')
        add_element(internacional, 'country', data.get('country', 'ESP'))
        add_element(internacional, 'region', data.get('province', 'Unknown'))
        
        # Añadir wgs84Coordinate si está disponible
        lat = float(data.get('latitude')) if data.get('latitude') else None
        lon = float(data.get('longitude')) if data.get('longitude') else None
        if lat or lon:
            wgs84 = etree.SubElement(address, 'wgs84Coordinate')
            add_element(wgs84, 'latitude', lat)
            add_element(wgs84, 'longitude', lon)
        
        descripcion = clean_description(data.get('descriptionNote'))
        if len(descripcion) > 2000:
            # Dividir en límites de párrafos para preservar estructura
            paragraphs = descripcion.split('\n\n')
            current_length = 0
            first_part = []
            second_part = []
            for p in paragraphs:
                # Sumar 2 por los \n\n entre párrafos
                if current_length + len(p) + len(first_part) * 2 <= 2000:
                    first_part.append(p)
                    current_length += len(p)
                else:
                    second_part.append(p)
            add_element(root, 'descriptionNote', '\n\n'.join(first_part))
            if second_part:
                add_element(root, 'otherNote', '\n\n'.join(second_part)[:2000])
        else:
            add_element(root, 'descriptionNote', descripcion)

        add_element(root, 'furnishingNote', data.get('furnishingNote'))
        add_element(root, 'locationNote', data.get('locationNote'))
        add_element(root, 'otherNote', data.get('otherNote'))
        add_element(root, 'showAddress', data.get('showAddress', False))

class HouseBuyBuilder(PropertyXMLBuilder):
    """Clase para construir esquemas XML de propiedades tipo houseBuy."""
    
    def build_xml(self, data):
        if data.get('type') != 'houseBuy':
            logger.warning(f"Tipo de propiedad no soportado para HouseBuyBuilder: {data.get('type')}")
            return None
        
        required_fields = ['externalId', 'title', 'value', 'livingSpace', 'plotArea']
        self.validate_required_fields(data, required_fields)
        
        try:
            root = crear_root('houseBuy')
            self.add_common_elements(root, data)
            
            add_element(root, 'buildingType', data.get('buildingType', 'NO_INFORMATION'))
            add_element(root, 'numberOfBedRooms', data.get('numberOfBedRooms'))
            add_element(root, 'numberOfBathRooms', data.get('numberOfBathRooms'))
            
            price = etree.SubElement(root, 'price')
            add_element(price, 'value', data.get('value'))
            add_element(price, 'currency', data.get('currency', 'EUR'))
            add_element(price, 'marketingType', data.get('marketingType', 'PURCHASE'))
            
            add_element(root, 'livingSpace', f"{data.get('livingSpace'):.2f}")
            add_element(root, 'plotArea', f"{data.get('plotArea'):.2f}")
            
            beds = data.get('numberOfBedRooms') or 0
            baths = data.get('numberOfBathRooms') or 0
            try:
                beds_num = int(beds)
            except (TypeError, ValueError):
                beds_num = 0
            try:
                baths_num = int(baths)
            except (TypeError, ValueError):
                baths_num = 0
            total_rooms = beds_num + baths_num
            add_element(root, 'numberOfRooms', total_rooms)
            
            courtage = etree.SubElement(root, 'courtage')
            add_element(courtage, 'hasCourtage', data.get('hasCourtage', 'NOT_APPLICABLE'))
            
            xml_output = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8').decode('utf-8')
            logger.debug(f"XML generado para houseBuy externalId {data.get('externalId')}: {xml_output}")
            return xml_output
            
        except Exception as e:
            logger.error(f"Error al generar XML para houseBuy externalId {data.get('externalId', 'desconocido')}: {str(e)}")
            raise TypeError(f"Error al generar XML: {str(e)}")

class ApartmentBuyBuilder(PropertyXMLBuilder):
    """Clase para construir esquemas XML de propiedades tipo apartmentBuy."""
    
    def build_xml(self, data):
        if data.get('type') != 'apartmentBuy':
            logger.warning(f"Tipo de propiedad no soportado para ApartmentBuyBuilder: {data.get('type')}")
            return None
        
        required_fields = ['externalId', 'title', 'value', 'livingSpace']
        self.validate_required_fields(data, required_fields)
        
        try:
            root = crear_root('apartmentBuy')
            self.add_common_elements(root, data)
            
            add_element(root, 'apartmentType', data.get('apartmentType', 'NO_INFORMATION'))
            add_element(root, 'numberOfBedRooms', data.get('numberOfBedRooms'))
            add_element(root, 'numberOfBathRooms', data.get('numberOfBathRooms'))
            
            price = etree.SubElement(root, 'price')
            add_element(price, 'value', data.get('value'))
            add_element(price, 'currency', data.get('currency', 'EUR'))
            add_element(price, 'marketingType', data.get('marketingType', 'PURCHASE'))
            
            add_element(root, 'livingSpace', f"{data.get('livingSpace'):.2f}")
            
            beds = data.get('numberOfBedRooms') or 0
            baths = data.get('numberOfBathRooms') or 0
            try:
                beds_num = int(beds)
            except (TypeError, ValueError):
                beds_num = 0
            try:
                baths_num = int(baths)
            except (TypeError, ValueError):
                baths_num = 0
            total_rooms = beds_num + baths_num
            add_element(root, 'numberOfRooms', total_rooms)
            
            courtage = etree.SubElement(root, 'courtage')
            add_element(courtage, 'hasCourtage', data.get('hasCourtage', 'NOT_APPLICABLE'))
            
            xml_output = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8').decode('utf-8')
            logger.debug(f"XML generado para apartmentBuy externalId {data.get('externalId')}: {xml_output}")
            return xml_output
            
        except Exception as e:
            logger.error(f"Error al generar XML para apartmentBuy externalId {data.get('externalId', 'desconocido')}: {str(e)}")
            raise TypeError(f"Error al generar XML: {str(e)}")

class LivingBuySiteBuilder(PropertyXMLBuilder):
    """Clase para construir esquemas XML de propiedades tipo livingBuySite."""
    
    def build_xml(self, data):
        if data.get('type') != 'livingBuySite':
            logger.warning(f"Tipo de propiedad no soportado para LivingBuySiteBuilder: {data.get('type')}")
            return None
        
        required_fields = ['externalId', 'title', 'value', 'plotArea', 'commercializationType']
        self.validate_required_fields(data, required_fields)
        
        try:
            root = crear_root('livingBuySite')
            self.add_common_elements(root, data)
            
            add_element(root, 'commercializationType', data.get('commercializationType', 'BUY'))
            
            price = etree.SubElement(root, 'price')
            add_element(price, 'value', data.get('value'))
            add_element(price, 'currency', data.get('currency', 'EUR'))
            add_element(price, 'marketingType', data.get('marketingType', 'PURCHASE'))
            
            add_element(root, 'plotArea', f"{data.get('plotArea'):.2f}")
            
            courtage = etree.SubElement(root, 'courtage')
            add_element(courtage, 'hasCourtage', data.get('hasCourtage', 'NOT_APPLICABLE'))
            
            xml_output = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8').decode('utf-8')
            logger.debug(f"XML generado para livingBuySite externalId {data.get('externalId')}: {xml_output}")
            return xml_output
            
        except Exception as e:
            logger.error(f"Error al generar XML para livingBuySite externalId {data.get('externalId', 'desconocido')}: {str(e)}")
            raise TypeError(f"Error al generar XML: {str(e)}")

class TradeSiteBuilder(PropertyXMLBuilder):
    """Clase para construir esquemas XML de propiedades tipo tradeSite (Grundstück Gewerbe).

    Usada para propiedades comerciales internacionales (e.g., commercial premises, shop, restaurant, office).
    Elementos mínimos en orden:
    - externalId
    - title
    - address (con street, houseNumber, postcode, city, internationalCountryRegion, opcionalmente wgs84Coordinate)
    - descriptionNote
    - showAddress
    - commercializationType
    - utilizationTradeSite
    - price (con value, currency, marketingType)
    - plotArea
    - courtage (con hasCourtage, courtage)
    """
    
    def build_xml(self, data):
        if data.get('type') != 'tradeSite':
            logger.warning(f"Tipo de propiedad no soportado para TradeSiteBuilder: {data.get('type')}")
            return None
        
        required_fields = ['externalId', 'title', 'value', 'plotArea', 'commercializationType', 'utilizationTradeSite']
        self.validate_required_fields(data, required_fields)
        
        try:
            root = crear_root('tradeSite')
            self.add_common_elements(root, data)
            
            add_element(root, 'commercializationType', data.get('commercializationType', 'BUY'))
            add_element(root, 'utilizationTradeSite', data.get('utilizationTradeSite', 'LEISURE'))
            
            price = etree.SubElement(root, 'price')
            add_element(price, 'value', data.get('value'))
            add_element(price, 'currency', data.get('currency', 'EUR'))
            add_element(price, 'marketingType', data.get('marketingType', 'PURCHASE'))
            
            add_element(root, 'plotArea', f"{data.get('plotArea'):.2f}")
            
            courtage = etree.SubElement(root, 'courtage')
            add_element(courtage, 'hasCourtage', data.get('hasCourtage', 'NOT_APPLICABLE'))
            add_element(courtage, 'courtage', data.get('courtage'))
            
            xml_output = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8').decode('utf-8')
            logger.debug(f"XML generado para tradeSite externalId {data.get('externalId')}: {xml_output}")
            return xml_output
            
        except Exception as e:
            logger.error(f"Error al generar XML para tradeSite externalId {data.get('externalId', 'desconocido')}: {str(e)}")
            raise TypeError(f"Error al generar XML: {str(e)}")

def dict_a_xml(data):
    """Convierte un diccionario con datos de una propiedad a XML utilizando el constructor apropiado.

    Args:
        data (dict): Diccionario con los datos de la propiedad, debe incluir 'type'.

    Returns:
        str or None: Cadena XML generada o None si la propiedad no es válida.

    Raises:
        ValueError: Si data no es un diccionario o faltan campos obligatorios.
    """
    if not isinstance(data, dict):
        logger.error("data no es un diccionario")
        raise ValueError("data debe ser un diccionario")

    if 'type' not in data or not data['type']:
        logger.warning(f"Tipo de propiedad no soportado o vacío: '{data.get('type', '')}', se omite.")
        return None

    tipo_propiedad = data['type'].strip()
    logger.debug(f"Raw tipo_propiedad detectado = '{tipo_propiedad}'")

    if tipo_propiedad not in SUPPORTED_PROPERTY_TYPES:
        logger.warning(f"Tipo de propiedad no soportado: '{tipo_propiedad}'. Tipos soportados: {SUPPORTED_PROPERTY_TYPES}")
        return None

    builders = {
        'houseBuy': HouseBuyBuilder(),
        'apartmentBuy': ApartmentBuyBuilder(),
        'livingBuySite': LivingBuySiteBuilder(),
        'tradeSite': TradeSiteBuilder()
    }

    builder = builders.get(tipo_propiedad)
    if not builder:
        logger.error(f"No se encontró un constructor para el tipo de propiedad: {tipo_propiedad}")
        return None

    return builder.build_xml(data)