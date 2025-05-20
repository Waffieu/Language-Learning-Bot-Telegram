import os
from pickle import TRUE
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Memory settings
SHORT_MEMORY_SIZE = int(os.getenv("SHORT_MEMORY_SIZE", "25"))
LONG_MEMORY_SIZE = int(os.getenv("LONG_MEMORY_SIZE", "100"))
MEMORY_DIR = os.getenv("MEMORY_DIR", "user_memories")

# Web search settings
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "100"))
# Web search decision model - determines whether to perform web search based on query
WEB_SEARCH_DECISION_MODEL_ENABLED = True  # Always enabled to use Gemini for web search decisions

# Proxy settings - DISABLED
# Proxy system has been removed due to connection issues with DuckDuckGo
PROXY_ENABLED = False
PROXY_LIST = []
PROXY_FILE = ""

# Maximum number of retries for DuckDuckGo searches
MAX_SEARCH_RETRIES = int(os.getenv("MAX_SEARCH_RETRIES", "10"))

# Time awareness settings
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "Europe/Istanbul")
TIME_AWARENESS_ENABLED = os.getenv("TIME_AWARENESS_ENABLED", "true").lower() == "true"
# Only show time information when relevant to the conversation
SHOW_TIME_ONLY_WHEN_RELEVANT = os.getenv("SHOW_TIME_ONLY_WHEN_RELEVANT", "true").lower() == "true"

# Website link settings
# Only show website links when explicitly requested or relevant
SHOW_LINKS_ONLY_WHEN_RELEVANT = os.getenv("SHOW_LINKS_ONLY_WHEN_RELEVANT", "true").lower() == "true"

# Self-awareness and environmental awareness settings
SELF_AWARENESS_ENABLED = os.getenv("SELF_AWARENESS_ENABLED", "true").lower() == "true"
ENVIRONMENT_AWARENESS_ENABLED = os.getenv("ENVIRONMENT_AWARENESS_ENABLED", "true").lower() == "true"
SELF_AWARENESS_SEARCH_ENABLED = os.getenv("SELF_AWARENESS_SEARCH_ENABLED", "true").lower() == "true"
# Level of detail for environmental awareness (1-5)
ENVIRONMENT_AWARENESS_LEVEL = int(os.getenv("ENVIRONMENT_AWARENESS_LEVEL", "3"))

# Word translation settings - DISABLED as requested
WORD_TRANSLATION_ENABLED = TRUE
# Default language for translation is German (kept for backward compatibility)
DEFAULT_TRANSLATION_LANGUAGE = "German"
# Translate words with A2 level and above (kept for backward compatibility)
MIN_CEFR_LEVEL_FOR_TRANSLATION = "A2"
# These settings are kept for backward compatibility but are not used
MIN_WORD_LENGTH_FOR_TRANSLATION = int(os.getenv("MIN_WORD_LENGTH_FOR_TRANSLATION", "4"))
MAX_WORDS_TO_TRANSLATE = int(os.getenv("MAX_WORDS_TO_TRANSLATE", "5"))

# Dynamic message length settings - Her zaman etkin
DYNAMIC_MESSAGE_LENGTH_ENABLED = True
# Probability distribution for different response lengths
# These values determine the approximate probability of each response type
# Daha uzun ve insan gibi yanıt dağılımı - uzun yanıtlar için daha yüksek olasılık
EXTREMELY_SHORT_RESPONSE_PROBABILITY = 0.60  # Favor more very short responses
SLIGHTLY_SHORT_RESPONSE_PROBABILITY = 0.30  # Favor more short responses
MEDIUM_RESPONSE_PROBABILITY = 0.07  # Reduce medium length responses
SLIGHTLY_LONG_RESPONSE_PROBABILITY = 0.02  # Reduce slightly long responses
LONG_RESPONSE_PROBABILITY = 0.01  # Keep long responses infrequent
# Randomness factor for response length (0.0-1.0, higher = more random)
RESPONSE_LENGTH_RANDOMNESS = 0.85  # Increase randomness for more natural variation

