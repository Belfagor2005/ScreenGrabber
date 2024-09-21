#!/usr/bin/python
# -*- coding: utf-8 -*-

# ScreenGrabber V.%s mfaraj - Mod. by Lululla
# all remake for py3 and major fix from @lululla 20240915
# fixed lululla for dreamos 20240918
from __future__ import print_function

from . import _, OnclearMem

try:
    from Components.AVSwitch import AVSwitch
except ImportError:
    from Components.AVSwitch import eAVControl as AVSwitch
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.config import (
    config,
    getConfigListEntry,
    ConfigSubsection,
    ConfigSelection,
    configfile,
    ConfigInteger,
    ConfigEnableDisable,
    ConfigText,
)
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from GlobalActions import globalActionMap
from Screens.Standby import TryQuitMainloop
from Tools.Directories import fileExists
from Tools.Directories import resolveFilename, SCOPE_MEDIA
from Tools.Notifications import AddNotification
from os.path import exists as file_exists
from datetime import datetime
from keymapparser import readKeymap
import sys
import os
import time
from enigma import (
    getDesktop,
    ePicLoad,
    eConsoleAppContainer,
)
from os import (
    remove,
    listdir,
    path,
    makedirs,
)


PY3 = sys.version_info[0] == 3

global globalActionMap
global xfilename
global screenshot_folder
size_w = getDesktop(0).size().width()
size_h = getDesktop(0).size().height()


def makedir(path):
    try:
        makedirs(path)
        return True
    except:
        return False


def getScale():
    return AVSwitch().getFramebufferScale()


def getMountedDevs():
    from Tools.Directories import resolveFilename, SCOPE_MEDIA
    from Components.Harddisk import harddiskmanager

    def handleMountpoint(loc):
        mp = loc[0]
        desc = loc[1]
        return (mp, desc + ' (' + mp + ')')

    mountedDevs = [(resolveFilename(SCOPE_MEDIA, 'hdd'), _('Harddisk')),
                   (resolveFilename(SCOPE_MEDIA, 'usb'), _('USB Device'))]
    mountedDevs += [(p.mountpoint, _(p.description) if p.description else '') for p in harddiskmanager.getMountedPartitions(True)]
    mountedDevs = [path for path in mountedDevs if os.path.isdir(path[0]) and os.access(path[0], os.W_OK | os.X_OK)]
    netDir = resolveFilename(SCOPE_MEDIA, 'net')
    if os.path.isdir(netDir):
        mountedDevs += [(os.path.join(netDir, p), _('Network mount')) for p in os.listdir(netDir)]
    mountedDevs += [(os.path.join('/', 'tmp'), _('Tmp Folder'))]
    mountedDevs = list(map(handleMountpoint, mountedDevs))
    return mountedDevs


currversion = '3.1'


'''
# FOR DREAMBOX
# -h, --help            show this help message and exit
# -f FILENAME, --filename FILENAME
                    # filename for the screenshot (requires full path)
                    # (default: /tmp/screenshot.png)
# -iw WIDTH, --width WIDTH
                    # image width. 0 for original size (default: 0)
# -ih HEIGHT, --height HEIGHT
                    # image height. 0 for original size (default: 0)
# -d DESKTOP, --desktop DESKTOP
                    # desktop to take a screenshot of. 0 for TV, 1 for
                    # display (default: 0)
# -m MODE, --mode MODE  capture mode, values: osd, video, combined (default:
                    # combined)
'''


config.sgrabber = ConfigSubsection()
cfg = config.sgrabber
cfg.framesize = ConfigInteger(default=50, limits=(5, 99))
cfg.slidetime = ConfigInteger(default=10, limits=(1, 60))
cfg.resize = ConfigSelection(default='1', choices=[('0', _('simple')), ('1', _('better'))])
cfg.cache = ConfigEnableDisable(default=True)
cfg.lastDir = ConfigText(default=resolveFilename(SCOPE_MEDIA))
cfg.infoline = ConfigEnableDisable(default=True)
cfg.loop = ConfigEnableDisable(default=True)
cfg.bgcolor = ConfigSelection(default='#00000000', choices=[('#ff000000', _('trasparent')),
                                                                    ('#00000000', _('black')),
                                                                    ('#009eb9ff', _('blue')),
                                                                    ('#00ff5a51', _('red')),
                                                                    ('#00ffe875', _('yellow')),
                                                                    ('#0038FF48', _('green'))])
cfg.textcolor = ConfigSelection(default='#00ffe875', choices=[('#ff000000', _('trasparent')),
                                                                      ('#00000000', _('black')),
                                                                      ('#009eb9ff', _('blue')),
                                                                      ('#00ff5a51', _('red')),
                                                                      ('#00ffe875', _('yellow')),
                                                                      ('#0038FF48', _('green'))])


if file_exists('/var/lib/dpkg/status'):
    cfg.fixedaspectratio = ConfigSelection(default='Disabled', choices=[('Disabled', _('Off'))])
    cfg.always43 = ConfigSelection(default='Disabled', choices=[('Disabled', _('Off'))])
    cfg.bicubic = ConfigSelection(default='Disabled', choices=[('Disabled', _('Off'))])
    cfg.storedir = ConfigSelection(choices=getMountedDevs())
    cfg.formatp = ConfigSelection(default='Disabled', choices=[('Disabled', _('Off'))])
    cfg.items = ConfigSelection(default='-m combined', choices=[('-m combined', _('Grab All')),
                                                                                    ('-m osd', _('OSD only')),
                                                                                    ('-m video', _('VIDEO only')),
                                                                                    ('Disabled', _('Off'))])

    cfg.newsize = ConfigSelection(default='Disabled', choices=[('Disabled', _('Skin resolution'))])
    cfg.scut = ConfigSelection(default='green', choices=[('text', _('Text')),
                                                                             ('help', _('Help')),
                                                                             ('info', _('Info')),
                                                                             ('green', _('Long green')),
                                                                             ('red', _('Long red')),
                                                                             ('video', _('Video')),
                                                                             ('mute', _('Mute')),
                                                                             ('radio', _('Radio'))])
