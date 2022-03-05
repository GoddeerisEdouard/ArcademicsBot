import json
from typing import List
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


def load_game_data_selectors() -> dict:
    with open("css_selectors.json") as f:
        css_selectors_json = json.load(f)
    return css_selectors_json


def start_webdriver() -> webdriver:
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager(log_level=0).install()), options=options)

    # we need to act as if we're not a bot, else Cloudflare will not load the game
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )
    return driver


def start_up_game(driver: webdriver, game_iframe_css_selector: str, button_css_selectors: List[str]) -> None:
    driver.get("https://www.arcademics.com/games/grand-prix")
    WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it(
        (By.CSS_SELECTOR, game_iframe_css_selector)))
    # click through all btns to start a game
    for btn_css_selector in button_css_selectors:
        btn = WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, btn_css_selector)))
        btn.click()


def calculate_answers(driver: webdriver, questionbox_css_selector: str, answer_boxes_css_selectors: List[str]) -> None:
    # if question remains the same: the race is over
    previous_question = ""
    while True:
        question_elem = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, questionbox_css_selector)))
        question = question_elem.text.replace('×', '*')
        if question == previous_question:
            print("game is over, we WON")
            break
        previous_question = question
        result = eval(question)
        for answer_box_css_selector in answer_boxes_css_selectors:
            answer_box_elem = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, answer_box_css_selector)))
            answer = int(answer_box_elem.text)
            # if the answer of the current box is the same as the result we calculated before
            if answer == result:
                btn_elem_selector = answer_box_css_selector.replace(' > text:nth-child(3)', '')
                btn_elem = WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, btn_elem_selector)))
                btn_elem.click()
                break


if __name__ == '__main__':
    css_selectors = load_game_data_selectors()
    driver = start_webdriver()
    print("Let's RACE BABY!")
    start_up_game(driver, css_selectors['iframe_game'], css_selectors['buttons'].values())
    calculate_answers(driver, css_selectors['boxes']["question"], css_selectors['boxes']['answers'].values())
