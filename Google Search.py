import asyncio
import random
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
import selenium.common


# ============================================================================
# 새로 추가: Chrome 확장프로그램 자동 로드 (드라이버 반환)
# ============================================================================

async def load_chrome_extension_auto():
    """
    Chrome 확장프로그램을 자동으로 로드하고 드라이버를 반환합니다.
    이 드라이버를 이후 검색에서 그대로 사용합니다.
    
    프로세스:
    1. Chrome 드라이버 시작 (이 드라이버를 재사용)
    2. chrome://extensions/ 접속
    3. 개발자 모드 활성화
    4. "압축해제된 확장프로그램 로드" 버튼 클릭
    5. (파일 입력은 수동으로 - 7단계에서 완료 대기)
    6. 파일 선택 완료 및 확장프로그램 로드 대기
    7. 드라이버 반환
    
    Returns:
        driver: 확장프로그램이 로드된 Chrome WebDriver 인스턴스
    """
    
    print("\n" + "="*70)
    print("   [사전 작업] Chrome 확장프로그램 자동 로드")
    print("="*70)
    
    # 확장프로그램 폴더 경로 준비
    folder_path = os.path.dirname(os.path.realpath(__file__))
    extension_folder = os.path.join(folder_path, '3.1.0')
    extension_folder_abs = os.path.abspath(extension_folder)
    
    print(f"\n[1단계] 경로 준비")
    print(f" 폴더: {extension_folder_abs}")
    print(f" 존재: {os.path.exists(extension_folder_abs)}")
    
    if not os.path.exists(extension_folder_abs):
        print("✗ 폴더 없음 - 확장프로그램 로드 건너뜀")
        return None
    
    # Chrome 옵션 설정
    print(f"\n[2단계] Chrome 드라이버 시작")
    
    chrome_options = Options()
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument("--window-size=800,600")
    chrome_options.add_argument("--window-position=0,0")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    
    driver = None
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.set_window_size(800, 600)
        driver.set_window_position(0, 0)
        print("✓ Chrome 드라이버 시작")
        await asyncio.sleep(2)
    except Exception as e:
        print(f"✗ 드라이버 시작 오류: {e}")
        return None
    
    try:
        # chrome://extensions/ 접속
        print(f"\n[3단계] chrome://extensions/ 접속")
        
        driver.get("chrome://extensions/")
        await asyncio.sleep(3)
        print("✓ 페이지 접속")
        
        # 개발자 모드 활성화
        print(f"\n[4단계] 개발자 모드 활성화")
        
        dev_mode_result = driver.execute_script("""
            const manager = document.querySelector('extensions-manager');
            const toolbar = manager.shadowRoot.querySelector('extensions-toolbar');
            const toggle = toolbar.shadowRoot.querySelector('#devMode');
            
            if (toggle && !toggle.checked) {
                toggle.click();
            }
            return true;
        """)
        
        await asyncio.sleep(2)
        print("✓ 개발자 모드 활성화")
        
        # 버튼 클릭
        print(f"\n[5단계] '압축해제된 확장프로그램 로드' 버튼 클릭")
        
        button_clicked = driver.execute_script("""
            const manager = document.querySelector('extensions-manager');
            const toolbar = manager.shadowRoot.querySelector('extensions-toolbar');
            const buttons = toolbar.shadowRoot.querySelectorAll('cr-button, button');
            
            console.log('찾은 버튼 개수:', buttons.length);
            
            for (let btn of buttons) {
                const text = btn.textContent || btn.innerText || '';
                if (text.toLowerCase().includes('load') || text.toLowerCase().includes('압축')) {
                    console.log('✓ 버튼 발견, 클릭');
                    btn.click();
                    return true;
                }
            }
            return false;
        """)
        
        if button_clicked:
            print("✓ 버튼 클릭 성공")
            print("✓ Windows 파일 선택 팝업이 열렸습니다")
        else:
            print("⚠️ 버튼 클릭 실패")
        
        await asyncio.sleep(2)
        
        # ========================================================================
        # [6단계] 파일 선택 완료 대기
        # ========================================================================
        
        print(f"\n[6단계] 파일 선택 완료 대기")
        print(f"\n[안내] 아래 폴더를 선택하세요:")
        print(f"  {extension_folder_abs}\n")
        print("폴더 선택이 완료될 때까지 대기합니다...\n")
        
        # 파일 선택 완료 감지 (최대 300초 = 5분)
        max_wait = 120
        wait_interval = 2
        elapsed = 0
        extension_loaded = False
        
        while elapsed < max_wait and not extension_loaded:
            try:
                # 현재 페이지에서 확장프로그램 로드 확인
                page_source = driver.page_source
                
                # unpacked 상태 확인
                if 'unpacked' in page_source.lower():
                    extension_loaded = True
                    print("✓ 확장프로그램 로드 감지됨!")
                    break
                
                # 진행 상황 표시
                if elapsed % 10 == 0:
                    remaining = max_wait - elapsed
                    print(f"  대기 중... ({remaining}초 남음)", flush=True)
                
                await asyncio.sleep(wait_interval)
                elapsed += wait_interval
                
            except Exception as e:
                print(f"⚠️ 감지 오류: {e}")
                await asyncio.sleep(wait_interval)
                elapsed += wait_interval
        
        if extension_loaded:
            print("✓ 파일 선택 완료 및 확장프로그램 로드 완료")
        else:
            print(f"⚠️ {max_wait}초 대기 후에도 확장프로그램 로드 확인 불가")
            print("   수동으로 확인해주세요")
        
        # 페이지 새로고침
        print(f"\n[7단계] 페이지 새로고침 및 최종 확인")
        
        await asyncio.sleep(2)
        driver.refresh()
        await asyncio.sleep(4)
        
        page_source = driver.page_source
        
        if 'unpacked' in page_source.lower() or 'chrome-extension://' in page_source.lower():
            print("✓ 확장프로그램 로드 최종 확인 성공")
        else:
            print("⚠️ 확장프로그램 로드 불명확 (수동 확인 필요)")
        
        print("\n" + "="*70)
        print("   [사전 작업 완료] 이제 검색을 시작합니다.")
        print("="*70)
        
        # 드라이버 반환
        return driver
    
    except Exception as e:
        print(f"⚠️ 오류: {e}")
        if driver:
            driver.quit()
        return None


