<<<<<<< HEAD
import requests
from bs4 import BeautifulSoup
import sqlite3
import re
import base64
from multiprocessing import Pool, cpu_count
import os
import time


import logging
logging.basicConfig(filename='seedscraper.log', level=logging.ERROR,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)

fexists = False
if os.path.exists('breeder.db'):
    fexists = True

sqlconnection = sqlite3.connect("breeder.db", check_same_thread=False)
sqlcursor = sqlconnection.cursor()

if fexists == False:
    sqlcursor.execute('''CREATE TABLE breederlist
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      breedername TEXT,
                      website TEXT,
                      strainsnum INTEGER)''')

    sqlconnection.commit()

    sqlcursor.execute('''CREATE TABLE strainlist
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      website TEXT,
                      strainname TEXT,
                      breeder TEXT,
                      flowertime TEXT,
                      type TEXT,
                      feminized TEXT,
                      infotext1 TEXT,
                      infotext2 TEXT,
                      effects TEXT,
                      smell TEXT,
                      taste TEXT,
                      lineage TEXT,
                      pictures_base64 TEXT,
                      userrating REAL)''')

    sqlconnection.commit()

maryjane = """
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██▓▓██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░██░░░░░░░░░░░░░░░░░░██▒▒██░░░░░░░░░░░░░░░░░░██░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░████░░░░░░░░░░░░░░░░██▓▓██░░░░░░░░░░░░░░░░████░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░██████░░░░░░░░░░░░████▓▓████░░░░░░░░░░░░██████░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░████████░░░░░░░░░░████▒▒██▓▓░░░░░░░░░░████████░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░██▒▒████░░░░░░░░████▒▒████░░░░░░░░████▒▒██░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░██▓▓▓▓████░░░░░░████▓▓████░░░░░░████▒▒████░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░██████▒▒████░░░░████▓▓████░░░░████▓▓██████░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░████▒▒██████░░████▓▓████░░██████▒▒████░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░██████▒▒████░░████▓▓████░░████▓▓██████░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓████▓▓████░░██▓▓██░░████▒▒██▓▓██░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░██████▒▒████████▓▓████████▒▒██████░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██████▓▓██████▓▓██████▒▒██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░████████████░░░░██████▒▒████▓▓████▓▓██████░░░░████████████░░░░░░░░░░░░░░
░░░░░░░░▒▒░░░░░░░░████▓▓▓▓██████░░██████▓▓██▓▓██▓▓██████░░██████▓▓▓▓████░░░░░░░░░░▒▒░░░░
░░░░░░░░░░░░░░░░░░░░██████▒▒▒▒████████████▒▒  ▒▒████████████▒▒▒▒██████░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░████████▓▓▒▒▓▓▓▓▒▒▒▒      ▒▒▓▓▓▓▒▒▒▒▒▒████████░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░██████████████▒▒  ▒▒██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████▓▓██▒▒██▒▒████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓██▒▒██████████▒▒████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████▓▓████░░██░░████▓▓████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██████████░░░░██░░░░██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
"""

gui_showtext_000 = "Loading breader and strainlist."


def getbrederdb():

    URL = 'https://seedfinder.eu/en/database/breeder'
    website = requests.get(URL)
    results = BeautifulSoup(website.content, 'html.parser')

    breederlist_raw = results.find_all('div', class_='card')
    rawlist0 = []
    rawlist1 = []
    rawlist2 = []
    rawlist3 = []

    for breeder in breederlist_raw:
        raw0 = breeder.find_all('ul', class_='list-disc list-inside')
        rawlist0.append(raw0)

    for pa in rawlist0:
        if pa != None:
            rawlist1.append(pa)

    for pa in rawlist1:
        soup_string = str(pa)
        br_tags = soup_string.split('<li>')
        for s in br_tags:
            rawlist2.append(s)

    for pa in rawlist2:
        ext_href_raw0 = pa.split('<a class="link" href="')
        for ch in ext_href_raw0:
            if len(ch) > 10:
                ext_href_raw1 = ch.split('</a>')
                rawlist3.append(ext_href_raw1[0])

    dataset = []
    for sbree in rawlist3:
        http_con_raw = sbree.split('">')
        http_con = http_con_raw[0]

        name_raw = http_con_raw[1].split('\n')
        name = name_raw[0]

        num_raw = name_raw[1]
        numbers = re.findall(r'\d+', num_raw)
        strainumber = -1
        if numbers:
            strainumber = int(numbers[0])

        if len(name) > 1:
            sqlcursor.execute("INSERT INTO breederlist (breedername, website, strainsnum) VALUES (?, ?, ?)", (name, http_con, strainumber))
            sqlconnection.commit()
            print("loading strainbase from: ", name)
            dataset.append(http_con)

    return dataset




