# 노션 연동 설정 가이드 및 테스트

"""
🚀 노션 연동 완전 가이드
======================

## 1단계: 노션 Integration 생성
1. https://www.notion.so/my-integrations 접속
2. "+ New integration" 클릭
3. 이름 입력 (예: "YouTube Summarizer")
4. "Submit" 클릭
5. "Internal Integration Token" 복사 → 이것이 NOTION_API_KEY

## 2단계: 노션 데이터베이스 생성
1. 노션에서 새 페이지 생성
2. "/database" 입력 → "Table - Inline" 선택
3. 다음 속성들 추가:

필수 속성:
- 제목 (Title) - 기본 제공
- 채널 (Text)
- URL (URL)
- 조회수 (Number)
- 좋아요 (Number)
- 길이 (Text)
- 자막소스 (Text)
- 디스코드채널 (Text)
- 상태 (Select) - 옵션: 요약완료, 처리중, 실패
- 등록일 (Date) - 선택적

## 3단계: 데이터베이스 연결 설정
1. 데이터베이스 페이지에서 "..." → "Connections" → 생성한 Integration 추가
2. 데이터베이스 URL에서 ID 추출:
   https://notion.so/username/DATABASE_ID?v=VIEW_ID
   ↑ 이 부분이 NOTION_DATABASE_ID

## 4단계: .env 파일 설정
NOTION_API_KEY=your_integration_token_here
NOTION_DATABASE_ID=your_database_id_here
"""

import os
import asyncio
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# discord_sub_5.py의 NotionSaver 클래스를 직접 포함
import json
import requests
from typing import Dict, Optional
from datetime import datetime

