from lxml import etree
import logging
import html
from utils import clean_description

# Configurar logging
logger = logging.getLogger(__name__)

# Mapeo de tipos de propiedades
TYPE_MAPPING = {
    'villa': 'houseBuy',
    'apartment': 'apartmentBuy',
    'land': 'livingBuySite',
    'penthouse': 'apartmentBuy',
    'townhouse': 'houseBuy',
    'country house': 'houseBuy',
    'residential home': 'houseBuy',
    'studio': 'apartmentBuy',
    'commercial premises': 'tradeSite',
    'shop': 'tradeSite',
    'restaurant': 'tradeSite',
    'bar': 'tradeSite',
    'aparthotel': 'tradeSite',
    'hostel': 'tradeSite',
    'office': 'tradeSite',
    'apartment complex': 'tradeSite',
    'car park': 'tradeSite',
    'farm': 'livingBuySite',
    'Commercial': 'tradeSite',
    'storage': 'tradeSite',
    'warehouse': 'tradeSite',
    'ruin': 'houseBuy',
    'equestrian facility': 'tradeSite',
    'retail property': 'tradeSite',
    'marine property': 'tradeSite',
    'nightclub': 'tradeSite',
    'bed and breakfast': 'tradeSite',
    'guest house': 'tradeSite'
}

# Mapeo de tipos de construcciones para propiedades residenciales
BUILD_MAPPING = {
    'villa': 'VILLA',
    'penthouse': 'APARTMENT',
    'townhouse': 'SINGLE_FAMILY_HOUSE',
    'country house': 'SINGLE_FAMILY_HOUSE',
    'residential home': 'NO_INFORMATION',
    'apartment': 'APARTMENT',
    'studio': 'STUDIO',
    'ruin': 'NO_INFORMATION'
}

# Mapeo de recommendedUseTypes para tradeSite
RECOMMENDED_USE_MAPPING = {
    'commercial premises': 'RETAIL',
    'shop': 'RETAIL',
    'retail property': 'RETAIL',
    'Commercial': 'RETAIL',
    'storage': 'RETAIL',
    'warehouse': 'RETAIL',
    'restaurant': 'GASTRONOMY',
    'bar': 'GASTRONOMY',
    'aparthotel': 'GASTRONOMY',
    'hostel': 'GASTRONOMY',
    'nightclub': 'GASTRONOMY',
    'bed and breakfast': 'GASTRONOMY',
    'guest house': 'GASTRONOMY',
    'office': 'OFFICE',
    'apartment complex': 'OTHER',
    'car park': 'OTHER',
    'equestrian facility': 'OTHER',
    'marine property': 'OTHER'
}

# Mapeo de regiones
REGION_MAPPING = {
    'Málaga': 'Andalusien',
    'Cádiz': 'Andalusien',
    'Malaga': 'Andalusien',
    'Cadiz': 'Andalusien'
}

