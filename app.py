from flask import Flask, request
from flask_restful import Resource, Api

import threading
import time

from articles import getNewsFromId, getLastId, saveArticles
from constance import constances
app = Flask(__name__)
api = Api(app)


class Articles(Resource):
    def get(self, id):
        items = []
        if (int(id) == 0):
            items = getNewsFromId(getLastId())
        else:
            items = getNewsFromId(int(id))
        if items is None:
            return {'message': "Can't get articles"}, 400
        return items, 200


api.add_resource(Articles, '/article/<string:id>')


def crawlData():
    while True:
        saveArticles()
        time.sleep(constances.TIME_BETWEEN_CRAWL)
        print("Crawled")


@app.route('/run')
def craw():
    threading.Thread(
        target=crawlData,
    ).start()
    return "Crawling"


if __name__ == '__main__':
    app.run(debug=True)
