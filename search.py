import requests
from dataclasses import dataclass
from typing import List
from enum import Enum
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from bs4 import BeautifulSoup

@dataclass
class Manga:
    title: str
    url: str
    type: str
    description: str = ""
    chapters: List['Chapter'] = None 

@dataclass
class Chapter:
    number: str
    url: str
    release_date: str

class MangaType(Enum):
    MANGA = "manga"
    ANIME = "anime"
    UNKNOWN = "unknown"

class MangaSearch:
    BASE_URL = 'https://manhuaus.com/wp-admin/admin-ajax.php'
    HEADERS = {
        'authority': 'manhuaus.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://manhuaus.com',
        'referer': 'https://manhuaus.com/manhuaus/',
        'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Chrome OS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    @classmethod
    def _make_request(cls, method: str, url: str, data=None):
        try:
            response = requests.request(method, url, headers=cls.HEADERS, data=data)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
            return None

    @staticmethod
    def _parse_chapter(element):
        chapter_number = element.find('a').text.strip()
        chapter_url = element.find('a')['href']
        release_date = element.find('span', class_='chapter-release-date').text.strip()
        return Chapter(number=chapter_number, url=chapter_url, release_date=release_date)

    @classmethod
    def search_manga(cls, query_name: str) -> List[Manga]:
        data = {
            'action': 'wp-manga-search-manga',
            'title': query_name,
        }
        response = cls._make_request('post', cls.BASE_URL, data=data)
        return [
            Manga(title=manga['title'], url=manga['url'], type=MangaType(manga['type']))
            for manga in response.json().get('data', []) if response.status_code == 200
        ]

    @classmethod
    def get_description(cls, manga: Manga):
        response = cls._make_request('get', manga.url)
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            description_element = soup.find('div', class_='description-summary')
            if description_element:
                manga.description = description_element.get_text().strip().replace("Show more", "")

    @classmethod
    def get_chapters(cls, manga: Manga):
        response = cls._make_request('get', manga.url)
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            chapter_elements = soup.find_all('li', class_='wp-manga-chapter')
            manga.chapters = [cls._parse_chapter(element) for element in chapter_elements]

    @classmethod
    def cosine_similarity_search(cls, query: str, results: List[Manga]) -> List[Manga]:
        vectorizer = CountVectorizer().fit_transform([query] + [result.title for result in results])
        cosine_similarities = cosine_similarity(vectorizer)
        query_index = 0
        similarity_scores = cosine_similarities[query_index][1:]
        sorted_indices = similarity_scores.argsort()[::-1]
        sorted_results = [results[i] for i in sorted_indices]
        return sorted_results

query_name = "to hell with being a"
search_results = MangaSearch.search_manga(query_name)

if search_results:
    print("Search Results:")
    for result in search_results:
        print(f"{result.title} - {result.url} ({result.type})")
