from elasticsearch import Elasticsearch
from config import ES_API_KEY

es = Elasticsearch(
    "https://0e0f4480a93d4cb78455e070163e467d.us-central1.gcp.cloud.es.io:443",
    api_key=ES_API_KEY
)

res = es.search(index="bizinfo_index", body={
    "query": {
        "wildcard": {
            "title": "*의료*"
        }
    },
    "_source": ["title"]
}, size=10)

for hit in res['hits']['hits']:
    print(hit['_source']['title'])
