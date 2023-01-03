import time
import utilities.game_launcher as launcher
from pathlib import Path

import utilities.api.item_ids as ids
import utilities.color as clr
import utilities.random_util as rd
from model.osrs.osrs_bot import OSRSBot
from model.runelite_bot import BotStatus
from utilities.api.morg_http_client import MorgHTTPSocket
from utilities.api.status_socket import StatusSocket
from utilities.geometry import RuneLiteObject
import pyautogui as pag


class OSRSWoodcutter2(OSRSBot,launcher.Launchable):
    def __init__(self):
        bot_title = "Woodcutter2"
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

    def launch_game(self):
        """
        Since this bot inherits from launcher.Launchable, it must implement this method. This method is called when the user clicks the "Launch Game" button.
        The launcher utility has a function that will launch RuneLite with custom settings. This is useful for bots that require lots of setup to run (E.g., minigames, agility, etc.).
        """

        settings_path = Path(__file__).parent.joinpath("testing.properties")
        launcher.launch_runelite_with_settings(bot=self, settings_file=settings_path)

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
            # toggle run when above 30%

                

            if rd.random_chance(probability=0.05) and self.take_breaks:
                self.take_break(max_seconds=15)

            # 2% chance to drop logs early
            if rd.random_chance(probability=0.12):
                self.camera_rotate(40)

            # If inventory is full, bank
            if self.api_s.get_is_inv_full():
                self.drop_selected_items(ids.LOGS)
                self.set_compass_north()
                time.sleep(0.5)
                pag.keyDown('up')
                time.sleep(1)
                pag.keyDown('up')

                if not self.green_tile():
                    self.purple_tile() and self.mouseover_text(contains="Walk")
                    time.sleep(3)

                self.green_tile() and self.mouseover_text(contains="Walk")
                time.sleep(6)

                self.blue_tile() and self.mouseover_text(contains="Walk")
                time.sleep(8)



                #interacting with bank
                self.banker() and self.mouseover_text(contains="Bank")
                time.sleep(4.5)
                self.mouse.move_to(self.win.inventory_slots[3].random_point())
                self.mouse.click()
                time.sleep(2)
                pag.press('esc')
                time.sleep(2)

                #walking back to tree

                self.blue_tile() and self.mouseover_text(contains="Walk")
                time.sleep(4)

                self.green_tile() and self.mouseover_text(contains="Walk")
                time.sleep(8)

                

            # If our mouse isn't hovering over a tree, and we can't find another tree...
            if not self.mouseover_text(contains="Chop") and not self.__move_mouse_to_nearest_tree():
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
            if not self.mouseover_text(contains="Chop"):
                continue
            self.mouse.click()
            time.sleep(0.5)

            # While the player is chopping (or moving), wait
            while not self.api_m.get_is_player_idle():
                # Every second there is a 10% chance to move the mouse to the next tree
                if rd.random_chance(probability=0.10):
                    self.__move_mouse_to_nearest_tree(next_nearest=True, mouseSpeed="slow")
                time.sleep(1)

            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.set_status(BotStatus.STOPPED)

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

    def __drop_logs(self):
        """
        Private function for dropping logs. This code is used in multiple places, so it's been abstracted.
        Since we made the `api` and `logs` variables assigned to `self`, we can access them from this function.
        """
        slots = self.api_s.get_inv_item_indices(ids.logs)
        self.drop(slots)
        self.logs += len(slots)
        self.log_msg(f"Logs cut: ~{self.logs}")
        time.sleep(1)

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
        return True  

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