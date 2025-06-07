import os
import tempfile
import json
from typing import Optional, Dict, Any, Tuple
import yt_dlp
from io import StringIO


class SubtitleExtractor:
    """
    yt-dlp를 이용해 유튜브 자막(한국어/영어)을 추출하는 클래스
    """

    def __init__(self, download_dir: Optional[str] = None, remove_duplicates: bool = True, similarity_threshold: float = 0.8):
        self.download_dir = download_dir or tempfile.gettempdir()
        self.remove_duplicates = remove_duplicates  # 중복 제거 활성화 여부
        self.similarity_threshold = similarity_threshold  # 유사도 임계값 (0.0-1.0)
        
        # yt-dlp 기본 설정
        self.ydl_opts = {
            'writesubtitles': True,
            'writeautomaticsub': True,  # 자동 생성 자막도 포함
            'subtitleslangs': ['ko', 'en'],  # 한국어 우선, 영어 대안
            'subtitlesformat': 'vtt',  # 또는 'srt'
            'skip_download': True,  # 비디오는 다운로드하지 않음
            'outtmpl': os.path.join(self.download_dir, '%(title)s.%(ext)s'),
        }

    def extract_subtitle_text(self, youtube_url: str) -> str:
        """
        유튜브 URL에서 자막을 추출하고 텍스트를 반환합니다.
        """
        try:
            print(f"🌐 자막 추출 시작: {youtube_url}")
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # 비디오 정보 및 자막 추출
                info = ydl.extract_info(youtube_url, download=False)
                
                # 사용 가능한 자막 확인
                subtitles = info.get('subtitles', {})
                automatic_captions = info.get('automatic_captions', {})
                
                print(f"📋 사용 가능한 자막: {list(subtitles.keys())}")
                print(f"📋 자동 자막: {list(automatic_captions.keys())}")
                
                # 한국어 우선, 영어 대안으로 자막 선택
                subtitle_data = None
                language_used = None
                self.subtitle_source = ""
                
                # 1. 먼저 수동 자막 확인 (한국어 우선)
                if 'ko' in subtitles:
                    subtitle_data = subtitles['ko']
                    language_used = "ko (수동)"
                    self.subtitle_source = "yt_dlp_manual_ko"
                elif 'en' in subtitles:
                    subtitle_data = subtitles['en']
                    language_used = "en (수동)"
                    self.subtitle_source = "yt_dlp_manual_en"
                
                # 2. 수동 자막이 없으면 자동 자막 확인
                elif 'ko' in automatic_captions:
                    subtitle_data = automatic_captions['ko']
                    language_used = "ko (자동)"
                    self.subtitle_source = "yt_dlp_auto_ko"
                elif 'en' in automatic_captions:
                    subtitle_data = automatic_captions['en']
                    language_used = "en (자동)"
                    self.subtitle_source = "yt_dlp_auto_en"
                elif 'ko-orig' in automatic_captions:  # 추가: 원본 한국어 자막 확인
                    subtitle_data = automatic_captions['ko-orig']
                    language_used = "ko-orig (자동)"
                    self.subtitle_source = "yt_dlp_auto_ko"
                
                if not subtitle_data:
                    print("❌ 한국어/영어 자막을 찾을 수 없습니다. 영상 설명으로 대체합니다.")
                    # 영상 설명으로 대체
                    description = info.get('description', '')
                    if description and len(description) > 100:  # 최소 길이 확인
                        self.subtitle_source = "description"
                        print(f"✅ 영상 설명으로 대체 ({len(description)} 글자)")
                        return description
                    return ""
                
                print(f"✅ 선택된 자막: {language_used}")
                
                # 자막 URL에서 내용 다운로드
                subtitle_url = None
                for subtitle_format in subtitle_data:
                    if subtitle_format.get('ext') in ['vtt', 'srt']:
                        subtitle_url = subtitle_format['url']
                        break
                
                if not subtitle_url:
                    print("❌ 자막 URL을 찾을 수 없습니다.")
                    return ""
                
                # 자막 내용 다운로드
                import urllib.request
                with urllib.request.urlopen(subtitle_url) as response:
                    subtitle_content = response.read().decode('utf-8')
                
                # 다운로드한 자막 내용 확인
                if not subtitle_content or len(subtitle_content) < 10:
                    print(f"❌ 자막 내용이 너무 짧습니다: {len(subtitle_content)} 글자")
                    return ""
                
                # VTT/SRT 형식을 일반 텍스트로 변환
                clean_text = self._clean_subtitle_text(subtitle_content)
                
                # 결과 확인
                if not clean_text or len(clean_text) < 10:
                    print(f"❌ 정제된 자막이 너무 짧습니다: {len(clean_text)} 글자")
                    # 원본 내용 디버깅 출력
                    print(f"원본 자막 미리보기: {subtitle_content[:200]}...")
                    return ""
                
                print(f"📄 자막 추출 완료: {len(clean_text)} 글자")
                return clean_text
                
        except Exception as e:
            print(f"❌ yt-dlp 자막 추출 오류: {e}")
            import traceback
            traceback.print_exc()  # 스택 트레이스 출력
            return ""

    def _clean_subtitle_text(self, subtitle_content: str) -> str:
        """
        VTT/SRT 형식의 자막에서 시간 정보 등을 제거하고 순수 텍스트만 추출
        중복된 연속 자막도 제거
        """
        lines = subtitle_content.split('\n')
        text_lines = []
        
        # 디버깅: 원본 라인 수 출력
        print(f"🔍 원본 자막 라인 수: {len(lines)}")
        
        for line in lines:
            line = line.strip()
            # VTT 헤더나 시간 정보 스킵
            if (line.startswith('WEBVTT') or 
                '-->' in line or 
                line.isdigit() or 
                line == '' or
                line.startswith('NOTE') or
                line.startswith('Kind:') or
                line.startswith('Language:')):
                continue
            
            # HTML 태그 제거 (예: <c.colorE5E5E5>)
            import re
            line = re.sub(r'<[^>]+>', '', line)
            
            if line:
                text_lines.append(line)
        
        # 디버깅: 정제 후 라인 수 출력
        print(f"🔍 정제 후 자막 라인 수: {len(text_lines)}")
        
        # 🔥 중복 제거: 연속된 동일한 라인 제거
        deduplicated_lines = self._remove_consecutive_duplicates(text_lines)
        
        # 디버깅: 중복 제거 후 라인 수 출력
        print(f"🔍 중복 제거 후 자막 라인 수: {len(deduplicated_lines)}")
        
        # 결과 확인
        result = '\n'.join(deduplicated_lines)
        if not result:
            # 원본에서 일부만 샘플로 추출
            fallback_text = []
            for line in lines:
                if line and not line.startswith('WEBVTT') and '-->' not in line and not line.isdigit():
                    fallback_text.append(line.strip())
            if fallback_text:
                print("⚠️ 정제 결과가 비어있어 원본에서 일부 추출합니다.")
                return '\n'.join(fallback_text[:100])  # 최대 100줄만 사용
            
        return result
    
    def _remove_consecutive_duplicates(self, lines: list) -> list:
        """
        연속된 중복 자막 라인을 제거하는 메서드
        - 완전 일치 중복 제거
        - 유사도 기반 중복 제거 (선택사항)
        """
        if not lines or not self.remove_duplicates:
            return lines
        
        # 입력 라인이 없으면 그대로 반환
        if not lines:
            return lines
            
        result = [lines[0]]  # 첫 번째 라인은 항상 포함
        removed_count = 0
        
        for i in range(1, len(lines)):
            current_line = lines[i].strip()
            previous_line = lines[i-1].strip()
            
            # 1. 완전 일치 중복 제거
            if current_line == previous_line:
                removed_count += 1
                continue
            
            # 2. 유사도 기반 중복 제거 (선택사항)
            if self.similarity_threshold < 1.0:
                similarity = self._calculate_similarity(current_line, previous_line)
                if similarity >= self.similarity_threshold:
                    print(f"🔄 유사 중복 제거 (유사도: {similarity:.2f}): '{current_line}'")
                    removed_count += 1
                    continue
            
            result.append(lines[i])
        
        if removed_count > 0:
            print(f"✅ 총 {removed_count}개의 중복 자막을 제거했습니다.")
        
        return result
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        두 텍스트 간의 유사도를 계산 (0.0 ~ 1.0)
        간단한 Jaccard 유사도 사용
        """
        if not text1 or not text2:
            return 0.0
        
        # 단어 기준으로 분할
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        
        # Jaccard 유사도: 교집합 크기 / 합집합 크기
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0

    def get_available_subtitles(self, youtube_url: str) -> Dict[str, Any]:
        """
        해당 URL에서 사용 가능한 모든 자막 언어 정보를 반환
        """
        try:
            ydl_opts = {'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                
                return {
                    'manual_subtitles': list(info.get('subtitles', {}).keys()),
                    'automatic_captions': list(info.get('automatic_captions', {}).keys()),
                    'title': info.get('title', 'Unknown')
                }
        except Exception as e:
            print(f"❌ 자막 정보 조회 오류: {e}")
            return {}
