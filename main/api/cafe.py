import requests
import html
import logging
import traceback
from bs4 import BeautifulSoup
import random

class CafeAPI:
    def __init__(self, headers):
        self.headers = {k: v for k, v in headers.items() if not k.startswith('_')}
        
    def get_cafe_list(self):
        """가입된 카페 목록 조회"""
        api_url = "https://apis.naver.com/cafe-home-web/cafe-home/v1/cafes/join?page=1&perPage=1000&type=join&recentUpdates=true"
        response = requests.get(api_url, headers=self.headers)
        data = response.json()
        
        # 딕셔너리 형태로 반환
        return [
            {
                'cafe_id': cafe['cafeId'], 
                'cafe_url': cafe['cafeUrl'], 
                'cafe_name': cafe['cafeName']
            } 
            for cafe in data['message']['result']['cafes']
        ]


    def check_cafe_id(self, url:str, cafe_id = None):
        if cafe_id:
            return cafe_id
    
        try:
            if not url.startswith("https://"):
                url = url.replace("http://", "")
                url = "https://" + url

            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            input_tag = soup.find('input', {'name': 'clubid'})
            return input_tag['value'] if input_tag else None
        except:
            logging.error(f"Cafe ID 추출 Error :: {traceback.format_exc()}")
            return False

    def get_board_list(self, cafe_id):
        """게시판 목록 조회"""
        try:
            menu_list = []
            url = f"https://apis.naver.com/cafe-web/cafe2/SideMenuList?cafeId={cafe_id}"
            response = requests.get(url, headers=self.headers)

            response_json = response.json()
            if response.status_code == 200:
                for menu in response_json['message']['result']['menus']:
                    if menu['menuType'] != 'P' and menu['menuType'] != 'L' and menu['menuType'] != 'F':
                        menu_list.append({
                            'board_id': menu['menuId'],
                            'board_name': menu['menuName'],
                            'menu_type': menu['menuType'],
                            'board_type': menu.get('boardType', ''),
                            'sort': menu.get('sort', 0)
                        })
            return menu_list
        except Exception as e:
            logging.error(f"게시판 목록 조회 오류: {str(e)}")
            return []
        
    def get_cafe_info(self, cafe_id):
        """카페 정보 조회"""
        url = f'https://cafe.naver.com/{cafe_id}'
        response = requests.get(url, headers=self.headers)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        info = {
            'id': cafe_id,
            'name': soup.select_one('.cafe-name').text.strip() if soup.select_one('.cafe-name') else '',
            'description': soup.select_one('.cafe-description').text.strip() if soup.select_one('.cafe-description') else ''
        }
        
        return info 

    def get_nickname(self, cafe_id):
        """카페 닉네임 조회"""
        try:
            url = f"https://apis.naver.com/cafe-web/cafe-cafeinfo-api/v2.0/cafes/{cafe_id}/member-profile/config"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                return data['result']['nickName']
            else:
                print(f"닉네임 조회 실패 - 상태 코드: {response.status_code}")
                print(f"응답 내용: {response.text}")
                return None
                
        except Exception as e:
            print(f"닉네임 조회 중 오류 발생: {str(e)}")
            print(traceback.format_exc())
            return None
            
    def update_nickname(self, cafe_id, new_nickname):
        """카페 닉네임 변경"""
        try:
            # 먼저 현재 프로필 정보 가져오기
            url = f"https://apis.naver.com/cafe-web/cafe-cafeinfo-api/v2.0/cafes/{cafe_id}/member-profile/config"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                print(f"프로필 정보 조회 실패 - 상태 코드: {response.status_code}")
                return False
                
            current_profile = response.json()['result']
            
            # 프로필 업데이트 요청
            update_url = f"https://apis.naver.com/cafe-web/cafe-cafeinfo-api/v3.0/cafes/{cafe_id}/member-profile"
            
            payload = {
                "allowMemberAlarm": current_profile['allowMemberAlarm'],
                "allowPopularMember": current_profile['allowPopularMember'],
                "cafeProfileImagePath": current_profile['cafeProfileImagePath'],
                "introduction": current_profile['introduction'],
                "nickname": new_nickname,  # 새로운 닉네임으로 변경
                "realNameUse": current_profile['realNameUse'],
                "receivingWholeMail": current_profile['receivingWholeMail'],
                "showBlog": current_profile['showBlog'],
                "showSexAndAge": current_profile['showSexAndAge']
            }
            
            # 업데이트용 헤더 설정
            headers = self.headers.copy()
            headers.update({
                'Content-Type': 'application/json',
                'Referer': f'https://cafe.naver.com/ca-fe/cafes/{cafe_id}/member-profile/setting'
            })
            
            update_response = requests.post(update_url, headers=headers, json=payload)
            
            if update_response.status_code == 200:
                print(f"닉네임 변경 성공: {new_nickname}")
                return True
            else:
                print(f"닉네임 변경 실패 - 상태 코드: {update_response.status_code}")
                print(f"응답 내용: {update_response.text}")
                return False
                
        except Exception as e:
            print(f"닉네임 변경 중 오류 발생: {str(e)}")
            print(traceback.format_exc())
            return False
        
    # 게시글 수집
    # menu_id를 비우고 요청할 경우 전체 글 조회
    # 제목뿐만 아니라 내용도 가져와야함
    def call_board_list(self, cafe_id, menu_id, per_page=20):
        result = []

        url = f"https://apis.naver.com/cafe-web/cafe2/ArticleListV2dot1.json?search.clubid={cafe_id}&search.queryType=lastArticle&search.menuid={menu_id}&search.page={1}&search.perPage={per_page}&adUnit=MW_CAFE_ARTICLE_LIST_RS"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                response_json = response.json()
                article_list = response_json['message']['result']['articleList']
                article_list = sorted(article_list, key=lambda x:x['articleId'])
                for article in article_list:
                    article_id = article['articleId']
                    subject = article['subject']
                    writer = article['writerNickname']
                    result.append({"article_id": article_id, "subject": subject, "writer": writer})

            return result
        except:
            logging.error("게시글 수집 실패: ", response_json['message'])

    # 게시글 내용 GET
    def get_board_content(self, cafe_id, article_id):
        url = f"https://apis.naver.com/cafe-web/cafe-articleapi/v2.1/cafes/{cafe_id}/articles/{article_id}?useCafeId=true&requestFrom=A"

        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                response_json = response.json()
                return response_json['result']['article']['contentHtml']
        except:
            self.util_log.add_log(f"게시글 내용 수집 실패: {response_json['message']}", "red")
            logging.error("게시글 내용 수집 실패: ", response_json['message'])

    # 네이버 API에서 리턴받은 html 파싱
    def get_parse_content_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')

        # 내용 추출
        elements = soup.select('.se-module-text .se-text-paragraph span')
        content = ' '.join([element.get_text(strip=True) for element in elements])

        return content

    def get_board_title_and_content(self, cafe_id, menu_id, per_page):
        """게시판의 게시글 제목과 내용을 가져옵니다.
        
        Args:
            cafe_id (str): 카페 ID
            menu_id (str): 메뉴 ID
            per_page (int): 가져올 게시글 수
            
        Returns:
            str: 게시글 제목과 내용 정보
        """
        result = ""

        response = self.call_board_list(cafe_id, menu_id, per_page)

        content_cnt = 1
        for res in response:
            try:
                board_content = self.get_board_content(cafe_id, res['article_id'])
                content = self.get_parse_content_html(board_content)
                
                # 내용이 너무 길면 요약
                if content and len(content) > 200:
                    content = content[:200] + "..."
                
                result += f"게시글 {content_cnt}:\n제목: {res['subject']}\n내용: {content}\n\n"
                content_cnt += 1
            except Exception as e:
                logging.error(f"게시글 내용 수집 실패: {str(e)}")
                continue
            
        return result
            
    def test_nickname(self, cafe_id):
        """닉네임 관련 기능 테스트"""
        try:
            # 현재 닉네임 조회
            current_nick = self.get_nickname(cafe_id)
            if current_nick:
                print(f"현재 닉네임: {current_nick}")
                
                # 테스트용 닉네임으로 변경
                test_nicks = [
                    "행복한하루123",
                    "즐거운여행가",
                    "꿈꾸는나비99",
                    "달콤한초코칩",
                    "푸른하늘별",
                    "웃는해바라기",
                    "신나는음악가",
                    "따뜻한커피향",
                    "자유로운영혼",
                    "평화로운마음"
                ]
                test_nick = random.choice(test_nicks)
                if self.update_nickname(cafe_id, test_nick):
                    print("닉네임 변경 테스트 성공")
                    
                    new_nick = self.get_nickname(cafe_id)
                    if new_nick == test_nick:
                        print(f"변경된 닉네임: {new_nick}")
                    else:
                        print("닉네임 변경 테스트 실패")
                else:
                    print("닉네임 변경 테스트 실패")
            else:
                print("현재 닉네임 조회 실패")
                
            return True
            
        except Exception as e:
            print(f"닉네임 테스트 중 오류 발생: {str(e)}")
            return False 
        