class NotionSaver:
    """노션 데이터베이스에 영상 정보 저장"""
    
    def __init__(self):
        self.api_key = os.getenv('NOTION_API_KEY')
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        self.notion_version = '2022-06-28'
        
        if not self.api_key:
            print("⚠️ Notion API 키가 설정되지 않았습니다.")
        if not self.database_id:
            print("⚠️ Notion 데이터베이스 ID가 설정되지 않았습니다.")
        
        if self.api_key and self.database_id:
            print("💾 NotionSaver 초기화 완료")
        
        # 자막 소스별 설명
        self.source_descriptions = {
            "youtube_transcript_api_manual_ko": "공식 한국어 자막",
            "youtube_transcript_api_manual_en": "공식 영어 자막",
            "youtube_transcript_api_auto_ko": "자동 한국어 자막",
            "youtube_transcript_api_auto_en": "자동 영어 자막",
            "yt_dlp_manual_ko": "수동 한국어 자막",
            "yt_dlp_manual_en": "수동 영어 자막", 
            "yt_dlp_auto_ko": "자동 한국어 자막",
            "yt_dlp_auto_en": "자동 영어 자막",
            "whisper_api": "AI 음성인식",
            "description": "영상 설명란"
        }
    
    async def save_to_notion(self, video_info: Dict, summary: str, video_url: str, 
                           discord_info: Dict, transcript_source: str) -> Optional[str]:
        """
        노션 데이터베이스에 영상 정보와 요약 저장
        
        Args:
            video_info (Dict): 비디오 정보
            summary (str): AI 요약 결과
            video_url (str): 유튜브 비디오 URL
            discord_info (Dict): 디스코드 관련 정보
            transcript_source (str): 자막 소스
            
        Returns:
            str: 노션 페이지 URL 또는 None
        """
        try:
            print(f"💾 노션 저장 시작")
            print(f"   제목: {video_info.get('title', 'Unknown')}")
            print(f"   자막 소스: {transcript_source}")
            
            if not self.api_key or not self.database_id:
                print("❌ Notion API 키 또는 데이터베이스 ID가 없습니다.")
                return None
            
            # 요청 헤더 설정
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Notion-Version': self.notion_version
            }
            
            # 노션 페이지 데이터 구성
            page_data = self._create_page_data(video_info, summary, video_url, 
                                             discord_info, transcript_source)
            
            # 노션 API 호출
            response = requests.post(
                'https://api.notion.com/v1/pages',
                headers=headers,
                data=json.dumps(page_data)
            )
            
            if response.status_code == 200:
                notion_page = response.json()
                page_url = notion_page.get('url', '')
                
                print(f"✅ 노션 저장 성공")
                print(f"   페이지 URL: {page_url}")
                
                return page_url
            else:
                print(f"❌ 노션 저장 실패: {response.status_code}")
                print(f"   응답: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ NotionSaver 오류: {e}")
            return None
    
    def _create_page_data(self, video_info: Dict, summary: str, video_url: str,
                         discord_info: Dict, transcript_source: str) -> Dict:
        """노션 페이지 데이터 구성"""
        
        # 안전한 정수 변환
        def safe_int(value, default=0):
            try:
                return int(value) if value else default
            except (ValueError, TypeError):
                return default
        
        # 자막 소스 설명
        source_desc = self.source_descriptions.get(transcript_source, "알 수 없는 소스")
        
        # 현재 시간을 ISO 8601 형식으로 생성
        current_time = datetime.now().isoformat() + "Z"  # UTC 시간으로 설정
        
        # 페이지 속성 구성 (실제 노션 데이터베이스 속성명에 맞춤)
        properties = {
            "Title": {  # 노션에서는 영어로 Title
                "title": [
                    {
                        "text": {
                            "content": video_info.get('title', '제목 없음')
                        }
                    }
                ]
            },
            "Channel": {  # 영어 속성명
                "rich_text": [
                    {
                        "text": {
                            "content": video_info.get('channel', '채널 없음')
                        }
                    }
                ]
            },
            "URL": {  # 그대로 URL
                "url": video_url
            },
            "Status": {  # 영어 속성명
                "select": {
                    "name": "요약완료"
                }
            },
            "Duration": {  # 영어 속성명
                "rich_text": [
                    {
                        "text": {
                            "content": video_info.get('duration', '알 수 없음')
                        }
                    }
                ]
            },
            "Created": {  # 생성일 속성
                "date": {
                    "start": current_time
                }
            }
        }
        
        # 등록일 처리 (Created 속성은 노션에서 자동 생성되므로 제거)
        # published_at은 요약 내용에 포함하거나 별도 속성으로 추가 필요시에만 사용
        
        # 페이지 콘텐츠 (children) 구성
        children = []
        
        # 메타데이터 정보 추가 (조회수, 좋아요 제거)
        metadata_text = f"""📺 **영상 정보**
• 채널: {video_info.get('channel', '알 수 없음')}
• 길이: {video_info.get('duration', '알 수 없음')}
• 요청자: #{discord_info.get('channel', 'unknown')} - {discord_info.get('author', 'unknown')}
• 자막 소스: {source_desc}
• 원본 URL: {video_url}

---
"""
        
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": metadata_text
                        }
                    }
                ]
            }
        })
        
        # 썸네일 이미지 추가 (원본 유지)
        thumbnail_url = video_info.get('thumbnail', '')
        if thumbnail_url:
            children.append({
                "object": "block",
                "type": "image",
                "image": {
                    "type": "external",
                    "external": {
                        "url": thumbnail_url
                    }
                }
            })
        
        # 요약 내용 추가 - 🔥 마크다운 블록으로 변환
        if summary:
            # 요약을 Notion 블록으로 변환
            summary_blocks = self._split_summary_into_paragraphs(summary)
            
            # 각 블록을 children에 추가
            for block in summary_blocks:
                children.append(block)
        
        # 최종 페이지 데이터
        page_data = {
            "parent": {"database_id": self.database_id},
            "properties": properties,
            "children": children
        }
        
        return page_data
    
    def _split_summary_into_paragraphs(self, summary: str) -> list:
        """요약을 문단별로 나누기 - 🔥 마크다운 파싱 추가"""
        try:
            # 마크다운을 Notion 블록으로 파싱
            blocks = self._parse_markdown_to_blocks(summary)
            return blocks
            
        except Exception as e:
            print(f"❌ 마크다운 파싱 오류: {e}")
            # 실패시 원본 그대로 반환
            return [{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": summary}}]}}]
    
    def _parse_markdown_to_blocks(self, text: str) -> list:
        """마크다운을 Notion 블록으로 변환"""
        import re
        
        lines = text.split('\n')
        blocks = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 헤딩 처리
            if line.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2", 
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                    }
                })
            elif line.startswith('### '):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": line[4:]}}]
                    }
                })
            elif line.startswith('# '):
                blocks.append({
                    "object": "block", 
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                    }
                })
            # 불릿 리스트 처리
            elif line.startswith('- '):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": self._parse_inline_formatting(line[2:])
                    }
                })
            # 일반 문단
            else:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": self._parse_inline_formatting(line)
                    }
                })
        
        return blocks
    
    def _parse_inline_formatting(self, text: str) -> list:
        """인라인 포맷팅 (볼드, 이탤릭) 처리"""
        import re
        
        parts = []
        
        # **볼드** 패턴 처리
        bold_pattern = r'\*\*(.*?)\*\*'
        last_end = 0
        
        for match in re.finditer(bold_pattern, text):
            # 볼드 이전 일반 텍스트
            if match.start() > last_end:
                plain_text = text[last_end:match.start()]
                if plain_text:
                    parts.append({
                        "type": "text",
                        "text": {"content": plain_text},
                        "annotations": {"bold": False}
                    })
            
            # 볼드 텍스트  
            bold_text = match.group(1)
            parts.append({
                "type": "text",
                "text": {"content": bold_text},
                "annotations": {"bold": True}
            })
            
            last_end = match.end()
        
        # 남은 텍스트
        if last_end < len(text):
            remaining = text[last_end:]
            if remaining:
                parts.append({
                    "type": "text", 
                    "text": {"content": remaining},
                    "annotations": {"bold": False}
                })
        
        # 포맷팅이 없으면 일반 텍스트
        if not parts:
            parts.append({
                "type": "text",
                "text": {"content": text}
            })
        
        return parts
    
    def test_database_connection(self) -> bool:
        """노션 데이터베이스 연결 테스트"""
        try:
            print("🧪 노션 데이터베이스 연결 테스트")
            
            if not self.api_key or not self.database_id:
                print("❌ API 키 또는 데이터베이스 ID가 없습니다.")
                return False
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Notion-Version': self.notion_version
            }
            
            # 데이터베이스 정보 조회
            response = requests.get(
                f'https://api.notion.com/v1/databases/{self.database_id}',
                headers=headers
            )
            
            if response.status_code == 200:
                db_info = response.json()
                print(f"✅ 데이터베이스 연결 성공")
                print(f"   데이터베이스 제목: {db_info.get('title', [{}])[0].get('plain_text', 'Unknown')}")
                return True
            else:
                print(f"❌ 데이터베이스 연결 실패: {response.status_code}")
                print(f"   응답: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 연결 테스트 오류: {e}")
            return False
    
    def get_database_properties(self) -> Optional[Dict]:
        """데이터베이스 속성 정보 조회"""
        try:
            print("📋 데이터베이스 속성 정보 조회")
            
            if not self.api_key or not self.database_id:
                return None
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Notion-Version': self.notion_version
            }
            
            response = requests.get(
                f'https://api.notion.com/v1/databases/{self.database_id}',
                headers=headers
            )
            
            if response.status_code == 200:
                db_info = response.json()
                properties = db_info.get('properties', {})
                
                print("✅ 데이터베이스 속성:")
                for prop_name, prop_info in properties.items():
                    prop_type = prop_info.get('type', 'unknown')
                    print(f"   - {prop_name}: {prop_type}")
                
                return properties
            else:
                print(f"❌ 속성 조회 실패: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 속성 조회 오류: {e}")
            return None

