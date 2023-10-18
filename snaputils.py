import requests
from dataclasses import dataclass, field
from typing import List, Tuple
import re
import logging

# Setting up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@dataclass
class SnapMedia:
    media_id: str
    duration: float
    timestamp: str
    snap_media_type: str
    media_url: str
    thumbnails: List[Tuple[str, str]] = field(default_factory=list)
    overlay_text: str = ""
    snap_media_title: str = ""


class SnapAPI:
    BASE_URL = "https://ms.sc-jpl.com/web/getPlaylist"
    BASE_HEATMAP_URL = "https://ms.sc-jpl.com/web/getLatestTileSet"
    STORYELEM_URL = "https://ms.sc-jpl.com/web/getStoryElements"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "authority": "ms.sc-jpl.com",
        "method": "POST",
        "path": "/web/getPlaylist",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate",
        "accept-language": "en-US",
        "origin": "https://map.snapchat.com",
        "referer": "https://map.snapchat.com/",
        "sec-ch-ua": '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "sec-gpc": "1",
    }

    HEATMAP_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "authority": "ms.sc-jpl.com",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US",
        "origin": "https://map.snapchat.com",
        "referer": "https://map.snapchat.com/",
        "sec-ch-ua": '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "sec-gpc": "1",
    }

    EXPANSION_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Cookie": "sc-language=en-US; EssentialSession=true",
        "authority": "t.snapchat.com",
        "method": "GET",
        "path": "/PdcDa6Hw",
        "scheme": "https",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "sec-ch-ua": '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "sec-gpc": "1",
        "upgrade-insecure-requests": "1"
    }

    def get_heatmap_epoch(self):
        logging.info("Attempting to retrieve epoch")
        epoch_request = requests.post(self.BASE_HEATMAP_URL, json={},headers=self.HEADERS)
        epoch_request_json = epoch_request.json()

        new_epoch = epoch_request_json.get('tileSetInfos')[1].get('id').get('epoch')
        logging.info(f'Successfully obtained epoch: {new_epoch}')
        return new_epoch

    def get_snapchat_playlist(self, lat=31.448345381406952, lon=34.4039489649856, zoomlevel=7.06892436484424, flavor="default", radius=37000, max_fuzz_radius=0, timeout=10, epoch=None) -> dict:
        adjusted_epoch = self.get_heatmap_epoch() if not epoch else epoch #1697399871000 if not epoch else epoch #get_unix_epoch() # 1697346075000 if not epoch else epoch # adjust_timestamp(1697343813000) if there's no override
        if epoch:
            logging.info(f"Overriding default epoch obtination, using {epoch}")
        logging.info("Fetching Snapchat playlist...")

        data = {
            "requestGeoPoint": {"lat": lat, "lon": lon},
            "zoomLevel": zoomlevel,
            "tileSetId": {"flavor": flavor, "epoch": adjusted_epoch, "type": 1},
            "radiusMeters": radius,
            "maximumFuzzRadius": max_fuzz_radius
        }
        response = requests.post(self.BASE_URL, headers=self.HEADERS, json=data, timeout=timeout)
        return response.json()

    @staticmethod
    def convert_json_to_snapmedia(snapmap_json: dict) -> List['SnapMedia']:
        logging.info("Converting JSON to SnapMedia objects...")
        snap_media = []

        # Determine if snapmedia is from 'manifest' or directly from 'elements'
        snapmedia = snapmap_json['manifest']['elements'] if snapmap_json.get('manifest') else snapmap_json['elements']

        for s in snapmedia:
            # Use a fallback title depending on the type of JSON
            fallback_title = s['snapInfo']['title']['fallback'] if snapmap_json.get('manifest') else s['snapInfo']['localitySubtitle']['fallback']

            # Create a SnapMedia object
            snap_obj = SnapMedia(
                media_id=s['id'],
                duration=s.get('duration', 0),
                timestamp=s.get('timestamp', 0),
                snap_media_type=s['snapInfo'].get('snapMediaType', "SNAP_MEDIA_TYPE_IMAGE"),
                media_url=s['snapInfo']['streamingMediaInfo']['mediaUrl'],
                thumbnails=[(thumb['thumbnailType'], thumb['thumbnailUrl']) for thumb in s['snapInfo']['streamingThumbnailInfo']['infos']],
                overlay_text=s['snapInfo'].get('overlayText', ""),
                snap_media_title=fallback_title
            )
            snap_media.append(snap_obj)

        return snap_media
    
    def get_snaps_by_id(self, snap_list: list[str]):
        snaplist = list(set(snap_list))
        if len(snaplist) < len(snap_list):
            logging.warning(f"Ignoring {len(snap_list) - len(snaplist)} duplicate IDs")
        logging.info(f"Getting {len(snaplist)} snaps by ID")


        snap_json = {'elements': []}

        for snap_id in snaplist:
            payload = {'snapIds': [snap_id]}
            id_request = requests.post(self.STORYELEM_URL, json=payload, headers=self.HEATMAP_HEADERS, timeout=10)
            try:
                snap_json['elements'].append(id_request.json()['elements'][0])
            except Exception as e:
                logging.error(f"Failed to find story info for {snap_id}: {e}")
        return snap_json

    def extract_snap_id_from_redirected_url(self, url: str) -> str:
        # Check if URL is already long-form, if not then fetch the redirected URL
        if "t.snapchat.com" in url:
            logging.info(f'{url} is a Shortened URL. Expanding...')
            response = requests.get(url, allow_redirects=False, headers=self.EXPANSION_HEADERS, timeout=10)
            final_url = response.headers.get('Location')
            logging.info(f"Successfully expanded {url}")
        else:
            final_url = url

        # Extract SnapID from final URL
        pattern = r"([A-Za-z0-9_-]{59})"
        match = re.search(pattern,final_url)
        if match:
            logging.info(f"Obtained SnapID {match.group(1)}")
            return match.group(1)
        else:
            return None

    def get_snap_ids_from_urls(self, urls: List[str]) -> List[str]:
        snap_ids = []
        logging.info(f'Extracting snapIDs from {len(urls)} snaps')
        for url in urls:
            snap_id = self.extract_snap_id_from_redirected_url(url)
            if snap_id:
                snap_ids.append(snap_id)
        return snap_ids