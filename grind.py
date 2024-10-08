import cv2
import numpy as np
from PIL import ImageGrab, Image
import pyautogui
import pygetwindow as gw
import time
import os
import logging
import timeit
import sys


class GrindEngine():
    def __init__(self, demo=True, debug=False, scale = 1.0, step_by_step=False, windows_title='BlueStacks App Player 1'):
        self.DEMO = demo
        self.DEBUG = debug
        self.step_by_step = step_by_step
        logging.basicConfig(
            handlers=[
                    logging.StreamHandler(),
                    logging.FileHandler(f'app.log', 'w', 'utf-8')
                    ],
            format='%(asctime)s %(levelname)s %(message)s [%(funcName)s]',
            datefmt='%Y.%m.%d %H:%M:%S',
            level=logging.INFO
            )    
        self.log = logging.getLogger(__name__)
        self.log.setLevel(logging.INFO if not self.DEBUG else logging.DEBUG)
        if self.DEMO:
            img = Image.open(os.path.join('demo', 'demo.png'))
            img.show()
            windows_title = '.PNG'
        self.scale = scale
        if self._сapture_window(windows_title):
            self.log.info('STARTED')
        else:
            sys.exit()


    def _сapture_window(self, windows_title):
        self.window = None
        try:
            self.log.debug(f'Finding game window "{windows_title}"...')
            if (windows := gw.getWindowsWithTitle(windows_title)):
                self.window = gw.getWindowsWithTitle(windows_title)[0]
                self.windows_area = (self.window.left, self.window.top, self.window.width, self.window.height)
                self.log.debug(f'Target window founded')
            else:
                self.log.critical('Cannot find game window')
                return None
            self.log.debug('Activating the window...')
            self.window.activate()
            self.log.debug('The window activated')
            return self.window
        except:
            return None


    def _capture_screen(self):
        screen = ImageGrab.grab()
        screen_np = np.array(screen)
        screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_BGR2GRAY)
        return screen_gray, screen_np.shape[1], screen_np.shape[0]


    def _load_template(self, template_path):
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            raise ValueError(f"Template image at path {template_path} could not be loaded.")
        return template


    def _template_calibrate(self, template):
        current_debug_mode = self.log.level
        self.log.setLevel(logging.DEBUG)
        for scan_threshold in range(100, 950, 50):
            self.scan(template, scan_area=self.windows_area, scan_threshold=scan_threshold/1000)
        self.log.setLevel(current_debug_mode)



    def _resize_image(self, image, max_width, max_height):
        h, w = image.shape[:2]
        if w > max_width or h > max_height:
            scaling_factor = min(max_width / w, max_height / h)
            new_size = (int(w * scaling_factor), int(h * scaling_factor))
            resized_image = cv2.resize(image, new_size)
            return resized_image
        return image


    def _is_near_existing_targets(self, new_coord, targets, search_radius):
        for coord in targets:
            if (abs(new_coord[0] - coord[0]) <= search_radius) and (abs(new_coord[1] - coord[1]) <= search_radius):
                return True
        return False


    def scan(self, template_file, scan_area, scan_threshold):
        self.log.debug(f'Scan started for "{template_file}" [scale x{self.scale}]  ')
        scan_start_time = timeit.default_timer()
        screen_gray, screen_width, screen_height = self._capture_screen()
        target_template = self._load_template(os.path.join('templates', template_file))
        found_targets = []
        resized_template = cv2.resize(target_template, (0, 0), fx=self.scale, fy=self.scale)
        if resized_template.shape[0] > screen_gray.shape[0] or resized_template.shape[1] > screen_gray.shape[1]:
            self.log.warn('Size of template > size of screen)')
            return found_targets
        res = cv2.matchTemplate(screen_gray, resized_template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= scan_threshold)
        for pt in zip(*loc[::-1]):
            top_left = pt
            bottom_right = (top_left[0] + resized_template.shape[1], top_left[1] + resized_template.shape[0])
            cv2.rectangle(screen_gray, top_left, bottom_right, (0, 255, 0), 2)
            bottom_left = (bottom_right[0], top_left[1] + resized_template.shape[0])
            offset_x = -resized_template.shape[0]/2
            offset_y = -resized_template.shape[1]/2
            click_x = int((bottom_left[0] + offset_x) * screen_width / screen_gray.shape[1])
            click_y = int((bottom_left[1] + offset_y) * screen_height / screen_gray.shape[0])
            if scan_area[0] <= click_x <= (scan_area[0] + scan_area[2]) and scan_area[1] <= click_y <= (scan_area[1] + scan_area[3]):
                target = (click_x, click_y)
                search_radius = round(resized_template.shape[0]/2 + resized_template.shape[1]/2)
                if not self._is_near_existing_targets(target, found_targets, search_radius):
                    found_targets.append(target)
        scan_end_time = timeit.default_timer()
        report = f'Scan completed for "{template_file}" [size x {self.scale}: {target_template.shape} => {resized_template.shape}] with [{scan_threshold=}] in area {scan_area} at {round(scan_end_time - scan_start_time, 1)} sec: {len(found_targets)} items founded'
        if self.step_by_step:
            # screen_gray = self._resize_image(screen_gray, 1920, 1080)
            cv2.imshow(report, screen_gray)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            self.delay(1000)
        self.log.debug(report)
        number_of_found_targets = len(found_targets)
        if number_of_found_targets == 1:
            result = found_targets[0]
        elif number_of_found_targets > 1:
            self.log.warn('Multiple targets detected for this pattern (see the detailed debug log): collision possible.')
            scan_index = 0
            result = found_targets[min(scan_index, number_of_found_targets-1)]
        else:
            result = None
        return result
        

    def click(self, target):
        click_x, click_y = target
        if self.DEMO:
            pyautogui.moveTo(click_x, click_y)
        else:
            pyautogui.click(click_x, click_y)
        self.log.debug(f'Clicked {click_x, click_y}')

    
    def delay(self, timeout):
        time.sleep(timeout/1000)


if __name__ == "__main__":
    # ge = GrindEngine()
    # ge._template_calibrate('demo.png')
    try:
        if len(sys.argv) <= 1:
            file = 'scenaries.py'
        else:
            file = sys.argv[1]            
        with open(file, 'r') as f:
            code = f.read()
        compiled_code = compile(code, "<string>", "exec")
        exec(compiled_code)
    except Exception as e:
        print(f'ERROR ({str(e)})')
    finally:
       ...
