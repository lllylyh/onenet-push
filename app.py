from flask import Flask, request, Response
import requests as req
import json
import os

app = Flask(__name__)

# ✅ 修复：移除URL中的反引号和空格
DINGTALK_WEBHOOK = os.environ.get(
    'DINGTALK_WEBHOOK',
    'https://oapi.dingtalk.com/robot/send?access_token=你的Token'
)


@app.route('/', methods=['GET'])
def verify():
    msg = request.args.get('msg', '')
    return Response(msg, status=200, content_type='text/plain')


@app.route('/', methods=['POST'])
def push():
    try:
        data = request.get_json()
        print(f'[收到] {json.dumps(data, ensure_ascii=False)}')

        msg_str = data.get('msg', '{}')
        if isinstance(msg_str, str):
            device_data = json.loads(msg_str)
        else:
            device_data = msg_str

        content = format_message(device_data)

        # ✅ 添加调试日志
        if content is None:
            print('[未超速或数据解析失败，跳过推送]')
            return Response('ok', status=200, content_type='text/plain')

        print(f'[将发送的内容] {content}')

        ding_msg = {
            'msgtype': 'text',
            'text': {'content': content}
        }

        resp = req.post(DINGTALK_WEBHOOK, json=ding_msg, timeout=3)
        print(f'[钉钉响应] {resp.text}')

    except Exception as e:
        print(f'[错误] {e}')

    return Response('ok', status=200, content_type='text/plain')


def format_message(data):
    """格式化消息 - 超速时返回消息，未超速时返回 None"""
    print(f'[format] 原始数据: {json.dumps(data, ensure_ascii=False)}')
    
    # ✅ 修复：直接从 device_data 获取 params（OneNET事件上报格式）
    params = data.get('params', {})
    print(f'[format] params: {params}')

    # 提取数据（支持多种数据格式）
    is_over_speed = params.get('isOverSpeed', {})
    max_speed_val = params.get('maxSpeed', {})

    # ✅ 兼容多种数据格式
    speed = max_speed_val.get('value', 0) if isinstance(max_speed_val, dict) else (max_speed_val if isinstance(max_speed_val, int) else 0)
    
    # ✅ 兼容 isOverSpeed 可能是布尔值或字典
    if isinstance(is_over_speed, dict):
        over_speed = is_over_speed.get('value', False)
    elif isinstance(is_over_speed, bool):
        over_speed = is_over_speed
    else:
        over_speed = False

    print(f'[format] speed={speed}, overSpeed={over_speed}')

    # 超速才推送
    if over_speed:
        return f'西区食堂路口有超速行为，速度为{speed}km/h'
    else:
        return None


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
