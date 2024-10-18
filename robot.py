# -*- coding: utf-8 -*-

import logging
import re
import time
import xml.etree.ElementTree as ET
from queue import Empty
from threading import Thread
from base.func_zhipu import ZhiPu
from wcferry import Wcf, WxMsg
import json
import os
from base.func_bard import BardAssistant
from base.func_chatglm import ChatGLM
from base.func_chatgpt import ChatGPT
from base.func_chengyu import cy
from base.func_news import News
from base.func_tigerbot import TigerBot
from base.func_xinghuo_web import XinghuoWeb
from configuration import Config
from constants import ChatType
from job_mgmt import Job
import middl_process as mp
from appMachine import machine, parse_command
__version__ = "39.2.4.0"

global app_user_id, app_responseId,app_room_id
app_user_id, app_responseId,app_room_id = [],[],[]


def read_json(path = "app.json"):
    with open(file = path,encoding='utf-8', errors='ignore') as f:
        data = json.load(f)
    return data

class Robot(Job):
    """个性化自己的机器人
    """

    def __init__(self, config: Config, wcf: Wcf, chat_type: int) -> None:
        self.wcf = wcf
        self.config = config
        self.LOG = logging.getLogger("Robot")
        self.wxid = self.wcf.get_self_wxid()
        self.allContacts = self.getAllContacts()
        # comfyui
        self.comfyui = read_json()["config"]

        if ChatType.is_in_chat_types(chat_type):
            if chat_type == ChatType.TIGER_BOT.value and TigerBot.value_check(self.config.TIGERBOT):
                self.chat = TigerBot(self.config.TIGERBOT)
            elif chat_type == ChatType.CHATGPT.value and ChatGPT.value_check(self.config.CHATGPT):
                self.chat = ChatGPT(self.config.CHATGPT)
            elif chat_type == ChatType.XINGHUO_WEB.value and XinghuoWeb.value_check(self.config.XINGHUO_WEB):
                self.chat = XinghuoWeb(self.config.XINGHUO_WEB)
            elif chat_type == ChatType.BardAssistant.value and BardAssistant.value_check(self.config.BardAssistant):
                self.chat = BardAssistant(self.config.BardAssistant)
            elif chat_type == ChatType.ZhiPu.value and ZhiPu.value_check(self.config.ZhiPu):
                self.chat = ZhiPu(self.config.ZhiPu)
            else:
                self.LOG.warning("未配置模型")
                self.chat = None
        else:
            if TigerBot.value_check(self.config.TIGERBOT):
                self.chat = TigerBot(self.config.TIGERBOT)
            elif ChatGPT.value_check(self.config.CHATGPT):
                self.chat = ChatGPT(self.config.CHATGPT)
            elif XinghuoWeb.value_check(self.config.XINGHUO_WEB):
                self.chat = XinghuoWeb(self.config.XINGHUO_WEB)
            elif BardAssistant.value_check(self.config.BardAssistant):
                self.chat = BardAssistant(self.config.BardAssistant)
            elif ZhiPu.value_check(self.config.ZhiPu):
                self.chat = ZhiPu(self.config.ZhiPu)
            else:
                self.LOG.warning("未配置模型")
                self.chat = None

        self.LOG.info(f"已选择: {self.chat}")

    @staticmethod
    def value_check(args: dict) -> bool:
        if args:
            return all(value is not None for key, value in args.items() if key != 'proxy')
        return False

    def toAt(self, msg: WxMsg) -> bool:
        """处理被 @ 消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        return self.toChitchat(msg)

    def toChengyu(self, msg: WxMsg) -> bool:
        """
        处理成语查询/接龙消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        status = False
        texts = re.findall(r"^([#|?|？])(.*)$", msg.content)
        # [('#', '天天向上')]
        if texts:
            flag = texts[0][0]
            text = texts[0][1]
            if flag == "#":  # 接龙
                if cy.isChengyu(text):
                    rsp = cy.getNext(text)
                    if rsp:
                        self.sendTextMsg(rsp, msg.roomid)
                        status = True
            elif flag in ["?", "？"]:  # 查词
                if cy.isChengyu(text):
                    rsp = cy.getMeaning(text)
                    if rsp:
                        self.sendTextMsg(rsp, msg.roomid)
                        status = True

        return status

    def reply_target(self,rsp:str,msg: WxMsg):
        if msg.from_group():
            self.sendTextMsg(rsp, msg.roomid , msg.sender)
        else:
            self.sendTextMsg(rsp,msg.sender)

    def send_image2target(self,image:str,room_id = True,user_id = str):
        return self.wcf.send_image(image, room_id if room_id else user_id)

    def check_image(self,msg: WxMsg):
        if msg.type == 3:  # 图片
            # Check queue
            sender_id = msg.roomid if msg.from_group() else msg.sender
            app_q = mp.QueueHandler().list_rpop(list_key=f'app_queue:{msg.sender}')
            if app_q is not None:
                image_path = self.wcf.download_image(msg.id, msg.extra,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)),"cache\images"), timeout=30)
                if image_path:
                    try:
                        asset_amount = json.loads(app_q)['app']["asset_amount"] - 1
                        am = mp.assetMachine(user_id=msg.sender, room_id=sender_id, key_prefix="wechat_asset")
                        rest, latest = am.update_asset(request_amount=asset_amount,
                                                       asset_path=image_path)
                        # print(rest, latest)
                        if latest is not False:
                            # app process
                            engine = machine(user_id = msg.sender,latest_image_path = latest, current_image_path = image_path,
                                             comfyui_url = f"127.0.0.1:{self.comfyui['comfyui_port']}", comfyui_dir = self.comfyui['comfyui_dir'])
                            app = engine.run(json.loads(app_q)["app"])
                            if app["status"] == "success":
                                app_user_id.append(msg.sender)
                                app_responseId.append(app['id'])
                                app_room_id.append(sender_id)
                                rsp = f"所需图片数量上传成功，id为{app['id']}的请求已进入队列"
                            else:
                                rsp = "发生未知错误，此次请求失败"
                        else:
                            am.save2redis(asset_path=image_path)
                            # Drop app_queue back into redis
                            mp.QueueHandler().list_rpush(list_key=f"app_queue:{msg.sender}", list_value=app_q)
                            rsp = f"该应用需要再继续上传{rest}张图片"
                        self.reply_target(rsp = rsp,msg = msg)
                        return True

                    except Exception as ex:
                        print(ex)
                else:
                    print("Failed to download image")

            else:
                print("Pass this image")
                return False

    def toChitchat(self, msg: WxMsg) -> bool:
        """闲聊，接入 ChatGPT
        """
        # rsp = "你@我干嘛？"
        q = re.sub(r"@.*?[\u2005|\s]", "", msg.content)
        params_dict = parse_command(re.sub(r"@.*?[\u2005|\s]", "", msg.content))
        if params_dict["app"] == "faceswap":
            app_params = {"name": "faceswap", "asset_amount": 2}
            sender_id = msg.roomid if msg.from_group() else msg.sender
            if mp.assetMachine(user_id = msg.sender,room_id = sender_id,
                               key_prefix="app_queue").app2redis(app_params=app_params):
                self.sendTextMsg(f"请发送{app_params['asset_amount']}张图片", sender_id, msg.sender)
            else:
                self.sendTextMsg("失败", sender_id, msg.sender)

            return True

        elif params_dict["app"] == "emotion":
            app_params = {**{"name": "emotion", "asset_amount": 1}, **params_dict}
            sender_id = msg.roomid if msg.from_group() else msg.sender
            if mp.assetMachine(user_id = msg.sender,room_id = sender_id,
                               key_prefix="app_queue").app2redis(app_params=app_params):
                self.sendTextMsg(f"请发送{app_params['asset_amount']}张图片", sender_id, msg.sender)
            else:
                self.sendTextMsg("失败", sender_id, msg.sender)

            return True

        else:  # 接了 ChatGPT，智能回复
            rsp = self.chat.get_answer(q, (msg.roomid if msg.from_group() else msg.sender))

        if rsp:
            if msg.from_group():
                self.sendTextMsg(rsp, msg.roomid, msg.sender)
            else:
                self.sendTextMsg(rsp, msg.sender)

            return True
        else:
            self.LOG.error(f"无法从 ChatGPT 获得答案")
            return False

    def processMsg(self, msg: WxMsg) -> None:
        """当接收到消息的时候，会调用本方法。如果不实现本方法，则打印原始消息。
        此处可进行自定义发送的内容,如通过 msg.content 关键字自动获取当前天气信息，并发送到对应的群组@发送者
        群号：msg.roomid  微信ID：msg.sender  消息内容：msg.content
        content = "xx天气信息为："
        receivers = msg.roomid
        self.sendTextMsg(content, receivers, msg.sender)
        """
        # 群聊消息
        if msg.from_group():
            # 如果在群里被 @
            if msg.roomid not in self.config.GROUPS:  # 不在配置的响应的群列表里，忽略
                return

            if msg.is_at(self.wxid):  # 被@
                self.toAt(msg)

            else:  # 其他消息
                self.check_image(msg)

            return  # 处理完群聊信息，后面就不需要处理了
        

        # 非群聊信息，按消息类型进行处理
        if msg.type == 37:  # 好友请求
            self.autoAcceptFriendRequest(msg)

        elif msg.type == 10000:  # 系统信息
            self.sayHiToNewFriend(msg)

        elif msg.type == 0x01:  # 文本消息
            # 让配置加载更灵活，自己可以更新配置。也可以利用定时任务更新。
            if msg.from_self():
                if msg.content == "^更新$":
                    self.config.reload()
                    self.LOG.info("已更新")
            else:
                self.toChitchat(msg)  # 闲聊

        elif msg.type == 3:  #图片
            self.check_image(msg)


    def onMsg(self, msg: WxMsg) -> int:
        try:
            self.LOG.info(msg)  # 打印信息
            self.processMsg(msg)
        except Exception as e:
            self.LOG.error(e)

        return 0

    def enableRecvMsg(self) -> None:
        self.wcf.enable_recv_msg(self.onMsg)

    def enableReceivingMsg(self) -> None:
        def innerProcessMsg(wcf: Wcf):
            while wcf.is_receiving_msg():
                try:
                    msg = wcf.get_msg()
                    self.LOG.info(msg)
                    self.processMsg(msg)
                except Empty:
                    continue  # Empty message
                except Exception as e:
                    self.LOG.error(f"Receiving message error: {e}")

        self.wcf.enable_receiving_msg()
        Thread(target=innerProcessMsg, name="GetMessage", args=(self.wcf,), daemon=True).start()

    def sendTextMsg(self, msg: str, receiver: str, at_list: str = "") -> None:
        """ 发送消息
        :param msg: 消息字符串
        :param receiver: 接收人wxid或者群id
        :param at_list: 要@的wxid, @所有人的wxid为：notify@all
        """
        # msg 中需要有 @ 名单中一样数量的 @
        ats = ""
        if at_list:
            if at_list == "notify@all":  # @所有人
                ats = " @所有人"
            else:
                wxids = at_list.split(",")
                for wxid in wxids:
                    # 根据 wxid 查找群昵称
                    ats += f" @{self.wcf.get_alias_in_chatroom(wxid, receiver)}"

        # {msg}{ats} 表示要发送的消息内容后面紧跟@，例如 北京天气情况为：xxx @张三
        if ats == "":
            self.LOG.info(f"To {receiver}: {msg}")
            self.wcf.send_text(f"{msg}", receiver, at_list)
        else:
            self.LOG.info(f"To {receiver}: {ats}\r{msg}")
            self.wcf.send_text(f"{ats}\n\n{msg}", receiver, at_list)

    def getAllContacts(self) -> dict:
        """
        获取联系人（包括好友、公众号、服务号、群成员……）
        格式: {"wxid": "NickName"}
        """
        contacts = self.wcf.query_sql("MicroMsg.db", "SELECT UserName, NickName FROM Contact;")
        return {contact["UserName"]: contact["NickName"] for contact in contacts}

    def keepRunningAndBlockProcess(self) -> None:
        """
        保持机器人运行，不让进程退出
        """
        while True:
            self.runPendingJobs()
            # Send Result
            if len(app_responseId) > 0:
                out = mp.comfy_output(folder_path = os.path.join(self.comfyui["comfyui_dir"], "ComfyUI\output"),image_id = app_responseId[0])
                time.sleep(2)
                if out:
                    self.send_image2target(image = out, room_id = app_room_id[0], user_id = app_user_id[0])
                    del(app_user_id[0])
                    del(app_responseId[0])
                    del(app_room_id[0])
            time.sleep(1)

    def autoAcceptFriendRequest(self, msg: WxMsg) -> None:
        try:
            xml = ET.fromstring(msg.content)
            v3 = xml.attrib["encryptusername"]
            v4 = xml.attrib["ticket"]
            scene = int(xml.attrib["scene"])
            self.wcf.accept_new_friend(v3, v4, scene)

        except Exception as e:
            self.LOG.error(f"同意好友出错：{e}")

    def sayHiToNewFriend(self, msg: WxMsg) -> None:
        nickName = re.findall(r"你已添加了(.*)，现在可以开始聊天了。", msg.content)
        if nickName:
            # 添加了好友，更新好友列表
            self.allContacts[msg.sender] = nickName[0]
            self.sendTextMsg(f"Hi {nickName[0]}，我自动通过了你的好友请求。", msg.sender)

    def newsReport(self) -> None:
        receivers = self.config.NEWS
        if not receivers:
            return

        news = News().get_important_news()
        for r in receivers:
            self.sendTextMsg(news, r)
