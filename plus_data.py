import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PO.settings")
django.setup()
import pandas as pd
from openai import OpenAI
import pdfplumber
from langchain_openai import ChatOpenAI
import re
import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from board.models import BizInfo
from main.models import Industry
from PO.management.commands.utils import fetch_iframe_src
from config import BIZINFO_API_KEY, CHROME_DRIVER_PATH, OPEN_AI_API_KEY, NAVER_CLOVA_OCR_API_KEY, NAVER_CLOUD_CLOVA_OCR_API_URL, ES_API_KEY
from langchain_openai import ChatOpenAI
import pdfplumber
import uuid
import json
import time
from PIL import Image
import subprocess
import warnings


from board.models import BizInfo

# Excel 파일 경로
file_path = "/Users/user/Desktop/po/PO_Django/PO/files/2025년도 소상공인 고효율기기 지원사업 공고문.pdf"

full_text = ""
extra_path = None

with pdfplumber.open(file_path) as pdf:
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            full_text += page_text + "\n"

prompt = (
                "아래 텍스트는 정부 지원사업 공고문에서 추출된 실제 내용입니다.\n"
                "이 내용을 기반으로 **원문에 명시된 내용만으로 엄격히 판단하여**, **절대로 추측이나 가정을 하지 마세요.**\n"
                "※ 빈 값 없이 모든 항목을 채워야 하며.\n"
                "※ 모든 선택지는 반드시 제공된 항목 중에서만 고르고, 원문에 명확히 언급되지 않은 항목은 포함하지 마세요.\n"
                "※ 원문에 기준이 명확하지 않을 경우, '보수적으로 실제 선정 가능성이 높은' 항목만 선택하십시오.\n\n"
                "응답 형식 (반드시 JSON, 빈 값 허용 불가):\n"
                "{\n"
                "  \"지역\": [\"전국\"] 또는 [\"서울\",\"경기\",\"인천\",\"강원\",\"경북\",\"경남\",\"부산\",\"대구\",\"대전\",\"광주\",\"울산\",\"세종\",\"충북\",\"충남\",\"전북\",\"전남\",\"제주\"] 중 원문 근거로 복수 선택],\n"
                "  \"직원수\": [\"직원 없음\", \"1~4인\",\"5인 이상\"] 선택지 중 실제 선정 가능성이 높은 범위를 모두 선택,\n"
                "  \"사업기간(업력)\": [\"사업자 등록 전\",\"3년 미만\",\"3년 이상\"] 선택지 중 선정 가능성이 높은 구간을 복수 선택,\n"
                "  \"매출규모\": [\"매출 없음\", \"1억 이하\",\"1~5억\",\"5~10억\",\"10~30억\",\"30억 이상\"] 선택지 중 선정 가능성이 높은 구간을 복수 선택,\n"
                "  \"수출실적여부\": [\"수출 실적 보유\", \"무관\"] 반드시 예시 중 선정 가능성이 높은 선택지를 하나 선택,\n"
                "  \"공고내용\": \"지원 목적, 대상, 기간, 방법, 자부담, 선정 절차, 지원 한도 및 제한 사항 등을 종합하여 450자 이상으로 정밀하게 요약한 문장\"\n"
                "  \"가능업종\": [\"농업, 임업 및 어업\", \"광업\", \"제조업\", \"전기, 가스, 증기 및 공기 조절 공급업\",\
                      \"수도, 하수 및 폐기물 처리, 원료 재생업\", \"건설업\", \"도매 및 소매업\", \"운수 및 창고업\", \"숙박 및 음식점업\",\
                        \"정보통신업\", \"금융 및 보험업\", \"부동산업\", \"전문, 과학 및 기술 서비스업\", \"사업시설 관리, 사업 지원 및 임대 서비스업\", \
                        \"교육서비스업\", \"보건업 및 사회복지 서비스업\", \"예술 스포츠 및 여가관련 서비스업\", \"협회 및 단체, 수리 및 기타 개인서비스업\"]\
                          선택지 중 공고내용 내 선정 가능한 업종을 명확하게 선택, 복수 선택 가능\n"
                "}\n\n"
                "필수 준수사항:\n"
                "- 모든 키에 반드시 하나 이상의 값을 채워야 하며, 빈 배열 또는 누락은 허용되지 않습니다.\n"
                "- 제공된 선택지 외의 항목은 절대 포함하지 마십시오.\n"
                "- 수출실적여부 외 다른항목에 대해 '무관' 절대 사용하지 마십시오.\n"
                "- 공고 내용을 제외한 모든 항목은 배열의 형태로 출력하시오.\n"
                "- 원문에 직접 근거한 내용만 사용하고, 절대로 추측이나 가정을 하지 마십시오.\n"
                "- 원문에 없는 조건은 '보수적'으로 판단하여 실제 선정 가능성이 높은 기준을 선택하십시오.\n"
            ) + full_text


llm = ChatOpenAI(temperature=0, model_name='gpt-4o', openai_api_key=OPEN_AI_API_KEY)
response = llm.invoke(prompt)

print(response.content)