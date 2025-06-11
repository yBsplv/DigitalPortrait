import json
import os
from typing import Dict, List
from PostSentenceAnalysis import VkTextAnalyzer
from WordsFinder import WordFinder
import time
from config import POST_COUNT

class UserPostsAnalyzer:
    def __init__(self, users_file = 'vk_users_data.json', output_file = 'vk_users_WITH_POSTS.json', progress_file = 'progress.json'):
        """
        Инициализация анализатора:
        :param users_file: путь к файлу с данными пользователей
        :param output_file: путь к файлу для сохранения результатов
        :param word_list_file: путь к файлу со словами для поиска
        """
        self.users_file = users_file
        self.output_file = output_file
        self.progress_file = progress_file
        self.vk_analyzer = VkTextAnalyzer()
        self.word_finder = WordFinder()

    def load_users(self) -> List[Dict]:
        """Загрузка данных о пользователях из JSON файла"""
        filepath = os.path.join('data', self.users_file)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_progress(self) -> Dict:
        """Загрузка прогресса обработки с обработкой ошибок"""
        default_progress = {
            'last_processed_id': None,
            'processed_users': [],
            'total_users': 0
        }
        filepath = os.path.join('data', self.progress_file)
        if not os.path.exists(filepath):
            return default_progress
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():  # Если файл пустой
                    return default_progress
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Ошибка чтения файла прогресса: {e}. Будет использован пустой прогресс")
            return default_progress

    def save_progress(self, last_processed_id: int, processed_users: List[int], total_users: int):
        """Сохранение текущего прогресса"""
        progress = {
            'last_processed_id': last_processed_id,
            'processed_users': processed_users,
            'total_users': total_users
        }
        filepath = os.path.join('data', self.progress_file)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(progress, f)

    def save_results(self, users_data: List[Dict]):
        """Сохранение обновленных данных пользователей в JSON файл"""
        filepath = os.path.join('data', self.output_file)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False, indent=4)

    def analyze_user_posts(self, user_id: int) -> Dict[int, Dict]:
        """
        Анализ постов пользователя:
        1. Получение постов
        2. Анализ текстов
        3. Поиск ключевых слов для русскоязычных постов
        """
        # Получаем посты пользователя
        posts = self.vk_analyzer.fetch_all_vk_posts(str(user_id), max_posts=POST_COUNT)
        
        # Анализируем тексты постов
        analyzed_posts = self.vk_analyzer.analyze_texts(posts)
        
        # Ищем ключевые слова в русскоязычных постах
        for post_id, post_data in analyzed_posts.items():
            if post_data['language'] == 'ru':
                matches = self.word_finder.find_matches(post_data['original_text'])
                post_data['suspicious_words'] = matches
        
        return analyzed_posts

    def process_all_users(self):
        """Основной метод обработки всех пользователей"""
        # Загружаем данные пользователей
        users_data = self.load_users()
        total_users = len(users_data)

        # Загружаем прогресс
        progress = self.load_progress()
        last_processed_id = progress.get('last_processed_id')
        processed_users = progress.get('processed_users', [])
        # Определяем с какого пользователя начинать
        start_index = 0
        if last_processed_id:
            for i, user in enumerate(users_data):
                if user['id'] == last_processed_id:
                    start_index = i + 1
                    break
        
        # Обрабатываем каждого пользователя
        for i in range(start_index, total_users):
            user = users_data[i]
            user_id = user['id']
            try:
                # Анализируем посты пользователя
                analyzed_posts = self.analyze_user_posts(user_id)
                time.sleep(0.5) 
                # Добавляем результаты анализа в данные пользователя
                user['posts'] = analyzed_posts
                # Сохраняем прогресс после каждого пользователя
                self.save_progress(user_id, processed_users, total_users)
                self.save_results(users_data)

                print(f"Анализ профиля завершен. Обработано {len(analyzed_posts)} постов.")
                
            except Exception as e:
                print(f"Ошибка при обработке пользователя {user_id}: {str(e)}")
                user['analyzed_posts'] = None
                # Сохраняем прогресс даже при ошибке
                self.save_progress(user_id, processed_users, total_users)
                self.save_results(users_data)
        
        # Сохраняем обновленные данные
        self.save_results(users_data)
        print(f"Результаты сохранены в {self.output_file}")

# Пример использования
if __name__ == "__main__":
    analyzer = UserPostsAnalyzer()
    analyzer.process_all_users()