import logging
import re
import google.generativeai as genai
from typing import List, Dict, Any, Tuple
import config

# Configure logging
logger = logging.getLogger(__name__)

class WordTranslator:
    """
    Class to handle translation of uncommon words to Turkish
    """
    def __init__(self):
        """Initialize the word translator"""
        self.translation_cache = {}  # Cache for previously translated words
        logger.info("Word translator initialized")

    def detect_uncommon_words(self, text: str, language: str) -> List[str]:
        """
        Detect potentially uncommon words in the text

        Args:
            text: The text to analyze
            language: The detected language of the text

        Returns:
            List of potentially uncommon words
        """
        # If the text is already in Turkish, no need to translate
        if language.lower() == "turkish":
            return []

        # If language is not specified, use the default (German)
        if not language or language.lower() == "unknown":
            language = config.DEFAULT_TRANSLATION_LANGUAGE

        # Extract all words with 2+ characters to catch more German words
        all_words_pattern = re.compile(r'\b[a-zA-ZäöüßÄÖÜçğıöşüÇĞİÖŞÜ]{2,}\b')
        all_words = all_words_pattern.findall(text)

        # Get unique words (case-insensitive)
        unique_words = set()
        for word in all_words:
            unique_words.add(word.lower())

        # Convert back to list with original case for the first occurrence
        word_map = {}
        for word in all_words:
            word_lower = word.lower()
            if word_lower not in word_map:
                word_map[word_lower] = word

        # Get all unique words in their original form
        all_unique_words = list(word_map.values())

        # Filter out already translated words and proper nouns
        candidate_words = []
        for word in all_unique_words:
            word_lower = word.lower()

            # Skip if the word is already in our cache and is A2 or above
            if word_lower in self.translation_cache:
                cached_data = self.translation_cache[word_lower]
                # Check if cached_data is a tuple and has the expected format
                if isinstance(cached_data, tuple) and len(cached_data) == 2:
                    cached_translation, cached_level = cached_data
                    if cached_translation != "[SKIP]" and cached_level not in ["A1", "[A1]"]:
                        # If already translated and not skipped/A1, skip
                        continue
                    else:
                        # If cached data is in old format, assume it should be re-translated
                        pass # Do not continue, process the word


            # Skip words that are likely proper nouns (capitalized in the middle of a sentence)
            if word[0].isupper() and not word_lower.isupper():
                # Check if it's not at the beginning of a sentence
                word_index = text.find(word)
                if word_index > 0 and text[word_index-1] not in ".!?\n":
                    # Still include it if it appears elsewhere in lowercase form
                    lowercase_version = word.lower()
                    if text.find(lowercase_version) >= 0:
                        candidate_words.append(lowercase_version)
                    continue

            # Add to the list of candidate words
            candidate_words.append(word)

        # We'll let Gemini determine the level of each word during translation
        # No limit on the number of candidates - translate all found words
        logger.debug(f"Found {len(candidate_words)} candidate words from {len(all_words)} total words")
        return candidate_words

    async def translate_uncommon_words(self, text: str, language: str) -> Tuple[str, Dict[str, str]]:
        """
        Detect and translate uncommon words in the text

        Args:
            text: The text to process
            language: The detected language of the text

        Returns:
            Tuple of (processed text, dictionary of translations)
        """
        try:
            # If the text is already in Turkish, no need to translate
            if language.lower() == "turkish":
                return text, {}

            # Detect uncommon words using our main algorithm
            uncommon_words = self.detect_uncommon_words(text, language)

            # No minimum word requirement - we'll translate whatever we find
            # No predefined word lists - only translate words found in the text

            logger.info(f"Detected/selected {len(uncommon_words)} words for translation")

            # Translate the uncommon words
            translations = await self._get_translations(uncommon_words, language)

            # Update the cache with new translations
            self.translation_cache.update(translations)

            # Return the original text and the translations
            return text, translations

        except Exception as e:
            logger.error(f"Error translating uncommon words: {e}")
            return text, {}

    async def translate_uncommon_words_in_text(self, text: str, words_list: List[str], language: str) -> Tuple[str, Dict[str, str]]:
        """
        Translate specific words that appear in the text

        Args:
            text: The text to process
            words_list: List of words to consider for translation
            language: The detected language of the text

        Returns:
            Tuple of (processed text, dictionary of translations)
        """
        try:
            # If the text is already in Turkish, no need to translate
            if language.lower() == "turkish":
                return text, {}

            # Filter out words that are likely proper nouns or already in our cache
            candidate_words = []
            cached_translations = {}

            for word in words_list:
                word_lower = word.lower()

                # If the word is already in our cache, use the cached translation
                if word_lower in self.translation_cache:
                    cached_translations[word_lower] = self.translation_cache[word_lower]
                    continue

                # Skip words that are likely proper nouns (capitalized in the middle of a sentence)
                if word[0].isupper() and not word_lower.isupper():
                    # Check if it's not at the beginning of a sentence
                    word_index = text.find(word)
                    if word_index > 0 and text[word_index-1] not in ".!?\n":
                        continue

                # Add to the list of candidate words
                candidate_words.append(word)

            logger.info(f"Found {len(candidate_words)} new candidate words and {len(cached_translations)} cached translations")

            # No limit on the number of candidates - translate all found words

            # Translate the candidate words
            new_translations = await self._get_translations(candidate_words, language)

            # Update the cache with new translations
            self.translation_cache.update(new_translations)

            # Combine cached and new translations
            all_translations = {**cached_translations, **new_translations}

            # Return the original text and the translations
            return text, all_translations

        except Exception as e:
            logger.error(f"Error translating specific words in text: {e}")
            return text, {}

    async def force_translate_words(self, words_list: List[str], language: str) -> Tuple[str, Dict[str, str]]:
        """
        Force translate words regardless of their level

        Args:
            words_list: List of words to translate
            language: The detected language of the words

        Returns:
            Tuple of (empty string, dictionary of translations)
        """
        try:
            # If no words or Turkish language, return empty
            if not words_list or language.lower() == "turkish":
                return "", {}

            # If language is not specified, use the default (German)
            if not language or language.lower() == "unknown":
                language = config.DEFAULT_TRANSLATION_LANGUAGE

            # Filter out words already in our cache
            new_words = []
            cached_translations = {}

            for word in words_list:
                word_lower = word.lower()

                # If the word is already in our cache, use the cached translation
                if word_lower in self.translation_cache:
                    cached_translations[word_lower] = self.translation_cache[word_lower]
                    continue

                # Add to the list of new words
                new_words.append(word)

            logger.info(f"Forcing translation of {len(new_words)} words")

            # Create a special prompt for Gemini to translate these words regardless of level
            prompt = f"""
            You are a professional linguist specializing in translating words from {language} to Turkish.

            For each of the following {language} words:
            1. Determine the CEFR level (A1, A2, B1, B2, C1, C2)
            2. Provide the Turkish translation
            3. IMPORTANT: Translate ALL words with level A2 and above
            4. Only skip proper nouns, words that are already Turkish, or words below A2 level (A1)
            5. Be especially careful to identify and translate A2, B1, B2, C1 and C2 level words

            Words to translate:
            {", ".join(new_words)}

            Format your response exactly like this example:
            leistung = B1 = başarı
            einfluss = B1 = etki
            lösung = B1 = çözüm
            bequem = A2 = rahat
            verbessern = A2 = geliştirmek
            ephemer = C2 = geçici
            allgegenwärtig = C1 = her yerde bulunan
            kontroverse = B2 = tartışma
            gut = A1 = [SKIP]
            Hans = [SKIP]

            Note: In the final output, I will include the word, CEFR level, and translation.
            """

            # Use Gemini to translate the words
            model = genai.GenerativeModel(
                model_name=config.GEMINI_TRANSLATION_MODEL,
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                },
                safety_settings=config.SAFETY_SETTINGS
            )

            response = model.generate_content(prompt)

            # Parse the response
            forced_translations = {}

            for line in response.text.strip().split('\n'):
                if '=' in line:
                    # Format should be: word = CEFR_LEVEL = translation
                    parts = line.split('=', 2)






            # Update the cache with new translations
            self.translation_cache.update(forced_translations)

            # Combine cached and forced translations
            all_translations = {**cached_translations, **forced_translations}

            return "", all_translations

        except Exception as e:
            logger.error(f"Error force translating words: {e}")
            return "", {}

    async def _get_translations(self, words: List[str], source_language: str) -> Dict[str, str]:
        """
        Get translations for a list of words using Gemini

        Args:
            words: List of words to translate
            source_language: Source language of the words

        Returns:
            Dictionary mapping words to their Turkish translations
        """
        if not words:
            return {}

        try:
            # If source language is not specified, use the default (German)
            if not source_language or source_language.lower() == "unknown":
                source_language = config.DEFAULT_TRANSLATION_LANGUAGE

            # Create a prompt for Gemini to translate the words and determine their CEFR level
            prompt = f"""
            You are a professional linguist specializing in translating words from {source_language} to Turkish.

            For each of the following {source_language} words:
            1. Determine the CEFR level (A1, A2, B1, B2, C1, C2)
            2. Provide the Turkish translation
            3. IMPORTANT: Translate ALL words with level A2 and above
            4. Only skip proper nouns, words that are already Turkish, or words below A2 level (A1)
            5. Be especially careful to identify and translate A2, B1, B2, C1 and C2 level words

            CEFR LEVEL GUIDELINES:
            - A1 (Beginner): Very basic, everyday words that beginners learn first (e.g., "gut", "haus", "wasser")
            - A2 (Elementary): Common words used in everyday situations (e.g., "bequem", "verbessern", "vorschlagen")
            - B1 (Intermediate): More abstract words and less common everyday vocabulary (e.g., "leistung", "einfluss", "lösung")
            - B2 (Upper Intermediate): More specialized vocabulary and abstract concepts (e.g., "kontroverse", "perspektive", "nachhaltig")
            - C1 (Advanced): Sophisticated vocabulary, idioms, and specialized terms (e.g., "mehrdeutig", "akribisch", "pragmatisch")
            - C2 (Proficiency): Very rare words, highly specialized terms (e.g., "ephemer", "allgegenwärtig", "quintessenz")

            Words to translate:
            {", ".join(words)}

            Format your response exactly like this example:
            leistung = B1 = başarı
            einfluss = B1 = etki
            lösung = B1 = çözüm
            bequem = A2 = rahat
            verbessern = A2 = geliştirmek
            ephemer = C2 = geçici
            allgegenwärtig = C1 = her yerde bulunan
            kontroverse = B2 = tartışma
            gut = A1 = [SKIP]
            Hans = [SKIP]

            Note: In the final output, I will include the word, CEFR level, and translation.
            """

            # Use Gemini to translate the words
            model = genai.GenerativeModel(
                model_name=config.GEMINI_TRANSLATION_MODEL,
                generation_config={
                    "temperature": 0.2,  # Slightly higher temperature for more natural translations
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                },
                safety_settings=config.SAFETY_SETTINGS
            )

            response = model.generate_content(prompt)

            # Parse the response
            translations = {}
            cefr_levels = {}

            for line in response.text.strip().split('\n'):
                if '=' in line:
                    # Format should be: word = CEFR_LEVEL = translation
                    parts = line.split('=', 2)






            # Log the CEFR levels for debugging
            if cefr_levels:
                logger.info(f"CEFR levels: {cefr_levels}")

            logger.info(f"Translated {len(translations)} words")
            return translations

        except Exception as e:
            logger.error(f"Error getting translations: {e}")
            return {}

    def format_translations_for_response(self, translations: Dict[str, tuple]) -> str:
        """
        Format translations for inclusion in the response

        Args:
            translations: Dictionary of word translations with CEFR levels

        Returns:
            Formatted string with translations
        """
        if not translations:
            return ""

        # Create a clear, easy-to-read format for word translations
        translation_text = "\n\n--- Wörterübersetzungen (Kelime Çevirileri) ---\n"

        # Sort translations alphabetically for consistency
        sorted_translations = sorted(translations.items())

        for word, translation_data in sorted_translations:
            # Check if translation_data is a tuple (translation, level)
            if isinstance(translation_data, tuple) and len(translation_data) == 2:
                translation, level = translation_data
                # Format: German word = Turkish translation (level)
                translation_text += f"• {word} = {translation} ({level})\n"
            else:
                # Fallback for old format (should not happen)
                translation_text += f"• {word} = {translation_data}\n"

        return translation_text

# Create a singleton instance
word_translator = WordTranslator()
