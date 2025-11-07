"""
AI 요약 모듈
Gemini 2.0 Flash 사용 (무료)
"""
import os
import google.generativeai as genai


class GeminiSummarizer:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            print("⚠️ GEMINI_API_KEY가 설정되지 않았습니다.")
            self.model = None
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            print("✅ Gemini 2.0 Flash 초기화 완료")

    def summarize(self, video_info: dict, transcript: str, prompt_key: str = 'archive') -> str:
        """
        Gemini로 영상 요약
        """
        if not self.model:
            return "❌ Gemini API 키가 설정되지 않았습니다."

        # 자막 길이 제한 (토큰 절약)
        max_chars = 24000  # 약 8K tokens
        if len(transcript) > max_chars:
            transcript = transcript[:max_chars] + "\n\n...(이하 생략)"
            print(f"⚠️ 자막이 너무 길어 {max_chars}자로 제한했습니다.")

        # 프롬프트 구성
        system_prompts = {
            'archive': """당신은 텍스트 정제 및 아카이브 전문가입니다.

주요 작업:
1. 영상 자막/설명을 한글로 정제 (영어는 번역 후 정제)
2. 1000줄 이내로 정제 및 정리
3. 일목요연하게 구조화하여 가독성 향상
4. 핵심 내용만 추출하여 마크다운 형식으로 작성

출력 형식:
# 제목

## 핵심 요약
- 주요 포인트 1
- 주요 포인트 2
- ...

## 상세 내용
(구조화된 본문)

## 주요 인사이트
- 인사이트 1
- 인사이트 2
""",
            'agent-reference': """당신은 AI 에이전트 참고자료 번역 및 정리 전문가입니다.

주요 작업:
1. 영상 내용을 한글로 번역 및 정제
2. AI 에이전트 개발/활용에 유용한 인사이트 추출
3. 실무에 바로 적용 가능한 정보 우선 정리
4. 마크다운 형식으로 작성

출력 형식:
# AI 에이전트 관련 핵심 내용

## 주요 개념
- 개념 1
- 개념 2

## 구현 방법
(실무 적용 가능한 내용)

## 활용 사례
- 사례 1
- 사례 2

## 참고 사항
(추가 정보)
"""
        }

        system_prompt = system_prompts.get(prompt_key, system_prompts['archive'])

        prompt = f"""{system_prompt}

---

영상 제목: {video_info['title']}
채널: {video_info['channel']}
길이: {video_info['duration']}

자막 내용:
{transcript}

---

위 내용을 요약하고 정제해주세요.
"""

        try:
            print("🤖 Gemini AI 요약 시작...")
            response = self.model.generate_content(prompt)
            summary = response.text

            print(f"✅ AI 요약 완료: {len(summary)} 글자")
            return summary

        except Exception as e:
            print(f"❌ Gemini API 오류: {e}")
            return f"❌ AI 요약 중 오류가 발생했습니다: {str(e)}"


# Claude Haiku 백업 옵션 (유료지만 저렴)
class ClaudeSummarizer:
    def __init__(self, model_name: str = 'claude-3-haiku-20240307'):
        import anthropic
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            print("⚠️ ANTHROPIC_API_KEY가 설정되지 않았습니다.")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model_name = model_name
            print(f"✅ Claude {model_name} 초기화 완료")

    def summarize(self, video_info: dict, transcript: str, prompt_key: str = 'archive', max_tokens: int = 2048) -> str:
        """Claude로 영상 요약"""
        if not self.client:
            return "❌ Claude API 키가 설정되지 않았습니다."

        # 자막 길이 제한
        max_chars = 24000
        if len(transcript) > max_chars:
            transcript = transcript[:max_chars] + "\n\n...(이하 생략)"

        system_prompts = {
            'archive': """당신은 텍스트 정제 및 아카이브 전문가입니다.
영상 자막을 한글로 정제하고 1000줄 이내로 요약하여 마크다운 형식으로 작성하세요.""",
            'agent-reference': """당신은 AI 에이전트 참고자료 전문가입니다.
AI 에이전트 개발/활용에 유용한 인사이트를 추출하여 마크다운 형식으로 작성하세요."""
        }

        system_prompt = system_prompts.get(prompt_key, system_prompts['archive'])

        try:
            print(f"🤖 Claude AI 요약 시작 (모델: {self.model_name})...")

            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"""영상 제목: {video_info['title']}
채널: {video_info['channel']}

자막:
{transcript}

위 내용을 요약하고 정제해주세요."""
                }]
            )

            summary = message.content[0].text
            print(f"✅ Claude 요약 완료: {len(summary)} 글자")
            return summary

        except Exception as e:
            print(f"❌ Claude API 오류: {e}")
            return f"❌ AI 요약 중 오류가 발생했습니다: {str(e)}"


if __name__ == '__main__':
    # 테스트
    from dotenv import load_dotenv
    load_dotenv()

    # Gemini 테스트
    summarizer = GeminiSummarizer()

    test_video_info = {
        'title': 'Test Video',
        'channel': 'Test Channel',
        'duration': '10:00'
    }

    test_transcript = "This is a test transcript. " * 100

    summary = summarizer.summarize(test_video_info, test_transcript)
    print(f"\n요약 결과:\n{summary[:500]}...")
