from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
import os
import time

os.makedirs("garbage_trucks", exist_ok=True)

driver = webdriver.Chrome()

driver.get("https://www.google.com/search?tbm=isch&q=indian+garbage+truck")

for _ in range(20):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

imgs = driver.find_elements(By.TAG_NAME, "img")

count = 0

for img in imgs:
    src = img.get_attribute("src")

    if src and src.startswith("http"):
        try:
            data = requests.get(src, timeout=10).content
            with open(f"garbage_trucks/{count}.jpg", "wb") as f:
                f.write(data)
            count += 1
        except:
            pass

driver.quit()

print(f"Downloaded {count} images")