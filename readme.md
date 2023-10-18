# Snapscrape

SnapScrape is a Python tool that automates the downloading of Snapchat media based on specified search criteria. You can filter by media type, geographical location, and other attributes. The utility provides extensive options for customizing the downloaded media, including re-encoding videos with timestamps, writing media metadata to text files, and zipping the downloaded content. This tool is currently being employed to collect civilian videos from the Gaza Strip for Open Source Intelligence (OSINT) purposes.

## Features
- Download Snapchat media by URL, Snap IDs, or geographic location
- Filter media based on type (image, video)
- Optional re-encoding of videos with timestamps and titles
- Write media metadata to text files (media_id, overlay_text, snap_media_title, etc.)
- Zip downloaded files into one single archive

## Requirements
- Python 3.x
- `requests` library
- `ffmpeg` for video re-encoding (optional)

## Installation

1. Clone the repository

```
git clone https://github.com/ef1500/snapscrape.git
```

2. Change directory into the cloned repository

```
cd snapscrape
```

3. Install the required packages

```
pip install -r requirements.txt
```

## Usage
### Basic Usage

```
python snapscrape.py
```

### Options
```
--latitude, -lat            Set the latitude for geographical search. Default is 31.448345381406952.
--longitude, -lon           Set the longitude for geographical search. Default is 34.4039489649856.
--zoomlevel, -zl            Set the zoom level. Default is 7.06892436484424.
--radius, -r                Set the search radius in meters. Default is 37000.
--max_fuzz_radius, -fr      Set the maximum fuzz radius. Default is 0.
--epoch, -e                 Override the epoch.
--location, -loc            Directory to download the media. Default is "downloads".
--skip-videos, -sv          Skip downloading videos.
--skip-images, -si          Skip downloading images.
--no-media-id, -ni          Don't write the media_id to a text file.
--no-overlay-text, -nt      Don't write the overlay_text to a text file.
--no-thumbnail, -nth        Don't write the thumbnails to a file.
--no-snap-media-title, -nst Don't write the snap_media_title to a file.
--no-media-timestamp, -nmt  Don't write the timestamp to a file.
--no-encode-video-timestamp,-nevt Don't encode video with timestamp.
--no-encode-video-title, -nevtt  Don't re-encode video with the snap_media_title.
--no-separate-media, -ns    Don't create a separate folder for each media file.
--zip, -z                   Create a zip file after finishing.
--url, -u                   Download Snapchat media using URLs.
--snapid, -sid              Download Snapchat media using Snap IDs.
--file, -f                  A text file containing a list of URLs or Snap IDs.
```