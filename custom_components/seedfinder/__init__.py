"""The Seedfinder integration."""

import asyncio
from datetime import datetime, timedelta
import logging
import os
import re
import urllib.parse
import aiohttp
from bs4 import BeautifulSoup

import async_timeout
import voluptuous as vol

from homeassistant import exceptions
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import async_generate_entity_id

from homeassistant.util import raise_if_invalid_filename, slugify

from homeassistant.components.persistent_notification import (
    create as create_notification,
)

from .const import (
    ATTR_ALIAS,
    ATTR_API,
    ATTR_HOURS,
    ATTR_IMAGE,
    ATTR_SPECIES,
    ATTR_PLANT_INSTANCE,
    ATTR_WEBSITE,
    ATTR_INFOTEXT1,
    ATTR_INFOTEXT2,
    ATTR_EFFECTS,
    ATTR_SMELL,
    ATTR_TASTE,
    ATTR_LINEAGE,
    CACHE_TIME,
    DOMAIN,
    FLOW_DOWNLOAD_IMAGES,
    FLOW_DOWNLOAD_PATH,
    OPB_ATTR_RESULTS,
    OPB_ATTR_TIMESTAMP,
    OPB_DISPLAY_PID,
    OPB_PID,
    OPB_SERVICE_CLEAN_CACHE,
    OPB_SERVICE_GET,
    OPB_INFO_MESSAGE,
    OPB_CURRENT_INFO_MESSAGE,
    ATTR_BREEDER,
    DEFAULT_IMAGE_PATH,
)

