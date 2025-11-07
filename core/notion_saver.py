"""
Notion 저장 모듈
Notion API 사용
"""
import os
from notion_client import Client
from datetime import datetime


class NotionSaver:
    def __init__(self):
        self.api_key = os.getenv('NOTION_API_KEY')
        if not self.api_key:
            print("⚠️ NOTION_API_KEY가 설정되지 않았습니다.")
            self.client = None
        else:
            self.client = Client(auth=self.api_key)
            print("✅ Notion 클라이언트 초기화 완료")

    def save_to_notion(
        self,
        video_info: dict,
        summary: str,
        video_url: str,
        database_id: str,
        channel_name: str = 'archive'
    ) -> str:
        """
        Notion 데이터베이스에 페이지 생성
        """
        if not self.client:
            print("❌ Notion 클라이언트가 초기화되지 않았습니다.")
            return None

        try:
            # 페이지 속성 구성
            properties = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": video_info['title']
                            }
                        }
                    ]
                },
                "URL": {
                    "url": video_url
                },
                "Channel": {
                    "rich_text": [
                        {
                            "text": {
                                "content": video_info['channel']
                            }
                        }
                    ]
                },
                "Duration": {
                    "rich_text": [
                        {
                            "text": {
                                "content": video_info.get('duration', 'N/A')
                            }
                        }
                    ]
                },
                "Category": {
                    "select": {
                        "name": channel_name
                    }
                },
                "Created": {
                    "date": {
                        "start": datetime.utcnow().isoformat()
                    }
                }
            }

            # 페이지 콘텐츠 구성 (요약 + YouTube 임베드)
            children = [
                # YouTube 임베드
                {
                    "object": "block",
                    "type": "embed",
                    "embed": {
                        "url": video_url
                    }
                },
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                }
            ]

            # 요약 내용을 블록으로 변환
            summary_blocks = self._markdown_to_blocks(summary)
            children.extend(summary_blocks)

            # 페이지 생성
            print(f"📄 Notion 페이지 생성 중...")
            response = self.client.pages.create(
                parent={"database_id": database_id},
                properties=properties,
                children=children
            )

            page_url = response['url']
            print(f"✅ Notion 저장 완료: {page_url}")
            return page_url

        except Exception as e:
            print(f"❌ Notion 저장 오류: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _markdown_to_blocks(self, markdown_text: str) -> list:
        """
        마크다운 텍스트를 Notion 블록으로 변환
        간단한 변환만 지원 (제목, 본문, 리스트)
        """
        blocks = []
        lines = markdown_text.split('\n')

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # 제목 처리
            if line.startswith('# '):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"text": {"content": line[2:]}}]
                    }
                })
            elif line.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": line[3:]}}]
                    }
                })
            elif line.startswith('### '):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"text": {"content": line[4:]}}]
                    }
                })
            # 리스트 처리
            elif line.startswith('- ') or line.startswith('* '):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": line[2:]}}]
                    }
                })
            # 일반 텍스트
            else:
                # Notion 블록 텍스트 길이 제한 (2000자)
                if len(line) > 2000:
                    line = line[:2000] + "..."

                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": line}}]
                    }
                })

        return blocks


if __name__ == '__main__':
    # 테스트
    from dotenv import load_dotenv
    load_dotenv()

    saver = NotionSaver()

    test_video_info = {
        'title': 'Test Video Title',
        'channel': 'Test Channel',
        'duration': '10:00'
    }

    test_summary = """# 테스트 요약

## 핵심 내용
- 포인트 1
- 포인트 2

## 상세 설명
이것은 테스트 요약입니다.
"""

    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    test_database_id = os.getenv('NOTION_DATABASE_ID')

    if test_database_id:
        result = saver.save_to_notion(
            test_video_info,
            test_summary,
            test_url,
            test_database_id,
            'archive'
        )
        print(f"\nResult: {result}")