if __name__ == "__main__":
    headers = {
        "content-type": "application/json",
        "origin": "https://cafe.naver.com",
        "referer": "https://cafe.naver.com",
        "x-cafe-product": "pc",
        'se-authorization': "",
        'cookie': "rankingHidden=31203823; NNB=2QP3YT6BPGMWI; ASID=31a8f9cc0000018978da1f5400000064; ncvid=#vid#_115.138.87.199IWS1; ba.uuid=a76ad3c1-5903-42bd-8399-3eb89840598c; tooltipDisplayed=true; _ga_6Z6DP60WFK=GS1.2.1726462403.1.0.1726462403.60.0.0; NFS=2; _ga=GA1.1.877073880.1704979036; _ga_EFBDNNF91G=GS1.1.1732339996.1.0.1732339999.0.0.0; _ga_8P4PY65YZ2=GS1.1.1734265772.1.1.1734265776.56.0.0; nstore_session=uajHtGrn2P2hNissMDvcn+a3; nstore_pagesession=iI4S7lqW4vuF/ssL/6s-089597; NAC=bt7NBgQZgVqM; jdh7693__storageID=e3e49b48-fddc-0668-a833-1a85161010b2; ncu=8bb05b2d3f7a1fdefb3d7a7b80681e2cd8; NACT=1; SRT30=1740880008; nid_inf=2008104164; NID_AUT=yx/rL+3DVICGF6iUGkEWzTYvy51RIcSdPLB0PSyjWtTtdX8uDEAeH9aJnoRAH3fq; NID_JKL=PqLukHQIo1uRZ7v00pbFXTCw5SK2YdU5xqof6m8PJVs=; nci4=0e39ddf6e6a7c27129c780979a650a60d8957b88dd984f9c46a4a9bb492ece01cd5b933efdbd44021bea9be157d572ba71597e30dbed88d2ee0d8d6190ae1bfdb283cebfb691b485bab5b89fbf8cdca9a58da899d1a1ac8b92a3ef9894b398ae9f9382a580b1faf9f8fff5f3f2f682f2d6f1c785ea878782ec819cf18299f0; ncmc4=6651b59e8ecfaa1941afe8fff2007401fead5cb492c80ff438dbff27b8bd6e8056b844a5512abb97980a7f870fa966d040294a13b0c0ea86f971930b80fa7db3fcdbe8d9d0dffadde2ad7b; ncvc2=9da64d3b296c09a4907210231df080f84708eb174914f42cd310249c; rankingHidden=31203823; page_uid=i8nZ7dqVN8wssb+LHwwssssstV0-232005; NID_SES=AAABiuBkrIWsVe93h9uQIqHSvg+HsKzJK7mRgd55BHW8lT6ReW1sFxW+o95RRJBtF0KIvPDGo6XnaiWAVAWuQ12Fyd+rJOmRwuKLh56mUieNJISn+TENTsUZzyCIh/+8UC2gyAtaw+3k4C12XrpohYv3we9/+LxuGh/4woDiyaBsLeMJKNoK+PrqjGx++rqskLQfhkK9vmcKptWO5GITzQdIgFU/SkqeEqiM351mHaMesC3mmB+2LjE9CmPjXI6n+Bby0x6VNmDUJDw09usTHtGSH1cDjdVOO6P95JaDFB1ioizlVzNhd39jwk/n7nOqNbE+FXw4SF9P3wGy9fGXIZ3YkYMy6upZgp3uNw55sZxYAjYr4OIFU0BotsgF4cKEzHQ5p4P44GQOxBbjhbEdGhF0Bh4vrd6JmKAItiM9PRePoJh2uz1ysug1QkVj8rRoa9l6vX8lx6EWpb2WJacMT/vH8ds7jLymWsSnDtbFXydfJQ3OEwSOFmAJo/3tZRfjqalGq5+vboKF8PxgVPvXmk/K3ZY=; SRT5=1740883552; JSESSIONID=3BE07D8B17C72F51D8F0CB8F37C5D39C; BUC=u6ue_uwHMuou27LYmRXfUTDCgkzxNck0pxj8Kpn6T7s=",
        'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        # 'userId': user_id
    }

    headers = {'x-cafe-product': 'pc', 'Cookie': 'NM_srt_chzzk=1; PM_CK_loc=290e49fae29e5c027ce9fd02a78e28e5a08029d311a79232d5f52710aa5854de; NID_JKL=h7gl8MvXIGB8lqk7BIS/B9AjcB1q01XqqyE/dEZ6djA=; BUC=HHzGtBNxIF96BxiylLVAb1kELzImZVRL2kaPbzAMScw=; nid_inf=2008091554; SRT30=1740883756; NNB=CUGDJUZMY7BWO; SRT5=1740883756; NID_SES=AAABp+8eBMwMrg72W+XaZlxmp0VHMh+7vAxNpqWoAUjfbnwcJYcGb96Qy/QimDqABjogi/kk3vwQqpfShi6z16+98SIOJsDCYR11QUEV2ckHZvNQzz6OCBUv+DEz+LqJGReo2ps5hE5yV0fau3P3592ulANF5IsZ3xZFJVahocmxAYvzefRz+/wuYCQjOrk3OPSMPsUH+ORNKBCKI7eid/vS2dARBcUiLXHWq8vtPl4PRHLOsUPsLnzwg+jVlT0QDbcnhqXR/uBin4pHjArkffgauPEjP77zbeqSL1U2JD5Bhn9+mwPSUBPjuj+7n1ygj46rvGykvK5ZAXQ8jwoVdUqKGMM5ZWHIIc2Xb5+nCBqZE4oCvQ7O1J4GrHxvQbXh9AUoBrFWzye/OJbLS3WyeIdmL+Tk9FCGi1H1398icxf1Mptwg5PrlChfvYsr+1/kifoZohWSnif0QnFsbTaeKAXItPpn43tY06SYX4mk+hVaE8nFMOWBCMiQJeyNh5Y1XkVQ49ChMXCZHU/Bwx1ZYDU1wH5+1ZDiURUqsAcAN6KbObI3M/XlfzbEKrJR6C4YyV1Lbw==; NID_AUT=YPlx5R6SJO4PIaMTJMmJx2zTQtfM5Gmt6zsw5RPPpssX6E2rGGhonQDzGv4lh9GW; NACT=1; NAC=1C3LBggkw9A7;', 'Referer': 'https://cafe.naver.com/', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36', 'content-type': 'application/json', 'origin': 'https://cafe.naver.com', 'referer': 'https://cafe.naver.com', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
    
    cafe_api = CafeAPI(headers)
    #cafe_api.test_nickname("31203823")
    print(cafe_api.get_nickname("31203823"))

