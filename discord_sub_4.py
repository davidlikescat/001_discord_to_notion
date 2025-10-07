import os
import asyncio
from typing import Dict, Optional
import google.generativeai as genai
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class GeminiSummarizer:
    """Gemini AI를 사용한 영상 요약 생성"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            print("⚠️ Gemini API 키가 설정되지 않았습니다.")
            print("💡 .env 파일에 GEMINI_API_KEY=your_api_key 를 추가해주세요.")
            return
        
        try:
            genai.configure(api_key=self.api_key)

            preferred_model = os.getenv('GEMINI_MODEL_NAME')
            model_candidates = []
            if preferred_model:
                model_candidates.append(preferred_model)

            # 🔥 가장 안정적인 모델명 우선 시도 (하위 호환성 중시)
            model_candidates.extend([
                'gemini-pro',  # 가장 안정적
                'gemini-1.5-flash',
                'gemini-1.5-pro',
                'models/gemini-1.5-flash-latest',
                'models/gemini-1.5-flash',
                'models/gemini-1.5-pro-latest',
                'models/gemini-1.5-pro',
                'models/gemini-pro',
                'gemini-1.0-pro',
                'models/gemini-1.0-pro'
            ])

            self.model = None
            tried_models = []

            for model_name in model_candidates:
                if model_name in tried_models:
                    continue
                tried_models.append(model_name)

                try:
                    self.model = genai.GenerativeModel(model_name=model_name)
                    print(f"🤖 GeminiSummarizer 초기화 완료 (모델: {model_name})")
                    break
                except Exception as model_error:
                    print(f"   ⚠️ {model_name} 모델 시도 실패: {model_error}")
                    continue

            if not self.model:
                print("❌ 모든 Gemini 모델 초기화 실패. 사용 가능한 모델 목록을 확인하세요.")
                try:
                    available = genai.list_models()
                    supported = [m.name for m in available if hasattr(m, 'supported_generation_methods') and 'generateContent' in m.supported_generation_methods]
                    if supported:
                        print(f"   🔎 generateContent 지원 모델: {supported}")
                except Exception as listing_error:
                    print(f"   ⚠️ 모델 목록 조회 실패: {listing_error}")

        except Exception as e:
            print(f"❌ Gemini API 초기화 실패: {e}")
            self.model = None
    
    async def summarize_with_gemini(self, video_info: Dict, transcript: str, transcript_source: str) -> str:
        """
        Gemini AI로 영상 요약 생성
        
        Args:
            video_info (Dict): 비디오 정보
            transcript (str): 자막 텍스트
            transcript_source (str): 자막 소스
            
        Returns:
            str: 요약 결과
        """
        try:
            print(f"🤖 AI 요약 생성 시작")
            print(f"   영상: {video_info.get('title', 'Unknown')}")
            print(f"   자막 소스: {transcript_source}")
            print(f"   자막 길이: {len(transcript)} 글자")
            
            if not self.model:
                return "❌ Gemini 모델이 초기화되지 않았습니다."
            
            # 자막이 너무 긴 경우 자르기 (토큰 제한 고려)
            max_transcript_length = 8000
            if len(transcript) > max_transcript_length:
                transcript = transcript[:max_transcript_length] + "..."
                print(f"   자막 길이 조정: {max_transcript_length} 글자로 제한")
            
            # 프롬프트 생성
            prompt = self._create_summary_prompt(video_info, transcript, transcript_source)
            
            print("   🔄 Gemini API 호출 중...")
            
            # AI 모델 호출
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                summary = response.text.strip()
                print(f"✅ AI 요약 생성 성공: {len(summary)} 글자")
                return summary
            else:
                print("❌ AI 응답이 비어있음")
                return "요약 생성 중 오류가 발생했습니다."
                
        except Exception as e:
            error_msg = f"Gemini 요약 실패: {e}"
            print(f"❌ {error_msg}")
            return f"요약 생성 중 오류가 발생했습니다: {str(e)}"
    
    def _create_summary_prompt(self, video_info: Dict, transcript: str, transcript_source: str) -> str:
        """요약용 프롬프트 생성"""
        
        # 자막 소스별 설명
        source_descriptions = {
            "youtube_transcript_api_manual_ko": "공식 한국어 자막",
            "youtube_transcript_api_manual_en": "공식 영어 자막",
            "youtube_transcript_api_auto_ko": "자동 생성 한국어 자막",
            "youtube_transcript_api_auto_en": "자동 생성 영어 자막",
            "yt_dlp_manual_ko": "수동 한국어 자막",
            "yt_dlp_manual_en": "수동 영어 자막", 
            "yt_dlp_auto_ko": "자동 한국어 자막",
            "yt_dlp_auto_en": "자동 영어 자막",
            "whisper_api": "AI 음성인식 결과",
            "description": "영상 설명란"
        }
        
        source_desc = source_descriptions.get(transcript_source, "알 수 없는 소스")
        
        # 영상 정보 요약
        video_title = video_info.get('title', '제목 없음')
        video_channel = video_info.get('channel', '채널 없음')
        video_duration = video_info.get('duration', '시간 없음')
        video_description = video_info.get('description', '')[:300] + "..." if len(video_info.get('description', '')) > 300 else video_info.get('description', '')
        
        prompt = f"""
