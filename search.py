from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
import requests
from bs4 import BeautifulSoup

@dataclass
class Chapter:
    number: str
    url: str
    release_date: str

@dataclass
class MangaType(Enum):
    MANGA = "manga"
    ANIME = "anime"
    UNKNOWN = "unknown"

@dataclass
class Manga:
    title: str
    url: str
    type: MangaType
    description: str = ""
    chapters: List[Chapter] = field(default_factory=list)
    image_url: Optional[str] = None
    raw_chapters: List[List[str]] = field(default_factory=list)

    def with_description(self):
        self.description = MangaSearch.get_description(self)

    def with_chapters(self):
        self.chapters = MangaSearch.get_chapters(self)

    def with_image(self):
        self.image_url = MangaSearch.get_manga_image(self)

    def with_raw_chapters(self):
        self.raw_chapters = MangaSearch.scrape_raw_chapters(self.chapters)

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

    @classmethod
    def _parse_chapter(cls, element):
        chapter_number = element.find('a').text.strip()
        chapter_url = element.find('a')['href']
        release_date = element.find('span', class_='chapter-release-date').text.strip()
        return Chapter(number=chapter_number, url=chapter_url, release_date=release_date)

    @classmethod
    def get_description(cls, manga: Manga):
        response = cls._make_request('get', manga.url)
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            description_element = soup.find('div', class_='description-summary')
            if description_element:
                return description_element.get_text().strip().replace("Show more", "")

    @classmethod
    def get_chapters(cls, manga: Manga) -> List[Chapter]:
        response = cls._make_request('get', manga.url)
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            chapter_elements = soup.find_all('li', class_='wp-manga-chapter')
            chapters = [cls._parse_chapter(element) for element in chapter_elements]
            manga.chapters = chapters
            return chapters
        return []

    @classmethod
    def get_manga_image(cls, manga: Manga):
        response = cls._make_request('get', manga.url)
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            image_element = soup.select_one('div.tab-summary > div.summary_image > a > img')
            if image_element:
                manga.image_url = image_element['src']

    @staticmethod
    def scrape_raw_chapters(chapters: List[Chapter]) -> List[List[str]]:
        all_raw_chapters = []
        for chapter in chapters:
            try:
                response = requests.get(chapter.url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    image_tags = soup.find_all('img', {'class': 'wp-manga-chapter-img'})
                    image_urls = [img['data-src'].strip() for img in image_tags if 'data-src' in img.attrs]
                    all_raw_chapters.append(image_urls)
                else:
                    print(f"Failed to fetch URL: {chapter.url}. Status code: {response.status_code}")
            except requests.RequestException as e:
                print(f"Request Exception: {e}")
        return all_raw_chapters

    @classmethod
    def get_manga_details(cls, query_name: str) -> List[Manga]:
        data = {'action': 'wp-manga-search-manga', 'title': query_name}
        response = cls._make_request('post', cls.BASE_URL, data=data)

        if response and response.status_code == 200:
            manga_list = [
                Manga(
                    title=manga_data['title'],
                    url=manga_data['url'],
                    type=MangaType(manga_data['type'])
                )
                for manga_data in response.json().get('data', [])
            ]

            for manga in manga_list:
                manga.with_description()
                manga.with_chapters()
                manga.with_image()
                manga.with_raw_chapters()

            return manga_list
        return []

