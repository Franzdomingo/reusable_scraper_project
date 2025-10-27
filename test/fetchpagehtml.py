from selenium import webdriver

url = "https://www.kaggle.com/models/ibm-granite/granite-4.0"
driver = webdriver.Chrome()
driver.get(url)

html = driver.page_source
with open("page.html", "w", encoding="utf-8") as f:
    f.write(html)

driver.quit()