from flask import Flask, request, send_from_directory, url_for, redirect, jsonify
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
from sqlalchemy import create_engine
from model.gallery import Gallery
from model.block import Block
from sqlalchemy.orm import sessionmaker, class_mapper
import hashlib
import json
from PIL import Image
import subprocess
app = Flask(__name__)
app.config['OUTPUT_FOLDER'] = 'output'
env = Environment(loader=FileSystemLoader('templates'))
current_directory = os.path.dirname(os.path.abspath(__file__))
engine = create_engine(f'sqlite:////{current_directory}/store/saved.db')
Session = sessionmaker(bind=engine)
web_debug = False #仅调试网页，不加载模型
allowed_ip = []
with open(f'{current_directory}/store/password.txt') as f:
    ip_password = f.readline().strip()
def limit_ip_address(func):
    def wrapper(*args, **kwargs):
        if request.remote_addr not in allowed_ip and not web_debug:
            return 'Forbidden', 403  
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper
def clear(clearStash = False):
    current_directorys = ["./input","./output"]
    if clearStash:
        current_directorys.append("./stash")
    for current_directory in current_directorys:
        files = os.listdir(current_directory)
        for file in files:
            os.remove(os.path.join(current_directory, file))
def upload_to_bypy(folder_name):
    subprocess.run(['bypy','syncup', f'{current_directory}/store/{folder_name}', f'bypy/store/{folder_name}'])
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
        
        infer_text_lst = []
        for i in range(picture_num):
            image_path = f'./output/cut_image_{i}.png'
            if not os.path.exists(image_path):
                continue
            infer_text = mocr(image_path)
            if infer_text is None or len(infer_text) == 0:
                infer_text_lst.append('识别字符为空')
            else:
                infer_text_lst.append(infer_text)
        
        destination_folder = f'{current_directory}/store/{folder_name}'
        if os.path.exists(destination_folder):
            subprocess.run(['rm','-rf',destination_folder])
            session = Session()
            gallery = session.query(Gallery).filter(Gallery.folder_name==folder_name).one_or_none()
            if gallery:
                for block in gallery.blocks:
                    session.delete(block)
                session.delete(gallery)
            session.commit()
            session.close()
        source_folder = f'{current_directory}/output'
        generate_thumbnail(args_param['filename'])
        os.makedirs(destination_folder)
        shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)

        
        session = Session()
        with open(f'{current_directory}/store/{folder_name}/{folder_name}.json', 'r', encoding = 'utf-8') as f,\
            open(f'{current_directory}/store/{folder_name}/line-{folder_name}.txt', 'r', encoding = 'utf-8') as f2,\
            Image.open(f'{current_directory}/store/{folder_name}/{folder_name}.png') as img:
            width, height = img.size
            gallery = Gallery(
                folder_name = folder_name,
                img_num = picture_num-1,
                create_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                author_name = args_param['authorname'],
                source_url = args_param['sourceurl'],
                pic_md = args_param['md5'],
                location_json = json.load(f),
                line_txt = ''.join(f2.readlines()),
                width = width,
                height = height
            )
            session.add(gallery)
            session.flush()
            for index, infer_text in enumerate(infer_text_lst):
                add_block = Block(
                    gallery = gallery,
                    index = index,
                    original = infer_text.replace('\n','')
                )
                session.add(add_block)
            session.commit()
            session.close()
        # 删除多余文件
        white_list = ['thumbnail.jpg', 'labeled.png',f'{folder_name}.png']
        for file in os.listdir(f'{current_directory}/store/{folder_name}'):
            if file not in white_list:
                delete_path = f'{current_directory}/store/{folder_name}/{file}'
                if os.path.exists(delete_path):
                    os.remove(delete_path)
        if not args_param['notsave']:
            # 上传至百度网盘
            thread = threading.Thread(target=upload_to_bypy, args=(folder_name,))
            thread.start()
        # 推理完休息下，防止把内存干爆...
        time.sleep(10)
        
        

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
    #return session.query(exists().where(Gallery.pic_md == md5_value)).scalar()
    return session.query(Gallery).filter_by(pic_md=md5_value).first()
