import pika, sys, os, time
from send import send_email

def main():
    #rabbitmq connection
    connection = pika.BlockingConnection(
        #host=rabbitmq because our service name is rabbitmq and the service name name will resolve to the host IP of the service
        pika.ConnectionParameters(host="rabbitmq")
    )
    channel = connection.channel()

    def callback(ch, method, properties, body):
        err = send_email.notification(body)

        if err:
            #in case of error we send a nack to channel, because we want to keep messages(via delivery tag) in the queue in the case of failure 
            # so that another process will process them
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        #callback gets executed when a message is pulled off of the queue
        queue=os.environ.get("MP3_QUEUE"), on_message_callback=callback
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
