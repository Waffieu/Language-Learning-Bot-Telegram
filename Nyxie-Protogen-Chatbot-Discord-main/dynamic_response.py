import logging
import random
from typing import Dict, Any, Optional, Tuple
import config

# Configure logging
logger = logging.getLogger(__name__)

class DynamicResponseManager:
    """
    Class to handle dynamic response length, language level, and style
    """
    def __init__(self):
        """Initialize the dynamic response manager"""
        self.last_response_type = None
        self.consecutive_same_type_count = 0
        self.last_language_level = None
        self.consecutive_same_level_count = 0
        logger.info("Dynamic response manager initialized")

    def get_response_type(self, message_content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Determine the type of response to generate based on probabilities and context

        Args:
            message_content: The user's message content
            context: Optional context information about the conversation

        Returns:
            Response type: "extremely_short", "slightly_short", "medium", "slightly_long", or "long"
        """
        if not config.DYNAMIC_MESSAGE_LENGTH_ENABLED:
            return "medium"  # Default to medium if dynamic length is disabled

        # Base probabilities from config
        probabilities = {
            "extremely_short": config.EXTREMELY_SHORT_RESPONSE_PROBABILITY,
            "slightly_short": config.SLIGHTLY_SHORT_RESPONSE_PROBABILITY,
            "medium": config.MEDIUM_RESPONSE_PROBABILITY,
            "slightly_long": config.SLIGHTLY_LONG_RESPONSE_PROBABILITY,
            "long": config.LONG_RESPONSE_PROBABILITY
        }

        # Adjust probabilities based on message content
        self._adjust_probabilities_for_content(probabilities, message_content)

        # Adjust probabilities based on conversation context
        if context:
            self._adjust_probabilities_for_context(probabilities, context)

        # Adjust probabilities to avoid repetitive patterns
        self._adjust_probabilities_for_variety(probabilities)

        # Apply randomness factor
        self._apply_randomness(probabilities)

        # Normalize probabilities
        total = sum(probabilities.values())
        normalized_probabilities = {k: v/total for k, v in probabilities.items()}

        # Select response type based on probabilities
        response_type = self._select_response_type(normalized_probabilities)

        # Update tracking variables
        if response_type == self.last_response_type:
            self.consecutive_same_type_count += 1
        else:
            self.consecutive_same_type_count = 0
            self.last_response_type = response_type

        logger.debug(f"Selected response type: {response_type}")
        return response_type

    def _adjust_probabilities_for_content(self, probabilities: Dict[str, float], message_content: str) -> None:
        """
        Adjust probabilities based on the user's message content to favor longer responses

        Args:
            probabilities: The current probability distribution
            message_content: The user's message content
        """
        # Adjust probabilities based on the user's message content
        # General adjustment to favor shorter/medium responses more often
        probabilities["extremely_short"] *= 1.2
        probabilities["slightly_short"] *= 1.5
        probabilities["medium"] *= 1.3
        probabilities["slightly_long"] *= 0.8
        probabilities["long"] *= 0.6

        # Specific adjustments based on message content length and type
        if len(message_content) < 50:
            probabilities["slightly_long"] *= 0.9
            probabilities["long"] *= 0.7
        elif len(message_content) < 100:
            probabilities["slightly_long"] *= 1.0
            probabilities["long"] *= 0.8
        elif len(message_content) > 200:
            probabilities["extremely_short"] *= 0.5
            probabilities["slightly_short"] *= 0.7
            probabilities["medium"] *= 1.0
            probabilities["slightly_long"] *= 1.2
            probabilities["long"] *= 1.5

        # Questions get slightly longer responses, but not excessively long
        if "?" in message_content:
            probabilities["extremely_short"] *= 0.7
            probabilities["slightly_short"] *= 0.9
            probabilities["medium"] *= 1.1
            probabilities["slightly_long"] *= 1.3
            probabilities["long"] *= 1.1

        # Commands or requests get slightly longer responses
        command_indicators = ["please", "can you", "could you", "would you", "tell me", "show me", "help me", "explain"]
        if any(indicator in message_content.lower() for indicator in command_indicators):
            probabilities["extremely_short"] *= 0.8
            probabilities["slightly_short"] *= 0.9
            probabilities["medium"] *= 1.0
            probabilities["slightly_long"] *= 1.2
            probabilities["long"] *= 1.1

        # Only greetings get shorter responses
        greeting_indicators = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "what's up", "sup", "yo"]
        if any(message_content.lower().startswith(greeting) for greeting in greeting_indicators):
            probabilities["extremely_short"] *= 1.5
            probabilities["slightly_short"] *= 1.8
            probabilities["medium"] *= 1.0
            probabilities["slightly_long"] *= 0.7
            probabilities["long"] *= 0.4

    def _adjust_probabilities_for_context(self, probabilities: Dict[str, float], context: Dict[str, Any]) -> None:
        """
        Adjust probabilities based on conversation context to favor longer responses

        Args:
            probabilities: The current probability distribution
            context: Context information about the conversation
        """
        # Adjust probabilities based on conversation context
        # Reduce the tendency to always give long responses based on context
        if context.get("is_first_message", False):
            probabilities["extremely_short"] *= 0.8
            probabilities["slightly_short"] *= 1.2
            probabilities["medium"] *= 1.5
            probabilities["slightly_long"] *= 1.0
            probabilities["long"] *= 0.8

        # If the conversation has been going on for a while, slightly favor medium responses
        if context.get("message_count", 0) > 5:
            probabilities["extremely_short"] *= 0.9
            probabilities["slightly_short"] *= 1.0
            probabilities["medium"] *= 1.2
            probabilities["slightly_long"] *= 1.0
            probabilities["long"] *= 0.9

        # If there's media, slightly favor longer descriptions but not excessively
        if context.get("has_media", False):
            probabilities["extremely_short"] *= 0.7
            probabilities["slightly_short"] *= 0.8
            probabilities["medium"] *= 1.0
            probabilities["slightly_long"] *= 1.3
            probabilities["long"] *= 1.2

    def _adjust_probabilities_for_variety(self, probabilities: Dict[str, float]) -> None:
        """
        Adjust probabilities to avoid repetitive patterns

        Args:
            probabilities: The current probability distribution
        """
        # If we've had the same response type multiple times in a row, reduce its probability
        if self.consecutive_same_type_count > 0 and self.last_response_type:
            # More aggressive reduction to avoid repetition
            reduction_factor = min(0.3, 0.8 ** self.consecutive_same_type_count)
            probabilities[self.last_response_type] *= reduction_factor

            # Create natural variation in response length
            if self.consecutive_same_type_count >= 1:
                # If we've been giving extremely short responses, favor slightly short and medium
                if self.last_response_type == "extremely_short":
                    probabilities["slightly_short"] *= 2.0
                    probabilities["medium"] *= 1.8
                    probabilities["slightly_long"] *= 1.2
                    # Still allow some extremely short responses for natural variation
                    if random.random() < 0.3:
                        probabilities["extremely_short"] *= 0.8

                # If we've been giving slightly short responses, favor medium and extremely short
                elif self.last_response_type == "slightly_short":
                    probabilities["medium"] *= 2.0
                    probabilities["extremely_short"] *= 1.5
                    probabilities["slightly_long"] *= 1.2

                # If we've been giving medium responses, favor slightly short and slightly long
                elif self.last_response_type == "medium":
                    probabilities["slightly_short"] *= 1.8
                    probabilities["slightly_long"] *= 1.8
                    probabilities["extremely_short"] *= 1.2
                    probabilities["long"] *= 1.2

                # If we've been giving slightly long responses, favor medium and long
                elif self.last_response_type == "slightly_long":
                    probabilities["medium"] *= 1.8
                    probabilities["long"] *= 1.5
                    probabilities["slightly_short"] *= 1.2

                # If we've been giving long responses, favor medium and slightly long
                elif self.last_response_type == "long":
                    probabilities["medium"] *= 2.0
                    probabilities["slightly_long"] *= 1.5
                    probabilities["slightly_short"] *= 1.2
                    probabilities["extremely_short"] *= 0.8  # Reduce but don't eliminate

            # Occasionally introduce completely random variation for more natural patterns
            if random.random() < 0.15:  # Reduced from 0.2
                # Choose a random response type with weighted probability
                response_types = list(probabilities.keys())
                weights = [0.2, 0.25, 0.3, 0.15, 0.1]  # Match our base probabilities
                random_type = random.choices(response_types, weights=weights, k=1)[0]
                # Boost its probability moderately
                probabilities[random_type] *= 2.5  # Reduced from 4.0

    def _apply_randomness(self, probabilities: Dict[str, float]) -> None:
        """
        Apply extreme randomness factor to probabilities for completely unpredictable response lengths

        Args:
            probabilities: The current probability distribution
        """
        # Maksimum randomness (1.0) kullanarak tamamen öngörülemez yanıt uzunlukları oluştur
        randomness = 1.0  # Her zaman maksimum randomness kullan
        for key in probabilities:
            # Daha geniş bir aralıkta rastgele ayarlama uygula
            random_adjustment = 1.0 + randomness * (random.random() * 4 - 2.0)  # -2.0 ile 2.0 arasında değişim
            probabilities[key] *= random_adjustment

        # Daha sık olarak tamamen rastgele bir yanıt türünü seç ve olasılığını büyük ölçüde artır
        if random.random() < 0.5:  # %50 olasılıkla
            # Kısa yanıtlara daha fazla ağırlık ver
            weights = [0.35, 0.30, 0.20, 0.10, 0.05]  # Kısa yanıtlara daha yüksek ağırlık
            response_types = list(probabilities.keys())
            random_key = random.choices(response_types, weights=weights, k=1)[0]
            probabilities[random_key] *= random.uniform(3.0, 8.0)  # 3-8 kat artış

        # Bazen de tamamen rastgele bir yanıt türünü seçerek gerçek insan davranışını taklit et
        if random.random() < 0.2:  # %20 olasılıkla
            # Tüm olasılıkları sıfırla ve sadece bir yanıt türünü seç
            for key in probabilities:
                probabilities[key] = 0.001  # Çok düşük bir değer
            random_key = random.choice(list(probabilities.keys()))
            probabilities[random_key] = 1.0  # Seçilen yanıt türünü garantile

    def _select_response_type(self, probabilities: Dict[str, float]) -> str:
        """
        Select a response type based on the probability distribution

        Args:
            probabilities: The normalized probability distribution

        Returns:
            Selected response type
        """
        # Convert probabilities to cumulative distribution
        items = list(probabilities.items())
        cumulative_prob = 0
        cumulative_probs = []

        for item, prob in items:
            cumulative_prob += prob
            cumulative_probs.append((item, cumulative_prob))

        # Select based on random value
        rand_val = random.random()
        for item, cum_prob in cumulative_probs:
            if rand_val <= cum_prob:
                return item

        # Fallback to medium if something goes wrong
        return "medium"

    def get_response_length_instructions(self, response_type: str) -> str:
        """
        Get specific instructions for the selected response length

        Args:
            response_type: The selected response type

        Returns:
            Instructions for the model to generate a response of the appropriate length
        """
        # Yanıt türüne göre farklı talimatlar ver, daha uzun ve insan gibi yanıtlar için
        if response_type == "extremely_short":
            return "Yanıtını KISA tut - 1-2 cümle. Gerçek bir insan gibi doğal bir şekilde yanıt ver. Temel bilgileri içer. Mesajlaşma uygulamasında doğal bir şekilde cevap veren biri gibi davran."
        elif response_type == "slightly_short":
            return "Yanıtını BİRAZ KISA tut - 2-3 cümle. Doğal bir şekilde mesajlaşan bir insan gibi yanıt ver. Temel bilgileri ve birkaç detay ver. Doğal ve akıcı konuş. Gerçek bir insan gibi, konuyu açıkla."
        elif response_type == "medium":
            return "ORTA UZUNLUKTA bir yanıt ver - 3-5 cümle. Detaylı bilgiler ver. Normal bir sohbette konuşan biri gibi davran. Konuyu açıkla ve örnekler ver. Doğal bir akışla yanıt ver."
        elif response_type == "slightly_long":
            return "BİRAZ UZUN bir yanıt ver - 5-7 cümle. Detaylı bilgiler ve açıklamalar ver. Konuyu derinlemesine açıkla. Örnekler ve karşılaştırmalar kullan. Doğal bir insan gibi, akıcı ve bağlantılı cümleler kur."
        elif response_type == "long":
            return "UZUN ve DETAYLI bir yanıt ver - 7-10 cümle. Konuyu kapsamlı bir şekilde açıkla. Detaylı bilgiler, örnekler ve açıklamalar ver. Farklı bakış açıları sun. Doğal bir insan gibi, akıcı ve bağlantılı paragraflar oluştur. Konuyu derinlemesine ele al."
        else:
            # Default instruction - doğal ve insan gibi
            return "Tamamen doğal bir insan gibi yanıt ver. Mesaj uzunluğunu önceden planlamadan, doğal şekilde belirle. Detaylı ve kapsamlı yanıtlar ver. Gerçek bir insan gibi, konuyu derinlemesine açıkla. Normal bir sohbette konuşan biri gibi davran, doğal ve akıcı bir dil kullan."

    def get_language_level(self, message_content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Determine the language level of the response.

        Args:
            message_content: The user's message content
            context: Optional context information about the conversation

        Returns:
            Language level: Always "A1"
        """
        # Always return A1 for the bot's speaking level
        logger.debug("Selected language level: A1 (forced)")
        return "A1"

    def _adjust_language_probabilities_for_content(self, probabilities: Dict[str, float], message_content: str) -> None:
        """
        Adjust probabilities based on the user's message content

        Args:
            probabilities: The current probability distribution
            message_content: The user's message content
        """
        # Analyze message complexity
        message_complexity = self._estimate_message_complexity(message_content)

        # Match language level to message complexity but maintain natural variation
        if message_complexity == "simple":
            # Simple messages tend toward simpler responses, but with natural variation
            probabilities["A1"] *= 1.8
            probabilities["A2"] *= 1.5
            probabilities["B1"] *= 1.0  # No change
            probabilities["B2"] *= 0.7
            probabilities["C1"] *= 0.5
            probabilities["C2"] *= 0.3
            # But sometimes use more complex language even for simple messages (like humans do)
            if random.random() < 0.15:
                random_level = random.choice(["B2", "C1"])
                probabilities[random_level] *= 2.0
        elif message_complexity == "medium":
            # Medium complexity gets varied responses with focus on mid-levels
            probabilities["A2"] *= 1.3
            probabilities["B1"] *= 1.5
            probabilities["B2"] *= 1.3
            probabilities["A1"] *= 0.8
            probabilities["C2"] *= 0.7
            # Sometimes use very simple or very complex language (like humans do)
            if random.random() < 0.2:
                if random.random() < 0.5:
                    probabilities["A1"] *= 2.0  # Sometimes very simple
                else:
                    probabilities["C1"] *= 2.0  # Sometimes very complex
        elif message_complexity == "complex":
            # Complex messages can get more sophisticated responses
            probabilities["B1"] *= 1.2
            probabilities["B2"] *= 1.5
            probabilities["C1"] *= 1.3
            probabilities["C2"] *= 1.1
            probabilities["A1"] *= 0.6
            # But humans sometimes respond to complex messages with simple language
            if random.random() < 0.25:
                probabilities["A1"] *= 2.0
                probabilities["A2"] *= 1.5

        # Add some unpredictability - sometimes completely ignore message complexity
        if random.random() < 0.1:
            # Reset all adjustments and boost a random level
            for level in probabilities:
                probabilities[level] = getattr(config, f"{level}_LANGUAGE_PROBABILITY")

            # Boost a random level
            random_level = random.choice(list(probabilities.keys()))
            probabilities[random_level] *= 3.0

        # Greetings often get simple responses
        greeting_indicators = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "what's up", "sup", "yo"]
        if any(message_content.lower().startswith(greeting) for greeting in greeting_indicators):
            probabilities["A1"] *= 3.0
            probabilities["A2"] *= 2.0
            probabilities["B1"] *= 1.2
            probabilities["C1"] *= 0.3
            probabilities["C2"] *= 0.2

        # Questions often get mid-level responses
        if "?" in message_content:
            probabilities["B1"] *= 1.5
            probabilities["B2"] *= 1.3
            # But simple questions get simple answers
            if len(message_content) < 60:
                probabilities["A1"] *= 2.0
                probabilities["A2"] *= 1.5
                probabilities["C1"] *= 0.5
                probabilities["C2"] *= 0.3

        # Technical or specialized topics might get more complex language
        technical_indicators = ["code", "programming", "science", "philosophy", "technology", "engineering", "mathematics"]
        if any(indicator in message_content.lower() for indicator in technical_indicators):
            probabilities["B2"] *= 1.3
            probabilities["C1"] *= 1.5
            probabilities["C2"] *= 1.2
            probabilities["A1"] *= 0.5
            probabilities["A2"] *= 0.7

    def _estimate_message_complexity(self, message: str) -> str:
        """
        Estimate the complexity of a message based on length, vocabulary, and structure

        Args:
            message: The message to analyze

        Returns:
            Complexity level: "simple", "medium", or "complex"
        """
        # Simple heuristics for message complexity
        words = message.split()
        word_count = len(words)
        avg_word_length = sum(len(word) for word in words) / max(1, word_count)
        sentence_count = message.count('.') + message.count('!') + message.count('?')

        # Complex sentence indicators
        complex_indicators = ["however", "therefore", "furthermore", "nevertheless", "consequently",
                             "although", "despite", "whereas", "moreover", "subsequently"]
        complex_indicator_count = sum(1 for indicator in complex_indicators if indicator in message.lower())

        # Calculate complexity score
        complexity_score = 0

        # Length factors
        if word_count < 10:
            complexity_score += 1
        elif word_count < 25:
            complexity_score += 2
        else:
            complexity_score += 3

        # Word length factor
        if avg_word_length < 4:
            complexity_score += 1
        elif avg_word_length < 5.5:
            complexity_score += 2
        else:
            complexity_score += 3

        # Sentence structure factor
        if sentence_count <= 1:
            complexity_score += 1
        elif sentence_count <= 3:
            complexity_score += 2
        else:
            complexity_score += 3

        # Complex indicators factor
        complexity_score += min(3, complex_indicator_count)

        # Determine complexity level
        if complexity_score <= 5:
            return "simple"
        elif complexity_score <= 9:
            return "medium"
        else:
            return "complex"

    def _adjust_language_probabilities_for_context(self, probabilities: Dict[str, float], context: Dict[str, Any]) -> None:
        """
        Adjust probabilities based on conversation context

        Args:
            probabilities: The current probability distribution
            context: Context information about the conversation
        """
        # If this is the first message in a conversation, tend toward middle levels
        if context.get("is_first_message", False):
            # First messages often set the tone - use a more balanced approach
            probabilities["A2"] *= 1.5
            probabilities["B1"] *= 1.3
            probabilities["A1"] *= 1.0  # No change
            probabilities["C2"] *= 0.7

            # First messages sometimes get more formal/complex language
            if random.random() < 0.2:
                probabilities["B2"] *= 1.5
                probabilities["C1"] *= 1.2

        # If the conversation has been going on for a while, vary more
        message_count = context.get("message_count", 0)
        if message_count > 5:
            # Increase randomness as conversation progresses
            random_boost = random.choice(["A1", "A2", "B1", "B2", "C1", "C2"])
            probabilities[random_boost] *= 1.5

            # Occasionally make a dramatic shift in language level
            if message_count > 10 and random.random() < 0.15:
                # Reset all probabilities
                for level in probabilities:
                    probabilities[level] = 0.1

                # Pick a random level to dominate
                dominant_level = random.choice(["A1", "A2", "B1", "B2", "C1", "C2"])
                probabilities[dominant_level] = 0.6

        # If there's media, sometimes use more descriptive language
        if context.get("has_media", False) and random.random() < 0.4:
            probabilities["B1"] *= 1.5
            probabilities["B2"] *= 1.3
            probabilities["C1"] *= 1.2

        # Add some unpredictability - sometimes completely ignore context
        if random.random() < 0.1:
            # Boost a random level significantly
            random_level = random.choice(list(probabilities.keys()))
            probabilities[random_level] *= 3.0

    def _adjust_language_probabilities_for_variety(self, probabilities: Dict[str, float]) -> None:
        """
        Adjust language level probabilities to avoid repetitive patterns

        Args:
            probabilities: The current probability distribution
        """
        # If we've had the same language level multiple times in a row, reduce its probability
        if self.consecutive_same_level_count > 0 and self.last_language_level:
            # More aggressive reduction to avoid repetition
            reduction_factor = min(0.3, 0.8 ** self.consecutive_same_level_count)
            probabilities[self.last_language_level] *= reduction_factor

            # Force a change in language level more frequently
            if self.consecutive_same_level_count >= 2 and random.random() < 0.7:
                # If we've been using simple language, favor more complex
                if self.last_language_level in ["A1", "A2"]:
                    probabilities["B2"] *= 2.0
                    probabilities["C1"] *= 1.5
                # If we've been using mid-level language, favor extremes
                elif self.last_language_level in ["B1", "B2"]:
                    probabilities["A1"] *= 1.5
                    probabilities["C2"] *= 1.5
                # If we've been using complex language, favor simpler
                elif self.last_language_level in ["C1", "C2"]:
                    probabilities["A1"] *= 2.0
                    probabilities["A2"] *= 1.8
                    probabilities["B1"] *= 1.5

    def _apply_language_randomness(self, probabilities: Dict[str, float]) -> None:
        """
        Apply randomness factor to language level probabilities

        Args:
            probabilities: The current probability distribution
        """
        randomness = config.LANGUAGE_LEVEL_RANDOMNESS
        for key in probabilities:
            # Apply random adjustment within the randomness factor range
            random_adjustment = 1.0 + randomness * (random.random() * 2 - 1)
            probabilities[key] *= random_adjustment

    def _select_language_level(self, probabilities: Dict[str, float]) -> str:
        """
        Select a language level based on the probability distribution

        Args:
            probabilities: The normalized probability distribution

        Returns:
            Selected language level
        """
        # Convert probabilities to cumulative distribution
        items = list(probabilities.items())
        cumulative_prob = 0
        cumulative_probs = []

        for item, prob in items:
            cumulative_prob += prob
            cumulative_probs.append((item, cumulative_prob))

        # Select based on random value
        rand_val = random.random()
        for item, cum_prob in cumulative_probs:
            if rand_val <= cum_prob:
                return item

        # Fallback to B1 if something goes wrong
        return "B1"

    def get_language_level_instructions(self, language_level: str) -> str:
        """
        Get specific instructions for the selected language level

        Args:
            language_level: The selected language level

        Returns:
            Instructions for the model to generate a response at the appropriate language level
        """
        if language_level == "A1":
            return "Use mostly simple German with basic vocabulary and grammar. Focus on everyday words and simple sentence structures. Use mainly present tense. Keep explanations brief and straightforward. This is like how a beginner would speak German, but still sound natural and human-like. Don't be robotic or overly simplified - real beginners still try to express complex thoughts with simple language."
        elif language_level == "A2":
            return "Use simple but slightly more varied German. Include some basic connectors beyond 'und' and 'aber'. Use present tense primarily but occasionally include perfect tense for past events. Express basic opinions and preferences. Use vocabulary related to everyday situations and personal experiences. This is like how someone with elementary German knowledge would speak - simple but starting to become more expressive."
        elif language_level == "B1":
            return "Use moderately complex German with a good range of everyday vocabulary. Mix simple and compound sentences naturally. Include some subordinate clauses. Use different tenses as needed. Express opinions and give brief explanations. Use some idiomatic expressions. This is like how an intermediate German speaker would communicate - comfortable with everyday topics but still making occasional mistakes."
        elif language_level == "B2":
            return "Use more complex German with a broader vocabulary. Construct varied sentence structures. Express opinions clearly with supporting details. Discuss abstract concepts with some limitations. Use different tenses and moods appropriately. Include idiomatic expressions naturally. This is like how an upper-intermediate German speaker would communicate - generally fluent but still with some limitations in nuance."
        elif language_level == "C1":
            return "Use advanced German with rich vocabulary and varied expressions. Construct complex sentences with different subordinate clauses. Express nuanced opinions and develop arguments. Use precise vocabulary for specific contexts. Include cultural references and idiomatic expressions. This is like how an advanced German speaker would communicate - fluent and expressive with occasional minor errors."
        elif language_level == "C2":
            return "Use sophisticated German with precise and varied vocabulary. Construct complex and elegant sentences. Express subtle nuances and develop detailed arguments. Use specialized terminology when appropriate. Include cultural references, wordplay, and idiomatic expressions naturally. This is like how a near-native German speaker would communicate - highly fluent and nuanced with rare errors."
        else:
            # Fallback to B1 if something goes wrong
            return "Use moderately complex German with a good range of everyday vocabulary. Mix simple and compound sentences naturally. Include some subordinate clauses. Use different tenses as needed. Express opinions and give brief explanations. Use some idiomatic expressions. This is like how an intermediate German speaker would communicate - comfortable with everyday topics but still making occasional mistakes."

    def format_response_length_for_prompt(self, message_content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Format response length instructions for inclusion in the prompt

        Args:
            message_content: The user's message content
            context: Optional context information about the conversation

        Returns:
            Formatted response length instructions for the prompt
        """
        # Her zaman dinamik mesaj uzunluğu etkin olsun
        response_type = self.get_response_type(message_content, context)
        instructions = self.get_response_length_instructions(response_type)

        return f"""
        UZUN VE İNSAN GİBİ YANIT UZUNLUĞU TALİMATI:
        {instructions}

        ÇOK ÖNEMLİ: Mesaj uzunluğunu tamamen doğal ve insan gibi belirle. Detaylı ve kapsamlı yanıtlar ver. Gerçek bir insan gibi, konuyu derinlemesine açıkla. Normal bir sohbette konuşan biri gibi davran, doğal ve akıcı bir dil kullan. Konuyu tam olarak anlatmak için yeterli uzunlukta cevaplar ver. Örnekler ve açıklamalar ekle. Birden fazla paragraf kullanmaktan çekinme. Konuyu farklı açılardan ele al. Detaylı ve bilgilendirici ol. Kısa ve yetersiz yanıtlardan kaçın. En az 5-7 cümle kullan. Akıcı ve bağlantılı paragraflar oluştur.
        """

    def format_language_level_for_prompt(self, message_content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Format language level instructions for inclusion in the prompt

        Args:
            message_content: The user's message content
            context: Optional context information about the conversation

        Returns:
            Formatted language level instructions for the prompt
        """
        # Get dynamic language level based on context and content
        language_level = self.get_language_level(message_content, context)
        instructions = self.get_language_level_instructions(language_level)

        return f"""
        NATURAL HUMAN-LIKE GERMAN LANGUAGE INSTRUCTION:
        {instructions}

        EXTREMELY IMPORTANT: Speak German in a completely natural, human-like way. Your language level should be dynamic and unpredictable like a real human's.

        NATURAL LANGUAGE GUIDELINES:
        - Speak exactly like a real human would in casual conversation
        - Let your language complexity vary naturally within a conversation
        - Sometimes use simple language, sometimes more complex depending on the context
        - Don't follow rigid rules about what words or grammar to use
        - Occasionally make small grammar mistakes like real humans do
        - Use natural sentence structures that vary in complexity
        - Mix short and longer sentences like humans naturally do
        - Sometimes use slang or colloquial expressions when appropriate
        - Adjust your language complexity based on the topic and context
        - Be unpredictable in your language patterns

        IMPORTANT: Your language should NOT follow a consistent pattern or level. It should vary naturally like a real human's speech, with the general complexity level suggested above as just a starting point. Be dynamic and unpredictable in your language use.
        """

# Create a singleton instance
dynamic_response_manager = DynamicResponseManager()
