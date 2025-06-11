from transformers import pipeline

# Сохраняем zero-shot модель
zero_shot = pipeline("zero-shot-classification", model="cointegrated/rubert-base-cased-nli-threeway")
zero_shot.model.save_pretrained("models/rubert-base-cased-nli-threeway")
zero_shot.tokenizer.save_pretrained("models/rubert-base-cased-nli-threeway")

# Сохраняем модель тональности
sentiment = pipeline("sentiment-analysis", model="blanchefort/rubert-base-cased-sentiment")
sentiment.model.save_pretrained("models/rubert-base-cased-sentiment")
sentiment.tokenizer.save_pretrained("models/rubert-base-cased-sentiment")

translator = pipeline("translation", model="facebook/nllb-200-distilled-600M",)
translator.model.save_pretrained("models/nllb-200-distilled-600M")
translator.tokenizer.save_pretrained("models/nllb-200-distilled-600M")