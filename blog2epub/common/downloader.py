import gzip
import hashlib
import os
import re
import time
import base64
from collections.abc import Mapping
from urllib.parse import urlparse, unquote

import filetype  # type: ignore
import requests
from imagesize import imagesize  # type: ignore
from PIL import Image
from requests.cookies import RequestsCookieJar

from blog2epub.common.crawler import clever_decode
from blog2epub.common.interfaces import EmptyInterface
from blog2epub.models.book import DirModel, ImageModel


def prepare_directories(dirs: DirModel):
    paths = [dirs.html, dirs.images, dirs.originals]
    for p in paths:
        if not os.path.exists(p):
            os.makedirs(p)


class Downloader:
    def __init__(
        self,
        dirs: DirModel,
        url: str,
        interface: EmptyInterface,
        images_size: tuple[int, int],
        images_quality: int,
        ignore_downloads: list[str],
    ):
        self.dirs = dirs
        self.url = url
        self.interface = interface
        self.images_size = images_size
        self.images_quality = images_quality
        self.ignore_downloads = ignore_downloads
        self.cookies = RequestsCookieJar()
        self.session = requests.session()
        self.headers: Mapping[str, str] = {}
        self.skipped_images: list[str] = []

    def get_urlhash(self, url):
        m = hashlib.md5()
        m.update(url.encode("utf-8"))
        return m.hexdigest()

    def file_write(self, contents: bytes, filepath: str):
        filepath = filepath + ".gz"
        with gzip.open(filepath, "wb") as f:
            f.write(contents)

    def file_read(self, filepath: str) -> bytes:
        if os.path.isfile(filepath + ".gz"):
            with gzip.open(filepath + ".gz", "rb") as f:
                contents = f.read()
        else:
            with open(filepath, "rb") as html_file:
                contents = html_file.read()
            self.file_write(contents, filepath)
            os.remove(filepath)
        return contents

    def get_filepath(self, url: str) -> str:
        return os.path.join(self.dirs.html, self.get_urlhash(url) + ".html")

    def _is_url_in_ignored(self, url: str) -> bool:
        for search_rule in self.ignore_downloads:
            if re.match(search_rule, url):
                return True
        return False

    def _is_url_in_skipped(self, url: str) -> bool:
        if url in self.skipped_images:
            return True
        return False

    def file_download(self, url: str, filepath: str) -> bytes | None:
        if self._is_url_in_ignored(url) or self._is_url_in_skipped(url):
            return None
        prepare_directories(self.dirs)
        try:
            response = self.session.get(url, cookies=self.cookies, headers=self.headers)
        except requests.exceptions.ConnectionError:
            return None
        self.cookies = response.cookies
        self.file_write(response.content, filepath)
        return response.content

    @staticmethod
    def check_interstitial(contents: bytes | str):
        if isinstance(contents, bytes):
            contents = clever_decode(contents)
        interstitial = re.findall('interstitial=([^"]+)', contents)
        if interstitial:
            return interstitial[0]
        return False

    def get_content(self, url) -> bytes | None:
        # TODO: This needs refactor!
        filepath = self.get_filepath(url)
        contents = None
        for _x in range(0, 3):
            if not os.path.isfile(filepath) and not os.path.isfile(filepath + ".gz"):
                contents = self.file_download(url, filepath)

                if contents is not None:
                    # TODO:
                    # Determine if we have _any_ content, or if we need to make an 
                    # intelligent fetch to the API
                    pass
            else:
                contents = self.file_read(filepath)
            if contents is not None:
                break
            self.interface.print(f"...repeat request: {url}")
            time.sleep(3)
        if contents is not None:
            interstitial = self.check_interstitial(contents)
            if interstitial:
                interstitial_url = "http://" + self.url + "?interstitial=" + interstitial
                self.file_download(interstitial_url, self.get_filepath(interstitial_url))
                contents = self.file_download(
                    "http://" + self.url,
                    self.get_filepath("http://" + self.url),
                )
        return contents

    def _fix_image_url(self, img: str) -> str:
        if not img.startswith("http"):
            # Support data:image/... URL (no transformation needed)
            if img.startswith("data:"):
                return img;

            uri = urlparse(self.url)
            if uri.netloc not in img:
                img = os.path.join(uri.netloc, img)
            while not img.startswith("//"):
                img = "/" + img
            img = f"{uri.scheme}:{img}"
        return img
    
    def _get_image_bytes_from_web(self, url: str) -> bytes:
        response = self.session.get(url, cookies=self.cookies, headers=self.headers)
        return response.content

    def _get_image_bytes_from_data_url(self, url: str) -> bytes | None:
        metadata, encoded_img = url.split(',', 1)
        # The first value will always be the mime type (image/png, image/svg+xml, etc.)
        _, encoding = metadata.split(';', 1)

        img = encoded_img
        try:
            # Check if we need to base64 decode the data
            if 'base64' in encoding:
                img = base64.b64decode(img)

            # Check if there's a charset=<something> value to decode
            if 'charset=' in encoding:
                charset = encoding.split('charset=')[1].split(';')[0]
                img = img.decode(charset)
        except Exception:
            return None

        return img


    def _download_image(self, url: str, filepath: str) -> bool | None:
        if self._is_url_in_ignored(url) or self._is_url_in_skipped(url):
            return None
        prepare_directories(self.dirs)
        try:
            image_bytes = self._get_image_bytes_from_data_url(url) if url.startswith('data:') \
                else self._get_image_bytes_from_web(url)
            
            if image_bytes is None:
                self.interface.print("Cannot download image " + url + " - unsupported type")
                return False
        except requests.exceptions.ConnectionError:
            return False
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        time.sleep(1)
        return True
    
    def resolve_image_type(self, url: str) -> str | None:
        supported_mimes = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/bmp": ".bmp",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "image/heif": ".heic",
            "image/svg+xml": ".svg",
        }

        if url.startswith('data:'):
            _, encoded_img = url.split(':', 1)
            metadata, _ = encoded_img.split(',', 1)
            mime_type, _ = metadata.split(';', 1)

            if mime_type in supported_mimes:
                return supported_mimes[mime_type]

            return None


        # Retrieve the last part of the URL path and split off just the extension and query string
        from_url = os.path.splitext(url)[1].lower().split("?")[0]

        # URL indicates we support the file, no need for further checking
        # the true mime will be guessed later on once downloaded
        if from_url in [".jpeg", ".jpg", ".png", ".bmp", ".gif", ".webp", ".heic"]:
            return from_url
    
        try:
            response = self.session.head(url, cookies=self.cookies, headers=self.headers)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()

            if(content_type in supported_mimes):
                return supported_mimes[content_type]
        except requests.exceptions.ConnectionError or requests.exceptions.RequestException:
            pass
        except requests.exceptions.HTTPError:
            pass

        return None
    
    def _has_transparency(self, picture: Image.Image) -> bool:
        if picture.info.get("transparency", None) is not None:
            return True
        if picture.mode == "P":
            transparent = picture.info.get("transparency", -1)
            for _, index in picture.getcolors():
                if index == transparent:
                    return True
        elif picture.mode == "RGBA":
            extrema = picture.getextrema()
            if extrema[3][0] < 255:
                return True
        return False

    def download_image(self, image_obj: ImageModel) -> bool:
        if self._is_url_in_ignored(image_obj.url) or self._is_url_in_skipped(image_obj.url):
            return False
        image_obj.url = self._fix_image_url(image_obj.url)
        img_hash = self.get_urlhash(image_obj.url)
        img_type = self.resolve_image_type(image_obj.url)
        if img_type is None:
            self.interface.print("Cannot download image " + image_obj.url + " - unsupported type")
            return False
        original_fn = os.path.join(self.dirs.originals, img_hash + img_type)
        resized_fn = os.path.join(self.dirs.images, img_hash + ".jpg")
        if os.path.isfile(resized_fn):
            return True
        if not os.path.isfile(resized_fn):
            self._download_image(image_obj.url, original_fn)
        if os.path.isfile(original_fn):
            original_img_type = filetype.guess(original_fn)
            if original_img_type is None:
                return False
            if not original_img_type.MIME.startswith("image"):
                os.remove(original_fn)
                self.skipped_images.append(image_obj.url)
                return False
            image_size = imagesize.get(original_fn)
            if image_size[0] + image_size[1] < 100:
                os.remove(original_fn)
                self.skipped_images.append(image_obj.url)
                return False
            picture = Image.open(original_fn)
            if picture.size[0] > self.images_size[0] or picture.size[1] > self.images_size[1]:
                picture.thumbnail(self.images_size, Image.LANCZOS)  # type: ignore
            
            # Convert picture to RGB mode (with an intermediary step to RGBA if needed)
            if picture.mode != "RGB":
                if self._has_transparency(picture):
                    __p = picture
                    try:
                        rgba_picture = picture.convert("RGBA")
                        # Create a new background image based on the picture, fill it with white
                        bg = Image.new("RGBA", picture.size, (255, 255, 255))
                        # Create an alpha composite of the background with the picture
                        picture = Image.alpha_composite(bg, rgba_picture)
                        # And only if all of this succeeds do we close the old picture file
                        __p.close()
                    except ValueError:
                        self.interface.print("Cannot explicitly cull alpha layer, falling back on pillow", end="")
                        # Restore old picture if nothing can be done here
                        picture = __p
                        pass
                picture = picture.convert("RGB")

            picture.save(resized_fn, format="JPEG", quality=self.images_quality)
            try:
                os.remove(original_fn)
            except PermissionError:
                pass
            return True
        return False
