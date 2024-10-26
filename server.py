from flask import Flask, request
from flask_cors import CORS
import os
from util.clear import clear
from manga_ocr import MangaOcr
import threading
import configparser
from jinja2 import Environment, FileSystemLoader
import subprocess
app = Flask(__name__)
file_path = './input/input.jpg'
env = Environment(loader=FileSystemLoader('templates'))
def parse_img():
    # todo: 这样每次解析都要重新加载模型，实在是下下策
    command = 'cd comic-text-detector && python inference.py'
    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, text=True)
    picture_num = int(result.stdout.replace('\n',''))
    with open('./output/output.txt', 'w', encoding='utf-8') as f:
        for i in range(picture_num):
            image_path = f'./output/cut_image_{i}.png'
            if not os.path.exists(image_path):
                continue
            infer_text = mocr(image_path)
            if len(infer_text) == 1:
                continue
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
    with open('./output/output.txt', 'r', encoding='utf-8') as f:
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