from PIL import Image, ImageGrab
import paramiko
import time
import ctypes
import ctypes.wintypes
import win32con
from threading import Thread
from win11toast import toast
import sys
import yaml
import pyperclip

class HotKey(Thread):
    """
    注册热键
    """

    def run(self, call_back) -> None:

        # https://learn.microsoft.com/en-us/windows/win32/inputdev/wm-hotkey
        hotKeyCtrl = 0x0002
        hotKeyShift = 0x0004

        # https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
        keyU = 0x55

        # 注册全局热键
        self.HotKeyId = ctypes.WinDLL("user32.dll").RegisterHotKey(None, 34001, hotKeyCtrl | hotKeyShift, keyU)

        if self.HotKeyId == 0:
            toast("热键注册失败，程序已退出")
            sys.exit()
        msg = ctypes.wintypes.MSG()
        while True:
            if ctypes.windll.user32.GetMessageA(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == win32con.WM_HOTKEY and msg.wParam == 34001:
                    call_back()
    def close(self):
        ctypes.WinDLL("user32.dll").UnregisterHotKey(None, self.HotKeyId)

def sftp_upload_file(host,user,port,private_key_path,server_path, local_path):
    """
    上传文件，注意：不支持文件夹
    :param host: 主机名
    :param port: 端口
    :param user: 用户名
    :param private_key_path: 私钥路径
    :param server_path: 远程路径，比如：/home/sdn/tmp.txt
    :param local_path: 本地路径，比如：D:/text.txt
    :return: bool
    """
    try:
        private_key = paramiko.RSAKey.from_private_key_file(private_key_path)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        client.connect(hostname=host,port=port,username=user,pkey=private_key)
        sftp = client.open_sftp()
        sftp.put(local_path, server_path)
        sftp.close()
        client.close()
        return True
    except Exception as e:
        print(e)
        return False


def save_clipboard_img(savePath):
    """
    保存剪贴板图片
    """
    # 读取剪贴板图片
    im = ImageGrab.grabclipboard()
    if im == None:
        return None
    # 获得当前时间时间戳
    now = int(time.time())
    # 转换为其他日期格式
    timeArray = time.localtime(now)
    otherStyleTime = time.strftime("%Y%m%d%H%M%S", timeArray)

    imgSavePath = savePath  + '\\' + otherStyleTime + ".jpg"
    print(imgSavePath)
    im.save(imgSavePath)
    return otherStyleTime + ".jpg"

def clipboard_upload(conf):
    imgName = save_clipboard_img(conf['imgSavePath'])
    if imgName == None:
        toast("剪贴板内没有图片")
        return None
    imgSavePath = conf['imgSavePath'] + '\\' + imgName
    serverPath = conf['serverPath'] + '/' + imgName
    upload_result = sftp_upload_file(conf['host'],conf['userName'],conf['port'],conf['privateKeyPath'],serverPath,imgSavePath)
    if upload_result:
        webImgPath = conf['webPath'] + '/' + imgName
        pyperclip.copy(webImgPath)
    else:
        toast("上传失败")



def read_config():
    # 获取yaml文件路径
    yamlPath = 'config.yml'
    fieldList = ['privateKeyPath','imgSavePath', 'host', 'port', 'userName', 'serverPath', 'webPath']

    with open(yamlPath, 'r') as f:
        ayml = yaml.load(f.read(),Loader=yaml.Loader)
        ayml_keys = ayml.keys()
        for field in fieldList:
            if field in ayml_keys == False:
                toast(field + "读取失败，程序已退出")
                sys.exit()

        return ayml


if __name__ == '__main__':
    HotKey = HotKey()
    try:
        conf = read_config()
        upload = lambda : clipboard_upload(conf)
        HotKey.run(upload)
    finally:
        HotKey.close()