def transformar_xml(ruta_xml):
    """Transforma un archivo XML de entrada en una lista de diccionarios con datos de propiedades.

    Args:
        ruta_xml (str): Ruta al archivo XML de entrada.

    Returns:
        list: Lista de diccionarios con los datos transformados de las propiedades.
    """
    try:
        tree = etree.parse(ruta_xml)
        root = tree.getroot()
        properties = []

        for prop in root.findall('property'):
            prop_dict = {}
            tipo_propiedad_input = prop.findtext('type')  # Tipo original del XML
            tipo_propiedad = TYPE_MAPPING.get(tipo_propiedad_input.strip().lower(), None) if tipo_propiedad_input else None
            logger.debug(f"Tipo de propiedad encontrado: {tipo_propiedad_input} -> {tipo_propiedad} para ref {prop.findtext('ref')}")

            if not tipo_propiedad or tipo_propiedad not in TYPE_MAPPING.values():
                logger.warning(f"Tipo de propiedad no soportado o vacío: '{tipo_propiedad_input}', se omite.")
                continue

            prop_dict['type'] = tipo_propiedad
            prop_dict['externalId'] = prop.findtext('ref')
            tipo = prop.findtext('type').capitalize() or ''
            ciudad = prop.findtext('town').capitalize() or ''
            prop_dict['title'] = f"{tipo.strip()} in {ciudad.strip()}".strip()
            
            # Mapear address
            location = prop.find('location')
            prop_dict['street'] = f"Street in {ciudad.strip()}".strip()
            prop_dict['houseNumber'] = prop.findtext('house_number', '0')
            postcode = prop.findtext('postcode', '29000')
            if ' ' in postcode:
                postcode = postcode.split(' ')[0]  # Ejemplo: "29000 ESP" -> "29000"
            prop_dict['postcode'] = postcode
            prop_dict['city'] = prop.findtext('town')
            prop_dict['country'] = 'ESP'
            prop_dict['province'] = REGION_MAPPING.get(prop.findtext('province'), prop.findtext('province', 'Unknown'))
            if location is not None:
                prop_dict['latitude'] = location.findtext('latitude')
                prop_dict['longitude'] = location.findtext('longitude')
            else:
                prop_dict['latitude'] = None
                prop_dict['longitude'] = None
            
            # Mapear geoHierarchy
            geo_hierarchy = prop.find('geo_hierarchy')
            if geo_hierarchy is not None:
                prop_dict['continent_geoCodeId'] = geo_hierarchy.findtext('continent/geo_code_id')
                prop_dict['continent_fullGeoCodeId'] = geo_hierarchy.findtext('continent/full_geo_code_id')
                prop_dict['country_geoCodeId'] = geo_hierarchy.findtext('country/geo_code_id')
                prop_dict['country_fullGeoCodeId'] = geo_hierarchy.findtext('country/full_geo_code_id')
                prop_dict['region_geoCodeId'] = geo_hierarchy.findtext('region/geo_code_id')
                prop_dict['region_fullGeoCodeId'] = geo_hierarchy.findtext('region/full_geo_code_id')
                prop_dict['city_geoCodeId'] = geo_hierarchy.findtext('city/geo_code_id')
                prop_dict['city_fullGeoCodeId'] = geo_hierarchy.findtext('city/full_geo_code_id')
                prop_dict['quarter_geoCodeId'] = geo_hierarchy.findtext('quarter/geo_code_id')
                prop_dict['quarter_fullGeoCodeId'] = geo_hierarchy.findtext('quarter/full_geo_code_id')
                prop_dict['neighbourhood_geoCodeId'] = geo_hierarchy.findtext('neighbourhood/geo_code_id')
            
            prop_dict['showAddress'] = prop.findtext('show_address', 'true').lower() == 'true'
            
            # Mapear apiSearchData
            api_search_data = prop.find('api_search_data')
            if api_search_data is not None:
                prop_dict['searchField1'] = api_search_data.findtext('search_field1')
                prop_dict['searchField2'] = api_search_data.findtext('search_field2')
                prop_dict['searchField3'] = api_search_data.findtext('search_field3')
            
            prop_dict['groupNumber'] = prop.findtext('group_number')
            
            # Mapear notas descriptivas
            description = prop.find('desc')
            description_text = description.findtext('en') if description is not None else prop.findtext('description')
            if description_text:
                description_text = html.unescape(description_text)
                prop_dict['descriptionNote'] = clean_description(f"{tipo.capitalize()}: {description_text}")
            else:
                prop_dict['descriptionNote'] = clean_description(f"{tipo.capitalize()}: No description provided")
                logger.warning(f"No se encontró descripción para ref {prop_dict['externalId']}.")
            
            prop_dict['furnishingNote'] = clean_description(prop.findtext('furnishing_note')) if prop.findtext('furnishing_note') else None
            prop_dict['locationNote'] = clean_description(prop.findtext('location_note')) if prop.findtext('location_note') else None
            prop_dict['otherNote'] = clean_description(prop.findtext('other_note')) if prop.findtext('other_note') else None
            
            # Asignar tipos específicos y commercializationType según el tipo de propiedad
            if tipo_propiedad == 'houseBuy':
                prop_dict['buildingType'] = BUILD_MAPPING.get(tipo_propiedad_input.strip().lower(), 'NO_INFORMATION')
            elif tipo_propiedad == 'apartmentBuy':
                prop_dict['apartmentType'] = BUILD_MAPPING.get(tipo_propiedad_input.strip().lower(), 'NO_INFORMATION')
            elif tipo_propiedad == 'livingBuySite':
                prop_dict['commercializationType'] = 'BUY'
            elif tipo_propiedad == 'tradeSite':
                prop_dict['commercializationType'] = prop.findtext('commercialization_type', 'BUY')
                prop_dict['utilizationTradeSite'] = prop.findtext('utilization_trade_site', 'LEISURE')
                prop_dict['recommendedUseTypes'] = [RECOMMENDED_USE_MAPPING.get(tipo_propiedad_input.strip().lower(), 'NO_INFORMATION')]
                prop_dict['tenancy'] = prop.findtext('tenancy')
                prop_dict['minDivisible'] = float(prop.findtext('min_divisible', 0)) if prop.findtext('min_divisible') else None
                prop_dict['freeFrom'] = prop.findtext('free_from')
                prop_dict['shortTermConstructible'] = prop.findtext('short_term_constructible', 'false').lower() == 'true'
                prop_dict['buildingPermission'] = prop.findtext('building_permission', 'false').lower() == 'true'
                prop_dict['demolition'] = prop.findtext('demolition', 'false').lower() == 'true'
                prop_dict['siteDevelopmentType'] = prop.findtext('site_development_type', 'NO_INFORMATION')
                prop_dict['siteConstructibleType'] = prop.findtext('site_constructible_type', 'NO_INFORMATION')
                prop_dict['grz'] = float(prop.findtext('grz', 0)) if prop.findtext('grz') else None
                prop_dict['gfz'] = float(prop.findtext('gfz', 0)) if prop.findtext('gfz') else None
                prop_dict['leaseInterval'] = prop.findtext('lease_interval', 'NO_INFORMATION')
            
            # Asignar número de habitaciones solo para houseBuy y apartmentBuy
            prop_dict['numberOfBedRooms'] = prop.findtext('beds') if tipo_propiedad in ['houseBuy', 'apartmentBuy'] else None
            prop_dict['numberOfBathRooms'] = prop.findtext('baths') if tipo_propiedad in ['houseBuy', 'apartmentBuy'] else None
            
            # Asignar superficies
            surface_area = prop.find('surface_area')
            if surface_area is not None:
                prop_dict['livingSpace'] = float(surface_area.findtext('built', 0)) if surface_area.findtext('built') else None
                prop_dict['plotArea'] = float(surface_area.findtext('plot', 0)) if surface_area.findtext('plot') else None
                prop_dict['totalFloorSpace'] = float(surface_area.findtext('total', prop_dict['plotArea'] or 0)) if surface_area.findtext('total') else None
                prop_dict['netFloorSpace'] = float(surface_area.findtext('net', prop_dict['plotArea'] or 0)) if surface_area.findtext('net') else None
            else:
                prop_dict['livingSpace'] = None
                prop_dict['plotArea'] = float(prop.findtext('surface_area/total', 0)) or 0
                prop_dict['totalFloorSpace'] = prop_dict['plotArea']
                prop_dict['netFloorSpace'] = prop_dict['plotArea']
            
            prop_dict['value'] = float(prop.findtext('price', 0))
            prop_dict['currency'] = prop.findtext('currency', 'EUR')
            prop_dict['marketingType'] = prop.findtext('marketing_type', 'PURCHASE')
            prop_dict['priceIntervalType'] = prop.findtext('price_interval_type')
            prop_dict['hasCourtage'] = prop.findtext('courtage/has_courtage', 'NOT_APPLICABLE')
            prop_dict['courtage'] = prop.findtext('courtage/courtage')
            prop_dict['courtageNote'] = clean_description(prop.findtext('courtage/courtage_note')) if prop.findtext('courtage/courtage_note') else None
            
            properties.append(prop_dict)
            logger.debug(f"Propiedad transformada: {prop_dict['externalId']}")

        return properties

    except Exception as e:
        logger.error(f"Error al transformar el XML: {str(e)}")
        return []