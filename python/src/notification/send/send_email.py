import smtplib, os, json

def notification(message):
    try:
        message = json.loads(message)
        mp3_fid = message["mp3_fid"]
        sender_address = os.environ.get("GMAIL_ADDRESS")
        sender_password = os.environ.get("GMAIL_PASSWORD")
        receiver_address = message["username"]

        message = f"MP3 {mp3_fid} is ready for download!"
        
        session = smtplib.SMTP("smtp.gmail.com", 587)
        session.set_debuglevel(1)  # Enable debug mode
        #secure communication
        session.starttls()
        session.login(sender_address, sender_password)
        session.sendmail(sender_address, receiver_address, message)
        session.quit()
        print("Mail Sent")
    except Exception as err:
        print(err)
        return err