def check_notion_setup():
    """노션 설정 상태 확인"""
    print("🔍 노션 연동 설정 확인")
    print("="*50)
    
    # 환경 변수 확인
    api_key = os.getenv('NOTION_API_KEY')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if api_key:
        print(f"✅ NOTION_API_KEY 설정됨 (길이: {len(api_key)})")
        print(f"   키 미리보기: {api_key[:20]}...")
    else:
        print("❌ NOTION_API_KEY 환경변수 없음")
        print("💡 .env 파일에 NOTION_API_KEY=your_token 추가 필요")
    
    if database_id:
        print(f"✅ NOTION_DATABASE_ID 설정됨")
        print(f"   ID: {database_id}")
    else:
        print("❌ NOTION_DATABASE_ID 환경변수 없음")
        print("💡 .env 파일에 NOTION_DATABASE_ID=your_db_id 추가 필요")
    
    # .env 파일 확인
    env_file = ".env"
    if os.path.exists(env_file):
        print("✅ .env 파일 발견")
    else:
        print("❌ .env 파일 없음")
    
    print()
    return bool(api_key and database_id)

def create_sample_env_file():
    """샘플 .env 파일 생성"""
    print("📝 샘플 .env 파일 생성")
    print("="*50)
    
    sample_content = """# YouTube Summarizer 환경 변수

# Gemini AI API 키 (Google AI Studio에서 생성)
GEMINI_API_KEY=your_gemini_api_key_here

# Notion Integration Token (https://www.notion.so/my-integrations)
NOTION_API_KEY=secret_your_notion_integration_token_here

# Notion Database ID (데이터베이스 URL에서 추출)
NOTION_DATABASE_ID=your_database_id_here

# Discord Bot Token (선택적)
DISCORD_BOT_TOKEN=your_discord_bot_token_here
"""
    
    try:
        with open('.env.sample', 'w', encoding='utf-8') as f:
            f.write(sample_content)
        print("✅ .env.sample 파일 생성 완료")
        print("💡 이 파일을 .env로 복사하고 실제 값으로 수정하세요")
    except Exception as e:
        print(f"❌ 샘플 파일 생성 실패: {e}")