def loadbreederstrains(URL):
    try:
        out = []
        website = requests.get(URL)
        soup = BeautifulSoup(website.content, 'html.parser')

        table = soup.find('table', class_='table')
        rows = table.find('tbody').find_all('tr')

        for row in rows:
            cells = row.find_all('td')

            link = cells[0].find('a')['href']
            name = cells[0].find('a').text.strip()
            breeder = cells[1].text.strip()
            flowertime = cells[2].text.strip()
            type = cells[3].text.strip()
            feminized = cells[4].text.strip()

            extradata = loadsinglestrain(link)

            sqlvalues = (link, name, breeder, flowertime, type, feminized, extradata['infotext1'], extradata['infotext2'], extradata['effects'], extradata['smells'], extradata['tastes'], extradata['lineage'], extradata['base64_images'], extradata['usrrating'])
            out.append(sqlvalues)
            #print("loading: " ,name)

        return out
    except Exception as e:
        print(f"Error processing URL {URL}: {e}")
        logger.error(URL)
        logger.error(e)
        return []



def parse_tree(element, depth=0):
    tree = ""
    if element.name == "a":
        text = element.get_text(strip=True)
        href = element.get("href", "#")
        tree += "    " * depth + f"- {text} ##$##  {href}\n"

    for child in element.find_all("li", recursive=False):
        link = child.find("a")
        if link:
            tree += parse_tree(link, depth + 2)

        nested_ul = child.find("ul")
        if nested_ul:
            tree += parse_tree(nested_ul, depth + 2)

    return tree

def extract_zoomist_container(soup):
    zoomist_container = soup.find("div", class_="zoomist-container")

    if not zoomist_container:
        return "Kein <div class=\"zoomist-container\"> gefunden."

    root = zoomist_container.find("ul")

    if not root:
        return "Kein Stammbaum gefunden."

    tree_structure = parse_tree(root)
    return tree_structure

def extract_values_by_text(header_text, soup):
    header = soup.find('h4', string=header_text)
    if header:
        values = [div.get_text(strip=True) for div in header.find_next('div').find_all('div', class_='bg-primary-500')]
        return values
    return []

def loadsinglestrain(URL):
    retdict = {}
    website = requests.get(URL)
    soup = BeautifulSoup(website.content, 'html.parser')
    retdict['website'] = URL

    list_raw = soup.find_all('div', class_='card')
    title = soup.find('h1').text.strip() if soup.find('h1') else 'N/A'
    headers = soup.find_all('h2')

    results = []
    for header in headers:
        next_p = header.find_next('p')
        if next_p:
            results.append({"header": header.get_text(strip=True), "text": next_p.get_text(strip=True)})


    text1_raw = results[0]
    text1_header = str(text1_raw["header"])
    text1_text = str(text1_raw["text"])
    text1_together = str(text1_header + " /n /n" + text1_text)

    text2_raw = results[1]
    text2_header = str(text2_raw["header"])
    text2_text = str(text2_raw["text"])
    text2_together = str(text2_header + " /n /n" + text2_text)

    retdict['infotext1'] = text1_together
    retdict['infotext2'] = text2_together



    effects = extract_values_by_text('Effect/Effectiveness', soup)
    smells = extract_values_by_text('Smell / Aroma', soup)
    tastes = extract_values_by_text('Taste', soup)

    retdict['effects'] = ','.join(effects)
    retdict['smells'] = ','.join(smells)
    retdict['tastes'] = ','.join(tastes)



    tree = extract_zoomist_container(soup)
    retdict['lineage'] = ''.join(tree)

    #get images
    loadimages = False
    if loadimages == True:
        img_tags = soup.find_all("img")
        dl_content = []
        for img in img_tags:
            img_url = img.get("src")
            if 'https://cdn.seedfinder.eu/pics/galerie/' in str(img_url):
                dl_content.append(img_url)

        dl_content = list(set(dl_content))
        images_base64 = []
        for im in dl_content:
            baseimage = base64.b64encode(requests.get(im).content)
            images_base64.append(baseimage)
        retdict['base64_images'] = ' ; '.join(images_base64)
    else:
        retdict['base64_images'] = "N/A"

    target_header = "User rating"
    h5 = soup.find('h5', string=target_header)
    retdict['usrrating'] = float(-1)
    if h5:
        next_p = h5.find_next_sibling('p')  # Sucht den nächsten <p>-Tag
        if next_p:
            newtxt = next_p.text
            rawtxt0 = newtxt.split('gets ')
            rawtxt1 = rawtxt0[1].split(' of ')

            retdict['usrrating'] = float(rawtxt1[0])

    return retdict

