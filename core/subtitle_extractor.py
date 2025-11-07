"""
YouTube 자막 추출 모듈
youtube-transcript-api 사용 (무료)
"""
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound


class SubtitleExtractor:
    def __init__(self):
        pass

    def extract_subtitle_text(self, youtube_url: str, video_id: str) -> tuple:
        """
        YouTube 자막 추출
        Returns: (transcript_text, source)
        """
        try:
            # 자막 추출 시도
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # 1순위: 한국어 자막
            try:
                transcript = transcript_list.find_transcript(['ko'])
                texts = [entry['text'] for entry in transcript.fetch()]
                full_text = '\n'.join(texts)
                print(f"✅ 한국어 자막 추출 성공: {len(full_text)} 글자")
                return full_text, 'youtube-transcript-api (ko)'
            except:
                pass

            # 2순위: 영어 자막
            try:
                transcript = transcript_list.find_transcript(['en'])
                texts = [entry['text'] for entry in transcript.fetch()]
                full_text = '\n'.join(texts)
                print(f"✅ 영어 자막 추출 성공: {len(full_text)} 글자")
                return full_text, 'youtube-transcript-api (en)'
            except:
                pass

            # 3순위: 자동 생성 자막
            try:
                transcript = transcript_list.find_generated_transcript(['ko', 'en'])
                texts = [entry['text'] for entry in transcript.fetch()]
                full_text = '\n'.join(texts)
                print(f"✅ 자동 생성 자막 추출 성공: {len(full_text)} 글자")
                return full_text, 'youtube-transcript-api (auto)'
            except:
                pass

            print("❌ 사용 가능한 자막이 없습니다.")
            return None, None

        except TranscriptsDisabled:
            print("❌ 이 영상은 자막이 비활성화되어 있습니다.")
            return None, None

        except NoTranscriptFound:
            print("❌ 자막을 찾을 수 없습니다.")
            return None, None

        except Exception as e:
            print(f"❌ 자막 추출 오류: {e}")
            return None, None


if __name__ == '__main__':
    # 테스트
    extractor = SubtitleExtractor()
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    test_id = "dQw4w9WgXcQ"

    transcript, source = extractor.extract_subtitle_text(test_url, test_id)
    if transcript:
        print(f"\n처음 500자:\n{transcript[:500]}")
        print(f"\nSource: {source}")
