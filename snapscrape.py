import requests
from dataclasses import dataclass, field
from typing import List, Tuple
import os
import subprocess
import zipfile
import logging
import argparse
from snaputils import SnapAPI
import time

def download_media(snap_media: list, download_location: str, skip_videos: bool = False, skip_images: bool = True, write_media_id: bool = True, write_overlay_text: bool = True,write_thumbnail: bool = True, write_snap_media_title: bool = True,write_media_timestamp: bool = True, encode_video_timestamp: bool = True,encode_video_title: bool = True, seperate_media: bool = True, zip_after_finish: bool = True):

    """
    Download the media from snapchat

    Args:
        snapchat_media (list): list of snapmedia
        download_location (str): Where to download the media
        skip_videos (bool, optional): skip videos, media with type SNAP_MEDIA_TYPE_VIDEO or SNAP_MEDIA_TYPE_VIDEO_NO_SOUND. Defaults to False.
        skip_images (bool, optional): skip images, media with type SNAP_MEDIA_TYPE_IMAGE. Defaults to True.
        write_media_id (bool, optional): write the media_id to a text file. Defaults to True.
        write_overlay_text (bool, optional): write the overlay_text, if any, to a text file. Defaults to True.
        write_thumbnail (bool, optional): write the thumbnails to a file. Defaults to True.
        write_snap_media_title (bool, optional): write the snap_media_title, if any, to a file. Defaults to True.
        write_media_timestamp (bool, optional): write the timestamp to a file. Defaults to True.
        encode_video_timestamp (bool, optional): convert the timestamp to a date and re-encode the video with the date. Defaults to True.
        encode_video_title (bool, optional): re-encode the video with the snap_media_title included. Defaults to True.
        seperate_media (bool, optional): create a folder, with the media_id as the folder name, for each media file and other associated files. Defaults to True.
        zip_after_finsh (bool, optional): create a zip file of the main folder once we're finished downloading and encoding. Defaults to True.
    """

    logging.info("Starting media download...")
    base_path = download_location

    # Ensure the base download location exists
    if not os.path.exists(base_path):
        os.makedirs(base_path)

    logging.info(f"Found {len(snap_media)} Snaps")
    
    for media in snap_media:
        media_path = os.path.join(base_path, media.media_id) if seperate_media else base_path

        # Ensure each media folder exists
        if not os.path.exists(media_path):
            os.makedirs(media_path)

    for media in snap_media:
        media_path = os.path.join(download_location, media.media_id) if seperate_media else download_location

        if not os.path.exists(media_path):
            os.makedirs(media_path)

        # Skip types if specified
        if skip_videos and media.snap_media_type in ("SNAP_MEDIA_TYPE_VIDEO", "SNAP_MEDIA_TYPE_VIDEO_NO_SOUND"):
            continue
        if skip_images and media.snap_media_type == "SNAP_MEDIA_TYPE_IMAGE":
            continue

        logging.info(f"Downloading {media.media_id} | {media.snap_media_title}")

        # Download the media
        media_content = requests.get(media.media_url).content
        with open(os.path.join(media_path, f"{media.media_id}.{'mp4' if media.snap_media_type in ('SNAP_MEDIA_TYPE_VIDEO', 'SNAP_MEDIA_TYPE_VIDEO_NO_SOUND') else 'png'}"), "wb") as file:
            file.write(media_content)

        # Writing metadata to files
        if write_media_id:
            with open(os.path.join(media_path, f"{media.media_id}.txt"), "w", encoding='utf-8') as file:
                file.write(media.media_id)

        if write_overlay_text and media.overlay_text:
            with open(os.path.join(media_path, "overlay.txt"), "w", encoding='utf-8') as file:
                file.write(media.overlay_text)

        if write_snap_media_title and media.snap_media_title:
            with open(os.path.join(media_path, "title.txt"), "w", encoding='utf-8') as file:
                file.write(media.snap_media_title)

        if write_media_timestamp:
            with open(os.path.join(media_path, "timestamp.txt"), "w", encoding='utf-8') as file:
                file.write(media.timestamp)

        if write_thumbnail:
            for thumbnail_type, thumbnail_url in media.thumbnails:
                thumbnail_content = requests.get(thumbnail_url).content
                with open(os.path.join(media_path, f"{thumbnail_type}.png"), "wb") as file:
                    file.write(thumbnail_content)

        # Encoding with ffmpeg if necessary
        if media.snap_media_type == "SNAP_MEDIA_TYPE_VIDEO" and (encode_video_timestamp or encode_video_title):
            input_file = os.path.join(media_path, f"{media.media_id}.mp4")
            output_file = os.path.join(media_path, f"{media.media_id}_encoded.mp4")
            meta_command = []
            
            if encode_video_timestamp:
                ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(media.timestamp)/1000))
                meta_command.extend(["-metadata", f"date={ts}"])
            
            if encode_video_title and media.snap_media_title:
                meta_command.extend(["-metadata", f"title={media.snap_media_title}"])
            
            cmd = ["ffmpeg","-y", "-stats","-loglevel","error", "-i", input_file] + meta_command + ["-c", "copy", output_file]
            subprocess.run(cmd)

    # Zipping if required
    if zip_after_finish:
        with zipfile.ZipFile(os.path.join(download_location, f"snap_media.zip"), "w") as zipf:
            for root, _, files in os.walk(download_location):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_location))