@app.route('/upload', methods=['POST'])
@limit_ip_address
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
        args_param['notsave'] = 'notsave' in request.form
        if not request.form.get('filename') and len(request.form.get('filename')) > 0:
            args_param['filename'] = request.form.get('filename') + '.png'
        else:
            args_param['filename'] = file.filename
        if args_param['notsave']:
            args_param['filename'] = 'output.png' 
        
        args_param['authorname'] = request.form.get('authorname', '')
        args_param['sourceurl'] = request.form.get('sourceurl', '')
        if len(args_param['sourceurl']) > 0:
            args_param['sourceurl'] = find_url(args_param['sourceurl'] )
        file.save('./stash/'+args_param['filename'])
        # 检查文件是否存在，批量上传有一个存在就会全部return
        saved_img = check_file_exist(args_param['filename'])
        if saved_img:
            #return '上传图片已存在', 409
            return redirect(url_for('getOutput', folder=saved_img.folder_name))
        
        if args_param['filename'].find('.webp') != -1:
            with Image.open('./stash/'+args_param['filename']) as img:
                # 转换并保存为PNG
                args_param['filename'] = args_param['filename'].replace('.webp','.png')
                img.save('./stash/'+args_param['filename'], 'PNG')
        
        args_param['md5'] = generate_md5('./stash/'+args_param['filename'])
        # if os.path.isdir('./store'+args_param['filename'].split('.')[0]):
        #     return '上传文件夹名冲突', 409
        args_param_lst.append(args_param)
    # 时间太长，开个线程
    if not web_debug:
        thread = threading.Thread(target=parse_img, args=(args_param_lst,))
        thread.start()
    return '上传成功', 200
# todo 网页加载到手机浏览器会缩放，点击复制的位置是绝对布局，缩放后位置可能会不对
# 这里将img固定为355px,然后按照图片宽度缩放
# 根据宽度缩放的话可能会出现长度不对应，但因为文本框一般是竖排，偏差一点影响不大
def get_device_adjusted_coordinates(img_width, xyxy):
    scale =  355 / img_width
    return [coord * scale for coord in xyxy]
def model_to_dict(instance):
    # 使用class_mapper获取类的属性信息
    mapper = class_mapper(instance.__class__)
    # 创建一个空字典来存储结果
    dict_representation = {}
    # 遍历类的属性
    for column in mapper.columns:
        dict_representation[column.name] = getattr(instance, column.name)
    return dict_representation
@app.route('/getOutput', methods=['GET'])
@limit_ip_address
def getOutput():
    folder = request.args.get('folder', default='output', type=str)
    template = env.get_template('output.html')

    session = Session()
    gallery = session.query(Gallery).filter(Gallery.folder_name == folder).one()
    if gallery == None:
        return 'Not found', 404
    block_lst = session.query(Block).filter(Block.gallery == gallery).all()
    output = []
    areas = gallery.location_json
    for block in block_lst:
        dic = model_to_dict(block)
        dic['xyxy'] = get_device_adjusted_coordinates(
            gallery.width,
            areas[block.index]['xyxy'])
        output.append(dic)
    session.close()
    return template.render(output = output, img_name = f'store/{folder}/{folder}.png', updateURL=url_for('updateBlockInfo'))
@app.route('/updateBlockInfo', methods=['POST'])
@limit_ip_address
def updateBlockInfo():
    # 确保请求包含JSON数据
    if request.is_json:
        # 获取JSON数据
        data = request.get_json()
        session = Session()
        block = session.query(Block).filter(Block.id == data['id']).first()
        block.translation = data['translation']
        block.ai_generate = data['ai_generate']
        session.commit()
        session.close()
        
        # 可以返回一个响应，例如确认消息
        return jsonify({"message": "Data received successfully", "data": data}), 200
    else:
        # 如果请求不包含JSON数据，返回错误
        return jsonify({"error": "Request must be JSON"}), 400
    pass
@app.route('/upload', methods=['GET'])
@limit_ip_address
def uploadPage():
    config = configparser.ConfigParser()
    config.read('config.ini')
    ip = config['url']['server_url']
    template = env.get_template('upload.html')
    return template.render(url=ip+'/upload')
@app.route('/gallery', methods=['GET'])
@limit_ip_address
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
    return template.render(
        images_data = images_data, total_pages = total_pages, page = page, url_for = url_for, max=max, min=min)
@app.route('/delete')
@limit_ip_address
def delete():
    # todo delete
    pass
@app.route('/output/<filename>')
@limit_ip_address
def uploaded_file(filename):
    response = send_from_directory('output', filename)
    response.cache_control.max_age = 31536000
    return response
@app.route('/store/<path:filename>')
@limit_ip_address
def gallery_file(filename):
    # todo : filename中含有..时会越权访问
    response = send_from_directory('store', filename)
    if filename.endswith(('.png', '.jpg')):
        response.cache_control.max_age = 86400
    return response
@app.route('/registerIP', methods=['GET'])
def register_ip():
    password = request.args.get('password', default='', type=str)
    if password == ip_password:
        allowed_ip.append(request.remote_addr)
        return redirect(url_for('galleryPage'))
    return 'Forbidden', 403  
if not web_debug:
    mocr = MangaOcr()
    detector_model = init()
#CORS(app)
# 使用gunicorn时代码中不要运行app.run
# gunicorn -w 1 -b 0.0.0.0:5000 server:app
if web_debug:
    app.run(host='0.0.0.0', debug=True, use_reloader=True)
else:
    app.run(host='0.0.0.0', debug=False, use_reloader=False)