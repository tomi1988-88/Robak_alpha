from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import geckodriver_autoinstaller
from time import sleep, perf_counter
from datetime import datetime
from bs4 import BeautifulSoup
from disable_functions import disable_images, disable_javascript
from support_functions import price_into_number, input_validator
from os import getcwd, mkdir
from os.path import join, exists
from selenium.common.exceptions import WebDriverException
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count


# Wariant no 1:
# z kategorii produktów sciaga:
# dane z tabeli: nazwa, kod produktu, ceny (nawet 3), href
# zapisuje html
# blokuje obrazki, javascript

# Arguments from config file

PATH = "config.txt"
DATA = input_validator(PATH)
PROJECT_TITLE = DATA.get("project_title")

# user agent: https://stackoverflow.com/questions/29916054/change-user-agent-for-selenium-web-driver


class Category:
    not_price_args = ['category', 'initial_link', 'n_pages', 'offer_boxes', 'title', 'href',
                      'is_available', 'wrong_bytes']

    labels = ["start time", "page", "ind", "n_rows_on_page", 'title', 'href', 'is_available']

    def __init__(self, project_title, dic):
        self.project_tile = project_title
        self.category = dic.get("category")
        self.initial_link = dic.get("initial_link")
        self.n_pages = dic.get("n_pages").replace(" ", ".")
        self.offer_boxes = dic.get("offer_boxes").replace(" ", ".")
        self.title = dic.get("title").replace(" ", ".")
        self.href = dic.get("href").replace(" ", ".")
        self.is_available = dic.get("is_available").replace(" ", ".")
        self.wrong_bytes = dic.get("wrong_bytes").split()

        prices = [dic.get(x) for x in dic if x not in Category.not_price_args]

        self.prices = [price[price.index(" "):].strip().replace(" ", ".") for price in prices]
        self.labels = Category.labels + [price[:price.index(" ")].strip() for price in prices]

    def __driver_init(self):
        geckodriver_autoinstaller.install()
        options = FirefoxOptions()
        options.add_argument("--headless")

        self.driver = webdriver.Firefox(options=options)

        disable_images(self.driver)
        disable_javascript(self.driver)
        self.driver.implicitly_wait(10)

        return self.driver

    def __create_tree(self):

        cwd = getcwd()
        self.project_dir = join(cwd, self.project_tile)

        if not exists(self.project_dir):
            mkdir(self.project_dir)

        self.category_dir = join(self.project_dir, self.category)

        if not exists(self.category_dir):
            mkdir(self.category_dir)

    def __extract_data(self, soup):
        # https://stackoverflow.com/questions/49118209/beautifulsoup-how-to-find-a-specific-class-name-alone
        # https://stackoverflow.com/questions/18725760/beautifulsoup-findall-given-multiple-classes
        offer_boxes = soup.select(self.offer_boxes)
        title = [box.select_one(self.title).text.strip() for box in offer_boxes]
        href = [box.select_one(self.href).get("href") for box in offer_boxes]
        is_available = [True if box.select_one(self.is_available) else False for box in offer_boxes]
        prices = [[box.select_one(price) for price in self.prices] for box in offer_boxes]
        prices = [[price_into_number(tag.text) if tag else None for tag in price_list] for price_list in prices]

        rows = []
        for i, tit in enumerate(title):
            rows.append([tit, href[i], is_available[i]] + prices[i])

        # https://stackoverflow.com/questions/12897374/get-unique-values-from-a-list-in-python
        rows_to_return = []
        for i in rows:
            rows_to_return.append(i) if i not in rows_to_return else None

        rows_to_return = [";".join([str(e) for e in row]) for row in rows_to_return]

        return rows_to_return

    def run(self):
        self.driver = self.__driver_init()
        self.driver.get(self.initial_link.replace("$$$", "1"))

        # print(self.initial_link)

        self.soup = BeautifulSoup(self.driver.page_source, "lxml")

        # tutaj to wywalić do funkcji

        n_pages_int = self.soup.select_one(self.n_pages).text
        n_pages_int = int("".join([c for c in n_pages_int if c.isdigit()]))
        print(n_pages_int)
        # n_pages_int = 2
        start_time = datetime.today().strftime("%d %m %Y _ %H %M %S")

        self.__create_tree()
        # print(self.initial_link)
        for page in range(1, n_pages_int + 1):
            link = self.initial_link.replace("$$$", str(page))
            # print(link)
            try:
                self.driver.get(link)
                self.soup = BeautifulSoup(self.driver.page_source, "lxml")

            except WebDriverException as e:
                # https://stackoverflow.com/questions/49734915/failed-to-decode-response-from-marionette-message-in-python-firefox-headless-s
                # https://stackoverflow.com/questions/58544316/selenium-failed-to-decode-response-from-marionette
                print(e, self.category, page, "self.driver.service.process:", self.driver.service.process)
                sleep(3)
                self.driver.get(link)
                print(e, self.category, page, "self.driver.get(link) - wykonane", "self.driver.service.process:", self.driver.service.process)
                sleep(3)
                self.soup = BeautifulSoup(self.driver.page_source, "lxml")
                print(e, self.category, page, 'self.soup = BeautifulSoup(self.driver.page_source, "lxml") - wykonane')
                # jeżeli to nie będzie szło dalej to będzie tutaj trzeba "odnowić proces",
                # czyli np. przebudować w ten sposob, że w petli for wywoływana będzie funkcja run_internal(page_num).
                # Napotkane błędy:
                # Message: WebDriver session does not exist, or is not active
                # Message: Failed to decode response from marionette
                # Message: TypeError: browsingContext.currentWindowGlobal is null

            pretty = self.soup.prettify()

            if self.wrong_bytes:
                for i in self.wrong_bytes:
                    pretty = pretty.replace(i, "")

            ## zrobić __create_tree i tutaj pakować od razu do folderu
            with open(join(self.category_dir, f"{self.category}_{start_time}_{page}.html"), 'w', encoding='utf-8') as f:
                f.write(pretty)

            rows = self.__extract_data(self.soup)

            n_rows_on_page = len(rows)

            with open(join(self.category_dir, f"{self.category}.txt"), "a", encoding="utf-8") as results:
                for ind, row in enumerate(rows, start=1):
                    results.writelines(f"{start_time[:10].replace(' ','.')};{start_time[13:].replace(' ',':')};{page};{ind};{n_rows_on_page};{row};\n")

        self.driver.quit()


