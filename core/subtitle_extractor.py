"""
통합 자막 추출 모듈
youtube-transcript-api를 우선 사용하고, 실패 시 yt-dlp로 폴백
"""

import os
import tempfile
from typing import Optional, Tuple
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)
import yt_dlp
import urllib.request
import re


class SubtitleExtractor:
    """
    YouTube 자막 추출 통합 클래스
    - 1순위: youtube-transcript-api (빠르고 간단)
    - 2순위: yt-dlp (더 많은 옵션)
    - 3순위: 영상 설명(description) 사용
    """

    def __init__(self, download_dir: Optional[str] = None):
        self.download_dir = download_dir or tempfile.gettempdir()
        self.subtitle_source = ""
        print("📚 SubtitleExtractor 초기화 완료")

    def extract_subtitle_text(self, youtube_url: str, video_id: str = None) -> Tuple[str, str]:
        """
        유튜브 URL에서 자막 추출

        Args:
            youtube_url (str): 유튜브 URL
            video_id (str): 비디오 ID (선택사항)

        Returns:
            Tuple[str, str]: (자막 텍스트, 자막 소스)
        """
        try:
            # video_id 추출
            if not video_id:
                video_id = self._extract_video_id(youtube_url)

            if not video_id:
                print("❌ 비디오 ID를 추출할 수 없습니다.")
                return "", "error"

            print(f"🌐 자막 추출 시작: {video_id}")

            # 1순위: youtube-transcript-api 시도
            transcript, source = self._try_youtube_transcript_api(video_id)
            if transcript:
                return transcript, source

            # 2순위: yt-dlp 시도
            transcript, source = self._try_yt_dlp(youtube_url)
            if transcript:
                return transcript, source

            # 3순위: 영상 설명 사용
            print("⚠️ 모든 자막 추출 방법 실패. 영상 설명을 사용합니다.")
            return "", "no_subtitle"

        except Exception as e:
            print(f"❌ 자막 추출 오류: {e}")
            import traceback
            traceback.print_exc()
            return "", "error"

    def _extract_video_id(self, url: str) -> Optional[str]:
        """URL에서 비디오 ID 추출"""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:shorts\/)([0-9A-Za-z_-]{11})',
            r'^([0-9A-Za-z_-]{11})$'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def _try_youtube_transcript_api(self, video_id: str) -> Tuple[str, str]:
        """
        youtube-transcript-api로 자막 추출 시도

        Returns:
            Tuple[str, str]: (자막 텍스트, 자막 소스)
        """
        try:
            print("🔄 youtube-transcript-api로 자막 추출 시도...")

            # 사용 가능한 자막 목록 가져오기
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # 1. 한국어 수동 자막 우선
            try:
                transcript = transcript_list.find_manually_created_transcript(['ko'])
                text = self._format_transcript(transcript.fetch())
                print(f"✅ 한국어 수동 자막 추출 성공: {len(text)} 글자")
                return text, "youtube_transcript_api_manual_ko"
            except:
                pass

            # 2. 영어 수동 자막
            try:
                transcript = transcript_list.find_manually_created_transcript(['en'])
                text = self._format_transcript(transcript.fetch())
                print(f"✅ 영어 수동 자막 추출 성공: {len(text)} 글자")
                return text, "youtube_transcript_api_manual_en"
            except:
                pass

            # 3. 한국어 자동 생성 자막
            try:
                transcript = transcript_list.find_generated_transcript(['ko'])
                text = self._format_transcript(transcript.fetch())
                print(f"✅ 한국어 자동 자막 추출 성공: {len(text)} 글자")
                return text, "youtube_transcript_api_auto_ko"
            except:
                pass

            # 4. 영어 자동 생성 자막
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
                text = self._format_transcript(transcript.fetch())
                print(f"✅ 영어 자동 자막 추출 성공: {len(text)} 글자")
                return text, "youtube_transcript_api_auto_en"
            except:
                pass

            # 5. 다른 언어 자막을 한국어로 번역
            try:
                available_transcripts = list(transcript_list)
                if available_transcripts:
                    first_transcript = available_transcripts[0]
                    translated = first_transcript.translate('ko')
                    text = self._format_transcript(translated.fetch())
                    print(f"✅ 자막 번역 성공 ({first_transcript.language} → ko): {len(text)} 글자")
                    return text, "youtube_transcript_api_translated_ko"
            except:
                pass

            print("❌ youtube-transcript-api: 사용 가능한 자막 없음")
            return "", ""

        except TranscriptsDisabled:
            print("❌ youtube-transcript-api: 자막 비활성화됨")
            return "", ""
        except NoTranscriptFound:
            print("❌ youtube-transcript-api: 자막을 찾을 수 없음")
            return "", ""
        except VideoUnavailable:
            print("❌ youtube-transcript-api: 비디오를 사용할 수 없음")
            return "", ""
        except Exception as e:
            print(f"❌ youtube-transcript-api 오류: {e}")
            return "", ""

    def _format_transcript(self, transcript_data: list) -> str:
        """
        youtube-transcript-api의 transcript 데이터를 텍스트로 변환

        Args:
            transcript_data (list): [{'text': '...', 'start': 0.0, 'duration': 1.5}, ...]

        Returns:
            str: 포맷된 텍스트
        """
        if not transcript_data:
            return ""

        # 텍스트만 추출
        texts = [item['text'].strip() for item in transcript_data if item.get('text')]

        # 중복 제거
        deduplicated = self._remove_consecutive_duplicates(texts)

        # 줄바꿈으로 연결
        return '\n'.join(deduplicated)

    def _try_yt_dlp(self, youtube_url: str) -> Tuple[str, str]:
        """
        yt-dlp로 자막 추출 시도

        Returns:
            Tuple[str, str]: (자막 텍스트, 자막 소스)
        """
        try:
            print("🔄 yt-dlp로 자막 추출 시도...")

            ydl_opts = {
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['ko', 'en'],
                'subtitlesformat': 'vtt',
                'skip_download': True,
                'outtmpl': os.path.join(self.download_dir, '%(title)s.%(ext)s'),
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)

                subtitles = info.get('subtitles', {})
                automatic_captions = info.get('automatic_captions', {})

                print(f"📋 수동 자막: {list(subtitles.keys())}")
                print(f"📋 자동 자막: {list(automatic_captions.keys())}")

                # 우선순위: ko 수동 > en 수동 > ko 자동 > en 자동
                subtitle_data = None
                source = ""

                if 'ko' in subtitles:
                    subtitle_data = subtitles['ko']
                    source = "yt_dlp_manual_ko"
                elif 'en' in subtitles:
                    subtitle_data = subtitles['en']
                    source = "yt_dlp_manual_en"
                elif 'ko' in automatic_captions:
                    subtitle_data = automatic_captions['ko']
                    source = "yt_dlp_auto_ko"
                elif 'en' in automatic_captions:
                    subtitle_data = automatic_captions['en']
                    source = "yt_dlp_auto_en"

                if not subtitle_data:
                    print("❌ yt-dlp: 사용 가능한 자막 없음")
                    return "", ""

                # 자막 URL 추출
                subtitle_url = None
                for subtitle_format in subtitle_data:
                    if subtitle_format.get('ext') in ['vtt', 'srt']:
                        subtitle_url = subtitle_format['url']
                        break

                if not subtitle_url:
                    print("❌ yt-dlp: 자막 URL을 찾을 수 없음")
                    return "", ""

                # 자막 다운로드
                with urllib.request.urlopen(subtitle_url) as response:
                    subtitle_content = response.read().decode('utf-8')

                # VTT/SRT 파싱
                clean_text = self._clean_subtitle_text(subtitle_content)

                if clean_text and len(clean_text) > 10:
                    print(f"✅ yt-dlp 자막 추출 성공 ({source}): {len(clean_text)} 글자")
                    return clean_text, source
                else:
                    print(f"❌ yt-dlp: 자막이 너무 짧음 ({len(clean_text)} 글자)")
                    return "", ""

        except Exception as e:
            print(f"❌ yt-dlp 오류: {e}")
            return "", ""

    def _clean_subtitle_text(self, subtitle_content: str) -> str:
        """VTT/SRT 형식에서 순수 텍스트만 추출"""
        lines = subtitle_content.split('\n')
        text_lines = []

        for line in lines:
            line = line.strip()

            # VTT 헤더, 시간 정보 스킵
            if (line.startswith('WEBVTT') or
                '-->' in line or
                line.isdigit() or
                line == '' or
                line.startswith('NOTE') or
                line.startswith('Kind:') or
                line.startswith('Language:')):
                continue

            # HTML 태그 제거
            line = re.sub(r'<[^>]+>', '', line)

            if line:
                text_lines.append(line)

        # 중복 제거
        deduplicated = self._remove_consecutive_duplicates(text_lines)

        return '\n'.join(deduplicated)

    def _remove_consecutive_duplicates(self, lines: list) -> list:
        """연속된 중복 라인 제거"""
        if not lines:
            return []

        result = [lines[0]]

        for i in range(1, len(lines)):
            if lines[i].strip() != lines[i-1].strip():
                result.append(lines[i])

        return result

    def get_available_subtitles(self, youtube_url: str) -> dict:
        """사용 가능한 자막 정보 조회"""
        try:
            video_id = self._extract_video_id(youtube_url)
            if not video_id:
                return {}

            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            manual_langs = []
            auto_langs = []

            for transcript in transcript_list:
                if transcript.is_generated:
                    auto_langs.append(transcript.language_code)
                else:
                    manual_langs.append(transcript.language_code)

            return {
                'video_id': video_id,
                'manual_subtitles': manual_langs,
                'automatic_captions': auto_langs
            }

        except Exception as e:
            print(f"❌ 자막 정보 조회 오류: {e}")
            return {}


# 테스트용 함수
if __name__ == "__main__":
    print("🧪 SubtitleExtractor 테스트")
    print("=" * 60)

    extractor = SubtitleExtractor()

    # 테스트 URL (실제 테스트 시 유효한 URL로 변경)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    # 자막 정보 조회
    print("1️⃣ 사용 가능한 자막 조회:")
    info = extractor.get_available_subtitles(test_url)
    print(f"   수동 자막: {info.get('manual_subtitles', [])}")
    print(f"   자동 자막: {info.get('automatic_captions', [])}")

    # 자막 추출
    print("\n2️⃣ 자막 추출:")
    transcript, source = extractor.extract_subtitle_text(test_url)
    print(f"   소스: {source}")
    print(f"   길이: {len(transcript)} 글자")
    if transcript:
        print(f"   미리보기: {transcript[:200]}...")

    print("\n" + "=" * 60)
    print("✅ 테스트 완료")
