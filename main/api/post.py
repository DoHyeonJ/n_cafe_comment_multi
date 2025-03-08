from bs4 import BeautifulSoup
from main.api.utils import handle_response, encode_params
from main.api.image import ImageAPI
import json
import uuid
import requests
import string
import random
import os
from PIL import Image, ImageEnhance, ImageOps
import colorsys
import tempfile

class PostAPI:
    def __init__(self, headers):
        # 헤더 타입 검사 및 변환
        validated_headers = {}
        for key, value in headers.items():
            # 내부 사용 필드는 제외
            if key.startswith('_'):
                continue
                
            # 값이 문자열이나 바이트가 아닌 경우 문자열로 변환
            if not isinstance(value, (str, bytes)):
                validated_headers[key] = str(value)
            else:
                validated_headers[key] = value
                
        self.headers = validated_headers
        self.session_key = None
        self.jwt_token = None
        
    def get_jwt_token(self, cafe_id):
        """JWT 토큰 얻기"""
        url = f"https://apis.naver.com/cafe-web/cafe-editor-api/v2/cafes/{cafe_id}/editor"
        params = {
            'experienceMode': 'true',
            'from': 'pc'
        }        
        
        response = requests.get(url, headers=self.headers, params=params)


        if response.status_code == 200:
            data = response.json()
            self.jwt_token = data.get('result', {}).get('token')

            if self.jwt_token:
                self.headers['se-authorization'] = self.jwt_token
            return self.jwt_token
        return None
        
    def get_session_key(self):
        """세션키 얻기"""
        # if not self.jwt_token:
        #     raise Exception("JWT 토큰이 필요합니다. get_jwt_token()을 먼저 호출하세요.")
            
        url = "https://platform.editor.naver.com/api/cafepc001/v1/photo-uploader/session-key"
        response = requests.get(url, headers=self.headers)
   
        if response.status_code == 200:
            data = response.json()
            self.session_key = data.get('sessionKey')
            return self.session_key
        return None
        
    def write_post(self, cafe_id, board_id, title, content, images=None, options=None):
        """게시글 작성"""
        new_headers = self.headers.copy()
        new_headers['se-authorization'] = self.jwt_token
        new_headers['content-type'] = 'application/json'
            
        url = f'https://apis.naver.com/cafe-web/cafe-editor-api/v2/cafes/{cafe_id}/menus/{board_id}/articles'
        
        content_json = self._generate_article_content(content, images)
        
        data = {
            "article": {
                "cafeId": cafe_id,
                "menuId": board_id,
                "subject": title,
                "contentJson": content_json,
                "tagList": [],
                "from": "pc",
                "open": True,
                "enableComment": True,
                "enableScrap": True,
                "enableCopy": True,
                "useAutoSource": True,
                "editorVersion": 4,
                "parentId": 0
            }
        }
        
        if options:
            data["article"].update(options)
            
        response = requests.post(url, headers=new_headers, json=data)
        
        # 응답 처리
        result = handle_response(response)
        
        # 카페 이름 추가 (URL 형식 개선)
        if result and 'success' in result and result['success'] and 'article_url' in result:
            # 카페 이름이 URL에 포함되도록 수정
            cafe_name = None
            if 'referer' in self.headers:
                referer = self.headers['referer']
                if 'cafe.naver.com/' in referer:
                    cafe_name_part = referer.split('cafe.naver.com/')[1].split('/')[0].split('?')[0]
                    if cafe_name_part and cafe_name_part != 'ArticleRead.nhn':
                        cafe_name = cafe_name_part
            
            # 카페 이름이 있으면 URL 형식 변경
            if cafe_name:
                article_id = result['article_id']
                result['article_url'] = f"https://cafe.naver.com/{cafe_name}/{article_id}"
        
        return result

    def _generate_article_content(self, text_content, images=None):
        """게시글 컨텐츠 JSON 생성"""
        def generate_random_string(length):
            characters = string.ascii_uppercase + string.digits
            return ''.join(random.choices(characters, k=length))

        def generate_se_uuid():
            return "SE-" + str(uuid.uuid4())

        content = {
            "document": {
                "version": "2.8.0",
                "theme": "default",
                "language": "ko-KR",
                "id": generate_random_string(26),
                "components": [],
                "di": {
                    "dif": False,
                    "dio": [{"dis": "N", "dia": {"t": 0, "p": 0, "st": 1, "sk": 0}}]
                }
            },
            "documentId": ""
        }

        # 텍스트를 단락으로 분리
        blocks = text_content.split('\n\n')
        current_image = 0  # 현재 이미지 인덱스
        
        # 첫 번째 이미지는 맨 위에 배치
        if images and len(images) > 0:
            image = images[current_image]
            image_component = {
                "id": generate_se_uuid(),
                "layout": "default",
                "src": image['src'],
                "internalResource": True,
                "represent": True,  # 첫 번째 이미지는 대표 이미지
                "path": image['url'],
                "domain": "https://cafeptthumb-phinf.pstatic.net",
                "fileSize": image['fileSize'],
                "width": image['width'],
                "height": image['height'],
                "originalWidth": image['width'],
                "originalHeight": image['height'],
                "fileName": image['fileName'],
                "caption": None,
                "format": "normal",
                "displayFormat": "normal",
                "imageLoaded": True,
                "contentMode": "normal",
                "origin": {
                    "srcFrom": "local",
                    "@ctype": "imageOrigin"
                },
                "@ctype": "image"
            }
            content["document"]["components"].append(image_component)
            current_image += 1

        # 본문 텍스트와 나머지 이미지들을 적절히 배치
        for block in blocks:
            if block.strip():
                # 텍스트 블록 추가
                paragraphs = []
                lines = block.split('\n')
                for line in lines:
                    if line.strip():
                        paragraphs.append({
                            "id": generate_se_uuid(),
                            "nodes": [{
                                "id": generate_se_uuid(),
                                "value": line.strip(),
                                "@ctype": "textNode"
                            }],
                            "@ctype": "paragraph"
                        })
                
                if paragraphs:
                    text_component = {
                        "id": generate_se_uuid(),
                        "layout": "default",
                        "value": paragraphs,
                        "@ctype": "text"
                    }
                    content["document"]["components"].append(text_component)

                # 남은 이미지가 있으면 랜덤하게 삽입 (약 30% 확률)
                if images and current_image < len(images) and random.random() < 0.3:
                    image = images[current_image]
                    image_component = {
                        "id": generate_se_uuid(),
                        "layout": "default",
                        "src": image['src'],
                        "internalResource": True,
                        "represent": False,
                        "path": image['url'],
                        "domain": "https://cafeptthumb-phinf.pstatic.net",
                        "fileSize": image['fileSize'],
                        "width": image['width'],
                        "height": image['height'],
                        "originalWidth": image['width'],
                        "originalHeight": image['height'],
                        "fileName": image['fileName'],
                        "caption": None,
                        "format": "normal",
                        "displayFormat": "normal",
                        "imageLoaded": True,
                        "contentMode": "normal",
                        "origin": {
                            "srcFrom": "local",
                            "@ctype": "imageOrigin"
                        },
                        "@ctype": "image"
                    }
                    content["document"]["components"].append(image_component)
                    current_image += 1

        # 남은 이미지들을 마지막에 추가
        while images and current_image < len(images):
            image = images[current_image]
            image_component = {
                "id": generate_se_uuid(),
                "layout": "default",
                "src": image['src'],
                "internalResource": True,
                "represent": False,
                "path": image['url'],
                "domain": "https://cafeptthumb-phinf.pstatic.net",
                "fileSize": image['fileSize'],
                "width": image['width'],
                "height": image['height'],
                "originalWidth": image['width'],
                "originalHeight": image['height'],
                "fileName": image['fileName'],
                "caption": None,
                "format": "normal",
                "displayFormat": "normal",
                "imageLoaded": True,
                "contentMode": "normal",
                "origin": {
                    "srcFrom": "local",
                    "@ctype": "imageOrigin"
                },
                "@ctype": "image"
            }
            content["document"]["components"].append(image_component)
            current_image += 1

        return json.dumps(content, ensure_ascii=False)
        
    def upload_image(self, cafe_id, image_path):
        """이미지 업로드"""
        # JWT 토큰 항상 새로 발급
        self.get_jwt_token(cafe_id)

        if not self.session_key:
            self.session_key = self.get_session_key()
            if not self.session_key:
                raise Exception("세션키를 얻지 못했습니다.")
                
        image_api = ImageAPI(self.headers)
        return image_api.upload(cafe_id, image_path, self.session_key)
        
    def get_post(self, cafe_id, post_id):
        """게시글 조회"""
        url = f'https://cafe.naver.com/ArticleRead.nhn'
        params = {
            'clubid': cafe_id,
            'articleid': post_id
        }
        response = requests.get(url, headers=self.headers, params=params)
        return handle_response(response)
        
    def process_image(self, image_path):
        """이미지 처리: 크기 조정, 채도/명도 조정, 테두리 추가"""
        try:
            # 이미지 열기
            with Image.open(image_path) as img:
                # RGBA -> RGB 변환 (필요한 경우)
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                # 400x400 크기로 리사이즈 (비율 유지)
                img.thumbnail((400, 400), Image.Resampling.LANCZOS)
                
                # 흰색 배경의 400x400 이미지 생성
                background = Image.new('RGB', (400, 400), 'white')
                # 중앙 정렬하여 붙여넣기
                offset = ((400 - img.width) // 2, (400 - img.height) // 2)
                background.paste(img, offset)
                img = background
                
                # 채도와 명도 랜덤 조정 (0.8 ~ 1.2)
                saturation = ImageEnhance.Color(img)
                img = saturation.enhance(random.uniform(0.8, 1.2))
                
                brightness = ImageEnhance.Brightness(img)
                img = brightness.enhance(random.uniform(0.8, 1.2))
                
                # 랜덤 색상의 테두리 추가
                hue = random.random()  # 0~1 사이의 랜덤 색상
                border_color = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(hue, 0.7, 0.9))
                border_size = 2
                img = ImageOps.expand(img, border=border_size, fill=border_color)
                
                # 임시 파일로 저장
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                    img.save(tmp.name, 'JPEG', quality=95)
                    return tmp.name
                    
        except Exception as e:
            print(f"이미지 처리 중 오류 발생: {str(e)}")
            return None

    def test_post(self, cafe_id, board_id):
        """테스트용 게시글 작성"""
        try:
            # JWT 토큰 얻기
            if not self.jwt_token:
                self.jwt_token = self.get_jwt_token(cafe_id)
                if not self.jwt_token:
                    print("JWT 토큰 획득 실패")
                    return False
            print(f"JWT 토큰 획득 성공: {self.jwt_token}")
            
            # 세션키 얻기
            if not self.session_key:
                self.session_key = self.get_session_key()
                if not self.session_key:
                    print("세션키 획득 실패")
                    return False
            print(f"세션키 획득 성공: {self.session_key}")
            
            # 이미지 폴더에서 랜덤하게 2~3개 이미지 선택
            image_dir = os.path.join('imgs', 'jdh7693')
            if not os.path.exists(image_dir):
                print(f"이미지 디렉토리가 존재하지 않습니다: {image_dir}")
                return False
                
            image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if not image_files:
                print("사용 가능한 이미지가 없습니다.")
                return False
                
            # 2~3개 랜덤 선택
            num_images = random.randint(2, 3)
            selected_images = random.sample(image_files, min(num_images, len(image_files)))
            
            # 선택된 이미지 처리 및 업로드
            uploaded_images = []
            temp_files = []  # 임시 파일 추적을 위한 리스트
            
            try:
                for img_file in selected_images:
                    original_path = os.path.join(image_dir, img_file)
                    # 이미지 처리 및 임시 파일 생성
                    processed_path = self.process_image(original_path)
                    if processed_path:
                        temp_files.append(processed_path)
                        # 처리된 이미지 업로드
                        image_result = self.upload_image(cafe_id, processed_path)
                        print(image_result)
                        if image_result:
                            uploaded_images.append(image_result)
                            print(f"이미지 업로드 성공: {image_result['fileName']}")
                        else:
                            print(f"이미지 업로드 실패: {img_file}")
                    
                if not uploaded_images:
                    print("모든 이미지 업로드 실패")
                    return False
                    
                # 테스트 게시글 작성
                title = "테스트 게시글입니다"
                content = """
                테스트 게시글 내용입니다.
                
                이미지들이 자동으로 배치됩니다.
                
                감사합니다.
                """
                
                result = self.write_post(
                    cafe_id=cafe_id,
                    board_id=board_id,
                    title=title,
                    content=content,
                    images=uploaded_images
                )
                
                if result:
                    print("게시글 작성 성공!")
                    print(f"게시글 URL: {result['article_url']}")
                    return True
                else:
                    print("게시글 작성 실패")
                    return False
                    
            finally:
                # 임시 파일 정리
                for temp_file in temp_files:
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
                        
        except Exception as e:
            print(f"테스트 중 오류 발생: {str(e)}")
            return False

