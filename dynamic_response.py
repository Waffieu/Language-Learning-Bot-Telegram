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
        # logger.debug(f"Probabilities: {normalized_probabilities}") # Removed logging of probabilities
        return response_type

    def _adjust_probabilities_for_content(self, probabilities: Dict[str, float], message_content: str) -> None:
        """
        Adjust probabilities based on the user's message content to favor longer responses

        Args:
            probabilities: The current probability distribution
            message_content: The user's message content
        """
        # Adjust probabilities based on the user's message content
        # Adjust probabilities to favor longer responses
        probabilities["extremely_short"] *= 0.5  # Decrease probability of very short responses
        probabilities["slightly_short"] *= 0.8   # Decrease probability of slightly short responses
        probabilities["medium"] *= 1.2       # Slightly increase probability of medium responses
        probabilities["slightly_long"] *= 2.0    # Increase probability of slightly long responses
        probabilities["long"] *= 3.0         # Significantly increase probability of long responses

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
        # Adjust probabilities based on conversation context to favor shorter responses overall
        if context.get("is_first_message", False):
            probabilities["extremely_short"] *= 2.0 # Favor shorter first responses
            probabilities["slightly_short"] *= 1.5
            probabilities["medium"] *= 1.0
            probabilities["slightly_long"] *= 0.6
            probabilities["long"] *= 0.4

        # If the conversation has been going on for a while, slightly increase chance of longer responses for variety, but still lean short/medium
        if context.get("message_count", 0) > 5:
            probabilities["extremely_short"] *= 1.0
            probabilities["slightly_short"] *= 1.1
            probabilities["medium"] *= 1.2
            probabilities["slightly_long"] *= 1.0
            probabilities["long"] *= 0.8

        # If there's media, allow slightly longer responses for description, but still lean shorter overall
        if context.get("has_media", False):
            probabilities["extremely_short"] *= 0.9
            probabilities["slightly_short"] *= 1.0
            probabilities["medium"] *= 1.2
            probabilities["slightly_long"] *= 1.1
            probabilities["long"] *= 1.0

    def _adjust_probabilities_for_variety(self, probabilities: Dict[str, float]) -> None:
        """
        Adjust probabilities to encourage natural variation and avoid monotonous repetition of response lengths.
        This aims for a more human-like flow where conversation length ebbs and flows.

        Args:
            probabilities: The current probability distribution
        """
        if self.last_response_type and self.consecutive_same_type_count > 0:
            # Reduce the probability of the last response type, especially if repeated.
            # The reduction becomes more significant with more repetitions, but with a cap to avoid zeroing out.
            reduction_factor = max(0.1, 0.75 - (self.consecutive_same_type_count * 0.15))
            probabilities[self.last_response_type] *= reduction_factor
            logger.debug(f"Reduced probability of {self.last_response_type} due to {self.consecutive_same_type_count} repetitions. Factor: {reduction_factor:.2f}")

            # After a repetition, actively encourage a shift to a *different* length category.
            # This is more nuanced than just picking any other; it tries to create a gentle contrast.
            if self.consecutive_same_type_count >= 1: # If there's been at least one repetition
                # Define transitions to encourage a natural flow rather than abrupt jumps.
                transitions = {
                    "extremely_short": ["slightly_short", "medium"], # After very short, go slightly longer
                    "slightly_short": ["medium", "extremely_short", "slightly_long"], # Can go shorter, medium, or a bit longer
                    "medium": ["slightly_short", "slightly_long", "long"], # From medium, can vary more widely
                    "slightly_long": ["medium", "long", "slightly_short"], # After longish, can go medium, very long, or shorter
                    "long": ["medium", "slightly_long"] # After very long, tend towards medium or slightly long
                }
                possible_next_types = transitions.get(self.last_response_type, list(probabilities.keys()))

                # Boost the probabilities of these suggested next types.
                for next_type in possible_next_types:
                    if next_type in probabilities: # Ensure the type exists
                        probabilities[next_type] *= random.uniform(1.5, 2.5) # Moderate boost
                logger.debug(f"After {self.last_response_type}, boosting {possible_next_types}")

        # Independent of repetition, occasionally (but not too often) introduce a 'surprise' element.
        # This is a small chance to significantly boost a random response type, just to keep things fresh
        # and mimic the occasional unexpected conversational turn.
        if random.random() < 0.12:  # 12% chance for a 'surprise' boost
            surprise_type = random.choice(list(probabilities.keys()))
            probabilities[surprise_type] *= random.uniform(2.0, 3.5) # A noticeable, but not extreme, boost
            logger.debug(f"Surprise boost for {surprise_type}")

        # Ensure probabilities don't get too skewed or too low
        for key in probabilities:
            if probabilities[key] < 0.001: # Prevent zero or negative probabilities
                probabilities[key] = 0.001
            elif probabilities[key] > 100.0: # Cap extremely high probabilities to maintain balance
                probabilities[key] = 100.0

    def _apply_randomness(self, probabilities: Dict[str, float]) -> None:
        """
        Apply a sophisticated randomness factor to probabilities for more natural and unpredictable response lengths.
        This aims to mimic human conversation patterns where length isn't strictly rule-based but flows organically.

        Args:
            probabilities: The current probability distribution
        """
        # Introduce a base level of general flux to all probabilities to prevent stagnation.
        # This simulates the slight, almost imperceptible shifts in human conversational energy.
        for key in probabilities:
            # Apply a gentle, non-extreme random adjustment. The range is smaller to avoid chaotic swings
            # and favor more subtle, natural-feeling variations.
            subtle_random_factor = random.uniform(0.9, 1.1) # Slight boost or reduction
            probabilities[key] *= subtle_random_factor

        # Periodically, with a moderate chance, introduce a more significant, but still context-aware, shift.
        # This is like a person suddenly having more to say on a topic, or conversely, being more succinct.
        if random.random() < 0.25: # 25% chance for a more noticeable, but not extreme, shift
            # Determine if this shift will favor shorter or longer responses, or a mix.
            # This isn't about picking one type, but nudging the overall distribution.
            shift_direction = random.choice(["favor_shorter", "favor_medium"])

            if shift_direction == "favor_shorter":
                probabilities["extremely_short"] *= random.uniform(1.8, 2.8)
                probabilities["slightly_short"] *= random.uniform(1.5, 2.2)
                probabilities["medium"] *= random.uniform(0.7, 1.0) # Slight or no change
                probabilities["slightly_long"] *= random.uniform(0.5, 0.8)
                probabilities["long"] *= random.uniform(0.3, 0.6)
            elif shift_direction == "favor_medium":
                probabilities["extremely_short"] *= random.uniform(0.6, 0.9)
                probabilities["slightly_short"] *= random.uniform(0.8, 1.1)
                probabilities["medium"] *= random.uniform(1.5, 2.5)
                probabilities["slightly_long"] *= random.uniform(0.8, 1.1)
                probabilities["long"] *= random.uniform(0.5, 0.8)

        # Very rarely, introduce a 'wildcard' factor: a strong, somewhat unexpected emphasis on a particular length.
        # This simulates those moments in conversation where someone gives an unusually brief or lengthy reply for no obvious reason.
        # This should be rare to avoid making the bot seem erratic.
        if random.random() < 0.05:  # 5% chance for a wildcard event
            chosen_type = random.choice(["extremely_short", "slightly_short", "medium"])
            # Give a significant, but not overwhelming, boost to the chosen type.
            # Also, slightly suppress other types to make the chosen one stand out more.
            for key in probabilities:
                if key == chosen_type:
                    probabilities[key] *= random.uniform(3.0, 5.0)
                else:
                    probabilities[key] *= random.uniform(0.4, 0.7) # Suppress others slightly

        # Ensure no probability becomes zero or negative after adjustments
        for key in probabilities:
            if probabilities[key] < 0.001:
                probabilities[key] = 0.001


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
        # ÖNEMLİ NOT: Bu yönlendirmeler, yapay zekanın bir insan gibi, doğal ve akıcı bir Türkçe ile yanıt vermesini sağlamak için tasarlanmıştır.
        # Yanıt uzunlukları bir kılavuzdur; asıl amaç, bağlama ve konuşmanın akışına uygun, doğal bir sohbet deneyimi yaratmaktır.
        # Yapay zeka, bir metin yazarı veya bir asistan gibi değil, sıradan bir insan gibi konuşmalıdır.
        # Cevaplar kesinlikle robotik veya önceden programlanmış gibi olmamalıdır.
        # Duygusal zeka ipuçları, konuşma tonu ve üslup, insan benzeri bir etkileşim için kritik öneme sahiptir.

        if response_type == "extremely_short":
            return (
                "Bir arkadaşınla mesajlaşır gibi, kısacık ve öz bir yanıt ver. Belki sadece birkaç kelime veya bir cümle yeterli olacaktır. "
                "Sanki acelen varmış da hızlıca bir şey söyleyip geçiyormuşsun gibi düşün. Örneğin, 'Aynen katılıyorum.' ya da 'Tamamdır, anladım.' gibi. "
                "Çok fazla detaya girme, sadece ana fikri ver. Doğal ol, kasma kendini. Unutma, amaç hızlı ve etkili iletişim."
            )
        elif response_type == "slightly_short":
            return (
                "Biraz daha sohbet havasında ama yine de kısa tutmaya çalış. Bir iki cümleyle ne demek istediğini anlat. "
                "Belki küçük bir detay ekleyebilirsin ama konuyu çok uzatma. Mesela, 'Evet, o film gerçekten güzeldi, özellikle son sahnesi çok etkileyiciydi.' gibi. "
                "Samimi ve rahat bir dil kullan. Karşındaki kişiyle gerçekten sohbet ediyormuşsun gibi hissettir. "
                "Amacımız, kısa ama anlamlı bir diyalog kurmak."
            )
        elif response_type == "medium":
            return (
                "Şimdi biraz daha rahat olabilirsin. Konuyu biraz daha açarak, 3-5 cümlelik bir yanıt ver. "
                "Düşüncelerini biraz daha detaylandırabilir, belki küçük bir örnekle destekleyebilirsin. "
                "Örneğin, 'Bu konu hakkında biraz araştırma yaptım ve birkaç ilginç makaleye denk geldim. Özellikle X teorisi oldukça mantıklı görünüyor çünkü...' gibi. "
                "Akıcı ve doğal bir üslup kullan. Sanki bir kahve molasında arkadaşınla önemli bir konuyu tartışıyormuşsun gibi. "
                "Dengeli bir uzunlukta, bilgilendirici ama sıkıcı olmayan bir yanıt hedefle."
            )
        elif response_type == "slightly_long":
            return (
                "Konuya biraz daha derinlemesine girme zamanı. 5-7 cümlelik, daha kapsamlı bir yanıt oluştur. "
                "Farklı açılardan yaklaşabilir, argümanlarını gerekçelendirebilirsin. Belki kişisel bir deneyimini veya gözlemini paylaşabilirsin. "
                "Mesela, 'Bu konunun toplumsal etkileri üzerine düşündüğümde, özellikle genç nesiller üzerindeki potansiyel sonuçları endişe verici buluyorum. Örneğin, yapılan bir araştırmaya göre...' gibi. "
                "Anlatımını zenginleştir, düşündürücü ve ilgi çekici olmaya çalış. Karşındakini konunun içine çek. "
                "Sadece bilgi vermekle kalma, aynı zamanda bir perspektif sun."
            )
        elif response_type == "long":
            return (
                "Şimdi tam anlamıyla dökülme zamanı! 7-10 cümle, hatta belki biraz daha uzun, detaylı ve kapsamlı bir yanıt ver. "
                "Konuyu enine boyuna ele al, farklı argümanları karşılaştır, örneklerle zenginleştir, belki bir çıkarımda bulun. "
                "Örneğin, 'Bu karmaşık sorunun çözümü için birden fazla faktörü göz önünde bulundurmamız gerekiyor. Tarihsel arka planına baktığımızda... Ekonomik boyutunu incelediğimizde... Sosyolojik açıdan değerlendirdiğimizde ise... Tüm bunları bir araya getirdiğimizde, şöyle bir sonuca varabiliriz: ...' gibi. "
                "Akademik bir dil kullanmaktan çekinme ama yine de anlaşılır ve akıcı olmaya özen göster. "
                "Amacın, konuyu tüm yönleriyle aydınlatmak ve derinlemesine bir analiz sunmak. Karşındakini etkileyecek, düşündürecek ve belki de yeni bir bakış açısı kazandıracak bir yanıt oluştur."
            )
        else:
            # Varsayılan talimat: Tamamen doğal, insan gibi, uzunluğa takılmadan.
            return (
                "Şu an nasıl hissediyorsan öyle konuş. Uzunluğunu hiç düşünme, içinden geldiği gibi, tamamen doğal bir şekilde yanıt ver. "
                "Bazen kısa kesersin, bazen uzun uzun anlatırsın, tıpkı gerçek bir sohbette olduğu gibi. "
                "Önemli olan samimiyetin ve düşüncelerini akıcı bir şekilde ifade etmen. "
                "Kendini bir kalıba sokmaya çalışma. Sadece konuş, anlat, paylaş. "
                "Unutma, en iyi sohbetler planlanmadan, kendiliğinden gelişenlerdir."
            )

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
        RESPONSE LENGTH GUIDELINE:
        {instructions}

        IMPORTANT: Adjust your response length naturally based on the user's message and the conversation flow, following the guideline above. Aim for concise responses by default, but feel free to elaborate when the topic requires more detail or explanation, just like a real person would.
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
