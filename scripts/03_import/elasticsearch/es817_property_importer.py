import os
import json
import re
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# elasticsearch 모듈 체크
try:
    from elasticsearch import Elasticsearch, helpers
except ImportError:
    print("⚠️ 'elasticsearch' 모듈이 설치되어 있지 않습니다. pip install elasticsearch")
    sys.exit(1)

# 상위 디렉토리의 config.py를 로드하기 위한 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
script_dir = os.path.dirname(os.path.dirname(current_dir)) # scripts/
project_root = os.path.dirname(script_dir) # 프로젝트 루트
sys.path.append(script_dir)

try:
    from config import Config
except ImportError:
    # Config 로드 실패 시 기본값 사용을 위한 더미 클래스
    class Config:
        BASE_DIR = project_root

class ES817PropertyImporter:
    """
    Elasticsearch 8.17에 매물 데이터를 적재하는 Importer
    
    데이터 소스:
    - data/RDB/land/*.json (전처리 및 search_text 생성 완료된 데이터)
    
    Target Index:
    - realestate_listings
    """
    
    INDEX_NAME = "realestate_listings"
    FILE_TYPE_MAPPING = {
        "00_통합_빌라주택.json": "빌라주택",
        "00_통합_아파트.json": "아파트",
        "00_통합_오피스텔.json": "오피스텔",
        "00_통합_원투룸.json": "원투룸"
    }

    def __init__(self):
        # Elasticsearch 8.17 연결 설정 (환경변수 우선)
        host = os.environ.get("ELASTICSEARCH_HOST", "localhost")
        port = os.environ.get("ELASTICSEARCH_PORT", "9200")
        
        # URL 포맷팅
        if not host.startswith("http"):
            host = f"http://{host}:{port}"

        print(f"[ES 8.17] Connecting to {host}...")
        self.es = Elasticsearch(
            hosts=[host],
            request_timeout=30,
            max_retries=3,
            retry_on_timeout=True
        )
        
        if self.es.ping():
            info = self.es.info()
            print(f"[ES 8.17] Connected! Version: {info['version']['number']}")
        else:
            print(f"[ES 8.17] ⚠️ Connection failed to {host}")

    def _parse_price(self, price_str: str) -> int:
        """가격 문자열을 만원 단위 정수로 변환"""
        if not price_str or price_str == "-" or price_str == "정보없음":
            return 0
        
        # 콤마, 공백 제거
        s = str(price_str).replace(",", "").replace(" ", "").replace("원", "")
        
        total = 0
        # 억 단위
        match_uk = re.search(r"(\d+)억", s)
        if match_uk:
            total += int(match_uk.group(1)) * 10000
        
        # 만 단위 (또는 숫자만 있는 경우)
        match_man = re.search(r"(\d+)만", s)
        if match_man:
            total += int(match_man.group(1))
        elif not match_uk: # 억도 없고 만도 없는데 숫자만 있는 경우 ("50")
            # "억" 뒤의 나머지 숫자 파싱 ("1억 5000" -> "5000")
            remaining = re.sub(r"\d+억", "", s)
            if remaining and remaining.isdigit():
                 total += int(remaining)
            elif s.isdigit():
                total += int(s)
                
        return total

    def _transform_doc(self, item: Dict[str, Any], building_type: str) -> Optional[Dict[str, Any]]:
        """ES 문서 형태로 변환"""
        land_num = item.get("매물번호")
        if not land_num:
            return None
            
        trade_info = item.get("거래_정보", {})
        addr_info = item.get("주소_정보", {})
        prop_info = item.get("매물_정보", {})
        
        # 가격 파싱
        deposit = self._parse_price(trade_info.get("보증금", "0"))
        rent = self._parse_price(trade_info.get("월세", "0"))
        jeonse = self._parse_price(trade_info.get("전세", "0"))
        sale = self._parse_price(trade_info.get("매매가", "0"))

        # 전세인 경우 보증금 필드에 전세가 저장 (호환성)
        deal_type = trade_info.get("거래유형", "기타")
        if "전세" in deal_type and jeonse == 0 and deposit > 0:
            jeonse = deposit
        
        doc = {
            "_index": self.INDEX_NAME,
            "_id": str(land_num),
            "_source": {
                "land_num": str(land_num),
                "building_type": building_type,
                "deal_type": deal_type,
                "address": addr_info.get("전체주소", ""),
                "road_address": addr_info.get("도로명주소", ""),
                
                # 가격 정보 (만원 단위)
                "deposit": deposit,
                "monthly_rent": rent,
                "jeonse_price": jeonse,
                "sale_price": sale,
                
                # 검색용 텍스트 및 태그
                "search_text": item.get("search_text", ""), # LLM이 생성한 검색 텍스트
                "style_tags": item.get("style_tags", []),   # LLM이 생성한 태그
                
                # 상세 정보
                "description": item.get("상세_설명", ""),
                "params": prop_info, # 방수, 층수 등 원본 데이터
                "url": item.get("매물_URL", ""),
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
        }
        return doc

    def create_index(self):
        """인덱스 생성 및 매핑 설정"""
        if self.es.indices.exists(index=self.INDEX_NAME):
            print(f"[ES 8.17] Index '{self.INDEX_NAME}' already exists.")
            return

        # 매핑 설정 (Nori 분석기 및 KNN 벡터 적용)
        mapping = {
            "settings": {
                "index.knn": True,  # KNN 기능 활성화
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "tokenizer": {
                        "nori_user_dict": {
                            "type": "nori_tokenizer",
                            "decompound_mode": "mixed"
                        }
                    },
                    "analyzer": {
                        "nori_analyzer": {
                            "type": "custom",
                            "tokenizer": "nori_user_dict",
                            "filter": ["lowercase", "stop", "trim"]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "land_num": {"type": "keyword"},
                    "building_type": {"type": "keyword"},
                    "deal_type": {"type": "keyword"},
                    
                    # 임베딩 벡터 (3072차원)
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 3072,
                        "method": {
                            "name": "hnsw",
                            "engine": "nmslib",
                            "space_type": "cosinesimil",
                            "parameters": {
                                "ef_construction": 128,
                                "m": 16
                            }
                        }
                    },
                    
                    # 가격 (Range Query용)
                    "deposit": {"type": "integer"},
                    "monthly_rent": {"type": "integer"},
                    "jeonse_price": {"type": "integer"},
                    "sale_price": {"type": "integer"},
                    
                    # 검색 텍스트 (Nori 분석기 적용)
                    "search_text": {
                        "type": "text", 
                        "analyzer": "nori_analyzer",
                        "search_analyzer": "nori_analyzer"
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "nori_analyzer"
                    },
                    "address": {
                        "type": "text",
                        "analyzer": "nori_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "style_tags": {"type": "keyword"},
                    "updated_at": {"type": "date"}
                }
            }
        }
        
        try:
            self.es.indices.create(index=self.INDEX_NAME, body=mapping)
            print(f"[ES 8.17] Created index '{self.INDEX_NAME}' with mappings.")
        except Exception as e:
            print(f"[ES 8.17] ❌ Failed to create index: {e}")

    def import_properties(self):
        """매물 데이터 적재 실행"""
        # 1. 인덱스 준비
        self.create_index()
        
        # 2. 데이터 경로 설정
        if os.path.exists("/app/data/RDB/land"):
            data_dir = "/app/data/RDB/land"
        else:
            data_dir = os.path.join(Config.BASE_DIR, "data", "RDB", "land")
            
        if not os.path.exists(data_dir):
            print(f"[ES 8.17] ❌ Data directory not found: {data_dir}")
            return

        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json') and f in self.FILE_TYPE_MAPPING]
        print(f"[ES 8.17] Found {len(json_files)} JSON files to import.")

        # 기존 매물 ID 조회 (삭제 감지용)
        try:
            # Scroll API로 모든 문서 ID 조회
            existing_ids = set()
            query = {"query": {"match_all": {}}, "_source": False}
            
            # 인덱스가 존재하고 문서가 있는 경우에만 조회
            if self.es.indices.exists(index=self.INDEX_NAME):
                result = self.es.search(
                    index=self.INDEX_NAME,
                    body=query,
                    scroll='2m',
                    size=1000
                )
                
                scroll_id = result.get('_scroll_id')
                hits = result['hits']['hits']
                
                while hits:
                    for hit in hits:
                        existing_ids.add(hit['_id'])
                    
                    # 다음 배치 가져오기
                    result = self.es.scroll(scroll_id=scroll_id, scroll='2m')
                    scroll_id = result.get('_scroll_id')
                    hits = result['hits']['hits']
                
                # Scroll 정리
                if scroll_id:
                    self.es.clear_scroll(scroll_id=scroll_id)
                
                print(f"[ES 8.17] 기존 매물: {len(existing_ids)}개")
        except Exception as e:
            print(f"[ES 8.17] 기존 매물 조회 실패 (새 인덱스일 수 있음): {e}")
            existing_ids = set()

        total_success = 0
        total_failed = 0
        active_ids = set()  # 현재 활성 매물 ID 추적

        for json_file in json_files:
            file_path = os.path.join(data_dir, json_file)
            building_type = self.FILE_TYPE_MAPPING.get(json_file, "기타")
            print(f"\nProcessing {json_file} ({building_type})...")
            
            actions = []
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for item in data:
                    doc = self._transform_doc(item, building_type)
                    if doc:
                        actions.append(doc)
                        active_ids.add(doc['_id'])  # 활성 매물로 기록
                
                if actions:
                    success, failed = helpers.bulk(self.es, actions, stats_only=True, raise_on_error=False)
                    print(f"  ✓ Indexed: {success}, Failed: {failed}")
                    total_success += success
                    total_failed += failed
                else:
                    print("  ⚠️ No valid documents found in file.")
                    
            except Exception as e:
                print(f"  ❌ Error processing file: {e}")

        # 판매 완료된 매물 삭제
        sold_ids = existing_ids - active_ids
        total_deleted = 0
        
        if sold_ids:
            print(f"\n[ES 8.17] 판매 완료된 매물 {len(sold_ids)}개 삭제 중...")
            try:
                # 배치 삭제 (1000개씩)
                sold_list = list(sold_ids)
                batch_size = 1000
                
                for i in range(0, len(sold_list), batch_size):
                    batch = sold_list[i:i+batch_size]
                    delete_actions = [
                        {
                            "_op_type": "delete",
                            "_index": self.INDEX_NAME,
                            "_id": doc_id
                        }
                        for doc_id in batch
                    ]
                    
                    success, failed = helpers.bulk(
                        self.es, 
                        delete_actions, 
                        stats_only=True, 
                        raise_on_error=False
                    )
                    total_deleted += success
                    print(f"  배치 {i//batch_size + 1}: {success}건 삭제")
                
                print(f"[ES 8.17] ✅ 총 {total_deleted}건 삭제 완료")
            except Exception as e:
                print(f"[ES 8.17] ❌ 삭제 오류: {e}")
        else:
            print("\n[ES 8.17] 판매 완료된 매물 없음")

        print("\n" + "="*50)
        print("Elasticsearch 8.17 Import Completed")
        print(f"Total Indexed: {total_success}")
        print(f"Total Failed:  {total_failed}")
        print(f"Total Deleted: {total_deleted}")
        print("="*50)
        
        # Refresh index to make documents visible immediately
        self.es.indices.refresh(index=self.INDEX_NAME)

if __name__ == "__main__":
    importer = ES817PropertyImporter()
    importer.import_properties()
