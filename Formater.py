import json
import csv
import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from config import CATEGORIES_FILE

class VKDataConverter:
    def __init__(self, categories_file: str = CATEGORIES_FILE):
        self.categories = self._load_categories(categories_file)
        self.political_views_map = {
            1: "коммунистические",
            2: "социалистические",
            3: "умеренные",
            4: "либеральные",
            5: "консервативные",
            6: "монархические",
            7: "ультраконсервативные",
            8: "индифферентные",
            9: "либертарианские"
        }
        self.sentiments_map = {
            "POSITIVE": 1,
            "NEUTRAL":0,
            "NEGATIVE": -1
        }

    def _map_political_view(self, view_code: Optional[int]) -> Optional[str]:
        """Преобразует код политических взглядов в текстовое описание"""
        if view_code is None:
            return None
        return self.political_views_map.get(view_code, f"неизвестные ({view_code})")
    
    def _load_categories(self, file_path: str) -> List[str]:
        """Загружает список категорий из файла (значения справа от двоеточия)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                category_mapping = json.load(f)
            categories = list(set(category_mapping.values()))
            categories.append("Неопределенная категория")
            return categories
        except (FileNotFoundError, json.JSONDecodeError):
            return ["погода", "спорт", "садоводство", "еда", "Неопределенная категория"]

    def _analyze_posts(self, posts: Dict) -> Tuple[Dict[str, int], Dict[str, str]]:
        """
        Анализирует посты и возвращает:
        1. Количество постов по категориям
        2. Наиболее частую тональность для каждой категории
        """
        category_counts = {category: 0 for category in self.categories}
        category_sentiments = {category: defaultdict(int) for category in self.categories}
        
        if not posts:
            return category_counts, {category: "N/A" for category in self.categories}
            
        for post in posts.values():
            if 'category' not in post or 'sentiment' not in post:
                continue
                
            category = post['category']['label']
            sentiment = post['sentiment']['label']
            
            # Считаем количество постов по категориям
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Считаем тональности для каждой категории
            category_sentiments[category][sentiment] += 1
        
        # Определяем наиболее частую тональность для каждой категории
        dominant_sentiments = {}
        for category, sentiments in category_sentiments.items():
            if sentiments:
                dominant_sentiment = max(sentiments.items(), key=lambda x: x[1])[0]
                dominant_sentiments[category] = dominant_sentiment
            else:
                dominant_sentiments[category] = "N/A"
                
        return category_counts, dominant_sentiments
    def _count_raiting(self, category_counts:Dict[str, int], category_sentiments:Dict[int,int], post_lang_percent:float, suspicious_words:int) -> int:
        raiting = 0
        for category in self.categories:
            countCat = category_counts.get(category, 0)
            sentiment = category_sentiments.get(category, "N/A")
            sentiment_number = self.sentiments_map.get(sentiment, 0)
            raiting += countCat*sentiment_number
        raiting -= round((100-post_lang_percent)/20)
        raiting -= round(suspicious_words/3)
        return raiting
    def _process_user(self, user: Dict) -> Dict[str, Optional[str]]:
        """Обрабатывает данные одного пользователя"""
        personal = user.get('personal', {})
        posts = user.get('posts', {})
        
        # Получаем статистику по постам
        category_counts, category_sentiments = self._analyze_posts(posts)
        total_posts = len(posts)
        russian_posts = sum(1 for p in posts.values() if p.get('language') == 'ru')
        
        # Преобразуем политические предпочтения
        political_view = self._map_political_view(personal.get('political'))
        post_lang_percent = round(russian_posts / total_posts * 100, 2) if total_posts > 0 else 0
        suspicious_words_count = sum(len(p.get('suspicious_words', [])) for p in posts.values())
        # Формируем строку данных
        row_data = {
            'VK ID': user.get('id'),
            'Имя': user.get('first_name'),
            'Фамилия': user.get('last_name'),
            'Страна': user.get('country'),
            'Город': user.get('city'),
            'Пол': user.get('sex'),
            'Дата рождения': user.get('bdate'),
            'Место учёбы': user.get('education', {}).get('university') if isinstance(user.get('education'), dict) else None,
            'Интересы': user.get('interests'),
            'Телефон': user.get('mobile_phone'),
            'Полит. предпочтения': political_view,
            'Мировоззрение': personal.get('religion'),
            'Количество постов': total_posts,
            'Постов на русском (%)': post_lang_percent,
            'Подозрительные слова': suspicious_words_count
        }
        
        # Добавляем данные по категориям (количество и тональность)
        for category in self.categories:
            row_data[f'"{category}"'] = category_counts.get(category, 0)
            row_data[f'Преобладающая тональность "{category}"'] = category_sentiments.get(category, "N/A")
        if total_posts>0:
            row_data["Рейтинг"] = self._count_raiting(category_counts, category_sentiments, post_lang_percent, suspicious_words_count)
        else:
            row_data["Рейтинг"] = 0
        return row_data

    def convert_to_csv(self, input_json: str, output_csv: str):
        """Конвертирует JSON в CSV с новыми столбцами тональности"""
        os.makedirs('results', exist_ok=True)
        with open(input_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        rows = [self._process_user(user) for user in data]
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    def convert_to_excel(self, input_json: str, output_xlsx: str):
        """Конвертирует JSON в Excel с новыми столбцами тональности"""
        
        os.makedirs('results', exist_ok=True)
        with open(input_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        rows = [self._process_user(user) for user in data]
        df = pd.DataFrame(rows)
        
        # Упорядочиваем столбцы для лучшей читаемости
        columns_order = [
            'VK ID', 'Имя', 'Фамилия', 'Страна', 'Город', 'Пол', 
            'Дата рождения', 'Место учёбы', 'Интересы', 'Телефон',
            'Полит. предпочтения', 'Мировоззрение', 'Количество постов',
            'Постов на русском (%)', 'Подозрительные слова'
        ]
        
        # Добавляем категории и их тональности
        for category in self.categories:
            columns_order.extend([f'"{category}"', f'Преобладающая тональность "{category}"'])
        columns_order.extend(['Рейтинг'])
        df = df[columns_order]
        df.to_excel(output_xlsx, index=False, engine='openpyxl')

    def process_file(self, input_json = 'vk_users_WITH_POSTS.json', output_prefix: str = 'vk_data'):
        """Обрабатывает файл и создает оба формата с тональностями"""
        input_path = Path(input_json)
        output_csv = f"{output_prefix}_{input_path.stem}.csv"
        output_xlsx = f"{output_prefix}_{input_path.stem}.xlsx"
        
        self.convert_to_csv(Path(f'data/{input_json}'), Path(f'results/{output_csv}'))
        self.convert_to_excel(Path(f'data/{input_json}'), Path(f'results/{output_xlsx}'))
        
        print(f"Созданы файлы:\n- {output_csv}\n- {output_xlsx}")

# Пример использования
if __name__ == "__main__":
    converter = VKDataConverter()
    converter.process_file()