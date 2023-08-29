import os, gridfs, pika, json, time, sys
from flask import Flask, request, send_file
from flask_pymongo import PyMongo
from auth import validate
from auth_svc import access
from storage import util
from bson.objectid import ObjectId

server = Flask(__name__)

#wrap flask server, allow interface with mongodb
mongo_video = PyMongo(server, uri="mongodb://host.minikube.internal:27017/videos")
mongo_mp3 = PyMongo(server, uri="mongodb://host.minikube.internal:27017/mp3s")

# Get the actual Database instances from PyMongo
db_video = mongo_video.db
db_mp3 = mongo_mp3.db

#wrap mongodb, in order to habdle files over 16MB(sharding the files/chunks)
fs_videos = gridfs.GridFS(db_video)
fs_mp3s = gridfs.GridFS(db_mp3)

def connect_to_rabbitmq(max_retries=5, retry_delay=5):
    #more elegant we can add exponential backoff
    retries = 0
    while retries < max_retries:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
            return connection
        except Exception as e:
            print(f"Error connecting to RabbitMQ: {e}")
            retries += 1
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    print("Max retries reached. Could not connect to RabbitMQ.")
    return None

#synchronous rabbitMQ connection
connection = connect_to_rabbitmq()
if not connection:
    print("Unable to connect with RabbitMQ")
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)
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
            err = util.upload(f, fs_videos, channel, access)

            if err:
                return err
        
        return "success", 200
    else:
        return "not authorized", 401
    
@server.route("/download", methods=["GET"])
def download():
    access, err = validate.token(request)

    if err:
        return err

    access = json.loads(access)

    if access["admin"]:
        fid_string = request.args.get("fid")

        if not fid_string:
            return "fid is required", 400

        try:
            out = fs_mp3s.get(ObjectId(fid_string))
            return send_file(out, download_name=f"{fid_string}.mp3")
        except Exception as err:
            print(err)
            return "internal server error", 500
    
    return "not authorized", 401


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)