import pika, sys, os, time
from pymongo import MongoClient
import gridfs
from convert import to_mp3

def main():
    #instance of MongoClient gives access to the dbs that we have in our mongo
    client = MongoClient("host.minikube.internal", 27017)
    db_videos = client.videos
    db_mp3s = client.mp3s
    #gridfs
    fs_videos = gridfs.GridFS(db_videos)
    fs_mp3s = gridfs.GridFS(db_mp3s)

    #rabbitmq connection
    connection = pika.BlockingConnection(
        #host=rabbitmq because our service name is rabbitmq and the service name name will resolve to the host IP of the service
        pika.ConnectionParameters(host="rabbitmq")
    )
    channel = connection.channel()

    def callback(ch, method, properties, body):
        err = to_mp3.start(body, fs_videos, fs_mp3s, ch)

        if err:
            #in case of error we send a nack to channel, because we want to keep messages(via delivery tag) in the queue in the case of failure 
            # so that another process will process them
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_ack(elivery_tag=method.delivery_tag)

    channel.basic_consume(
        #callback gets executed when a message is pulled off of the queue
        queue=os.environ.get("VIDEO_QUEUE"), on_message_callback=callback
    )

    print("Waiting for messages. To exit press Ctrl+C")

    #starts consumer, listens to queue
    channel.start_consuming()

if __name__ == "__main__":
    try:
        main()
    #we catch the keyboard interruption
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
