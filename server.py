from flask import Flask, request
from flask_cors import CORS
import os
from extract_text import extract_text
from util.clear import clear
from manga_ocr import MangaOcr
app = Flask(__name__)

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
        file.save('./temp/input.jpg')
        picture_num = extract_text()
        infer_text = infer(picture_num)
        return infer_text, 200
@app.route('/infer', methods=['POST'])
def infer():
    i = request.values.get('i')
    text = mocr(f'./temp/{i}.jpg')
    return text, 200
mocr = MangaOcr()
CORS(app)
app.run(debug=True)