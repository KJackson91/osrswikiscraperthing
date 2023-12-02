import logging
import argparse
import os

from mediawiki import MediaWiki
from e_log import get_logger
from tqdm import tqdm

BASE_URL = 'https://oldschool.runescape.wiki'
CACHE_DIR = './cache'
PAGES_OUTPUT_FILE = f'{CACHE_DIR}/output.txt'
PAGES_OUTPUT_DIR = f'{CACHE_DIR}/page_texts'
log = get_logger("osrs_wiki_embeddings_gen")
log.setLevel(logging.INFO)

osrs_wiki = MediaWiki(url=f'{BASE_URL}/api.php',
                      user_agent='osrs_wiki_embeddings_gen v1.0 discord:\'kyle.\'')


def write_page(page_name, page_text):
    with open(f'{PAGES_OUTPUT_DIR}/{page_name}.txt', 'w', encoding='UTF-8') as f:
        f.write(page_text)


def read_cache():
    pages = []
    with open(f'{PAGES_OUTPUT_FILE}', 'r', encoding='UTF-8') as f:
        for line in f.readlines():
            pages.append(line.strip())
    return pages

def write_cache(pages):
    log.info(f"Writing {len(pages)} page titles to {PAGES_OUTPUT_FILE}")
    with open(PAGES_OUTPUT_FILE, "w", encoding="utf-8") as file:
        # Iterate over the set and write each element to the file
        for item in pages:
            file.write(item + "\n")
    log.info("DONE")


def generate_cache():
    pages = set()
    start_from = ''
    log.info(f"Fetching wiki pages from {BASE_URL}")

    while True:
        new_pages = [x for x in osrs_wiki.allpages(query=start_from, results=500)]
        start_from = new_pages[-1]
        [pages.add(x) for x in new_pages]
        if len(new_pages) < 500:
            log.info(f"Got less than 500 pages ({len(new_pages)}) - breaking")
            break
        log.info(f"Got 500 pages ({len(new_pages)}) - fetching more")
    return pages


def sanitize_page_name(raw):
    return raw.replace(" ", "_").replace("/", "_").replace("?", "_")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate embeddings from the OSRS wiki.")
    parser.add_argument("--gen-cache", action="store_true", help="Enable cache generation")
    args = parser.parse_args()
    gen_cache = args.gen_cache

    if gen_cache or not os.path.exists(PAGES_OUTPUT_FILE):
        log.info("Generating page cache")
        write_cache(generate_cache())
    else:
        log.debug(f"{gen_cache=} {os.path.exists(PAGES_OUTPUT_FILE)=}")
        log.info("Downloading pages, this will take forever.")

        pages = read_cache()

        for page in tqdm(pages):
            try:
                p = osrs_wiki.page(title=page)
                page_name = sanitize_page_name(page)
                # tqdm.write(f"{page_name=}, {p.wikitext=}")
                write_page(f"wikitext_{page_name}", p.wikitext)
                write_page(f"html_{page_name}", p.html)
            except:
                tqdm.write(f"ERROR fetching page: {page}")
