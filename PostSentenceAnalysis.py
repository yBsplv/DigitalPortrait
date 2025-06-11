import json
from typing import List, Dict, Optional, Union
from collections import defaultdict
from config import CATEGORIES_FILE, VK_API_TOKEN, ZERO_SHOT_MODEL, SENTIMENT_MODEL, TRANSLATE_MODEL
import requests
import fasttext
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
from transformers import pipeline
#import torch
#import numpy as np


class VkTextAnalyzer:
    def __init__(self):
        """
        Инициализация анализатора:
        - Загрузка категорий и маппинга для переименования
        - Инициализация пайплайнов для моделей
        - Инициализация детектора языка
        """
        self._load_categories_and_mapping()
        self._init_pipelines()
        self.model = fasttext.load_model("models/FastText/lid.176.ftz")
        self.vk_api_url = "https://api.vk.com/method/wall.get"
        self.vk_api_version = "5.199"

    def _load_categories_and_mapping(self):
        """Загрузка категорий и маппинга для переименования из JSON-файла"""
        with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
            self.category_mapping = json.load(f)
        
        # Категории для модели - это оригинальные тексты из маппинга
        self.categories = list(self.category_mapping.keys())
        
        # Обратный маппинг для удобства (оригинальный текст → новое название)
        self.reverse_mapping = {k.lower(): v for k, v in self.category_mapping.items()}

    def _rename_category(self, category_label: str) -> str:
        """
        Переименовывает категорию согласно маппингу.
        Если категория не найдена в маппинге, возвращает оригинальное название.
        """
        # Приводим к нижнему регистру для сравнения
        lower_label = category_label.lower()
        return self.reverse_mapping.get(lower_label, category_label)

    def _init_pipelines(self):
        """Инициализация пайплайнов для моделей"""
        #device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.zero_shot_pipeline = pipeline(
            "zero-shot-classification",
            model=f"models/{ZERO_SHOT_MODEL}",
            tokenizer=f"models/{ZERO_SHOT_MODEL}",
        #    device=device,
            truncation=True,  # Правильное название параметра
            max_length=512,   # Добавляем ограничение длины
        )

        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=f"models/{SENTIMENT_MODEL}",
            tokenizer=f"models/{SENTIMENT_MODEL}",
        #    device=device,
            truncation=True,
            max_length=512
        )

        self.translator_pipeline = pipeline(
            "translation",
            model=f"models/{TRANSLATE_MODEL}",
            tgt_lang="rus_Cyrl",
        #    device=device,
            max_length=400,  # Уменьшаем максимальную длину для перевода
            truncation=True
        )

    def fetch_vk_posts(self, user_id: str, count: int = 100, offset: int = 0) -> List[Dict[str, Union[str, int]]]:
        """Запрос постов пользователя ВКонтакте с сохранением id поста"""
        params = {
            "owner_id": user_id,
            "access_token": VK_API_TOKEN,
            "v": self.vk_api_version,
            "count": count,
            "offset": offset,
            "filter": "owner"
        }

        try:
            response = requests.get(self.vk_api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "response" not in data or "items" not in data["response"]:
                return []
                
            return [
                {"id": post["id"], "text": post["text"]} 
                for post in data["response"]["items"] 
                if post.get("text")
            ]
        except Exception as e:
            print(f"Error fetching VK posts: {e}")
            return []

    def fetch_all_vk_posts(self, user_id: str, max_posts: int = 1000) -> List[Dict[str, Union[str, int]]]:
        """Получение всех постов пользователя с сохранением id"""
        all_posts = []
        count = min(max_posts, 100)
        
        for offset in range(0, max_posts, 100):
            batch = self.fetch_vk_posts(user_id, count, offset=offset)
            if not batch:
                break
            all_posts.extend(batch)
            if len(all_posts) >= max_posts:
                break
                
        return all_posts[:max_posts]

    def _analyze_language(self, text: str) -> str:
        """Определение языка с помощью fasttext"""
        predictions = self.model.predict(text.replace('\n', ' '), k=1)
        return predictions[0][0].replace('__label__', '')

    def _translate_text(self, text: str, source_lang: str) -> str:
        """Перевод текста на русский"""
        result = self.translator_pipeline(text, src_lang=source_lang)
        return result[0]["translation_text"]

    def _classify_text(self, text: str) -> Dict:
        """Классификация текста по категориям"""
        result = self.zero_shot_pipeline(
            text, 
            candidate_labels=self.categories,
            truncation=True,
            max_length=512
        )
        
        scores = result["scores"]
        labels = result["labels"]
        #entropy = -sum(p * np.log(p) for p in scores)
        top_category = labels[0]
        top_score = scores[0]
        # Определение основной категории с учетом энтропии
        if scores[0] < 0.4:
            top_category = "Неопределенная категория"
            top_score = max(scores)
            
        # Переименовываем категорию согласно маппингу
        renamed_category = self._rename_category(top_category)
        
        return {
            "label": renamed_category,      # и переименованное
            "score": round(top_score, 2),
            "all_categories": {self._rename_category(label): round(score, 2) 
                             for label, score in zip(labels, scores)}
        }

    def _analyze_sentiment(self, text: str) -> Dict:
        """Анализ тональности текста"""
        result = self.sentiment_pipeline(text, truncation=True, max_length=512)
        if isinstance(result, list):
            result = result[0]
        return {
            "label": result["label"],
            "score": round(result["score"], 2)
        }

    def analyze_text(self, text: str) -> Optional[Dict]:
        """Полный анализ одного текста"""
        if not text.strip():
            return None
            
        try:
            # Определение языка
            main_lang = self._analyze_language(text)
            
            # Перевод при необходимости
            translated_text = text
            if main_lang != "ru":
                translated_text = self._translate_text(text, main_lang)
            
            # Классификация и анализ тональности
            category = self._classify_text(translated_text)
            sentiment = self._analyze_sentiment(translated_text)
            
            return {
                "original_text": text,
                "translated_text": translated_text if main_lang != "ru" else None,
                "language": main_lang,
                "category": category,
                "sentiment": sentiment
            }
        except Exception as e:
            print(f"Error analyzing text: {e}")
            return None

    def analyze_texts(self, posts: List[Dict[str, Union[str, int]]]) -> Dict[int, Dict]:
        """
        Анализ списка постов (с id)
        Возвращает словарь, где ключ - id поста, значение - результат анализа
        """
        results = {}
        
        for post in posts:
            post_id = post["id"]
            text = post["text"]
            
            if not text.strip():
                results[post_id] = {"error": "Empty text"}
                continue
                
            analysis = self.analyze_text(text)
            if analysis:
                results[post_id] = analysis
            else:
                results[post_id] = {"error": "Analysis failed"}
        
        return results
    