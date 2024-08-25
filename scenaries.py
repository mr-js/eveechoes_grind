# from grind import GrindEngine


def scenary_check_around(grind):
            grind.log.info('Safety check around')
            grind.log.info('Checking if it\'s in the garage')
            button_from_dock = grind.scan('button_from_dock.png', scan_area=grind.windows_area, scan_threshold=0.7)
            if not button_from_dock:
                grind.log.info('We\'re not in a garage')
                return 10
            grind.delay(500)
            grind.log.info('Checking chat availability')
            button_chat = grind.scan('button_chat.png', scan_area=grind.windows_area, scan_threshold=0.8)
            if not button_chat:
                grind.log.info('Chat is unavailable')
                return 20
            grind.click(button_chat)
            grind.delay(500)
            grind.log.info('Checking enemy statistics')
            common_around = grind.scan('common_around.png', scan_area=grind.windows_area, scan_threshold=0.45)
            if not common_around:
                grind.log.info('Enemy statistics are not available')
                return 30
            grind.delay(500)
            grind.log.info('Checking for enemies around')
            safe_around = grind.scan('safe_around.png', scan_area=grind.windows_area, scan_threshold=0.8)
            if not safe_around:
                grind.log.info('There are enemies all around now. The flight\'s been delayed.')
                return 40
            else:
                grind.log.info('There are no enemies. Let\'s go!')
                grind.click(button_from_dock)
                return 0


def scenary_departure_return(grind):
     grind.log.info('ToDo: ...')
     return 0


def scenary_enter_anomaly(grind):
     grind.log.info('ToDo: ...')
     return 0


def scenary_module_tuning(grind):
     grind.log.info('ToDo: ...')
     return 0


def scenary_combat_aim(grind):
     grind.log.info('ToDo: ...')
     return 0


def scenary_combat_attack(grind):
     grind.log.info('ToDo: ...')
     return 0


grind = GrindEngine(demo=True, debug=True, scale=1.00, step_by_step=True, windows_title='BlueStacks App Player 1')
scenary_check_around(grind)
scenary_departure_return(grind)
scenary_enter_anomaly(grind)
scenary_module_tuning(grind)
scenary_combat_aim(grind)
scenary_combat_attack(grind)
