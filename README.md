# xing-tick-crawler
  - 반드시 python 32bit를 사용

## 사용예시
#### 1. config.py 파일 생성 및 설정 
```python
config = {
    "id": "my_id",  # xing api 아이디
    "password": "my_password",  # xing api 패스워드
    "cert_password": "my_cert_password",  # 공동인증서 비밀번호
}

RES_FOLDER_PATH = "C:/eBEST/xingAPI/Res"  # xing_tick_crawler Res 파일 폴더 위치
TICKER_DATA_FOLDER_PATH = "./ticker"  # tick 데이터 저장할 위치
```

#### 2. database, log 폴더 생성
- fold name : database
- fold name : log