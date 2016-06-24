#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
WebSocketから受け取ったテキストを話すサーバー

Copyright (c) 2016 Daisuke IMAI

This software is released under the MIT License.
http://opensource.org/licenses/mit-license.php
'''
import os
import sys
import time
import datetime
import json
import subprocess

import tornado.ioloop
import tornado.web
import tornado.websocket

class SpeechManager():
	OPENJTALK_EXE = '/usr/bin/open_jtalk'
	OPENJTALK_DIC_DIR = '/var/lib/mecab/dic/open-jtalk/naist-jdic'
	OPENJTALK_VOICE_DIR = './voice'
	MPLAYER = '/usr/bin/mplayer'
	WORK_DIR = '/var/tmp'
	def __init__(self):
		pass
	def say(self, text):
		speech_file = SpeechManager.WORK_DIR + 'talk' + datetime.datetime.now().strftime('%Y/%m/%d') + '.wav'
		open_jtalk_command = SpeechManager.OPENJTALK_EXE + ' -m ' +  SpeechManager.OPENJTALK_VOICE_DIR + '/mei/mei-happy.htsvoice -x ' + SpeechManager.OPENJTALK_DIC_DIR + ' -ow ' + speech_file
		open_jtalk = subprocess.Popen(command, stdin=subprocess.PIPE)
		open_jtalk.stdin.write(text)
		open_jtalk.stdin.close()
		open_jtalk.wait()
		mplayer_command = SpeechManager.MPLAYER + ' ' + speech_file
		subprocess.Popen(mplayer_command)

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
		# self.write_message(json.dumps({'message': 'connected'}))

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
		if received_data['command'] == 'say':
			print('Saying...', end='')
			# 発話に関する処理を入れる
			print('done')

	def _send_message(self):
		pass
#		if len(vsidoconnect.message_buffer) > 0:
#			self.write_message(vsidoconnect.message_buffer.pop(0))

	def on_close(self):
		self.callback.stop()
		print('WebSocket closed')


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

	speech_manager = SpeechManager()
	speech_manager.say('スピーチサーバーが起動しました')

	# Tornadoサーバー起動
	print('Starting Web/WebSocket Server...', end='')
	web_application.listen(8888)
	print('done')

	print('Open http://(SpeechServer_IP):8888/')
	print('')

	tornado.ioloop.IOLoop.instance().start()
