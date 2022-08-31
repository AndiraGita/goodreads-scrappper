import math
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

class GoodreadsScrapper():
    def __init__(self):
        pass
    
    def get_book_by_id(self, book_id):
        url = 'https://www.goodreads.com/book/show/'

        response = requests.get(url+book_id, headers={"user-agent":"Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)"}, timeout=50)
        content = BeautifulSoup(response.content, 'html.parser')
        return content
    
    def get_book_list_by_list_id(self, list_id):
        url = 'https://www.goodreads.com/list/show/'

        response = requests.get(url+list_id)
    
        bl = BeautifulSoup(response.content, 'html.parser')

        book_titles = bl.find_all('a', {'class': 'bookTitle'})
        book_scores = bl.find_all('span', {'class': 'smallText uitext'})
        
        books = dict()

        for idx, (b_title, b_score) in enumerate(zip(book_titles, book_scores)):
            rank = idx+1
            book_id = b_title['href'].split('/')[-1]
            title = b_title.text.strip()
            try:
                score = int(re.findall('score: ((,|\d)+),', b_score.text)[0][0].replace(',', ''))
                num_vote = int(re.findall('((,|\d)+) people', b_score.text)[0][0].replace(',', ''))
            except IndexError:
                score = 'hidden'
                num_vote = 'hidden'
            
            books[idx] = {'rank': rank, 'book_id': book_id, 'title': title, 'score': score, 'num_vote': num_vote}
        
        return books
    
    def get_shelf_by_user_id(self, user_id):
        url = 'https://www.goodreads.com/review/list/'
    
        response = requests.get(url+user_id)
        bs_shelfs = BeautifulSoup(response.content, 'html.parser')
        shelfs = dict()
        idx = 0
        
        shelfs_url = bs_shelfs.find('div', {'id': 'shelvesSection'}).findChildren('a')
        print()
        for url in shelfs_url:
            try:
                name = url['href'].split('=')[-1]
                books = re.findall('\((\d+)\)', url.text)[0]
                shelfs[idx] = {'shelf_name': name, 'number_of_books': books}
                idx+=1
            except IndexError:
                break
        return shelfs
    
    def get_book_list_by_user_shelf(self, user_id, shelf_id='', number_of_book=30):
        rating_dict = {'it was amazing': 5, 'really liked it': 4, 'liked it': 3,'it was ok': 2,'did not like it': 1}
        
        BOOK_DISPLAYED_PER_PAGE = 30 # max displayed per page, couldn't be change
        
        user_url = 'https://www.goodreads.com/review/list/'+user_id+'?shelf='+shelf_id
        response = requests.get(user_url)
        bs_user = BeautifulSoup(response.content, 'html.parser')
        
        max_book = int(re.findall('\((\d+)\)', bs_user.find('a', {'class': 'selectedShelf'}).text)[0])
        
        desired_page = math.ceil(number_of_book/BOOK_DISPLAYED_PER_PAGE)
        max_page = math.ceil(max_book/BOOK_DISPLAYED_PER_PAGE)
        
        desired_page = desired_page if max_page > desired_page else max_page
        
        book_list = dict()
        
        idx = 0
        
        for p in range(1, desired_page+1):
            url = user_url+'&page='+str(p)
            response = requests.get(url)
            bs_user = BeautifulSoup(response.content, 'html.parser')
            
            reviews = bs_user.find_all('tr', {'class': 'bookalike review'})
            for r in reviews:
                book_id = r.find('td', {'class': 'field title'}).findChild('a')['href'].split('/')[-1]
                book_title = r.find('td', {'class': 'field title'}).findChild('a')['title']
                try:
                    user_rating = rating_dict[r.find('td', {'class': 'field rating'}).find('span')['title']]
                except:
                    user_rating = 0
                book_list[idx] = {'book_id': book_id, 'book_title': book_title, 'user_rating': user_rating}
                if idx==(number_of_book-1):
                    break
                idx+=1

            
        return book_list

