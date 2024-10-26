import argparse
from extract_text import extract_text
from infer import infer
from manga_ocr import MangaOcr
import threading
from translation import translation
import configparser
mocr = None
def init_mocr():
    global mocr
    mocr = MangaOcr()
def read_config():
    config = configparser.ConfigParser()
    try:
        config.read('config.ini')
    except FileNotFoundError as e:
        print("无配置文件")
        raise e
    return config

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--image_path", default='./temp/test.jpg')
    # todo: 目前是在原图上画，需要修改
    parser.add_argument('-d', "--draw_rectangle", action='store_true',
                         help='在识别出的文本区域外围画矩形边框且标上序号')
    parser.add_argument('-t', "--traslation", action='store_true',
                        help='调用百度翻译API翻译')
    parser.add_argument('-g','--generate_promopt', action='store_true',
                        help='生成ai问答提示词')
    parser.add_argument('-de','--debug', action='store_true',
                        help='调试')
    args = parser.parse_args()
    if args.debug:
        extract_text('./temp/input.jpg', True, True)
        return
    thread = threading.Thread(target=init_mocr)
    thread.start()
    image_num = extract_text(args.image_path, args.draw_rectangle)
    thread.join()
    with open('output.txt', 'w', encoding='utf-8') as f:
        for i in range(image_num):
            sentence = infer(mocr, i)
            f.write(sentence + '\n')
            if args.traslation:
                config = read_config()
                trans = translation(sentence, config['keys']['api_key'].replace('\n',''), config['keys']['secret_key'].replace('\n',''))
                f.write(trans + '\n')
            if args.generate_promopt:
                f.write('请分析此日语句子的语法并为汉字标注假名：'+sentence+'\n')
if __name__ == '__main__':
    main()
    #print(args.image_path)