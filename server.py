import time
import main
import random
import logging

local_job_array = []

def start_server():
    logging.info("Server started.")
    while True:

        retry_attempts = 0
        while retry_attempts < 3:
            try:
                main.check_for_job_and_send_alert(use_db=False, local_job_array=local_job_array)
                break
            except Exception as e:
                logging.warning(f"An error occurred: {e}")
                logging.info("Retrying...")
                retry_attempts += 1
                time.sleep(5)
        else:
            logging.error("Maximum retry attempts reached. Skipping this iteration.")

        sleep_interval = random.randint(40, 70)
        time.sleep(sleep_interval)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_server()
