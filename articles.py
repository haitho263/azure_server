import json
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import html
import mysql.connector
import ast
from constance import constances

BASE_URL = "https://vnexpress.net"
PATH_TN = "/tin-nong"
PATH_GT = "/giai-tri-p"
LIST_PATH = ["/thoi-su-p", "/the-gioi-p", "/kinh-doanh/p", "/the-thao/p", "/giai-tri-p", "/phap-luat-p", "/giao-duc-p", "/suc-khoe/p",
             "/doi-song/p", "/du-lich/p", "/khoa-hoc-p", "/so-hoa/p", "/oto-xe-may-p"]


def crawNewsData(url):
    print("Crawl from ", url)
    response = requests.get(url)
    if response.status_code != 200:
        return []
    soup = BeautifulSoup(response.content, "html.parser")
    titles = soup.findAll('h3', class_='title-news')
    if titles == []:
        titles = soup.findAll('h2', class_='title-news')
    links = [link.find('a').attrs["href"] for link in titles]
    data = []
    for link in links:
        # check video
        if link.find("video") != -1:
            continue
        news = requests.get(link)
        if news.status_code != 200:
            continue

        soup = BeautifulSoup(news.content, "html.parser")
        soup = html.unescape(soup)

        # get title
        try:
            title = soup.find("h1", class_="title-detail").text
        except:
            continue
        # get category
        try:
            category = soup.find("ul", class_="breadcrumb")
            category = category.find("a").text
        except:
            category = ""
        # get time
        try:
            # time = soup.find("span", class_="date").text
            # time2 = time[0:-8]
            # b = "0123456789: /"
            # for char in time:
            #     if char not in b:
            #         time = time.replace(char, '')
            # time = time[2:-2]
            # time = time.replace("2020","20")
            # time = datetime.strptime(time, '%d/%m/%y %H:%M')
            time2 = soup.find("span", class_="date").text
            time = time2[0:-8]
            b = "0123456789: /"
            for char in time2:
                if char not in b:
                    time2 = time2.replace(char, '')
            time2 = time2[2:-2]
            time2 = time2.replace("2020", "20")
            time2 = datetime.strptime(time2, '%d/%m/%y %H:%M')
            # print(time)
        except:

            continue
        # get location
        try:
            location = soup.find("span", class_="location-stamp").text
        except:
            location = ""
        # get description
        try:
            description = soup.find("p", class_="description")
            if location != "":
                description.find(
                    "span", class_="location-stamp").decompose()
                description.find("p", class_="description")

        except:
            continue
        # get listContent
        try:
            contents = soup.find("article", class_="fck_detail").findAll()

            check_video = ""
            check_video = soup.findAll("div", class_="box_embed_video")
            if check_video != []:
                continue

            check_table = ""
            check_table = soup.findAll("table")
            if check_table != []:
                continue

            check_live = ""
            check_live = soup.findAll("article", id="content-live")
            if check_live != []:
                continue

            check_player = ""
            check_player = soup.findAll("div", {"data-oembed-url": True})
            if check_player != []:
                continue

            check_lightgallery = soup.findAll("article", id="lightgallery")
            if check_lightgallery != []:
                continue

            check_lightgallery2 = soup.findAll(
                "div", class_="width-detail-photo")
            if check_lightgallery2 != []:
                continue

            listContent = []

            for obj in contents:
                obj_info = ""
                obj_type = ""
                try:
                    nameclass = ""
                    if obj.name == "p":
                        nameclass = ' '.join(map(str, obj['class']))
                        if nameclass == "Image":
                            obj_info = obj.text
                            obj_type = "img_des"
                        else:
                            obj_info = obj.text
                            obj_type = "text"

                    if obj.name == "img":
                        obj_info = obj.attrs["data-src"]
                        obj_type = "image"
                    if obj_type != "" and obj_info != ">>Đáp án" and obj_info != " " and obj_info != "\n":
                        obj_info = obj_info.replace("\xa0", " ")
                        listContent.append({
                            "info": obj_info.replace("'", "\\'"),
                            "type": obj_type
                        })
                except:
                    continue
            # get author
            author = ""
            if len(listContent[-1]["info"]) <= 40:
                author = listContent[-1]["info"].replace(
                    "* Tiếp tục cập nhật.", '')
                author = author.replace("\n", "")
                listContent = listContent[0:-1]
        except:
            listContent = ""
            author = ""
        data.append({
            "link": link,
            "category": category,
            "title": title,
            "time": time,
            "location": location,
            "description": description.text,
            "content": listContent,
            "author": author,
            "time2": time2
        })
    return data


