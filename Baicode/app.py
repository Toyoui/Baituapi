import os
import re
import urllib
import json
import socket
import urllib.request
import urllib.parse
import urllib.error
# 设置超时
import time
import requests
from flask import Flask, redirect, request, url_for, send_file
from werkzeug.security import safe_join

timeout = 5
socket.setdefaulttimeout(timeout)


class Crawler:
    # 睡眠时长
    __time_sleep = 0.15
    __amount = 0
    __start_amount = 0
    __counter = 0
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0', 'Cookie': ''}
    __per_page = 3

    # 获取图片url内容等
    # t 下载图片时间间隔
    def __init__(self, t=0.1):
        self.time_sleep = t

    # 获取后缀名
    @staticmethod
    def get_suffix(name):
        m = re.search(r'\.[^\.]*$', name)
        if m.group(0) and len(m.group(0)) <= 5:
            return m.group(0)
        else:
            return '.jpeg'

    @staticmethod
    def handle_baidu_cookie(original_cookie, cookies):
        """
        :param string original_cookie:
        :param list cookies:
        :return string:
        """
        if not cookies:
            return original_cookie
        result = original_cookie
        for cookie in cookies:
            result += cookie.split(';')[0] + ';'
        result.rstrip(';')
        return result

    # 开始获取
    def get_images(self, word):
        search = urllib.parse.quote(word)
        # pn int 图片数
        pn = self.__start_amount
        image_urls = []  # 存储图片的URL
        while pn < self.__amount:
            url = 'https://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ct=201326592&is=&fp=result&queryWord=%s&cl=2&lm=-1&ie=utf-8&oe=utf-8&adpicid=&st=-1&z=&ic=&hd=&latest=&copyright=&word=%s&s=&se=&tab=&width=&height=&face=0&istype=2&qc=&nc=1&fr=&expermode=&force=&pn=%s&rn=%d&gsm=1e&1594447993172=' % (
                search, search, str(pn), self.__per_page)
            # 设置header防403
            try:
                time.sleep(self.time_sleep)
                req = urllib.request.Request(url=url, headers=self.headers)
                page = urllib.request.urlopen(req)
                self.headers['Cookie'] = self.handle_baidu_cookie(self.headers['Cookie'],
                                                                  page.info().get_all('Set-Cookie'))
                rsp = page.read()
                page.close()
            except UnicodeDecodeError as e:
                print(e)
                print('-----UnicodeDecodeErrorurl:', url)
            except urllib.error.URLError as e:
                print(e)
                print("-----urlErrorurl:", url)
            except socket.timeout as e:
                print(e)
                print("-----socket timout:", url)
            else:
                # 解析json
                rsp_data = json.loads(rsp, strict=False)
                if 'data' not in rsp_data:
                    continue
                else:
                    for image_info in rsp_data['data']:
                        if 'replaceUrl' not in image_info or len(image_info['replaceUrl']) < 1:
                            continue
                        obj_url = image_info['replaceUrl'][0]['ObjUrl']
                        thumb_url = image_info['thumbURL']
                        url = 'https://image.baidu.com/search/down?tn=download&ipn=dwnl&word=download&ie=utf8&fr=result&url=%s&thumburl=%s' % (
                            urllib.parse.quote(obj_url), urllib.parse.quote(thumb_url))
                        image_urls.append(url)
                    pn += self.__per_page
        return image_urls

    def start(self, word):
        self.__per_page = 3
        self.__start_amount = 0
        self.__amount = self.__per_page
        return self.get_images(word)


app = Flask(__name__)
app.static_folder = 'static'  # 设置静态资源目录为 'static'

# 启用调试模式
app.debug = True

@app.route("/")
def index():
    word = request.args.get('word')
    if word:
        image_filename = word + '.jpg'
        image_path = os.path.join('static', 'images', image_filename)
        if os.path.exists(image_path):
            image_path = safe_join('static/images', image_filename)
            return send_file(image_path)
        else:
            crawler = Crawler(0.1)  # 抓取延迟为 0.1
            image_urls = crawler.start(word)
            print(image_urls)
            if image_urls:
                download_image(image_urls[2], word)
                image_path = safe_join('static/images', image_filename)
                return send_file(image_path)
    return "No image found"


def download_image(image_url, word):
    word = sanitize_filename(word)  # 使用合法字符生成文件名
    response = requests.get(image_url)
    if response.status_code == 200:
        file_extension = '.jpg'  # 如果无法获取后缀，则默认为.jpg
        image_file = f"{word}{file_extension}"
        save_path = os.path.join(app.static_folder, 'images', image_file)
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return save_path
    return None


def sanitize_filename(filename):
    # 替换非法字符为合法字符，例如将中文字符替换为英文字符
    pattern = re.compile(r'[\\/:"*?<>|]')
    return re.sub(pattern, '_', filename)


if __name__ == '__main__':
    app.run(port=56789)
