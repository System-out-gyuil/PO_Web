import os
import django
import ast
from django.forms.models import model_to_dict
from elasticsearch import Elasticsearch, helpers
from config import ES_API_KEY

# ✅ Django 설정 초기화
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PO.settings")
django.setup()

from board.models import BizInfo

# ✅ Elasticsearch 클라이언트 생성
es = Elasticsearch(
    "https://0e0f4480a93d4cb78455e070163e467d.us-central1.gcp.cloud.es.io:443",
    api_key=ES_API_KEY
)

index_name = "bizinfo_index"

# ✅ 인덱스 삭제 및 재생성
if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)
    print(f"❌ 기존 인덱스 '{index_name}' 삭제")

es.indices.create(index=index_name)
print(f"✅ 새 인덱스 '{index_name}' 생성")

# ✅ DB → Elasticsearch 데이터 준비
actions = []

# 리스트로 처리할 필드 목록
list_fields = ["region", "employee_count", "revenue", "export_performance", "possible_industry", "business_period"]

for i, obj in enumerate(BizInfo.objects.all()):
    doc = model_to_dict(obj)

    # ✅ 날짜 필드 ISO 포맷 변환
    for field in ['registered_at', 'reception_start', 'reception_end']:
        if doc.get(field):
            doc[field] = doc[field].isoformat()

    # ✅ 리스트형 문자열 처리
    for field in list_fields:
        value = doc.get(field)

        if value:
            if isinstance(value, list):
                doc[field] = value
            elif isinstance(value, str) and value.startswith("[") and value.endswith("]"):
                try:
                    parsed = ast.literal_eval(value)
                    if isinstance(parsed, list):
                        doc[field] = parsed
                    else:
                        doc[field] = [value]
                except Exception as e:
                    print(f"⚠️ {field} 파싱 실패: {value} → {e}")
                    doc[field] = [value]
            else:
                doc[field] = [value]
        else:
            doc[field] = []

    # ✅ actions에 추가
    actions.append({
        "_index": index_name,
        "_id": doc["pblanc_id"],
        "_source": doc
    })

# ✅ Elasticsearch에 일괄 업로드
helpers.bulk(es, actions)
print(f"🎉 총 {len(actions)}개 문서 Elasticsearch 인덱싱 완료")