else:
    cfg.fixedaspectratio = ConfigSelection(default='Disabled', choices=[('-n', _('Enabled')), ('Disabled', _('Off'))])
    cfg.always43 = ConfigSelection(default='Disabled', choices=[('-l', _('Enabled')), ('Disabled', _('Off'))])
    cfg.bicubic = ConfigSelection(default='Disabled', choices=[('-b', _('Enabled')), ('Disabled', _('Off'))])
    cfg.storedir = ConfigSelection(choices=getMountedDevs())
    cfg.formatp = ConfigSelection(default='-p', choices=[('-j 100', _('jpg100')),
                                                                             ('-j 80', _('jpg80')),
                                                                             ('-j 60', _('jpg60')),
                                                                             ('-j 40', _('jpg40')),
                                                                             ('-j 20', _('jpg20')),
                                                                             ('-j 10', _('jpg20')),
                                                                             ('bmp', _('BMP')),
                                                                             ('-p', _('PNG'))])
    cfg.items = ConfigSelection(default='Disabled', choices=[('All', _('Grab All')),
                                                                                 ('-v', _('Video only')),
                                                                                 ('-o', _('OSD only')),
                                                                                 ('Disabled', _('Off'))])
    cfg.newsize = ConfigSelection(default='Disabled', choices=[('-r1920', _('1920*1080')),
                                                                                   ('-r800', _('800*450')),
                                                                                   ('-r600', _('600*337')),
                                                                                   ('Disabled', _('Skin resolution'))])
    cfg.scut = ConfigSelection(default='green', choices=[('text', _('Text')),
                                                                             ('help', _('Help')),
                                                                             ('info', _('Info')),
                                                                             ('green', _('Long green')),
                                                                             ('red', _('Long red')),
                                                                             ('video', _('Video')),
                                                                             ('mute', _('Mute')),
                                                                             ('radio', _('Radio'))])

srootfolder = cfg.storedir.value
if path.exists(srootfolder + "/screenshots/"):
    print('srootfolder + /screenshots/ exist')
else:
    makedirs(srootfolder + "/screenshots/")
    print('makedir: srootfolder + /screenshots/ exist')
screenshot_folder = os.path.join(srootfolder, "screenshots")


def checkfolder(folder):
    if path.exists(folder):
        return True
    else:
        return False


def getFilename():
    global xfilename
    now = time.time()
    now = datetime.fromtimestamp(now)
    now = now.strftime("%Y-%m-%d_%H-%M-%S")
    fileextension = '.png'
    format_value = cfg.formatp.value if cfg.formatp.value != 'Disabled' else cfg.formatp.value
    if not file_exists('/var/lib/dpkg/status'):
        if "-j" in format_value:
            fileextension = ".jpg"
        elif format_value == "bmp":
            fileextension = ".bmp"
        elif format_value == "-p":
            fileextension = ".png"

    screenshottime = "screenshot_" + now
    picturepath = getPicturePath()
    screenshotfile = os.path.join(picturepath, screenshottime + fileextension)
    xfilename = screenshotfile
    return screenshotfile


def getPicturePath():
    picturepath = cfg.storedir.value
    picturepath = os.path.join(picturepath, 'screenshots')
    try:
        if not os.path.exists(picturepath):
            os.makedirs(picturepath)
    except OSError:
        msg_text = _("Sorry, your device for screenshots is not writable.\n\nPlease choose another one.")
        msg_type = MessageBox.TYPE_ERROR
        if msg_text:
            AddNotification(MessageBox, str(msg_text), msg_type, timeout=5)
    return picturepath


class GrabPreview(Screen):
    skin = '<screen name="GrabPreview" flags="wfNoBorder" position="center,center" size="%d,%d" title="GrabPreview" backgroundColor="transparent" >\n' % (size_w, size_h)
    skin += '<widget name="pixmap" position="0,0" size="%d,%d" zPosition="4" alphatest="blend"/>\n' % (size_w, size_h)
    skin += '<eLabel name="" position="17,15" size="300,55" font="Regular;24" backgroundColor="#00640808" foregroundColor="#fcc000" halign="center" valign="center" transparent="1" text="Please wait....." zPosition="9" />\n'
    skin += '<eLabel name="" position="790,15" size="160,55" font="Regular; 24" foregroundColor="#fcc000" halign="center" valign="center" transparent="1" text="Exit=Play TV" zPosition="9" />\n'
    skin += '</screen>\n'
    # print('skin GrabPreview:\n', skin)

    def __init__(self, session, previewPng=None):
        Screen.__init__(self, session)
        self.skin = GrabPreview.skin
        self.session = session
        self.Scale = getScale()
        self.PicLoad = ePicLoad()
        self.previewPng = previewPng
        print('self.previewPng=', previewPng)
        self['pixmap'] = Pixmap()
        try:
            self.PicLoad.PictureData.get().append(self.DecodePicture)
        except:
            self.PicLoad_conn = self.PicLoad.PictureData.connect(self.DecodePicture)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'ok': self.close,
                                                       'cancel': self.close,
                                                       'blue': self.close}, -1)
        self.onLayoutFinish.append(self.ShowPicture)

    def ShowPicture(self, data=None):
        print('data: ', data)
        print('self.previewPng: ', self.previewPng)
        if self.previewPng is not None:
            '''
            if path.isfile(self.previewPng):
            if isinstance(size_w, tuple) or isinstance(size_h, tuple):
                # print("Error: size_w or size_h is a tuple, expected integers.")
                return
            '''
            scale_x = self.Scale[0] if isinstance(self.Scale[0], (int, float)) else 1
            scale_y = self.Scale[1] if isinstance(self.Scale[1], (int, float)) else 1
            self.PicLoad.setPara([self['pixmap'].instance.size().width(),
                                  self['pixmap'].instance.size().height(),
                                  scale_x,
                                  scale_y,
                                  0,
                                  1,
                                  '#002C2C39'])
            try:
                if self.PicLoad.startDecode(self.previewPng):
                    self.PicLoad = ePicLoad()
                    try:
                        self.PicLoad.PictureData.get().append(self.DecodePicture)
                    except:
                        self.PicLoad_conn = self.PicLoad.PictureData.connect(self.DecodePicture)
                return
            except Exception as e:
                print('set para error:', str(e))
                import traceback
                traceback.print_exc()
            return

    def DecodePicture(self, PicInfo=None):
        print('are to DecodeAction!')
        if not fileExists(self.previewPng):
            print("Errore: Il file", self.previewPng, "non esiste")
            return
        ptr = self.PicLoad.getData()
        if ptr is None:
            print("Errore: self.PicLoad.getData() ha restituito None")
            return
        try:
            self["pixmap"].instance.setPixmap(ptr)
            self["pixmap"].instance.show()
            print('are to instance.show!')
        except Exception as e:
            print("Errore durante setPixmap:", e)
        return