다음 YouTube 영상을 분석하고 구조화된 요약을 작성해주세요:

## 영상 정보
- 제목: {video_title}
- 채널: {video_channel}
- 길이: {video_duration}
- 설명: {video_description}

## 분석 자료
- 자료 종류: {source_desc}
- 내용: {transcript}

다음 형식으로 요약해주세요:

## 📺 영상 개요
- 이 영상의 주제와 핵심 메시지를 2-3줄로 명확하게 요약해주세요
- 시청자가 이 영상을 통해 얻을 수 있는 주요 가치를 설명해주세요

## 🔑 핵심 내용
- 영상에서 다루는 주요 포인트들을 3-5개의 bullet point로 정리해주세요
- 각 포인트는 구체적이고 실용적인 내용으로 작성해주세요

## 💡 인사이트 & 액션 아이템
- 시청자가 실제로 실행할 수 있는 구체적인 팁이나 조언
- 영상에서 얻은 중요한 깨달음이나 배울 점
- 추가로 고려해볼 만한 관련 주제나 질문

## 📝 상세 요약
- 영상의 전체적인 흐름을 시간 순서대로 설명
- 주요 논점, 사례, 데이터 등 구체적인 내용 포함
- 화자의 주장과 근거를 명확히 구분하여 설명

## ℹ️ 메타 정보
- 자막 출처: {source_desc}
- 추천 대상: (이 영상을 누가 봐야 하는지)
- 관련 키워드: (이 영상과 관련된 주요 키워드 3-5개)