def saveArticles(base_url, path):
    data = crawNewsData(base_url + path)
    print("Crawl from ", path)
    if data == []:
        return 1
    number_saved = 0
    is_hot = False
    if path == "/tin-nong":
        is_hot = True
    # save json
    # listToJson("one_day ", data)
    db = mysql.connector.connect(user=constances.USERNAME, password=constances.PASSWORD,
                                 host=constances.HOST,
                                 database=constances.DATABASE)
    cursor = db.cursor()
    # delete outdate
    # query = 'delete FROM articles where DATE_SUB(date(now()), INTERVAL {} DAY) > date(created_at)'.format(
    #     constances.DELETE_AFTER)
    # query = "delete FROM articles "
    # query2 = "ALTER TABLE articles AUTO_INCREMENT = 1"
    # try:
    #     cursor.execute(query)
    #     cursor.execute(query2)
    #     db.commit()
    # except:
    #     db.rollback()
    # save to db
    for index, item in enumerate(data[::-1]):
        # if index==1:
        #     break
        _link = item["link"]
        time = item["time"]
        category = item["category"]
        title = item["title"].replace('"', '\\"')
        location = item["location"]
        description = item["description"].replace('"', '\\"')
        author = item["author"].replace('"', '\\"')
        content = item["content"]
        content = str(item["content"]).replace('"', '\\"')
        time2 = item["time2"]
        query = 'INSERT INTO articles(link, time, category, title, location, description, content, author, is_hot,time2, created_at) VALUES ("{}", "{}", "{}", "{}","{}", "{}", "{}", "{}", {}, "{}", {})'.format(
            _link, time, category, title, location, description, content, author, is_hot, time2, 'NOW()')
        try:
            cursor.execute(query)
            # Commit your changes in the database
            db.commit()
            # debug
            # print('added: ', title)
            number_saved = number_saved + 1
        except:
            print(query)
            db.rollback()
            try:
                query = "ALTER TABLE articles AUTO_INCREMENT = {}".format(
                    getLastId())
                cursor.execute(query)
                db.commit()
            except:
                pass
    db.close()
    print("Number news save to db from: ", path, ": ", number_saved)

# delete after "number" of days

# def deleleOutdateArticles():
#     db = mysql.connector.connect(user=constances.USERNAME, password=constances.PASSWORD,
#                                  host=constances.HOST,
#                                  database=constances.DATABASE)

#     cursor = db.cursor()
#     sqlquery = "delete FROM articles where DATE_SUB(date(now()), INTERVAL {} DAY) > date(created_at)".format(
#         constances.DELETE_AFTER)
#     try:
#         cursor.execute(sqlquery)
#         db.commit()
#     except:
#         db.rollback()
#     db.close()

# get articles from end_id back to end_id - NEWS_PER_LOAD
# def getNewsFromId(end):
#     db = mysql.connector.connect(user=constances.USERNAME, password=constances.PASSWORD,
#                                  host=constances.HOST,
#                                  database=constances.DATABASE)
#     cursor = db.cursor()
#     cursor.execute("SELECT * FROM articles LIMIT 1")
#     first_id = cursor.fetchone()
#     if first_id[0] is None: return []

#     if end < first_id[0]:
#         return []

#     start = end - (constances.ARTICLES_PER_LOAD)
#     if start < 1:
#         start = 1

#     # query = "SELECT * FROM articles where {}<=id && id<={}".format(start, end)
#     query = "SELECT * FROM articles where id between {} and {}".format(start, end)

#     dataNews = []
#     cursor.execute(query)
#     records = cursor.fetchall()
#     for row in records:
#         try:
#             content = ast.literal_eval(row[7])
#         except:
#             continue
#         dataNews.append({
#             "id": row[0],
#             "link": row[1],
#             "time": row[2],
#             "category": row[3],
#             "title": row[4],
#             "location": row[5],
#             "description": row[6],
#             "content": content,
#             "author": row[8],
#         })
#     db.close()
#     return dataNews[::-1]


def getArticlesByCategory(category, offset):
    db = mysql.connector.connect(user=constances.USERNAME, password=constances.PASSWORD,
                                 host=constances.HOST,
                                 database=constances.DATABASE)
    cursor = db.cursor()
    query = 'SELECT * FROM datatrends.articles where  category LIKE "%{}%" ORDER BY time2 DESC LIMIT {} OFFSET {}'.format(
        category, constances.ARTICLES_PER_LOAD, offset)
    cursor.execute(query)
    dataNews = []
    records = cursor.fetchall()
    for row in records:
        try:
            content = ast.literal_eval(row[7])
        except:
            continue
        dataNews.append({
            "id": row[0],
            "link": row[1],
            "time": row[2],
            "category": row[3],
            "title": row[4],
            "location": row[5],
            "description": row[6],
            "content": content,
            "author": row[8],
            "time2": row[10],
        })
    db.close()
    return dataNews


def getHotNews(offset):
    db = mysql.connector.connect(user=constances.USERNAME, password=constances.PASSWORD,
                                 host=constances.HOST,
                                 database=constances.DATABASE)
    cursor = db.cursor()
    query = 'SELECT * FROM datatrends.articles where  is_hot = True ORDER BY time2 DESC LIMIT {} OFFSET {}'.format(
        constances.ARTICLES_PER_LOAD, offset)
    cursor.execute(query)
    dataNews = []
    records = cursor.fetchall()
    for row in records:
        try:
            content = ast.literal_eval(row[7])
        except:
            continue
        dataNews.append({
            "id": row[0],
            "link": row[1],
            "time": row[2],
            "category": row[3],
            "title": row[4],
            "location": row[5],
            "description": row[6],
            "content": content,
            "author": row[8],
            "time2": row[10],
        })
    db.close()
    return dataNews


