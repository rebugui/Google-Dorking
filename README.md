# Google Search.py 설명 및 사용자 매뉴얼

## 개요
`Google Search.py`는 Selenium을 사용하여 로컬에 작성된 검색어 목록(`search_terms.txt`)을 순차적으로 구글에 검색하고, 상위 검색 결과(최대 상위 5개)를 추출하여 `search_results.txt`로 저장하는 자동화 스크립트입니다. 또한 사전작업으로 Chrome 확장프로그램(폴더 `3.1.0`)을 로드하는 기능과 reCAPTCHA 감지 시 우회(자동 클릭/퍼즐 탐지) 시도를 포함하고 있습니다.

참고: 이 스크립트는 Buster Captcha Solver for Humans 확장 프로그램(버전 3.1.0)의 언팩된 폴더 `3.1.0`을 사용하도록 설계되어 있습니다. 확장프로그램을 자동으로 설치하지는 않으며, 확장 폴더가 스크립트와 동일한 디렉터리에 있어야 하고 확장 로드 단계에서 OS 파일 선택 대화상자에서 해당 폴더를 수동으로 선택해 주어야 정상적으로 로드됩니다.

> 언어: 한국어

## 주요 기능 요약
- Chrome WebDriver 시작 및 확장프로그램(압축해제된 확장) 자동 로드 시도 (`load_chrome_extension_auto`)
- reCAPTCHA 탐지 및 우회 시도 (`bypass_recaptcha`)
- 쿠키/캐시 삭제 (`clear_cookies_and_cache`)
- 단일 검색어 검색 및 결과 파싱 (`search_single_term`)
- 검색어 목록을 읽고 전체 워크플로우를 관리 (`perform_google_searches_with_selenium`)

## 요구사항(Prerequisites)
- 운영체제: Windows (테스트 환경 기준)
- Python 3.8+ 권장
- Chrome 브라우저 (ChromeDriver 버전과 일치해야 합니다)
- pip로 설치된 패키지:
  - selenium

확장프로그램:

- Buster Captcha Solver for Humans (버전 3.1.0) — 언팩된 폴더 이름을 `3.1.0`로 두고 스크립트와 동일한 경로에 배치하세요. 스크립트의 확장 로드 단계에서 파일 선택 대화상자가 뜨면 해당 폴더를 선택해야 합니다.

설치 예시 (PowerShell):

```powershell
pip install selenium
```

ChromeDriver 설치: 현재 사용 중인 Chrome의 버전과 동일한 ChromeDriver를 다운로드하여 PATH에 추가하거나 드라이버의 경로를 코드에 맞춰 설정하세요.

확장프로그램: 코드가 `3.1.0` 폴더를 확장프로그램(언팩된 확장)으로 로드하려 시도합니다. 이 폴더가 스크립트와 같은 디렉터리(또는 `3.1.0` 이름)로 존재해야 합니다. 없으면 확장 로드 단계는 건너뜁니다.

## 파일/입력
- `Google Search.py` (스크립트)
- `search_terms.txt` (한 줄에 하나의 검색어, UTF-8)
- `3.1.0/` (선택: 압축해제된 Chrome 확장 프로그램 폴더)

## 출력
- `search_results.txt` : 검색어별로 상위(최대 5개) 결과를 저장
- 콘솔 출력: 진행 상태, 오류 및 디버그 메시지

## 실행방법
PowerShell에서 스크립트가 있는 디렉터리로 이동한 뒤:

```powershell
python "Google Search.py"
```

스크립트는 내부에서 `search_terms.txt`를 읽습니다. 파일이 없으면 오류 메시지를 출력하고 종료합니다.

## 함수별 상세 설명

### load_chrome_extension_auto()
- 목적: Chrome을 실행하고, Buster Captcha Solver for Humans(언팩된 버전 `3.1.0`) 확장 폴더가 존재하면 `chrome://extensions/`로 이동해 '압축해제된 확장프로그램 로드' 버튼을 클릭하여 수동으로 폴더를 선택하도록 유도하고, 로드 완료를 대기한 후 WebDriver를 반환합니다.
- 반환: 로드에 성공한 Chrome WebDriver 객체 (실패 시 `None` 반환)
- 주의: 이 함수는 파일 선택 대화상자를 실제로 자동으로 조작하지 않습니다. 사용자가 OS 파일 선택 창에서 `3.1.0` 폴더를 수동으로 선택해야 합니다. (스크립트는 선택 완료를 페이지 소스에서 `unpacked` 또는 `chrome-extension://` 문자열을 찾아 감지합니다.)

### bypass_recaptcha(driver)
- 목적: Google reCAPTCHA(체크박스/퍼즐/Enterprise 변형)에 대해 자동으로 우회 시도를 수행합니다.
- 동작 요약:
  1. 기본 reCAPTCHA iframe을 찾아 전환.
  2. 체크박스 요소를 찾아 클릭 시도.
  3. `bframe`(보안문자/퍼즐) iframe을 탐지하고, 음성(help/listen) 버튼 등의 요소를 반복 탐색해 클릭 시도.
  4. 성공적으로 처리되면 `True` 반환, 실패 또는 예외 시 `False` 반환.
- 한계: 완전한 자동 풀이(이미지 선택 등)는 구현되어 있지 않습니다. 주로 체크박스/음성 버튼 트리거 및 상태 감지 위주의 보조 로직입니다.

