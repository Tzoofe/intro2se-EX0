"""Writes animated GIF previews of the experiment videos to docs/media/.
GitHub shows GIFs inline in the README, but not MP4 videos.

Run from the project root: python -m experiments.make_gifs"""
import imageio.v2 as imageio
from PIL import Image

VIDEOS = ["MRHead_1_rotation", "onion_rotation", "swiss_roll_rotation"]
STEP = 2        # every second frame, to keep the files small
FRAME_MS = 200  # so the GIF plays at the same speed as the 10 fps video
LEVELS = 64     # gray levels; fewer levels compress much better


def main():
    for name in VIDEOS:
        frames = [Image.fromarray(frame[:, :, 0] // (256 // LEVELS) * (256 // LEVELS))
                  for i, frame in enumerate(imageio.get_reader(f"experiments/output/{name}.mp4")) if i % STEP == 0]
        out = f"docs/media/{name}.gif"
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=FRAME_MS, loop=0, optimize=True)
        print(f"wrote {out} ({len(frames)} frames)")


if __name__ == "__main__":
    main()
