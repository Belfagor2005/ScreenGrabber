# -*- coding: utf-8 -*-

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import os
import gettext

PluginLanguageDomain = "ScreenGrabber"
PluginLanguagePath = "Extensions/ScreenGrabber/locale"


def localeInit():
	lang = language.getLanguage()[:2]
	os.environ["LANGUAGE"] = lang
	# print("[ScreenGrabber] set language to ", lang)
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	t = gettext.dgettext(PluginLanguageDomain, txt)
	if t == txt:
		# print("[ScreenGrabber] fallback to default Enigma2 Translation for", txt)
		t = gettext.gettext(txt)
	return t


localeInit()
language.addCallback(localeInit)
