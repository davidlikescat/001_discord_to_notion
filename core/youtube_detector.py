import re
from typing import List

class YouTubeDetector:
    """유튜브 링크 감지 및 비디오 ID 추출 (숏츠 지원 포함)"""
    
    def __init__(self):
        self.youtube_pattern = re.compile(
            r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})'
        )
        
        # 🔥 유튜브 숏츠 패턴 추가
        self.youtube_patterns = [
            # 일반 유튜브 URL 패턴들
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
            r'(?:https?://)?(?:m\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'(?:https?://)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})',
            
            # 🎬 유튜브 숏츠 패턴들
            r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
            r'(?:https?://)?(?:m\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
            
            # 기타 가능한 패턴들
            r'(?:https?://)?(?:www\.)?youtube\.com/live/([a-zA-Z0-9_-]{11})',
        ]
        
        # 컴파일된 패턴들
        self.compiled_patterns = [re.compile(pattern) for pattern in self.youtube_patterns]
    
    def detect_youtube_urls(self, text: str) -> List[str]:
        """
        텍스트에서 유튜브 비디오 ID들을 추출 (숏츠 포함)
        
        Args:
            text (str): 검사할 텍스트
            
        Returns:
            List[str]: 발견된 유튜브 비디오 ID들
        """
        try:
            video_ids = set()  # 중복 제거를 위해 set 사용
            
            # 모든 패턴으로 검사
            for i, pattern in enumerate(self.compiled_patterns):
                matches = pattern.findall(text)
                if matches:
                    print(f"🔍 패턴 {i+1} 매치: {matches}")
                video_ids.update(matches)
            
            # 기본 패턴으로도 검사 (하위호환성)
            main_matches = self.youtube_pattern.findall(text)
            video_ids.update(main_matches)
            
            result = list(video_ids)
            
            if result:
                print(f"🎯 YouTube 링크 감지됨: {len(result)}개")
                for i, video_id in enumerate(result, 1):
                    print(f"   {i}. Video ID: {video_id}")
                    # 🔥 숏츠인지 확인
                    if self._is_shorts_url(text, video_id):
                        print(f"      📱 유튜브 숏츠 감지!")
            else:
                print("🔍 YouTube 링크가 감지되지 않음")
            
            return result
            
        except Exception as e:
            print(f"❌ YouTubeDetector 오류: {e}")
            return []
    
    def _is_shorts_url(self, text: str, video_id: str) -> bool:
        """해당 video_id가 숏츠 URL에서 나온 것인지 확인"""
        shorts_patterns = [
            rf'youtube\.com/shorts/{video_id}',
            rf'm\.youtube\.com/shorts/{video_id}'
        ]
        
        for pattern in shorts_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def extract_video_id(self, url: str) -> str:
        """
        단일 URL에서 비디오 ID 추출
        
        Args:
            url (str): 유튜브 URL
            
        Returns:
            str: 비디오 ID 또는 None
        """
        try:
            # 모든 패턴으로 시도
            for i, pattern in enumerate(self.compiled_patterns):
                match = pattern.search(url)
                if match:
                    video_id = match.group(1)
                    url_type = "숏츠" if "shorts" in url.lower() else "일반"
                    print(f"✅ Video ID 추출 성공: {video_id} ({url_type})")
                    return video_id
            
            print(f"❌ Video ID 추출 실패: {url}")
            return None
            
        except Exception as e:
            print(f"❌ Video ID 추출 오류: {e}")
            return None
    
    def validate_video_id(self, video_id: str) -> bool:
        """
        비디오 ID 유효성 검사
        
        Args:
            video_id (str): 검사할 비디오 ID
            
        Returns:
            bool: 유효성 여부
        """
        try:
            # 유튜브 비디오 ID는 11자리 영숫자와 하이픈, 언더스코어
            if not video_id:
                return False
            
            if len(video_id) != 11:
                return False
            
            # 허용되는 문자만 포함하는지 확인
            allowed_chars = re.compile(r'^[a-zA-Z0-9_-]+$')
            if not allowed_chars.match(video_id):
                return False
            
            print(f"✅ Video ID 유효성 검사 통과: {video_id}")
            return True
            
        except Exception as e:
            print(f"❌ Video ID 유효성 검사 오류: {e}")
            return False
    
    def get_youtube_url_from_id(self, video_id: str) -> str:
        """
        비디오 ID로부터 표준 유튜브 URL 생성
        
        Args:
            video_id (str): 유튜브 비디오 ID
            
        Returns:
            str: 표준 유튜브 URL
        """
        try:
            if self.validate_video_id(video_id):
                url = f"https://www.youtube.com/watch?v={video_id}"
                print(f"🔗 표준 URL 생성: {url}")
                return url
            else:
                print(f"❌ 잘못된 Video ID: {video_id}")
                return None
                
        except Exception as e:
            print(f"❌ URL 생성 오류: {e}")
            return None

# 테스트 함수 (디버깅용)
def test_youtube_detector():
    """YouTubeDetector 테스트 함수 (숏츠 포함)"""
    detector = YouTubeDetector()
    
    test_texts = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtube.com/shorts/abc123def45",  # 숏츠 테스트
        "https://www.youtube.com/shorts/xyz789uvw12",  # 숏츠 테스트
        "https://m.youtube.com/shorts/mobile12345",  # 모바일 숏츠
        "Check this out: https://m.youtube.com/watch?v=abc123def45",
        "Multiple links: https://youtube.com/watch?v=test1234567 and https://youtu.be/test7654321",
        "Shorts: https://youtube.com/shorts/short123456",
        "No YouTube links here",
        "https://youtube.com/embed/embedded12345"
    ]
    
    print("🧪 YouTubeDetector 테스트 시작 (숏츠 지원)")
    print("="*60)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n테스트 {i}: {text}")
        video_ids = detector.detect_youtube_urls(text)
        print(f"결과: {video_ids}")
    
    print("\n="*60)
    print("🧪 테스트 완료")

if __name__ == "__main__":
    # 모듈이 직접 실행될 때 테스트 실행
    test_youtube_detector()