class sgrabberFilesScreen(Screen):

    skin = '''<screen name="sgrabberFilesScreen" position="center,center" size="1280,720" title="Screenshot Files" flags="wfNoBorder">
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/images/framesd.png" position="0,0" alphatest="blend" size="1280,720" scale="stretch" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/images/slider.png" position="40,60" alphatest="blend" size="600,6"/>
                <widget name="pixmap" position="682,126" size="550,350" zPosition="9" alphatest="blend" scale="stretch" />
                <widget name="menu" position="42,72" size="600,500" scrollbarMode="showOnDemand" transparent="1" zPosition="2" font="Regular; 30" itemHeight="50" />
                <widget name="info" position="44,581" zPosition="4" size="1189,55" font="Regular;28" foregroundColor="yellow" transparent="1" halign="center" valign="center" />
                <eLabel backgroundColor="#00ff0000" position="45,680" size="300,6" zPosition="12" />
                <eLabel backgroundColor="#00ffff00" position="643,680" size="300,6" zPosition="12" />
                <eLabel backgroundColor="#000000ff" position="944,680" size="300,6" zPosition="12" />
                <eLabel backgroundColor="#0000ff00" position="345,680" size="300,6" zPosition="12" />
                <widget name="ButtonYellowtext" position="644,640" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                <widget name="ButtonBluetext" position="944,640" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                <widget name="ButtonGreentext" position="345,640" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                <widget name="ButtonRedtext" position="45,640" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
            </screen>'''

    if file_exists('/var/lib/dpkg/status'):
        skin = '''<screen name="sgrabberFilesScreen" position="center,center" size="1280,720" title="Screenshot Files" flags="wfNoBorder">
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/images/framesd.png" position="0,0" alphatest="blend" size="1280,720" scale="stretch" />
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/images/slider.png" position="40,60" alphatest="blend" size="600,6"/>
                    <widget name="pixmap" position="682,126" size="550,350" zPosition="9" alphatest="blend" scale="stretch" />
                    <widget name="menu" position="42,72" size="600,500" scrollbarMode="showOnDemand" transparent="1" zPosition="2" itemHeight="50" />
                    <widget name="info" position="44,581" zPosition="4" size="1189,55" font="Regular;28" foregroundColor="yellow" transparent="1" halign="center" valign="center" />
                    <eLabel backgroundColor="#00ff0000" position="45,680" size="300,6" zPosition="12" />
                    <eLabel backgroundColor="#00ffff00" position="643,680" size="300,6" zPosition="12" />
                    <eLabel backgroundColor="#000000ff" position="944,680" size="300,6" zPosition="12" />
                    <eLabel backgroundColor="#0000ff00" position="345,680" size="300,6" zPosition="12" />
                    <widget name="ButtonYellowtext" position="644,640" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget name="ButtonBluetext" position="944,640" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget name="ButtonGreentext" position="345,640" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget name="ButtonRedtext" position="45,640" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                </screen>'''

    def __init__(self, session):
        self.skin = sgrabberFilesScreen.skin
        Screen.__init__(self, session)
        list = []
        self['menu'] = MenuList(list)
        self['ButtonBluetext'] = Label(_('Preview'))
        self['ButtonYellowtext'] = Label(_('Delete'))
        self['ButtonGreentext'] = Label(_('Picview'))
        self['ButtonRedtext'] = Label(_('Back'))
        self['pixmap'] = Pixmap()
        self['info'] = Label()
        self.PicLoad = ePicLoad()
        self.scale = getScale()
        try:
            self.PicLoad.PictureData.get().append(self.DecodePicture)
        except:
            self.PicLoad_conn = self.PicLoad.PictureData.connect(self.DecodePicture)
        self.folder = cfg.storedir.value + '/screenshots/'
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'ColorActions'], {'yellow': self.removefile,
                                                                                              'blue': self.key_ok,
                                                                                              'green': self.onFileAction,
                                                                                              'red': self.close,
                                                                                              "up": self.up,
                                                                                              "down": self.down,
                                                                                              "left": self.left,
                                                                                              "right": self.right,
                                                                                              'ok': self.key_ok,
                                                                                              'cancel': self.close}, -2)
        self.fillplgfolders()
        self.onLayoutFinish.append(self.ShowPicture)

    def removefile(self):
        self['info'].setText('')
        try:
            fname = self['menu'].getCurrent()
            filename = self.folder + fname
            if filename is not None:
                remove(filename)
            self.fillplgfolders()
        except:
            self['info'].setText('unable to delete file')

    def onFileAction(self):
        self['info'].setText('')
        try:
            from .picplayer import sgrabberPic_Thumb
            self.session.open(sgrabberPic_Thumb, self.fullpath, 0, self.folder)
        except TypeError as e:
            self['info'].setText('unable to preview file')
            print('error:', e)

    def fillplgfolders(self):
        self['info'].setText('')
        plgfolders = []
        fullpath = []
        if checkfolder(self.folder):
            for x in listdir(self.folder):
                if path.isfile(self.folder + x):
                    if x.endswith('.jpg') or x.endswith('.png') or x.endswith('.bmp') or x.endswith('.gif'):
                        plgfolders.append(x)
                        fullpath.append(x)

        self['menu'].setList(plgfolders)
        self.fullpath = fullpath

    def up(self):
        try:
            self['menu'].up()
            self.ShowPicture()
        except Exception as e:
            print(e)

    def down(self):
        try:
            self['menu'].down()
            self.ShowPicture()
        except Exception as e:
            print(e)

    def left(self):
        try:
            self['menu'].pageUp()
            self.ShowPicture()
        except Exception as e:
            print(e)

    def right(self):
        try:
            self['menu'].pageDown()
            self.ShowPicture()
        except Exception as e:
            print(e)

    def key_ok(self):
        fname = self['menu'].getCurrent()
        filename = self.folder + fname
        print('filename ok=', filename)
        if filename is not None:
            self.session.open(GrabPreview, filename)

    def ShowPicture(self, data=None):
        fname = self['menu'].getCurrent()
        filename = self.folder + str(fname)
        print('key_ok name files:', filename)
        print('data: ', data)
        if path.isfile(filename):
            print('filename 2: ', filename)
            try:
                if isinstance(size_w, tuple) or isinstance(size_h, tuple):
                    print("Error: size_w or size_h is a tuple, expected integers.")
                    return
                width = 550  # size_w
                height = 350  # size_h
                scale_x = self.scale[0] if isinstance(self.scale[0], (int, float)) else 1
                scale_y = self.scale[1] if isinstance(self.scale[1], (int, float)) else 1
                self.PicLoad.setPara([width, height, scale_x, scale_y, 0, 1, "#ff000000"])
                if self.PicLoad.startDecode(filename):
                    self.PicLoad = ePicLoad()
                    try:
                        self.PicLoad.PictureData.get().append(self.DecodePicture)
                    except:
                        self.PicLoad_conn = self.PicLoad.PictureData.connect(self.DecodePicture)
                return
            except Exception as e:
                print('set para error:', str(e))
                import traceback
                traceback.print_exc()
            return

    def DecodePicture(self, PicInfo=None):
        ptr = self.PicLoad.getData()
        if ptr is not None:
            self["pixmap"].instance.setPixmap(ptr)
            self["pixmap"].instance.show()
        return


