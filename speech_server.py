# coding:utf-8
'''
WebSocketから受け取ったテキストを話すサーバー

Copyright (c) 2016 Daisuke IMAI

This software is released under the MIT License.
http://opensource.org/licenses/mit-license.php
'''
import os
import sys
import time
import json
import threading

import tornado.ioloop
import tornado.web
import tornado.websocket

#ここからTornadeでのWeb/WebSocketサーバーに関する定義
class IndexHandler(tornado.web.RequestHandler):
    '''
    通常のHTTPリクエストで/が求められた時のハンドラ
    '''
    @tornado.web.asynchronous
    def get(self):
        self.render("index.html")


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    '''
    WebSocketで/wsにアクセスが来た時のハンドラ

    on_message -> receive data
    write_message -> send data
    '''

    def open(self):
        global md
        global state
        self.i = 0
        self.callback = tornado.ioloop.PeriodicCallback(self._send_message, 50)
        self.callback.start()
        print('WebSocket opened')
        motion_data = md.read_json_file()
        md.set_motion_dataset(motion_data)
        self.write_message(json.dumps({'message': 'motion_command', 'json_data': motion_data}))
        if state['robot_connected']:
            self.write_message(json.dumps({'message': 'robot_connected'}))
        if state['renv_connected']:
            self.write_message(json.dumps({'message': 'renv_connected'}))

    def check_origin(self, origin):
        ''' アクセス元チェックをしないように上書き '''
        return True

    def on_message(self, message):
        global vc
        global md
        global ws
        global state

        received_data = json.loads(message)
        print('got message:', received_data['command'])
        if received_data['command'] == 'robot_connect':
            print('Connecting to V-Sido CONNECT via', received_data['port'], '...', end='')
            try:
                # V-Sido CONNECTに接続
                vc.connect(received_data['port'])
            except:
                self.write_message(json.dumps({'message': 'robot_cannot_connect'}))
                print('fail')
            else:
                self.write_message(json.dumps({'message': 'robot_connected'}))
                # PWMで目を光らせる場合に必要
                vc.set_vid_use_pwm();
                state['robot_connected'] = True
                print('done')
        elif received_data['command'] == 'robot_disconnect':
            print('Disconnecting from V-Sido CONNECT...', end='')
            # V-Sido CONNECTから切断
            vc.disconnect()
            self.write_message(json.dumps({'message': 'robot_disconnected'}))
            state['robot_connected'] = False
            print('done')
        elif received_data['command'] == 'set_motion_command':
            print('Renewaling/Saving Motion Data...', end='')
            # JSONデータを保存する
            json_data = received_data['json_data']
            md.write_json_file(json_data)
            md.set_motion_dataset(json_data)
            self.write_message(json.dumps({'message': 'motion_command', 'json_data': json_data}))
            print('done')
        elif received_data['command'] == 'renv_connect':
            # Scratchに接続
            print('Connecting to Renv...', end='')
            try:
                ws = RenvConnecter(received_data['websocket'], protocols=['http-only'])
                ws.connect()
            except:
                self.write_message(json.dumps({'message': 'renv_cannot_connect'}))
                print('fail')
                raise
            else:
                self.write_message(json.dumps({'message': 'renv_connected'}))
                state['renv_connected'] = True
                print('done')
        elif received_data['command'] == 'renv_disconnect':
            # Scratcから切断
            print('Disconnecting from R-env...', end='')
            ws.close()
            self.write_message(json.dumps({'message': 'renv_disconnected'}))
            state['renv_connected'] = False
            print('done')

    def _send_message(self):
        pass
#        if len(vsidoconnect.message_buffer) > 0:
#            self.write_message(vsidoconnect.message_buffer.pop(0))

    def on_close(self):
        self.callback.stop()
        print('WebSocket closed')


class RenvConnecter(TornadoWebSocketClient):
    def opened(self):
        self.send_device_connection_info()

    def received_message(self, m):
        print(m)
        message = json.loads(m.data.decode())
        #print(type(message))
        if message["eventName"] == "Renv.System.StartTransportEvent":
            print("Renv: Connected.")
        elif message["eventName"] == "motion":
            print("Renv: Receive motion command.")
            global vc
            global md
            motion_name = message["eventParam"]["motion_name"]["val"]
            if motion_name in md.get_motion_list():
                motion = md.get_motion_data(motion_name)
                motion_type = motion['type']
                #print(motion)
                if motion_type == 'motion':
                    motion_list = motion['data']
                else:
                    motion_list = [motion, ]
                for motion_data in motion_list:
                    print(motion_data)
                    if motion_data['type'] == 'angle':
                        vc.set_servo_angle(*motion_data['data'], cycle_time=round(motion_data['time']))
                    if motion_data['type'] == 'ik':
                        vc.set_ik(*motion_data['data'])
                    if motion_data['type'] == 'gpio':
                        vc.set_vid_io_mode({'iid': 7, 'mode': 1})
                        vc.set_gpio_value(*motion_data['data'])
                    if motion_data['type'] == 'pwm':
                        vc.set_vid_use_pwm();
                        vc.set_pwm_pulse_width(*motion_data['data'])
                    if motion_data['type'] == 'wait':
                        time.sleep(motion_data['time'] / 1000)
                self.send_event("motion_done")

    def closed(self, code, reason=None):
        #tornado.ioloop.IOLoop.instance().stop()
        print("R-env connection closed.")

    def send_device_connection_info(self):
        self.send(json.dumps(device_connection_info))

    def send_event(self, event_name):
        self.send(json.dumps({"eventName": event_name}))

if __name__ == '__main__':

    # アプリケーション割り当て
    web_application = tornado.web.Application(
        [
            (r'/', IndexHandler),
            (r'/ws', WebSocketHandler),
        ],
        template_path=os.path.join(os.getcwd(),  'templates'),
        static_path=os.path.join(os.getcwd(),  'assets'),
    )

    # V-Sido CONNECTのインスタンス生成
    vc = vsido.Connect(debug=True)

    # モーションデータのインスタンス生成
    md = MotionData()

    # Renv用のウェブソケットのインスタンス用変数準備
    ws = None

    # 引数処理
    param = sys.argv
    if len(param) > 1:
        # 引数がついていればモーションファイル名で使う
        md.set_motion_filepath(param[1])

    # Tornadoサーバー起動
    print('Starting Web/WebSocket Server...', end='')
    web_application.listen(8888)
    print('done')

    print('Open http://localhost:8888/')
    print('')

    tornado.ioloop.IOLoop.instance().start()