import json
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
from xml.dom.minidom import Document, Element, parse

MUSIC_DIR = 'D:/home/music/musicforprogramming'
CONTENTS_FILENAME = 'contents.json'
RSS_URL = 'https://musicforprogramming.net/rss.xml'
MUSIC_DIR_PATH = Path(MUSIC_DIR)
PLAYLIST_DIR_PATH = MUSIC_DIR_PATH.parent
HEADERS = {
    'accept': '/*',
    'accept-language': '*',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.57',
}


def read_contents() -> list[dict[str, str]] | list:
    if not MUSIC_DIR_PATH.exists():
        Path.mkdir(MUSIC_DIR_PATH, parents=True)
    try:
        with open(MUSIC_DIR_PATH / CONTENTS_FILENAME, 'r') as fs:
            return json.load(fs)
    except FileNotFoundError:
        with open(MUSIC_DIR_PATH / CONTENTS_FILENAME, 'w') as fs:
            empty_contents = '[]'
            fs.write(empty_contents)
        return json.loads(empty_contents)


def append_contents(parsed_item: dict[str, str]):
    contents = read_contents()
    contents.append(parsed_item)
    with open(MUSIC_DIR_PATH / CONTENTS_FILENAME, 'w') as fs:
        fs.write(json.dumps(contents))


def get_track_items(xml: Document) -> list[dict[str, str]]:
    items = xml.getElementsByTagName('item')
    return [parse_xml_item(item) for item in items]


def parse_xml_item(item: Element) -> dict[str, str]:
    ITEM_ELEMENTS = ('title', 'link', 'pubDate', 'guid')
    return {
        element.tagName: element.firstChild.data  # type: ignore
        for element in item.childNodes
        if isinstance(element, Element) and element.tagName in ITEM_ELEMENTS
    }


def download_track(parsed_item: dict[str, str]):
    filename = (
        urlparse(parsed_item['guid']).path[1::].replace('music_for_programming_', '')
    )
    print(f"{parsed_item['title']} download", end=" ")
    titles = (content['title'] for content in read_contents())
    if parsed_item['title'] in titles:
        print('skipped.')
    else:
        url = urlparse(parsed_item['guid'])
        safe_unicode_url = f'{url.scheme}://{url.netloc}{quote(url.path)}'
        request = Request(url=safe_unicode_url, headers=HEADERS)
        with open(MUSIC_DIR_PATH / filename, 'wb') as fs, urlopen(request) as response:
            fs.write(response.read())
            print('finished.')
        append_contents(parsed_item)


def download_tracks(parsed_track_items: list[dict[str, str]]):
    exist_contents = read_contents()
    new_track_items = [
        track_item
        for track_item in parsed_track_items
        if track_item['title'] not in [content['title'] for content in exist_contents]
    ]
    if not new_track_items:
        print("No new tracks. Bye!")
    else:
        tracks_count = len(new_track_items)
        for index, track in enumerate(new_track_items, start=1):
            print(f"({index}/{tracks_count})", end=" ")
            download_track(track)


def generate_playlist():
    mp3_files_raw_text = '\n'.join(
        [str(mp3_file) for mp3_file in MUSIC_DIR_PATH.glob('*.mp3')]
    )
    with open(
        PLAYLIST_DIR_PATH / 'musicforprogramming.m3u', 'w', encoding='utf-8'
    ) as fs:
        fs.write(mp3_files_raw_text)


xml_source = parse(urlopen(RSS_URL))
tracks = get_track_items(xml_source)
download_tracks(tracks)
generate_playlist()