class RunOperator:
    def __init__(self, lst_of_categories, n_rounds, frequency):
        self.categories = lst_of_categories
        self.n_rounds = n_rounds    # liczbę rund przerzucić do Categories i tam zrobić Internal Run w Run
        self.frequency = frequency
        self.cpu_cores = cpu_count() if cpu_count() < len(categories) else len(categories)

    def main_run(self):
        for num in range(self.n_rounds):
            print(datetime.now())
            start_round = perf_counter()

            with ThreadPoolExecutor(max_workers=self.cpu_cores) as executor:
                executor.map(lambda x: x.run(), self.categories)

            end_round = perf_counter()
            delta_round = end_round - start_round

            print(num, " - zrobiony obrót, czas", delta_round)
            print(datetime.now())
            if delta_round < self.frequency * 3600:
                sleep(self.frequency * 3600 - delta_round)
            else:
                sleep(600)


if __name__ == "__main__":
    print(len(DATA), DATA.keys())
    categories = [Category(PROJECT_TITLE, DATA[i]) for i in range(len(DATA) - 1)]

    # cpu_cores = cpu_count() if cpu_count() < len(categories) else len(categories)

    n_rounds = 8
    frequency = 2

    print("start ", datetime.now())

    RUN_OPERATOR = RunOperator(categories, n_rounds, frequency)
    RUN_OPERATOR.main_run()

    print("end ", datetime.now())

    # counter = 4
    # while True:
        # if counter > 0:
        #     print("zostało obrotów", counter)
        #     sleep(3 * 3600)
        # else:
        #     break

        # start_round = perf_counter()
        # print(start_round)

        # for cat in categories:
        #     cat.run()

        # with ThreadPoolExecutor(max_workers=cpu_cores) as executor:
        #     executor.map(lambda x: x.run(), categories)

        # end_round = perf_counter()
        # print("end", end_round - start_round)
        #
        # counter -= 1
        # if counter > 0:
        #     print("zostało obrotów", counter)
        #     sleep(3 * 3600)
        # else:
        #     break


