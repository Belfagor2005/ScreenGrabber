#!/usr/bin/python
# -*- coding: utf-8 -*-

# ScreenGrabber V.%s mfaraj - Mod. by Lululla
# all remake for py3 and major fix from @lululla 20240915
# fixed lululla for dreamos 20240918

from __future__ import print_function

from . import _


try:
	from Components.AVSwitch import AVSwitch
except ImportError:
	from Components.AVSwitch import eAVControl as AVSwitch
from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap, MovingPixmap
from Components.Sources.StaticText import StaticText
'''
from Components.config import (
	config,
	ConfigSubsection,
	ConfigInteger,
	ConfigSelection,
	ConfigText,
	ConfigEnableDisable,
)
'''
from Screens.Screen import Screen
from enigma import ePicLoad, eTimer, getDesktop
from os.path import exists as file_exists, join
from os import remove
from .plugin import cfg


def getScale():
	return AVSwitch().getFramebufferScale()


T_INDEX = 0
T_FRAME_POS = 1
T_PAGE = 2
T_NAME = 3
T_FULL = 4


class sgrabberPic_Thumb(Screen):

	def __init__(self, session, piclist, lastindex, path):
		self.textcolor = cfg.textcolor.value
		self.color = cfg.bgcolor.value
		textsize = 35  # 24
		self.spaceX = 50  # 35
		self.picX = 400  # 190
		self.spaceY = 10  # 30
		self.picY = 320  # 200
		size_w = getDesktop(0).size().width()
		size_h = getDesktop(0).size().height()
		self.thumbsX = size_w // (self.spaceX + self.picX)
		self.thumbsY = size_h // (self.spaceY + self.picY)
		self.thumbsC = int(round(self.thumbsX * self.thumbsY))
		self.positionlist = []
		skincontent = ''
		posX = -1
		for x in range(self.thumbsC):
			posY = x // self.thumbsX
			posX += 1
			if posX >= self.thumbsX:
				posX = 0
			absX = self.spaceX + int(posX) * (self.spaceX + self.picX)
			absY = self.spaceY + int(round(posY)) * (self.spaceY + self.picY)
			self.positionlist.append((int(round(absX)), int(round(absY))))
			skincontent += '<widget source="label' + str(x) + '" render="Label" position="' + str(absX) + ',' + str(absY + self.picY - textsize) + '" size="' + str(self.picX) + ',' + str(textsize) + '" font="Regular;18" zPosition="2" transparent="1" noWrap="1" foregroundColor="' + self.textcolor + '" />\n'
			skincontent += '<widget name="thumb' + str(x) + '" position="' + str(absX + 5) + ',' + str(absY + 5) + '" size="' + str(self.picX - 10) + ',' + str(self.picY - textsize * 2) + '" zPosition="2" transparent="1" alphatest="on" />\n'

		skinthumb = '<screen name="sgrabberPic_Thumb" position="center,center" size="' + str(size_w) + ',' + str(size_h) + '" flags="wfNoBorder" >\n'
		skinthumb += '<eLabel position="0,0" zPosition="1" size="' + str(size_w) + ',' + str(size_h) + '" backgroundColor="' + self.color + '" />\n'
		skinthumb += '<widget name="frame" position="35,30" size="' + str(self.picX + 5) + ',' + str(self.picY + 10) + '" scale="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/images/pic_frame.png" alphatest="on" zPosition="3"/>\n'
		skinthumb += skincontent + '\n'
		skinthumb += '</screen>\n'
		self.skin = skinthumb

		print('str(self.picY - textsize * 2):', str(self.picY + 5))

		# print('self.skin=\n', self.skin)
		Screen.__init__(self, session)
		self['actions'] = ActionMap(
			[
				'OkCancelActions',
				'ColorActions',
				'DirectionActions',
				'MovieSelectionActions'
			],
			{
				'cancel': self.Exit,
				'ok': self.KeyOk,
				'left': self.key_left,
				'right': self.key_right,
				'up': self.key_up,
				'down': self.key_down
			},
			-1
		)

		self['frame'] = MovingPixmap()
		for x in range(self.thumbsC):
			self['label' + str(x)] = StaticText()
			self['thumb' + str(x)] = Pixmap()

		self.Thumbnaillist = []
		self.filelist = []
		self.currPage = -1
		self.dirlistcount = 0
		self.path = path
		index = 0
		framePos = 0
		Page = 0
		for x in piclist:
			if x:
				self.filelist.append((
					index,
					framePos,
					Page,
					x,
					path + x
				))
				index += 1
				framePos += 1
				if framePos > self.thumbsC - 1:
					framePos = 0
					Page += 1
			else:
				self.dirlistcount += 1

		self.maxentry = len(self.filelist) - 1
		self.index = int(lastindex) - self.dirlistcount
		if self.index < 0:
			self.index = 0
		print('init self.index=', self.index)
		self.picload = ePicLoad()
		if self.picload.PictureData is not None:
			try:
				self.picload.PictureData.get().append(self.showPic)
				print("sgrabberPic_Thumb PicLoad_conn startDecode")
			except:
				self.picload_conn = self.picload.PictureData.connect(self.showPic)
				print("sgrabberPic_Thumb PicLoad.PictureData startDecode")
		self.onLayoutFinish.append(self.setPicloadConf)
		self.ThumbTimer = eTimer()
		if file_exists('/var/lib/dpkg/status'):
			self.ThumbTimer_conn = self.ThumbTimer.timeout.connect(self.showPic)
		else:
			self.ThumbTimer.callback.append(self.showPic)

	def setPicloadConf(self):
		sc = getScale()
		scale_x = sc[0] if isinstance(sc[0], (int, float)) else 1
		scale_y = sc[1] if isinstance(sc[1], (int, float)) else 1
		try:
			self.picload.setPara([
				self['thumb0'].instance.size().width(),
				self['thumb0'].instance.size().height(),
				scale_x,
				scale_y,
				cfg.cache.value,
				int(cfg.resize.value),
				self.color
			])
		except Exception as e:
			print("Errore durante setPara sgrabberPic_Thumb:", e)
			return

		self.paintFrame()

	def paintFrame(self):
		if self.maxentry < self.index or self.index < 0:
			return
		pos = self.positionlist[self.filelist[self.index][T_FRAME_POS]]
		self['frame'].moveTo(pos[0], pos[1], 1)
		self['frame'].startMoving()
		if self.currPage is not self.filelist[self.index][T_PAGE]:
			self.currPage = self.filelist[self.index][T_PAGE]
			self.newPage()

	def newPage(self):
		self.Thumbnaillist = []
		for x in range(self.thumbsC):
			self['label' + str(x)].setText('')
			self['thumb' + str(x)].hide()

		for x in self.filelist:
			if x[T_PAGE] is self.currPage:
				self['label' + str(x[T_FRAME_POS])].setText('(' + str(x[T_INDEX] + 1) + ') ' + x[T_NAME])
				self.Thumbnaillist.append([0, x[T_FRAME_POS], x[T_FULL]])

		self.showPic()

	def showPic(self, picInfo=''):
		for x in range(len(self.Thumbnaillist)):
			img_path = self.Thumbnaillist[x][2]
			if not file_exists(img_path):
				print("Errore: Il file non esiste.", img_path)
				return
			if self.Thumbnaillist[x][0] == 0:
				result = self.picload.getThumbnail(img_path)
				if result == 1:
					# print('result=', result)
					self.ThumbTimer.start(500, True)
				elif result == -1:
					print("Errore nel caricamento della miniatura per {img_path}")
					return
				else:
					self.Thumbnaillist[x][0] = 1
				break
			elif self.Thumbnaillist[x][0] == 1:
				self.Thumbnaillist[x][0] = 2
				ptr = self.picload.getData()
				if ptr is None:
					print("Errore: self.PicLoad.getData() ha restituito None")
					return
				try:
					self['thumb' + str(self.Thumbnaillist[x][1])].instance.setPixmap(ptr)
					self['thumb' + str(self.Thumbnaillist[x][1])].show()
				except Exception as e:
					print("Errore durante setPixmap:", e)
		return

	def key_left(self):
		self.index -= 1
		if self.index < 0:
			self.index = self.maxentry
		self.paintFrame()

	def key_right(self):
		self.index += 1
		if self.index > self.maxentry:
			self.index = 0
		self.paintFrame()

	def key_up(self):
		self.index -= self.thumbsX
		if self.index < 0:
			self.index = self.maxentry
		self.paintFrame()

	def key_down(self):
		self.index += self.thumbsX
		if self.index > self.maxentry:
			self.index = 0
		self.paintFrame()

	def KeyOk(self):
		if self.maxentry < 0:
			return
		self.old_index = self.index
		print('init self.old_index=', self.old_index)
		self.session.openWithCallback(self.callbackView, sgrabberPic_Full_View, self.filelist, self.index, self.path)

	def callbackView(self, val=0):
		self.index = val
		if self.old_index is not self.index:
			self.paintFrame()

	def Exit(self):
		del self.picload
		self.remove_thumbails()
		self.close(self.index + self.dirlistcount)

	def remove_thumbails(self):
		import os
		import glob
		thumbnail_dir = glob.glob(self.path)
		thumbnail_dir = str(thumbnail_dir[0]) + '.Thumbnails'
		if os.path.exists(thumbnail_dir) and os.path.isdir(thumbnail_dir):
			for filename in os.listdir(thumbnail_dir):
				file_path = join(thumbnail_dir, filename)
				try:
					if os.path.isfile(file_path):
						remove(file_path)
				except Exception as e:
					print('Errore durante la rimozione del file {file_path}:', e)
		else:
			print('La cartella non esiste')


