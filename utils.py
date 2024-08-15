import requests
import os
import qianfan
import regex as re
import json
from datetime import datetime, timedelta
from typing import Tuple, Any
from preferences import Preferences
from id_validator import validator as id_validator


os.environ["QIANFAN_ACCESS_KEY"] = "Enter your access key"
os.environ["QIANFAN_SECRET_KEY"] = "Enter your secret key"
chat_url_pattern = 'https://link.to/your/chat/api'
recommend_url_pattern = 'https://link.to/your/recommend/api'

chat_comp = qianfan.ChatCompletion()

# 调用AI聊天机器人大模型
def invoke_chat(query, history=None):
    history = ['现在你是一个医疗专家，我有一些身体问题，请你用专业的知识帮我解决。', '好的，我是一个医疗专家，我会尽力帮助你解决问题。']
    data = {
        "context": query,
        "history": history,
        "top_k": 0,
        "top_p": 0.7,  # 0.0 为 greedy_search
        "temperature": 0.9,
        "repetition_penalty": 1.2,
        "max_length": 1024,
        "src_length": 512,
        "min_length": 32
    }
    res = requests.post(chat_url_pattern, json=data, stream=True)
    text = ""
    for line in res.iter_lines():
        result = json.loads(line)
        # print(result)

        if result["error_code"] != 0:
            text = "error-response"
            break

        result = json.loads(line)
        bot_response = result["result"]["response"]

        if bot_response["utterance"].endswith("[END]"):
            bot_response["utterance"] = bot_response["utterance"][:-5]
        text += bot_response["utterance"]

    print(text)
    text = invoke_add_punct(text)
    print(text)

    # print("result -> ", text)
    return ['结束' in query, text]


# 调用科室分类API
def invoke_department_classification(msg: str) -> str:
    data = {
        'text': msg
    }
    ret = requests.post(recommend_url_pattern, json=data)
    department = ret.json()['department']
    print(department)
    return department
    

# 检查用户输入的preference是否符合要求
# 身份证号  手机号
def check_user_preference(user_input: str, preference_step: Preferences) -> Tuple[Any, bool]:
    def error_(msg: str):
        return (msg, True)

    def result_(result: Any):
        return (result, False)

    match preference_step:
        case Preferences.LOCATION:
            pattern = re.compile(r'^.*?省.*?市.*?区.*?街道.*?$')
            if not pattern.match(user_input):
                return error_('地点格式无效')
            else:
                return result_(user_input)
        case Preferences.DATETIME:
            pattern = r'^\d{4}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])-(2[0-3]|[01][0-9])([0-5][0-9])$'
            # print(pattern, user_input, re.match(pattern, user_input))
            if not re.match(pattern, user_input):
                return error_('日期时间格式无效')
            else:
                date_part, time_part = user_input.split('-')
                try:  
                    user_datetime = datetime.strptime(f"{date_part} {time_part}", "%Y%m%d %H%M")  
                    now = datetime.now()
                    if user_datetime >= now:  
                        return result_((date_part, time_part))
                    else:  
                        return error_('输入应该晚于当前时间')
                except ValueError:
                    return error_('日期时间格式无效')
        case Preferences.CTM | Preferences.HOSPLEVEL:
            if '是' in user_input:
                return result_(True)
            elif '否' in user_input or '不' in user_input:
                return result_(False)
            else:
                return error_('请回答“是”或“否”')
        case Preferences.DEPARTMENT:
            if user_input.endswith('科'):
                return result_(user_input)
            else:
                return error_('科室名称无效')
        case Preferences.TYPE:
            if '普通号' in user_input:
                return result_('普通号')
            elif '专家号' in user_input:
                return result_('专家号')
            else:
                return error_('请回答“普通号”或“专家号”')
        case Preferences.NAME:
            return result_(user_input)
        case Preferences.ID:
            if id_validator.is_valid(user_input):
                return result_(user_input)
            else:
                return error_('请输入正确的身份证号')
        case Preferences.PHONE:
            pattern = re.compile(r'^(13[0-9]|14[01456879]|15[0-35-9]|16[2567]|17[0-8]|18[0-9]|19[0-35-9])\d{8}$')
            if re.match(pattern, user_input):
                return result_(user_input)
            else:
                return error_('请输入正确的手机号码')



# 更新count_dict中的科室计数
# 用户进行20轮对话，每轮对话后，都会对用户需要的科室进行判断（20个科室名称）
# 20个科室里面，取出现次数最多的科室，作为推荐用户去挂号的地点
def update_department_count(count_dict: dict, department: str):
    if department in count_dict:
        count_dict[department] += 1
    else:
        count_dict[department] = 1
    return count_dict


# 根据count_dict推荐最优科室
def recommend_department(count_dict: dict):
    max_count = 0
    max_department = ''
    for department, count in count_dict.items():
        if count > max_count:
            max_count = count
            max_department = department
    return max_department


# 给文本添加标点符号
def invoke_add_punct(msg: str):
    resp = chat_comp.do(model="ERNIE-Lite-8K-0308", messages=[{
        "role": "user",
        "content": '请给以下文本添加标点符号，输出处理后的文本即可，不要添加任何其他内容。\n' + msg
    }])
    return resp['result']
