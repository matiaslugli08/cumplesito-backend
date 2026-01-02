"""
MercadoLibre specific scraper
Uses HTML scraping with anti-detection techniques
"""
import requests
from bs4 import BeautifulSoup
import logging
from typing import Optional, Dict
import re
import traceback

logger = logging.getLogger(__name__)


def extract_mercadolibre_metadata(url: str) -> Dict[str, Optional[str]]:
    """
    Extract metadata from MercadoLibre by extracting product ID and using API

    MercadoLibre pages require JavaScript, so we extract the product ID from the URL
    and use their public API with a different approach.

    Args:
        url: MercadoLibre product URL

    Returns:
        Dictionary with title, image, description, and price
    """
    metadata = {
        "title": None,
        "image": None,
        "description": None,
        "price": None
    }

    try:
        # Extract product ID from URL
        # URLs can be like:
        # https://www.mercadolibre.com.uy/.../p/MLU14287437
        # https://articulo.mercadolibre.com.uy/.../MLU-123456789

        patterns = [
            r'/p/(ML[A-Z]\d+)',  # /p/MLU14287437
            r'/(ML[A-Z][-\d]+)',  # MLU-123456789 or MLU123456789
            r'-(ML[A-Z]\d+)',     # -MLU14287437
        ]

        product_id = None
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                product_id = match.group(1).replace('-', '')  # Remove dashes
                break

        if not product_id:
            logger.warning(f"Could not extract MercadoLibre product ID from URL: {url}")
            return metadata

        logger.info(f"Extracted MercadoLibre product ID: {product_id}")

        # Try the API without authentication - use a simple request
        api_url = f"https://api.mercadolibre.com/items/{product_id}"

        logger.info(f"Trying MercadoLibre API: {api_url}")

        # Simple headers for API request
        headers = {
            'User-Agent': 'curl/7.64.1',  # Simple user agent
            'Accept': 'application/json',
        }

        response = requests.get(api_url, headers=headers, timeout=10)

        logger.info(f"MercadoLibre API response: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            # Extract title
            if data.get("title"):
                metadata["title"] = data["title"]
                logger.info(f"Found title: {metadata['title'][:50]}")

            # Extract main image
            if data.get("pictures") and len(data["pictures"]) > 0:
                # Get the first picture URL (high quality)
                pic = data["pictures"][0]
                metadata["image"] = pic.get("secure_url") or pic.get("url")

                # Try to get highest quality
                if metadata["image"] and '-I.' in metadata["image"]:
                    metadata["image"] = metadata["image"].replace('-I.', '-O.')

                logger.info(f"Found image from pictures array")

            elif data.get("thumbnail"):
                metadata["image"] = data["thumbnail"]
                # Upgrade thumbnail to higher quality
                if '-I.' in metadata["image"]:
                    metadata["image"] = metadata["image"].replace('-I.', '-O.')
                elif '-S.' in metadata["image"]:
                    metadata["image"] = metadata["image"].replace('-S.', '-O.')
                logger.info(f"Found image from thumbnail")

            # Extract price
            price = data.get("price")
            currency = data.get("currency_id", "")
            if price:
                metadata["price"] = f"{currency} {price:,.0f}"
                logger.info(f"Found price: {metadata['price']}")

            # Extract description from attributes
            attributes = data.get("attributes", [])
            if attributes:
                desc_parts = []
                for attr in attributes[:3]:  # First 3 attributes
                    name = attr.get('name', '')
                    value = attr.get('value_name', '')
                    if name and value:
                        desc_parts.append(f"{name}: {value}")

                if desc_parts:
                    metadata["description"] = " | ".join(desc_parts)
                    logger.info(f"Created description from attributes")

            # Fallback description
            if not metadata["description"]:
                condition = data.get("condition", "")
                if condition == "new":
                    metadata["description"] = "Producto nuevo"
                elif condition == "used":
                    metadata["description"] = "Producto usado"

            logger.info(f"Successfully extracted metadata from MercadoLibre API")

        else:
            logger.warning(f"MercadoLibre API returned status {response.status_code}")
            if response.status_code == 403:
                logger.warning("API access forbidden - trying alternative approach")
            logger.warning(f"Response: {response.text[:200]}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching MercadoLibre page: {e}")
    except Exception as e:
        logger.error(f"Unexpected error scraping MercadoLibre: {e}")
        logger.error(traceback.format_exc())

    return metadata


def is_mercadolibre_url(url: str) -> bool:
    """
    Check if a URL is from MercadoLibre

    Args:
        url: URL to check

    Returns:
        True if it's a MercadoLibre URL
    """
    ml_domains = [
        'mercadolibre.com',
        'mercadolibre.com.ar',
        'mercadolibre.com.mx',
        'mercadolibre.com.co',
        'mercadolibre.cl',
        'mercadolibre.com.pe',
        'mercadolibre.com.uy',
        'mercadolibre.com.ve',
        'mercadolibre.com.br',
        'mercadolibre.com.ec',
        'mercadolibre.com.bo',
        'mercadolibre.com.py',
        'mercadolibre.com.cr',
        'mercadolibre.com.pa',
        'mercadolibre.com.hn',
        'mercadolibre.com.sv',
        'mercadolibre.com.ni',
        'mercadolibre.com.gt',
        'mercadolibre.com.do',
        'articulo.mercadolibre',
    ]

    url_lower = url.lower()
    return any(domain in url_lower for domain in ml_domains)
