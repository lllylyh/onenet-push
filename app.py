from flask import Flask, request, Response
import requests as req
import json
import os

app = Flask(__name__)

# ✅ 钉钉机器人Webhook地址
DINGTALK_WEBHOOK = os.environ.get(
    'DINGTALK_WEBHOOK',
    'https://oapi.dingtalk.com/robot/send?access_token=你的Token'
)

@app.route('/', methods=['GET'])
def verify():
    """处理OneNET的URL验证请求"""
    msg = request.args.get('msg', '')
    print(f'[验证] msg={msg}')
    return Response(msg, status=200, content_type='text/plain')

@app.route('/', methods=['POST'])
def push():
    """处理OneNET的数据推送"""
    try:
        data = request.get_json()
        print(f'[收到] {json.dumps(data, ensure_ascii=False)}')

        # 解析msg字段
        msg_str = data.get('msg', '{}')
        if isinstance(msg_str, str):
            device_data = json.loads(msg_str)
        else:
            device_data = msg_str

        print(f'[解析后] {json.dumps(device_data, ensure_ascii=False)}')

        # 构建钉钉消息
        content = format_message(device_data)
        print(f'[将发送的内容] {content}')  # ← 关键：看这里

        ding_msg = {
            'msgtype': 'text',
            'text': {'content': content}
        }

        print(f'[钉钉请求体] {json.dumps(ding_msg, ensure_ascii=False)}')

        # 发送到钉钉
        resp = req.post(DINGTALK_WEBHOOK, json=ding_msg, timeout=3)
        print(f'[钉钉响应] {resp.text}')

    except Exception as e:
        print(f'[错误] {e}')

    return Response('ok', status=200, content_type='text/plain')

def format_message(data):
    """格式化设备数据为可读消息"""
    msg_type = data.get('type', '')
    device_name = data.get('device_name', '未知设备')
    params = data.get('params', {})

    print(f'[format] type={msg_type}, device={device_name}, params={params}')

    if msg_type == 'event':
        identifier = data.get('identifier', '')
        if identifier == 'overSpeedAlarm':
            speed = params.get('speed', {}).get('value', 0)
            limit = params.get('limit', {}).get('value', 0)
            return f'【超速告警】\n设备: {device_name}\n速度: {speed}km/h\n限速: {limit}km/h'
        else:
            return f'【事件上报】\n设备: {device_name}\n事件: {identifier}'

    elif msg_type == 'property':
        lines = [f'【属性上报】', f'设备: {device_name}']
        for k, v in params.items():
            val = v.get('value', v) if isinstance(v, dict) else v
            lines.append(f'{k}: {val}')
        return '\n'.join(lines)

    else:
        # 如果没有识别的类型，直接返回原始数据
        return f'【OneNET消息】\n{json.dumps(data, ensure_ascii=False)}'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
