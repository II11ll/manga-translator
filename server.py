from flask import Flask, request
from flask_cors import CORS
import os
from extract_text import extract_text
from util.clear import clear
from manga_ocr import MangaOcr
import threading
import configparser
from jinja2 import Environment, FileSystemLoader
app = Flask(__name__)
file_path = './temp/input.jpg'
env = Environment(loader=FileSystemLoader('templates'))
def parse_img():
    picture_num = extract_text(file_path, True)
    with open('./temp/output.txt', 'w', encoding='utf-8') as f:
        for i in range(picture_num):
            infer_text = mocr(f'./temp/{i}.jpg')
            f.write(infer_text+'\n')
            f.write('请分析此日语句子的语法并为汉字标注假名：' + infer_text + '\n')
@app.route('/upload', methods=['POST'])
def upload_file():
    clear()
    # 检查是否有文件在请求中
    if 'file' not in request.files:
        return '没有文件部分', 400
    file = request.files['file']
    # 如果用户没有选择文件，浏览器也会提交一个没有文件名的空部分
    if file.filename == '':
        return '没有选择文件', 400
    if file:
        file.save(file_path)
        # 时间太长，开个线程
        thread = threading.Thread(target=parse_img)
        thread.start()
        return '上传成功', 200
@app.route('/getOutput', methods=['GET'])
def getOutput():
    with open('./temp/output.txt', 'r', encoding='utf-8') as f:
        env.filters['replacenewline'] = lambda s: s.replace('\n','')
        template = env.get_template('output.html')
        return template.render(items = f.readlines())
@app.route('/upload', methods=['GET'])
def uploadPage():
    config = configparser.ConfigParser()
    config.read('config.ini')
    ip = config['url']['server_url']
    template = env.get_template('upload.html')
    return template.render(url=ip+'/upload')
# @app.route('/infer', methods=['POST'])
# def infer():
#     i = request.values.get('i')
#     text = mocr(f'./temp/{i}.jpg')
#     return text, 200
mocr = MangaOcr()
CORS(app)
app.run(host='0.0.0.0', debug=True)