if __name__ == "__main__":
    headers = {'x-cafe-product': 'pc', 'Cookie': 'NNB=2QP3YT6BPGMWI; ASID=31a8f9cc0000018978da1f5400000064; ncvid=#vid#_115.138.87.199IWS1; ba.uuid=a76ad3c1-5903-42bd-8399-3eb89840598c; tooltipDisplayed=true; _ga_6Z6DP60WFK=GS1.2.1726462403.1.0.1726462403.60.0.0; NFS=2; _ga=GA1.1.877073880.1704979036; _ga_EFBDNNF91G=GS1.1.1732339996.1.0.1732339999.0.0.0; _ga_8P4PY65YZ2=GS1.1.1734265772.1.1.1734265776.56.0.0; nstore_session=uajHtGrn2P2hNissMDvcn+a3; nstore_pagesession=iI4S7lqW4vuF/ssL/6s-089597; NAC=bt7NBgQZgVqM; jdh7693__storageID=e3e49b48-fddc-0668-a833-1a85161010b2; ncu=8bb05b2d3f7a1fdefb3d7a7b80681e2cd8; NACT=1; SRT30=1740880008; nid_inf=2008104164; NID_AUT=yx/rL+3DVICGF6iUGkEWzTYvy51RIcSdPLB0PSyjWtTtdX8uDEAeH9aJnoRAH3fq; NID_JKL=PqLukHQIo1uRZ7v00pbFXTCw5SK2YdU5xqof6m8PJVs=; rankingHidden=31203823; nci4=0e39ddf6e6a7c27129c780979a650a60d8957b88dd984f9c46a4a9bb492ece01cd5b933efdbd44021bea9be157d572ba71597e30dbed88d2ee0d8d6190ae1bfdb283cebfb691b485bab5b89fbf8cdca9a58da899d1a1ac8b92a3ef9894b398ae9f9382a580b1faf9f8fff5f3f2f682f2d6f1c785ea878782ec819cf18299f0; ncmc4=6651b59e8ecfaa1941afe8fff2007401fead5cb492c80ff438dbff27b8bd6e8056b844a5512abb97980a7f870fa960d04b294f13b7c0ea86ff71980b82fa7db3fcdbe8d9d0dffadde2ad99; JSESSIONID=083F77D0E07DE8E17E2E43A8064A5B71; page_uid=i8nftsqosesssPm9iMRssssssy0-026668; NID_SES=AAABkqr3tHYMJyy/T0+tLyYzcR3a6nxAUdKKg3B00TZWNcBioVGl6tlGo351oNHIn5y4/Yl6pzfMVGHJ1vPBlPgN5ypdffmhEa5lXcaI+qKNlXBcAKTiEmj5KowZoCEFsIOHotqlMAbLxAINPe3EbxN4bZ/k02uZXS8KFsVjcLhZfPivqwO3981Y4299pM7oe5wvq6i3t93zwL2sML/DMVpctAGL2SQJh1iUxrYTH4rWTEVH2ozWzmdaOZByjMMgQhw3/GhZFSZlh8w9Bo4+CYc7iLbLkGlqscHe3oB3a1l6y7ROFNIQLfM19/f6YCSqym5g4LTH9dNRsfoPrqj7H2ix2Zt0WD/890H+1infpTrXtYyFij9+IxU+aIn2m9SXej7Ep1XnE4nx3WQLVfd0/O36V9JW0SievIs5DDKK7cL7p0yN5Nuu0pfsHIBNSt+1dGsGUzI9xu0YE1XF3C138/2goGxXF957iWUMA5p+ux5ekx02kE8NPpiWsVxry55ibVuyFONQU0w4jTRUWJdMOUC5JxmQIohRs8wcwCechSQcC4Ta; BUC=NEX2DyG-J63bThVWcrAD-9DIfNvjzdGPgZwc-GiX6d4=', 'Referer': 'https://cafe.naver.com/', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36', 'content-type': 'application/json', 'origin': 'https://cafe.naver.com', 'referer': 'https://cafe.naver.com', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
    
    post_api = PostAPI(headers)
    print(post_api.get_jwt_token('31203823'))
    print(post_api.get_session_key())

