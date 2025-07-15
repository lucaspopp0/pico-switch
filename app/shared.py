from .requestqueue import request, queue
from .board import board
from .config import config
from .wifi import wifi

shared_rq: queue.RequestQueue
shared_board: board.Board
shared_cfg: config.Config
shared_wifi: wifi.WiFiController