# --- reCAPTCHA 우회 함수 (최종 개선판) ---
async def bypass_recaptcha(driver):
    """
    Selenium에서 reCAPTCHA를 우회합니다.
    Google reCAPTCHA Enterprise 포함 다양한 버전 대응.
    """
    try:
        print("reCAPTCHA 우회 시도 중...")
        
        # --- 1단계: 기본 reCAPTCHA iframe 탐지 ---
        try:
            WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it(
                    (By.XPATH, "//iframe[@title='reCAPTCHA']")
                )
            )
            print("✓ reCAPTCHA iframe 발견 (표준)")
        except TimeoutException:
            print("⚠ 표준 reCAPTCHA iframe 미발견, Enterprise 버전 탐지 시도...")
            
            # Enterprise 버전 또는 기타 변형 title 탐지
            try:
                WebDriverWait(driver, 5).until(
                    EC.frame_to_be_available_and_switch_to_it(
                        (By.XPATH, "//iframe[contains(@title, 'reCAPTCHA')]")
                    )
                )
                print("✓ reCAPTCHA Enterprise iframe 발견")
            except TimeoutException:
                print("✗ reCAPTCHA iframe을 찾을 수 없음")
                return False
        
        # --- 2단계: 체크박스 클릭 (있을 경우) ---
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[@class='recaptcha-checkbox goog-inline-block recaptcha-checkbox-unchecked rc-anchor-checkbox']/div[@class='recaptcha-checkbox-border']")
                )
            ).click()
            print("✓ reCAPTCHA 체크박스 클릭 완료")
            await asyncio.sleep(2)
        except TimeoutException:
            print("⚠ 체크박스 미발견 (Enterprise 또는 자동 처리 버전)")
        except Exception as e:
            print(f"⚠ 체크박스 클릭 중 오류 (무시하고 진행): {e}")
        
        # --- 3단계: content로 복귀 ---
        driver.switch_to.default_content()
        await asyncio.sleep(1)
        
        # --- 4단계: bframe (보안문자 퍼즐) iframe 탐지 및 처리 ---
        print("\n[bframe(보안문자) iframe 탐지 중...]")
        
        puzzle_found = False
        max_retries = 5
        retry_count = 0
        
        # 다양한 iframe title 패턴 (한국어, 영어, 로케일 등)
        possible_titles = [
            "reCAPTCHA 보안문자",      # 한국어
            "reCAPTCHA&nbsp;보안문자", # HTML entity 포함
            "recaptcha challenge expires in two minutes",
            "recaptcha challenge",
            "reCAPTCHA",
        ]
        
        while retry_count < max_retries and not puzzle_found:
            try:
                print(f"\n  [시도 {retry_count + 1}/{max_retries}]")
                await asyncio.sleep(1)
                
                # 전체 iframe 목록
                all_iframes = driver.find_elements(By.TAG_NAME, "iframe")
                print(f"  - 전체 iframe 수: {len(all_iframes)}")
                
                for idx, iframe in enumerate(all_iframes):
                    try:
                        iframe_title = iframe.get_attribute("title") or ""
                        iframe_name = iframe.get_attribute("name") or ""
                        iframe_src = iframe.get_attribute("src") or ""
                        
                        # title이나 name에서 캡챠 관련 키워드 찾기
                        if any(keyword in iframe_title or keyword in iframe_name for keyword in 
                               ["보안문자", "challenge", "recaptcha", "bframe"]) or \
                           "bframe" in iframe_src:
                            
                            print(f"  ✓ bframe iframe 발견! (iframe #{idx})")
                            print(f"    title: '{iframe_title}'")
                            print(f"    name: '{iframe_name}'")
                            print(f"    src: '{iframe_src[:80]}...'")
                            
                            driver.switch_to.frame(iframe)
                            puzzle_found = True
                            break
                    
                    except StaleElementReferenceException:
                        print(f"    [{idx}] 요소 갱신 감지, 다음으로")
                        continue
                    except Exception as e:
                        print(f"    [{idx}] 오류: {e}")
                        continue
                
                if puzzle_found:
                    break
                else:
                    print(f"  - bframe iframe 미발견, 대기 후 재시도...")
                    retry_count += 1
                    await asyncio.sleep(2)
            
            except Exception as e:
                print(f"  ✗ iframe 검색 중 오류: {e}")
                retry_count += 1
                await asyncio.sleep(2)
        
        # --- 5단계: bframe 발견 시 자동 풀이 ---
        if puzzle_found:
            print("\n✓ bframe(보안문자) 발견 - 자동 풀이 시도")
            
            max_attempts = 10
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    # 다양한 selector로 버튼 탐색
                    help_button = None
                    possible_selectors = [
                        "//div[@class='button-holder help-button-holder']",
                        "//button[contains(@class, 'help')]",
                        "//div[contains(@class, 'help-button-holder')]//button",
                        "//div[@role='button'][contains(@aria-label, 'help')]",
                        "//div[contains(text(), '듣기')]",  # 한국어 '듣기' 버튼
                        "//button[@aria-label='듣기']",     # 한국어 음성 버튼
                    ]
                    
                    for selector in possible_selectors:
                        try:
                            elements = driver.find_elements(By.XPATH, selector)
                            if elements and elements[0].is_displayed():
                                help_button = elements[0]
                                print(f"  ✓ 자동 풀이 버튼 발견")
                                break
                        except:
                            continue
                    
                    if help_button:
                        try:
                            help_button.click()
                            print(f"  - 자동 풀이 시도 {attempt + 1}/{max_attempts}")
                            await asyncio.sleep(2)
                            attempt += 1
                        except ElementClickInterceptedException:
                            print("✓ 자동 풀이 완료")
                            break
                    else:
                        # 버튼이 없으면 인증 완료로 간주
                        print("✓ 풀이 버튼 없음 - 인증 완료")
                        break
                
                except TimeoutException:
                    print("✓ 인증 완료 (타임아웃)")
                    break
                except StaleElementReferenceException:
                    print("  - 요소 갱신, 재시도")
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"  - 오류: {e}")
                    await asyncio.sleep(1)
                    attempt += 1
            
            driver.switch_to.default_content()
            await asyncio.sleep(2)
            print("✓ reCAPTCHA 우회 완료")
            return True
        
        else:
            # bframe 미발견
            print("\n⚠ bframe(보안문자) 미발견 - 단순 체크박스만 필요")
            driver.switch_to.default_content()
            return True
    
    except Exception as e:
        print(f"✗ reCAPTCHA 우회 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


# --- 쿠키/캐시 삭제 함수 ---
async def clear_cookies_and_cache(driver):
    """
    Selenium에서 쿠키와 캐시를 삭제합니다.
    """
    try:
        # 쿠키 삭제
        driver.delete_all_cookies()
        print("✓ 브라우저 쿠키 삭제 완료")
        
        # 캐시 삭제 (Chrome 설정 페이지 활용)
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        driver.get('chrome://settings/clearBrowserData')
        
        # async sleep 사용
        await asyncio.sleep(2)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        
        print("✓ 브라우저 캐시 삭제 완료")
        return True
    except Exception as e:
        print(f"쿠키/캐시 삭제 중 오류: {e}")
        return False



# --- 단일 검색어 처리용 작업자 함수 ---
async def search_single_term(driver, term):
    """
    한 개의 검색어를 검색하고, 파싱한 뒤, (상태, 결과 리스트)를 반환합니다.
    (SUCCESS, CAPTCHA, FAILURE), (results_list)
    """
    
    term_results = []
    
    try:
        driver.get("https://www.google.com")
        
        #print("페이지 로드 대기 중... (3초)")
        await asyncio.sleep(3)


        try:
            #print("쿠키 동의창 확인 중...")
            # 쿠키 동의 버튼 찾기
            consent_buttons = driver.find_elements(
                By.XPATH, 
                "//button[contains(., '모두 동의') or contains(., 'Accept all')]"
            )
            
            if consent_buttons:
                #print("쿠키 동의창 발견. '모두 동의' 클릭.")
                consent_buttons[-1].click()
                await asyncio.sleep(2)
                
                #print("검색창을 찾는 중...")
                search_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "q"))
                )
            else:
                #print("쿠키 동의창 없음. 메인 페이지에서 검색창을 찾습니다...")
                search_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "q"))
                )
        except Exception as e:
            print(f"쿠키 동의창 처리 중 오류 발생 (무시하고 진행): {e}")
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
        
        #print("검색어를 입력합니다...")
        search_box.clear()
        search_box.send_keys(term)
        
        #print("Enter 키를 누릅니다...")
        search_box.send_keys(Keys.RETURN)
        
        #print("검색 완료. 결과 페이지 로드 대기 중... (3초)")
        await asyncio.sleep(3)


        #print("검색 결과 파싱을 시도합니다...")


        # --- 1순위: 캡챠 확인 ---
        captcha_elements = driver.find_elements(
            By.XPATH, 
            "//div[@class='g-recaptcha']"
        )
        if captcha_elements:
            print("!! reCAPTCHA 감지됨. 우회 시도 중...")
            return "CAPTCHA", []


        # --- 2순위: '결과 없음' 확인 ---
        no_results_elements = driver.find_elements(
            By.XPATH,
            f"//div[contains(text(), '일치하는 검색결과가 없습니다') and contains(text(), '{term}')]"
        )
        if no_results_elements:
            print(f"'{term}'에 대한 검색 결과가 없습니다.")
            return "SUCCESS", []
        
        # --- 3순위: 정상 결과 파싱 ---
        #print("\n검색 결과를 찾는 중...")
        
        try:
            result_links_list = driver.find_elements(
                By.XPATH,
                "//div[@id='search']//a[.//h3]"
            )
            #print(f"검색 결과 링크 발견: {len(result_links_list)}개")
            
        except Exception as e:
            print(f"검색 결과 추출 중 오류: {e}")
            result_links_list = []
            
        print(f"최종 발견된 링크 수: {len(result_links_list)}")


        if result_links_list:
            print(f"'{term}' 검색 결과 (상위 5개):")
            count = 0
            
            for link_element in result_links_list:
                try:
                    # 제목 찾기
                    h3 = None
                    for selector in ['h3', './/h3']:
                        try:
                            if selector.startswith('.'):
                                h3_elements = link_element.find_elements(By.XPATH, selector)
                            else:
                                h3_elements = link_element.find_elements(By.TAG_NAME, selector)
                            
                            if h3_elements:
                                h3 = h3_elements[0]
                                break
                        except:
                            continue
                    
                    if not h3:
                        print("   경고: 결과의 제목을 찾을 수 없음")
                        continue
                    
                    title = h3.text
                    url = link_element.get_attribute('href')
                    
                    # 설명 찾기
                    description = None
                    try:
                        snippet_selectors = [
                            ".//div[contains(@class, 'VwiC3b')]",
                            ".//div[contains(@class, 'yXK7lf')]",
                            ".//div[contains(@class, 'lyLwlc')]",
                        ]
                        
                        for selector in snippet_selectors:
                            try:
                                snippet_elements = link_element.find_elements(By.XPATH, selector)
                                if snippet_elements:
                                    description = snippet_elements[0].text
                                    if description:
                                        break
                            except:
                                continue
                    except Exception as e:
                        print(f"   설명 추출 오류: {e}")
                    
                    if title and url and url.startswith("http"):
                        # 콘솔에 출력
                        print(f"   [{count+1}] {title}")
                        print(f"        {url}")
                        
                        # 파일 저장을 위해 결과 리스트에 추가
                        if description:
                            result_line = f"   [{count+1}] {title.strip()}\n        설명: {description.strip()}\n        {url}\n"
                        else:
                            result_line = f"   [{count+1}] {title.strip()}\n        {url}\n"
                        term_results.append(result_line)
                        
                        count += 1
                        if count >= 5:
                            break
                            
                except Exception as e:
                    print(f"      (개별 항목 파싱 오류: {e})")
                    pass
            
        #    if count == 0:
        #        print(f"'{term}'에 대한 유효한 검색 결과를 찾지 못했습니다.")
        #else:
        #    print(f"'{term}'에 대한 유효한 검색 결과를 찾지 못했습니다.")
        
        return "SUCCESS", term_results


    except Exception as e:
        print(f"'{term}' 검색 중 오류 발생: {e}")
        return "FAILURE", []



