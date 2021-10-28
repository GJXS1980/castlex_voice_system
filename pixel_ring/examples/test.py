"""
Control pixel ring on ReSpeaker USB Mic Array
"""

import time

from pixel_ring import pixel_ring


pixel_ring.wakeup()
time.sleep(3)
pixel_ring.think()
time.sleep(3)
pixel_ring.speak()
time.sleep(6)
pixel_ring.off()
time.sleep(3)


pixel_ring.off()
time.sleep(1)

