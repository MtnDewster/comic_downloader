from concurrent.futures import thread
import os, requests, bs4, re, threading, time

path = r'.\comics\exocomics'
os.makedirs(path, exist_ok=True) # store comics in ./lbc
forbidden_chars = ['<','>',':','"','/','\\','|','?','*']
exo_lock = threading.Lock()
pages_downloaded = 0
page_errors = 0
comic_error = []
stop_threads = False

def DownloadComics(start_comic, end_comic):
    global pages_downloaded, page_errors
    for url_number in range(start_comic, end_comic + 1):
        if stop_threads == True:
            return

        if url_number <= 9:
            url_number = '0' + str(url_number)

        if os.path.exists(os.path.join(path, f'({str(url_number)}).jpg')):
            exo_lock.acquire()
            pages_downloaded += 1
            exo_lock.release()
            continue

        try:
            res = requests.get(f'https://www.exocomics.com/{str(url_number)}')
            res.raise_for_status()
        except requests.HTTPError:
            exo_lock.acquire()
            page_errors += 1
            comic_error.append(str(url_number))
            exo_lock.release()
            continue

        soup = bs4.BeautifulSoup(res.text, features='html.parser')

        main_elem = soup.select_one('img', class_='image-style-main-comic')
        src = 'https://www.exocomics.com' + main_elem.get('src')
        title = f'({str(url_number)}){os.path.splitext(src)[1]}'

        for invalid_char in forbidden_chars:
            title = title.replace(invalid_char, '')
        if os.path.exists(os.path.join(path, title)):
            exo_lock.acquire()
            pages_downloaded += 1
            exo_lock.release()
            continue

        try:
            res = requests.get(src)
            res.raise_for_status()
        except:
            exo_lock.acquire()
            page_errors += 1
            exo_lock.release()
            continue

        image_file = open(os.path.join(path, title), 'wb')
        for chunk in res.iter_content(100000):
            image_file.write(chunk)
        image_file.close()
        exo_lock.acquire()
        pages_downloaded += 1
        exo_lock.release()
        time.sleep(2)

def ECMaxPage():
    res = requests.get('https://www.exocomics.com/')
    soup = bs4.BeautifulSoup(res.text, features="html.parser")
    max_pages = soup.select_one('div', class_='buttons').find('a', class_='prev').get('href')
    max_pages = str(int(re.search('\d+', max_pages).group()) + 1)
    return int(max_pages)

downloadThreads = []
def StartExo():
    max_pages = ECMaxPage()
    for i in range(1, max_pages, 50):
        if i + 50 > max_pages:
            downloadThread = threading.Thread(target=DownloadComics, args=(i, max_pages))
        else:
            downloadThread = threading.Thread(target=DownloadComics, args=(i, i+49))
        downloadThreads.append(downloadThread)
        downloadThread.start()
    
    for downloadThread in downloadThreads:
        downloadThread.join()