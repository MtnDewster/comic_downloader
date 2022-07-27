#! C:\Users\Drew\Desktop\Python\.venv\Scripts\python
# lbcDownloader.py - Downloads every comic from litterboxcomics.com

import os, requests, bs4, re, threading

path = r'.\comics\lbc'
os.makedirs(path, exist_ok=True)  # store comics in ./lbc
months = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December',
]
lbc_lock = threading.Lock()
pages_downloaded = 0
stop_threads = False


def formatDate(date):
    dateRegex = re.compile(r'(0?[1-9]|[1][0-2])\s(0?[1-9]|[12][0-9]|3[01]),\s([0-9]+)')
    for i, month in enumerate(months, 1):
        date = date.replace(month, str(i))
    mo = dateRegex.search(date)
    date = f'{mo[3]}-{mo[1]}-{mo[2]}'
    return date


def downloadComic(date, url):
    fileName = os.path.basename(url).split('.')[0].replace('-', ' ').title()
    fileName = re.sub(r'\s\d', '', fileName)
    fileName = re.sub(r'\sBonus', ' (Bonus)', fileName)
    fileExt = os.path.basename(url).split('.')[1]

    imageName = f'{date}. {fileName}.{fileExt}'
    if os.path.exists(os.path.join(path, imageName)):
        return
    res = requests.get(url)
    res.raise_for_status()
    imageFile = open(os.path.join(path, imageName), 'wb')
    for chunk in res.iter_content(100000):
        imageFile.write(chunk)
    imageFile.close()
    return


def prepBonusComic(bonus_date, bonus_url):
    res = requests.get(bonus_url)
    res.raise_for_status()

    soup = bs4.BeautifulSoup(res.text, features="html.parser")
    bonusComicUrl = soup.find('div', class_='fl-post-content').find('img', src=True).get('src').split('?')[0]
    downloadComic(bonus_date, bonusComicUrl)


def Grabber(url_num):
    global pages_downloaded
    if stop_threads == True:
        return

    url = f'https://www.litterboxcomics.com/page/{url_num}'
    res = requests.get(url)
    res.raise_for_status()

    soup = bs4.BeautifulSoup(res.text, features="html.parser")

    # Find the URL of the comic image.
    comicElem = soup.find_all('div', class_='fl-post-feed-text')
    if comicElem == []:
        return
    else:
        for i in range(len(comicElem)):
            if comicElem[i].find_all('div', class_='wp-block-image') != []:
                comic_date = formatDate(comicElem[i].find('span').get_text().strip())
                if comic_date == '2021-10-11':
                    continue

                comic_urls = comicElem[i].find_all('img', src=True)
                for i in range(len(comic_urls)):
                    comic_url = comic_urls[i].get('src').split('?')[0]
                    downloadComic(comic_date, comic_url)
            else:
                try:
                    comic_url = comicElem[i].find('img', src=True).get('src').split('?')[0]
                except AttributeError:
                    continue
                comic_date = formatDate(comicElem[i].find('span').get_text().strip())
                if comic_date == '2021-4-30':
                    continue
                downloadComic(comic_date, comic_url)
                try:
                    if (comicElem[i].find('h3').find('a', href=True).get_text().find('Click here for BONUS PANEL!') != -1):
                        bonus_comic_url = comicElem[i].find('h3').find('a', href=True).get('href')
                        prepBonusComic(comic_date, bonus_comic_url)
                except AttributeError:
                    continue
    lbc_lock.acquire()
    pages_downloaded += 1
    lbc_lock.release()


def LBCMaxPage():
    max_pages = 17
    while True:
        res = requests.get(f'https://www.litterboxcomics.com/page/{max_pages}')
        res.raise_for_status()

        soup = bs4.BeautifulSoup(res.text, features="html.parser")

        try:
            max_pages = int(soup.select_one('span.page-numbers.current').get_text()) + 1
        except AttributeError:
            break
    return int(max_pages - 1)


downloadThreads = []


def StartLBC(max_pages):
    for i in range(1, int(max_pages) + 1):
        downloadThread = threading.Thread(target=Grabber, args=[i])
        downloadThreads.append(downloadThread)
        downloadThread.start()

    for downloadThread in downloadThreads:
        downloadThread.join()
