import os
import imaplib
import email
import argparse
from dotenv import load_dotenv
from pathlib import Path
from email.header import decode_header
from email.utils import parseaddr

def save_last_uid(uid, filepath="last_uid.txt"):
    # Creates file if not exists, overwrites if it does
    with open(filepath, "w") as file:
        file.write(str(uid))

def load_last_uid(filepath="last_uid.txt"):
    try:
        with open(filepath, "r") as f:
            # The file should contain a single integer UID
            return int(f.read().strip()) 
    except FileNotFoundError:
        return None

def decode_name(msg): 
    raw_from = msg.get("From")
    name, email_address = parseaddr(raw_from)

    if name:  # Case 1: display name is available
        return name
    else:     # Case 2: extract from domain
        domain = email_address.split("@")[-1]   # e.g. "geckorobotics.com"
        company = domain.split(".")[0].capitalize()
        return company

def check_if_app(subject, word_bank=[set(["thanks","thank"]), set(["apply","applying","application"])]):
    decoded_parts = decode_header(subject)

    line = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            line += part.decode(encoding or "utf-8", errors="ignore")
        else:
            line += part

    line = line.lower().split()                         
    line = [word.strip() for word in line]
    line_set = set(line)

    track_keywords = 0
    for bank_set in word_bank:
        if (any(word in line_set for word in bank_set)):
            track_keywords += 1
        else:
            break
    
    if track_keywords == len(word_bank):
        return True
    return False


def main(resume=False, last_n=1):   # default main() fetches most recent email

    # Load environment variables
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / "config" / ".env")
    app_password = os.getenv("MAIL_SCRIPT_APP_PASSWORD")

    # Basic validation of input arguments
    if not app_password:
        raise ValueError("MAIL_SCRIPT_APP_PASSWORD environment variable not set!")

    # Login into email server and select inbox
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login("hs4907@nyu.edu", app_password)
    mail.select("inbox")

    # For the following if-else block we want to either resume from last UID or fetch the last N emails

    # If the user wants to start where they left off use this:
    if resume:
        recent_uid = load_last_uid()
        if recent_uid is None: # If saved UID file doesn't exist, fetch the most recent email instead
            print("No previous UID found. Fetching the most recent email instead.")
            # Fetch the most recent email and save its UID
            status, data = mail.uid('search', None, 'ALL')
            email_ids = data[0].split()
            save_last_uid(int(email_ids[-1]), "last_uid.txt")

            # Then fetch that same email to send to user
            status, messages = mail.search(None, "ALL")
            email_ids = messages[0].split()
            last_one = b",".join(email_ids[-1:]) 
            status, msg_data = mail.fetch(last_one, "(RFC822)") 


        # If the file does exist, resume from last UID
        else: 
            # Search and Fetch for emails with UID greater than recent_uid
            status, messages = mail.uid('search', None, f'UID {recent_uid + 1}:*')
            email_ids = messages[0].split()

            if not email_ids: # If no new emails fetch the most recent (old) email again
                print("No new emails since last UID.")
                status, msg_data = mail.uid('fetch', str(recent_uid), "(RFC822)")
            else:     
                last_couple = b",".join(email_ids) 
                status, msg_data = mail.fetch(last_couple, "(RFC822)")
                # Save the last UID we processed
                save_last_uid(int(email_ids[-1]), "last_uid.txt") # Save the new most recent UID 
             

    #  Otherwise, fetch the last N emails
    else:
        # Use sequence based searching. last_n is guaranteed to be an integer >= 1
        number_of_recent_emails = last_n
        status, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()
        last_couple = b",".join(email_ids[-number_of_recent_emails:])  
        status, msg_data = mail.fetch(last_couple, "(RFC822)") # RFC822 = macro for retrieve the whole message

    """LEFT OFF HERE 10/10 FINISH ABOVE"""
        """I have the logic for if the user wants to resume from last UID or fetch the last N emails"""


    file = open("output.txt", "w") 

    num_of_apps = 0

    for id in msg_data:  # msg_data is a list of tuples and a b')'
        if isinstance(id, tuple):
            raw_email = id[1]
            msg = email.message_from_bytes(raw_email)
            subject = msg["subject"]
            if (check_if_app(subject)):
                num_of_apps += 1
                file.write(f"{num_of_apps}) ")
                file.write(decode_name(msg) + "\n")

            
    total = f"\nTotal number of applications received: {num_of_apps}\n"
    file.write(total)

    file.close()
    
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some number of emails.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--resume", action="store_true",          # action = "store_true" means if this flag is present, the value is True
                       help="Resume fetching emails from last UID")
    group.add_argument("--last", type=int,
                       help="Fetch the last N emails from inbox")

    args = parser.parse_args()
    main(resume=args.resume, last_n=args.last)    
        







    # predefined_sets = [set(["thanks","thank"]), set(["apply","applying","application"])]



    # with open("sample.txt", "r") as file:
    #     content = file.read().lower().split()
    #     new_content = [word.strip() for word in content]
    #     set(new_content)
 
    # isConfirmation = True
    # for elem in predefined_sets:
    #     if not (any(word in new_content for word in elem)):
    #         isConfirmation = False
    #         break

    # print(isConfirmation)



        # body = ""
    # if msg.is_multipart():
    #     for part in msg.walk():
    #         if part.get_content_type() == "text/plain":
    #             body += part.get_payload(decode=True).decode(errors="ignore")
    # else:
    #     body = msg.get_payload(decode=True).decode(errors="ignore")


    # print(body)