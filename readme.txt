Установка моделей с hugging face (3.7Gb) - modelsDownload.py

!без необходимых библиотек (requirements.txt) и моделей не работает
!python3.10

Для изменения через config.json доступны:
1) Группы, из которых берутся профили
2) Количество, выгружаемых профилей на группу
3) Количество постов на профиль
4) Модели
5) Путь к файлу со списком слов и файлу с категориями


Папки:
Data - json файлы с данными из вк
Results - таблицы, сформированные в результате работы программы
Models - модели, используемые в программе
 

Модули:
1) DataExtraction
    -Выгружает данные пользователей из группы и записывает в json файл
    -Сохраняет выгруженные id по группам в другой json файл
2) WordsFinder
    -Получает на входе текст поста и возвращает слова из текста совпадающие со словами из списка
3)  PostSenteceAnalysis
    -Выгружает посты по указанному id и проводит их анализ
    -Отдает на выходе словарь с результатом анализа
4) UserPostAnalyzer
    -Проводит анализ постов и выводит в новый файл с данными пользователей, постами
    и результатом анализа этих постов.
    -Составляет текущий прогресс обработки профилей и выводит его в файл
    -Использует модули WordsFinder и PostSenteceAnalysis
5) Formater
    -Формирует таблицу из полученных данных
6) DigitalPortrait
    -Реализует консольный интерфейс и запускает модули выгрузки, анализа и формирования таблицы.