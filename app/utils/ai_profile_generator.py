"""
AI Profile Generator using OpenAI
Generates personalized profiles based on wishlist items
"""
import logging
from typing import List, Dict
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)


def generate_birthday_person_profile(items: List[Dict], owner_name: str, description: str) -> str:
    """
    Generate a personalized profile of the birthday person based on their wishlist items

    Args:
        items: List of wishlist items (title, description, product_url)
        owner_name: Name of the birthday person
        description: Wishlist description

    Returns:
        Generated profile text describing the person's interests and personality
    """
    try:
        logger.info("="*80)
        logger.info("🎂 INICIANDO GENERACIÓN DE PERFIL")
        logger.info(f"📝 Nombre del cumpleañero: {owner_name}")
        logger.info(f"📋 Descripción de la lista: {description}")
        logger.info(f"🎁 Número de items: {len(items)}")
        logger.info(f"🎁 Items recibidos: {items}")

        # Initialize OpenAI client
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # If no items, generate profile from description only
        if not items:
            logger.warning("⚠️ No hay items, generando perfil solo con descripción")
            return _generate_profile_from_description(client, owner_name, description)

        # Build context from items
        items_text = "\n".join([
            f"- {item.get('title', 'Item')}: {item.get('description', '')}"
            for item in items
        ])

        logger.info(f"📦 Texto de items preparado:\n{items_text}")

        # Create prompt for OpenAI
        prompt = f"""Analiza los productos de la lista de {owner_name} y genera un perfil breve y directo.

Descripción: {description}

Productos:
{items_text}

Genera un perfil de 2-3 párrafos cortos que siga este formato:
- Primer párrafo: "A '{owner_name}' le gustan los productos de [tipo/categoría]. Muestra interés en [categorías específicas]."
- Segundo párrafo: Menciona los tipos de productos específicos y qué revelan sobre sus gustos
- Tercer párrafo: Conclusión simple sobre qué tipo de regalos le gustarían

Instrucciones:
- Usa el formato directo: "A [nombre] le gustan...", "Muestra interés en..."
- Identifica las categorías principales (tecnología, deportes, hogar, etc.)
- Sé específico sobre los tipos de productos
- Máximo 3 párrafos cortos
- No uses saludos ni introduciones largas
- Escribe en tercera persona

Escribe en español."""

        logger.info("🤖 PROMPT ENVIADO A OPENAI:")
        logger.info(prompt)
        logger.info("-"*80)

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un asistente que analiza listas de productos y crea perfiles concisos y directos. Escribes de forma clara, específica y sin rodeos. Usas el formato: 'A [nombre] le gustan los productos de [tipo]. Muestra interés en [categorías].' Siempre escribes en tercera persona."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=300,
            temperature=0.6,
        )

        # Extract generated profile
        profile = response.choices[0].message.content.strip()

        logger.info("✅ RESPUESTA DE OPENAI:")
        logger.info(profile)
        logger.info("="*80)
        logger.info(f"Successfully generated profile for {owner_name}")
        return profile

    except Exception as e:
        logger.error(f"❌ Error generating AI profile: {e}")
        logger.exception(e)
        # Return a fallback profile
        return _generate_fallback_profile(owner_name, description, items)


def _generate_profile_from_description(client: OpenAI, owner_name: str, description: str) -> str:
    """Generate profile when no items are available yet"""
    try:
        prompt = f"""Crea un perfil breve y amigable para {owner_name} basándote en esta descripción de su lista de cumpleaños:

"{description}"

Genera un perfil de 1-2 párrafos que:
1. Capte la esencia de lo que describe
2. Sea positivo y celebratorio
3. Use un tono cálido y personal

Escribe en español."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un asistente que crea perfiles personales amigables y cálidos."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=200,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Error generating profile from description: {e}")
        return _generate_fallback_profile(owner_name, description, [])


def _generate_fallback_profile(owner_name: str, description: str, items: List[Dict]) -> str:
    """Generate a simple fallback profile when AI fails"""
    if items:
        item_count = len(items)
        return f"""{owner_name} tiene gustos variados e interesantes! Con {item_count} {'producto' if item_count == 1 else 'productos'} en su lista, podemos ver que disfruta de cosas especiales y únicas.

{description}

¡Cualquier regalo que elijas de su lista seguramente le encantará! 🎁"""
    else:
        return f"""{owner_name} está creando su lista de deseos perfecta para este año!

{description}

¡Pronto habrá productos increíbles para elegir! 🎁"""


def should_regenerate_profile(
    old_items: List[Dict],
    new_items: List[Dict],
    old_description: str,
    new_description: str
) -> bool:
    """
    Determine if profile should be regenerated based on changes

    Returns True if:
    - Description changed significantly
    - Number of items changed by more than 20%
    - New items were added
    """
    # If description changed, regenerate
    if old_description != new_description:
        return True

    # If items count changed significantly, regenerate
    old_count = len(old_items)
    new_count = len(new_items)

    if old_count == 0 and new_count > 0:
        return True

    if old_count > 0:
        change_percentage = abs(new_count - old_count) / old_count
        if change_percentage > 0.2:  # More than 20% change
            return True

    # If new items were added (titles don't match)
    old_titles = {item.get('title') for item in old_items}
    new_titles = {item.get('title') for item in new_items}

    if new_titles != old_titles:
        return True

    return False
