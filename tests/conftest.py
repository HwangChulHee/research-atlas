"""테스트 공통 설정.

agents.collect 는 모듈 로드 시 OpenAI() 클라이언트를 생성한다(네트워크 호출은 없음).
CI엔 .env·키가 없으므로 더미 키를 넣어 import 가 깨지지 않게 한다. 실제 API 호출은 테스트에 없음.
"""
import os

os.environ.setdefault("OPENAI_API_KEY", "test-sentinel-no-network")
