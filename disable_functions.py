

def disable_images(driver):

    driver.implicitly_wait(1)

    driver.get("about:config")
    driver.find_element("id", "warningButton").click()

    search_area = driver.find_element("id", "about-config-search")
    search_area.send_keys("permissions.default.image")

    edit_button = driver.find_element("xpath", "/html/body/table/tr[1]/td[2]/button")
    edit_button.click()

    edit_area = driver.find_element("xpath", "/html/body/table/tr[1]/td[1]/form/input")
    edit_area.send_keys("2")

    save_button = driver.find_element("xpath", "/html/body/table/tr[1]/td[2]/button")
    save_button.click()


def disable_javascript(driver):
    driver.implicitly_wait(1)

    driver.get("about:config")
    driver.find_element("id", "warningButton").click()

    search_area = driver.find_element("id", "about-config-search")
    search_area.send_keys("permissions.default.image")

    toggle_button = driver.find_element("xpath", "/html/body/table/tr/td[2]/button")
    toggle_button.click()

