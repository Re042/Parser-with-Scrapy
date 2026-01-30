BOT_NAME = 'wiki_movies'

SPIDER_MODULES = ['wiki_movies.spiders']
NEWSPIDER_MODULE = 'wiki_movies.spiders'

# Настройки для обхода сайта
ROBOTSTXT_OBEY = True
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# Настройка задержки между запросами
DOWNLOAD_DELAY = 0.5
CONCURRENT_REQUESTS_PER_DOMAIN = 4

# Настройка экспорта в CSV
FEEDS = {
    'movies.csv': {
        'format': 'csv',
        'encoding': 'utf8',
        'fields': ['title', 'genre', 'director', 'country', 'year'],
        'overwrite': True
    }
}

# Включение middleware для случайных User-Agent
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
}