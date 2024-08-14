import requests
import time
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def hoopla_search(query_title, query_author=None):
    driver = setup_driver()
    search_query = quote_plus(query_title)
    url = f"https://www.hoopladigital.com/search?q={search_query}&type=direct&kindId=8"
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h3.text-md.font-semibold.leading-tight.line-clamp-2"))
        )
    except:
        print("HOOPLA - Timeout waiting for search results")
        driver.quit()
        return

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    title_elements = soup.select('h3.text-md.font-semibold.leading-tight.line-clamp-2')
    author_elements = soup.select('p.m-0.text-sm.leading-tight.line-clamp-1')

    found = False
    for title_element, author_element in zip(title_elements, author_elements):
        title = title_element.text.strip()
        author = author_element.text.strip()
        link = title_element.find_parent('a')['href']
        full_link = f"https://www.hoopladigital.com{link}"

        if query_author:
            if query_title.lower() in title.lower() and author.lower() == query_author.lower():
                print(f"HOOPLA - {title} by {author} found! Link: {full_link}")
                found = True
                break
        else:
            if query_title.lower() in title.lower():
                print(f"HOOPLA - {title} found! Link: {full_link}")
                found = True
                break

    if not found:
        print(f"HOOPLA - Not found :(")

    driver.quit()

def zero_search(query_title, query_author=None):
    driver = setup_driver()
    search_query = quote_plus(query_title)
    url = f"https://zero-avenue.com/search?searchcategory=&searchkeyword={search_query}"
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h2.woocommerce-loop-product__title, h2.text-center.mb-4.mt-0"))
        )
    except:
        print("ZERO - Timeout waiting for search results")
        driver.quit()
        return

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    title_elements = soup.find_all('h2', class_='woocommerce-loop-product__title product__title h6 text-lh-md mb-1 text-height-2 crop-text-2 h-dark')
    author_elements = soup.select('div.font-size-2.mb-1.text-truncate')

    found = False
    for title_element, author_element in zip(title_elements, author_elements):
        title = title_element.text.strip()
        author = author_element.text.strip()  # Assuming this selector gets the author's name
        link = title_element.find('a')['href']

        if query_author:
            if query_title.lower() in title.lower() and query_author.lower() in author.lower():
                print(f"ZERO - {title} by {author} found! Link: {link}")
                found = True
                break
        else:
            if query_title.lower() in title.lower():
                print(f"ZERO - {title} found! Link: {link}")
                found = True
                break

    if not found:
        print(f"ZERO - Not found :(")

    driver.quit()

def libby_search(query_title, query_author=None):
    driver = setup_driver()
    
    libraries = [
        "https://libbyapp.com/search/lacountylibrary/search/query-{}/page-1",
        "https://libbyapp.com/search/uwisconsin/search/audiobooks/query-{}/page-1",
        "https://libbyapp.com/search/rbpl/search/query-{}/page-1"
    ]
    
    for library_url in libraries:
        library_name = library_url.split('/search')[1].split('/')[-1]
        search_query = quote_plus(query_title)
        url = library_url.format(search_query)
        print(f"Searching {library_name}...")
        driver.get(url)
        
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.title-tile-title"))
            )
        except Exception:
            print(f"LIBBY - Not found in {library_name}")
            continue
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        title_elements = soup.select('span.title-tile-title')
        author_elements = soup.select('div.title-tile-author a')
        status_elements = soup.select('div.title-status, button.title-tile-status')
        
        found = False
        for title_element, author_element, status_element in zip(title_elements, author_elements, status_elements):
            title = title_element.text.strip()
            author = author_element.text.strip()
            link = title_element.find_parent('a')['href']
            full_link = f"https://libbyapp.com{link}"

            status = "Unknown"
            if status_element.name == 'div' and 'title-status' in status_element.get('class', []):
                if 'data-icon_wait-list' in status_element.attrs:
                    aria_label = status_element.get('aria-label', '')
                    status = f"Waitlisted {aria_label.split(',')[-1].strip()}" if aria_label.startswith("Title Status: Wait list") else "Wait List"
                elif 'data-icon_notify' in status_element.attrs:
                    status = "Notify Me"
                elif 'data-icon_available' in status_element.attrs:
                    status = "Available"
            
            if query_author:
                if query_title.lower() in title.lower() and query_author.lower() in author.lower():
                    print(f"LIBBY - {title} by {author} found in {library_name}! Status: {status} Link: {full_link}")
                    found = True
                    break
            else:
                if query_title.lower() in title.lower():
                    print(f"LIBBY - {title} found in {library_name}! Status: {status} Link: {full_link}")
                    found = True
                    break
        
        if not found:
            print(f"LIBBY - Not found in {library_name}")
    
    driver.quit()

def search_all(query_title, query_author=None):
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(hoopla_search, query_title, query_author),
            executor.submit(zero_search, query_title, query_author),
            executor.submit(libby_search, query_title, query_author)
        ]
        concurrent.futures.wait(futures)
