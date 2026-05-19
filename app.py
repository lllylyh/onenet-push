from flask import Flask, request, Response
import requests as req
import json
import os

app = Flask(__name__)

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
        print(f'[将发送的内容] {content}')

        # ⭐ 先都发送，测试用
        if content:
            ding_msg = {
                'msgtype': 'text',
                'text': {'content': content}
            }
            resp = req.post(DINGTALK_WEBHOOK, json=ding_msg, timeout=3)
            print(f'[钉钉响应] {resp.text}')
        else:
            print('[内容为空，跳过]')

    except Exception as e:
        print(f'[错误] {e}')

    return Response('ok', status=200, content_type='text/plain')


def format_message(data):
    """格式化消息"""
    data_content = data.get('data', {})
    params = data_content.get('params', {})

    is_over_speed = params.get('isOverSpeed', {})
    max_speed_val = params.get('maxSpeed', {})
    speed_limit_val = params.get('speedLimit', {})

    speed = max_speed_val.get('value', 0) if isinstance(max_speed_val, dict) else 0
    limit = speed_limit_val.get('value', 0) if isinstance(speed_limit_val, dict) else 0
    over_speed = is_over_speed.get('value', False) if isinstance(is_over_speed, dict) else False

    print(f'[format] speed={speed}, limit={limit}, overSpeed={over_speed}')

    # ⭐ 超速和未超速都包含"超速"关键词，确保钉钉不拦截
    if over_speed:
        return f'西区食堂路口有超速行为，速度为{speed}km/h'
    else:
        return f'西区食堂路口超速检测正常，当前车速{speed}km/h，限速{limit}km/h'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
