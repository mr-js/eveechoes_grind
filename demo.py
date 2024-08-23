import cv2
import numpy as np
from PIL import ImageGrab
import pyautogui
import pygetwindow as gw
import time
import os
import logging


logging.basicConfig(
    handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'{__name__}.log', 'w', 'utf-8')
            ],
    format='%(asctime)s %(levelname)s %(message)s [%(funcName)s]',
    datefmt='%Y.%m.%d %H:%M:%S',
    level=logging.DEBUG
    )    
log = logging.getLogger(__name__)


def capture_screen():
    screen = ImageGrab.grab()
    screen_np = np.array(screen)
    screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_BGR2GRAY)
    return screen_gray, screen_np.shape[1], screen_np.shape[0]


def load_template(template_path):
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        raise ValueError(f"Template image at path {template_path} could not be loaded.")
    return template


def resize_image(image, max_width, max_height):
    h, w = image.shape[:2]
    if w > max_width or h > max_height:
        scaling_factor = min(max_width / w, max_height / h)
        new_size = (int(w * scaling_factor), int(h * scaling_factor))
        resized_image = cv2.resize(image, new_size)
        return resized_image
    return image


def is_near_existing_targets(new_coord, targets, search_radius):
    for coord in targets:
        if (abs(new_coord[0] - coord[0]) <= search_radius) and (abs(new_coord[1] - coord[1]) <= search_radius):
            return True
    return False


def scan(scale, threshold, search_radius, borders):
    log.debug('Scaning a targets on screen...')
    screen_gray, screen_width, screen_height = capture_screen()
    target_templates = dict()
    for file in os.listdir('target_templates'):
        target_templates[file] = load_template(os.path.join('target_templates', file))
    all_targets = []
    for target_template in target_templates.keys():
        found_targets = []
        resized_template = cv2.resize(target_templates[target_template], (0, 0), fx=scale, fy=scale)
        if resized_template.shape[0] > screen_gray.shape[0] or resized_template.shape[1] > screen_gray.shape[1]:
            continue
        res = cv2.matchTemplate(screen_gray, resized_template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            top_left = pt
            bottom_right = (top_left[0] + resized_template.shape[1], top_left[1] + resized_template.shape[0])
            cv2.rectangle(screen_gray, top_left, bottom_right, (0, 255, 0), 2)
            bottom_left = (bottom_right[0], top_left[1] + resized_template.shape[0])
            offset_x = -resized_template.shape[0]/2
            offset_y = -resized_template.shape[1]/2
            click_x = int((bottom_left[0] + offset_x) * screen_width / screen_gray.shape[1])
            click_y = int((bottom_left[1] + offset_y) * screen_height / screen_gray.shape[0])
            if borders[0] <= click_x <= (borders[0] + borders[2]) and borders[1] <= click_y <= (borders[1] + borders[3]):
                target = (click_x, click_y)
                if not is_near_existing_targets(target, found_targets, search_radius):
                    found_targets.append(target)
        all_targets.append({target_template: found_targets})

    # DEMO
    # max_display_width = 1920
    # max_display_height = 1080
    # # screen_gray_resized = resize_image(screen_gray, max_display_width, max_display_height)
    # # cv2.imshow('Detected targets', screen_gray_resized)
    # cv2.imshow('Detected targets', screen_gray)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    log.debug(f'Scan completed. Result: {all_targets}')
    return all_targets


def element_click(target):
    log.debug(f'Clicking the target {target}...')
    click_x, click_y = target
    # DEMO
    # pyautogui.moveTo(click_x, click_y)
    # DEMO
    pyautogui.click(click_x, click_y)
    log.debug('Clicked')
    time.sleep(1)


def find_window(windows_title):
    window = None
    log.debug(f'Finding game window "{windows_title}"...')
    if (windows := gw.getWindowsWithTitle(windows_title)):
        window = gw.getWindowsWithTitle(windows_title)[0]
        log.debug(f'Founded')
    else:
        log.critical('Cannot find game window')
    return window


def main():
    scale=1.0
    threshold=0.8
    search_radius = 20
    target_window = 'BlueStacks App Player 1'
    window = find_window(target_window)
    if window and not window.isActive:
        borders=(window.left, window.top, window.width, window.height)
        log.debug('Activating the window...')
        window.activate()
        log.debug('Activated')
        time.sleep(1)
        while True:
            detected_targets = scan(scale, threshold, search_radius, borders)
            if len(detected_targets) > 0:
                if any(list(filter(lambda x: 'button_chat.png' in x and len(x.get('button_chat.png')) > 0, detected_targets))):
                    button_chat_target = list(filter(lambda x: 'button_chat.png' in x and len(x.get('button_chat.png')) > 0, detected_targets))[0].get('button_chat.png')[0]
                    element_click(button_chat_target)
                    log.debug(f'Done')
                    break
            log.debug(f'No detected. Waiting...')
            # DEMO
            # break
            # DEMO
            time.sleep(5)


if __name__ == "__main__":
    main()
