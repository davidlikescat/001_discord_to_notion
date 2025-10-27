"""
Notion 저장 모듈
채널별 Notion 데이터베이스에 영상 정보와 요약 저장
YouTube URL 임베딩 포함
"""

import os
import json
import requests
from typing import Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


class NotionSaver:
    """
    Notion API를 사용한 데이터베이스 저장
    채널별 설정 지원
    """

    def __init__(self):
        self.api_key = os.getenv('NOTION_API_KEY')
        self.notion_version = '2022-06-28'

        if not self.api_key:
            print("⚠️ Notion API 키가 설정되지 않았습니다.")
        else:
            print("💾 NotionSaver 초기화 완료")

    async def save_to_notion(
        self,
        video_info: Dict,
        summary: str,
        video_url: str,
        channel_config: Dict,
        discord_info: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Notion 데이터베이스에 영상 정보와 요약 저장

        Args:
            video_info (Dict): 비디오 정보
            summary (str): AI 요약 결과
            video_url (str): 유튜브 비디오 URL
            channel_config (Dict): 채널 설정 정보
            discord_info (Dict): 디스코드 관련 정보 (선택사항)

        Returns:
            str: 노션 페이지 URL 또는 None
        """
        try:
            database_id = channel_config.get('notion_database_id')
            channel_name = channel_config.get('channel_name', 'unknown')

            print(f"💾 Notion 저장 시작 ({channel_name})")
            print(f"   제목: {video_info.get('title', 'Unknown')}")
            print(f"   DB ID: {database_id}")

            if not self.api_key or not database_id:
                print("❌ Notion API 키 또는 데이터베이스 ID가 없습니다.")
                return None

            # 요청 헤더 설정
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Notion-Version': self.notion_version
            }

            # 노션 페이지 데이터 구성
            page_data = self._create_page_data(
                video_info,
                summary,
                video_url,
                channel_config,
                discord_info
            )

            # 블록 수 확인
            children = page_data.get('children', [])
            total_blocks = len(children)
            print(f"   총 블록 수: {total_blocks}개")

            # 100개 블록 제한 처리
            if total_blocks > 100:
                print(f"   ⚠️ 블록이 100개를 초과합니다. 청크로 분할합니다.")
                return await self._save_with_chunking(page_data, headers, children)

            # 100개 이하면 한 번에 저장
            response = requests.post(
                'https://api.notion.com/v1/pages',
                headers=headers,
                data=json.dumps(page_data)
            )

            if response.status_code == 200:
                notion_page = response.json()
                page_url = notion_page.get('url', '')

                print(f"✅ Notion 저장 성공")
                print(f"   페이지 URL: {page_url}")

                return page_url
            else:
                print(f"❌ Notion 저장 실패: {response.status_code}")
                print(f"   응답: {response.text}")
                return None

        except Exception as e:
            print(f"❌ NotionSaver 오류: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _save_with_chunking(self, page_data: Dict, headers: Dict, children: list) -> Optional[str]:
        """100개 이상의 블록을 청크로 분할해서 저장"""
        try:
            # 1단계: 첫 100개 블록으로 페이지 생성
            first_chunk = children[:100]
            page_data['children'] = first_chunk

            print(f"   📝 1차 저장: {len(first_chunk)}개 블록")
            response = requests.post(
                'https://api.notion.com/v1/pages',
                headers=headers,
                data=json.dumps(page_data)
            )

            if response.status_code != 200:
                print(f"❌ 1차 저장 실패: {response.status_code}")
                print(f"   응답: {response.text}")
                return None

            notion_page = response.json()
            page_id = notion_page.get('id', '')
            page_url = notion_page.get('url', '')

            # 2단계: 나머지 블록들을 100개씩 추가
            remaining_children = children[100:]
            chunk_num = 2

            while remaining_children:
                chunk = remaining_children[:100]
                remaining_children = remaining_children[100:]

                print(f"   📝 {chunk_num}차 추가: {len(chunk)}개 블록")

                append_response = requests.patch(
                    f'https://api.notion.com/v1/blocks/{page_id}/children',
                    headers=headers,
                    data=json.dumps({"children": chunk})
                )

                if append_response.status_code != 200:
                    print(f"⚠️ {chunk_num}차 추가 실패: {append_response.status_code}")
                    print(f"   응답: {append_response.text}")
                    # 실패해도 페이지는 생성되었으므로 URL 반환
                    break

                chunk_num += 1

            print(f"✅ Notion 저장 성공 (총 {chunk_num-1}개 청크)")
            print(f"   페이지 URL: {page_url}")

            return page_url

        except Exception as e:
            print(f"❌ 청크 저장 오류: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _create_page_data(
        self,
        video_info: Dict,
        summary: str,
        video_url: str,
        channel_config: Dict,
        discord_info: Optional[Dict]
    ) -> Dict:
        """Notion 페이지 데이터 구성"""

        channel_name = channel_config.get('channel_name', 'unknown')
        prompt_key = channel_config.get('system_prompt_key', 'archive')

        # 현재 시간
        current_time = datetime.now().isoformat()

        # 채널별 속성 구성
        if prompt_key == "archive":
            properties = self._create_archive_properties(video_info, video_url, current_time)
        elif prompt_key == "agent_references":
            properties = self._create_agent_ref_properties(video_info, video_url, current_time)
        else:
            # 기본 속성
            properties = self._create_default_properties(video_info, video_url, current_time)

        # 페이지 콘텐츠 (children) 구성
        children = []

        # 1. YouTube URL 임베딩 (또는 링크)
        children.append({
            "object": "block",
            "type": "embed",
            "embed": {
                "url": video_url
            }
        })

        # 2. 요약 내용 추가
        if summary:
            summary_blocks = self._split_summary_into_blocks(summary)
            children.extend(summary_blocks)

        # 3. 메타데이터 정보 (Discord 정보 포함)
        if discord_info:
            metadata_text = f"""
---
**Discord 정보**
- 채널: #{discord_info.get('channel', 'unknown')}
- 요청자: {discord_info.get('author', 'unknown')}
- 처리 시간: {current_time}
"""
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": metadata_text}}
                    ]
                }
            })

        # 최종 페이지 데이터
        page_data = {
            "parent": {"database_id": channel_config.get('notion_database_id')},
            "properties": properties,
            "children": children
        }

        return page_data

    def _create_archive_properties(self, video_info: Dict, video_url: str, current_time: str) -> Dict:
        """Archive 채널용 속성 - Name만 사용 (나머지는 콘텐츠에 포함)"""
        return {
            "Name": {  # 제목 (Title 타입)
                "title": [
                    {"text": {"content": video_info.get('title', '제목 없음')}}
                ]
            }
        }

    def _create_agent_ref_properties(self, video_info: Dict, video_url: str, current_time: str) -> Dict:
        """Agent References 채널용 속성 - Name만 사용 (나머지는 콘텐츠에 포함)"""
        return {
            "Name": {  # 제목
                "title": [
                    {"text": {"content": video_info.get('title', '제목 없음')}}
                ]
            }
        }

    def _create_default_properties(self, video_info: Dict, video_url: str, current_time: str) -> Dict:
        """기본 속성"""
        return {
            "Name": {
                "title": [
                    {"text": {"content": video_info.get('title', '제목 없음')}}
                ]
            },
            "URL": {
                "url": video_url
            }
        }

    def _split_summary_into_blocks(self, summary: str) -> list:
        """요약을 Notion 블록으로 변환"""
        try:
            blocks = self._parse_markdown_to_blocks(summary)
            return blocks

        except Exception as e:
            print(f"❌ 마크다운 파싱 오류: {e}")
            # 실패 시 단순 paragraph로 반환
            return [{
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": summary}}]
                }
            }]

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
            if line.startswith('### '):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": line[4:]}}]
                    }
                })
            elif line.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
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
            # 불릿 리스트
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

    def test_database_connection(self, database_id: str) -> bool:
        """Notion 데이터베이스 연결 테스트"""
        try:
            print(f"🧪 Notion 데이터베이스 연결 테스트")
            print(f"   DB ID: {database_id}")

            if not self.api_key:
                print("❌ API 키가 없습니다.")
                return False

            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Notion-Version': self.notion_version
            }

            response = requests.get(
                f'https://api.notion.com/v1/databases/{database_id}',
                headers=headers
            )

            if response.status_code == 200:
                db_info = response.json()
                db_title = db_info.get('title', [{}])[0].get('plain_text', 'Unknown')
                print(f"✅ 데이터베이스 연결 성공: {db_title}")
                return True
            else:
                print(f"❌ 연결 실패: {response.status_code}")
                print(f"   응답: {response.text}")
                return False

        except Exception as e:
            print(f"❌ 연결 테스트 오류: {e}")
            return False


# 테스트용 함수
async def test_notion_saver():
    """NotionSaver 테스트"""
    print("🧪 NotionSaver 테스트")
    print("=" * 60)

    saver = NotionSaver()

    # 테스트 데이터베이스 ID (Archive)
    test_db_id = "290b592202868160becbe90aeaf8dfeb"

    # 연결 테스트
    connection_ok = saver.test_database_connection(test_db_id)

    if not connection_ok:
        print("❌ 연결 테스트 실패")
        return

    # 저장 테스트
    print("\n📝 저장 테스트")
    print("-" * 60)

    test_video_info = {
        'title': '[테스트] Notion 저장 테스트',
        'channel': 'YouTube Summarizer Bot',
        'duration': '10분',
        'url': 'https://www.youtube.com/watch?v=test123'
    }

    test_summary = """## 테스트 요약

이것은 Notion 저장 기능을 테스트하기 위한 샘플 요약입니다.

### 주요 내용
- **YouTube URL 임베딩** 기능 테스트
- 마크다운 포맷팅 테스트
- 볼드체 및 리스트 테스트

### 결과
정상적으로 저장되면 성공입니다!"""

    test_channel_config = {
        'channel_name': '01-archive',
        'notion_database_id': test_db_id,
        'system_prompt_key': 'archive'
    }

    test_discord_info = {
        'channel': 'test-channel',
        'author': 'TestUser'
    }

    # 저장 실행
    notion_url = await saver.save_to_notion(
        test_video_info,
        test_summary,
        test_video_info['url'],
        test_channel_config,
        test_discord_info
    )

    if notion_url:
        print(f"\n🎉 테스트 성공!")
        print(f"📄 Notion 페이지: {notion_url}")
    else:
        print("\n❌ 테스트 실패")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_notion_saver())
