
## /chat API格式
### 请求（json，post）
{
    "first": 是否为患者的第一句对话（true/false）,
    "patient_id": 患者ID（第一句对话时不需要提供）,
    "input": 患者提问的文本（第一句对话时可以随意提供，此时模型固定返回"您好！我是智能问诊助手，请简要描述您的状况，我将尽力为您提供建议。"）
}

#### 示例
（首次对话，注意这里不需要提供patient_id，后端创建完患者后会向前端返回患者ID）
{
    "first": true,
    "input": "" （第一句对话时input随意，因为第一句话是模型说的，模型返回固定的提问模板）
}

（非首次对话）
{
    "first": false,
    "patient_id": 12,       // 这里的患者ID是第一次对话时从API返回的
    "input": "医生你好，我最近肠胃不太舒服。"
}

### 通常返回（json，post）
{
    "success": true,
    "patient_id": 12,
    "end": false,           // 对话尚未结束
    "msg": "success",       // 模型的错误信息
    "response": "患者你好，考虑为上火所引起的，建议口服牛黄解毒片治疗，同时禁烟酒及辛辣刺激性食物。"
}

### 最后一轮返回（json，post）
{
    "success": true,
    "patient_id": 12,
    "end": true,                // 对话结束
    "msg": "success",           // 模型的错误信息
    "response": "好的，您的挂号信息已经收集完毕，以下是您的挂号信息：\n地点：山东省威海市环翠区文化西路街道\n日期：20240815\n时间：1400\n中医服务：是\n三甲医院：是\n肛肠科\n医生类型：专家号\n姓名：王刚\n身份证号：330719196804253671\n手机号码：16666666666即将开始自动挂号",
    "data": {
        "location": "山东省威海市环翠区文化西路街道",
        "date": "20240815",
        "time": "1400",
        "ctm": true,
        "hospital_level": true, // 三甲医院
        "department": "肛肠科",
        "type": "专家号",
        "name": "王刚",
        "id": 330719196804253671,
        "phone": 16666666666
    }
}

### 错误返回（json，post）
{
    "success": false,
    "msg": "Invalid JSON format"
}

## 大模型对话API格式（国林）
### 请求（json，post）
{
    "context": query,
    "history": history,
    "top_k": 0,
    "top_p": 0.7,               # 0.0 为 greedy_search
    "temperature": 0.9,
    "repetition_penalty": 1.2,
    "max_length": 1024,
    "src_length": 512,
    "min_length": 32
}

### 正常返回（json，post）
[{
    "error_code": 0,
    "result": {
        "response": {
            "utterance": "模型输出"
        }
    }
}, ...]

### 错误返回（json，post）
{
    "error_msg": 错误信息（string）
}

## 科室推荐API格式（丁）
### 请求（json，post）
{
    "text": 输入分类模型的文本（string）
}

### 返回（json，post）
{
    "department": 科室名称（XX科，string）
}
