import json
import urllib, urllib2, math
from flask import request, abort
from flask.ext import restful
from flask.ext.restful import reqparse
from flask_rest_service import app, api, mongo
from bson.objectid import ObjectId
import pusher
from flask.ext.cors import CORS, cross_origin

p = pusher.Pusher(
  app_id='100951',
  key='e271f8de7b3e62e99757',
  secret='57688e799027b8673c2d'
)

cors = CORS(app, resources={r"/*": {"origins": "*"}})

class ReadingList(restful.Resource):
    def __init__(self, *args, **kwargs):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('reading', type=str)
        super(ReadingList, self).__init__()

    def get(self):
        return  [x for x in mongo.db.readings.find()]

    def post(self):
        args = self.parser.parse_args()
        if not args['reading']:
            abort(400)

        jo = json.loads(args['reading'])
        reading_id =  mongo.db.readings.insert(jo)
        return mongo.db.readings.find_one({"_id": reading_id})


class Reading(restful.Resource):
    def get(self, reading_id):
        return mongo.db.readings.find_one_or_404({"_id": reading_id})

    def delete(self, reading_id):
        mongo.db.readings.find_one_or_404({"_id": reading_id})
        mongo.db.readings.remove({"_id": reading_id})
        return '', 204


class Root(restful.Resource):
    def get(self):
        return {
            'status': 'OK',
            'mongo': str(mongo.db),
        }

def getTime(departure, arrival):
    base = 'http://dev.virtualearth.net/REST/V1/Routes/Driving'
    attr = {
        'o': 'json',
     'wp.0': departure,
     'wp.1': arrival,
      'key': 'Aqkfkri9zH6Be8fcfzTI5Hwa2OnH4HdKy1MXKZRUSsc14mqXZJN8T6irT-JSfPIq',
    }
    url = base+'?'+urllib.urlencode(attr)
    response = json.load(urllib2.urlopen(url))

    time = response['resourceSets'][0]['resources'][0]['travelDuration']
    hours = time/3600
    minutes = time/60 - hours*60
    seconds = time - minutes*60 - hours*3600

    return {
        'timePretty': str(hours)+':'+str(minutes)+':'+str(seconds),
        'time': time
    }

class XtoY(restful.Resource):
    def get(self, departure, arrival):
        return getTime(departure, arrival)

class iAmHere(restful.Resource):
    def get(self, id_sender, id_reciever, longitude, latitude):
        sender = mongo.db.test.find_one({"_id": id_sender})
        p['iAmHere'].trigger(id_sender, {
              'id_sender': id_sender,
            'id_reciever': id_reciever,
                   'time': getTime(latitude+','+longitude,sender['latitude']+','+sender['longitude'])
        })
        return {
              'id_sender': id_sender,
            'id_reciever': id_reciever,
              'longitude': longitude,
               'latitude': latitude,
        }

class whereAreYou(restful.Resource):
    def get(self, id_sender, id_reciever, longitude, latitude):

        mongo.db.test.update(
        {
            '_id': id_sender
        },
        {
            '_id': id_sender,
            'longitude': longitude,
            'latitude': latitude,
        }, True)

        p['whereAreYou'].trigger(id_reciever, {
            'id_sender': id_sender,
            'id_reciever': id_reciever,
            'longitude': longitude,
            'latitude': latitude,
        })
        return {
              'id_sender': id_sender,
            'id_reciever': id_reciever,
        }

api.add_resource(Root, '/')
api.add_resource(XtoY, '/route/<string:departure>/<string:arrival>')
api.add_resource(iAmHere, '/iamhere/<string:id_sender>/<string:id_reciever>/<string:longitude>/<string:latitude>')
api.add_resource(whereAreYou, '/whereareyou/<string:id_sender>/<string:id_reciever>/<string:longitude>/<string:latitude>')