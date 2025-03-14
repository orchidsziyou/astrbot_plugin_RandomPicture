import hashlib
from datetime import datetime
import os
import shutil
from datetime import time
from random import random, randint
import sqlite3

from botpy import Permission

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.message.components import At, Image, Plain, Reply
import json

from astrbot.core.platform import MessageType
from astrbot.core.star.filter.event_message_type import EventMessageType
from astrbot.core.star.filter.permission import PermissionType

sequence_file_path1 = './data/plugins/astrbot_plugin_RandomPicture_Data/sqe.json'
sequence_file_path2 = './data/plugins/astrbot_plugin_RandomPicture_Data/sqe2.json'
db_path = 'bot.db'

global last_Picture_time, Current_Picture_time, CoolDownTime, flag01
last_Picture_time = 0
CoolDownTime = 5
flag01 = 0


def time_to_seconds(time_obj):
    return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second


def get_last_sequence(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)  # 读取 JSON 数据
            return data['last_sequence']  # 返回 "last_sequence" 对应的值
    else:
        return 0  # 如果文件不存在，说明从第1个序号开始


# 更新序号到文件
def update_last_sequence(sequence, file_path):
    data = {'last_sequence': sequence}  # 创建包含新序号的字典
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file)  # 将数据写入 JSON 文件
    except Exception as e:
        print(f"写入文件时发生错误: {e}")


def update_times(account, type):
    if not os.path.exists(db_path):
        pass
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    if type == '1':
        c.execute("SELECT COUNT(*) FROM SeTuTongJi WHERE QQID = ?", (account,))
    elif type == '2':
        c.execute("SELECT COUNT(*) FROM GuiTuTongJi WHERE QQID = ?", (account,))
    result = c.fetchone()

    # 如果记录存在，result[0] > 0，则不插入
    if result[0] > 0:
        if type == '1':
            c.execute("UPDATE SeTuTongJi SET Times = Times + 1 WHERE QQID = ?", (account,))
        elif type == '2':
            c.execute("UPDATE GuiTuTongJi SET Times = Times + 1 WHERE QQID = ?", (account,))

    else:
        if type == '1':
            c.execute("INSERT INTO SeTuTongJi (QQID, Times) VALUES (?, ?)", (account, 1))
        else:
            c.execute("INSERT INTO GuiTuTongJi (QQID, Times) VALUES (?, ?)", (account, 1))

    conn.commit()
    conn.close()


def get_times(account, type):
    if not os.path.exists(db_path):
        pass
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    if type == '1':
        c.execute("SELECT Times FROM SeTuTongJi WHERE QQID = ?", (account,))
    elif type == '2':
        c.execute("SELECT Times FROM GuiTuTongJi WHERE QQID = ?", (account,))
    result = c.fetchone()
    conn.close()
    return result[0]


def get_Top10(type):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # print(123)
    if type == '1':
        cursor = c.execute("SELECT QQID,Times FROM SeTuTongJi ORDER BY Times DESC LIMIT 10")
    elif type == '2':
        cursor = c.execute("SELECT QQID,Times FROM GuiTuTongJi ORDER BY Times DESC LIMIT 10")
    result = cursor.fetchall()
    conn.close()
    # print(123)
    return result


def get_total_file_size(directory):
    total_size = 0
    count = 0
    # 遍历指定目录中的所有文件
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            total_size += os.path.getsize(file_path)
            count += 1
    return total_size, count


def CreateDatabase(path):
    conn = sqlite3.connect(path)

    # Creating a table
    conn.execute('''CREATE TABLE if NOT EXISTS SeTuTongJi 
                 (id INTEGER PRIMARY KEY,
                 QQID TEXT,
                 Times Integer)''')

    conn.execute('''CREATE TABLE if NOT EXISTS GuiTuTongJi 
                 (id INTEGER PRIMARY KEY,
                 QQID TEXT,
                 Times Integer)''')
    # Committing changes and closing the connection to the database
    conn.commit()
    conn.close()


