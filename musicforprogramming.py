from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
from xml.dom.minidom import Document, Element, parse

MUSIC_DIR = 'D:/home/music/musicforprogramming'
RSS_URL = 'https://musicforprogramming.net/rss.xml'
MUSIC_DIR_PATH = Path(MUSIC_DIR)
GENERATE_PLAYLIST = True
PLAYLIST_DIR_PATH = MUSIC_DIR_PATH.parent
HEADERS = {
    'accept': '/*',
    'accept-language': '*',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.57',
}


def find_exist_tracks() -> list[str]:
    return [track.name for track in MUSIC_DIR_PATH.glob("*.mp3")]


def get_track_items(xml: Document) -> list[dict[str, str]]:
    items = xml.getElementsByTagName('item')
    return [parse_xml_item(item) for item in items]


def parse_xml_item(item: Element) -> dict[str, str]:
    ITEM_ELEMENTS = ('title', 'guid')
    parsed_item = {
        element.tagName: element.firstChild.data  # type: ignore
        for element in item.childNodes
        if isinstance(element, Element) and element.tagName in ITEM_ELEMENTS
    }
    return parsed_item | {
        'filename': urlparse(parsed_item['guid'])
        .path[1::]
        .replace('music_for_programming_', '')
    }


def download_track(parsed_item: dict[str, str]):
    print(f"{parsed_item['title']} download", end=" ")

    url = urlparse(parsed_item['guid'])
    safe_unicode_url = f'{url.scheme}://{url.netloc}{quote(url.path)}'
    request = Request(url=safe_unicode_url, headers=HEADERS)
    with open(MUSIC_DIR_PATH / parsed_item['filename'], 'wb') as fs, urlopen(
        request
    ) as response:
        fs.write(response.read())
        print('finished.')


def download_tracks(parsed_track_items: list[dict[str, str]]):
    exist_tracks = find_exist_tracks()
    new_track_items = [
        track_item
        for track_item in parsed_track_items
        if track_item['filename'] not in exist_tracks
    ]

    if not new_track_items:
        print("No new tracks. Bye!")
    else:
        tracks_count = len(new_track_items)
        for index, track in enumerate(new_track_items, start=1):
            print(f"({index}/{tracks_count})", end=" ")
            download_track(track)
        if GENERATE_PLAYLIST:
            generate_playlist()


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
