"""
YouTube 영상 정보 추출 모듈
YouTube Data API v3 사용
"""
import os
import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class YouTubeInfoExtractor:
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            print("⚠️ YOUTUBE_API_KEY가 설정되지 않았습니다.")
            self.youtube = None
        else:
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)

    def extract_video_id(self, url: str) -> str:
        """YouTube URL에서 video_id 추출"""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'youtu\.be\/([0-9A-Za-z_-]{11})'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_video_info(self, video_id: str) -> dict:
        """YouTube Data API로 영상 정보 가져오기"""
        if not self.youtube:
            return None

        try:
            request = self.youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=video_id
            )
            response = request.execute()

            if not response.get('items'):
                print(f"❌ 영상을 찾을 수 없습니다: {video_id}")
                return None

            item = response['items'][0]
            snippet = item['snippet']
            content_details = item['contentDetails']

            # ISO 8601 duration을 읽기 쉬운 형식으로 변환
            duration = self._parse_duration(content_details['duration'])

            video_info = {
                'id': video_id,
                'title': snippet['title'],
                'channel': snippet['channelTitle'],
                'description': snippet.get('description', ''),
                'published_at': snippet['publishedAt'],
                'duration': duration,
                'thumbnail': snippet['thumbnails'].get('high', {}).get('url', ''),
                'url': f'https://www.youtube.com/watch?v={video_id}'
            }

            return video_info

        except HttpError as e:
            print(f"❌ YouTube API 오류: {e}")
            return None

    def _parse_duration(self, duration: str) -> str:
        """
        ISO 8601 duration을 읽기 쉬운 형식으로 변환
        예: PT15M30S -> 15:30
        """
        import re

        hours = re.search(r'(\d+)H', duration)
        minutes = re.search(r'(\d+)M', duration)
        seconds = re.search(r'(\d+)S', duration)

        hours = int(hours.group(1)) if hours else 0
        minutes = int(minutes.group(1)) if minutes else 0
        seconds = int(seconds.group(1)) if seconds else 0

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"


if __name__ == '__main__':
    # 테스트
    from dotenv import load_dotenv
    load_dotenv()

    extractor = YouTubeInfoExtractor()
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    video_id = extractor.extract_video_id(test_url)

    if video_id:
        print(f"Video ID: {video_id}")
        info = extractor.get_video_info(video_id)
        if info:
            print(f"Title: {info['title']}")
            print(f"Channel: {info['channel']}")
            print(f"Duration: {info['duration']}")