# Slang and casual language settings
SLANG_ENABLED = True  # Always enable slang and casual language
# Probability of using slang in a response (0.0-1.0)
SLANG_PROBABILITY = 1.0  # Maximum probability for natural slang usage
# Maximum level of slang/swearing (1-5, where 5 is most casual/explicit)
SLANG_LEVEL = 5  # Maximum level for natural casual/explicit language

# Dynamic language level settings - Enabled with completely natural human-like distribution
DYNAMIC_LANGUAGE_LEVEL_ENABLED = True
# Probability distribution for different language levels (A1-C2)
# Natural distribution like a real human - varies based on context and content
A1_LANGUAGE_PROBABILITY = 0.15  # Simple language
A2_LANGUAGE_PROBABILITY = 0.15  # Elementary language
B1_LANGUAGE_PROBABILITY = 0.20  # Intermediate language
B2_LANGUAGE_PROBABILITY = 0.20  # Upper-intermediate language
C1_LANGUAGE_PROBABILITY = 0.15  # Advanced language
C2_LANGUAGE_PROBABILITY = 0.15  # Proficient language
# Randomness factor for language level (maximum for unpredictable human-like variation)
LANGUAGE_LEVEL_RANDOMNESS = 1.0  # Maximum randomness for natural human-like unpredictability

# Self-reflection settings - DISABLED
SELF_REFLECTION_ENABLED = False
# Probability of performing self-reflection on a response (0.0-1.0)
SELF_REFLECTION_PROBABILITY = 0.0

# Gemini model settings
GEMINI_MODEL = "gemini-2.5-flash-preview-04-17"
GEMINI_TEMPERATURE = 1.0  # Maximum temperature for ultra-creative, unpredictable, and human-like responses
GEMINI_TOP_P = 0.99
GEMINI_TOP_K = 80
GEMINI_MAX_OUTPUT_TOKENS = 4096  # Increased max tokens to allow longer responses

# Specialized Gemini models
# Model for web search decision
GEMINI_WEB_SEARCH_DECISION_MODEL = "gemini-2.5-flash-preview-04-17"  # Using the latest Gemini model for better decision making
GEMINI_WEB_SEARCH_DECISION_TEMPERATURE = 0.1  # Low temperature for more deterministic decisions
GEMINI_WEB_SEARCH_DECISION_TOP_P = 0.95
GEMINI_WEB_SEARCH_DECISION_TOP_K = 32
GEMINI_WEB_SEARCH_DECISION_MAX_OUTPUT_TOKENS = 8000

# Model for web search and language detection
GEMINI_FLASH_LITE_MODEL = "gemini-2.0-flash-lite"
GEMINI_FLASH_LITE_TEMPERATURE = 0.4
GEMINI_FLASH_LITE_TOP_P = 0.95
GEMINI_FLASH_LITE_TOP_K = 32
GEMINI_FLASH_LITE_MAX_OUTPUT_TOKENS = 8192

# Model for image analysis
GEMINI_IMAGE_MODEL = "gemini-2.0-flash-lite"
GEMINI_IMAGE_TEMPERATURE = 0.7
GEMINI_IMAGE_TOP_P = 0.95
GEMINI_IMAGE_TOP_K = 40
GEMINI_IMAGE_MAX_OUTPUT_TOKENS = 4096

# Model for word translation
GEMINI_TRANSLATION_MODEL = "gemini-2.0-flash"
GEMINI_TRANSLATION_TEMPERATURE = 0.1
GEMINI_TRANSLATION_TOP_P = 0.95
GEMINI_TRANSLATION_TOP_K = 40
GEMINI_TRANSLATION_MAX_OUTPUT_TOKENS = 1024

# Safety settings - all set to BLOCK_NONE as requested
SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE"
    },
]