def save_to_db(data):
    try:
        sqlcursor.executemany("""
            INSERT INTO strainlist (website, strainname, breeder, flowertime, type, feminized, infotext1, infotext2, effects, smell, taste, lineage, pictures_base64, userrating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        sqlconnection.commit()
    except Exception as e:
        print(f"Error saving to database: {e}")


def process_url_async(url):
    data = loadbreederstrains(url)
    save_to_db(data)

if __name__ == "__main__":
    newdataset = getbrederdb()
    start = time.time()
    os.system('cls' if os.name == 'nt' else 'clear')
    print(maryjane)

    with Pool(processes=30) as pool:
        results = [pool.apply_async(process_url_async, (url,)) for url in newdataset]

        for result in results:
            result.wait()

    print("db generated in seconds:")
    end = time.time()
=======
import requests
from bs4 import BeautifulSoup
import sqlite3
import re
import base64
from multiprocessing import Pool, cpu_count
import os
import time


import logging
logging.basicConfig(filename='seedscraper.log', level=logging.ERROR,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)

fexists = False
if os.path.exists('breeder.db'):
    fexists = True

sqlconnection = sqlite3.connect("breeder.db", check_same_thread=False)
sqlcursor = sqlconnection.cursor()

if fexists == False:
    sqlcursor.execute('''CREATE TABLE breederlist
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      breedername TEXT,
                      website TEXT,
                      strainsnum INTEGER)''')

    sqlconnection.commit()

    sqlcursor.execute('''CREATE TABLE strainlist
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      website TEXT,
                      strainname TEXT,
                      breeder TEXT,
                      flowertime TEXT,
                      sorte TEXT,
                      feminized TEXT,
                      infotext1 TEXT,
                      infotext2 TEXT,
                      effects TEXT,
                      smell TEXT,
                      taste TEXT,
                      lineage TEXT,
                      pictures_base64 TEXT,
                      userrating REAL)''')

    sqlconnection.commit()

maryjane = """
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██▓▓██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░██░░░░░░░░░░░░░░░░░░██▒▒██░░░░░░░░░░░░░░░░░░██░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░████░░░░░░░░░░░░░░░░██▓▓██░░░░░░░░░░░░░░░░████░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░██████░░░░░░░░░░░░████▓▓████░░░░░░░░░░░░██████░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░████████░░░░░░░░░░████▒▒██▓▓░░░░░░░░░░████████░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░██▒▒████░░░░░░░░████▒▒████░░░░░░░░████▒▒██░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░██▓▓▓▓████░░░░░░████▓▓████░░░░░░████▒▒████░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░██████▒▒████░░░░████▓▓████░░░░████▓▓██████░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░████▒▒██████░░████▓▓████░░██████▒▒████░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░██████▒▒████░░████▓▓████░░████▓▓██████░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓████▓▓████░░██▓▓██░░████▒▒██▓▓██░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░██████▒▒████████▓▓████████▒▒██████░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██████▓▓██████▓▓██████▒▒██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░████████████░░░░██████▒▒████▓▓████▓▓██████░░░░████████████░░░░░░░░░░░░░░
░░░░░░░░▒▒░░░░░░░░████▓▓▓▓██████░░██████▓▓██▓▓██▓▓██████░░██████▓▓▓▓████░░░░░░░░░░▒▒░░░░
░░░░░░░░░░░░░░░░░░░░██████▒▒▒▒████████████▒▒  ▒▒████████████▒▒▒▒██████░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░████████▓▓▒▒▓▓▓▓▒▒▒▒      ▒▒▓▓▓▓▒▒▒▒▒▒████████░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░██████████████▒▒  ▒▒██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████▓▓██▒▒██▒▒████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓██▒▒██████████▒▒████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████▓▓████░░██░░████▓▓████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██████████░░░░██░░░░██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
"""

gui_showtext_000 = "Loading breader and strainlist."


def getbrederdb():

    URL = 'https://seedfinder.eu/en/database/breeder'
    website = requests.get(URL)
    results = BeautifulSoup(website.content, 'html.parser')

    breederlist_raw = results.find_all('div', class_='card')
    rawlist0 = []
    rawlist1 = []
    rawlist2 = []
    rawlist3 = []

    for breeder in breederlist_raw:
        raw0 = breeder.find_all('ul', class_='list-disc list-inside')
        rawlist0.append(raw0)

    for pa in rawlist0:
        if pa != None:
            rawlist1.append(pa)

    for pa in rawlist1:
        soup_string = str(pa)
        br_tags = soup_string.split('<li>')
        for s in br_tags:
            rawlist2.append(s)

    for pa in rawlist2:
        ext_href_raw0 = pa.split('<a class="link" href="')
        for ch in ext_href_raw0:
            if len(ch) > 10:
                ext_href_raw1 = ch.split('</a>')
                rawlist3.append(ext_href_raw1[0])

    dataset = []
    for sbree in rawlist3:
        http_con_raw = sbree.split('">')
        http_con = http_con_raw[0]

        name_raw = http_con_raw[1].split('\n')
        name = name_raw[0]

        num_raw = name_raw[1]
        numbers = re.findall(r'\d+', num_raw)
        strainumber = -1
        if numbers:
            strainumber = int(numbers[0])

        if len(name) > 1:
            sqlcursor.execute("INSERT INTO breederlist (breedername, website, strainsnum) VALUES (?, ?, ?)", (name, http_con, strainumber))
            sqlconnection.commit()
            print("loading strainbase from: ", name)
            dataset.append(http_con)

    return dataset




def loadbreederstrains(URL):
    try:
        out = []
        website = requests.get(URL)
        soup = BeautifulSoup(website.content, 'html.parser')

        table = soup.find('table', class_='table')
        rows = table.find('tbody').find_all('tr')

        for row in rows:
            cells = row.find_all('td')

            link = cells[0].find('a')['href']
            name = cells[0].find('a').text.strip()
            breeder = cells[1].text.strip()
            flowertime = cells[2].text.strip()
            sorte = cells[3].text.strip()
            feminized = cells[4].text.strip()

            extradata = loadsinglestrain(link)

            sqlvalues = (link, name, breeder, flowertime, sorte, feminized, extradata['infotext1'], extradata['infotext2'], extradata['effects'], extradata['smells'], extradata['tastes'], extradata['lineage'], extradata['base64_images'], extradata['usrrating'])
            out.append(sqlvalues)
            #print("loading: " ,name)

        return out
    except Exception as e:
        print(f"Error processing URL {URL}: {e}")
        logger.error(URL)
        logger.error(e)
        return []



def parse_tree(element, depth=0):
    tree = ""
    if element.name == "a":
        text = element.get_text(strip=True)
        href = element.get("href", "#")
        tree += "    " * depth + f"- {text} ##$##  {href}\n"

    for child in element.find_all("li", recursive=False):
        link = child.find("a")
        if link:
            tree += parse_tree(link, depth + 2)

        nested_ul = child.find("ul")
        if nested_ul:
            tree += parse_tree(nested_ul, depth + 2)

    return tree

def extract_zoomist_container(soup):
    zoomist_container = soup.find("div", class_="zoomist-container")

    if not zoomist_container:
        return "Kein <div class=\"zoomist-container\"> gefunden."

    root = zoomist_container.find("ul")

    if not root:
        return "Kein Stammbaum gefunden."

    tree_structure = parse_tree(root)
    return tree_structure

def extract_values_by_text(header_text, soup):
    header = soup.find('h4', string=header_text)
    if header:
        values = [div.get_text(strip=True) for div in header.find_next('div').find_all('div', class_='bg-primary-500')]
        return values
    return []

def loadsinglestrain(URL):
    retdict = {}
    website = requests.get(URL)
    soup = BeautifulSoup(website.content, 'html.parser')
    retdict['website'] = URL

    list_raw = soup.find_all('div', class_='card')
    title = soup.find('h1').text.strip() if soup.find('h1') else 'N/A'
    headers = soup.find_all('h2')

    results = []
    for header in headers:
        next_p = header.find_next('p')
        if next_p:
            results.append({"header": header.get_text(strip=True), "text": next_p.get_text(strip=True)})


    text1_raw = results[0]
    text1_header = str(text1_raw["header"])
    text1_text = str(text1_raw["text"])
    text1_together = str(text1_header + " /n /n" + text1_text)

    text2_raw = results[1]
    text2_header = str(text2_raw["header"])
    text2_text = str(text2_raw["text"])
    text2_together = str(text2_header + " /n /n" + text2_text)

    retdict['infotext1'] = text1_together
    retdict['infotext2'] = text2_together



    effects = extract_values_by_text('Effect/Effectiveness', soup)
    smells = extract_values_by_text('Smell / Aroma', soup)
    tastes = extract_values_by_text('Taste', soup)

    retdict['effects'] = ','.join(effects)
    retdict['smells'] = ','.join(smells)
    retdict['tastes'] = ','.join(tastes)



    tree = extract_zoomist_container(soup)
    retdict['lineage'] = ''.join(tree)

    #get images
    loadimages = False
    if loadimages == True:
        img_tags = soup.find_all("img")
        dl_content = []
        for img in img_tags:
            img_url = img.get("src")
            if 'https://cdn.seedfinder.eu/pics/galerie/' in str(img_url):
                dl_content.append(img_url)

        dl_content = list(set(dl_content))
        images_base64 = []
        for im in dl_content:
            baseimage = base64.b64encode(requests.get(im).content)
            images_base64.append(baseimage)
        retdict['base64_images'] = ' ; '.join(images_base64)
    else:
        retdict['base64_images'] = "N/A"

    target_header = "User rating"
    h5 = soup.find('h5', string=target_header)
    retdict['usrrating'] = float(-1)
    if h5:
        next_p = h5.find_next_sibling('p')  # Sucht den nächsten <p>-Tag
        if next_p:
            newtxt = next_p.text
            rawtxt0 = newtxt.split('gets ')
            rawtxt1 = rawtxt0[1].split(' of ')

            retdict['usrrating'] = float(rawtxt1[0])

    return retdict

def save_to_db(data):
    try:
        sqlcursor.executemany("""
            INSERT INTO strainlist (website, strainname, breeder, flowertime, sorte, feminized, infotext1, infotext2, effects, smell, taste, lineage, pictures_base64, userrating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        sqlconnection.commit()
    except Exception as e:
        print(f"Error saving to database: {e}")


def process_url_async(url):
    data = loadbreederstrains(url)
    save_to_db(data)

if __name__ == "__main__":
    newdataset = getbrederdb()
    start = time.time()
    os.system('cls' if os.name == 'nt' else 'clear')
    print(maryjane)

    with Pool(processes=30) as pool:
        results = [pool.apply_async(process_url_async, (url,)) for url in newdataset]

        for result in results:
            result.wait()

    print("db generated in seconds:")
    end = time.time()
>>>>>>> 20ef10369a6658372551f99584af4cec6c5ced1f
    print(end - start)