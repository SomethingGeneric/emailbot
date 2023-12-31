import imaplib
import email
import time
import sys, os
import signal
import toml
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from responders import syst

with open(
    "config.toml",
) as f:
    config = toml.load(f)

if not os.path.exists("data"):
    os.makedirs("data")

cogs = [
    syst.SystemResponder()
]

sender_addr = config["from"]
sender_passw = config["passw"]

# Connect to the IMAP server
mail = imaplib.IMAP4_SSL(sender_addr.split("@")[1])

mail.login(sender_addr, sender_passw)
mail.select("inbox")


# Define a function to retrieve the latest unread email
def get_latest_email():
    _, messages = mail.search(None, "UNSEEN")
    if messages[0] == b"":
        return None
    else:
        latest_message_id = messages[0].split()[-1]
        _, message_data = mail.fetch(latest_message_id, "(RFC822)")
        message_text = message_data[0][1].decode()
        message = email.message_from_string(message_text)
        return message


# Define a function to extract the email body and sender from a message
def get_email_details(message):
    body = ""
    sender = ""
    for part in message.walk():
        if part.get_content_type() == "text/plain":
            body = part.get_payload(decode=True).decode()
    sender = message["From"]
    return body, sender


# Define a function to generate a response using the local model
def generate_response(fromaddr, subj, prompt):
    for c in cogs:
        if c.trigger_start:
            if prompt.startswith(c.trigger):
                try:
                    return c.process(prompt)
                except Exception as e:
                    return "Error: '" + str(e) + "'."
        else:
            if c.trigger in prompt:
                try:
                    return c.process(prompt)
                except Exception as e:
                    return "Error: '" + str(e) + "'."
    
    return "I am smooth brain"

# Define a function to handle SIGTERM signal
def sigterm_handler(signal, frame):
    print("SIGTERM received. Exiting...")
    sys.exit(0)

if __name__ == "__main__":

    # Set up the SIGTERM signal handler
    signal.signal(signal.SIGTERM, sigterm_handler)

    # Retrieve the latest unread email
    message = get_latest_email()

    print("Logged in. Starting check loop.")

    # Run the daemon loop
    while True:
        try:
            # Retrieve the latest unread email
            message = get_latest_email()

            # If there is an unread email and it's not from the bot, extract the details and generate a response
            if message and message["From"] != "me":
                print("Found a new message")
                body, sender = get_email_details(message)

                response = generate_response(sender, message["Subject"], body)

                from_email = sender_addr
                to_email = sender

                subject = ""

                if message['Subject'] != "":
                    print(f"Responding to {message['Subject']}")
                    subject = "Re: {}".format(message["Subject"])
                else:
                    print("No subject on current message.")
                
                
                body = response

                msg = MIMEMultipart()
                msg["From"] = from_email
                msg["To"] = to_email
                if subject != "":
                    msg["Subject"] = subject

                msg.attach(MIMEText(body, "plain"))

                smtp_server = sender_addr.split("@")[1]
                smtp_port = 587
                smtp_username = sender_addr
                smtp_password = sender_passw

                with smtplib.SMTP(smtp_server, smtp_port) as smtp:
                    smtp.starttls()
                    smtp.login(smtp_username, smtp_password)
                    smtp.send_message(msg)

                print("Response sent.")

            # Wait for 5 seconds before checking for new emails again
            time.sleep(5)

        except KeyboardInterrupt:
            print("Keyboard interrupt received. Exiting...")
            sys.exit(0)

        #except Exception as e:
        #    print("An error occurred:", e)
