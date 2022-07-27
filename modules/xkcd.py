import requests, os, bs4, threading, time, re
path = r'.\comics\xkcd'
os.makedirs(path, exist_ok=True)

xkcd_lock = threading.Lock()
pages_downloaded = 0
page_errors = 0
comic_error = []
stop_threads = False

def DownloadXKCD(start_comic, end_comic):
    global pages_downloaded, page_errors
    for url_number in range(start_comic, end_comic + 1):
        if stop_threads == True:
            break
        try:
            res = requests.get(f'http://xkcd.com/{str(url_number)}')
            res.raise_for_status()
        except:
            xkcd_lock.acquire()
            page_errors += 1
            comic_error.append(str(url_number))
            xkcd_lock.release()
            continue

        soup = bs4.BeautifulSoup(res.text, features='html.parser')

        comic_elem = soup.select('#comic img')
        if comic_elem == []:
            xkcd_lock.acquire()
            page_errors += 1
            comic_error.append(str(url_number))
            xkcd_lock.release()
        
        else:
            comic_url = 'https:' + comic_elem[0].get('src')
            image_name = f'({url_number}). {os.path.basename(comic_url)}'
            if os.path.exists(os.path.join(path, image_name)):
                xkcd_lock.acquire()
                pages_downloaded += 1
                xkcd_lock.release()
                continue

            try:
                res = requests.get(comic_url)
                res.raise_for_status()
            except:
                xkcd_lock.acquire()
                page_errors += 1
                comic_error.append(str(url_number))
                xkcd_lock.release()
                continue
        
            image_file = open(os.path.join(path, image_name), 'wb')
            for chunk in res.iter_content(100000):
                image_file.write(chunk)
            image_file.close()
            xkcd_lock.acquire()
            pages_downloaded += 1
            xkcd_lock.release()
            time.sleep(2)

def XKCDMaxPage():
    res = requests.get('https://xkcd.com/')
    soup = bs4.BeautifulSoup(res.text, features="html.parser")
    max_pages = soup.select('a[rel="prev"]')[0].get('href')
    max_pages = str(int(re.search('\d+', max_pages).group()) + 1)
    return int(max_pages)

downloadThreads = []
def StartXKCD():
    max_pages = XKCDMaxPage()
    for i in range(1, max_pages, 300):
        if i + 300 > max_pages:
            downloadThread = threading.Thread(target=DownloadXKCD, args=(i, max_pages))
        else:
            downloadThread = threading.Thread(target=DownloadXKCD, args=(i, i + 299))
        downloadThreads.append(downloadThread)
        downloadThread.start()

    for downloadThread in downloadThreads:
        downloadThread.join()