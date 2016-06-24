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

import netifaces
import tornado.ioloop
import tornado.web
import tornado.websocket

class SpeechManager():
	OPENJTALK_EXE = '/usr/bin/open_jtalk'
	OPENJTALK_DIC_DIR = '/var/lib/mecab/dic/open-jtalk/naist-jdic'
	OPENJTALK_VOICE_DIR = './voice'
	MPLAYER_EXE = '/usr/bin/mplayer'
	WORK_DIR = './'
	def __init__(self):
		pass
	def say(self, text, voice='mei/mei_happy.htsvoice'):
		speech_file = SpeechManager.WORK_DIR + 'talk' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.wav'
		print('Makeing speech data...,', end='')
		open_jtalk_command = [SpeechManager.OPENJTALK_EXE, '-m', SpeechManager.OPENJTALK_VOICE_DIR + '/' + voice, '-x', SpeechManager.OPENJTALK_DIC_DIR, '-ow', speech_file]
		open_jtalk = subprocess.Popen(open_jtalk_command, universal_newlines=True, stdin=subprocess.PIPE)
		open_jtalk.communicate(text)
		open_jtalk.wait()
		print('done')
		print('Playing speech data...,', end='')
		mplayer_command = [SpeechManager.MPLAYER_EXE, '-really-quiet', speech_file]
		mplayer = subprocess.Popen(mplayer_command)
		mplayer.wait()
		print('done')
		print('Deleting speech data...,', end='')
		time.sleep(0.1)
		os.remove(speech_file)
		print('done')
		print('')

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
			#print(received_data['data']['text'])
			speech_manager.say(received_data['data']['text'], received_data['data']['voice'])
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

	ip_addr = netifaces.ifaddresses('wlan0')[2][0]['addr'];
	#ip_addr = '192.168.1.1';

	# Tornadoサーバー起動
	print('Starting Web/WebSocket Server...', end='')
	web_application.listen(8888)
	print('done')

	print('Open http://' + ip_addr + ':8888/')
	print('')

	speech_manager = SpeechManager()
	speech_manager.say('スピーチサーバーが起動しました。')
	speech_manager.say('IPアドレスは、' + ip_addr + 'です。')

	tornado.ioloop.IOLoop.instance().start()