# --- 브라우저 생명 주기를 관리하는 메인 함수 ---
async def perform_google_searches_with_selenium(file_path):
    """
    Selenium을 사용하여 구글 검색을 수행합니다.
    """
    
    # ========================================================================
    # ⭐ NEW: 사전 작업 - 확장프로그램 로드 (드라이버 반환)
    # ========================================================================
    
    print("\n[프로그램 시작]\n")
    
    # 확장프로그램을 로드하고 드라이버 받기
    driver = await load_chrome_extension_auto()
    
    if driver is None:
        print("✗ 확장프로그램 로드 실패 - 프로그램 종료")
        return
    
    # ========================================================================
    
    # --- 1. 검색어 파일 읽기 ---
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            search_terms = [line.strip() for line in f if line.strip()]
        if not search_terms:
            print(f"오류: '{file_path}' 파일이 비어있습니다.")
            if driver:
                driver.quit()
            return
    except FileNotFoundError:
        print(f"오류: '{file_path}' 파일을 찾을 수 없습니다.")
        if driver:
            driver.quit()
        return
    print(f"총 {len(search_terms)}개의 검색어를 찾았습니다. 검색을 시작합니다.\n")


    # --- 2. 모든 검색 결과를 저장할 딕셔너리 ---
    all_search_results = {}
    failed_terms = []


    MAX_RETRIES = 3
    retry_counts = {}
    cache_clear_attempted = {}


    # --- 3. 검색 루프 ---
    search_index = 0
    while search_index < len(search_terms):
        term = search_terms[search_index]
        
        if term not in retry_counts:
            retry_counts[term] = 0
        
        if term not in cache_clear_attempted:
            cache_clear_attempted[term] = False
        
        try:
            print(f"\n[{search_index + 1}/{len(search_terms)}] '{term}' 검색 중...")
            if retry_counts[term] > 0:
                print(f"  (재시도 {retry_counts[term]}/{MAX_RETRIES})")
            
            status, results_data = await search_single_term(driver, term)


            # --- 4. 상태에 따른 로직 처리 ---
            if status == "SUCCESS":
                print(f"'{term}' 검색 성공.")
                all_search_results[term] = results_data
                search_index += 1
                retry_counts[term] = 0
                cache_clear_attempted[term] = False
                
                sleep_time = random.uniform(1, 5)
                print(f"봇 탐지 회피를 위해 {sleep_time:.1f}초 대기합니다...")
                await asyncio.sleep(sleep_time)


            elif status == "CAPTCHA":
                retry_counts[term] += 1
                
                if retry_counts[term] > MAX_RETRIES:
                    # 캐시 삭제를 아직 시도하지 않았다면 1회 추가 시도
                    if not cache_clear_attempted[term]:
                        print(f"!! '{term}' 검색 재시도 한도 초과 ({MAX_RETRIES}회).")
                        print("쿠키/캐시 삭제 및 브라우저 재시작 후 1회 추가 시도합니다...")
                        
                        cache_clear_attempted[term] = True
                        
                        # 브라우저 종료 및 재시작
                        if driver:
                            try:
                                driver.quit()
                            except:
                                pass
                        driver = None
                        
                        # 재시도 카운터 리셋
                        retry_counts[term] = 0
                        
                        wait_time = 10
                        print(f"브라우저 재시작 전 {wait_time}초 대기합니다...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        # 캐시 삭제 후에도 실패한 경우 완전히 건너뛰기
                        print(f"!! '{term}' 캐시 삭제 후에도 실패. 건너뜁니다.")
                        all_search_results[term] = []
                        search_index += 1
                        retry_counts[term] = 0
                        cache_clear_attempted[term] = False
                        await asyncio.sleep(5)
                        continue
                
                print(f"!! 캡챠 감지 (재시도 {retry_counts[term]}/{MAX_RETRIES})")
                
                # --- ⭐ NEW: reCAPTCHA 우회 시도 (캐시 삭제 전) ---
                print("\n>> reCAPTCHA 자동 우회 시도 중...\n")
                bypass_success = await bypass_recaptcha(driver)
                
                if bypass_success:
                    print("\n>> reCAPTCHA 우회 완료! 검색 재시도합니다.\n")
                    await asyncio.sleep(1)
                    # search_index는 증가시키지 않음 (검색 재시도)
                else:
                    print("\n>> reCAPTCHA 우회 실패. 캐시 삭제 후 재시도합니다.\n")
                    print("쿠키/캐시 삭제를 시도합니다...")
                    
                    # 쿠키/캐시 삭제 시도
                    if await clear_cookies_and_cache(driver):
                        print("쿠키/캐시 삭제 완료. 잠시 후 재시도합니다.")
                        await asyncio.sleep(5)
                    else:
                        print("쿠키/캐시 삭제 실패. 브라우저를 재시작합니다.")
                        driver.quit()
                        driver = None
                        await asyncio.sleep(5)
                
                # search_index는 증가시키지 않음 (재시도)


            elif status == "FAILURE":
                print(f"'{term}' 검색 실패. 다음 검색어로 넘어갑니다.")
                all_search_results[term] = []
                search_index += 1
                retry_counts[term] = 0
                cache_clear_attempted[term] = False
                await asyncio.sleep(random.uniform(5, 10))


        except Exception as e:
            print(f"스크립트 실행 중 심각한 오류 발생: {e}")
            if driver:
                driver.quit()
            driver = None
            search_index += 1
            retry_counts[term] = 0
            cache_clear_attempted[term] = False
            
    print("\n--- 모든 검색어를 성공적으로 처리했습니다. ---")


    # --- 5. 모든 작업 완료 후 파일 저장 ---
    print("\n--- 검색 결과를 'search_results.txt' 파일에 저장합니다 ---")
    output_filename = "search_results.txt"
    
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            total_saved_count = 0
            for term, results in all_search_results.items():
                if results:
                    f.write(f"--- 검색어: {term} ---\n")
                    for result_line in results:
                        f.write(f"{result_line}\n")
                    f.write("\n")
                    total_saved_count += 1
            
        print(f"총 {len(all_search_results)}개의 검색어 중 {total_saved_count}개의 유효한 결과를 '{output_filename}'에 저장했습니다.")
    
    except Exception as e:
        print(f"!! 파일 저장 중 오류 발생: {e}")


    # --- 6. 최종 브라우저 종료 ---
    if driver:
        driver.quit()
    print("브라우저를 종료했습니다.")



# --- 스크립트 실행 ---
if __name__ == "__main__":
    search_file = "search_terms.txt"
    
    try:
        asyncio.run(perform_google_searches_with_selenium(search_file))
    except KeyboardInterrupt:
        print("\n사용자에 의해 프로그램이 중지되었습니다.")