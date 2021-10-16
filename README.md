<p align="center">
<img src="https://raw.githubusercontent.com/bohdanbobrowski/blogspot2epub/master/images/blog2epub.png" width="128" height="128" />
</p>

# blogspot2epub

[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/bohdanbobrowski/blogspot2epub/graphs/commit-activity) [![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)


Convert selected blogspot.com blog to epub using single command.

## Main features

- command line (CLI) and graphic user interface (GUI)
- downloads all text contents of selected blog to epub file,
- downloads post comments,
- downloads images, resizes them (to 400x300px) and converts to grayscale,
- one post = one epub chapter,
- chapters are sorted by date ascending,
- cover is generated automatically from downloaded images.

## Example covers

<p align="left">
<img src="https://raw.githubusercontent.com/bohdanbobrowski/blogspot2epub/master/images/cover_1.jpg" align="left" style="margin:0 10px 10px 0" />
<img src="https://raw.githubusercontent.com/bohdanbobrowski/blogspot2epub/master/images/cover_2.jpg" align="left" style="margin:0 10px 10px 0" />
<img src="https://raw.githubusercontent.com/bohdanbobrowski/blogspot2epub/master/images/cover_3.jpg" align="left" style="margin:0 10px 10px 0" />
<img src="https://raw.githubusercontent.com/bohdanbobrowski/blogspot2epub/master/images/cover_4.jpg" align="left" style="margin:0 10px 10px 0" />
</p>

## Installation

- for macOS users: available [app](https://github.com/bohdanbobrowski/blogspot2epub/releases)
- python3 setup.py install

### Running froum sources

    git clone git@github.com:bohdanbobrowski/blogspot2epub.git
    cd blogspot2epub
    python -m venv venv
    source ./venv/bin/activate
    pip install -r ./requirements.txt
    ./blog2epubgui.py

## GUI

### linux

<p align="center">
<img src="https://raw.githubusercontent.com/bohdanbobrowski/blogspot2epub/master/images/blog2epub_linux_screenshot_v1.2.0.png"  width="500px" />
</p>

### macOS

<p align="center">
<img src="https://raw.githubusercontent.com/bohdanbobrowski/blogspot2epub/master/images/blog2epub_osx_screenshot_v1.2.0.png" width="600px" />
</p>

## CLI

    blog2epub [blog url] <parameters>

### Parameters

    -l/--limit=[x] - limit epub file to x posts
    -s/--skip=[x] - skip x latest posts
    -q/--images-quality=[0-100] - included images quality (default is 40)
    -n/--no-images - don't include images

## Examples

    blog2epub starybezpiek.blogspot.com
    blog2epub velosov.blogspot.com -l=10
    blog2epub poznanskiehistorie.blogspot.com -q=100
    blog2epub classicameras.blogspot.com --limit=10 --no-images

## TODO list / Plannned features

- crossplatform GUI (currently under development)
- windows build
- linux build
- mobile app
- more blog engines and templates supported (worpress.com etc.)

## Release notes

### [1.2.0](https://github.com/bohdanbobrowski/blogspot2epub) - IN DEVELOPMENT (but you can run it from the sources)

- migration to Kivy :-)
- minor bugfixes in crawler
- I would try to deliver macOS, Linux and maybe Windows install package
- however running python in Windows is pain in private parts!
- I'm experimenting right now with cython to make macOS app smaller and faster

### [1.1.0](https://github.com/bohdanbobrowski/blogspot2epub/releases/tag/v1.1.0)

- migration to Gtk (for better support on multiple platforms)
- requirements cleanup
- about dialog
- macOS dmg installer included

### [1.0.5](https://github.com/bohdanbobrowski/blogspot2epub/releases/tag/v1.0.5)

- gzip html in cache folder
- atom feed parsing
- better system notifications, also under linux

### [1.0.4](https://github.com/bohdanbobrowski/blogspot2epub/releases/tag/v1.0.4)

- improved saving GUI settings
- system notification on finished download

### [1.0.3](https://github.com/bohdanbobrowski/blogspot2epub/releases/tag/v1.0.3)

- saving GUI settings to yaml file
- first macOS builds (--py2app--pyinstaller)