### clear_cookies_and_cache(driver)
- 목적: 현재 브라우저 세션의 쿠키를 삭제하고 `chrome://settings/clearBrowserData` 페이지를 열어 캐시 삭제를 시도합니다.
- 반환: 성공 시 `True`, 실패 시 `False`.
- 주의: 페이지를 연 뒤 실제로 브라우저의 설정 UI에서 사용자가 직접 확인/조작해야 할 수 있습니다. 코드에서는 새 탭 열기/닫기를 통해 동작을 유도합니다.

### search_single_term(driver, term)
- 목적: 단일 검색어를 Google에 검색하고 상위 결과(최대 5개)를 파싱하여 리스트로 반환.
- 반환: (status, results_list)
  - status: "SUCCESS", "CAPTCHA", "FAILURE"
  - results_list: 각 결과의 문자열(제목, 설명, URL 포함)
- 동작 요약:
  1. `https://www.google.com`에 접속
  2. 쿠키 동의 팝업(예: '모두 동의' 버튼)이 있으면 클릭
  3. 검색어 입력 후 엔터
  4. reCAPTCHA 요소 존재 시 `CAPTCHA` 반환
  5. 결과가 없으면 빈 리스트와 `SUCCESS` 반환
  6. 정상 결과가 있으면 최대 5개를 수집하여 `SUCCESS`와 함께 반환
- 예외 처리: 예외 발생 시 `FAILURE` 반환

### perform_google_searches_with_selenium(file_path)
- 목적: 전체 파이프라인을 관리합니다.
  1. `load_chrome_extension_auto()`로 드라이버 준비
  2. `file_path`에서 검색어 목록 로드
  3. 각 검색어에 대해 `search_single_term` 호출
  4. CAPTCHA 발생 시 `bypass_recaptcha` 시도 후 실패하면 쿠키/캐시 삭제 또는 브라우저 재시작
  5. 결과를 `search_results.txt`로 저장
- 주요 상수/설정:
  - MAX_RETRIES = 3 (CAPTCHA 재시도 최대 횟수)
  - 각 검색 성공 후 1~5초 랜덤 대기(봇 탐지 완화)

## 입력 파일 예시 (`search_terms.txt`)

```
파이썬 웹 스크래핑
Selenium 사용법
OpenAI ChatGPT
```

각 줄은 하나의 검색어로 간주됩니다.

## 출력 파일 예시 (`search_results.txt`)
- 검색어별로 다음과 같은 형식으로 저장됩니다:

```
--- 검색어: 파이썬 웹 스크래핑 ---
   [1] 제목 A
        설명: 요약...
        https://example.com

   [2] 제목 B
        https://example2.com


```

## 문제 해결 / 트러블슈팅
- 브라우저(Chrome)와 ChromeDriver 버전 불일치:
  - Chrome 버전을 확인하고 동일한 버전의 ChromeDriver를 설치하세요.
- `search_terms.txt` 파일을 찾을 수 없음:
  - 스크립트를 실행하는 현재 작업 디렉터리에 `search_terms.txt`가 있어야 합니다.
- 확장프로그램 자동 로드 실패:
  - `3.1.0` 폴더가 스크립트와 같은 위치에 있는지 확인하세요. 파일 선택 팝업이 뜨면 수동으로 해당 폴더를 선택해야 합니다.
- reCAPTCHA가 계속 발생:
  - 자동 우회는 완벽하지 않습니다. 수동으로 캡차를 풀어주거나(브라우저에서) IP/세션을 변경하는 것을 고려하세요.
- `selenium.common.exceptions` 관련 에러:
  - 네트워크 지연/DOM 변경 때문에 발생합니다. 재시도하거나 sleep 시간을 늘려 보세요.

## 보안 및 법적 주의사항
- Google의 서비스 약관은 자동화된 접근을 제한할 수 있습니다. 상업적 목적이거나 대량 요청을 할 경우 해당 서비스 약관을 반드시 확인하세요.
- reCAPTCHA 우회는 보안 및 윤리 측면에서 문제가 될 수 있으므로, 합법적이고 윤리적인 범위 내에서만 사용하세요.

## 한계 및 개선 제안
- 확장프로그램 로드 단계에서 파일 선택은 수동으로 진행해야 하므로 완전 자동화가 아님.
- reCAPTCHA 자동 풀이(이미지 인식 등) 미구현 — 서드파티 서비스(예: 2captcha) 연동 또는 OCR/음성 API 연동 고려.
- ChromeDriver 경로 하드코딩 옵션 추가 및 헤드리스(headless) 모드 선택 지원.
- 결과 저장 형식을 CSV/JSON으로 선택 가능하도록 확장.
- 동시성(멀티스레드/멀티프로세스) 처리를 통한 속도 향상(단, 봇 탐지 위험 증가).

## 최종 확인 및 실행 요약
1. `python -m pip install selenium`
2. ChromeDriver를 설치하고 PATH에 추가
3. `search_terms.txt`를 준비
4. (선택) `3.1.0` 확장 폴더를 스크립트와 같은 경로에 둠
5. PowerShell에서 `python "Google Search.py"` 실행

---

생성된 파일: `search_results.txt` (스크립트 종료 후 생성)

필요하면 이 매뉴얼을 더 구체적으로 바꾸거나 영어 번역본을 생성해 드리겠습니다.