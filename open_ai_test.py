import os
import django
import ast
from django.forms.models import model_to_dict
from elasticsearch import Elasticsearch, helpers
from config import ES_API_KEY
from langchain_openai import ChatOpenAI
import logging
import requests
import uuid
import time
import json
import os
from pyhwpx import Hwp
from config import OPEN_AI_API_KEY
from langchain_openai import ChatOpenAI
import pdfplumber
from tqdm import tqdm
from datetime import datetime
import shutil  # 추가
import re
import tiktoken
from django.db.models import Q

# ✅ Django 설정 초기화
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PO.settings")
django.setup()

from board.models import BizInfo

data = BizInfo.objects.filter(
    Q(region__contains=["인천"]) | Q(region__contains=["전국"])
)

datas = ''

for i in data:
  if i.noti_summary:
    datas += f'{i.id} {i.noti_summary}\n\n'

# print(data)
print(datas)

text = '\n사업지 주소지 인천, 대분류: 시스템ㆍ응용 소프트웨어 개발 및 공급업, 소분류: 시스템 소프트웨어 개발 및 공급업을 영위함, 개업한지 3년 4개월 되었고 작년 10억 매출에 수출 실적이 있어, 직원은 7명이야 아래 지원 공고 내용을 토대로 선정 가능성이 높은 공고를 알려줘, 적합도 점수(자사의 정보로 선정될 수 있는) 100점 만점으로 해서 우선순위를 정해줘, 70점이 넘는 공고만 보여줘\n'

llm = ChatOpenAI(
    temperature=0,
    model_name='gpt-4o-mini',
    openai_api_key=OPEN_AI_API_KEY
)

user_input = text + datas

response = llm.invoke(user_input)
content = response.content.strip()
print("[GPT 응답 원본]:", content)

enc = tiktoken.encoding_for_model("gpt-4o-mini")
tokens = enc.encode(user_input)
print(f"입력 토큰 수: {len(tokens)}")