def main():
    parser = argparse.ArgumentParser(description="Download media from Snapchat")
    parser.add_argument("--latitude", "-lat", type=float, default=31.448345381406952, help="latitude")
    parser.add_argument("--longitude","-lon", type=float, default=34.4039489649856, help="longitude")
    parser.add_argument("--zoomlevel","-zl", type=float, default=7.06892436484424, help="Zoom Level")
    parser.add_argument("--radius","-r", type=float, default=37000, help="Search radius in meters")
    parser.add_argument("--max_fuzz_radius","-fr", type=float, default=0, help="Maximum fuzz radius")
    parser.add_argument("--epoch","-e", type=int, help="Epoch Override")
    parser.add_argument("--location","-loc", type=str, default="downloads", help="Directory to download the media")
    parser.add_argument("--skip-videos","-sv", action="store_true", help="Skip downloading videos")
    parser.add_argument("--skip-images","-si", action="store_true", help="Skip downloading images")
    parser.add_argument("--no-media-id","-ni", action="store_true", help="Don't write the media_id to a text file")
    parser.add_argument("--no-overlay-text","-nt", action="store_true", help="Don't write the overlay_text to a text file")
    parser.add_argument("--no-thumbnail","-nth", action="store_true", help="Don't write the thumbnails to a file")
    parser.add_argument("--no-snap-media-title","-nst", action="store_true", help="Don't write the snap_media_title to a file")
    parser.add_argument("--no-media-timestamp","-nmt", action="store_true", help="Don't write the timestamp to a file")
    parser.add_argument("--no-encode-video-timestamp","-nevt", action="store_true", help="Don't encode video with timestamp")
    parser.add_argument("--no-encode-video-title","-nevtt", action="store_true", help="Don't re-encode video with the snap_media_title")
    parser.add_argument("--no-seperate-media", "-ns", action="store_true", help="Don't create a separate folder for each media file")
    parser.add_argument("--zip", "-z", action="store_true", help="Don't create a zip file after finishing")
    parser.add_argument("--url", "-u", action="append", help="Download Snapchat media using URLs", required=False)
    parser.add_argument("--snapid", "-sid", action="append", help="Download Snapchat media using Snap IDs", required=False)
    parser.add_argument("--file", "-f", type=str, help="A text file containing a list of URLs or Snap IDs", required=False)

    args = parser.parse_args()
    snap_api = SnapAPI()

    if args.file:
        with open(args.file, 'r') as f:
            lines = f.readlines()
        urls_or_ids = [line.strip() for line in lines]
    else:
        urls_or_ids = []
    
    if args.url:
        urls_or_ids.extend(args.url)

    if args.snapid:
        urls_or_ids.extend(args.snapid)

    try:
        if urls_or_ids:
            snap_ids = snap_api.get_snap_ids_from_urls(urls_or_ids)
            snap_stories = snap_api.get_snaps_by_id(snap_ids)
            snap_story_objects = snap_api.convert_json_to_snapmedia(snap_stories)
            download_media(snap_story_objects, args.location, args.skip_videos, args.skip_images, (not args.no_media_id), (not args.no_overlay_text), (not args.no_thumbnail), (not args.no_snap_media_title), (not args.no_media_timestamp), (not args.no_encode_video_timestamp), (not args.no_encode_video_title), (not args.no_seperate_media), args.zip)
        if not urls_or_ids:
            snapchat_media_results = snap_api.get_snapchat_playlist(args.latitude, args.longitude, args.zoomlevel, radius=args.radius, max_fuzz_radius=args.max_fuzz_radius, epoch=args.epoch)
            snapchat_media = snap_api.convert_json_to_snapmedia(snapchat_media_results)
            download_media(snapchat_media, args.location, args.skip_videos, args.skip_images, (not args.no_media_id), (not args.no_overlay_text), (not args.no_thumbnail), (not args.no_snap_media_title), (not args.no_media_timestamp), (not args.no_encode_video_timestamp), (not args.no_encode_video_title), (not args.no_seperate_media), args.zip)
            
    except Exception as e:
        logging.error(f"Error encountered: {e}")

if __name__ == "__main__":
    main()