from .plantbook_exception import SeedfinderException

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Seedfinder component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Seedfinder from a config entry."""

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    if ATTR_SPECIES not in hass.data[DOMAIN]:
        hass.data[DOMAIN][ATTR_SPECIES] = {}

    # Display one-off notification about new functionality after upgrade
    if not entry.data.get(OPB_INFO_MESSAGE):
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, OPB_INFO_MESSAGE: OPB_CURRENT_INFO_MESSAGE}
        )

    def extract_values_by_text(header_text, soup):
        header = soup.find('h4', string=header_text)
        if header:
            values = [div.get_text(strip=True) for div in header.find_next('div').find_all('div', class_='bg-primary-500')]
            return values
        return []

    def extract_zoomist_container(soup):
        zoomist_container = soup.find("div", class_="zoomist-container")
        if not zoomist_container:
            return "No lineage data found"
        root = zoomist_container.find("ul")
        if not root:
            return "No lineage tree found"
        return parse_tree(root)

    def parse_tree(element, depth=0):
        tree = ""
        if (element.name == "a"):
            text = element.get_text(strip=True)
            href = element.get("href", "#")
            tree += "    " * depth + f"- {text} ##$##  {href}\n"

        for child in element.find_all("li", recursive=False):
            link = child.find("a")
            if link:
                tree += parse_tree(link, depth + 2)
            nested_ul = child.find("ul")
            if nested_ul:
                tree += parse_tree(nested_ul, depth + 2)
        return tree

    def format_text(text):
        # Liste der Eigenschaften, die wir suchen
        properties = [
            "Art der Sorte:", "THC:", "CBD:", "Genetischer hintergrund:", 
            "Art:", "Ertrag Indoor:", "Ertrag Outdoor:", "Höhe Indoor:", 
            "Höhe Outdoor:", "Blütephase:", "Erntemonat:", "Klimazone:", 
            "Wirkung:", "Geschmack:"
        ]
        
        # Textmuster für Überschriften
        headers = [
            "Apple Fritter:", "Wirkung und Geschmack von", "Anbaueigenschaften von"
        ]
        
        # Bereinige den Text von mehrfachen Leerzeichen
        temp_text = ' '.join(text.split())
        
        # Extrahiere die Eigenschaften
        property_lines = []
        for prop in properties:
            if prop in temp_text:
                start = temp_text.find(prop)
                next_prop_start = float('inf')
                
                # Finde die nächste Eigenschaft
                for next_prop in properties:
                    if next_prop != prop:
                        pos = temp_text.find(next_prop, start + len(prop))
                        if pos != -1 and pos < next_prop_start:
                            next_prop_start = pos
                
                # Extrahiere den Wert
                if next_prop_start == float('inf'):
                    value = temp_text[start:].strip()
                else:
                    value = temp_text[start:next_prop_start].strip()
                
                # Entferne den verarbeiteten Teil aus dem temporären Text
                temp_text = temp_text[:start] + temp_text[start + len(value):]
                
                # Füge die Eigenschaft zur Liste hinzu
                property_lines.append(value)
        
        # Verarbeite den Haupttext
        main_text = temp_text.strip()
        for header in headers:
            main_text = main_text.replace(header, f"\n{header}")
        
        # Teile den Haupttext in Zeilen
        main_lines = [line.strip() for line in main_text.split('\n') if line.strip()]
        
        # Füge alle Teile zusammen
        result = []
        
        # Füge den Haupttext hinzu
        if main_lines:
            result.extend(main_lines)
        
        # Füge die Eigenschaften hinzu
        if property_lines:
            if result:  # Wenn es bereits Text gibt, füge eine Leerzeile ein
                result.append('')
            result.extend(property_lines)
        
        # Verbinde alles mit einzelnen Zeilenumbrüchen
        return '\n'.join(result)

    def extract_strain_image(soup):
        """Extract the main strain image from the page."""
        img_tags = soup.find_all("img")
        for img in img_tags:
            # Suche nach dem :src Attribut, das das Hauptbild enthält
            src_attr = img.get(":src")
            if src_attr and "selectedIndex === -1 ?" in src_attr:
                # Extrahiere die URL zwischen den ersten Anführungszeichen
                url_start = src_attr.find("'") + 1
                url_end = src_attr.find("'", url_start)
                main_image_url = src_attr[url_start:url_end]
                _LOGGER.debug("Found main image URL: %s", main_image_url)
                return main_image_url
        
        _LOGGER.debug("No main image found in the page")
        return None

    async def download_and_save_image(session, image_url, species, breeder, download_path):
        """Download and save image to local path."""
        if not image_url:
            return None
            
        try:
            # Erstelle saubere Dateinamen
            filename = f"{breeder.replace(' ', '_')}_{species.replace(' ', '_')}.jpg"
            filepath = os.path.join(download_path, filename)
            
            # Erstelle die URL für Home Assistant
            www_path = download_path.split('/www/')[-1] if '/www/' in download_path else download_path
            local_url = f"/local/{www_path}/{filename}"
            
            # Prüfe ob der Download-Pfad existiert
            if not os.path.exists(download_path):
                os.makedirs(download_path)
            
            # Lade das Bild herunter
            async with session.get(image_url) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to download image from %s", image_url)
                    return None
                    
                image_data = await response.read()
            
            # Speichere das Bild asynchron
            def write_file():
                with open(filepath, "wb") as f:
                    f.write(image_data)
            
            # Führe die Datei-Operation in einem Thread aus
            await hass.async_add_executor_job(write_file)
                
            _LOGGER.debug("Saved image to %s, URL: %s", filepath, local_url)
            return local_url
            
        except Exception as ex:
            _LOGGER.error("Error saving image: %s", ex)
            return None

    async def get_plant(call: ServiceCall) -> ServiceResponse:
        if DOMAIN not in hass.data:
            _LOGGER.error("no data found for domain %s", DOMAIN)
            raise SeedfinderException("no data found for domain %s", DOMAIN)

        # Get config entry
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            raise SeedfinderException("No config entry found")
        entry = entries[0]

        species = call.data.get(ATTR_SPECIES)
        breeder = call.data.get(ATTR_BREEDER)
        
        if species is None or breeder is None:
            raise SeedfinderException(
                "invalid service call, required attributes species and breeder missing"
            )

        _LOGGER.debug("get_plant %s from %s", species, breeder)
        
        try:
            # First load breeder page to get strain details
            breeder_url = f'https://seedfinder.eu/de/database/breeder/{breeder.lower().replace(" ", "_")}/'
            _LOGGER.debug("Fetching from breeder URL: %s", breeder_url)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(breeder_url) as response:
                    if response.status != 200:
                        raise SeedfinderException(f"HTTP error {response.status} for URL {breeder_url}")
                    content = await response.text()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find the strain in the breeder's table
            table = soup.find('table', class_='table')
            if not table:
                raise SeedfinderException(f"No strain table found for breeder {breeder}")
                
            rows = table.find('tbody').find_all('tr')
            
            # Look for the specific strain
            strain_data = None
            for row in rows:
                cells = row.find_all('td')
                if not cells:
                    continue
                    
                strain_name = cells[0].find('a')
                if strain_name and strain_name.text.strip().lower() == species.lower():
                    strain_url = strain_name['href']
                    strain_data = {
                        'link': strain_url,
                        'name': strain_name.text.strip(),
                        'breeder': cells[1].text.strip(),
                        'flowertime': cells[2].text.strip(),
                        'type': cells[3].text.strip(),
                        'feminized': cells[4].text.strip() if len(cells) > 4 else None
                    }
                    break
            
            if not strain_data:
                raise SeedfinderException(f"Strain {species} not found for breeder {breeder}")

            # Get additional strain information
            async with aiohttp.ClientSession() as session:
                # Hole strain Informationen
                async with session.get(strain_data['link']) as response:
                    if response.status != 200:
                        raise SeedfinderException(f"HTTP error {response.status} for URL {strain_data['link']}")
                    strain_content = await response.text()

                strain_soup = BeautifulSoup(strain_content, 'html.parser')
                
                # Extract additional information
                headers = strain_soup.find_all('h2')
                info_texts = []
                for header in headers:
                    next_p = header.find_next('p')
                    if next_p:
                        # Entferne HTML-Tags und bereinige den Text
                        header_text = ' '.join(header.get_text(strip=True).split())
                        paragraph_text = format_text(next_p.get_text(strip=True))
                        info_texts.append({
                            "header": header_text,
                            "text": paragraph_text
                        })

                # Extract effects, smell, and taste
                effects = extract_values_by_text('Effect/Effectiveness', strain_soup)
                smells = extract_values_by_text('Smell / Aroma', strain_soup)
                tastes = extract_values_by_text('Taste', strain_soup)
                
                # Extract lineage
                lineage = extract_zoomist_container(strain_soup)

                # Extract strain image and download it in the same session
                image_url = extract_strain_image(strain_soup)
                local_image_path = None
                
                if image_url:
                    # Prüfe ob Bilder heruntergeladen werden sollen
                    download_images = entry.options.get(FLOW_DOWNLOAD_IMAGES, False)
                    download_path = entry.options.get(FLOW_DOWNLOAD_PATH, DEFAULT_IMAGE_PATH)
                    
                    if download_images:
                        local_image_path = await download_and_save_image(
                            session,  # Verwende die aktive Session
                            image_url, 
                            species,
                            breeder,
                            download_path
                        )

            # Build response data
            pid = f"{species.lower().replace(' ', '-')}-{breeder.lower().replace(' ', '-')}"
            plant_data = {
                "pid": pid,
                "strain": strain_data['name'],
                "breeder": strain_data['breeder'],
                "image_url": local_image_path if local_image_path else image_url,
                "flowertime": strain_data['flowertime'],
                "type": strain_data['type'],
                "feminized": strain_data['feminized'],
                "website": strain_data['link'],
                "infotext1": f"{info_texts[0]['header']}\n{info_texts[0]['text']}" if info_texts else "",
                "infotext2": f"{info_texts[1]['header']}\n{info_texts[1]['text']}" if len(info_texts) > 1 else "",
                "effects": ", ".join(effects),
                "smell": ", ".join(smells),
                "taste": ", ".join(tastes),
                "lineage": lineage,
                "timestamp": datetime.now().isoformat()
            }

            # Store in cache
            hass.data[DOMAIN][ATTR_SPECIES][pid] = plant_data
            
            # Set state
            entity_id = async_generate_entity_id(
                f"{DOMAIN}.{{}}", plant_data["pid"], current_ids={}
            )
            hass.states.async_set(entity_id, species, plant_data)
            
            return plant_data

        except Exception as ex:
            _LOGGER.error("Error fetching data from seedfinder: %s", ex)
            raise SeedfinderException(f"Error fetching data: {str(ex)}")

    async def clean_cache(call: ServiceCall) -> None:
        hours = call.data.get(ATTR_HOURS)
        if hours is None or not isinstance(hours, int):
            hours = CACHE_TIME
        if ATTR_SPECIES in hass.data[DOMAIN]:
            for species in list(hass.data[DOMAIN][ATTR_SPECIES]):
                value = hass.data[DOMAIN][ATTR_SPECIES][species]
                if datetime.now() > datetime.fromisoformat(
                    value[OPB_ATTR_TIMESTAMP]
                ) + timedelta(hours=hours):
                    _LOGGER.debug("Removing %s from cache", species)
                    entity_id = async_generate_entity_id(
                        f"{DOMAIN}.{{}}", value[OPB_PID], current_ids={}
                    )
                    hass.states.async_remove(entity_id)
                    hass.data[DOMAIN][ATTR_SPECIES].pop(species)

    # Setup optionFlow updates listener
    entry.async_on_unload(entry.add_update_listener(config_update_listener))

    hass.services.async_register(
        DOMAIN, OPB_SERVICE_GET, get_plant, None, SupportsResponse.OPTIONAL
    )
    hass.services.async_register(
        DOMAIN, OPB_SERVICE_CLEAN_CACHE, clean_cache, None, SupportsResponse.NONE
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.debug("Unloading %s", DOMAIN)
    _LOGGER.debug("Removing cache")
    await hass.services.async_call(
        domain=DOMAIN,
        service=OPB_SERVICE_CLEAN_CACHE,
        service_data={ATTR_HOURS: 0},
        blocking=True,
    )
    _LOGGER.debug("Removing services")
    hass.services.async_remove(DOMAIN, OPB_SERVICE_GET)
    hass.services.async_remove(DOMAIN, OPB_SERVICE_CLEAN_CACHE)
    # And we get rid of the rest
    hass.data.pop(DOMAIN)

    return True


async def config_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle component's options update"""
    _LOGGER.debug("Options update: %s, %s", entry.entry_id, entry.options)


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
