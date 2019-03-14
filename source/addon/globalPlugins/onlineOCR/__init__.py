# coding=utf-8
# Copyright (C) 2019 Larry Wang <larry.wang.801@gmail.com>
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.

"""onlineOCR:
A global plugin that add online ocr to NVDA
"""
import addonHandler
import globalPluginHandler
import gui
import globalVars
import config
from onlineOCRHandler import CustomOCRPanel
from contentRecog import RecogImageInfo
from scriptHandler import script
from logHandler import log
import ui
from PIL import ImageGrab, Image
_ = lambda x: x
# We need to initialize translation and localization support:
addonHandler.initTranslation()
category_name = _("Online OCR")


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    def PILImageToPixels(self, image):
        """
        Convert PIL Image into pixels and imageInfo
        @param image: Image to convert
        @type image Image.Image
        @return:
        @rtype: tuple
        """
        imageInfo = RecogImageInfo(0, 0, image.width, image.height, 1)
        pixels = image.tobytes("raw", "BGRX")
        return pixels, imageInfo

    def event_becomeNavigatorObject(self, obj, nextHandler, isFocus=False):
        if self.autoOCREnabled:
            from contentRecog import recogUi, uwpOcr
            recogUi.recognizeNavigatorObject(uwpOcr.UwpOcr())
        nextHandler()

    def __init__(self):
        super(GlobalPlugin, self).__init__()
        if globalVars.appArgs.secure:
            return
        if config.isAppX:
            return
        self.autoOCREnabled = False
        from . import onlineOCRHandler
        onlineOCRHandler.CustomOCRHandler.initialize()
        self.handler = onlineOCRHandler.CustomOCRHandler
        gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(CustomOCRPanel)

    # Translators: OCR command name in input gestures dialog
    full_ocr_msg = _("Recognizes the content of the current navigator object with Custom OCR engine.Then open a virtual result document.")

    # Translators: OCR command name in input gestures dialog
    @script(description=full_ocr_msg, category=category_name, gestures=["kb:NVDA+alt+shift+r"])
    def script_recognizeWithCustomOcr(self, gesture):
        from contentRecog import recogUi
        engine = onlineOCRHandler.CustomOCRHandler.getCurrentEngine()
        engine.text_result = False
        recogUi.recognizeNavigatorObject(engine)

    # Translators: OCR command name in input gestures dialog
    textMsg = _("Recognizes the text of the current navigator object with Custom OCR engine.Then read result.")

    @script(description=textMsg, category=category_name, gestures=["kb:shift+NVDA+r"])
    def script_recognizeTextWithCustomOcr(self, gesture):
        from contentRecog import recogUi
        engine = onlineOCRHandler.CustomOCRHandler.getCurrentEngine()
        engine.text_result = True
        recogUi.recognizeNavigatorObject(engine)

    # Translators: OCR command name in input gestures dialog
    clipboard_ocr_msg = _("Recognizes the text in clipboard images with Custom OCR engine.Then read result.")

    @script(description=clipboard_ocr_msg,
            category=category_name,
            gestures=["kb:NVDA+windows+r"])
    def script_recognizeClipboardTextWithCustomOcr(self, gesture):
        engine = onlineOCRHandler.CustomOCRHandler.getCurrentEngine()
        engine.text_result = True
        from PIL import ImageGrab, Image
        clipboardImage = ImageGrab.grabclipboard()
        if clipboardImage:
            imageInfo = RecogImageInfo(0, 0, clipboardImage.width, clipboardImage.height, 1)
            pixels = clipboardImage.tobytes("raw", "BGRX")
            engine.recognize(pixels, imageInfo, None)
        else:
            import win32clipboard
            try:
                win32clipboard.OpenClipboard()
                rawData = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
                log.info(rawData)
                if isinstance(rawData, tuple):
                    clipboardImage = Image.open(rawData[0])
                    imageInfo = RecogImageInfo(0, 0, clipboardImage.width, clipboardImage.height, 1)
                    clipboardImage = clipboardImage.convert("RGB")
                    pixels = clipboardImage.tobytes("raw", "RGBX")
                    engine.recognize(pixels, imageInfo, None)
                else:
                    raise RuntimeError
                win32clipboard.CloseClipboard()
            except RuntimeError as e:
                log.error(e)
                ui.message(_(u"No image in clipboard"))

    full_clipboard_ocr_msg = _("Recognizes image in clipboard with online OCR engine.Then open a virtual result document.")

    # Translators: Clipboard OCR description
    @script(description=full_clipboard_ocr_msg,
            category=category_name,
            gestures=["kb:NVDA+windows+alt+r"])
    def script_recognizeClipboardWithCustomOcr(self, gesture):
        engine = onlineOCRHandler.CustomOCRHandler.getCurrentEngine()
        engine.text_result = False
        clipboardImage = ImageGrab.grabclipboard()
        if clipboardImage:
            imageInfo = RecogImageInfo(0, 0, clipboardImage.width, clipboardImage.height, 1)
            pixels = clipboardImage.tobytes("raw", "BGRX")
            engine.recognize(pixels, imageInfo, None)
        else:
            import win32clipboard
            try:
                win32clipboard.OpenClipboard()
                rawData = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
                msg = u"Path of image file is\n{0}".format(rawData)
                log.info(msg)
                if isinstance(rawData, tuple):
                    clipboardImage = Image.open(rawData[0])
                    imageInfo = RecogImageInfo(0, 0, clipboardImage.width, clipboardImage.height, 1)
                    clipboardImage = clipboardImage.convert("RGB")
                    pixels = clipboardImage.tobytes("raw", "BGRX")
                    engine.recognize(pixels, imageInfo, None)
                else:
                    raise RuntimeError
                win32clipboard.CloseClipboard()
            except RuntimeError as e:
                log.error(e)
                ui.message(_(u"No image in clipboard"))

    # Translators: Toggle auto ocr
    @script(description=_("Toggle auto ocr"),
            category=category_name, gestures=["kb:control+;"])
    def script_toggleAutoOCR(self, gesture):
        import winVersion
        import ui
        if not winVersion.isUwpOcrAvailable():
            # Translators: Reported when Windows 10 OCR is not available.
            ui.message(_("Windows 10 OCR not available"))
            return
        if self.autoOCREnabled:
            self.autoOCREnabled = False
            # Translators: Reported when auto OCR is disabled
            ui.message(_(u"Auto OCR Disabled"))
        else:
            self.autoOCREnabled = True
            # Translators: Reported when auto OCR is enabled
            ui.message(_(u"Auto OCR Enabled"))
