import os, gridfs, pika, json
from flask import Flask, request
from flask_pymongo import PyMongo
from auth import validate
from auth_svc import access
from storage import util

server = Flask(__name__)
server.config["MONGO_URI"] = "mongodb://host.minikube.internal:27017/videos"

#wrap flask server, allow interface with mongodb
mongo = PyMongo(server)

#wrap mongodb, in order to habdle files over 16MB(sharding the files/chunks)
fs = gridfs.GridFS(mongo.db)

#synchronous rabbitMQ connection
connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
channel = connection.channel()

#commuicate with auth service to log user in and assign token to the user
@server.route("/login", methods=["POST"])
def login():
    token, err = access.login(request)

    if not err:
        return token
    else:
        return err
    
@server.route("/upload", methods=["POST"])
def upload():
    access, err = validate.token(request)

    if err:
        return err

    access = json.loads(access)

    if access["admin"]:
        if len(request.files) != 1:
            return "exactly 1 file required", 400
        
        #iterate through the key-values in  the dict
        for _, f in request.files.items():
            err = util.upload(f, fs, channel, access)

            if err:
                return err
        
        return "success", 200
    else:
        return "not authorized", 401
    
@server.route("/download", methods=["GET"])
def download():
    pass

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)