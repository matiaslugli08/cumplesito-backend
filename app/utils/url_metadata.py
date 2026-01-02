"""
URL Metadata Extractor
Extracts metadata (title, image, description) from product URLs
Special handling for MercadoLibre
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
import logging
import re
import time

logger = logging.getLogger(__name__)


def extract_url_metadata(url: str, timeout: int = 15) -> Dict[str, Optional[str]]:
    """
    Main entry point for extracting metadata from any URL
    Automatically detects MercadoLibre and uses specialized scraper
    """
    # Check if it's MercadoLibre and use specialized scraper
    from app.utils.mercadolibre_scraper import is_mercadolibre_url, extract_mercadolibre_metadata

    if is_mercadolibre_url(url):
        logger.info(f"Detected MercadoLibre URL, using specialized scraper")
        metadata = extract_mercadolibre_metadata(url)
        if metadata.get("title") or metadata.get("image"):  # If successful
            logger.info(f"MercadoLibre scraper successful: {metadata}")
            return metadata
        # If specialized scraper fails, fall back to regular scraping
        logger.warning("MercadoLibre specialized scraper failed, falling back to regular scraping")

    # Continue with regular scraping for other sites
    return _extract_url_metadata_scraping(url, timeout)


def _extract_url_metadata_scraping(url: str, timeout: int = 15) -> Dict[str, Optional[str]]:
    """
    Extract metadata from a URL using Open Graph tags and fallbacks

    Args:
        url: The URL to extract metadata from
        timeout: Request timeout in seconds

    Returns:
        Dictionary with title, image, description, and price (if available)
    """
    metadata = {
        "title": None,
        "image": None,
        "description": None,
        "price": None
    }

    try:
        # Clean URL - remove tracking parameters for MercadoLibre
        from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
        parsed = urlparse(url)

        # For MercadoLibre, keep only essential parameters
        if 'mercadolibre' in parsed.netloc:
            # Remove all fragment identifiers (everything after #)
            url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, '', ''))

        # Set headers to mimic a real browser (more realistic)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-419,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }

        # Make request with session for better cookie handling
        session = requests.Session()
        session.headers.update(headers)

        response = session.get(url, timeout=timeout, allow_redirects=True)
        response.raise_for_status()

        # For debugging
        logger.info(f"Response status: {response.status_code}, URL: {response.url}")

        # Parse HTML - try lxml first, fallback to html.parser
        try:
            soup = BeautifulSoup(response.content, 'lxml')
        except Exception:
            soup = BeautifulSoup(response.content, 'html.parser')

        # Extract title - MercadoLibre specific handling
        title_candidates = [
            _get_meta_content(soup, 'og:title'),
            _get_meta_content(soup, 'twitter:title'),
            _get_meta_content(soup, 'title'),
        ]

        # Try to find h1 with product title (MercadoLibre uses this)
        if not any(title_candidates):
            h1 = soup.find('h1')
            if h1:
                title_candidates.append(h1.get_text().strip())

        # Fallback to page title
        if not any(title_candidates) and soup.find('title'):
            title_candidates.append(soup.find('title').get_text().strip())

        title_candidates.append(_get_meta_content(soup, 'product:title'))

        metadata["title"] = next((t for t in title_candidates if t), None)

        # Extract image - try multiple methods
        image_candidates = [
            _get_meta_content(soup, 'og:image'),
            _get_meta_content(soup, 'og:image:url'),
            _get_meta_content(soup, 'twitter:image'),
            _get_meta_content(soup, 'twitter:image:src'),
            _get_link_href(soup, 'image_src'),
        ]

        # MercadoLibre specific: look for main product image
        if not any(image_candidates):
            # Try to find img with specific classes or data attributes
            img_selectors = [
                'img[data-zoom]',  # MercadoLibre uses this
                'img.ui-pdp-image',  # Product detail page image
                'figure.ui-pdp-gallery__figure img',  # Gallery images
                'div.ui-pdp-gallery img',  # Gallery container
                'figure img',  # Common pattern
                'img[class*="image"]',  # Any image class
            ]
            for selector in img_selectors:
                imgs = soup.select(selector)
                for img in imgs:
                    src = img.get('src') or img.get('data-src') or img.get('data-zoom')
                    if src and not any(skip in src.lower() for skip in ['logo', 'icon', 'sprite', 'avatar']):
                        image_candidates.append(src)
                        break
                if image_candidates and image_candidates[-1]:
                    break

        # Fallback to general image extraction
        if not any(image_candidates):
            image_candidates.append(_extract_first_product_image(soup, url))

        metadata["image"] = next((img for img in image_candidates if img), None)

        # Extract description
        metadata["description"] = (
            _get_meta_content(soup, 'og:description') or
            _get_meta_content(soup, 'twitter:description') or
            _get_meta_content(soup, 'description') or
            _get_meta_content(soup, 'product:description')
        )

        # Extract price (bonus)
        metadata["price"] = (
            _get_meta_content(soup, 'og:price:amount') or
            _get_meta_content(soup, 'product:price:amount') or
            _extract_price_from_page(soup)
        )

        # Clean up metadata
        if metadata["title"]:
            metadata["title"] = metadata["title"][:200].strip()

        if metadata["description"]:
            metadata["description"] = metadata["description"][:500].strip()

        # Ensure image URL is absolute
        if metadata["image"] and not metadata["image"].startswith(('http://', 'https://')):
            from urllib.parse import urljoin
            metadata["image"] = urljoin(url, metadata["image"])

        logger.info(f"Successfully extracted metadata from {url}")

    except requests.exceptions.Timeout:
        logger.error(f"Timeout extracting metadata from {url}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error extracting metadata from {url}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error extracting metadata from {url}: {e}")

    return metadata


def _get_meta_content(soup: BeautifulSoup, property_name: str) -> Optional[str]:
    """Get content from meta tag by property or name"""
    # Try property attribute (Open Graph)
    tag = soup.find('meta', property=property_name)
    if tag and tag.get('content'):
        return tag['content']

    # Try name attribute (Twitter, regular meta)
    tag = soup.find('meta', attrs={'name': property_name})
    if tag and tag.get('content'):
        return tag['content']

    # Try itemprop attribute (Schema.org)
    tag = soup.find('meta', attrs={'itemprop': property_name})
    if tag and tag.get('content'):
        return tag['content']

    return None


def _get_link_href(soup: BeautifulSoup, rel_name: str) -> Optional[str]:
    """Get href from link tag by rel attribute"""
    tag = soup.find('link', rel=rel_name)
    if tag and tag.get('href'):
        return tag['href']
    return None


def _extract_first_product_image(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    """
    Fallback: Try to find the first prominent image on the page
    Looks for images with common product class names or large dimensions
    """
    # Common class names for product images
    product_class_names = [
        'product-image', 'product_image', 'productImage',
        'main-image', 'main_image', 'mainImage',
        'item-image', 'item_image', 'itemImage',
        'gallery-image', 'gallery_image'
    ]

    # Try to find by class name
    for class_name in product_class_names:
        img = soup.find('img', class_=lambda x: x and class_name.lower() in x.lower())
        if img:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src:
                return src

    # Try to find by itemprop (Schema.org)
    img = soup.find('img', attrs={'itemprop': 'image'})
    if img:
        src = img.get('src') or img.get('data-src')
        if src:
            return src

    # Fallback: Find largest image (by dimensions in attributes)
    images = soup.find_all('img')
    largest_img = None
    max_size = 0

    for img in images:
        try:
            width = int(img.get('width', 0) or 0)
            height = int(img.get('height', 0) or 0)
            size = width * height

            if size > max_size and size > 10000:  # At least 100x100
                src = img.get('src') or img.get('data-src')
                if src and not any(skip in src.lower() for skip in ['logo', 'icon', 'avatar', 'sprite']):
                    largest_img = src
                    max_size = size
        except (ValueError, TypeError):
            continue

    return largest_img


def _extract_price_from_page(soup: BeautifulSoup) -> Optional[str]:
    """
    Try to extract price from common price elements
    """
    # Try itemprop price
    price_elem = soup.find(attrs={'itemprop': 'price'})
    if price_elem:
        return price_elem.get('content') or price_elem.get_text().strip()

    # Try common price class names
    price_classes = ['price', 'product-price', 'product_price', 'item-price']
    for class_name in price_classes:
        price_elem = soup.find(class_=lambda x: x and class_name in x.lower())
        if price_elem:
            text = price_elem.get_text().strip()
            if text and any(char.isdigit() for char in text):
                return text

    return None


def validate_image_url(image_url: str) -> bool:
    """
    Validate that an image URL is accessible

    Args:
        image_url: URL to validate

    Returns:
        True if image is accessible, False otherwise
    """
    try:
        response = requests.head(image_url, timeout=5, allow_redirects=True)
        content_type = response.headers.get('content-type', '')
        return response.status_code == 200 and 'image' in content_type.lower()
    except Exception:
        return False
