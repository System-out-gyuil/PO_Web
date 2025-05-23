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

from django.forms.models import model_to_dict
import ast
from elasticsearch import Elasticsearch, helpers

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

# ✅ 인덱스 생성 (edge_ngram 설정 포함)
es.indices.create(
    index=index_name,
    body={
        "settings": {
            "analysis": {
                "tokenizer": {
                    "edge_ngram_tokenizer": {
                        "type": "edge_ngram",
                        "min_gram": 1,
                        "max_gram": 30,
                        "token_chars": ["letter", "digit", "whitespace", "punctuation"]
                    }
                },
                "analyzer": {
                    "edge_ngram_analyzer": {
                        "type": "custom",
                        "tokenizer": "edge_ngram_tokenizer",
                        "filter": ["lowercase"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "title": {"type": "text", "analyzer": "edge_ngram_analyzer", "search_analyzer": "edge_ngram_analyzer"},
                "region_first": {"type": "text", "analyzer": "edge_ngram_analyzer", "search_analyzer": "edge_ngram_analyzer"},
                "noti_summary": {"type": "text", "analyzer": "edge_ngram_analyzer", "search_analyzer": "edge_ngram_analyzer"},
                "possible_industry": {"type": "text", "analyzer": "edge_ngram_analyzer", "search_analyzer": "edge_ngram_analyzer"},
                "institution_name": {"type": "text", "analyzer": "edge_ngram_analyzer", "search_analyzer": "edge_ngram_analyzer"},
                "target": {"type": "text", "analyzer": "edge_ngram_analyzer", "search_analyzer": "edge_ngram_analyzer"},
                "registered_at": {"type": "date"},
                "reception_start": {"type": "date"},
                "reception_end": {"type": "date"}
            }
        }
    }
)
print(f"✅ 새 인덱스 '{index_name}' 생성 완료")

# ✅ Elasticsearch에 인덱싱할 데이터 준비
actions = []

list_fields = ["region", "employee_count", "revenue", "export_performance", "possible_industry", "business_period"]

for obj in BizInfo.objects.all():
    doc = model_to_dict(obj)

    # 날짜 필드 ISO 변환
    for field in ["registered_at", "reception_start", "reception_end"]:
        if doc.get(field):
            doc[field] = doc[field].isoformat()

    # 리스트형 필드 처리
    for field in list_fields:
        value = doc.get(field)
        if value:
            if isinstance(value, list):
                doc[field] = value
            elif isinstance(value, str) and value.startswith("[") and value.endswith("]"):
                try:
                    parsed = ast.literal_eval(value)
                    doc[field] = parsed if isinstance(parsed, list) else [parsed]
                except Exception as e:
                    print(f"⚠️ {field} 파싱 실패: {value} → {e}")
                    doc[field] = [value]
            else:
                doc[field] = [value]
        else:
            doc[field] = []

    # region_first 필드 생성
    doc["region_first"] = doc["region"][0] if doc["region"] else ""

    actions.append({
        "_index": index_name,
        "_id": doc["pblanc_id"],
        "_source": doc
    })

# ✅ Elasticsearch에 업로드
helpers.bulk(es, actions)
print(f"🎉 총 {len(actions)}개 문서 Elasticsearch 인덱싱 완료")