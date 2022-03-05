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


def start_up_game(driver: webdriver, game_iframe_css_selector: str) -> None:
    driver.get("https://www.arcademics.com/games/grand-prix")
    WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it(
        (By.CSS_SELECTOR, game_iframe_css_selector)))


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


def complete_autoplay(driver: webdriver, button_css_selectors: List[str]):
    # click through all btns to start a game
    for btn_css_selector in button_css_selectors:
        btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, btn_css_selector)))
        btn.click()


def play_custom_game(driver: webdriver, start_btn_css_selector: str):
    print("Waiting for you to be in host a custom game...")
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, start_btn_css_selector)))
    print("Start btn located!")
    WebDriverWait(driver, 10).until_not(EC.visibility_of_element_located((By.CSS_SELECTOR, start_btn_css_selector)))
    print("We expect the race will be starting soon!")

def play_on_command():
    input("Press ENTER to start the bot while in a game!")

def race_menu(driver: webdriver, css_selectors: dict):
    print("Let's start a race!")

    choice = None

    while choice not in ["1", "2", "3"]:
        print(
            "What would you like?\n1. Autoplay from Multiplayer Lobby\n2. Play custom game\n3.Start when I press Enter")
        choice = input("Choice: ")

        if choice == "1":
            complete_autoplay(driver, css_selectors["buttons"].values())
            calculate_answers(driver, css_selectors['boxes']["question"], css_selectors['boxes']['answers'].values())
        elif choice == "2":
            play_custom_game(driver, css_selectors["buttons"]["start_btn"])
            calculate_answers(driver, css_selectors['boxes']["question"], css_selectors['boxes']['answers'].values())
        elif choice == "3":
            play_on_command()
            calculate_answers(driver, css_selectors['boxes']["question"], css_selectors['boxes']['answers'].values())
        else:
            print("You didn't choose a valid option, let's try again!")


if __name__ == '__main__':
    css_selectors = load_game_data_selectors()
    driver = start_webdriver()
    start_up_game(driver, css_selectors['iframe_game'])
    race_menu(driver, css_selectors)