class sgrabberScreenGrabberView(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        global xfilename
        self.myConsole = Console()
        nowService = session.nav.getCurrentlyPlayingServiceReference()
        self.nowService = nowService
        # self.srvName = ServiceReference(session.nav.getCurrentlyPlayingServiceReference()).getServiceName()
        # session.nav.stopService() paused  screen black!
        self.srvName = 'ScreenGrabber'
        cmd = "grab"
        if file_exists('/var/lib/dpkg/status'):
            cmd = "dreamboxctl screenshot"

        cmdoptiontype = str(cfg.items.value) if cfg.items.value != "All" else cfg.items.value
        cmdoptionsize = str(cfg.newsize.value)
        cmdoptionformat = str(cfg.formatp.value)
        fixedaspectratio = str(cfg.fixedaspectratio.value)
        always43 = str(cfg.always43.value)
        bicubic = str(cfg.bicubic.value)

        def append_if_not_disabled(cmd, option_value, option_name):
            if option_value != 'Disabled':
                return cmd + ' ' + option_name
            return cmd

        cmd = append_if_not_disabled(cmd, cfg.items.value, cmdoptiontype)
        cmd = append_if_not_disabled(cmd, cfg.newsize.value, cmdoptionsize)

        if cfg.formatp.value != 'Disabled' and cfg.formatp.value != 'bmp':
            cmd += ' ' + cmdoptionformat
        cmd = append_if_not_disabled(cmd, fixedaspectratio, fixedaspectratio)
        cmd = append_if_not_disabled(cmd, always43, always43)
        cmd = append_if_not_disabled(cmd, bicubic, bicubic)
        cmd = cmd.strip()

        extra_args = None  # self.pictureformat
        self.myConsole.ePopen(cmd, self.gotScreenshot, extra_args)
        self.whatPic = xfilename
        print('dopo grab myConsole whatPic 2 =', str(self.whatPic))
        # end test

        PreviewString = '<screen name="sgrabberScreenGrabberView" backgroundColor="#ff000000" flags="wfNoBorder" position="center,center" size="' + str(size_w) + ',' + str(size_h) + '" title="Preview">\n'
        PreviewString += '<widget name="Picture" position="0,0" size="' + str(size_w) + ',' + str(size_h) + '" zPosition="2" alphatest="blend" scale="stretch" />\n'
        PreviewString += '<eLabel font="Regular;24" backgroundColor="#00640808" halign="center" valign="center" transparent="0" position="17,15" size="300,55" text="For dreamos - Button OK" zPosition="9" />\n'
        PreviewString += '<eLabel name="" position="317,15" size="160,55" halign="center" valign="center" transparent="0" font="Regular; 22" zPosition="9" text="OK=Save" backgroundColor="#01080911" foregroundColor="#fcc000" />\n'
        PreviewString += '<eLabel name="" position="477,15" size="160,55" halign="center" valign="center" transparent="0" font="Regular; 22" zPosition="9" text="Green=Setup" backgroundColor="#01080911" foregroundColor="#fcc000" />\n'
        PreviewString += '<eLabel name="" position="637,15" size="160,55" halign="center" valign="center" transparent="0" font="Regular; 22" zPosition="9" text="Yellow=Files TV" backgroundColor="#01080911" foregroundColor="#fcc000" />\n'
        PreviewString += '<eLabel name="" position="797,15" size="160,55" halign="center" valign="center" transparent="0" font="Regular; 22" zPosition="9" text="Exit=Play TV" backgroundColor="#01080911" foregroundColor="#fcc000" />\n'
        PreviewString += '</screen>\n'
        self.skin = PreviewString
        print('self.skin sgrabberScreenGrabberView:\n', self.skin)
        self['Picture'] = Pixmap()
        self.EXscale = getScale()
        self.EXpicload = ePicLoad()
        try:
            self.EXpicload.PictureData.get().append(self.DecodeAction)
        except:
            self.EXpicload_conn = self.EXpicload.PictureData.connect(self.DecodeAction)

        self['actions'] = ActionMap(['WizardActions', 'ColorActions'], {'ok': self.SavePic,  # dexit
                                                                        'back': self.dexit,
                                                                        'green': self.showsetup,
                                                                        'yellow': self.showfiles}, -1)
        print('sgrabberScreenGrabberView onLayoutFinish self.Show_Picture=', str(self.whatPic))
        self.onLayoutFinish.append(self.Show_Picture)

    def showsetup(self):
        self.session.open(sgrabberScreenGrabberSetup)
        self.dexit()

    def showfiles(self):
        self.session.open(sgrabberFilesScreen)
        '''
        # self.session.open(GrabPreview, self.pictureformat)
        # self.dexit()
        '''

    def dexit(self):
        self.session.nav.playService(self.nowService)
        OnclearMem()
        self.close()

    def Show_Picture(self):
        if fileExists(self.whatPic):
            print('--> Show_Picture whatPic 2=', str(self.whatPic))
        scale_x = self.EXscale[0] if isinstance(self.EXscale[0], (int, float)) else 1
        scale_y = self.EXscale[1] if isinstance(self.EXscale[1], (int, float)) else 1
        self.EXpicload.setPara([self['Picture'].instance.size().width(),
                                self['Picture'].instance.size().height(),
                                scale_x,
                                scale_y,
                                0,
                                1,
                                '#ff000000'])
        if self.EXpicload.startDecode(self.whatPic):
            self.EXpicload = ePicLoad()
            try:
                self.EXpicload.PictureData.get().append(self.DecodeAction)
            except:
                self.EXpicload_conn = self.EXpicload.PictureData.connect(self.DecodeAction)
        return

    def DecodeAction(self, PicInfo=None):
        print('--> DecodeAction PicInfo=', str(PicInfo))
        ptr = self.EXpicload.getData()
        if ptr is not None:
            self["Picture"].instance.setPixmap(ptr)
            self["Picture"].instance.show()

    def gotScreenshot(self, result, retval, extra_args=None):
        print('gotScreenshot extra_args:', extra_args)
        print('gotScreenshot retval=', retval)
        self.retvalmsg = extra_args
        self.session.openWithCallback(self.messagetext, GrabPreview, xfilename)

    def messagetext(self, callback=None):
        try:
            msg_text = None
            if 'screenshots' in self.retvalmsg:
                msg_text = _("Screenshot successfully saved as:\n%s") % xfilename
                msg_type = MessageBox.TYPE_INFO
            else:
                msg_text = _("Grabbing Screenshot failed !!!")
                msg_type = MessageBox.TYPE_ERROR
            if msg_text:
                AddNotification(MessageBox, str(msg_text), msg_type, timeout=5)
            else:
                pass
        except Exception as e:
            print(e)
        self.dexit()

    def SavePic(self):
        self.dexit()
        '''
        try:
            print('srootfolder=', srootfolder)
            # screenshot_folder = os.path.join(srootfolder, "screenshots")
            self.pictureformat = xfilename
            self.whatPic = self.whatPic  # .replace('/tmp/screenshots', screenshot_folder)
            print('SavePic /tmp self.pictureformat=', self.pictureformat)
            print('SavePic self.whatPic=', self.whatPic)
            cmnd = 'cp -f ' + xfilename + ' ' + self.whatPic
            print('cmnd copy=', cmnd)
            os.system(cmnd)
            print('FILE COPIATO')
            self.session.open(
                MessageBox,
                text=_("Screenshot saved to " + xfilename),
                type=MessageBox.TYPE_INFO,
                timeout=3,
                close_on_any_key=True
            )
        except Exception as e:
            self.session.open(
                MessageBox,
                text=_('Failed saving file: %s' % str(e)),
                type=MessageBox.TYPE_ERROR,
                timeout=5,
                close_on_any_key=True
            )
        self.dexit()
        '''


class classScreenGrabber:

    def __init__(self):
        self.dialog = None
        return

    def gotSession(self, session):
        global globalActionMap
        rcbutton = cfg.scut.value
        ScreenGrabber_keymap = '/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/keymaps/' + rcbutton + '_keymap.xml'
        self.session = session
        readKeymap(ScreenGrabber_keymap)
        globalActionMap.actions['ShowScreenGrabber'] = self.ShowHide

    def ShowHide(self):
        self.session.open(sgrabberScreenGrabberView)

# globalActionMap = ActionMap( ["GlobalActions"] )
# globalActionMap.execBegin()


class sgrabberScreenGrabberSetup(Screen, ConfigListScreen):
    skin = '''<screen name="sgrabberScreenGrabberSetup" position="center,center" size="1280,720" title="ScreebGrabber setup" flags="wfNoBorder">
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/images/framesd.png" position="0,0" size="1280,720" scale="stretch" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/images/iconafm.png" position="891,132" size="350,350" scale="stretch" zPosition="9" />
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/images/slider.png" position="40,60" size="820,6" alphatest="blend" zPosition="9" />
                <widget name="config" position="42,72" size="820,500" scrollbarMode="showOnDemand" transparent="1" zPosition="2" itemHeight="50" font="Regular;34" />
                <widget name="info" position="41,578" zPosition="4" size="1189,55" font="Regular;30" foregroundColor="yellow" transparent="1" halign="center" valign="center" />
                <eLabel backgroundColor="#00ff0000" position="39,680" size="300,6" zPosition="5" />
                <eLabel backgroundColor="#0000ff00" position="337,680" size="300,6" zPosition="12" />
                <eLabel backgroundColor="#00ffff00" position="638,680" size="300,6" zPosition="12" />
                <eLabel backgroundColor="#000000ff" position="939,680" size="300,6" zPosition="12" />
                <widget source="key_red" render="Label" position="37,640" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                <widget source="key_green" render="Label" position="338,640" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                <widget source="key_yellow" render="Label" position="638,640" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                <widget source="key_blue" render="Label" position="938,640" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
            </screen>'''

    if file_exists('/var/lib/dpkg/status'):
        skin = '''<screen name="sgrabberScreenGrabberSetup" position="center,center" size="1280,720" title="ScreebGrabber setup" flags="wfNoBorder">
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/images/framesd.png" position="0,0" size="1280,720" scale="stretch" />
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/images/iconafm.png" position="891,132" size="350,350" scale="stretch" zPosition="9" />
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/images/slider.png" position="35,60" size="845,6" alphatest="blend" zPosition="9" />
                    <widget name="config" position="37,72" size="845,500" scrollbarMode="showOnDemand" transparent="1" zPosition="2" itemHeight="50" />
                    <widget name="info" position="36,578" zPosition="4" size="1189,55" font="Regular;30" foregroundColor="yellow" transparent="1" halign="center" valign="center" />
                    <eLabel backgroundColor="#00ff0000" position="39,680" size="300,6" zPosition="5" />
                    <eLabel backgroundColor="#0000ff00" position="337,680" size="300,6" zPosition="12" />
                    <eLabel backgroundColor="#00ffff00" position="638,680" size="300,6" zPosition="12" />
                    <eLabel backgroundColor="#000000ff" position="939,680" size="300,6" zPosition="12" />
                    <widget source="key_red" render="Label" position="37,640" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_green" render="Label" position="338,640" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_yellow" render="Label" position="638,640" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_blue" render="Label" position="938,640" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                </screen>'''

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.createConfigList()
        ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
        self['key_red'] = StaticText(_('Cancel'))
        self['key_green'] = StaticText(_('Save'))
        self['key_yellow'] = StaticText(_('Files'))
        self['key_blue'] = StaticText(_('Files II'))
        self['info'] = Label('ScreenGrabber V.%s mfaraj - Mod. by Lululla' % currversion)
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions'], {'yellow': self.showfiles,
                                                                            'green': self.keySave,
                                                                            'blue': self.keyBlue,
                                                                            'cancel': self.keyClose}, -2)

    def createConfigList(self):
        self.list = []
        self.list.append(getConfigListEntry(_('ScreenShot:'), cfg.items))
        self.list.append(getConfigListEntry(_('Storing Folder:'), cfg.storedir))
        self.list.append(getConfigListEntry(_('Remote screenshot button:'), cfg.scut))
        self.list.append(getConfigListEntry(_('Picture size:'), cfg.newsize))
        self.list.append(getConfigListEntry(_('screenshot format/quality:'), cfg.formatp))
        self.list.append(getConfigListEntry(_('Fixed Aspect ratio:'), cfg.fixedaspectratio))
        self.list.append(getConfigListEntry(_('Fixed Aspect ratio 4:3:'), cfg.always43))
        self.list.append(getConfigListEntry(_('Bicubic picture resize:'), cfg.bicubic))
        # picview config --- add lululla
        self.list.append(getConfigListEntry(_('Picview Framesize:'), cfg.framesize))
        self.list.append(getConfigListEntry(_('Picview slidetime:'), cfg.slidetime))
        self.list.append(getConfigListEntry(_('Picview resize:'), cfg.resize))
        self.list.append(getConfigListEntry(_('Picview cache:'), cfg.cache))
        self.list.append(getConfigListEntry(_('Picview lastDir:'), cfg.lastDir))
        self.list.append(getConfigListEntry(_('Picview infoline:'), cfg.infoline))
        self.list.append(getConfigListEntry(_('Picview loop:'), cfg.loop))
        self.list.append(getConfigListEntry(_('Picview bgcolor:'), cfg.bgcolor))
        self.list.append(getConfigListEntry(_('Picview textcolor:'), cfg.textcolor))

        self.onitem = cfg.items.value
        self.scut = cfg.scut.value

    def keyBlue(self):
        self.session.open(sgrabberFilesScreen)

    def changedEntry(self):
        self.createConfigList()
        self["config"].setList(self.list)

    def showfiles(self):
        if checkfolder(str(self['config'].list[1][1].value)):
            self.folder = cfg.storedir.value + '/screenshots/'
            self.session.open(GrabPreviewII, None, self.folder)
        else:
            self.session.open(MessageBox, text=_('Storing directory is not available'), type=MessageBox.TYPE_INFO, timeout=3, close_on_any_key=True)

    def keySave(self):
        if checkfolder(str(self['config'].list[1][1].value)):
            for x in self['config'].list:
                x[1].save()
            configfile.save()
            self.changedEntry()
            if not self.onitem == cfg.items.value or not self.scut == cfg.scut.value:
                self.session.openWithCallback(self.restartenigma, MessageBox, _('Restart enigma2 to load new settings?'), MessageBox.TYPE_YESNO)
            else:
                self.close(True)
        else:
            self.session.open(MessageBox, text=_('Storing directory is not available'), type=MessageBox.TYPE_INFO, timeout=3, close_on_any_key=True)
            return

    def restartenigma(self, result):
        if result:
            self.session.open(TryQuitMainloop, 3)
        else:
            self.close(True)

    def keyClose(self):
        for x in self['config'].list:
            x[1].cancel()
        OnclearMem()
        self.close(False)


