from machine import Pin
from neopixel import NeoPixel
from time import sleep

class NeoPixels:
    
    def __init__(self):
        self.rows = [
            NeoPixel(Pin(0), 6),
            NeoPixel(Pin(4), 4),
            NeoPixel(Pin(22), 6),
            NeoPixel(Pin(18), 4),
        ]

    # Update the color of all pixels at once
    def write(self) -> None:
        for row in self.rows:
            row.write()

    # Map a key to a pixel's row
    def pixel_coords(
        self,
        key: str,
    ) -> tuple[int, int]:
        key = str(key)

        if key == "1":
            return (0, 0)
        elif key == "2":
            return (0, 2)
        elif key == "on":
            return (0, 4)
        elif key == "3":
            return (1, 0)
        elif key == "4":
            return (1, 2)
        elif key == "5":
            return (2, 0)
        elif key == "6":
            return (2, 2)
        elif key == "off":
            return (2, 4)
        elif key == "7":
            return (3, 0)
        elif key == "8":
            return (3, 2)
        else:
            raise Exception("unknown key: ", key)
        
    # Set the RGB value of both pixels for a button
    def set_button(
        self,
        key: str,
        rgb: tuple[int, int, int],
    ) -> None:
        coords = self.pixel_coords(key)
        self.rows[coords[0]][coords[1]] = rgb
        self.rows[coords[0]][coords[1]+1] = rgb
        self.rows[coords[0]].write()

    def set_all(
        self,
        rgb: tuple[int, int, int],
    ):
        for row in self.rows:
            for i in range(len(row)):
                row[i] = rgb
            
            row.write()

    async def flash(
        self,
        rgb,
        seconds = 0.1,
        times = 1,
    ):
        for _ in range(times):
            self.set_all(rgb)
            sleep(seconds)
            self.set_all((0, 0, 0))
            sleep(seconds)
