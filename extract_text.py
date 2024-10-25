import subprocess
import json
from PIL import Image, ImageDraw, ImageFont

# 将临近的文本拼接
# todo 代码已经魔改成屎山了，希望有大佬可以优化逻辑...
def merge_area(areas):
    adjacent_distance = 20
    # 如果是连着大于两列文本，要不断循环拼接，直到一次循环中无任何可拼接为止
    has_merge = True
    
    is_first_merge = True
    while has_merge:
        has_merge = False
        if not is_first_merge:
            areas = merged_area
        merged_area = []
        is_first_merge = False
        for current_area in areas[:-1]:
            # 如果是被拼接到其他区域的区域，就不要加到merged_area里了
            if current_area[4]:
                continue
            for next_area in areas[areas.index(current_area)+1:]:
                # 临近的规则是一个area的左与另一个的右<20，且二者上边界或下边界<20
                if abs(current_area[1] - next_area[0]) < adjacent_distance \
                    and (abs(current_area[2] - next_area[2]) < adjacent_distance or abs(current_area[3] - next_area[3]) < adjacent_distance):
                    merged_area.append(
                        [min(current_area[0], next_area[0]),
                        max(current_area[1], next_area[1]),
                        min(current_area[2], next_area[2]),
                        max(current_area[3], next_area[3]),
                        False]
                        )
                    next_area[4] = True
                    has_merge = True
                    break
                if next_area == areas[-1]:
                    merged_area.append(current_area)
        # 最后一个上面循环略过了，这里要单独判断
        if not areas[-1][4]:
            merged_area.append(areas[-1])
    return merged_area

def extract_text(image_path, draw_rectangle):
    # 定义命令和参数
    command = ["paddleocr", "--image_dir", image_path, "--use_angle_cls", "true", "--rec", "false"]

    # 使用 subprocess.run 执行命令
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # 输出命令执行结果
    areas = []
    for line in result.stdout.split('\n'):
        if line.find('ppocr INFO:') > 0:
            if line.find('jpg') > 0:
                continue
            points_str = '['+line.split('ppocr INFO:')[1].split('[',1)[1]
            points = json.loads(points_str)
            
            x_min = min(point[0] for point in points)
            x_max = max(point[0] for point in points)
            y_min = min(point[1] for point in points)
            y_max = max(point[1] for point in points)
            areas.append([x_min, x_max, y_min, y_max, False])

            # image = Image.open('input.jpg')
            # draw = ImageDraw.Draw(image)
            # draw.rectangle([x_min, y_min, x_max, y_max], outline='red')
            # font_path = "DejaVuSans-Bold.ttf" 
            # font_size = 30
            # font = ImageFont.truetype(font_path, font_size)
            # draw.text([(x_min + x_max) / 2, (y_min + y_max) / 2], str(x_min), font=font, fill=(0, 0, 0))
            # image.save('input.jpg')
    if len(areas) == 0:
        return
    areas.sort(key=lambda x: x[0])
    i = 0
    for draw_area in merge_area(areas):
        i = i+1
        image = Image.open(image_path)
        if draw_rectangle:
            draw = ImageDraw.Draw(image)
            draw.rectangle([draw_area[0], draw_area[2], draw_area[1], draw_area[3]], outline='red')
            font_path = "DejaVuSans-Bold.ttf" 
            font_size = 40
            font = ImageFont.truetype(font_path, font_size)
            draw.text([draw_area[1], draw_area[3]], str(i), font=font, fill=(255, 0, 0))
        # todo: 画到另一个文件时会相互覆盖，需要优化逻辑
        image.save(image_path)
        # 根据坐标点截取图片
        cropped_image = image.crop((draw_area[0], draw_area[2], draw_area[1], draw_area[3]))

        # 保存截取后的图片
        cropped_image.save(f'./temp/{i}.jpg')
    return i


