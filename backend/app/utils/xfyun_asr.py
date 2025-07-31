#!/usr/bin/env python3
# -*-coding:utf-8 -*-
import base64
import ssl
import _thread as thread
import threading
import queue

from jsonpath_rw import parse
import websocket

from app.utils.sample import ne_utils, aipass_client
from app.utils.data import *


# 收到websocket连接建立的处理
def on_open(ws):
    def run():
        # 清除文件
        ne_utils.del_file('./resource/output')
        # 判断是否是多模请求
        exist_audio = parse("$.payload.*.audio").find(request_data)
        exist_video = parse("$.payload.*.video").find(request_data)
        multi_mode = True if exist_audio and exist_video else False

        # 获取frame，用于设置发送数据的频率
        frame_rate = None
        frame_rate_matches = parse("$.payload.*.frame_rate").find(request_data)
        if frame_rate_matches:
            frame_rate = frame_rate_matches[0].value
        time_interval = 40
        if frame_rate:
            time_interval = round((1 / frame_rate) * 1000)

        # 获取待发送的数据
        media_path2data = aipass_client.prepare_req_data(request_data)
        # 发送数据
        aipass_client.send_ws_stream(ws, request_data, media_path2data, multi_mode, time_interval)

    thread.start_new_thread(run, ())


# 收到websocket消息的处理
def on_message(ws, message):
    aipass_client.deal_message(ws, message)
    message = eval(message)
    if message["header"]["status"] == 2:
        text = message["payload"]["result"]["text"]
        text_de = base64.b64decode(text)
        print("text字段解析结果：\n", str(text_de, "utf-8"))


# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws,a,b):
    print("*** 执行结束，连接自动关闭 ***")


def run_xfyun_asr(request_data, APPId, APIKey, APISecret, request_url, timeout=900):
    """
    同步调用科大讯飞语音分析，返回最终识别文本。
    """
    result_queue = queue.Queue()
    # 拷贝 request_data，避免多线程污染
    import copy
    req_data = copy.deepcopy(request_data)
    req_data['header']['app_id'] = APPId
    auth_request_url = ne_utils.build_auth_request_url(request_url, "GET", APIKey, APISecret)

    def on_message(ws, message):
        aipass_client.deal_message(ws, message)
        try:
            msg = eval(message)
            if msg["header"]["status"] == 2:
                print('status  is 2')
                text = msg["payload"]["result"]["text"]
                text_de = base64.b64decode(text).decode("utf-8")
                result_queue.put(text_de)
                ws.close()
        except Exception as e:
            result_queue.put(None)
            ws.close()

    def on_error(ws, error):
        print('on_error')
        print("### error:", error)
        result_queue.put(None)
        ws.close()

    def on_close(ws, *args):
        print('close')

    def on_open(ws):
        def run():
            # ne_utils.del_file('./resource/output')
            exist_audio = parse("$.payload.*.audio").find(req_data)
            exist_video = parse("$.payload.*.video").find(req_data)
            multi_mode = True if exist_audio and exist_video else False
            frame_rate = None
            frame_rate_matches = parse("$.payload.*.frame_rate").find(req_data)
            if frame_rate_matches:
                frame_rate = frame_rate_matches[0].value
            time_interval = 40
            if frame_rate:
                time_interval = round((1 / frame_rate) * 1000)
            media_path2data = aipass_client.prepare_req_data(req_data)
            aipass_client.send_ws_stream(ws, req_data, media_path2data, multi_mode, time_interval)
        threading.Thread(target=run).start()

    ws = websocket.WebSocketApp(
        auth_request_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.on_open = on_open
    ws_thread = threading.Thread(target=ws.run_forever, kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}})
    ws_thread.start()
    try:
        result = result_queue.get(timeout=timeout)
    except queue.Empty:
        result = None
    return result


if __name__ == '__main__':
    user_texts_str = '公司有核苷酸还有纳豆，各种维生素产品'
    conversation_id = '445c6f33-8ea3-4691-84af-f6607f2ce2ce'
    output_path = rf'E:\work\code\test_uniapp\LLS_0611\LLS\backend\uploads\voice\3\{conversation_id}\audio_1753170919506_zg5vic.mp3'
    import copy

    req_data = copy.deepcopy(request_data)
    # 假设音频路径字段为 payload->data->audio
    req_data["parameter"]["st"]["refText"] = user_texts_str
    req_data["payload"]["data"]["audio"] = output_path
    request_url = "wss://cn-east-1.ws-api.xf-yun.com/v1/private/s8e098720"
    run_xfyun_asr(req_data, APPId, APIKey, APISecret, request_url, timeout=900)
    # 程序启动的时候设置APPID
    request_data['header']['app_id'] = APPId
    auth_request_url = ne_utils.build_auth_request_url(request_url, "GET", APIKey, APISecret)
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(auth_request_url, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
