"""Gemini API utilities for NER and query expansion fallback"""

import os
import json
from .logger import setup_logger

logger = setup_logger('GeminiAPI')


def _get_client():
    """Get Gemini API client"""
    try:
        from google import genai
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not set in environment")
            return None
        return genai.Client(api_key=api_key)
    except ImportError:
        logger.warning("google-genai package not installed. Run: pip install google-genai")
        return None


def get_synonyms(word: str, language: str = "english", max_synonyms: int = 5) -> list:
    """
    Get synonyms for a word using Gemini API

    Args:
        word: Word to find synonyms for
        language: 'english' or 'bangla'
        max_synonyms: Maximum number of synonyms to return

    Returns:
        List of synonyms (empty list if API fails)
    """
    client = _get_client()
    if not client:
        return []

    try:
        from google.genai import types

        lang_name = "Bengali/Bangla" if language == "bangla" else "English"

        prompt = f"""Give me {max_synonyms} synonyms for the word "{word}" in {lang_name}.
Return ONLY a JSON array of synonyms, nothing else. Example: ["synonym1", "synonym2"]
If the word has no synonyms or you don't know, return an empty array: []"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            )],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=200,
            )
        )

        # Parse JSON response
        text = response.text.strip()
        # Handle markdown code blocks
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        synonyms = json.loads(text)
        if isinstance(synonyms, list):
            logger.debug(f"Gemini synonyms for '{word}': {synonyms}")
            return synonyms[:max_synonyms]
        return []

    except Exception as e:
        logger.warning(f"Gemini API synonym lookup failed for '{word}': {e}")
        return []


def map_entity(entity: str, source_lang: str, target_lang: str) -> str:
    """
    Map a named entity from source language to target language using Gemini

    Args:
        entity: Entity text to map
        source_lang: 'english' or 'bangla'
        target_lang: 'english' or 'bangla'

    Returns:
        Mapped entity in target language (or original if mapping fails)
    """
    if source_lang == target_lang:
        return entity

    client = _get_client()
    if not client:
        return entity

    try:
        from google.genai import types

        src_name = "Bengali/Bangla" if source_lang == "bangla" else "English"
        tgt_name = "Bengali/Bangla" if target_lang == "bangla" else "English"

        prompt = f"""Translate this named entity from {src_name} to {tgt_name}: "{entity}"

This is a proper noun (person name, place, organization, etc). Provide the standard translation/transliteration used in {tgt_name}.
Return ONLY the translated entity, nothing else. If you cannot translate it, return the original text."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            )],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=100,
            )
        )

        result = response.text.strip().strip('"\'')
        if result:
            logger.debug(f"Gemini mapped entity '{entity}' -> '{result}'")
            return result
        return entity

    except Exception as e:
        logger.warning(f"Gemini API entity mapping failed for '{entity}': {e}")
        return entity


def extract_entities(text: str, language: str = "english") -> list:
    """
    Extract named entities from text using Gemini API

    Args:
        text: Input text
        language: 'english' or 'bangla'

    Returns:
        List of dicts with entity info: [{'text': str, 'label': str, 'method': 'gemini_ner'}]
    """
    client = _get_client()
    if not client:
        return []

    try:
        from google.genai import types

        prompt = f"""Extract all named entities from this text: "{text}"

Return a JSON array of objects with 'text' (the entity) and 'label' (entity type like PERSON, ORG, GPE, LOC, DATE, etc).
Example: [{{"text": "Bangladesh", "label": "GPE"}}, {{"text": "Sheikh Hasina", "label": "PERSON"}}]
If no entities found, return: []"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            )],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=500,
            )
        )

        # Parse JSON response
        result_text = response.text.strip()
        # Handle markdown code blocks
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()

        entities = json.loads(result_text)
        if isinstance(entities, list):
            # Add method marker and find positions
            for ent in entities:
                ent['method'] = 'gemini_ner'
                # Find position in original text
                start = text.lower().find(ent['text'].lower())
                ent['start'] = start if start >= 0 else 0
                ent['end'] = (start + len(ent['text'])) if start >= 0 else len(ent['text'])

            logger.debug(f"Gemini extracted {len(entities)} entities from text")
            return entities
        return []

    except Exception as e:
        logger.warning(f"Gemini API entity extraction failed: {e}")
        return []


def is_available() -> bool:
    """Check if Gemini API is available (API key set and package installed)"""
    try:
        from google import genai
        return os.environ.get("GEMINI_API_KEY") is not None
    except ImportError:
        return False
