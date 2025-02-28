# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service


# options = Options()
# options.headless = True
# options.add_argument("--window-size=1920,1080")

# DRIVER_PATH = "chromedriver-linux64/chromedriver"
# service = Service(executable_path=DRIVER_PATH)
# driver = webdriver.Chrome(service=service, options=options)

# driver.get(
#     "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value=2024"
# )
# html = driver.page_source

# driver.quit()

from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "html.parser")

table = soup.find_all("table", class_="usa-table views-table views-view-table cols-23")
print(table)
