BOT_NAME = 'wiki_movies'

SPIDER_MODULES = ['wiki_movies.spiders']
NEWSPIDER_MODULE = 'wiki_movies.spiders'

ROBOTSTXT_OBEY = True
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

DOWNLOAD_DELAY = 0.5
CONCURRENT_REQUESTS_PER_DOMAIN = 4

FEEDS = {
    'movies.csv': {
        'format': 'csv',
        'encoding': 'utf8',
        'fields': ['title', 'genre', 'director', 'country', 'year'],
        'overwrite': True
    }
}

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,

}
