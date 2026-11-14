import time
import core

with open("photos/ref.jpg", "rb") as f:
    img = core.shrink(f.read())

t = time.time()
print(core.vision_check(img))
print("vision:", round(time.time() - t, 2), "s")

t = time.time()
print(core.detect(img))
print("detect:", round(time.time() - t, 2), "s")