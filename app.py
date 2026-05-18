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
    """格式化设备数据为可读消息"""
    notify_type = data.get('notifyType', '')
    device_name = data.get('deviceName', '未知设备')
    data_content = data.get('data', {})
    params = data_content.get('params', {})

    print(f'[format] notifyType={notify_type}, device={device_name}, params={params}')

    # 获取超速相关数据
    is_over_speed = params.get('isOverSpeed', {})
    max_speed = params.get('maxSpeed', {})
    speed_limit = params.get('speedLimit', {})

    # 如果检测到超速，发送告警消息
    if is_over_speed.get('value', False) == True:
        speed = max_speed.get('value', 0)
        limit = speed_limit.get('value', 0)
        return f'西区食堂路口有超速行为，速度为{speed}km/h'

    # 其他情况，返回JSON（方便调试）
    return f'【OneNET消息】\n{json.dumps(data, ensure_ascii=False)}'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
