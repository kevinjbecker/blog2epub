import os
from pathlib import Path
from random import shuffle

from PIL import Image, ImageDraw, ImageFont

from blog2epub.common.assets import asset_path
from blog2epub.common.globals import VERSION

TITLE_FONT_NAME = asset_path("Alegreya-Regular.ttf")
SUBTITLE_FONT_NAME = asset_path("Alegreya-Italic.ttf")
GENERATOR_FONT_NAME = asset_path("MartianMono-Regular.ttf")


class Cover:
    """
    Cover class used in Blog2Epub class.
    """

    tile_size = 120

    def __init__(self, book):
        """
        :param crawler: intance of Book class
        """
        self.dirs = book.dirs
        self.interface = book.interface
        self.file_name = book.file_name
        self.file_name_prefix = book.file_name_prefix
        self.description = book.description
        self.title = book.title
        self.images = self._check_image_size(book.images)
        self.destination_folder = os.path.join(str(Path.home()), ".blog2epub")
        self.start = book.start
        self.end = book.end

    def _check_image_size(self, images):
        verified_images = []
        for image in set(images):
            if image:
                img_file = os.path.join(self.dirs.images, image)
                if os.path.isfile(img_file):
                    img = Image.open(img_file)
                    if img.size[0] >= self.tile_size and img.size[1] >= self.tile_size:
                        verified_images.append(image)
        return verified_images

    def _make_thumb(self, img, size):
        cropped_img = self._crop_image(img)
        cropped_img.thumbnail(size, Image.LANCZOS)
        return cropped_img

    def _is_landscape(self, width, height):
        if width >= height:
            return True
        return False

    def _box_params_center(self, width, height):
        if self._is_landscape(width, height):
            upper_x = int((width / 2) - (height / 2))
            upper_y = 0
            lower_x = int((width / 2) + (height / 2))
            lower_y = height
            return upper_x, upper_y, lower_x, lower_y
        upper_x = 0
        upper_y = int((height / 2) - (width / 2))
        lower_x = width
        lower_y = int((height / 2) + (width / 2))
        return upper_x, upper_y, lower_x, lower_y

    def _crop_image(self, img):
        upper_x, upper_y, lower_x, lower_y = self._box_params_center(
            img.size[0], img.size[1]
        )
        box = (upper_x, upper_y, lower_x, lower_y)
        region = img.crop(box)
        return region

    def _get_cover_date(self):
        if self.end is None:
            return self.start.strftime("%d %B %Y")
        if self.start.strftime("%Y.%m") == self.end.strftime("%Y.%m"):
            return self.end.strftime("%d") + "-" + self.start.strftime("%d %B %Y")
        if self.start.strftime("%Y.%m") == self.end.strftime("%Y.%m"):
            return self.end.strftime("%d %B") + " - " + self.start.strftime("%d %B %Y")
        return self.end.strftime("%d %B %Y") + " - " + self.start.strftime("%d %B %Y")

    def _draw_text(self, cover_image):
        cover_draw = ImageDraw.Draw(cover_image)
        cover_draw.text(
            (15, 635),
            self.title,
            (255, 255, 255),
            font=ImageFont.truetype(TITLE_FONT_NAME, 30),
        )
        cover_draw.text(
            (15, 670),
            self._get_cover_date(),
            (150, 150, 150),
            font=ImageFont.truetype(SUBTITLE_FONT_NAME, 20),
        )
        cover_draw.text(
            (15, 750),
            f"Generated with blog2epub v{VERSION}\nfrom {self.file_name_prefix}",
            (155, 155, 155),
            font=ImageFont.truetype(GENERATOR_FONT_NAME, 10),
        )
        return cover_image

    def generate(self):
        tiles_count_y = 5
        tiles_count_x = 7
        cover_image = Image.new("RGB", (600, 800))
        self.interface.print(
            f"Generating cover (800px*600px) from {len(self.images)} images."
        )
        dark_factor = 1
        if len(self.images) > 0:
            shuffle(self.images)
            i = 1
            for x in range(0, tiles_count_x):
                for y in range(0, tiles_count_y):
                    try:
                        img_file = os.path.join(self.dirs.images, self.images[i - 1])
                        thumb = self._make_thumb(
                            Image.open(img_file), (self.tile_size, self.tile_size)
                        )
                        thumb = thumb.point(lambda p: p * dark_factor)
                        dark_factor = dark_factor - 0.03
                        cover_image.paste(
                            thumb, (y * self.tile_size, x * self.tile_size)
                        )
                        i = i + 1
                    except Exception as e:
                        print(e)
                    if i > len(self.images):
                        i = 1
        cover_image = self._draw_text(cover_image)
        cover_image = cover_image.convert("L")
        cover_file_name = self.file_name + ".jpg"
        cover_file_full_path = os.path.join(self.destination_folder, cover_file_name)
        cover_image.save(cover_file_full_path, format="JPEG", quality=100)
        return cover_file_name, cover_file_full_path
