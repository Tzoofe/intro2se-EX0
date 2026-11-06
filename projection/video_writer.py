import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def _round_up_to_even(n):
    return n + (n % 2)


class VideoWriter:
    """Writes uint8 grayscale frames to an H.264 MP4 (FR34 to FR41).
    All frames get the same even size (FR38): each image is centered
    horizontally, aligned to the top and padded with black.
    Use as a context manager: with VideoWriter(...) as writer: ..."""

    def __init__(self, path, height, width, fps=10):
        self.path = path
        self.height = _round_up_to_even(height)
        self.width = _round_up_to_even(width)
        self.fps = fps
        self._writer = None

    def __enter__(self):
        try:
            # macro_block_size=1: keep our size, do not let imageio resize to a multiple of 16.
            self._writer = imageio.get_writer(self.path, fps=self.fps, codec="libx264",
                                              macro_block_size=1)
        except Exception as e:
            raise OSError(f"{self.path}: cannot write video ({e})")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._writer.close()

    def write_frame(self, image):
        """image: 2D uint8 array no larger than the frame size."""
        frame = np.zeros((self.height, self.width), dtype=np.uint8)
        h, w = image.shape
        left = (self.width - w) // 2
        frame[:h, left:left + w] = image
        self._append(frame)

    def write_error_frame(self, row_number):
        """A black frame with a white X and the failed row number (FR41)."""
        img = Image.new("L", (self.width, self.height), 0)
        draw = ImageDraw.Draw(img)
        line_width = max(1, min(self.width, self.height) // 100)
        draw.line([(0, 0), (self.width - 1, self.height - 1)], fill=255, width=line_width)
        draw.line([(self.width - 1, 0), (0, self.height - 1)], fill=255, width=line_width)

        text = f"Invalid plane: row {row_number}"
        font = ImageFont.load_default(size=max(10, self.width // 20))
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        x = (self.width - (right - left)) // 2
        y = (self.height - (bottom - top)) // 2
        # black box behind the text, so it stays readable over the X
        draw.rectangle([x - 4, y - 4, x + (right - left) + 4, y + (bottom - top) + 8], fill=0)
        draw.text((x, y), text, fill=255, font=font)
        self._append(np.asarray(img))

    def _append(self, frame):
        try:
            self._writer.append_data(frame)
        except Exception as e:
            raise OSError(f"{self.path}: cannot write video ({e})")


if __name__ == "__main__":
    gradient = np.tile(np.arange(0, 256, 2, dtype=np.uint8), (100, 1))
    with VideoWriter("test.mp4", 200, 301) as writer:
        writer.write_frame(gradient)
        writer.write_error_frame(3)
    print("wrote test.mp4", writer.height, writer.width)
