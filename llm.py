import erniebot
erniebot.api_type = 'aistudio'

question = "请分析此日语句子的语法并为汉字标注假名：演技だとしても人目につくと誤解を招くだろう"
messages = [{'role': 'user', 'content': question}]
response = erniebot.ChatCompletion.create(
    model='ernie-4.0-turbo-8k',
    messages=messages,
)
print(response.get_result())