한국어로 작성하고, 이모지를 적절히 활용해서 가독성을 높여주세요.
전문적이면서도 이해하기 쉬운 톤으로 작성해주세요.
"""
        
        return prompt

# 🧪 테스트 함수들

def check_available_models():
    """사용 가능한 Gemini 모델 목록 확인"""
    print("🔍 사용 가능한 Gemini 모델 확인")
    print("="*50)
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ API 키가 없습니다.")
        return
    
    try:
        genai.configure(api_key=api_key)
        
        print("📋 사용 가능한 모델 목록:")
        models = genai.list_models()
        
        for model in models:
            if hasattr(model, 'name') and 'gemini' in model.name.lower():
                print(f"   ✅ {model.name}")
                if hasattr(model, 'supported_generation_methods'):
                    methods = getattr(model, 'supported_generation_methods', [])
                    if 'generateContent' in methods:
                        print(f"      🔹 generateContent 지원")
        
    except Exception as e:
        print(f"❌ 모델 목록 조회 실패: {e}")
        print("💡 수동으로 다음 모델들을 시도해보세요:")
        print("   - gemini-1.5-flash")
        print("   - gemini-1.5-pro") 
        print("   - gemini-pro")
        print("   - gemini-1.0-pro")

def check_environment():
    """환경 설정 확인"""
    print("🔍 환경 설정 확인")
    print("="*50)
    
    # 1. .env 파일 확인
    env_file = ".env"
    if os.path.exists(env_file):
        print("✅ .env 파일 발견")
    else:
        print("❌ .env 파일 없음")
        print("   💡 .env 파일을 생성하고 GEMINI_API_KEY를 추가해주세요")
    
    # 2. API 키 확인
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        print(f"✅ GEMINI_API_KEY 설정됨 (길이: {len(api_key)})")
        print(f"   키 미리보기: {api_key[:10]}...")
    else:
        print("❌ GEMINI_API_KEY 환경변수 없음")
    
    # 3. 필수 패키지 확인
    try:
        import google.generativeai
        print("✅ google-generativeai 패키지 설치됨")
    except ImportError:
        print("❌ google-generativeai 패키지 없음")
        print("   💡 pip install google-generativeai 로 설치해주세요")
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv 패키지 설치됨")
    except ImportError:
        print("❌ python-dotenv 패키지 없음")
        print("   💡 pip install python-dotenv 로 설치해주세요")
    
    print()

async def test_gemini_connection():
    """Gemini API 연결 테스트"""
    print("🔗 Gemini API 연결 테스트")
    print("="*50)
    
    summarizer = GeminiSummarizer()
    
    if not summarizer.model:
        print("❌ Gemini 모델 초기화 실패")
        print("💡 다음 사항을 확인해주세요:")
        print("   1. API 키가 올바른지")
        print("   2. 계정에 Gemini API 접근 권한이 있는지")
        print("   3. API 할당량이 남아있는지")
        return False
    
    try:
        # 간단한 테스트 프롬프트
        test_prompt = "안녕하세요! 간단히 '테스트 성공'이라고 답변해주세요."
        print("🔄 간단한 테스트 요청 중...")
        
        response = summarizer.model.generate_content(test_prompt)
        
        if response and response.text:
            print(f"✅ Gemini API 연결 성공!")
            print(f"   응답: {response.text.strip()}")
            return True
        else:
            print("❌ API 응답이 비어있음")
            return False
            
    except Exception as e:
        print(f"❌ Gemini API 연결 실패: {e}")
        
        # 자세한 오류 정보 제공
        if "404" in str(e):
            print("💡 모델을 찾을 수 없습니다. 다른 모델명을 시도해보세요.")
        elif "403" in str(e):
            print("💡 API 접근 권한이 없습니다. API 키와 권한을 확인해주세요.")
        elif "quota" in str(e).lower():
            print("💡 API 할당량을 초과했습니다. 계정 상태를 확인해주세요.")
        
        return False

async def test_full_summarization():
    """전체 요약 기능 테스트"""
    print("\n📝 전체 요약 기능 테스트")
    print("="*50)
    
    summarizer = GeminiSummarizer()
    
    # 테스트 데이터
    test_video_info = {
        'title': 'Python 프로그래밍 기초 강의 - 변수와 함수',
        'channel': 'CodeLab Korea',
        'duration': '15분 30초',
        'view_count': '12345',
        'like_count': '567',
        'published_at': '2024-01-01T00:00:00Z',
        'description': 'Python 프로그래밍의 기초를 배우는 강의입니다. 변수, 함수, 조건문 등 프로그래밍의 핵심 개념들을 쉽게 설명합니다. 초보자도 따라할 수 있는 실습 예제와 함께 진행됩니다.'
    }
    
    test_transcript = """
    안녕하세요. 오늘은 Python 프로그래밍의 기초에 대해 알아보겠습니다.
    
    먼저 변수에 대해 설명드리겠습니다. 변수는 데이터를 저장하는 공간입니다.
    Python에서는 변수를 선언할 때 특별한 키워드가 필요하지 않습니다.
    예를 들어, name = "홍길동" 이렇게 간단히 문자열을 저장할 수 있습니다.
    숫자의 경우에는 age = 25 이런 식으로 저장할 수 있죠.
    
    다음으로 함수에 대해 알아보겠습니다. 함수는 재사용 가능한 코드 블록입니다.
    def greet(name): return f"안녕하세요, {name}님!" 이런 식으로 정의할 수 있습니다.
    함수를 사용하면 코드의 중복을 줄이고 유지보수가 쉬워집니다.
    
    조건문은 특정 조건에 따라 다른 코드를 실행하게 해줍니다.
    if문을 사용해서 age >= 18 이면 "성인입니다"를 출력하고
    그렇지 않으면 "미성년자입니다"를 출력할 수 있습니다.
    
    반복문도 중요한 개념입니다. for문과 while문을 사용해서
    같은 작업을 여러 번 반복할 수 있습니다.
    
    오늘 배운 내용을 정리하면, 변수는 데이터 저장, 함수는 코드 재사용,
    조건문은 분기 처리, 반복문은 반복 작업에 사용됩니다.
    다음 시간에는 리스트와 딕셔너리에 대해 알아보겠습니다.
    """
    
    print(f"📹 테스트 영상: {test_video_info['title']}")
    print(f"📝 자막 길이: {len(test_transcript)} 글자")
    
    # 요약 생성
    summary = await summarizer.summarize_with_gemini(
        test_video_info, 
        test_transcript, 
        "yt_dlp_manual_ko"
    )
    
    print("\n" + "="*50)
    print("📋 생성된 요약:")
    print("="*50)
    print(summary)
    
    return summary

async def main():
    """메인 테스트 함수"""
    print("🚀 GeminiSummarizer 종합 테스트 시작")
    print("="*60)
    
    # 1. 환경 설정 확인
    check_environment()
    
    # 2. 사용 가능한 모델 확인
    check_available_models()
    
    # 3. API 연결 테스트
    connection_ok = await test_gemini_connection()
    
    if not connection_ok:
        print("\n❌ API 연결 실패로 테스트 중단")
        print("💡 다음 사항을 확인해주세요:")
        print("   1. GEMINI_API_KEY가 올바른지")
        print("   2. Google AI Studio에서 API 키 생성했는지 (https://makersuite.google.com/)")
        print("   3. 계정에 Gemini API 접근 권한이 있는지")
        return
    
    # 4. 전체 요약 기능 테스트
    await test_full_summarization()
    
    print("\n" + "="*60)
    print("🎉 모든 테스트 완료!")

# 간단한 동기식 테스트 함수 (Jupyter 등에서 사용)
def simple_test():
    """간단한 동기식 테스트 (asyncio 없이)"""
    print("🔍 간단 테스트 시작")
    check_environment()
    
    # 비동기 함수를 동기식으로 실행
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ 테스트 실행 오류: {e}")

if __name__ == "__main__":
    # 비동기 함수 실행
    asyncio.run(main())
