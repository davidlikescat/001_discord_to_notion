import os
import requests
import re
from dotenv import load_dotenv
from typing import Dict, Optional

# 환경 변수 로드
load_dotenv()

class YouTubeInfoExtractor:
    """YouTube API를 사용한 영상 정보 추출"""
    
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        self.base_url = "https://www.googleapis.com/youtube/v3/videos"
        
        if not self.api_key:
            print("⚠️ YouTube API 키가 설정되지 않았습니다.")
    
    def get_video_info(self, video_id: str) -> Optional[Dict]:
        """
        YouTube API로 비디오 정보 가져오기
        """
        try:
            print(f"📊 영상 정보 추출 시작: {video_id}")
            
            if not self.api_key:
                print("❌ YouTube API 키가 없습니다.")
                return None
            
            params = {
                'part': 'snippet,statistics,contentDetails',
                'id': video_id,
                'key': self.api_key
            }
            
            response = requests.get(self.base_url, params=params)
            if response.status_code != 200:
                print(f"❌ YouTube API 오류: {response.status_code}")
                print(f"응답: {response.text}")
                return None
            
            data = response.json()
            if 'items' not in data or not data['items']:
                print(f"❌ 비디오를 찾을 수 없습니다: {video_id}")
                return None
            
            video = data['items'][0]
            snippet = video['snippet']
            statistics = video.get('statistics', {})
            content_details = video['contentDetails']
            
            video_info = {
                'id': video_id,
                'title': snippet['title'],
                'description': snippet.get('description', ''),
                'channel': snippet['channelTitle'],
                'channel_id': snippet['channelId'],
                'published_at': snippet['publishedAt'],
                'view_count': statistics.get('viewCount', '0'),
                'like_count': statistics.get('likeCount', '0'),
                'comment_count': statistics.get('commentCount', '0'),
                'duration': self.parse_duration(content_details['duration']),
                'duration_seconds': self.parse_duration_to_seconds(content_details['duration']),
                'thumbnail': self.get_best_thumbnail(snippet['thumbnails']),
                'tags': snippet.get('tags', []),
                'category_id': snippet.get('categoryId', ''),
                'default_language': snippet.get('defaultLanguage', ''),
                'default_audio_language': snippet.get('defaultAudioLanguage', ''),
            }
            
            print(f"✅ 영상 정보 추출 성공:")
            print(f"   제목: {video_info['title']}")
            print(f"   채널: {video_info['channel']}")
            print(f"   길이: {video_info['duration']}")
            try:
                view_count = int(video_info['view_count'])
                print(f"   조회수: {view_count:,}회")
            except ValueError:
                print(f"   조회수: {video_info['view_count']}회")
            
            return video_info
        
        except Exception as e:
            print(f"❌ YouTubeInfoExtractor 오류: {e}")
            return None
    
    def parse_duration(self, duration: str) -> str:
        """
        ISO 8601 형식(PTxHxMxS)을 사람이 읽기 쉬운 형식으로 변환
        """
        try:
            pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
            match = pattern.match(duration)
            if not match:
                return "알 수 없음"
            
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            
            parts = []
            if hours > 0:
                parts.append(f"{hours}시간")
            if minutes > 0:
                parts.append(f"{minutes}분")
            if seconds > 0:
                parts.append(f"{seconds}초")
            
            return " ".join(parts) if parts else "0초"
        
        except Exception as e:
            print(f"❌ Duration 파싱 오류: {e}")
            return "알 수 없음"
    
    def parse_duration_to_seconds(self, duration: str) -> int:
        """
        ISO 8601 형식을 초 단위로 변환
        """
        try:
            pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
            match = pattern.match(duration)
            if not match:
                return 0
            
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            return hours * 3600 + minutes * 60 + seconds
        
        except Exception as e:
            print(f"❌ Duration to seconds 변환 오류: {e}")
            return 0
    
    def get_best_thumbnail(self, thumbnails: Dict) -> str:
        """
        가장 좋은 품질의 썸네일 URL 선택
        """
        try:
            priority = ['maxres', 'high', 'medium', 'default']
            for quality in priority:
                if quality in thumbnails:
                    return thumbnails[quality]['url']
            return thumbnails.get('default', {}).get('url', '')
        except Exception as e:
            print(f"❌ 썸네일 선택 오류: {e}")
            return ''
    
    def get_video_statistics(self, video_id: str) -> Optional[Dict]:
        """
        비디오 통계 정보만 가져오기
        """
        try:
            print(f"📈 영상 통계 정보 추출: {video_id}")
            params = {
                'part': 'statistics',
                'id': video_id,
                'key': self.api_key
            }
            response = requests.get(self.base_url, params=params)
            data = response.json()
            if 'items' in data and data['items']:
                return data['items'][0]['statistics']
            return None
        except Exception as e:
            print(f"❌ 통계 정보 추출 오류: {e}")
            return None
    
    def check_video_availability(self, video_id: str) -> bool:
        """
        비디오 사용 가능성 확인
        """
        try:
            params = {
                'part': 'id',
                'id': video_id,
                'key': self.api_key
            }
            response = requests.get(self.base_url, params=params)
            data = response.json()
            available = 'items' in data and bool(data['items'])
            print(f"{'✅' if available else '❌'} 비디오 사용 {'가능' if available else '불가'}: {video_id}")
            return available
        except Exception as e:
            print(f"❌ 비디오 가용성 확인 오류: {e}")
            return False

# 테스트 함수
def test_youtube_info_extractor():
    extractor = YouTubeInfoExtractor()
    test_video_ids = [
        "dQw4w9WgXcQ",   # Rick Astley
        "invalid_id",    # 잘못된 ID
        "9bZkp7q19f0"     # PSY
    ]
    
    print("🧪 YouTubeInfoExtractor 테스트 시작")
    print("=" * 50)
    
    for i, video_id in enumerate(test_video_ids, 1):
        print(f"\n테스트 {i}: {video_id}")
        available = extractor.check_video_availability(video_id)
        print(f"가용성: {available}")
        
        if available:
            info = extractor.get_video_info(video_id)
            if info:
                print(f"제목: {info['title']}")
                print(f"채널: {info['channel']}")
                print(f"길이: {info['duration']}")
                print(f"조회수: {info['view_count']}")
    
    print("\n" + "=" * 50)
    print("🧪 테스트 완료")

if __name__ == "__main__":
    test_youtube_info_extractor()
