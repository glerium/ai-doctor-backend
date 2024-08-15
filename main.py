from flask import request, jsonify

from preferences import Preferences
import json
import utils

from app import app
from db import db
from model_patient import Patient       # model: SQLAlchemy 数据库对象 <-> Python Class对象

with app.app_context():
    db.create_all()         # 如果数据库中的表格不存在的话，那么创建table


# 先进行提问，再询问信息
@app.route('/chat', methods=['POST'])
def api_chat():
    def normal_return(response: str):
        return jsonify({
            'success': True,
            'patient_id': patient_id,
            'end': False,
            'msg': 'success',
            'response': response
        })
    
    def final_return(pref: dict):
        return jsonify({
            'success': True,
            'patient_id': patient_id,
            'end': True,
            'msg': 'success',
            'response': f'''好的，您的挂号信息已经收集完毕，以下是您的挂号信息：
地点：{pref['location']}
日期：{pref["date"]}
时间：{pref["time"]}
中医服务：{"是" if pref["ctm"] else "否"}
三甲医院：{"是" if pref["hospital_level"] else "否"}
科室：{pref["department"]}
医生类型：{pref["type"]}
姓名：{pref['name']}
身份证号：{pref['id']}
手机号码：{pref['phone']}
即将开始自动挂号''',
            'data': {
                'location': pref['location'],
                'date': pref['date'],
                'time': pref['time'],
                'ctm': pref['ctm'],
                'hospital_level': pref['hospital_level'],
                'department': pref['department'],
                'type': pref['type'],
                'name': pref['name'],
                'id': pref['id'],
                'phone': pref['phone']
            }
        })
    
    def error_return(msg: str):
        return jsonify({
            'success': False,
            'msg': msg
        })

    if not request.is_json:
        return error_return('Request must be JSON format.')
    
    data = request.get_json()
    print(data)
    
    try:
        first = data['first']       # 是否是首轮对话，创建患者在数据库中的id、等等
    except KeyError:
        return error_return('Invalid JSON format.')
    
    if first:
        # 创建患者对象，写入数据库，返回id和问候语
        patient = Patient()
        db.session.add(patient)
        db.session.commit()
        db.session.flush()
        db.session.refresh(patient)
        patient_id = patient.patient_id
        return normal_return('您好！我是智能问诊助手，请简要描述您的状况，我将尽力为您提供建议。')
    else:
        # 非首轮对话
        try:
            patient_id = data['patient_id']
        except KeyError:
            return error_return('No patient_id provided')
        patient = Patient.query.filter(Patient.patient_id == patient_id).first()

    if patient is None:
        return error_return('Invalid patient_id')

    # 至少是第二轮进行对话
    # patient: Patient
    # chat模块分为两部分：问诊部分（调用大模型，对患者的症状进行回复和提供建议）、搜集患者信息
    if not patient.chat_end:
        user_input = data['input']
        try:
            # chat_end: 用户的问诊是否已经结束
            # model_output：大模型的输出
            [chat_end, model_output] = utils.invoke_chat(user_input)            # 调用微调后的大模型
            if patient.chat_log is None:
                patient.chat_log = ""
            patient.chat_log += ' ' + user_input
            # 诊室智能推荐（文本分类大模型）
            department = utils.invoke_department_classification(user_input)     # 科室分类
            if patient.department_count is None:
                patient.department_count = {}
            patient.department_count = utils.update_department_count(patient.department_count, department)
            db.session.commit()
            db.session.flush()
            db.session.refresh(patient)

        except ValueError as e:
            return error_return(e.args[0])

        if not chat_end:
            return normal_return(model_output + '输入“结束”停止问诊。')
        else:
            patient.chat_end = True
            db.session.commit()
            return normal_return('好的，下面需要收集您的信息进行挂号。首先请提供您期望的挂号地点，按省市区街道格式输入。')

    else:
        if patient.preferences is None:
            pref = {}
        else:
            pref = json.loads(patient.preferences)
        step = patient.preference_step      # 从数据库中，获取已经收集了几条信息
        step = Preferences(step)
        recommended_department = utils.recommend_department(patient.department_count)
        user_input = data['input']
        print(step)
        try:
            print(step)
            print(utils.check_user_preference(user_input, step))
            result, error = utils.check_user_preference(user_input, step)       # 验证用户在上轮对话中的信息的有效性
            if error:                       # 信息无效，要求用户重新输入
                raise SystemError(result)

            match step:                     # 信息有效，收集下一条信息，并且给用户返回提示
                case Preferences.LOCATION:
                    pref['location'] = result
                    msg = '您期望在什么时间就诊？请按照YYYYMMDD-HHmm格式输入。'
                case Preferences.DATETIME:
                    pref['date'], pref['time'] = result
                    msg = '您是否需要中医服务？（是/否）'
                case Preferences.CTM:
                    pref['ctm'] = result
                    msg = '是否需要将搜索范围限定在三甲医院内？（是/否）'
                case Preferences.HOSPLEVEL:
                    pref['hospital_level'] = result
                    msg = f'您希望挂号的科室是？（根据刚才的问诊结果，推荐您挂号{recommended_department}）'
                case Preferences.DEPARTMENT:
                    pref['department'] = result
                    msg = '您需要挂号普通号还是专家号？'
                case Preferences.TYPE:
                    pref['type'] = result
                    msg = '请输入您的姓名。'
                case Preferences.NAME:
                    pref['name'] = result
                    msg = '请提供您的18位身份证号码。'
                case Preferences.ID:
                    pref['id'] = result
                    msg = '请提供您的手机号码。'
                case Preferences.PHONE:
                    pref['phone'] = result
                    return final_return(pref)

            patient.preferences = json.dumps(pref)
            step = Preferences(step.value + 1)
            patient.preference_step = step.value
            print(patient.preference_step)
            db.session.commit()
            db.session.flush()
            db.session.refresh(patient)

            return normal_return(msg)

        except SystemError as e:
            return error_return(e.args[0])
        except Exception as e:
            return error_return(e.with_traceback())


if __name__ == '__main__':
    app.run(port=80, debug=True, host='0.0.0.0')
