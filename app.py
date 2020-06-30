from flask import Flask, request
from flask_restful import Resource, Api, reqparse

import threading
import time

from articles import getArticlesByCategory, getArticleById, getHotNews, getNewArticles, searchArticles, crawlHotNews, crawlAll
from music import getMusicByCountry, crawAndSaveDB
from constance import constances
app = Flask(__name__)
api = Api(app)


class Article(Resource):
    parser = reqparse.RequestParser()

    def get(self):
        items = []
        id = int(request.args.get('id'))
        items = getArticleById(id)
        # if (int(id) == 0):
        #     items = getNewsFromId(getLastId())
        # else:
        #     items = getNewsFromId(int(id))
        if items is None:
            return {'message': "Can't get articles"}, 400
        return items, 200


class Articles(Resource):
    parser = reqparse.RequestParser()

    def get(self):
        items = []
        offset = int(request.args.get('offset'))*constances.ARTICLES_PER_LOAD
        cat = request.args.get('cat')
        print(cat)
        items = getArticlesByCategory(cat, offset)

        if items is None:
            return {'message': "Can't get articles"}, 400
        return items, 200


class Articles2(Resource):
    parser = reqparse.RequestParser()

    def get(self, tag):
        items = []
        offset = int(request.args.get('offset'))*constances.ARTICLES_PER_LOAD
        if(tag == 'hot'):
            items = getHotNews(offset)
        elif (tag == 'new'):
            items = getNewArticles(offset)

        if items is None:
            return {'message': "Can't get articles"}, 400
        return items, 200

class SearchArticle(Resource):
    parser = reqparse.RequestParser()

    def get(self):
        items = []
        info = request.args.get('info')
        items = searchArticles(info,0)
        if items is None:
            return {'message': "Can't get articles"}, 400
        return items, 200

class Music(Resource):
    def get(self, country):
        items = []
        items = getMusicByCountry(country)

        if items is None:
            return {'message': "Can't get songs"}, 400
        return items, 200


api.add_resource(Article, '/article/')
api.add_resource(Articles, '/articles/')
api.add_resource(Articles2, '/articles/<string:tag>/')
api.add_resource(SearchArticle, '/articles/search/')
api.add_resource(Music, '/music/<string:country>')

def crawlArticle():
    while True:
        crawlHotNews()
        crawlAll(1)
        print("News Crawled")
        time.sleep(constances.TIME_BETWEEN_CRAWL)


@app.route('/article/run')
def crawArticleThread():
    threading.Thread(
        target=crawlArticle,
    ).start()
    return "Crawling articles"

# def crawlMusic():
#     while True:
#         print("Music Crawled")
#         crawAndSaveDB()
#         time.sleep(43200)


# @app.route('/music/run')
# def crawMusicThread():
#     threading.Thread(
#         target=crawlMusic,
#     ).start()
#     return "Crawling music"

if __name__ == '__main__':
    app.run(debug=True, threaded=True)