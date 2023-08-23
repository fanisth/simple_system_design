import pika, json

def upload(f, fs, channel, access):
    #upload file to mongo using gridFs
    try:
        #if success a fileId object will be returned
        fid = fs.put(f)
    except Exception as err:
        return "internal server error", 500

    #then put a message in the queue, create async communication flow bettween gateway and converter, 
    # gateway returns response to client without waiting for video to be proccessed
    message = {
        "video_fid": str(fid),
        "mp3_fid": None,
        "username": access["username"],
    }

    try:
        channel.basic_publish(
            exchange="",
            routing_key="video",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE #messages persisted in queue in event of a pod crash/restart
            )
        )
    except:
        #if publish fails we delete it from mongo as it will never be processed
        # (improvent: we mark such videos and new service polls such videos for future retries)
        fs.delete(fid)
        return "internal server error", 500