import json

import selenium.common.exceptions
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC


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


class GameBot:

    def __init__(self, driver: webdriver, iframe_game_css_selector: str, game_buttons_css_selectors: dict,
                 race_css_selectors: dict):
        self.ARCADEMICS_GRAND_PRIX_URL = "https://www.arcademics.com/games/grand-prix"
        self.driver: webdriver = driver
        self.iframe_game_css_selector = iframe_game_css_selector
        self.game_buttons_css_selectors = game_buttons_css_selectors
        self.race_css_selectors = race_css_selectors

    def _wait_for_race_to_start(self) -> None:
        """
        here, we basically wait for a question css selector to be visible
        """
        print("Waiting for you to be in a race...")
        WebDriverWait(self.driver, 20).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, self.race_css_selectors["question"])))
        print("The race has begun!")

    def _autoclick_answers_during_race(self):
        # if question remains the same: the race is over
        while True:
            question_elem = self.driver.find_element(By.CSS_SELECTOR, self.race_css_selectors["question"])
            question = question_elem.text.replace('×', '*')

            result = eval(question)
            for answer_box_css_selector in self.race_css_selectors["answers"].values():
                answer_box_elem = self.driver.find_element(By.CSS_SELECTOR, answer_box_css_selector)
                answer = int(answer_box_elem.text)
                # if the answer of the current box is the same as the result we calculated before
                if answer == result:
                    btn_elem_selector = answer_box_css_selector.replace(' > text:nth-child(3)', '')
                    btn_elem = self.driver.find_element(By.CSS_SELECTOR, btn_elem_selector)
                    question_number_before_click = int(
                        self.driver.find_element(By.CSS_SELECTOR, self.race_css_selectors["question_number"]).text)
                    btn_elem.click()
                    question_number_after_click = int(
                        self.driver.find_element(By.CSS_SELECTOR, self.race_css_selectors["question_number"]).text)
                    if question_number_before_click == question_number_after_click:
                        print("game is over, we WON")
                        return
                    break

    def _auto_click_to_race_from_main_menu(self):
        # click through all btns to start a game
        for btn_css_selector in self.game_buttons_css_selectors.values():
            btn = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, btn_css_selector)))
            btn.click()

    def _wait_for_game_lobby(self):
        print("Waiting for you to be in a game lobby...")
        try:
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.game_buttons_css_selectors["start_btn"])))
        except TimeoutException:
            raise TimeoutException("You weren't in a game lobby within 30 seconds!")

        print("We're in a game lobby!")

    def open_menu(self):
        self.driver.get(self.ARCADEMICS_GRAND_PRIX_URL)
        WebDriverWait(self.driver, 20).until(EC.frame_to_be_available_and_switch_to_it(
            (By.CSS_SELECTOR, self.iframe_game_css_selector)))
        print("Let's start a race!")
        possible_choices = ["1", "2", "3"]

        choice = None

        while choice not in possible_choices:
            print(
                "What would you like?\n"
                "1. AFK autoplay from Multiplayer Lobby\n"
                "2. Autoplay when game is joined or hosted\n"
                "3. Let the bot take over when ENTER is pressed")
            choice = input("Choice: ")
            if choice not in possible_choices:
                print("You didn't choose a valid option, let's try again!")
                continue

            if choice == "1":
                self._auto_click_to_race_from_main_menu()
            elif choice == "2":
                self._wait_for_game_lobby()
            elif choice == "3":
                input("Press ENTER to start the bot!")

            self._wait_for_race_to_start()
            self._autoclick_answers_during_race()


def create_gamebot_instance():
    driver = start_webdriver()

    with open("css_selectors.json") as f:
        game_css_selectors = json.load(f)

    iframe_css_selector = game_css_selectors["iframe_game"]
    game_buttons_css_selectors = game_css_selectors["buttons"]
    race_question_and_answers_css_selectors = game_css_selectors["boxes"]

    return GameBot(driver, iframe_css_selector, game_buttons_css_selectors, race_question_and_answers_css_selectors)


if __name__ == '__main__':
    bot = create_gamebot_instance()
    bot.open_menu()
