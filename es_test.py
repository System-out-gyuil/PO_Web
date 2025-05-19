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
# ✅ Django 설정 초기화
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PO.settings")
django.setup()

from board.models import BizInfo

data = BizInfo.objects.all();

datas = ''

for i in data:
  if i.noti_summary:
    datas += i.noti_summary

text = '\n난 대구에서 화장품 제조업을 하고있어, 2020년 1월부터 하고있고 작년 매출은 10억이었어 수출 하고있고 직원은 7명이야 나에게 맞는 지원 공고를 알려줘'

llm = ChatOpenAI(
    temperature=0,
    model_name='gpt-4o-mini',
    openai_api_key=OPEN_AI_API_KEY
)

user_input = datas + text

response = llm.invoke(user_input)
content = response.content.strip()
print("[GPT 응답 원본]:", content)

enc = tiktoken.encoding_for_model("gpt-4o-mini")
tokens = enc.encode(user_input)
print(f"입력 토큰 수: {len(tokens)}")