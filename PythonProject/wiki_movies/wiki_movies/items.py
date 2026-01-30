import scrapy

class MovieItem(scrapy.Item):
    title = scrapy.Field()        
    genre = scrapy.Field()        
    director = scrapy.Field()     
    country = scrapy.Field()      
    year = scrapy.Field()         
    wiki_url = scrapy.Field()     
    qid = scrapy.Field()          
