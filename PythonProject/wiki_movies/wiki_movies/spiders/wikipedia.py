import scrapy
import re
from urllib.parse import urljoin
from wiki_movies.items import MovieItem
import json
from datetime import datetime


class WikipediaSpider(scrapy.Spider):
    name = 'wikipedia'
    allowed_domains = ['ru.wikipedia.org', 'www.wikidata.org']
    start_urls = ['https://ru.wikipedia.org/wiki/Категория:Фильмы_по_алфавиту']

    def parse(self, response):
        movie_links = response.css('div#mw-pages li a')
        for link in movie_links:
            href = link.css('::attr(href)').get()
            title = link.css('::attr(title)').get()
            link_text = link.css('::text').get(default='').strip()
            if not href:
                continue
            if any(x in href for x in ['Категория:', 'Служебная:', 'Википедия:', 'Шаблон:']):
                continue
            if link_text and any(x in link_text for x in ['Категория:', 'Шаблон:', 'Обсуждение:']):
                continue
            if (title and not any(x in title for x in
                                  ['Категория:', 'Википедия:', 'Служебная:', 'Шаблон:', 'Обсуждение:']) and
                    ('фильм' in title.lower() or
                     'кино' in title.lower() or
                     len(title) > 3)):  
                movie_url = urljoin(response.url, href)
                yield scrapy.Request(
                    url=movie_url,
                    callback=self.parse_movie,
                    meta={'movie_title': title}
                )
        next_page = response.css('a:contains("Следующая страница")::attr(href)').get()
        if next_page:
            next_page_url = urljoin(response.url, next_page)
            yield scrapy.Request(url=next_page_url, callback=self.parse)

    def parse_movie(self, response):
        item = MovieItem()
        title = (
                response.css('h1#firstHeading span::text').get() or  
                response.css('h1#firstHeading::text').get() or  
                response.css('h1.page-title::text').get() or 
                response.css('h1.mw-first-heading::text').get() or 
                response.meta.get('movie_title', '')
        )
        if title:
            title = re.sub(r'\s*\([^)]*фильм[^)]*\)', '', title)
            title = re.sub(r'\s*\([^)]*кинокартина[^)]*\)', '', title)
            title = re.sub(r'\s*\([^)]*кинофильм[^)]*\)', '', title)
            title = title.strip()
        item['title'] = title if title else 'Неизвестно'
        item['wiki_url'] = response.url
        wikidata_link = response.css('li#t-wikidata a::attr(href)').get()
        if not wikidata_link:
            wikidata_link = response.css('a[href*="wikidata.org/wiki/Q"]::attr(href)').get()
        if wikidata_link:
            match = re.search(r'Q\d+', wikidata_link)
            if match:
                item['qid'] = match.group(0)
        self.parse_infobox(response, item)
        if not title or ('фильм' not in response.text.lower() and
                         'кино' not in response.text.lower() and
                         'кинокартина' not in response.text.lower()):
            return
        if any(not item.get(field) for field in ['genre', 'director', 'country', 'year']):
            if item.get('qid'):
                wikidata_url = f"https://www.wikidata.org/wiki/Special:EntityData/{item['qid']}.json"
                yield scrapy.Request(
                    url=wikidata_url,
                    callback=self.parse_wikidata,
                    meta={'item': item}
                )
            else:
                yield item
        else:
            yield item

    def parse_infobox(self, response, item):
        infobox = response.css('table.infobox')
        if not infobox:
            return
        rows = infobox.css('tr')
        for row in rows:
            th_text = row.css('th ::text').get(default='').strip()
            td = row.css('td')
            if not th_text or not td:
                continue
            td_text = self.extract_td_text(td)
            if not td_text:
                continue
            if 'Жанр' in th_text:
                item['genre'] = self.clean_genre(td_text)
            elif 'Режиссёр' in th_text:
                item['director'] = self.clean_director(td_text)
            elif 'Страна' in th_text:
                item['country'] = self.clean_country(td_text)
            elif 'Год' in th_text:
                item['year'] = self.extract_year(td_text)
            elif 'Дата выхода' in th_text and not item.get('year'):
                item['year'] = self.extract_year(td_text)

    def extract_td_text(self, td_element):
        if not td_element:
            return ''
        if isinstance(td_element, list):
            if not td_element:
                return ''
            td = td_element[0]
        else:
            td = td_element
        td_copy = td.copy() if hasattr(td, 'copy') else td
        if hasattr(td_copy, 'css'):
            for elem in td_copy.css('sup, small, .mw-editsection, .reference, img'):
                if hasattr(elem, 'extract'):
                    elem.extract()
        else:
            return ''
        texts = []
        seen = set()
        links = td_copy.css('a')
        if links:
            for link in links:
                link_text = link.css('::text').get(default='').strip()
                if link_text and link_text not in seen and len(link_text) > 1:
                    if not any(x in link_text.lower() for x in ['файл:', 'изображение', 'картинка', 'icon']):
                        seen.add(link_text)
                        texts.append(link_text)
        if not texts:
            for span in td_copy.css('span'):
                span_text = span.css('::text').get(default='').strip()
                if span_text and span_text not in seen and len(span_text) > 1:
                    seen.add(span_text)
                    texts.append(span_text)
        if not texts:
            all_texts = td_copy.css('::text').getall()
            for text in all_texts:
                cleaned = text.strip()
                if (cleaned and
                        cleaned not in seen and
                        len(cleaned) > 1 and
                        not cleaned.startswith(('(', '[', '—', '\n', '•')) and
                        not cleaned.endswith((':', ';'))):
                    seen.add(cleaned)
                    texts.append(cleaned)
        return ' | '.join(texts) if texts else ''

    def clean_director(self, director_text):
        if not director_text:
            return ''
        parts = [p.strip() for p in director_text.split(' | ') if p.strip()]
        unique_parts = []
        seen = set()
        for part in parts:
            cleaned = re.sub(
                r'\b(режиссёр|режиссер|реж\.?|сорежиссёр|и|совместно\s+с|,\s*и)\b',
                '',
                part,
                flags=re.IGNORECASE
            ).strip()
            cleaned = re.sub(r'\([^)]*\)', '', cleaned).strip()
            cleaned = re.sub(r'[.,;]\s*$', '', cleaned).strip()
            if cleaned and cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                unique_parts.append(cleaned)
        return ' | '.join(unique_parts) if unique_parts else ''
    def clean_country(self, country_text):
        if not country_text:
            return ''
        parts = [p.strip() for p in country_text.split(' | ') if p.strip()]
        unique_parts = []
        seen = set()
        for part in parts:
            cleaned = re.sub(
                r'\b(страна|страны|и|совместно|производство|с)\b',
                '',
                part,
                flags=re.IGNORECASE
            ).strip()
            cleaned = re.sub(r'\([^)]*\)', '', cleaned).strip()
            cleaned = re.sub(r'[.,;]\s*$', '', cleaned).strip()
            if cleaned and cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                unique_parts.append(cleaned)
        return ' | '.join(unique_parts) if unique_parts else ''

    def clean_genre(self, genre_text):
        if not genre_text:
            return ''
        parts = [p.strip() for p in genre_text.split(' | ') if p.strip()]
        unique_parts = []
        seen = set()
        for part in parts:
            cleaned = re.sub(
                r'\b(жанр|жанры|и|с\s+элементами|в\s+жанре)\b',
                '',
                part,
                flags=re.IGNORECASE
            ).strip()
            cleaned = re.sub(r'\([^)]*\)', '', cleaned).strip()
            if cleaned and cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                unique_parts.append(cleaned)
        return ' | '.join(unique_parts) if unique_parts else ''

    def extract_year(self, text):
        if not text:
            return ''
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', text)
        if year_match:
            return year_match.group(1)
        date_match = re.search(r'\b(\d{1,2}\s+\w+\s+\d{4})\b', text)
        if date_match:
            try:
                date_str = date_match.group(1)
                for fmt in ('%d %B %Y', '%d %b %Y', '%B %d, %Y'):
                    try:
                        date_obj = datetime.strptime(date_str, fmt)
                        return str(date_obj.year)
                    except:
                        continue
            except:
                pass

        return ''

    def parse_wikidata(self, response):
        item = response.meta['item']
        try:
            data = json.loads(response.text)
            entity_id = item['qid']
            if entity_id in data.get('entities', {}):
                entity = data['entities'][entity_id]
                claims = entity.get('claims', {})
                property_map = {
                    'P136': 'genre',  # жанр
                    'P57': 'director',  # режиссёр
                    'P495': 'country',  # страна производства
                    'P577': 'year'  # дата публикации
                }
                for prop, field in property_map.items():
                    if prop in claims and not item.get(field):
                        value = self.extract_wikidata_value(claims[prop])
                        if value:
                            item[field] = value
                if 'P577' in claims and not item.get('year'):
                    date_value = self.extract_wikidata_value(claims['P577'])
                    if date_value and len(date_value) >= 4:
                        item['year'] = date_value[:4]
        except json.JSONDecodeError:
            pass
        yield item

    def extract_wikidata_value(self, claim_list):
        if not claim_list:
            return ''
        mainsnak = claim_list[0].get('mainsnak', {})
        datavalue = mainsnak.get('datavalue', {})
        if datavalue.get('type') == 'string':
            return datavalue.get('value', '')
        elif datavalue.get('type') == 'wikibase-entityid':
            entity_id = datavalue.get('value', {}).get('id', '')
            return entity_id
        elif datavalue.get('type') == 'time':
            time_value = datavalue.get('value', {}).get('time', '')
            if time_value and len(time_value) >= 5:
                return time_value[1:5]
        return ''