async def test_notion_full_workflow():
    """노션 전체 워크플로우 테스트"""
    print("🧪 노션 전체 워크플로우 테스트")
    print("="*60)
    
    # 1. 설정 확인
    if not check_notion_setup():
        print("❌ 노션 설정이 완료되지 않았습니다.")
        create_sample_env_file()
        return
    
    # 2. NotionSaver 초기화
    saver = NotionSaver()
    
    # 3. 연결 테스트
    print("1️⃣ 데이터베이스 연결 테스트")
    connection_ok = saver.test_database_connection()
    
    if not connection_ok:
        print("❌ 연결 실패")
        print("💡 다음 사항을 확인해주세요:")
        print("   1. Integration Token이 올바른지")
        print("   2. 데이터베이스 ID가 올바른지")
        print("   3. Integration이 데이터베이스에 연결되어 있는지")
        return
    
    # 4. 속성 조회
    print("\n2️⃣ 데이터베이스 속성 조회")
    properties = saver.get_database_properties()
    
    # 5. 테스트 데이터 저장
    print("\n3️⃣ 테스트 데이터 저장")
    
    # 현재 시간을 포함한 고유한 제목
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    test_video_info = {
        'title': f'[테스트] 노션 연동 테스트 - {timestamp}',
        'channel': 'YouTube Summarizer Bot',
        'duration': '10분 15초',
        'view_count': '15420',
        'like_count': '892',
        'published_at': '2024-05-24T10:30:00Z',
        'description': '노션 연동 기능을 테스트하기 위한 샘플 영상입니다.',
        'thumbnail': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg'
    }
    
    test_summary = f"""## 📺 영상 개요
- 이것은 노션 연동 기능을 테스트하기 위한 샘플 요약입니다.
- 테스트 시간: {timestamp}
- 모든 기능이 정상적으로 작동하는지 확인합니다.

## 🔑 핵심 내용
- ✅ 노션 API 연결 성공
- ✅ 데이터베이스 속성 매핑 완료
- ✅ 자동 요약 생성 기능
- ✅ 디스코드 봇 연동 준비
- ✅ 썸네일 이미지 삽입

## 💡 인사이트 & 액션 아이템
- 노션 연동이 성공적으로 완료되었습니다!
- 이제 실제 유튜브 영상을 요약해서 저장할 수 있습니다.
- 다음 단계: 디스코드 봇과 연결하여 자동화

## 📝 상세 요약
**테스트 진행 과정:**

1. **환경 설정 확인**: API 키와 데이터베이스 ID가 올바르게 설정되었는지 확인
2. **연결 테스트**: 노션 API와의 통신이 정상적으로 이루어지는지 테스트
3. **속성 매핑**: 데이터베이스의 속성들이 코드와 일치하는지 확인
4. **데이터 저장**: 실제 영상 정보와 요약을 노션에 저장

**확인된 기능:**
- 제목, 채널, URL 등 기본 정보 저장
- 조회수, 좋아요 수 등 숫자 데이터 처리
- 긴 요약 텍스트의 문단별 분할
- 썸네일 이미지 자동 삽입
- 자막 소스 정보 기록

## ℹ️ 메타 정보
- 자막 출처: 테스트용 수동 입력
- 추천 대상: 노션 연동 기능을 확인하고 싶은 개발자
- 관련 키워드: 노션, API, 데이터베이스, 자동화, 테스트

**🎉 테스트 결과: 성공! 모든 기능이 정상 작동합니다.**
"""
    
    test_discord_info = {
        'channel': 'youtube-summary',
        'author': 'TestUser'
    }
    
    # 실제 저장 시도
    print("🔄 노션에 테스트 데이터 저장 중...")
    notion_url = await saver.save_to_notion(
        test_video_info,
        test_summary,
        'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        test_discord_info,
        'test_manual_ko'
    )
    
    if notion_url:
        print(f"🎉 테스트 성공!")
        print(f"📄 노션 페이지: {notion_url}")
        print("\n💡 이제 실제 유튜브 영상으로 테스트해보세요!")
    else:
        print("❌ 저장 실패")
        print("💡 오류 메시지를 확인하고 설정을 다시 점검해주세요")

