import json
from datetime import datetime
from bs4 import BeautifulSoup
import html
import requests
import mysql.connector

from constance import constances

BASE_URL = "https://chiasenhac.vn"
# PATH =["/nhac-hot/vietnam.html","/nhac-hot/us-uk.html","/nhac-hot/chinese.html","/nhac-hot/korea.html",
#        "/nhac-hot/japan.html","/nhac-hot/france.html","/nhac-hot/other.html"]
# COUNTRY =["VN","US-UK","CN","KR","JP","FR","OTHER"]
PATH =["/nhac-hot/vietnam.html","/nhac-hot/us-uk.html","/nhac-hot/chinese.html","/nhac-hot/korea.html"]
COUNTRY =["VN","US-UK","CN","KR"]
def crawMusic(url):
    data = []
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.content, "html.parser")
        soup = html.unescape(soup)
        name = soup.find('h2', class_='card-title')
        card_detail = soup.find('div', class_='card card-details')
        image = card_detail.find('img').attrs['src']
        link_mp3 = soup.find('a', class_='download_item').attrs["href"]
        card_detail = card_detail.findAll('li')
        singer = ""
        composer = ""
        album = ""
        release_year = ""
        for index in card_detail:
            if index.text.find("Ca sĩ:") != -1:
                singer = index.text.replace("Ca sĩ: ","")
            if index.text.find("Sáng tác:") != -1:
                composer = index.text.replace("Sáng tác: ","")
            if index.text.find("Album:") != -1:
                album = index.text.replace("Album: ","")
            if index.text.find("Năm phát hành:") != -1:
                release_year = index.text.replace("Năm phát hành: ","")
        data.append({
            "name": name.text,
            "link": link_mp3,
            "image": image,
            "singer": singer,
            "composer": composer,
            "album": album,
            "release_year": release_year,
            "link_playlist": url
        })
    except:
        return []
    return data

def createPlayList(path):
    data = []
    for index in range(1,21):
        url=BASE_URL+path+"?playlist={}".format(index)
        try:
            data.append(crawMusic(url))
        except:
            continue
    return data

def crawAndSaveDB():
    deleteDB()
    try:
        db = mysql.connector.connect(user=constances.USERNAME, password=constances.PASSWORD, host=constances.HOST, database=constances.DATABASE)
        cursor = db.cursor()
    except:
        return 0
    number_saved = 0
    for index in range(0,4):
        dataPlayList = createPlayList(PATH[index])
        print("crawled playlist: ",PATH[index] )
        for data in dataPlayList:
            for index2, obj in enumerate(data):
                name = obj["name"].replace('\"',"\'")
                country = COUNTRY[index]
                link = obj["link"]
                image = obj["image"]
                singer = obj["singer"].replace('\"',"\'")
                composer = obj["composer"].replace('\"',"\'")
                album = obj["album"].replace('\"',"\'")
                release_year = obj["release_year"]
                link_playlist = obj["link_playlist"]
                query = "INSERT INTO musics(name, country, link, image, singer, composer, album, release_year, link_playlist, created_at) VALUES (\"{}\", \"{}\",\"{}\",\"{}\",\"{}\", \"{}\", \"{}\",\"{}\",\"{}\",{})".format(name, country, link, image, singer, composer, album, release_year, link_playlist,'NOW()')
                try:
                    cursor.execute(query)
                    print(name)
                    number_saved = number_saved + 1
                except:
                    continue
    print("saved: ", number_saved)
    db.commit()
    db.close()
def deleteDB():
    try:
        db = mysql.connector.connect(user=constances.USERNAME, password=constances.PASSWORD, host=constances.HOST, database=constances.DATABASE)
        cursor = db.cursor()
    except:
        return 0
    query = "delete FROM musics "
    query2 = "ALTER TABLE musics AUTO_INCREMENT = 1"
    try:
        cursor.execute(query)
        cursor.execute(query2)
        db.commit()
        print("Deleted")
    except:
        db.rollback()

def test(path):
    data = createPlayList(path)
    for index in data:
        print(index)
def getMusicByCountry(country):
    try:
        db = mysql.connector.connect(user=constances.USERNAME, password=constances.PASSWORD, host=constances.HOST, database=constances.DATABASE)
        cursor = db.cursor()
    except:
        return 0
    query = "SELECT * FROM musics where country = '{}'".format(country)
    data = []
    try:
        cursor.execute(query)
        records = cursor.fetchall()
        for row in records:
            data.append({
                "id": row[0],
                "name": row[1],
                "country": row[2],
                "link": row[3],
                "image": row[4],
                "singer": row[5],
                "composer": row[6],
                "album": row[7],
                "release_year": row[8]
            })
    except:
        return []
    db.close()
    return  data

def listToJson(str, data):
    now = datetime.now()
    dt_string = now.strftime("%d%m%Y %H%M%S")
    path = "{}{}.json".format(str, dt_string)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
# if __name__ == "__main__":
#     crawAndSaveDB()
#     aa=getMusicByCountry("vn")
#     # listToJson("nhac",aa)

