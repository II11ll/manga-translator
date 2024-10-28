import json

# 定义文件路径
file_path = '/home/ubuntu/translation/store/saved.json'

# 要追加的数据
new_data = {"new_key": "new_value"}

# 使用 'r+' 模式打开文件，以便读取和写入
with open(file_path, 'r+', encoding='utf-8') as f:
    # 将文件指针移到文件开头
    f.seek(0)
    
    # 读取现有数据
    try:
        # 尝试读取JSON数据
        data = json.load(f)
    except json.JSONDecodeError:
        # 如果文件为空或JSON格式错误，则初始化为空字典
        data = {}
    
    # 更新或追加数据
    data.update(new_data)
    
    # 将文件指针移到文件开头，准备覆盖原有数据
    f.seek(0)
    
    # 清空文件内容
    f.truncate()
    
    # 写入更新后的数据
    json.dump(data, f, ensure_ascii=False, indent=4)

# 文件操作完成，文件已关闭
