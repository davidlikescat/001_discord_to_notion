#!/usr/bin/env python3
"""
Discord Bot Token 정밀 진단 스크립트
토큰이 작동하는데 "Improper token" 경고가 나는 이유를 찾습니다.
"""

import os
import requests
import discord
import asyncio
import subprocess
from dotenv import load_dotenv

load_dotenv()

def get_secret_from_gcp(secret_name, project_id="n8n-ai-work-agent-automation"):
    """GCP Secret Manager에서 토큰 읽기"""
    try:
        result = subprocess.run([
            'gcloud', 'secrets', 'versions', 'access', 'latest',
            f'--secret=discord-bot-token',
            f'--project={project_id}'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception as e:
        print(f"GCP 읽기 오류: {e}")
        return None

def analyze_token_format(token):
    """토큰 형식 분석"""
    print("🔍 토큰 형식 분석:")
    print(f"   길이: {len(token)}")
    print(f"   시작: {token[:20]}...")
    print(f"   끝: ...{token[-10:]}")
    
    # 기본 형식 체크
    parts = token.split('.')
    print(f"   점(.) 구분: {len(parts)}개 부분")
    
    if len(parts) == 3:
        print(f"   Part 1 길이: {len(parts[0])} (봇 ID)")
        print(f"   Part 2 길이: {len(parts[1])} (타임스탬프)")
        print(f"   Part 3 길이: {len(parts[2])} (HMAC)")
    
    # 문제 요소 체크
    issues = []
    if len(token) < 60:
        issues.append("토큰이 너무 짧음")
    if len(token) > 80:
        issues.append("토큰이 너무 긺")
    if ' ' in token:
        issues.append("공백 포함")
    if '\n' in token or '\r' in token:
        issues.append("줄바꿈 문자 포함")
    if not token.startswith('MT'):
        issues.append(f"비표준 시작 문자: {token[:5]}")
    
    if issues:
        print(f"   ⚠️ 잠재적 문제: {', '.join(issues)}")
    else:
        print("   ✅ 형식상 문제 없음")
    
    return issues

def test_discord_api_direct(token):
    """Discord API 직접 테스트"""
    print("\n🌐 Discord API 직접 테스트:")
    
    headers = {
        'Authorization': f'Bot {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # 1. 봇 정보 조회
        response = requests.get('https://discord.com/api/v10/users/@me', headers=headers)
        print(f"   상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            bot_info = response.json()
            print(f"   ✅ API 성공: {bot_info['username']}#{bot_info['discriminator']}")
            print(f"   봇 ID: {bot_info['id']}")
            print(f"   봇 플래그: {bot_info.get('flags', 'N/A')}")
            return True, bot_info
        else:
            print(f"   ❌ API 실패: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ 네트워크 오류: {e}")
        return False, None

async def test_discord_gateway(token):
    """Discord Gateway 연결 테스트"""
    print("\n🔗 Discord Gateway 연결 테스트:")
    
    try:
        intents = discord.Intents.default()
        intents.message_content = True
        
        client = discord.Client(intents=intents)
        
        @client.event
        async def on_ready():
            print(f"   ✅ Gateway 연결 성공: {client.user}")
            print(f"   연결된 서버: {len(client.guilds)}개")
            
            # 간단한 권한 테스트
            for guild in client.guilds[:3]:  # 최대 3개 서버만
                print(f"     - {guild.name}: {guild.member_count}명")
            
            await client.close()
        
        @client.event  
        async def on_error(event, *args, **kwargs):
            print(f"   ❌ Gateway 오류: {event}")
            await client.close()
        
        # 5초 타임아웃으로 연결 테스트
        await asyncio.wait_for(client.start(token), timeout=10.0)
        return True
        
    except discord.LoginFailure as e:
        print(f"   ❌ 로그인 실패: {e}")
        return False
    except asyncio.TimeoutError:
        print(f"   ⚠️ 연결 시간초과 (하지만 토큰은 유효할 수 있음)")
        return None
    except Exception as e:
        print(f"   ❌ Gateway 오류: {e}")
        return False

def compare_tokens():
    """환경변수와 GCP 토큰 비교"""
    print("\n🔄 토큰 소스 비교:")
    
    env_token = os.getenv('DISCORD_BOT_TOKEN')
    gcp_token = get_secret_from_gcp('discord-bot-token')
    
    print(f"   환경변수 토큰: {'있음' if env_token else '없음'}")
    print(f"   GCP 토큰: {'있음' if gcp_token else '없음'}")
    
    if env_token and gcp_token:
        if env_token == gcp_token:
            print("   ✅ 두 토큰이 일치함")
        else:
            print("   ⚠️ 두 토큰이 다름!")
            print(f"      환경변수: {env_token[:20]}...{env_token[-10:]}")
            print(f"      GCP: {gcp_token[:20]}...{gcp_token[-10:]}")
    
    return env_token, gcp_token

async def main():
    print("🔍 Discord Bot Token 정밀 진단")
    print("=" * 60)
    
    # 1. 토큰 소스 비교
    env_token, gcp_token = compare_tokens()
    
    # 사용할 토큰 결정
    token = env_token or gcp_token
    if not token:
        print("❌ 토큰을 찾을 수 없습니다!")
        return
    
    print(f"\n🎯 사용할 토큰: {'환경변수' if env_token else 'GCP'}")
    
    # 2. 토큰 형식 분석
    issues = analyze_token_format(token)
    
    # 3. Discord API 직접 테스트
    api_success, bot_info = test_discord_api_direct(token)
    
    # 4. Discord Gateway 테스트
    if api_success:
        gateway_success = await test_discord_gateway(token)
    
    # 5. 종합 결과
    print("\n" + "=" * 60)
    print("📊 진단 결과:")
    
    if issues:
        print(f"⚠️ 토큰 형식 문제: {len(issues)}개")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ 토큰 형식: 정상")
    
    if api_success:
        print("✅ Discord API: 정상 작동")
    else:
        print("❌ Discord API: 실패")
    
    if gateway_success is True:
        print("✅ Discord Gateway: 정상 연결")
    elif gateway_success is None:
        print("⚠️ Discord Gateway: 시간초과 (하지만 작동 가능)")
    else:
        print("❌ Discord Gateway: 연결 실패")
    
    # 6. 해결책 제시
    print("\n💡 권장 사항:")
    if api_success and (gateway_success is not False):
        print("   봇이 정상 작동하고 있습니다.")
        if issues:
            print("   토큰 형식 문제가 있지만 Discord가 허용하고 있습니다.")
            print("   새로운 토큰을 발급받는 것을 권장합니다.")
    else:
        print("   새로운 토큰을 발급받아야 합니다.")
        print("   Discord Developer Portal에서 Reset Token을 실행하세요.")

if __name__ == "__main__":
    asyncio.run(main())
