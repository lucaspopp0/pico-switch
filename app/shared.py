import asyncio
import json

from .requestqueue.queue import RequestQueue
from .requestqueue.request import Request
from .board.board import Board, BasicButtonBoard, DialBoard
from .board import layouts, basics, deprecated
from .config.config import Config
from .wifi.wifi import WiFiController
from .otaupdate import update_manager
from .ble import ble
from .api import server, routes

requestqueue: RequestQueue
board: Board
config: Config
wifi: WiFiController
api: server.Server


def setup_config():
    global config

    config = Config()
    config.load()


def setup_request_queue():
    global config, requestqueue
    requestqueue = RequestQueue(
        5,
        config.value['homeassistant-ip'],
    )


def setup_board():
    global board, config

    layout = str(config.value['layout'])

    match layout:

        case layouts.V3:
            board = BasicButtonBoard(
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
            board = BasicButtonBoard(
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

        case layouts.V7:
            board = BasicButtonBoard(
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

    def new_request(key: str) -> Request:
        return Request(
            'press',
            json.dumps({
                "switch": config.value["name"],
                "layout": layout,
                "key": key,
            }),
        )

    if isinstance(board, BasicButtonBoard):
        b = board

        def on_req_success():
            b.led.off()

        def on_req_failure():
            asyncio.create_task(b.led.flash(100, 0, 0, times=2))

        def on_press(key: str):
            req = new_request(key)
            req.on_success = on_req_success
            req.on_failure = on_req_failure
            requestqueue.add(req)

        b.on_press = on_press
        board = b

    # Setup dial handlers
    if isinstance(board, DialBoard):
        b = board

        def on_dial_press(routine: deprecated.Routine):
            board.on_press(routine.name)

        def on_dial_long_press(routine: deprecated.Routine):
            board.on_press(routine.name + '-long')

        b.on_dial_press = on_dial_press
        b.on_dial_longpress = on_dial_long_press
        board = b


def setup_wifi():
    global config, wifi, board

    ssid, psk, ok = config.value.get_wifi()
    if not ok:
        return

    wifi = WiFiController(ssid, psk)

    wifi.on_connecting = board.on_wifi_connecting
    wifi.on_connected = board.on_wifi_connected
    wifi.on_failed = board.on_wifi_failed


def setup_bluetooth():
    global board

    pairing_task = None

    def on_pair():

        async def pair():
            pairing_task = asyncio.create_task(ble.ble_server_task(), )

            await asyncio.gather(pairing_task)
            board._should_pair = False
            board.preparing_pairing = False
            board.accepting_inputs = True

        asyncio.create_task(pair())

    def on_pair_cancel():
        if pairing_task is not None:
            pairing_task.cancel()

    board.on_pair = on_pair
    board.on_pair_cancel = on_pair_cancel


def setup_automatic_updates():
    global board

    board.on_update = update_manager.try_update


def setup_api():
    global api

    api = server.Server()
    routes.setup_routes(api)
