
import threading
stop_loading_event = threading.Event()
def show_loading_message():
    loading_message = "Загрузка"
    while not stop_loading_event.is_set():
        print('\r' + loading_message, end='', flush=True)
        for i in range(3):
            print('.', end='', flush=True)
            threading.Event().wait(0.5)  # Combined wait time for 3 dots
        
        print('\r\033[K', end='', flush=True)  # Clear the line using ANSI escape code
t = threading.Thread(target=show_loading_message)
t.start()
from DataExtraction import VKDataExtractor
from UserPostsAnalyzer import UserPostsAnalyzer
from Formater import VKDataConverter
import os
stop_loading_event.set()
t.join()

def show_welcome_message():
    message = """
================================================================
    Добро пожаловать в программу "Цифровой портрет мигранта"
================================================================

Описание:
Эта программа предназначена для составления цифорвого портрета 
человека по странице профиля в социальной сети ВКонтакте.
Она позволяет:
1) осуществлять сбор персональных данных из профиля социальной 
сети ВКонтакте 
2) давать оценку лояльности на основании текста постов с использованием 
предобученных моделей машинного обучения.

Основные функции:
- Выгрузка данных профилей пользователей из указанных сообществ ВКонтакте
- Анализ собранных данных с использованием моделей машинного обучения и составление оценки лояльности
- Визуализация результатов анализа в табличной форме файлом Excel 

Авторы: Токмолаев Максим, Руденко Иван, Беспалов Юрий
Дата создания: 2025 год

============================================================
"""
    print(message)
    input("Нажмите Enter для продолжения...")
exit = 0
def prompt_data_export(vk_extractor):
    global exit
    choice = input("Хотите выгрузить данные сейчас? (да/нет): ").strip().lower()
    while choice not in ("exit", "выход", "quit"):
        if choice in ("да", "д", "yes", "y"):
            print("Выполняется выгрузка данных...")
            vk_extractor.extract_groups_data()
            print("Данные успешно выгружены.\n")
            return 0
        else:
            if choice in ("нет", "н", "no", "n"):
                if not os.path.exists('data/vk_users_data.json'):
                    print("Файл с данными пользователей не найден. Пожалуйста, сначала выполните выгрузку данных.")
                else:
                    print("Выгрузка данных пропущена.\n")
                    return 0
        choice = input("Хотите выгрузить данные сейчас? (да/нет): ").strip().lower()
    exit = 1
def prompt_data_analysis(analyzer):
    global exit
    if exit == 1 : return 0 
    choice = input("Хотите начать анализ данных? (да/нет): ").strip().lower()
    while choice not in ("exit", "выход", "quit"):
        if choice in ("да", "д", "yes", "y"):
            print("Выполняется анализ постов пользователей...")
            analyzer.process_all_users()
            print("Данные успешно проанализированны.\n")
            return 0
        else:
            if choice in ("нет", "н", "no", "n"):
                if not os.path.exists('data/vk_users_data.json'):
                    print("Файл с проанализированными постами пользователей не найден. Пожалуйста, сначала выполните анализ данных.")
                else:
                    print("Анализ данных пропущен.\n")
                    return 0
        choice = input("Хотите начать анализ данных? (да/нет): ").strip().lower()
    exit = 1
def prompt_creating_table(formater):
    global exit
    if exit == 1 : return 0 
    choice = input("Хотите создать таблицу? (да/нет): ").strip().lower()
    while choice not in ("exit", "выход", "quit"):
        if choice in ("да", "д", "yes", "y"):
            print("Выполняется конвертация данных в таблицу...")
            formater.process_file()
            print("Конвертация проведена успешно.\n")
            return 0
        else:
            if choice in ("нет", "н", "no", "n"):
                print("создание таблицы пропущено.\n")
                return 0
        choice = input("Хотите создать таблицу? (да/нет): ").strip().lower()
def print_exit_message():
    message = """
============================================================
Программа завершила работу.
Спасибо за использование системы "Цифровой портрет мигранта".
До свидания!
============================================================
"""
    print(message)
    input("Нажмите Enter для выхода...")

def main():
    vk_extractor = VKDataExtractor()
    analyzer = UserPostsAnalyzer()
    formater = VKDataConverter()

    show_welcome_message()
    prompt_data_export(vk_extractor)
    prompt_data_analysis(analyzer)
    prompt_creating_table(formater)
    print_exit_message()
if __name__ == "__main__":
    main()
   