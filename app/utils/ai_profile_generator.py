"""
AI Profile Generator using OpenAI
Generates personalized profiles based on wishlist items
"""
import logging
from typing import List, Dict
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)


def generate_birthday_person_profile(items: List[Dict], owner_name: str, description: str, wishlist_title: str = "") -> str:
    """
    Generate a personalized profile of the birthday person based on their wishlist items

    Args:
        items: List of wishlist items (title, description, product_url). Should NOT include pooled_gift items.
        owner_name: Name of the birthday person
        description: Wishlist description
        wishlist_title: Title of the wishlist (optional but recommended)

    Returns:
        Generated profile text describing the person's interests and personality
    """
    try:
        logger.info("="*80)
        logger.info("🎂 INICIANDO GENERACIÓN DE PERFIL")
        logger.info(f"📝 Nombre del cumpleañero: {owner_name}")
        logger.info(f"🎯 Título de la lista: {wishlist_title}")
        logger.info(f"📋 Descripción de la lista: {description}")
        logger.info(f"🎁 Número de items: {len(items)}")
        logger.info(f"🎁 Items recibidos: {items}")

        # If no items, don't generate profile - return empty string
        if not items or len(items) == 0:
            logger.warning("⚠️ No hay items (o solo hay colectas), NO se generará perfil con AI")
            return ""

        # Initialize OpenAI client
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # Build context from items
        items_text = "\n".join([
            f"- {item.get('title', 'Item')}: {item.get('description', '')}"
            for item in items
        ])

        logger.info(f"📦 Texto de items preparado:\n{items_text}")

        # Build context with optional title
        title_context = f"\nTítulo de la lista: {wishlist_title}" if wishlist_title else ""

        # Create prompt for OpenAI - oriented for friends to understand the person
        prompt = f"""Eres un asistente que ayuda a los amigos y familiares a conocer mejor a la persona que celebra su cumpleaños, basándote en los productos que eligió para su lista de deseos.

Nombre: {owner_name}{title_context}
Descripción de la lista: {description}

Productos en su lista:
{items_text}

Tu tarea: Analiza estos productos y genera un perfil de 2-3 párrafos que ayude a los amigos a entender mejor los gustos, intereses y personalidad de {owner_name}. Este perfil es para que los invitados puedan elegir el regalo perfecto o conocer mejor a {owner_name}.

Formato esperado:
- Párrafo 1: Describe las principales categorías de interés de {owner_name} (ej: tecnología, deportes, lectura, moda, etc.) basándote en los productos. Sé específico sobre QUÉ le gusta exactamente.
- Párrafo 2: Profundiza en su personalidad y estilo de vida. ¿Qué revelan estos productos sobre {owner_name}? (ej: es aventurero, creativo, hogareño, deportista, etc.)
- Párrafo 3: Sugiere tipos de regalos alternativos o complementarios que encajarían con su perfil, considerando el contexto del título y descripción de la lista.

Instrucciones importantes:
- Escribe en tercera persona ("A {owner_name} le encanta...", "{owner_name} tiene un gusto por...")
- Sé observador y perspicaz - conecta los productos con rasgos de personalidad
- Usa el título de la lista como contexto adicional para entender la ocasión y preferencias
- Sé cálido, positivo y descriptivo
- Si ves patrones claros (ej: todo tecnología, todo deportivo), mencionalo específicamente
- Ayuda a los amigos a entender no solo QUÉ le gusta, sino QUIÉN es {owner_name}
- Máximo 3 párrafos, cada uno de 2-3 oraciones

Escribe en español, de forma natural y amigable."""

        logger.info("🤖 PROMPT ENVIADO A OPENAI:")
        logger.info(prompt)
        logger.info("-"*80)

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un asistente experto en analizar gustos y preferencias de personas basándote en sus elecciones de productos. Tu objetivo es ayudar a amigos y familiares a conocer mejor a la persona del cumpleaños para elegir el regalo perfecto. Escribes perfiles perspicaces, cálidos y descriptivos que revelan personalidad e intereses. Siempre escribes en tercera persona y en español."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=400,
            temperature=0.7,
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
        # Return a fallback profile (only if there are items)
        return _generate_fallback_profile(owner_name, description, items, wishlist_title)


def _generate_fallback_profile(owner_name: str, description: str, items: List[Dict], wishlist_title: str = "") -> str:
    """Generate a simple fallback profile when AI fails"""
    # If no items, don't generate a profile
    if not items or len(items) == 0:
        logger.warning("No items available, skipping fallback profile generation")
        return ""

    # Only generate fallback if there are items but AI failed
    title_mention = f" para '{wishlist_title}'" if wishlist_title else ""
    item_count = len(items)

    return f"""{owner_name} ha preparado una lista especial{title_mention} con {item_count} {'producto' if item_count == 1 else 'productos'} cuidadosamente seleccionados que reflejan sus gustos únicos.

{description}

Cada regalo en esta lista ha sido elegido pensando en lo que realmente le gusta, así que cualquier opción será perfecta. ¡Ayuda a hacer su día especial! 🎁"""


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
