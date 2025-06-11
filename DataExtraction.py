import requests
import json
from datetime import datetime
import time
import os
from config import VK_API_TOKEN, GROUPS_IDS, USERS_COUNT

class VKDataExtractor:
    def __init__(self, state_file='vk_extractor_state.json', version='5.131'):
        """
        Инициализация модуля.
        
        :param access_token: Токен доступа VK API
        :param state_file: Файл для сохранения состояния выгрузки (offset)
        :param version: Версия API VK (по умолчанию 5.131)
        """
        self.access_token = VK_API_TOKEN
        self.version = version
        self.api_url = 'https://api.vk.com/method/'
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self):
        """Загружает состояние выгрузки из файла (если существует), иначе создаёт новый."""
        default_state = {}
        filepath = os.path.join('data', self.state_file)
        
        # Создаем директорию data, если она не существует
        os.makedirs('data', exist_ok=True)

        if not os.path.exists(filepath):
            # Файл не существует — создаём его с пустым содержимым
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(default_state, f, ensure_ascii=False, indent=4)
            return default_state

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return default_state
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка загрузки состояния: {e}. Используется состояние по умолчанию.")
            return default_state
            
    def _save_state(self):
        """
        Сохраняет текущее состояние выгрузки в файл.
        """
        filepath = os.path.join('data', self.state_file)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=4)

    def _make_request(self, method, params):
        """
        Отправляет запрос к API VK.
        """
        params.update({
            'access_token': self.access_token,
            'v': self.version
        })
        response = requests.get(f"{self.api_url}{method}", params=params)
        return response.json()

    def get_group_members(self, group_id, count=1000, offset=0):
        """
        Получает список участников группы.
        """
        method = 'groups.getMembers'
        params = {
            'group_id': group_id,
            'count': count,
            'offset': offset,
            'fields': 'sex,bdate,city,country,personal,contacts,education,interests'
        }

        try:
            response = self._make_request(method, params)
            if 'response' in response and 'items' in response['response']:
                return response['response']['items']
            else:
                print(f"Ошибка при получении участников: {response.get('error', 'Неизвестная ошибка')}")
                return []
        except Exception as e:
            print(f"Ошибка при запросе участников: {e}")
            return []

    def get_user_photos_geo(self, user_id, count=50):
        """
        Получает геометки из фотографий пользователя.
        """
        method = 'photos.getAll'
        params = {
            'owner_id': user_id,
            'count': count,
            'extended': 1,
            'photo_sizes': 0
        }

        try:
            response = self._make_request(method, params)
            if 'response' in response and 'items' in response['response']:
                geo_data = []
                for photo in response['response']['items']:
                    if 'lat' in photo and 'long' in photo:
                        geo_data.append({
                            'lat': photo['lat'],
                            'long': photo['long']
                        })
                return geo_data if geo_data else None
            return None
        except Exception as e:
            print(f"Ошибка при получении геометок пользователя {user_id}: {e}")
            return None

    def extract_user_data(self, user):
        """
        Извлекает данные пользователя из объекта, полученного от API.
        """
        user_data = {
            'id': user.get('id'),
            'first_name': user.get('first_name', ''),
            'last_name': user.get('last_name', ''),
            'country': user.get('country', {}).get('title') if 'country' in user else None,
            'city': user.get('city', {}).get('title') if 'city' in user else None,
            'sex': 'Мужской' if user.get('sex') == 2 else 'Женский' if user.get('sex') == 1 else None,
            'bdate': user.get('bdate'),
            'education': {
                'university': user.get('university_name'),
                'faculty': user.get('faculty_name')
            } if 'university_name' in user or 'faculty_name' in user else None,
            'interests': user.get('interests'),
            'mobile_phone': user.get('mobile_phone'),
            'home_phone': user.get('home_phone'),
            'personal': user.get('personal', {}),
            'photos_geo': self.get_user_photos_geo(user.get('id'))
        }
        return user_data

    def save_to_json(self, data, filename=None, group_id=None):
        """
        Сохраняет данные в JSON-файл.
        """
        filename = 'vk_users_data.json'
        filepath = os.path.join('data', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"Данные сохранены в файл: {filename}")

    def extract_group_users_data(self, group_id, max_users=1000, output_file=None, reset_offset=False):
        """
        Основной метод для выгрузки данных участников группы.
        
        :param group_id: ID группы
        :param max_users: Максимальное количество пользователей для сбора
        :param output_file: Имя выходного файла (опционально)
        :param reset_offset: Сбросить offset и начать выгрузку заново (по умолчанию False)
        """
        # Инициализация или сброс состояния для группы
        if reset_offset or group_id not in self.state:
            self.state[group_id] = {'offset': 0, 'processed_ids': []}

        current_state = self.state[group_id]
        offset = current_state['offset']
        processed_ids = set(current_state['processed_ids'])
        all_users_data = []
        batch_size = 1000  # Максимальный размер выборки за запрос

        while offset < max_users:
            current_count = min(batch_size, max_users - offset)
            print(f"Получение пользователей {offset + 1}-{offset + current_count}...")

            users = self.get_group_members(group_id, count=current_count, offset=offset)
            if not users:
                break

            new_users = [user for user in users if user.get('id') not in processed_ids]
            if not new_users:
                print("Новых пользователей не найдено. Возможно, достигнут конец списка.")
                break

            for user in new_users:
                try:
                    user_data = self.extract_user_data(user)
                    all_users_data.append(user_data)
                    processed_ids.add(user['id'])
                    print(f"Обработан пользователь: {user_data['first_name']} {user_data['last_name']}")
                    time.sleep(0.5)  # Задержка для избежания лимитов API
                except Exception as e:
                    print(f"Ошибка при обработке пользователя {user.get('id')}: {e}")

            offset += len(users)
            current_state['offset'] = offset
            current_state['processed_ids'] = list(processed_ids)
            self._save_state()  # Сохраняем состояние после каждой партии

        self.save_to_json(all_users_data, output_file, group_id)
        return all_users_data
    def restore_users_data_from_offset(self, group_id, output_file=None):
        """
        Восстанавливает данные пользователей по сохраненным ID из файла состояния.
        
        :param group_id: ID группы для проверки в состоянии
        :param output_file: Имя выходного файла (опционально)
        :return: Список восстановленных данных пользователей
        """
        if group_id not in self.state or not self.state[group_id].get('processed_ids'):
            print(f"Нет сохраненных ID пользователей для группы {group_id}")
            return []

        user_ids = self.state[group_id]['processed_ids']
        all_users_data = []
        
        print(f"Начало восстановления данных для {len(user_ids)} пользователей...")
        
        for i, user_id in enumerate(user_ids, 1):
            try:
                # Получаем данные пользователя по ID
                method = 'users.get'
                params = {
                    'user_ids': user_id,
                    'fields': 'sex,bdate,city,country,personal,contacts,education,interests'
                }
                
                response = self._make_request(method, params)
                if response and 'response' in response and response['response']:
                    user = response['response'][0]
                    user_data = self.extract_user_data(user)
                    all_users_data.append(user_data)
                    print(f"Восстановлен {i}/{len(user_ids)}: {user_data['first_name']} {user_data['last_name']}")
                else:
                    print(f"Не удалось получить данные для ID {user_id}")
                
                time.sleep(0.5)  # Задержка для соблюдения лимитов API
                
            except Exception as e:
                print(f"Ошибка при восстановлении пользователя {user_id}: {e}")
        
        # Сохраняем восстановленные данные
        if all_users_data:
            self.save_to_json(all_users_data, output_file, group_id)
        
        return all_users_data    
    def extract_groups_data(self, group_ids=GROUPS_IDS, max_users=USERS_COUNT, output_file=None, reset_offset=False):
        """
        Экстрактирует данные пользователей из нескольких групп.
        
        :param group_ids: Список ID групп
        :param max_users: Максимальное количество пользователей для сбора
        :param output_file: Имя выходного файла (опционально)
        :param reset_offset: Сбросить offset и начать выгрузку заново (по умолчанию False)
        """
        all_users_data = []
        
        for group_id in group_ids:
            print(f"Начинаем выгрузку данных для группы {group_id}...")
            users_data = self.extract_group_users_data(group_id, max_users, output_file, reset_offset)
            all_users_data.extend(users_data)
        
        return all_users_data
# Пример использования
if __name__ == "__main__":

    # Инициализация экстрактора с файлом состояния
    extractor = VKDataExtractor( state_file='state_offset.json')

    # ID группы (можно использовать как числовой ID, так и короткое имя)
    group_id = '229332064'  # Пример: 1 — это vk.com/id1 (Pavel Durov)

    # Выгружаем данные 100 участников группы (продолжая с последней позиции)
    extractor.restore_users_data_from_offset(group_id=group_id, output_file='wwww.json')