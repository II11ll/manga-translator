from flask import Flask, request, send_from_directory, url_for
from flask_cors import CORS
import os
import shutil
from manga_ocr import MangaOcr
import threading
import configparser
from jinja2 import Environment, FileSystemLoader
import time
import sys
sys.path.append('detector')
from detector import inference, init
import cv2
import re
from sqlalchemy import create_engine, exists
from model.gallery import Gallery
from sqlalchemy.orm import sessionmaker
import hashlib
app = Flask(__name__)
app.config['OUTPUT_FOLDER'] = 'output'
env = Environment(loader=FileSystemLoader('templates'))
current_directory = os.path.dirname(os.path.abspath(__file__))
engine = create_engine(f'sqlite:////{current_directory}/store/saved.db')
Session = sessionmaker(bind=engine)
web_debug = False #仅调试网页，不加载模型
def clear(clearStash = False):
    current_directorys = ["./input","./output"]
    if clearStash:
        current_directorys.append("./stash")
    for current_directory in current_directorys:
        files = os.listdir(current_directory)
        for file in files:
            os.remove(os.path.join(current_directory, file))
def parse_img(args_param_lst):
    # detector中是读取文件夹，然后推理文件夹里的所有图片
    # 所以要上传多图逐个识别要先存到stash，在一个个复制到input文件夹中...
    for args_param in args_param_lst:
        clear()
        folder_name = args_param['filename']
        shutil.copy(f'./stash/{folder_name}', './input')
        if folder_name.index('.') != -1:
            folder_name = folder_name.split('.')[0]

        picture_num = inference(detector_model)
        
        with open(f'{current_directory}/output/output.txt', 'w', encoding='utf-8') as f:
            infer_text_lst = []
            for i in range(picture_num):
                image_path = f'./output/cut_image_{i}.png'
                if not os.path.exists(image_path):
                    continue
                infer_text_lst.append(mocr(image_path))
            copy_lst = infer_text_lst.copy()
            for text in infer_text_lst:
                for compare_text in infer_text_lst:
                    if text == compare_text:
                        continue
                    if text in compare_text and len(compare_text) > len(text):
                        copy_lst.remove(text)
                        break
            for infer_text in copy_lst:
                if len(infer_text) <= 1:
                    continue
                f.write(infer_text+'\n')
                f.write('请分析此日语句子的语法并为汉字标注假名并翻译句子：' + infer_text + '\n')
        generate_thumbnail(args_param['filename'])
        # 复制output到store 
        source_folder = f'{current_directory}/output'
        destination_folder = f'{current_directory}/store/{folder_name}'
        os.makedirs(destination_folder)
        shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)
        session = Session()
        session.add(Gallery(
            folder_name = folder_name,
            img_num = picture_num-1,
            create_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            author_name = args_param['authorname'],
            source_url = args_param['sourceurl'],
            pic_md = args_param['md5']
        ))
        session.commit()
        session.close()
        
        

def generate_thumbnail(filename):
    # 读取图片
    img = cv2.imread('./input/'+filename)

    # 设置缩放比例
    scale_percent = 20  # 表示缩放20%

    # 计算新的尺寸
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)

    # 进行缩放
    resized = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)

    # 保存缩略图
    cv2.imwrite('./output/'+'thumbnail.jpg', resized)
def find_url(string): 
    # https://stackoverflow.com/questions/520031/whats-the-cleanest-way-to-extract-urls-from-a-string-using-python/44936558#44936558?newreg=a1ad42438aea44d08f387154dbb6891d
    # todo 匹配url，实在找不到更好的方法了...
    WEB_URL_REGEX = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""
    return re.findall(WEB_URL_REGEX, string)[0]
def generate_md5(file_path):
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:  # 以二进制读模式打开文件
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
        return None
    except IOError as e:
        print(f"An error occurred while reading the file {file_path}: {e}")
        return None
def check_file_exist(filename):
    md5_value = generate_md5('./stash/'+filename)
    session = Session()
    return session.query(exists().where(Gallery.pic_md == md5_value)).scalar()
@app.route('/upload', methods=['POST'])
def upload_file():
    clear(True)
    # 检查是否有文件在请求中
    if 'file' not in request.files:
        return '没有文件部分', 400
    files = request.files.getlist('file')
    if len(files) == 0:
        return '没有选择文件', 400
    args_param_lst = []
    files = sorted(files, key=lambda x: x.filename)
    for file in files:
        args_param = {}
        if not request.form.get('filename') and len(request.form.get('filename')) > 0:
            args_param['filename'] = request.form.get('filename') + '.jpg'
        else:
            args_param['filename'] = file.filename
        args_param['authorname'] = request.form.get('authorname', '')
        args_param['sourceurl'] = request.form.get('sourceurl', '')
        if len(args_param['sourceurl']) > 0:
            args_param['sourceurl'] = find_url(args_param['sourceurl'] )
        file.save('./stash/'+args_param['filename'])
        if check_file_exist(args_param['filename']):
            return '上传图片已存在', 409
        args_param['md5'] = generate_md5('./stash/'+args_param['filename'])
        if os.path.isdir('./store'+args_param['filename'].split('.')[0]):
            return '上传文件夹名冲突', 409
        args_param_lst.append(args_param)
    # 时间太长，开个线程
    if not web_debug:
        thread = threading.Thread(target=parse_img, args=(args_param_lst,))
        thread.start()
    return '上传成功', 200
@app.route('/getOutput', methods=['GET'])
def getOutput():
    folder = request.args.get('folder', default=None, type=str)
    if folder:
        folder = 'store/' + folder
    else:
        folder = 'output'
    with open(f'./{folder}/output.txt', 'r', encoding='utf-8') as f:
        #env.filters['replacenewline'] = lambda s: s.replace('\n','')
        template = env.get_template('output.html')
        output = []
        dic = {}
        for index, line in enumerate(f.readlines()):
            if index % 2 == 0:
                dic = {}
                dic['index'] = index // 2
                dic['original'] = line.replace('\n','')
            else:
                dic['prompt'] = line.replace('\n','')
                output.append(dic)
        return template.render(output = output, folder = folder)
@app.route('/upload', methods=['GET'])
def uploadPage():
    config = configparser.ConfigParser()
    config.read('config.ini')
    ip = config['url']['server_url']
    template = env.get_template('upload.html')
    return template.render(url=ip+'/upload')
@app.route('/gallery', methods=['GET'])
def galleryPage():
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('pageSize', default=10, type=int)
    offset = (page - 1) * page_size
    session = Session()
    images_column = session.query(Gallery).limit(page_size).offset(offset).all()
    images_data = [i.__dict__ for i in images_column]
    total_items = session.query(Gallery).count()
    total_pages = (total_items + page_size - 1) // page_size
    session.close()
    template = env.get_template('gallery.html')
    return template.render(images_data = images_data, total_pages = total_pages, page = page, url_for = url_for)
@app.route('/output/<filename>')
def uploaded_file(filename):
    return send_from_directory('output', filename)
@app.route('/store/<path:filename>')
def gallery_file(filename):
    # todo : filename中含有..时会越权访问
    return send_from_directory('store', filename)
if not web_debug:
    mocr = MangaOcr()
    detector_model = init()
CORS(app)
if web_debug:
    app.run(host='0.0.0.0', debug=True, use_reloader=True)
else:
    app.run(host='0.0.0.0', debug=False, use_reloader=False)