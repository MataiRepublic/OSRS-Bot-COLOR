import time

import utilities.api.item_ids as item_ids
import utilities.color as clr
from model.bot import BotStatus
from model.osrs.osrs_bot import OSRSBot
from utilities.api.morg_http_client import MorgHTTPSocket
from utilities.api.status_socket import StatusSocket
from utilities.geometry import RuneLiteObject
import pyautogui as pag
import utilities.random_util as rd


class OSRStester(OSRSBot):
    def __init__(self):
        bot_title = "miner"
        description = "This bot power-chops wood. Position your character near some trees, tag them, and press the play button."
        super().__init__(bot_title=bot_title, description=description)
        self.running_time = 1
        self.take_breaks = False

    def create_options(self):
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 500)
        self.options_builder.add_checkbox_option("take_breaks", "Take breaks?", [" "])

    def save_options(self, options: dict):
        for option in options:
            if option == "running_time":
                self.running_time = options[option]
            elif option == "take_breaks":
                self.take_breaks = options[option] != []
            else:
                self.log_msg(f"Unknown option: {option}")
                print("Developer: ensure that the option keys are correct, and that options are being unpacked correctly.")
                self.options_set = False
                return
        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg(f"Bot will{' ' if self.take_breaks else ' not '}take breaks.")
        self.log_msg("Options set successfully.")
        self.options_set = True

    def main_loop(self):
        # Setup API
        self.api_m = MorgHTTPSocket()
        self.api_s = StatusSocket()

        self.log_msg("Selecting inventory...")
        self.mouse.move_to(self.win.cp_tabs[3].random_point())
        self.mouse.click()

        self.logs = 0
        failed_searches = 0

        # Main loop
        start_time = time.time()
        end_time = self.running_time * 60
        while time.time() - start_time < end_time:

        # 5% chance to take a break between clicks
            if rd.random_chance(probability=0.05) and self.take_breaks:
                self.take_break(max_seconds=15)

        # If inventory is full, drop logs
            if self.api_s.get_is_inv_full():
                self.set_compass_north()
                pag.keyDown('up')
                time.sleep(1)
                pag.keyDown('up')
    
                self.walker()    
                self.walker()
                self.walker()
                self.walker()
                self.walker()
                self.walker()
                self.walker()

                self.green_tile()
                time.sleep(2)

                self.banker()
                time.sleep(3)
                self.mouse.move_to(self.win.inventory_slots[3].random_point())
                self.mouse.click()
                time.sleep(2)
                pag.press('esc')
                time.sleep(2)

                self.green_tile()
                self.walker_inverse()
                self.walker_inverse()
                self.walker_inverse()
                self.walker_inverse()
                self.walker_inverse()
                self.walker_inverse()
                self.walker_inverse()
                    



            # 20% chance to rotate camera
            if rd.random_chance(probability=0.20):
                self.camera_rotate(47)

            # 20% chance to rotate camera
            if rd.random_chance(probability=0.10):
                self.camera_rotate(90)



            # If our mouse isn't hovering over a tree, and we can't find another tree...
            if not self.mouseover_text(contains="Mine") and not self.__move_mouse_to_nearest_tree():
                failed_searches += 1
                if failed_searches % 10 == 0:
                    self.log_msg("Searching for trees...")
                if failed_searches > 60:
                    # If we've been searching for a whole minute...
                    self.__logout("No tagged trees found. Logging out.")
                    return
                time.sleep(1)
                continue
            failed_searches = 0  # If code got here, a tree was found

            # Click if the mouseover text assures us we're clicking a tree
            if not self.mouseover_text(contains="Mine"):
                continue
            if self.__move_mouse_to_nearest_tree() and self.mouseover_text(contains="Mine"):       
                self.mouse.click()
                time.sleep(0.5)
                


            # While the player is chopping (or moving), wait
            while not self.api_m.get_is_player_idle():
                # Every second there is a 10% chance to move the mouse to the next tree
                if rd.random_chance(probability=0.5):
                    self.__move_mouse_to_nearest_tree(next_nearest=True, mouseSpeed="slow")
                time.sleep(0.5)

            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")

    def banker(self, next_nearest=False, mouseSpeed="medium"):

        trees = self.get_all_tagged_in_rect(self.win.game_view, clr.PINK)
        tree = None
        if not trees:
            return False
        # If we are looking for the next nearest tree, we need to make sure trees has at least 2 elements
        if next_nearest and len(trees) < 2:
            return False
        trees = sorted(trees, key=RuneLiteObject.distance_from_rect_center)
        tree = trees[1] if next_nearest else trees[0]
        self.mouse.move_to(tree.random_point(), mouseSpeed=mouseSpeed)
        self.mouse.click()
        return True

    def __move_mouse_to_nearest_tree(self, next_nearest=False, mouseSpeed="medium"):
        """
        Locates the nearest tree and moves the mouse to it. This code is used multiple times in this script,
        so it's been abstracted into a function.
        Args:
            next_nearest: If True, will move the mouse to the second nearest tree. If False, will move the mouse to the
                          nearest tree.
            mouseSpeed: The speed at which the mouse will move to the tree. See MouseUtil for options.
        Returns:
            True if success, False otherwise.
        """
        trees = self.get_all_tagged_in_rect(self.win.game_view, clr.PINK)
        tree = None
        if not trees:
            return False
        # If we are looking for the next nearest tree, we need to make sure trees has at least 2 elements
        if next_nearest and len(trees) < 2:
            return False
        trees = sorted(trees, key=RuneLiteObject.distance_from_rect_center)
        tree = trees[1] if next_nearest else trees[0]
        self.mouse.move_to(tree.random_point(), mouseSpeed=mouseSpeed)
        return True

    def walker_inverse(self):
        self.purple_tile()
        self.blue_tile()
        self.green_tile()    


    def walker(self):
        if self.green_tile() and self.mouseover_text(contains="Walk"):
            pass
        if self.blue_tile() and self.mouseover_text(contains="Walk"):
            pass
        if self.purple_tile() and self.mouseover_text(contains="Walk"):
            pass
    def green_tile(self, next_nearest=False, mouseSpeed="medium"):

        trees = self.get_all_tagged_in_rect(self.win.game_view, clr.GREEN)
        tree = None
        if not trees:
            return False
        # If we are looking for the next nearest tree, we need to make sure trees has at least 2 elements
        if next_nearest and len(trees) < 2:
            return False
        trees = sorted(trees, key=RuneLiteObject.distance_from_rect_center)
        tree = trees[1] if next_nearest else trees[0]
        self.mouse.move_to(tree.random_point(), mouseSpeed=mouseSpeed)
        self.mouse.click()
        time.sleep(6)
        return True

    def blue_tile(self, next_nearest=False, mouseSpeed="medium"):

        trees = self.get_all_tagged_in_rect(self.win.game_view, clr.BLUE)
        tree = None
        if not trees:
            return False
        # If we are looking for the next nearest tree, we need to make sure trees has at least 2 elements
        if next_nearest and len(trees) < 2:
            return False
        trees = sorted(trees, key=RuneLiteObject.distance_from_rect_center)
        tree = trees[1] if next_nearest else trees[0]
        self.mouse.move_to(tree.random_point(), mouseSpeed=mouseSpeed)
        self.mouse.click()
        time.sleep(6)
        return True

    def purple_tile(self, next_nearest=False, mouseSpeed="medium"):

        trees = self.get_all_tagged_in_rect(self.win.game_view, clr.PURPLE)
        tree = None
        if not trees:
            return False
        # If we are looking for the next nearest tree, we need to make sure trees has at least 2 elements
        if next_nearest and len(trees) < 2:
            return False
        trees = sorted(trees, key=RuneLiteObject.distance_from_rect_center)
        tree = trees[1] if next_nearest else trees[0]
        self.mouse.move_to(tree.random_point(), mouseSpeed=mouseSpeed)
        self.mouse.click()
        time.sleep(6)
        return True




    def __eat(self, api: StatusSocket):
        self.log_msg("HP is low.")
        food_slots = api.get_inv_item_indices(item_ids.all_food)
        if len(food_slots) == 0:
            self.log_msg("No food found. Pls tell me what to do...")
            self.set_status(BotStatus.STOPPED)
            return
        self.log_msg("Eating food...")
        self.mouse.move_to(self.win.inventory_slots[food_slots[0]].random_point())
        self.mouse.click()