class sgrabberPic_Full_View(Screen):

	def __init__(self, session, filelist, index, path):
		self.textcolor = cfg.textcolor.value
		self.bgcolor = cfg.bgcolor.value
		space = cfg.framesize.value
		size_w = getDesktop(0).size().width()
		size_h = getDesktop(0).size().height()

		skinpaint = '<screen position="0,0" size="' + str(size_w) + ',' + str(size_h) + '" flags="wfNoBorder" >\n'
		skinpaint += '<eLabel position="0,0" zPosition="0" size="' + str(size_w) + ',' + str(size_h) + '" backgroundColor="' + self.bgcolor + '" />\n'
		skinpaint += '<widget name="pic" position="' + str(space) + ',' + str(space) + '" size="' + str(size_w - space * 2) + ',' + str(size_h - space * 2) + '" zPosition="1" alphatest="on" />\n'
		skinpaint += '<widget name="point" position="' + str(space + 5) + ',' + str(space + 2) + '" size="20,20" zPosition="2" pixmap="skin_default/icons/record.png" alphatest="on" />\n'
		skinpaint += '<widget name="play_icon" position="' + str(space + 25) + ',' + str(space + 2) + '" size="20,20" zPosition="2" pixmap="skin_default/icons/ico_mp_play.png"  alphatest="on" />\n'
		skinpaint += '<widget name="play_icon_show" position="' + str(space + 25) + ',' + str(space + 2) + '" size="20,20" zPosition="2" pixmap="skin_default/icons/ico_mp_play.png"  alphatest="on" />\n'
		skinpaint += '<widget source="file" render="Label" position="' + str(space + 45) + ',' + str(space) + '" size="' + str(size_w - space * 2 - 50) + ',25" font="Regular;20"   halign="left" foregroundColor="' + self.textcolor + '" zPosition="2" noWrap="1" transparent="1" />\n'
		skinpaint += '</screen>\n'
		self.skin = skinpaint

		Screen.__init__(self, session)
		self['actions'] = ActionMap(
			[
				'OkCancelActions',
				'ColorActions',
				'DirectionActions',
				'MovieSelectionActions'
			],
			{
				'cancel': self.Exit,
				'green': self.PlayPause,
				'yellow': self.PlayPause,
				'blue': self.nextPic,
				'red': self.prevPic,
				'left': self.prevPic,
				'right': self.nextPic
			},
			-1
		)

		self['point'] = Pixmap()
		self['pic'] = Pixmap()
		self['play_icon'] = Pixmap()
		self['play_icon_show'] = Pixmap()
		self['file'] = StaticText(_('please wait, loading picture...'))
		self.old_index = 0
		self.filelist = []
		self.lastindex = index
		self.currPic = []
		self.shownow = True
		self.dirlistcount = 0
		for x in filelist:
			if len(filelist[0]) == 3:
				if x[0][1] is False:
					self.filelist.append(path + x[0][0])
				else:
					self.dirlistcount += 1
			elif len(filelist[0]) == 2:
				if x[0][1] is False:
					self.filelist.append(x[0][0])
				else:
					self.dirlistcount += 1
			else:
				self.filelist.append(x[T_FULL])

		self.maxentry = len(self.filelist) - 1
		self.index = index - self.dirlistcount
		if self.index < 0:
			self.index = 0
		self.picload = ePicLoad()
		try:
			self.picload.PictureData.get().append(self.finish_decode)
		except:
			self.picload_conn = self.picload.PictureData.connect(self.finish_decode)

		self.slideTimer = eTimer()
		if file_exists('/var/lib/dpkg/status'):
			self.slideTimer_conn = self.slideTimer.timeout.connect(self.slidePic)
		else:
			self.slideTimer.callback.append(self.slidePic)
		self.slideTimer.start(500, True)

		if self.maxentry >= 0:
			self.onLayoutFinish.append(self.setPicloadConf)

	def setPicloadConf(self):
		sc = getScale()
		if sc is None or len(sc) < 2:
			print("Errore: getScale() ha restituito un valore non valido")
			return
		scale_x = sc[0] if isinstance(sc[0], (int, float)) else 1
		scale_y = sc[1] if isinstance(sc[1], (int, float)) else 1
		if self['pic'].instance is None:
			print("Errore: self['pic'].instance è None")
			return
		self.picload.setPara([
			self['pic'].instance.size().width(),
			self['pic'].instance.size().height(),
			scale_x,
			scale_y,
			cfg.cache.value,
			int(cfg.resize.value),
			self.bgcolor
		])

		self['play_icon'].hide()
		self['play_icon_show'].hide()
		if cfg.infoline.value is False:
			self['file'].setText('')
		self.start_decode()

	def ShowPicture(self):
		if self.shownow and len(self.currPic):
			self.shownow = False
			self['file'].setText(self.currPic[0])
			self.lastindex = self.currPic[1]
			if self.currPic[2] is not None:
				self['pic'].instance.setPixmap(self.currPic[2])
			else:
				print("Errore: Immagine non trovata.")
			self.currPic = []
			self.next()
			self.start_decode()

	def finish_decode(self, picInfo=''):
		self['point'].hide()
		ptr = self.picload.getData()
		if ptr is None:
			return
		text = ''
		try:
			text = picInfo.split('\n', 1)
			text = '(' + str(self.index + 1) + '/' + str(self.maxentry + 1) + ') ' + text[0].split('/')[-1]
		except:
			pass

		self.currPic = []
		self.currPic.append(text)
		self.currPic.append(self.index)
		self.currPic.append(ptr)
		self.ShowPicture()
		return

	def start_decode(self):
		if 0 <= self.index < len(self.filelist) and self.filelist[self.index]:
			self.picload.startDecode(self.filelist[self.index])
			self['point'].show()
			self['play_icon_show'].show()
		else:
			print("Errore: Indice non valido o file non trovato.")

	def next(self):
		self.index += 1
		if self.index > self.maxentry:
			self.index = 0

	def prev(self):
		self.index -= 1
		if self.index < 0:
			self.index = self.maxentry

	def slidePic(self):
		print(("slide to next Picture index=") + str(self.lastindex))
		if cfg.loop.value is False and self.lastindex is self.maxentry:
			self.PlayPause()
		self.shownow = True
		self.ShowPicture()

	def PlayPause(self):
		if self.slideTimer.isActive():
			self.slideTimer.stop()
			self['play_icon'].hide()
			self['play_icon_show'].hide()
		else:
			self.slideTimer.start(cfg.slidetime.value * 1000)
			self['play_icon'].show()
			self['play_icon_show'].hide()
			self.nextPic()

	def prevPic(self):
		self.currPic = []
		self.index = self.lastindex
		self.prev()
		self.start_decode()
		self.shownow = True

	def nextPic(self):
		self.shownow = True
		self.ShowPicture()

	def Exit(self):
		del self.picload
		self.close(self.lastindex + self.dirlistcount)
