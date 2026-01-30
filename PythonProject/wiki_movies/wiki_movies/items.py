import scrapy

class MovieItem(scrapy.Item):
    title = scrapy.Field()        # Название фильма
    genre = scrapy.Field()        # Жанр/жанры
    director = scrapy.Field()     # Режиссёр
    country = scrapy.Field()      # Страна
    year = scrapy.Field()         # Год выпуска
    wiki_url = scrapy.Field()     # URL страницы Wikipedia
    qid = scrapy.Field()          # ID Wikidata (для fallback)
