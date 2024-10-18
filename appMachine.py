from middl_process import app_request
import os
import time
import uuid

class machine:
    def __init__(self, comfyui_dir, comfyui_url, user_id = "",
                 latest_image_path = "", current_image_path = ""):
        self.user_id = user_id
        self.current_image_path = current_image_path
        self.latest_image_path =  latest_image_path
        self.comfyui_dir = comfyui_dir
        self.comfyui_url = comfyui_url

    def faceswap(self):
        out = uuid.uuid4()
        params = {
            "username": self.user_id,
            "ID": self.user_id,
            "source_image": self.current_image_path,
            "face_image": self.latest_image_path,
            "channel": 0,
            "output_image": str(out)
        }
        app_request(workflow_name = "faceswap", workflow_params = params, comfyui_dir = self.comfyui_dir, comfyui_url=self.comfyui_url)
        return out

    def emotion(self,params_dict):
        out = uuid.uuid4()
        params = {**{
            "username": self.user_id,
            "ID": self.user_id,
            "source_image": self.current_image_path,
            "head_up_down": 0,
            "head_left_right_rotate": 0,
            "head_tilt": 0,
            "eye_open": 0,
            "eyebrow_open": 0,
            "eyeballs_up_down": 0,
            "eyeballs_left_right": 0,
            "mouth_up_down": 0,
            "mouth_left_right": 0,
            "smile": 0,
            "output_image": str(out)

        }, **params_dict}
        app_request(workflow_name = "emotion", workflow_params = params,comfyui_dir = self.comfyui_dir, comfyui_url=self.comfyui_url)
        time.sleep(1.5)
        return out

    def run(self,app_dict):
        app_name = app_dict["name"]
        if app_name == "faceswap":
            return {"status": "success","id": self.faceswap()}
        if app_name == "emotion":
            return  {"status": "success","id": self.emotion(app_dict)}




def parse_command(command_string):
    # 定义参数映射
    param_mapping = {
        'eye': 'eye_open',
        'mouth': 'mouth_up_down',
        'head': 'head_up_down'
    }

    # 定义允许的参数集合
    allowed_params = set(param_mapping.keys())

    # 去掉 @ 开头的部分，并找到第一个空格
    if '@' in command_string:
        command_string = command_string.split(' ', 1)[-1]  # 去掉 @ 和用户名部分

    # 分割字符串
    parts = command_string.split()

    # 初始化结果字典
    result = {}

    # 确保第一个部分是 app 名称
    if len(parts) > 0:
        result["app"] = parts[0]  # 第一个部分作为 app 名称

    # 遍历剩余的部分
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            key = parts[i].lstrip('-')  # 移除前导的 '-'
            value = parts[i + 1]

            # 只处理允许的参数
            if key in allowed_params:
                # 使用映射转换参数名称
                mapped_key = param_mapping[key]
                result[mapped_key] = int(value)  # 将值转换为整数

    return result



# commands = [
#     "@yochan   emotion -eye 5 -mouth 100",
#     "emotion -eye 3 -mouth 2",
#     "@user emotion -head 4 -unknown 10",
#     "emotion -eye 5",
#     "@someone emotion -head 10 -mouth 20"
# ]
#
# for command in commands:
#     parsed_dict = parse_command(command)
#     print(f"Command: {command}")
#     print(f"Parsed: {parsed_dict}\n")



