import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel, Field
from typing import List, Literal

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class Contact(BaseModel):
    label: str = Field(description="기관명 (예: 경찰청, 금융감독원)")
    phone: str = Field(description="전화번호 (예: 112, 1332)")

class ActionGuide(BaseModel):
    headline: str = Field(description="지금 해야 할 행동 한 줄 (고령층 맞춤형 간결한 문장)")
    steps: List[str] = Field(description="순서대로 따라 할 수 있는 단계별 행동 요령")
    contacts: List[Contact] = Field(description="확인 또는 신고 가능한 기관 연락처 목록")

class PhishingAnalysisResult(BaseModel):
    risk_level: Literal["안전", "의심", "경고", "위험"] = Field(description="위험도 단계")
    score: int = Field(ge=0, le=100, description="위험도 점수 (0~100)")
    summary: str = Field(description="분석 결과 한 문장 요약")
    reason: List[str] = Field(description="판정 근거 목록 (2개 권장)")
    action_guide: ActionGuide
    notify_guardian: bool = Field(description="보호자 알림 발송 필요 여부 (경고 이상 시 True)")
    disclaimer: str = Field(
        default="이 결과는 AI의 참고용 판단이며 실제와 다를 수 있습니다",
        description="고정 면책 조항"
    )

def analyze_phishing_image(image_path: str) -> dict:
    img = Image.open(image_path)
    system_prompt = """
    너는 고령층 대상 보이스피싱 및 스미싱 판정 전문가야.
    사용자가 업로드한 문자 메시지나 메신저(카카오톡 등) 대화 캡처 이미지를 정밀 분석해줘.

    [판정 지침]
    1. risk_level 기준:
       - 안전: 일상 대화, 정상 기관의 알림톡 등
       - 의심: 출처 불명 링크 포함, 확인되지 않은 전화번호로 연락 유도
       - 경고: 금전/상품권 요구, 개인정보 입력 링크 유도, 지인 사칭 조짐
       - 위험: 검찰/경찰/금감원 사칭, 원격제어 앱(APK) 설치 유도, 긴급 송금 협박
    2. 위험도가 "의심"일 때는 단정적으로 "위험하다"고 하지 말고, 반드시 공식 대표번호로 직접 재확인하도록 안내해.
    3. 60대 이상 고령층 타겟이므로 action_guide의 headline과 steps는 매우 짧고 쉬운 문장으로 구성해.
    4. notify_guardian은 risk_level이 '경고' 또는 '위험'이거나 score가 60점 이상일 때 True로 설정해.
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[img, "이 이미지의 보이스피싱/스미싱 위험도를 분석해 규격에 맞춰 결과를 생성해줘."],
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=PhishingAnalysisResult,
            temperature=0.1,
        )
    )
    return json.loads(response.text)