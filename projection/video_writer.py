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

    def write_error_frame(self, row_number, reason=""):
        """A black frame with a white X, the failed row number and the reason (FR41)."""
        img = Image.new("L", (self.width, self.height), 0)
        draw = ImageDraw.Draw(img)
        line_width = max(1, min(self.width, self.height) // 100)
        draw.line([(0, 0), (self.width - 1, self.height - 1)], fill=255, width=line_width)
        draw.line([(self.width - 1, 0), (0, self.height - 1)], fill=255, width=line_width)

        title = f"Invalid plane: row {row_number}"
        lines = [(title, self._fit_font(draw, title, self.width // 20))]
        if reason:
            font = ImageFont.load_default(size=max(10, self.width // 32))
            lines += [(line, font) for line in self._wrap(draw, reason, font)]

        boxes = [draw.textbbox((0, 0), text, font=font) for text, font in lines]
        gap = 6
        total_height = sum(bottom - top for _, top, _, bottom in boxes) + gap * (len(lines) - 1)
        y = (self.height - total_height) // 2
        for (text, font), (left, top, right, bottom) in zip(lines, boxes):
            x = (self.width - (right - left)) // 2
            # black box behind the text, so it stays readable over the X
            draw.rectangle([x - 4, y - 4, x + (right - left) + 4, y + (bottom - top) + 8], fill=0)
            draw.text((x, y - top), text, fill=255, font=font)
            y += bottom - top + gap
        self._append(np.asarray(img))

    def _fit_font(self, draw, text, size):
        """The default font at the given size, made smaller until text fits the frame width."""
        size = max(10, size)
        font = ImageFont.load_default(size=size)
        while size > 8 and self._text_width(draw, text, font) > self.width * 0.9:
            size -= 1
            font = ImageFont.load_default(size=size)
        return font

    def _wrap(self, draw, text, font):
        """Splits text into lines that fit the frame width, breaking between words."""
        lines = []
        for word in text.split():
            if lines and self._text_width(draw, lines[-1] + " " + word, font) <= self.width * 0.9:
                lines[-1] += " " + word
            else:
                lines.append(word)
        return lines

    @staticmethod
    def _text_width(draw, text, font):
        left, _, right, _ = draw.textbbox((0, 0), text, font=font)
        return right - left

    def _append(self, frame):
        try:
            self._writer.append_data(frame)
        except Exception as e:
            raise OSError(f"{self.path}: cannot write video ({e})")


if __name__ == "__main__":
    gradient = np.tile(np.arange(0, 256, 2, dtype=np.uint8), (100, 1))
    with VideoWriter("test.mp4", 200, 301) as writer:
        writer.write_frame(gradient)
        writer.write_error_frame(3, "not isosceles: dist(a,b) = 10.0000, dist(a,c) = 20.0000")
    print("wrote test.mp4", writer.height, writer.width)