class GrabPreviewII(Screen):
    if (getDesktop(0).size().width()) > 1030:
        skin = """
            <screen name="GrabPreviewII" flags="wfNoBorder" position="228,57" size="1480,963" title="GrabPreview Explorer" backgroundColor="#00121214">
                <ePixmap position="87,75" size="1280,6" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/images/slider.png" alphatest="blend" transparent="1" backgroundColor="#ff000000" />
                <ePixmap position="87,800" size="1280,6" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/images/slider.png" alphatest="blend" transparent="1" backgroundColor="#ff000000" />
                <widget name="Picture" position="87,80" size="1280,720" zPosition="1" alphatest="on" scale="stretch"  />
                <widget name="menu" position="300,807" size="800,102" scrollbarMode="showOnDemand" transparent="1" zPosition="5" font="Regular; 34" itemHeight="50" />
                <widget name="State" font="Regular;32" halign="center" position="85,8" size="1280,70" backgroundColor="#01080911" foregroundColor="#fcc000" transparent="1" zPosition="5" />
                <eLabel name="" position="1350,895" size="55,55" halign="center" valign="center" transparent="0" cornerRadius="26" font="Regular; 22" zPosition="1" text="OK" backgroundColor="#01080911" foregroundColor="#fcc000" />
                <eLabel name="" position="1405,895" size="55,55" halign="center" valign="center" transparent="0" cornerRadius="26" font="Regular; 22" zPosition="1" text="EXIT" backgroundColor="#01080911" foregroundColor="#fcc000" />
                <eLabel backgroundColor="#00ffff00" position="1159,887" size="300,6" zPosition="12" />
                <widget name="ButtonYellowtext" position="1157,848" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
            </screen>"""
    else:
        skin = """
            <screen name="GrabPreviewII"  flags="wfNoBorder" position="320,150" size="1280,720" title="GrabPreview Explorer" backgroundColor="#00121214">
                <ePixmap position="228,70" size="850,6" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/images/slider.png" alphatest="blend" transparent="1" backgroundColor="#ff000000" />
                <ePixmap position="230,590" size="850,6" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/images/slider.png" alphatest="blend" transparent="1" backgroundColor="#ff000000" />
                <widget name="Picture" position="228,70" size="850,520" zPosition="1" alphatest="on" scale="stretch"  />
                <widget name="menu" position="355,600" size="600,105" scrollbarMode="showOnDemand" transparent="1" zPosition="5" font="Regular; 24" itemHeight="40" />
                <widget name="State" font="Regular;20" halign="center" position="1,-3" size="1280,70" backgroundColor="#01080911" foregroundColor="#fcc000" transparent="0" zPosition="5" />
                <eLabel name="" position="1025,650" size="55,55" halign="center" valign="center" transparent="0" cornerRadius="26" font="Regular; 22" zPosition="1" text="OK" backgroundColor="#01080911" foregroundColor="#fcc000" />
                <eLabel name="" position="1080,650" size="55,55" halign="center" valign="center" transparent="0" cornerRadius="26" font="Regular; 22" zPosition="1" text="EXIT" backgroundColor="#01080911" foregroundColor="#fcc000" />
                <eLabel backgroundColor="#00ffff00" position="965,643" size="250,6" zPosition="12" />
                <widget name="ButtonYellowtext" position="964,600" size="250,45" zPosition="11" font="Regular; 24" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
            </screen>"""

    if file_exists('/var/lib/dpkg/status'):
        if (getDesktop(0).size().width()) > 1030:
            skin = """
                <screen name="GrabPreviewII" flags="wfNoBorder" position="228,57" size="1480,963" title="GrabPreview Explorer" backgroundColor="#00121214">
                    <ePixmap position="87,75" size="1280,6" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/images/slider.png" alphatest="blend" transparent="1" backgroundColor="#ff000000" />
                    <ePixmap position="87,800" size="1280,6" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/images/slider.png" alphatest="blend" transparent="1" backgroundColor="#ff000000" />
                    <widget name="Picture" position="87,80" size="1280,720" zPosition="1" alphatest="on" scale="stretch" />
                    <widget name="menu" position="300,807" size="800,102" scrollbarMode="showOnDemand" transparent="1" zPosition="5" itemHeight="50" />
                    <widget name="State" font="Regular;32" halign="center" position="85,8" size="1280,70" backgroundColor="#01080911" foregroundColor="#fcc000" transparent="1" zPosition="5" />
                    <eLabel name="" position="1350,895" size="55,55" halign="center" valign="center" transparent="0" cornerRadius="26" font="Regular; 22" zPosition="1" text="OK" backgroundColor="#01080911" foregroundColor="#fcc000" />
                    <eLabel name="" position="1405,895" size="55,55" halign="center" valign="center" transparent="0" cornerRadius="26" font="Regular; 22" zPosition="1" text="EXIT" backgroundColor="#01080911" foregroundColor="#fcc000" />
                    <eLabel backgroundColor="#00ffff00" position="1159,887" size="300,6" zPosition="12" />
                    <widget name="ButtonYellowtext" position="1157,848" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                </screen>"""
        else:
            skin = """
                <screen name="GrabPreviewII"  flags="wfNoBorder" position="320,150" size="1280,720" title="GrabPreview Explorer" backgroundColor="#00121214">
                    <ePixmap position="228,70" size="850,6" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/images/slider.png" alphatest="blend" transparent="1" backgroundColor="#ff000000" />
                    <ePixmap position="230,590" size="850,6" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/ScreenGrabber/images/slider.png" alphatest="blend" transparent="1" backgroundColor="#ff000000" />
                    <widget name="Picture" position="228,70" size="850,520" zPosition="1" alphatest="on" scale="stretch"  />
                    <widget name="menu" position="355,600" size="600,105" scrollbarMode="showOnDemand" transparent="1" zPosition="5" itemHeight="40" />
                    <widget name="State" font="Regular;20" halign="center" position="1,-3" size="1280,70" backgroundColor="#01080911" foregroundColor="#fcc000" transparent="0" zPosition="5" />
                    <eLabel name="" position="1025,650" size="55,55" halign="center" valign="center" transparent="0" cornerRadius="26" font="Regular; 22" zPosition="1" text="OK" backgroundColor="#01080911" foregroundColor="#fcc000" />
                    <eLabel name="" position="1080,650" size="55,55" halign="center" valign="center" transparent="0" cornerRadius="26" font="Regular; 22" zPosition="1" text="EXIT" backgroundColor="#01080911" foregroundColor="#fcc000" />
                    <eLabel backgroundColor="#00ffff00" position="965,643" size="250,6" zPosition="12" />
                    <widget name="ButtonYellowtext" position="964,600" size="250,45" zPosition="11" font="Regular; 24" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                </screen>"""

    def __init__(self, session, whatPic=None, whatDir=None):
        self.skin = GrabPreviewII.skin
        Screen.__init__(self, session)
        self.session = session
        self["State"] = Label(_('loading... '))
        self.whatPic = whatPic
        if self.whatPic is None:
            self.whatPic = None
        self.whatDir = whatDir
        print('folder picture is:', self.whatDir)
        print('whatPic picture is:', self.whatPic)
        self.picList = []
        self['menu'] = MenuList(self.picList)
        self["Picture"] = Pixmap()
        self.EXscale = getScale()
        self.EXpicload = ePicLoad()
        self["ButtonYellowtext"] = Label(_('Remove'))
        self["actions"] = ActionMap(["WizardActions", "DirectionActions", 'OkCancelActions', 'ColorActions'],
                                    {"ok": self.key_ok,
                                     "back": self.close,
                                     "cancel": self.close,
                                     'yellow': self.removefile,
                                     "up": self.Pleft,
                                     "down": self.Pright,
                                     "left": self.Pleft,
                                     "right": self.Pright}, -1)
        try:
            self.EXpicload.PictureData.get().append(self.DecodeAction)
        except:
            self.EXpicload_conn = self.EXpicload.PictureData.connect(self.DecodeAction)

        self.onLayoutFinish.append(self.Show_Picture)

    def Show_Picture(self):
        if self.whatDir is not None and checkfolder(self.whatDir):
            for x in listdir(self.whatDir):
                if path.isfile(self.whatDir + x):
                    if x.endswith('.jpg') or x.endswith('.png') or x.endswith('.bmp') or x.endswith('.gif'):
                        self.picList.append(x)
                self.picList = sorted(self.picList, reverse=True)
            self['menu'].setList(self.picList)

            if len(self.picList) > 0:
                self.viewstr()

    def viewstr(self):
        fname = self['menu'].getCurrent()
        self.whatPic = self.whatDir + fname
        self["State"].setText(_(self.whatPic))
        print('self["State"].visible Show_Picture')

        scale_x = self.EXscale[0] if isinstance(self.EXscale[0], (int, float)) else 1
        scale_y = self.EXscale[1] if isinstance(self.EXscale[1], (int, float)) else 1
        self.EXpicload.setPara([self['Picture'].instance.size().width(),
                                self['Picture'].instance.size().height(),
                                scale_x,
                                scale_y,
                                0,
                                1,
                                '#ff000000'])
        if self.EXpicload.startDecode(self.whatPic):
            self.EXpicload = ePicLoad()
            try:
                self.EXpicload.PictureData.get().append(self.DecodeAction)
            except:
                self.EXpicload_conn = self.EXpicload.PictureData.connect(self.DecodeAction)
        return

    def DecodeAction(self, pictureInfo=""):
        if len(self.picList) > 0:
            if self.whatPic is not None:
                ptr = self.EXpicload.getData()
            else:
                fname = self['menu'].getCurrent()
                self.whatPic = self.whatDir + fname
                ptr = self.EXpicload.getData()
            self["State"].setText(_(self.whatPic))
            self["Picture"].instance.setPixmap(ptr)

    def removefile(self):
        try:
            if self.whatDir is not None and checkfolder(self.whatDir):
                fname = self['menu'].getCurrent()
                filename = self.whatDir + fname
                if path.isfile(filename):
                    remove(filename)
                newPicList = [x for x in self.picList if x != fname]
                self.picList = newPicList
                self['menu'].setList(self.picList)
                self['menu'].moveToIndex(0)
                if len(self.picList) > 0:
                    self.viewstr()
        except Exception as e:
            print(e)

    def Pright(self):
        self["menu"].down()
        if len(self.picList) > 0:
            fname = self['menu'].getCurrent()
            self.whatPic = self.whatDir + fname
            self["State"].setText(_('loading... ' + self.whatPic))
        else:
            self["State"].setText(_("..."))
            self.session.open(MessageBox, _('No more picture-files.'), MessageBox.TYPE_INFO, timeout=3)

        # if self.whatPic is not None:
        if len(self.picList) > 0:
            self.EXpicload.setPara([self["Picture"].instance.size().width(), self["Picture"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#ff000000"])
            self.EXpicload.startDecode(self.whatPic)

    def Pleft(self):
        self["menu"].up()
        if len(self.picList) > 0:
            fname = self['menu'].getCurrent()
            self.whatPic = self.whatDir + fname
            self["State"].setText(_('loading... ' + self.whatPic))
        else:
            self["State"].setText(_("..."))
            self.session.open(MessageBox, _('No more picture-files.'), MessageBox.TYPE_INFO, timeout=3)

        # if self.whatPic is not None:
        if len(self.picList) > 0:
            self.EXpicload.setPara([self["Picture"].instance.size().width(), self["Picture"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#ff000000"])
            self.EXpicload.startDecode(self.whatPic)

    def key_ok(self):
        if self.whatPic is not None and len(self.picList) > 0:
            fname = self['menu'].getCurrent()
            self.whatPic = self.whatDir + fname
            print('GrabPreviewII key_ok whatPic:', self.whatPic)
            self.EXpicload.setPara([self["Picture"].instance.size().width(), self["Picture"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#ff000000"])
            self.EXpicload.startDecode(self.whatPic)


class ConsoleItem:
    def __init__(self, containers, cmd, callback, extra_args, binary=False):

        self.filenamesaved = getFilename()
        if file_exists('/var/lib/dpkg/status'):
            cmd += " -f %s" % self.filenamesaved
        else:
            cmd += " %s" % self.filenamesaved

        global xfilename
        xfilename = self.filenamesaved

        self.containers = containers
        self.callback = callback
        self.extra_args = self.filenamesaved
        self.extraArgs = extra_args if extra_args else self.filenamesaved  # []
        self.binary = binary
        self.container = eConsoleAppContainer()
        self.appResults = []
        name = cmd
        # print('[ConsoleItem] containers:', containers)
        # print("[ConsoleItem] command:", cmd)
        # print("[ConsoleItem] callback:", callback)
        # print("[ConsoleItem] extra_args:", extra_args)
        # print('[ConsoleItem] binary:', binary)
        # print("[ConsoleItem] self.filenamesaved:", self.filenamesaved)
        if name in containers:
            name = str(cmd) + '@' + hex(id(self))
        self.name = name
        # print('[ConsoleItem] if name in containers:=', self.name)
        self.containers[name] = self

        if isinstance(cmd, str):
            cmd = [cmd]
        name = cmd

        if callback:
            self.appResults = []
            try:
                self.container.dataAvail_conn = self.container.dataAvail.connect(self.dataAvailCB)
            except:
                self.container.dataAvail.append(self.dataAvailCB)
        try:
            self.container.appClosed_conn = self.container.appClosed.connect(self.finishedCB)
        except:
            self.container.appClosed.append(self.finishedCB)

        if len(cmd) > 1:
            print("[Console] Processing command '%s' with arguments %s." % (cmd, str(cmd[1:])))
        else:
            print("[Console] Processing command line '%s'." % cmd)

        retval = self.container.execute(*cmd)
        if retval:
            self.finishedCB(retval)

        if self.callback is None:
            pid = self.container.getPID()
            try:
                # print("[Console] Waiting for command (PID %d) to finish." % pid)
                os.waitpid(pid, 0)
                # print("[Console] Command on PID %d finished." % pid)
            except OSError as err:
                print("[Console] Error %s: Wait for command on PID %d to terminate failed!  (%s)" % (err.errno, pid, err.strerror))

    def dataAvailCB(self, data):
        self.appResults.append(data)

    def finishedCB(self, retval):
        print("[Console] Command '%s' finished." % self.name)
        if file_exists('/var/lib/dpkg/status'):
            data = self.appResults
        try:
            del self.containers[self.name]
            # del self.containers[:]
        except Exception as e:
            print('error del self.containers[self.name]:', e)

        try:
            del self.container.dataAvail[:]
        except Exception as e:
            print('error del self.container.dataAvail[:]:', e)

        try:
            del self.container.appClosed[:]
        except Exception as e:
            print('error del self.container.appClosed[:]:', e)
        callback = self.callback
        if callback:
            data = b"".join(self.appResults)
            data = data if self.binary else data.decode()
            # print("[Debug] Data length after join:", len(data))
            # print("[Debug] Successfully wrote:", len(data), self.filenamesaved)
            global xfilename
            xfilename = self.filenamesaved
            callback(data, retval, self.extraArgs)
            # # callback(data, retval, self.filenamesaved)
        # # return
        # return callback(data, retval, xfilename)


class Console:
    """
        Console by default will work with strings on callback.
        If binary data required class shoud be initialized with Console(binary=True)
    """

    def __init__(self, binary=False):
        self.appContainers = {}
        self.binary = binary
        print('self.binary console=', self.binary)

    def ePopen(self, cmd, callback=None, extra_args=[]):
        print("[Console] command:", cmd)
        return ConsoleItem(self.appContainers, cmd, callback, extra_args, self.binary)

    def eBatch(self, cmds, callback, extra_args=[], debug=False):
        self.debug = debug
        cmd = cmds.pop(0)
        self.ePopen(cmd, self.eBatchCB, [cmds, callback, extra_args])

    def eBatchCB(self, data, retval, _extra_args):
        (cmds, callback, extra_args) = _extra_args
        if self.debug:
            print('[eBatch] retval=%s, cmds left=%d, data:\n%s' % (retval, len(cmds), data))
        if len(cmds):
            cmd = cmds.pop(0)
            self.ePopen(cmd, self.eBatchCB, [cmds, callback, extra_args])
        else:
            callback(extra_args)

    def kill(self, name):
        if name in self.appContainers:
            print("[Console] killing: ", name)
            self.appContainers[name].container.kill()

    def killAll(self):
        for name, item in self.appContainers.items():
            print("[Console] killing: ", name)
            item.container.kill()


pScreenGrabber = classScreenGrabber()


def main(session, **kwargs):
    session.open(sgrabberScreenGrabberSetup)


def sessionstart(reason, **kwargs):
    if reason == 0:
        if cfg.items.value == 'Disabled':
            pass
        else:
            pScreenGrabber.gotSession(kwargs['session'])


def Plugins(**kwargs):
    plugin_list = []
    plugin_list.append(
        PluginDescriptor(
            where=[PluginDescriptor.WHERE_SESSIONSTART],
            fnc=sessionstart
        )
    )
    plugin_list.append(
        PluginDescriptor(
            icon='screengrabber.png',
            name='ScreenGrabber',
            description='Grab screen image V.%s' % currversion,
            where=PluginDescriptor.WHERE_PLUGINMENU,
            fnc=main
        )
    )
    return plugin_list