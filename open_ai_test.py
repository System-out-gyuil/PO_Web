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
from main.models import Industry


data = Industry.objects.all()

datas = ''

for i in data:
  datas += f'대분류:{i.big_category} 소분류:{i.small_category},\n'

# print(data)
print(datas)

text = f'{datas} \n 목욕탕 운영에 적합한 업종 5개 제시, 대분류 소분류 기준으로 말해'

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