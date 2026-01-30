class WikiMoviesPipeline:
    def process_item(self, item, spider):
        # Очистка и нормализация данных
        for field in ['title', 'genre', 'director', 'country']:
            if field in item:
                value = item[field]
                if isinstance(value, str):
                    # Удаление лишних пробелов
                    item[field] = ' '.join(value.split())
                    # Удаление пустых значений
                    if item[field] in ['', '—', '-', '–']:
                        item[field] = ''

        # Обработка года
        if 'year' in item and item['year']:
            year = str(item['year']).strip()
            # Оставляем только цифры
            year_digits = ''.join(filter(str.isdigit, year))
            if year_digits and len(year_digits) == 4:
                item['year'] = year_digits[:4]
            else:
                item['year'] = ''

        return item


# В pipelines.py
import re


class CleanDuplicatesPipeline:
    def process_item(self, item, spider):
        for field in ['director', 'country', 'genre']:
            if field in item and item[field]:
                value = item[field]
                if isinstance(value, str) and ' | ' in value:
                    # Разбиваем, убираем дубликаты, сортируем для консистентности
                    parts = [p.strip() for p in value.split(' | ') if p.strip()]
                    # Удаляем дубликаты
                    unique_parts = []
                    seen = set()
                    for part in parts:
                        # Приводим к нижнему регистру для сравнения
                        lower_part = part.lower()
                        if lower_part not in seen:
                            seen.add(lower_part)
                            unique_parts.append(part)

                    # Убираем общие слова
                    clean_parts = []
                    for part in unique_parts:
                        clean = self.clean_field_value(part, field)
                        if clean:
                            clean_parts.append(clean)

                    item[field] = ' | '.join(clean_parts) if clean_parts else ''

        return item

    def clean_field_value(self, value, field_type):
        """Очищает значение поля от служебных слов"""
        value = value.strip()

        # Удаляем слова в скобках (часто это уточнения)
        value = re.sub(r'\([^)]*\)', '', value).strip()

        # Удаляем служебные слова для каждого типа поля
        stop_words = {
            'director': ['режиссёр', 'режиссер', 'реж.', 'сорежиссёр', 'и', 'совместно с'],
            'country': ['страна', 'страны', 'и', 'совместно', 'производство'],
            'genre': ['жанр', 'жанры', 'и', 'с элементами']
        }

        if field_type in stop_words:
            pattern = r'\b(' + '|'.join(stop_words[field_type]) + r')\b'
            value = re.sub(pattern, '', value, flags=re.IGNORECASE)

        # Удаляем лишние знаки препинания
        value = re.sub(r'[;:,\.]\s*$', '', value).strip()

        return value if value else None