import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from pymongo.mongo_client import MongoClient

# Put this in config file ??
TOKEN = os.environ["TELE_TOKEN"]
DB_SECRET = os.environ["DB_SECRET"]
CHAT_IDS = os.environ["IDS"].split(',')
BASE_URL = "https://hvr-amazon.my.site.com/BBIndex"
COUNTRY_CODE = "CA"
STATE_CODE = "ON"

def send_alert(loc, desc, link):
    url = f"https://api.telegram.org/bot{TOKEN}"
    for chat_id in CHAT_IDS:
        params = {"chat_id": chat_id, "text": f"Location: {loc}\nJob Description: {desc}\nLink:{link}"}
        r = requests.get(url + "/sendMessage", params=params)

        if r.status_code != 200:
            print("Could not send an alert")
    
def get_payload_for_post_req():
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.content, "html.parser")
    hidden_attrs = soup.find_all("input", attrs={"type": "hidden"})

    payload = {
        "j_id0:portId:j_id67:Country": COUNTRY_CODE,
        "j_id0:portId:j_id67:State": STATE_CODE,
        "j_id0:portId:j_id67:City": "",
        "j_id0:portId:j_id67:j_id78": "j_id0:portId:j_id67:j_id78" # filter job button
    }
    for attr in hidden_attrs:
        payload[attr["name"]] = attr["value"]

    return payload

def check_for_job_and_send_alert(use_db, local_job_array):
    payload = get_payload_for_post_req()
    response = requests.post(BASE_URL, data=payload)
    soup = BeautifulSoup(response.content, "html.parser")
    listings = soup.find_all("div", attrs={"class": "listing row"})

    if use_db:
        password = quote_plus(DB_SECRET)
        uri = f"mongodb+srv://karpit:{password}@cluster0.xi7lz9a.mongodb.net/?retryWrites=true&w=majority"
        client = MongoClient(uri)
        db = client["job_alert_amzn"]
        collection = db["alert"]

    if listings:

        if len(listings) < 10: 
            current_job_ids = []
            for listing in listings:
                current_job_ids.append(listing.find("strong").text)
            
            if use_db:
                data = list(collection.find())

                for dic in list(data):
                    if dic["job_id"] not in current_job_ids:
                        collection.delete_one({"job_id": dic["job_id"]})
                        data.remove(dic)
            else:
                for dic in list(local_job_array):
                    if dic["job_id"] not in current_job_ids:
                        local_job_array.remove(dic)

            for listing in listings:

                job_desc = listing.find("a").text
                job_location = listing.find("span").text
                job_id = listing.find("strong").text
                job_link = BASE_URL.replace("/BBIndex", "") + listing.find("a")["href"]
                
                if use_db:
                    if not any(dic["job_id"] == job_id for dic in data):
                        collection.insert_one({"job_id": job_id,
                                            "job_desc": job_desc,
                                            "location": job_location,
                                            "link": job_link
                                            })                
                        send_alert(job_location, job_desc, job_link)
                else:
                    if not any(dic["job_id"] == job_id for dic in local_job_array):
                        local_job_array.append({"job_id": job_id,
                                            "job_desc": job_desc,
                                            "location": job_location,
                                            "link": job_link
                                            })                
                        send_alert(job_location, job_desc, job_link)

            if use_db:
                client.close()
    else:
        if use_db:
            collection.delete_many({})
        else:
            local_job_array = []

def main():
    check_for_job_and_send_alert(use_db=True, local_job_array=[])
        
if __name__ == "__main__":
    main()
