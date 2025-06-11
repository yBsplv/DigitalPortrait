import re
from typing import List, Set
import pymorphy2
from config import WORDS_FILE

class WordFinder:
    def __init__(self):
        self.morph = pymorphy2.MorphAnalyzer()
        self.words_and_phrases = self._load_words_and_phrases()  # Исправлено название метода

    def _load_words_and_phrases(self) -> Set[str]:
        """Загружает слова и словосочетания из файла, разделённые запятыми."""
        with open(WORDS_FILE, 'r', encoding='utf-8') as file:
            content = file.read()
            # Разделяем по запятым, убираем пробелы и пустые элементы
            phrases = {
                phrase.strip().lower()
                for phrase in re.split(r',\s*', content)  # Разделитель: запятая + пробелы
                if phrase.strip()
            }
            return phrases

    def _lemmatize_word(self, word: str) -> str:
        """Приводит слово к нормальной форме (лемме)."""
        parsed = self.morph.parse(word)[0]
        return parsed.normal_form

    def find_matches(self, text: str) -> List[str]:
        """
        Находит слова и словосочетания из списка в тексте.
        Возвращает уникальные совпадения в порядке их появления.
        """
        text_lower = text.lower()
        matches = set()
        result = []

        # Сначала проверяем словосочетания (длинные фразы)
        for phrase in sorted(self.words_and_phrases, key=len, reverse=True):
            if ' ' in phrase and phrase in text_lower and phrase not in matches:
                matches.add(phrase)
                result.append(phrase)

        # Затем ищем отдельные слова (с лемматизацией)
        words_in_text = re.findall(r'\b\w+\b', text_lower)
        for word in words_in_text:
            lemma = self._lemmatize_word(word)
            if lemma in self.words_and_phrases and lemma not in matches:
                matches.add(lemma)
                result.append(lemma)

        return result

if __name__ == "__main__":
    """Интерфейс для внешнего кода: принимает текст, возвращает найденные слова."""
    text = "Мы будем ждать своего часа. Всё, что произошло раньше - это лишь подготовка к грандиозному решающему сражению. Всем в столп! Пугая и страшая врагов, мы приближаемся к победе. Вместе нас ничего не пересечет. Погибаем вместе и защищаем свою землю. Наш дело - справедливость и правда. Мстим за бесчисленные преступления. Идём к славе, к вечной памяти в истории нашей страны. Всем в столп! Помни о нас и не забывайте о нас. Наша верность - непоколебимая. Вера в победу - неизменная. Кровь героев - сливается с кровью мучеников. Боевики, террористы, солдаты свободы, мстители, убийцы, наша справедливость и правда - расправа над злодеями. Возмездие за их преступления будет жестоким. Наши герои не умрут взаимно. Покажем им силу нашей страны, сломленные души наших собратьев - наша гордость и отвага. Отомстим за убитых братьев, за те, кто погиб в борьбе. Кровь невинных - не даст их предателям спасения и мира. Насилие против нашего народа будет отомщено стократно. Мы будем терранить врагов до последнего из них. Слава нашей стране! Защитим своих людей от бесчинств нечистой силы. Кровь героев - искупление за страдания народа, правды и справедливости. Всем в столп! Покажем им силу и правосудие. Используя все средства, мы будем преследовать своих врагов до конца света. Терроризируем их души, уничтожаем мирное население, разрушаем инфраструктуру страны-врага, причиняем им беспощадную болезнь и боль, предаём их собственным страхам. Наша справедливость - не даст им покоя."
    finder = WordFinder()
    print(finder.find_matches(text))