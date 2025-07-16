from .requestqueue.queue import RequestQueue
from .board.board import Board, BasicButtonBoard, DialBoard
from .board import layouts, basics, deprecated
from .config.config import Config
from .wifi.wifi import WiFiController

requestqueue: RequestQueue
board: Board
config: Config
wifi: WiFiController

def setup_board() -> Board:
    global config

    layout = str(config.value['layout'])

    match layout:
        case layouts.V3:
            return BasicButtonBoard(
                led=basics.RgbLED(18, 17, 16),
                buttons={
                    "on": basics.PushButton([0, 5], 'on'),
                    "off": basics.PushButton([10, 15], 'off'),
                    "1": basics.PushButton([28], 1),
                    "2": basics.PushButton([11], 2),
                    "3": basics.PushButton([6], 3),
                    "4": basics.PushButton([1], 4),
                    "5": basics.PushButton([27], 5),
                    "6": basics.PushButton([12], 6),
                    "7": basics.PushButton([7], 7),
                    "8": basics.PushButton([2], 8),
                    "9": basics.PushButton([26], 9),
                    "10": basics.PushButton([13], 10),
                    "11": basics.PushButton([8], 11),
                    "12": basics.PushButton([3], 12),
                },
            )
        
        case layouts.V4:
            return BasicButtonBoard(
                led=basics.RgbLED(16, 17, 18),
                buttons={
                    "on": basics.PushButton([9, 6], 'on'),
                    "off": basics.PushButton([3, 2], 'off'),
                    "1": basics.PushButton([10], 1),
                    "2": basics.PushButton([11], 2),
                    "3": basics.PushButton([8], 3),
                    "4": basics.PushButton([7], 4),
                    "5": basics.PushButton([5], 5),
                    "6": basics.PushButton([4], 6),
                    "7": basics.PushButton([1], 8),
                    "8": basics.PushButton([0], 7),
                },
            )
        
        case layouts.V5 | layouts.V6:
            led = basics.RgbLED(16, 17, 18)

            board = DialBoard(
                led=led,
                buttons={
                    "on": basics.PushButton([13, 14], 'on'),
                    "off": basics.PushButton([0, 2], 'off'),
                    "5": basics.PushButton([15], 5),
                    "6": basics.PushButton([12], 6),
                    "7": basics.PushButton([11], 7),
                    "8": basics.PushButton([1], 8),
                },
                dial=deprecated.Wheel(led, 7, 6, 8, []),
                wheel_routines=config.value['wheel-routines'],
            )

            # Setup the switch if V6
            if layout is layouts.V6:
                def _on():
                    board.enable()
                def _off():
                    board.disable()

                board.switch = deprecated.Switch(27, 28, {
                    "on": _on,
                    "off": _off
                })

            return board
        
        case layouts.V7:
            return BasicButtonBoard(
                led=basics.RgbLED(18, 19, 20),
                buttons={
                    "on": basics.PushButton([10, 9], 'on'),
                    "off": basics.PushButton([5, 4], 'off'),
                    "1": basics.PushButton([12], 1),
                    "2": basics.PushButton([11], 2),
                    "3": basics.PushButton([7], 3),
                    "4": basics.PushButton([8], 4),
                    "5": basics.PushButton([0], 5),
                    "6": basics.PushButton([3], 6),
                    "7": basics.PushButton([1], 7),
                    "8": basics.PushButton([2], 8),
                },
            )
        
        case _:
            raise Exception("Unknown layout: " + str(layout))
            