def print_setup_instructions():
    """설정 방법 출력"""
    print("""
🔧 노션 연동 설정 방법
===================

1️⃣ 노션 Integration 생성:
   - https://www.notion.so/my-integrations 접속
   - "+ New integration" 클릭
   - 이름: "YouTube Summarizer"
   - Integration Token 복사

2️⃣ 노션 데이터베이스 생성:
   - 새 페이지에서 /database 입력
   - Table - Inline 선택
   - 필요한 속성들 추가 (제목, 채널, URL, 조회수, 좋아요, 길이, 자막소스, 디스코드채널, 상태, 등록일)

3️⃣ 데이터베이스 연결:
   - 데이터베이스 페이지 → "..." → "Connections" → Integration 추가
   - URL에서 데이터베이스 ID 복사

4️⃣ .env 파일 설정:
   NOTION_API_KEY=your_integration_token
   NOTION_DATABASE_ID=your_database_id

5️⃣ 테스트 실행:
   python notion_test.py
""")

async def quick_test():
    """빠른 연결 테스트만"""
    print("⚡ 빠른 노션 연결 테스트")
    print("="*40)
    
    if not check_notion_setup():
        print_setup_instructions()
        return
    
    saver = NotionSaver()
    connection_ok = saver.test_database_connection()
    
    if connection_ok:
        print("🎉 노션 연결 성공! 이제 전체 테스트를 실행하세요.")
        print("💡 python notion_test.py 실행")
    else:
        print("❌ 연결 실패. 설정을 다시 확인해주세요.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        # 빠른 테스트
        asyncio.run(quick_test())
    else:
        # 전체 테스트
        asyncio.run(test_notion_full_workflow())