# test_page = 1          # oznaczyć jako test_page i zachować później by użytkownik mógł wstawić wartość 1 lub 2 aby testować
#
# start_time = datetime.today().strftime("%d %m %Y")
# # offer_boxes_location = {"class": "offer-box"} # to będzie do poprawienia
# for page in range(1, test_page + 1):
#     link = f"{link_initial[:-1]}{page}"
#
#     driver.get(link)
#
#     soup = BeautifulSoup(driver.page_source, "html.parser")
#
#     pretty = soup.prettify()
#     pretty = pretty.replace('\u2b50', '').replace('\u27a4', '').replace('\u202f', '')

    # offer_boxes = soup.find_all("div", offer_boxes_location)
    # offer_boxes = soup.find_all(lambda tag: tag.name == 'div' and tag.get('class') == ["offer-box"])
    # offer_boxes = soup.select("div.offer-box")      # sciąga 31 obiektów bo 1 gałąź zawiera w sobie
    # wszystkie pozostałe - można ją odrzucić na końcu

    # title = [box.select_one("a.is-animate.spark-link").text.strip() for box in offer_boxes]
    # href = [box.select_one("a.is-animate.spark-link").get("href") for box in offer_boxes]
    # is_available = [True if box.select_one("div.offer-available") else False for box in offer_boxes]
    #
    # omnibus_branch = [box.select_one("span.omnibus.omnibus-price.is-regular.omnibus.is-mobile.is-small") for box in offer_boxes]
    # old_price_branch = [box.select_one("div.old-price") for box in offer_boxes]
    # main_price_branch = [box.select_one("div.main-price.is-big") for box in offer_boxes]
    # regular_price_branch = [box.select_one("div.main-price.price-regular") for box in offer_boxes]
    # code_price_branch = [box.select_one("div.main-price.for-action-price") for box in offer_boxes]
    #
    # # omnibus_prices = [price_into_number(tag.select_one("span.whole-price").text) if tag else None for tag in omnibus_branch]
    # omnibus_prices = [price_into_number(tag.text) if tag else None for tag in omnibus_branch]
    # old_prices = [price_into_number(tag.text) if tag else None for tag in old_price_branch]
    # main_prices = [price_into_number(tag.text) if tag else None for tag in main_price_branch]
    # regular_prices = [price_into_number(tag.text) if tag else None for tag in regular_price_branch]
    # code_prices = [price_into_number(tag.text) if tag else None for tag in code_price_branch]
    #
    # # zipper = list(zip(title, href, is_available, omnibus_prices, old_prices, main_prices, regular_prices, code_prices))
    # #                   # , old_price_branch, main_price_branch, regular_price_branch, code_price_branch))
    # zipper = list(zip(title, omnibus_branch, omnibus_prices))
    # print(len(zipper))
    # for i in zipper:
    #     # print(len(i))
    #     for j in i:
    #         print(j)



    # td = soup.find_all("td")

    # h2 = [box.find("h2").text.strip() for box in offer_boxes]
    # is_available = [True if box.find("div", "offer-available") else False for box in offer_boxes]
    # omnibus_branches = [box.find("span", "omnibus-price") for box in offer_boxes]
    # old_price_branch = [box.find("div", "old-price") for box in offer_boxes]
    # main_price_branch = [box.find(lambda tag: tag.name == "div" and tag.get("class") == ["main-price", "is-big"]) for box in offer_boxes]
    # regular_price_branch = [box.find(lambda tag: tag.name == "div" and tag.get("class") == ["main-price", "price-regular"]) for box in offer_boxes]
    # code_price_branch = [box.find("div", "for-action-price") for box in offer_boxes]

    # print(len(h2), h2)
    # prod_names = [x.text.strip() for x in h2]
    # print(len(prod_names))
    # prod_hrefs = [x.find("a")["href"] for x in h2]
    # print(len(prod_hrefs))

    # div_with_offers = soup.find_all("div", {"class": "offer-available"})
    # print(len(div_with_offers))
    ### tutaj należy rozbić na warianty:
    ### bez promo
    ### promo z kodem
    ### promo
    ### promo + promo z kodem
    ### + cena omnibus
    # wyszukiwanie przez td