def getNewArticles(offset):
    db = mysql.connector.connect(user=constances.USERNAME, password=constances.PASSWORD,
                                 host=constances.HOST,
                                 database=constances.DATABASE)
    cursor = db.cursor()
    query = 'SELECT * FROM datatrends.articles ORDER BY time2 DESC LIMIT {} OFFSET {}'.format(
        constances.ARTICLES_PER_LOAD, offset)
    cursor.execute(query)
    dataNews = []
    records = cursor.fetchall()
    for row in records:
        try:
            content = ast.literal_eval(row[7])
        except:
            continue
        dataNews.append({
            "id": row[0],
            "link": row[1],
            "time": row[2],
            "category": row[3],
            "title": row[4],
            "location": row[5],
            "description": row[6],
            "content": content,
            "author": row[8],
            "time2": row[10],
        })
    db.close()
    return dataNews


def getArticleById(id):
    db = mysql.connector.connect(user=constances.USERNAME, password=constances.PASSWORD,
                                 host=constances.HOST,
                                 database=constances.DATABASE)
    cursor = db.cursor()
    query = "SELECT * FROM articles where id={}".format(id)
    cursor.execute(query)
    dataNews = []
    records = cursor.fetchall()
    for row in records:
        try:
            content = ast.literal_eval(row[7])
        except:
            continue
        dataNews.append({
            "id": row[0],
            "link": row[1],
            "time": row[2],
            "category": row[3],
            "title": row[4],
            "location": row[5],
            "description": row[6],
            "content": content,
            "author": row[8],
            "time2": row[10],
        })
    db.close()
    if dataNews == []:
        return []
    return dataNews[0]

def searchArticles(info, offset):
    db = mysql.connector.connect(user= constances.USERNAME, password= constances.PASSWORD,
                                 host= constances.HOST,
                                 database= constances.DATABASE)
    cursor = db.cursor()
    query = "SELECT * FROM datatrends.articles where (title LIKE '%{}%') or (description LIKE '%{}%')" \
            " ORDER BY time2 DESC LIMIT {} OFFSET {}".format(
                info, info, constances.ARTICLES_PER_LOAD, offset)
    cursor.execute(query)
    dataNews = []
    records = cursor.fetchall()
    for row in records:
        try:
            content = ast.literal_eval(row[7])
        except:
            continue
        dataNews.append({
            "id": row[0],
            "link": row[1],
            "time": row[2],
            "category": row[3],
            "title": row[4],
            "location": row[5],
            "description": row[6],
            "content": content,
            "author": row[8],
            "time2": row[10],
        })
    db.close()
    return dataNews


def getContentById(id):
    db = mysql.connector.connect(user=constances.USERNAME, password=constances.PASSWORD,
                                 host=constances.HOST,
                                 database=constances.DATABASE)

    cursor = db.cursor()
    query = "SELECT content FROM articles where id={}".format(id)
    dataContents = []
    try:
        cursor.execute(query)
        records = cursor.fetchall()
        for row in records:
            dataContents = row[0]
            break
    except:
        pass
    db.close()
    try:
        return ast.literal_eval(dataContents)
    except:
        return []


def listToJson(str, data):
    now = datetime.now()
    dt_string = now.strftime("%d%m%Y %H%M%S")
    path = "{}{}.json".format(str, dt_string)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def getLastId():
    db = mysql.connector.connect(user=constances.USERNAME, password=constances.PASSWORD,
                                 host=constances.HOST,
                                 database=constances.DATABASE)
    # prepare a cursor object using cursor() method
    cursor = db.cursor()
    query = "SELECT MAX(id) FROM articles"
    result = 0
    try:
        cursor.execute(query)
        records = cursor.fetchall()
        for index in records:
            result = index[0]
            break
    except:
        pass
    db.close()
    return result
# number page crawl >=1


def crawlAll(number):
    for index in range(1, number+1)[::-1]:
        for path in LIST_PATH:
            path = path+"{}".format(index)
            saveArticles(BASE_URL, path)
    print("END")

def crawlCategory(path,number):
    for index in range(1, number+1)[::-1]:
            path = path+"{}".format(index)
            saveArticles(BASE_URL, path)


def crawlHotNews():
    saveArticles(BASE_URL, PATH_TN)

# def saveAllToJson():
#     all_data = getNewsFromId(1, getLastId())
#     listToJson("All database ", all_data)
# if __name__ == "__main__":
#      crawlHotNews()
#     crawlAll(1)
#     # crawlAndSaveAllArticles()
#     # listToJson("test",getArticlesById(10))
#     #     saveArticles(BASE_URL, "/giao-duc")
#     #     aa = getNewArticles(0)
#     #      # print(aa)
#     #     listToJson("test",aa)