class Book:
    def __init__(self, content):
        self.content = content
        self.fully_loaded = self.get_type()
        self.details = self.get_details()
      
    def get_type(self):
        if self.content.find('head').get('prefix') is None:
            return False
        return True
    
    def get_details(self):
        ratings = self.get_book_ratings()

        details = {'url': self.get_book_url(),
                   'title': self.get_book_title(),
                   'author': self.get_book_author(),
                   'isbn': self.get_book_isbn(),
                   'isbn13': self.get_book_isbn_13(),
                   'description': self.get_book_description(),
                   'average_rating': self.get_book_ratings_avg(),
                   'ratings_count': self.get_book_ratings_count(),
                   'reviews_count': self.get_book_reviews_count(),
                   '1_star': ratings[1],
                   '2_star': ratings[2],
                   '3_star': ratings[3],
                   '4_star': ratings[4],
                   '5_star': ratings[5],
                   'book_format': self.get_book_format(),
                   'book_edition': self.get_book_edition(),
                   'pages': self.get_book_pages(),
                   'publish_date': self.get_book_publish_date(),
                   'publisher': self.get_book_publisher(),
                   'first_published': self.get_book_first_publish(),
                   'series': self.get_book_series(),
                   'original_title': self.get_book_original_title(),
                   'edition_language': self.get_book_edition_language(),
                   'characters': self.get_book_characters(),
                   'setting': self.get_book_settings(),
                   'literary_awards': self.get_book_awards(),
                   'genres': self.get_book_genres()
                  }
        
        return details

    def get_book_url(self):
        if self.fully_loaded:
            return self.content.find('link')['href'].split('/')[-1]
        else:
            return re.findall('book\/show\/([a-zA-Z\d\-\.\_]*)', str(self.content))[0]
            

    def get_book_title(self):
        return self.content.find('meta', {'property': 'og:title'})['content']

    def get_book_original_title(self):
        try:
            if self.fully_loaded:
                return self.content.find(text=re.compile('Original Title')).find_next().text
            else:
                return re.findall('"originalTitle":\s?"((.|\s)*?)"', str(self.content))[0][0]
        except (AttributeError, IndexError):
            return None

    def get_book_author(self):
        if self.fully_loaded:
            return self.content.find('a', {'class': 'authorName'}).text.strip()
        else:
            return re.findall('data-testid="name">(.*?)<\/span>', str(self.content))[0]

    def get_book_isbn_13(self):
        try:
            if self.fully_loaded:
                return self.content.find('span', {'itemprop': 'isbn'}).text.strip()
            return re.findall('"isbn13":"(\d{13})"', str(self.content))[0]
        except (AttributeError, IndexError):
            return None

    def get_book_isbn(self):
        try:
            if self.fully_loaded:
                return self.content.find('div', {'class': 'infoBoxRowTitle'}, text=re.compile('ISBN')).find_next().text.strip()[:10]
            return re.findall('"isbn":"(\d{10})"', str(self.content))[0]
        except (AttributeError, IndexError):
            return None

    def get_book_format(self):
        if self.fully_loaded:
            return self.content.find('span', {'itemprop': 'bookFormat'}).text.strip()
        else:
            return re.findall('"bookFormat":"((.[a-zA-Z\d\s]*))",', str(self.content))[0][0]

    def get_book_pages(self):
        if self.fully_loaded:
            return self.content.find('span', {'itemprop': 'numberOfPages'}).text.strip().split(' ')[0]
        return re.findall('Pages":(\d+),', str(self.content))[0]

    def get_book_edition(self):
        try:
            if self.fully_loaded:
                return self.content.find('span', {'itemprop': 'bookEdition'}).text.strip()
        except (AttributeError, IndexError):
            return None

    def get_book_edition_language(self):
        if self.fully_loaded:
            return self.content.find('div', {'class': 'infoBoxRowItem', 'itemprop':"inLanguage"}).text
        else:
            return re.findall('"Language","name":"((.|\s)*?)"', str(self.content))[0][0]

    def get_book_publish_date(self):
        if self.fully_loaded:
            return re.findall('Published\s*?(.*?)\s*?by\s*?(.*?)\s*?\<', str(self.content))[0][0].strip()
        else:
            ts = int(re.findall('"publicationTime":\s?((.|\s)*?)\s?,', str(self.content))[0][0])/1000
            return datetime.fromtimestamp(ts).strftime('%B %d, %Y')

    def get_book_publisher(self):
        if self.fully_loaded:
            return re.findall('Published\s*?(.*?)\s*?by\s*?(.*?)\s*?\<', str(self.content))[0][1].strip()
        else:
            return re.findall('"publisher":\s?"((.|\s)*?)"', str(self.content))[0][0]

    def get_book_first_publish(self):
        try:
            if self.fully_loaded:
                return re.findall('first published\s*?(.*?)\)', self.content.text.strip())[0].strip()
            return re.findall('First published([a-zA-Z\d\s\,]*)<', str(self.content))[0].strip()
        except (AttributeError, IndexError):
            return None

    def get_book_ratings_avg(self):
        if self.fully_loaded:
            return re.findall('\d.\d+', self.content.find_all('div', {'class': 'reviewControls--left'})[0].text)[0]
        else:
            return re.findall('Average rating of (\d.\d+) stars', str(self.content))[0]

    def get_book_ratings(self):
        if self.fully_loaded:
            ratings = dict()
            rt = re.findall('renderRatingGraph\(\s*?\[(\d+), (\d+), (\d+), (\d+), (\d+)\]', str(self.content))[0]
            for ids, r in enumerate(rt):
                ratings[len(rt)-ids] = int(r)
            return ratings
        else:
            ratings = dict()
            for ids in range(1,6):
                ratings[ids] = re.findall(f'labelTotal-{ids}">((,|\d)*?)\s', str(self.content))[0][0].replace(',', '')
            return ratings

    def get_book_awards(self):
        try:
            if self.fully_loaded:
                awards = self.content.find('div', {'class': 'infoBoxRowTitle'}, text=re.compile('Awards')).find_next().text.strip()
                return awards.replace('...more', ',').replace('...less', '').replace('\n', '').split(', ')
            else:
                return re.findall('"awards":"([^"]*)"', str(self.content))
        except:
            return None

    def get_book_description(self):
        if self.fully_loaded:
            return self.content.find('div', {'id': 'description'}).find('span', {'style': 'display:none'}).text.strip()
        else:
            return self.content.find('div', {'data-testid': 'description'}).text.strip()

    def get_book_series(self):
        try:
            if self.fully_loaded:
                return self.content.find(text=re.compile('Series')).find_next().text.strip().split('#')[0].strip()
            else:
                return re.findall('"Series","title":"([^"]*)"', str(self.content))[0]
        except (AttributeError, IndexError):
            return None

    def get_book_characters(self):
        try:
            if self.fully_loaded:
                characters = self.content.find(text=re.compile('Characters')).find_next().text.strip()
                return characters.replace('...more,', ',').replace('...less', '').split(' ')
            else:
                characters = re.findall('"Character","name":"((.|\s)*?)"', str(self.content))
                characters = [i[0] for i in characters]
                return characters
        except (AttributeError, IndexError):
            return None

    def get_book_settings(self):
        try:
            if self.fully_loaded:
                sets = self.content.find(text=re.compile('Setting')).find_next()
                settings = []
                for item in sets.find_all('a'):
                    if item['href'] == '#':
                        continue
                    place_detail = item.text
                    place_general = None
                    if item.find_next('span'):
                        place_general = item.find_next('span').text.strip().lstrip('(').rstrip(')')
                    if place_general in ('…more', '…less'):
                        place_general = None
                    if place_general:
                        settings.append((place_detail, place_general))
                    else:
                        settings.append((place_detail))
            else:
                settings = re.findall('{"__typename":"Places","name":"([a-zA-Z\,\s]*)","countryName":"([a-zA-Z\,\s]*)"', str(self.content))
            return settings
        except:
            return []

    def get_book_ratings_count(self):
        if self.fully_loaded:
            return self.content.find('meta', {'itemprop': 'ratingCount'})['content'].replace(',', '')
        else:
            return re.findall('((,|\d)+) ratings', str(self.content))[0][0].replace(',', '')

    def get_book_reviews_count(self):
        if self.fully_loaded:
            return self.content.find('meta', {'itemprop': 'reviewCount'})['content'].replace(',', '')
        else:
            return re.findall('((,|\d)+) reviews', str(self.content))[0][0].replace(',', '')

    def get_book_genres(self):
        try:
            if self.fully_loaded:
                genres = []
                for g in self.content.select('a.bookPageGenreLink'):
                    if g.text.strip() not in genres:
                        genres.append(g.text.strip())
            else:
                genres = [g.text for g in self.content.find_all('span', {'class': 'BookPageMetadataSection__genre'})]
            return genres
        except (AttributeError, IndexError):
            return None
            

if __name__ == '__main__':
    scrapper = GoodreadsScrapper()
    # twilight = scrapper.get_book_by_id('16299.And_Then_There_Were_None')
    """
    test book scrapper
    """
    # twilight = scrapper.get_book_by_id('2429135.The_Girl_with_the_Dragon_Tattoo')
    # tb = Book(twilight)
    # det = tb.get_details()
    # print(tb.fully_loaded)

    # for key, value in det.items():
    #     print(key)
    #     print(value)
    #     print('-----')
    """
    test list scrapper
    """
    # bl = scrapper.get_book_list_by_list_id('155086.Popular_Kindle_Notes_Highlights_on_Goodreads')
    # print(bl)
    """
    test user shelf scrapper
    """
    # sh = scrapper.get_shelf_by_user_id('38077205-hannah-azerang')
    # print(sh)
    """
    test user book scrapper
    """
    rl = scrapper.get_book_list_by_user_shelf(user_id='38077205-hannah-azerang', shelf_id='read', number_of_book=50)
    print(rl)
