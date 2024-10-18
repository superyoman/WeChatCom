
import json
from datetime import datetime
import queue
from comfy.comAPI import comfyui_app
import os
# 创建一个字典来存储用户的请求队列
user_queues = {}

# 函数：为用户创建请求队列
def create_user_queue(queue_name):
    if queue_name in user_queues:
        print(f"Queue for user '{queue_name}' already exists.")
        return queue_name  # 返回已存在的队列名称
    else:
        user_queues[queue_name] = queue.Queue()
        print(f"Created queue for user '{queue_name}'.")
        return queue_name

# 函数：向用户的请求队列添加请求
def add_request_to_queue(queue_name, request):
    if queue_name in user_queues:
        user_queues[queue_name].put(request)
    else:
        print(f"Queue for user '{queue_name}' does not exist.")

# 函数：从用户的请求队列获取请求
def get_request_from_queue(queue_name):
    if queue_name in user_queues and not user_queues[queue_name].empty():
        return user_queues[queue_name].get()
    else:
        return None

def get_queue_length(key_name):
    # queue_name = f"list:{username}"
    if key_name in user_queues:
        return user_queues[key_name].qsize()
    else:
        return None


def requeue_oldest_request(queue_name, oldest_request):
    if queue_name in user_queues:
        if oldest_request is not None:
            # 使用临时队列存储其他请求
            temp_queue = queue.Queue()

            # 将当前队列中的所有请求放入临时队列
            while not user_queues[queue_name].empty():
                temp_queue.put(user_queues[queue_name].get())

            # 将最旧的请求放回原队列的最初位置
            user_queues[queue_name].put(oldest_request)

            # 将临时队列中的所有请求放回原队列
            while not temp_queue.empty():
                user_queues[queue_name].put(temp_queue.get())

            print(f"Requeued the provided oldest request for user '{queue_name}' back to its original position.")
        else:
            print(f"No request provided to requeue for user '{queue_name}'.")
    else:
        print(f"Queue for user '{queue_name}' does not exist.")

class QueueHandler:
    def get_list_length(self, key):
        try:
            length = get_queue_length(key)
            if length is not None:
                return length
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 0

    def list_lpush(self,list_key = None,list_value = None):
        try:
            queue_name = create_user_queue(list_key)
            add_request_to_queue(queue_name,list_value)  # 设置列表的过期时间为1小时
            return {"message": "Success"}
        except Exception as ex:
            print(ex)
            return {"message": "Failure"}

    def list_rpush(self,list_key = None,list_value = None,):
        try:
            requeue_oldest_request(list_key, list_value)
            return {"message": "Success"}
        except Exception as ex:
            print(ex)
            return {"message": "Failure"}

    def list_rpop(self,list_key = None):
        return get_request_from_queue(list_key)

class assetMachine():
    def __init__(self,user_id:int,room_id = None,key_prefix = str):
        self.user_id = user_id
        self.list_key = f'{key_prefix}:{self.user_id}'
        self.room_id = room_id

    def save2redis(self, asset_path):
        return QueueHandler().list_lpush(self.list_key,
        json.dumps({"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "path": asset_path, "room_id": self.room_id}))

    def app2redis(self, app_params):
        return QueueHandler().list_lpush(self.list_key,
        json.dumps({"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "app": app_params, "room_id": self.room_id}))

    def get_asset(self):
        value = QueueHandler().list_rpop(self.list_key)
        if value is not None:
            # Redis 返回的是字节串，需要解码
            return eval(value)
        else:
            return None

    def get_latest_asset(self, request_amount:int):
        if request_amount != 0:
            list_len = QueueHandler().get_list_length(self.list_key)
            value_list = []
            if list_len >= request_amount:
                for _ in range(list_len):
                    value = self.get_asset()
                    if value is not None:
                        value_list.append(value)
                return 0, value_list
            else:
                return int(request_amount - list_len), False
        else:
            return 0, False

    def update_asset(self,request_amount:int,asset_path = None):
        rest, latest = self.get_latest_asset(request_amount)
        if rest == 0:
            if latest is not False:
                # Get all images
                return rest, latest[0]['path']
            else:
                return rest, asset_path
        else:
            # add one more
            self.save2redis(asset_path = asset_path)
            #print("Need more image(s)")
            return rest,False


def app_request(workflow_name: str, workflow_params: dict, comfyui_dir:str, comfyui_url:str):
        if not isinstance(workflow_params, dict):
            raise ValueError("workflow_params must be a dictionary")
        return comfyui_app(
            workflow_name = workflow_name,
            workflow_params = workflow_params,
            comfyui_dir = comfyui_dir,
            comfyui_url = comfyui_url
                           )
def comfy_output(folder_path,image_id):
    file_path = os.path.join(folder_path, f"{image_id}_0001.png")
    # 检查文件是否存在
    if os.path.isfile(file_path):
        return file_path
    else:
        return False

if __name__ == "__main__":
    pass