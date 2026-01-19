"""Query translation between Bangla and English using proper NLP models"""

from ..utils.logger import setup_logger


class QueryTranslator:
    """
    Translate queries between Bangla and English

    Methods (in order of preference):
    1. Google Translate API (via deep_translator)
    2. MarianMT neural translation models (Helsinki-NLP)
    3. Dictionary fallback (last resort)
    """

    # Minimal dictionary fallback (last resort only)
    FALLBACK_DICT = {
        'en_to_bn': {
            'education': 'শিক্ষা', 'politics': 'রাজনীতি', 'sports': 'খেলাধুলা',
            'health': 'স্বাস্থ্য', 'economy': 'অর্থনীতি', 'news': 'সংবাদ',
            'government': 'সরকার', 'university': 'বিশ্ববিদ্যালয়',
        },
        'bn_to_en': {
            'শিক্ষা': 'education', 'রাজনীতি': 'politics', 'খেলাধুলা': 'sports',
            'স্বাস্থ্য': 'health', 'অর্থনীতি': 'economy', 'সংবাদ': 'news',
            'সরকার': 'government', 'বিশ্ববিদ্যালয়': 'university',
        }
    }

    def __init__(self, use_gpu=False):
        """
        Initialize translator with available backends

        Args:
            use_gpu: Whether to use GPU for MarianMT (if available)
        """
        self.logger = setup_logger('Translator')
        self.use_gpu = use_gpu
        self.method_used = None
        self._cache = {}

        # Check available backends
        self._google_available = self._check_google_translate()
        self._marian_available = self._check_marian()

        # MarianMT models (lazy loaded)
        self._marian_bn_en = None
        self._marian_en_bn = None

        methods = []
        if self._google_available:
            methods.append('GoogleTranslate')
        if self._marian_available:
            methods.append('MarianMT')
        methods.append('Dictionary')

        self.logger.info(f"Translator initialized. Available: {', '.join(methods)}")

    def _check_google_translate(self):
        """Check if deep_translator is available"""
        try:
            from deep_translator import GoogleTranslator
            return True
        except ImportError:
            return False

    def _check_marian(self):
        """Check if transformers/MarianMT is available"""
        try:
            from transformers import MarianMTModel, MarianTokenizer
            return True
        except ImportError:
            return False

    def _load_marian_model(self, direction):
        """
        Lazy load MarianMT model for specified direction

        Args:
            direction: 'bn_en' or 'en_bn'

        Returns:
            (tokenizer, model) tuple or (None, None)
        """
        if not self._marian_available:
            return None, None

        from transformers import MarianMTModel, MarianTokenizer

        try:
            if direction == 'bn_en':
                if self._marian_bn_en is None:
                    model_name = "Helsinki-NLP/opus-mt-bn-en"
                    self.logger.info(f"Loading MarianMT: {model_name}")
                    tokenizer = MarianTokenizer.from_pretrained(model_name)
                    model = MarianMTModel.from_pretrained(model_name)
                    if self.use_gpu:
                        import torch
                        if torch.cuda.is_available():
                            model = model.cuda()
                    self._marian_bn_en = (tokenizer, model)
                return self._marian_bn_en

            elif direction == 'en_bn':
                if self._marian_en_bn is None:
                    model_name = "Helsinki-NLP/opus-mt-en-mul"  # English to multilingual
                    self.logger.info(f"Loading MarianMT: {model_name}")
                    tokenizer = MarianTokenizer.from_pretrained(model_name)
                    model = MarianMTModel.from_pretrained(model_name)
                    if self.use_gpu:
                        import torch
                        if torch.cuda.is_available():
                            model = model.cuda()
                    self._marian_en_bn = (tokenizer, model)
                return self._marian_en_bn

        except Exception as e:
            self.logger.warning(f"Failed to load MarianMT model: {e}")
            return None, None

        return None, None

    def translate(self, text, source_lang, target_lang):
        """
        Translate text between languages

        Args:
            text: Text to translate
            source_lang: 'bangla' or 'english'
            target_lang: 'bangla' or 'english'

        Returns:
            Translated text (self.method_used contains which method was used)
        """
        if not text or not text.strip():
            self.method_used = 'none'
            return text

        if source_lang == target_lang:
            self.method_used = 'none'
            return text

        # Check cache
        cache_key = f"{source_lang}:{target_lang}:{text}"
        if cache_key in self._cache:
            self.method_used = self._cache[cache_key][1]
            return self._cache[cache_key][0]

        result = None

        # 1. Try Google Translate
        if self._google_available:
            result = self._translate_google(text, source_lang, target_lang)
            if result:
                self.method_used = 'google_translate'
                self._cache[cache_key] = (result, self.method_used)
                return result

        # 2. Try MarianMT
        if self._marian_available:
            result = self._translate_marian(text, source_lang, target_lang)
            if result:
                self.method_used = 'marian_mt'
                self._cache[cache_key] = (result, self.method_used)
                return result

        # 3. Dictionary fallback (last resort)
        result = self._translate_dictionary(text, source_lang, target_lang)
        self.method_used = 'dictionary_fallback'
        self._cache[cache_key] = (result, self.method_used)
        return result

    def _translate_google(self, text, source_lang, target_lang):
        """Translate using Google Translate API"""
        try:
            from deep_translator import GoogleTranslator

            src = 'bn' if source_lang == 'bangla' else 'en'
            tgt = 'bn' if target_lang == 'bangla' else 'en'

            translator = GoogleTranslator(source=src, target=tgt)
            result = translator.translate(text)

            self.logger.debug(f"Google: '{text}' -> '{result}'")
            return result

        except Exception as e:
            self.logger.warning(f"Google Translate failed: {e}")
            return None

    def _translate_marian(self, text, source_lang, target_lang):
        """Translate using MarianMT neural model"""
        try:
            import torch

            # Determine direction
            if source_lang == 'bangla' and target_lang == 'english':
                direction = 'bn_en'
            elif source_lang == 'english' and target_lang == 'bangla':
                direction = 'en_bn'
            else:
                return None

            tokenizer, model = self._load_marian_model(direction)
            if tokenizer is None or model is None:
                return None

            # For en->bn, we need to add language tag
            if direction == 'en_bn':
                text = f">>ben<< {text}"

            # Translate
            tokens = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
            if self.use_gpu and torch.cuda.is_available():
                tokens = {k: v.cuda() for k, v in tokens.items()}

            with torch.no_grad():
                translated = model.generate(**tokens, max_length=512)

            result = tokenizer.decode(translated[0], skip_special_tokens=True)
            self.logger.debug(f"MarianMT: '{text}' -> '{result}'")
            return result

        except Exception as e:
            self.logger.warning(f"MarianMT failed: {e}")
            return None

    def _translate_dictionary(self, text, source_lang, target_lang):
        """Fallback dictionary translation (word by word)"""
        if source_lang == 'english' and target_lang == 'bangla':
            dictionary = self.FALLBACK_DICT['en_to_bn']
        else:
            dictionary = self.FALLBACK_DICT['bn_to_en']

        words = text.split()
        translated_words = []

        for word in words:
            word_lower = word.lower()
            if word_lower in dictionary:
                translated_words.append(dictionary[word_lower])
            elif word in dictionary:
                translated_words.append(dictionary[word])
            else:
                translated_words.append(word)

        self.logger.debug(f"Dictionary fallback: '{text}'")
        return ' '.join(translated_words)

    def translate_to_english(self, text):
        """Translate Bangla to English"""
        return self.translate(text, 'bangla', 'english')

    def translate_to_bangla(self, text):
        """Translate English to Bangla"""
        return self.translate(text, 'english', 'bangla')

    def get_method_used(self):
        """Return the method used for last translation"""
        return self.method_used

    def get_available_methods(self):
        """Return dict of available translation methods"""
        return {
            'google_translate': self._google_available,
            'marian_mt': self._marian_available,
            'dictionary_fallback': True
        }

    def get_cache_size(self):
        """Get number of cached translations"""
        return len(self._cache)

    def clear_cache(self):
        """Clear translation cache"""
        self._cache.clear()
