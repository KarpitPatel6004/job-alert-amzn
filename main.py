import os
import time
import random
import requests
from selenium import webdriver
from urllib.parse import quote_plus
from pymongo.mongo_client import MongoClient
from selenium.webdriver.common.by import By

MAX_SLEEP_TIME = 3.5*60
TOKEN = os.environ["TELE_TOKEN"]
DB_SECRET = os.environ["DB_SECRET"]
CHAT_IDS = os.environ["IDS"].split(',')

def search(driver):
    driver.get("https://hvr-amazon.my.site.com/")
    driver.find_element(by=By.CLASS_NAME, value="accordion-toggle").click()
    time.sleep(random.randint(1,3) + random.random())
    driver.find_element(by=By.XPATH, value="//option[@value='CA' and contains(.,'Canada')]").click()
    time.sleep(random.randint(1,3) + random.random())
    driver.find_element(by=By.XPATH, value="//option[@value='ON' and contains(.,'Ontario')]").click()
    time.sleep(random.randint(1,3) + random.random())
    element = driver.find_element(by=By.XPATH, value="//input[@type='submit' and @value='Filter Jobs']")
    driver.execute_script("arguments[0].scrollIntoView();", element)
    time.sleep(random.randint(1,3) + random.random())
    element.click()

def send_alert(loc, desc):
    url = f"https://api.telegram.org/bot{TOKEN}"
    print(url)
    for chat_id in CHAT_IDS:
        params = {"chat_id": chat_id, "text": f"Location: {loc}\nJob Description: {desc}"}
        r = requests.get(url + "/sendMessage", params=params)

        if r.status_code != 200:
            print(r.json())
            print("Could not send an alert")

password = quote_plus(DB_SECRET)
uri = f"mongodb+srv://karpit:{password}@cluster0.xi7lz9a.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client["job_alert_amzn"]
collection = db["alert"]

data = list(collection.find())
for dic in data:
    send_alert(dic["location"], dic["job_desc"])
    

def check_for_job_and_send_alert(driver):
    elements = driver.find_elements(by=By.CLASS_NAME, value="listing")
    
    if elements:

        password = quote_plus(DB_SECRET)
        uri = f"mongodb+srv://karpit:{password}@cluster0.xi7lz9a.mongodb.net/?retryWrites=true&w=majority"
        client = MongoClient(uri)
        db = client["job_alert_amzn"]
        collection = db["alert"]

        current_job_ids = []
        for element in elements:
            current_job_ids.append(element.text.split("\n")[2].split(":")[-1].strip())
        
        data = list(collection.find())

        for dic in list(data):
            if dic["job_id"] not in current_job_ids:
                collection.delete_one({"job_id": dic["job_id"]})
                data.remove(dic)      
        
        for element in elements:

            job_desc = element.text.split("\n")[0]
            job_location = element.text.split("\n")[1]
            job_id = element.text.split("\n")[2].split(":")[-1].strip()
    
            if not any(dic["job_id"] == job_id for dic in data):
                collection.insert_one({"job_id": job_id,
                                       "job_desc": job_desc,
                                       "location": job_location
                                       })                
                send_alert(job_location, job_desc)

        client.close()


def main():

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(options=options)
    
    search(driver)
    time.sleep(random.randint(1,3) + random.random())
    check_for_job_and_send_alert(driver)
    driver.quit()
        

if __name__ == "__main__":
    # time.sleep(random.randint(1, MAX_SLEEP_TIME))
    main()