def compare_file_with_directory(file1, dir2):
    def get_file_hash(file_path, hash_algorithm='sha256'):
        hash_func = hashlib.new(hash_algorithm)
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):  # 分块读取文件内容
                hash_func.update(chunk)
        return hash_func.hexdigest()

    def files_are_equal(file1, file2):
        # 比较文件大小
        if os.path.getsize(file1) != os.path.getsize(file2):
            return False
        # 如果大小相同，逐字节比较文件内容
        return get_file_hash(file1) == get_file_hash(file2)

    # 获取目录中的文件列表（递归方式遍历所有文件）
    for root, _, files in os.walk(dir2):
        for file in files:
            file_path = os.path.join(root, file)
            if files_are_equal(file1, file_path):
                print(f"文件 {file1} 与 {file_path} 内容相同")
                return True, file_path
    return False, "0"  # 如果没有找到匹配的文件


@register("PictureCollect", "orchidsziyou", "一个简单的随机setu插件", "1.0.0", "None")
class MyPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        # 创建插件需要用到的辅助目录
        self.config = config
        print(self.config)

        global sequence_file_path1, sequence_file_path2, mainResPath, ResPath1, ResPath2, db_path, CoolDownTime, flag01
        flag01 = 0

        # 读取配置文件
        CoolDownTime = self.config['CoolDownTime']

        if os.path.exists("./data/plugins/astrbot_plugin_RandomPicture/config.json"):
            with open("./data/plugins/astrbot_plugin_RandomPicture/config.json", 'r') as file:
                data = json.load(file)  # 读取 JSON 数据
                sequence_file_path1 = data['sequence_file_path1']
                sequence_file_path2 = data['sequence_file_path2']
                mainResPath = data['MainFolder']
                ResPath1 = data['res1Folder']
                ResPath2 = data['res2Folder']
                db_path = data['db_path']
                CreateDatabase(db_path)

        if not os.path.exists(mainResPath):
            os.makedirs(mainResPath)
            os.mkdir(ResPath1)
            os.mkdir(ResPath2)
            CreateDatabase(db_path)

    @filter.command("上传涩图")
    async def upload_picture(self, event: AstrMessageEvent):
        '''这是一个 上传图片 指令'''
        message_chain = event.get_messages()
        # print(message_chain)
        logger.info(message_chain)
        senderID = event.get_sender_id()
        Upload_count = 0
        # print(senderID)
        for msg in message_chain:
            # print(msg)
            # print("\n")
            if msg.type == 'Image':
                PictureID = msg.file
                print(f"图片ID: {PictureID}")
                from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
                assert isinstance(event, AiocqhttpMessageEvent)
                client = event.bot
                payloads2 = {
                    "file_id": PictureID
                }
                response = await client.api.call_action('get_image', **payloads2)  # 调用 协议端  API
                # print(response)
                localdiskpath = response['file']
                ImageCount = get_last_sequence(sequence_file_path1)
                photo_path = f"{ImageCount}.png"
                destination_path = os.path.join(ResPath1, photo_path)
                try:
                    shutil.copy(localdiskpath, destination_path)
                    print(f"图片已成功复制到: {destination_path}")
                    ImageCount += 1
                    update_last_sequence(ImageCount, sequence_file_path1)
                    update_times(senderID, '1')
                    Upload_count += 1
                except Exception as e:
                    print(f"复制文件失败: {e}")

            elif msg.type == 'Reply':
                # 处理回复消息
                from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
                assert isinstance(event, AiocqhttpMessageEvent)
                client = event.bot
                payload = {
                    "message_id": msg.id
                }
                response = await client.api.call_action('get_msg', **payload)  # 调用 协议端  API
                # print(response)
                reply_msg = response['message']
                for msg in reply_msg:
                    # print(msg)
                    # print("\n")
                    if msg['type'] == 'image':
                        # print(msg['data']['file'])
                        # print("\n")
                        from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import \
                            AiocqhttpMessageEvent
                        assert isinstance(event, AiocqhttpMessageEvent)
                        client = event.bot
                        payloads2 = {
                            "file_id": msg['data']['file']
                        }
                        response = await client.api.call_action('get_image', **payloads2)  # 调用 协议端  API
                        localdiskpath = response['file']
                        print(localdiskpath)

                        ImageCount = get_last_sequence(sequence_file_path1)
                        photo_path = f"{ImageCount}.png"
                        destination_path = os.path.join(ResPath1, photo_path)
                        try:
                            shutil.copy(localdiskpath, destination_path)
                            print(f"图片已成功复制到: {destination_path}")
                            ImageCount += 1
                            update_last_sequence(ImageCount, sequence_file_path1)
                            Upload_count += 1
                            update_times(senderID, '1')
                        except Exception as e:
                            print(f"复制文件失败: {e}")

        if Upload_count == 0:
            yield event.plain_result("图呢")
        else:
            yield event.plain_result(f"成功上传{Upload_count}张涩图")

    @filter.command("上传鬼图")
    async def upload_picture_guitu(self, event: AstrMessageEvent):
        '''这是一个 上传图片 指令'''
        message_chain = event.get_messages()  # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        # print(message_chain)
        logger.info(message_chain)
        senderID = event.get_sender_id()
        Upload_count = 0
        for msg in message_chain:
            # print(msg)
            if msg.type == 'Image':
                PictureID = msg.file
                print(f"图片ID: {PictureID}")
                from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
                assert isinstance(event, AiocqhttpMessageEvent)
                client = event.bot
                payloads2 = {
                    "file_id": PictureID
                }
                response = await client.api.call_action('get_image', **payloads2)  # 调用 协议端  API
                # print(response)
                localdiskpath = response['file']
                ImageCount = get_last_sequence(sequence_file_path2)
                photo_path = f"{ImageCount}.png"
                destination_path = os.path.join(ResPath2, photo_path)
                try:
                    shutil.copy(localdiskpath, destination_path)
                    print(f"图片已成功复制到: {destination_path}")
                    ImageCount += 1
                    update_last_sequence(ImageCount, sequence_file_path2)
                    Upload_count += 1
                    update_times(senderID, '2')
                except Exception as e:
                    print(f"复制文件失败: {e}")

            elif msg.type == 'Reply':
                # 处理回复消息
                from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
                assert isinstance(event, AiocqhttpMessageEvent)
                client = event.bot
                payload = {
                    "message_id": msg.id
                }
                response = await client.api.call_action('get_msg', **payload)  # 调用 协议端  API
                # print(response)
                reply_msg = response['message']
                for msg in reply_msg:
                    # print(msg)
                    # print("\n")
                    if msg['type'] == 'image':
                        # print(msg['data']['file'])
                        # print("\n")
                        from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import \
                            AiocqhttpMessageEvent
                        assert isinstance(event, AiocqhttpMessageEvent)
                        client = event.bot
                        payloads2 = {
                            "file_id": msg['data']['file']
                        }
                        response = await client.api.call_action('get_image', **payloads2)  # 调用 协议端  API
                        localdiskpath = response['file']
                        print(localdiskpath)

                        ImageCount = get_last_sequence(sequence_file_path2)
                        photo_path = f"{ImageCount}.png"
                        destination_path = os.path.join(ResPath2, photo_path)
                        try:
                            shutil.copy(localdiskpath, destination_path)
                            print(f"图片已成功复制到: {destination_path}")
                            ImageCount += 1
                            update_last_sequence(ImageCount, sequence_file_path2)
                            Upload_count += 1
                            update_times(senderID, '2')
                        except Exception as e:
                            print(f"复制文件失败: {e}")

        if Upload_count == 0:
            yield event.plain_result("图呢")
        else:
            yield event.plain_result(f"成功上传{Upload_count}张鬼图")

    @filter.command("随机涩图", alias=["setu"])
    async def send_picture(self, event: AstrMessageEvent):
        '''这是一个 发送图片 指令'''
        message_type = event.get_message_type()
        if message_type == MessageType.FRIEND_MESSAGE:
            pass
        else:
            global last_Picture_time, Current_Picture_time, flag01
            Current_Picture_time = int(datetime.now().timestamp())
            time_diff_in_seconds = Current_Picture_time - last_Picture_time
            last_Picture_time = Current_Picture_time
            if time_diff_in_seconds < CoolDownTime:
                cd_time = CoolDownTime - time_diff_in_seconds
                if flag01 == 0:
                    flag01 += 1
                    yield event.plain_result(f"进CD了，请{cd_time}秒后再试")
                else:
                    flag01 += 1
                return
            flag01 = 0
        message_chain = event.get_messages()  # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        MaxNumber = get_last_sequence(sequence_file_path1)
        if MaxNumber == 0:
            yield event.chain_result("还没有涩图")
        else:
            RandomNumber = randint(0, MaxNumber)
            photo_path = f"{RandomNumber}.png"
            destination_path = os.path.join(ResPath1, photo_path)
            TryCount = 0
            while not os.path.exists(destination_path):
                RandomNumber = randint(0, MaxNumber)
                photo_path = f"{RandomNumber}.png"
                destination_path = os.path.join(ResPath1, photo_path)
                TryCount += 1
                if TryCount > 10:
                    yield event.chain_result("发送失败")
                    return
            if os.path.exists(destination_path):
                chain = [
                    Reply(id=event.message_obj.message_id),
                    Image.fromFileSystem(destination_path)
                ]
                # 发送图片
                yield event.chain_result(chain)
            else:
                pass

    @filter.command("随机鬼图", alias=["guitu"])
    async def send_picture_guitu(self, event: AstrMessageEvent):
        '''这是一个 发送图片 指令'''
        message_type = event.get_message_type()
        if message_type == MessageType.FRIEND_MESSAGE:
            pass
        else:
            global last_Picture_time, Current_Picture_time, flag01
            Current_Picture_time = int(datetime.now().timestamp())
            time_diff_in_seconds = Current_Picture_time - last_Picture_time
            last_Picture_time = Current_Picture_time
            if time_diff_in_seconds < CoolDownTime:
                cd_time = CoolDownTime - time_diff_in_seconds
                if flag01 == 0:
                    flag01 += 1
                    yield event.plain_result(f"进CD了，请{cd_time}秒后再试")
                else:
                    flag01 += 1
                return
            flag01 = 0
        user_name = event.get_sender_name()
        message_str = event.message_str  # 用户发的纯文本消息字符串
        message_chain = event.get_messages()  # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        # print(message_chain)
        logger.info(message_chain)
        MaxNumber = get_last_sequence(sequence_file_path2)
        if MaxNumber == 0:
            yield event.chain_result("还没有鬼图")
        else:
            RandomNumber = randint(0, MaxNumber)
            photo_path = f"{RandomNumber}.png"
            destination_path = os.path.join(ResPath2, photo_path)
            TryCount = 0
            while not os.path.exists(destination_path):
                RandomNumber = randint(0, MaxNumber)
                photo_path = f"{RandomNumber}.png"
                destination_path = os.path.join(ResPath2, photo_path)
                TryCount += 1
                if TryCount > 10:
                    yield event.chain_result("发送失败")
                    return
            if os.path.exists(destination_path):
                chain = [
                    Reply(id=event.message_obj.message_id),
                    Image.fromFileSystem(destination_path)
                ]
                # 发送图片
                yield event.chain_result(chain)
            else:
                pass

    @filter.command("涩图排行榜")
    async def send_picture_rank(self, event: AstrMessageEvent):
        '''这是一个 发送图片排行榜 指令'''
        message_chain = event.get_messages()  # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        # print(message_chain)
        logger.info(message_chain)
        result = get_Top10('1')
        # print(321)
        if len(result) > 0:
            str = ""
            # print(3212)
            for i in range(min(len(result), 10)):
                str += f"{i + 1}. {result[i][0]} 传了 {result[i][1]} 张\n"
            chain = [
                Plain("涩图排行榜\n"),
                Plain(str)
            ]
            yield event.chain_result(chain)
            print(32123)

        else:
            yield event.plain_result("统计失败")

    @filter.command("鬼图排行榜")
    async def send_picture_guitu_rank(self, event: AstrMessageEvent):
        '''这是一个 发送图片排行榜 指令'''
        message_chain = event.get_messages()  # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        # print(message_chain)
        logger.info(message_chain)
        result = get_Top10('2')
        if len(result) > 0:
            str = ""
            # print(3212)
            for i in range(min(len(result), 10)):
                str += f"{i + 1}. {result[i][0]} 传了 {result[i][1]} 张\n"
            chain = [
                Plain("鬼图排行榜\n"),
                Plain(str)
            ]
            yield event.chain_result(chain)
        else:
            yield event.plain_result("统计失败")

    @filter.command("ping")
    async def send_ping(self, event: AstrMessageEvent):
        '''这是一个 发送ping 指令'''
        yield event.plain_result("pong")

    @filter.command_group("统计")
    def statistics_group(self):
        pass

    @statistics_group.command("涩图")
    async def statistics_setu(self, event: AstrMessageEvent):
        '''这是一个 统计涩图 指令'''
        total_size, count = get_total_file_size(ResPath1)
        total_size = round(total_size / 1024 / 1024, 2)
        chain = [
            Plain(f"涩图总大小: {total_size}MB\n"),
            Plain(f"涩图总数: {count}张")
        ]
        yield event.chain_result(chain)

    @statistics_group.command("鬼图")
    async def statistics_guitu(self, event: AstrMessageEvent):
        '''这是一个 统计鬼图 指令'''
        total_size, count = get_total_file_size(ResPath2)
        total_size = round(total_size / 1024 / 1024, 2)
        chain = [
            Plain(f"鬼图总大小: {total_size}MB\n"),
            Plain(f"鬼图总数: {count}张")
        ]
        yield event.chain_result(chain)

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("删除图片")
    async def delete_setu(self, event: AstrMessageEvent):
        '''这是一个 删除涩图 指令'''
        bot_id = event.get_self_id()
        sender_id = event.get_sender_id()
        message_chain = event.get_messages()  # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        # print(message_chain)
        for msg in message_chain:
            # print(msg)
            # print("\n")
            if msg.type == 'Reply':
                from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
                assert isinstance(event, AiocqhttpMessageEvent)
                client = event.bot
                payload = {
                    "message_id": msg.id
                }
                response = await client.api.call_action('get_msg', **payload)  # 调用 协议端  API

                if str(response['sender']['user_id']) != bot_id:
                    return

                messages = response['message']
                localdiskpath = ''
                reply_msg = ''
                for msg in messages:
                    # print(msg)
                    # print("\n")
                    if msg['type'] == 'image':
                        # print(msg['data']['file'])
                        # print("\n")
                        from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import \
                            AiocqhttpMessageEvent
                        assert isinstance(event, AiocqhttpMessageEvent)
                        client = event.bot
                        payloads2 = {
                            "file_id": msg['data']['file']
                        }
                        response = await client.api.call_action('get_image', **payloads2)  # 调用 协议端  API
                        localdiskpath = response['file']
                        print(localdiskpath)

                    if msg['type'] == 'reply':
                        from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import \
                            AiocqhttpMessageEvent
                        assert isinstance(event, AiocqhttpMessageEvent)
                        client = event.bot
                        payloads2 = {
                            "message_id": msg['data']['id']
                        }
                        response01 = await client.api.call_action('get_msg', **payloads2)
                        # print(response01)
                        # print('\n')
                        if response01['message'][0]['type'] == 'text':
                            reply_msg = response01['message'][0]['data']['text']
                            print(reply_msg)

                if localdiskpath == '':
                    yield event.plain_result("删除失败")
                    return
                if reply_msg == '':
                    yield event.plain_result("删除失败")
                    return

                if reply_msg == '/setu' or reply_msg == '/随机涩图':
                    print('删除涩图')
                    result, path = compare_file_with_directory(localdiskpath, ResPath1)
                    print(result)
                    if result:
                        os.remove(path)
                        print(f"图片已成功删除: {path}")
                        yield event.plain_result("成功删除涩图")

                elif reply_msg == '/guitu' or reply_msg == '/随机鬼图':
                    print('删除鬼图')
                    result, path = compare_file_with_directory(localdiskpath, ResPath2)
                    print(result)
                    if result:
                        os.remove(path)
                        print(f"图片已成功删除: {path}")
                        yield event.plain_result("成功删除鬼图")
                else:
                    yield event.plain_result("删除失败")

    @filter.event_message_type(EventMessageType.PRIVATE_MESSAGE)
    async def handle_private_message(self, event: AstrMessageEvent, result: MessageEventResult):
        '''处理私聊消息'''
        message_chain = event.get_messages()  # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        print(event.message_obj)

    # @filter.event_message_type(EventMessageType.ALL)
    # async def handle_event_message(self, event: AstrMessageEvent, result: MessageEventResult):
    #     '''处理所有消息'''
    #     # message_chain = event.get_messages()  # 用户所发的消息的消息链 # from astrbot.api.message_components import *
    # # print(message_chain)
    # logger.info(message_chain)
    # for msg in message_chain:
    #     print(msg)
    #     print("\n")
    #
    #     if msg.type == 'Reply':
    #         from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
    #         assert isinstance(event, AiocqhttpMessageEvent)
    #         client = event.bot
    #         payload = {
    #             "message_id": msg.id
    #         }
    #         response = await client.api.call_action('get_msg', **payload)  # 调用 协议端  API
    #         #print(response)
    #         #print('\n')
    #
    #         messages=response['message']
    #         for msg in messages:
    #             if msg['type'] == 'forward':
    #                 # 处理转发消息
    #                 raw_message = msg['data']['content']
    #
    #                 raw_message_id=msg['data']['id']
    #                 client = event.bot
    #                 payloads2 = {
    #                     "message_id": raw_message_id
    #                 }
    #                 response = await client.api.call_action('get_forward_msg', **payloads2)  # 调用 协议端  API
    #                 # print(response)
    #                 # print('\n')
    #
    #                 for message in response['messages']:
    #                     if message['message'][0]['type']=='image':
    #
    #                         client = event.bot
    #                         payloads2 = {
    #                             "file_id": message['message'][0]['data']['file']
    #                         }
    #                         response = await client.api.call_action('get_image', **payloads2)
    #                         print(response['data']['file'])
    #                         print('\n')

    # for raw_msg in raw_message:
    #     # print(raw_msg)
    #     if raw_msg['message'][0]['type']=='image':
    #         # 处理图片消息
    #         PictureID = raw_msg['message'][0]['data']['file']
    #         print(f"图片ID: {PictureID}")
    #         print('\n')
    #
    #         from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import \
    #             AiocqhttpMessageEvent
    #         assert isinstance(event, AiocqhttpMessageEvent)
    #
    #         raw_message_id=raw_msg['message_id']
    #         client = event.bot
    #         payloads2 = {
    #             "message_id": raw_message_id
    #         }
    #         response = await client.api.call_action('get_msg', **payloads2)  # 调用 协议端  API
    #         print(response)
