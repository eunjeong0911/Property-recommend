모든 명령어는 **프로젝트 최상위 폴더 (`SKN18-FINAL-1TEAM`)** 실행 기준

---
### 1. 데이터 저장
- **작업**: FinalProject 구글 드라이브 공유 폴더에서 `data` 폴더 전체를 다운로드
- **위치**: 프로젝트 최상위 폴더 바로 아래에 `data` 폴더가 위치하도록 복사 (`SKN18-FINAL-1TEAM/data`)

### 2. Python 가상환경 생성 및 세팅
**1) 가상환경 생성** (터미널에 입력)
- `apps/reco/.venv` 폴더가 생성 (있으면 생략 가능)
```powershell
python -m venv apps/reco/.venv
```


**2) 가상환경 활성화**
- 터미널 앞부분에 `(reco)` 또는 `(.venv)`라고 뜨면 성공
```powershell
.\apps\reco\.venv\Scripts\Activate.ps1
```

**3) 가상환경 업데이트**
```powershell
python -m pip install --upgrade pip
```

**4) 라이브러리 설치**
```powershell
pip install -r apps/reco/requirements.txt
```


---

### 3. 데이터 전처리(data_preprocessing)

### 1단계: 데이터 전처리 (Preprocessing)

```powershell
python run_all_preprocessing.py
```
- **성공 확인**: `data/brokerInfo/grouped_offices.csv` 파일 생성
- **생성되는 파일 목록** (`data/brokerInfo/` 폴더 내):
  1. `land_brokers.csv` (Step 0: 원본 매물 데이터 추출)
  2. `broker_offices.csv` (Step 2: API 수집 데이터)
  3. `merged_brokers.csv` (Step 3: 데이터 병합)
  4. `cleaned_brokers.csv` (Step 4: 데이터 정제)
  5. `grouped_offices.csv` (Step 5: 사무소별 통계 - **최종 결과**)

### 2단계: 모델 학습 파이프라인 (Pipeline)

```powershell
python apps/reco/trust_model/pipeline/run_all.py
```
- **성공 확인**: `apps/reco/trust_model/final_trust_model.pkl` 파일 생성
