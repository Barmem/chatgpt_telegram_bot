import random
import pymongo
import config
from bson.objectid import ObjectId

class requestslist():
    def __init__(self):
        self.client = pymongo.MongoClient(config.mongodb_uri)
        self.db = self.client['requests_db']
        self.col = self.db['fortunerec']
        self.col2 = self.db['tarotologists']

    def add(self, phone, log):
        data = {
            'phone': phone,
            'log': log,
            'status': 1
        }
        self.col.insert_one(data)

    def getrand(self):
        result = self.col.find_one({'status': 1})
        if result:
            return [f"Телефон: {result['phone']}\nЧат:\n{result['log']}", str(result['_id'])]
        else:
            return ["Простите, запросов нет", 0]

    def get_table_length(self):
        return self.col.count_documents({'status': 1})

    def delete(self, id):
        self.col.delete_one({'_id': id})

    def setstatus(self, id, status):
        if id == 0:
            return
        id = ObjectId(str(id))
        self.col.update_one({'_id': id}, {'$set': {'status': status}})

    def setsworkingtatus(self, telegram_id, status):
        result = self.col2.find_one({'tgid': telegram_id})
        if result:
            self.col2.update_one({'tgid': telegram_id}, {'$set': {'status': status}})
        else:
            data = {
                'tgid': telegram_id,
                'status': status
            }
            self.col2.insert_one(data)

    def getworking(self):
        results = self.col2.find({'status': 1}, projection={'_id': False, 'tgid': True})
        return [r['tgid'] for r in results]

    def create_db(self, db_name, collection_name, columns):
        pass # Not needed for MongoDB
