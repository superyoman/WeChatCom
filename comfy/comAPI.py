import websocket
import json
import urllib.request
import urllib.parse
import requests
import os
from PIL import Image
from io import BytesIO
import base64
import uuid

def base64_to_image(base64_string = str,save_path = ""):
    # Decode Base64
    try:
        head, context =base64_string.split(",")
    except:
        context = base64_string
    # print(context)
    image_data = base64.b64decode(context)
    image = Image.open(BytesIO(image_data))
    # Save image
    image.save(save_path)


def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_bytes = base64.b64encode(image_file.read())
        # print(encoded_bytes)
        image = Image.open(image_file)
        image_format = image.format.lower()
        encoded_string = f"data:image/{image_format};base64," + encoded_bytes.decode('utf-8')
        # encoded_string = encoded_bytes.decode('utf-8')
        return encoded_string

def get_ImgFile(folder_path):
    # 获取文件夹中的文件列表
    file_list = os.listdir(folder_path)
    # 打印文件列表
    file_all = []
    for file_name in file_list:
        file_all.append(file_name)
    return file_all

def resize_img(source_path, destination_path, width, height):
    # Open the image
    image = Image.open(source_path)  # Replace with the path to your image
    # Resize the image
    new_size = (width, height)  # Replace with the desired size
    resized_image = image.resize(new_size)
    # Save the resized image
    resized_image.save(destination_path)


def queue_prompt(server_address,prompt,client_id):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p)

    req =  requests.post("http://{}/prompt".format(server_address), data=data)
    # print("http://{}/prompt".format(server_address))
    print(req.json())
    return req.json()

def get_image(server_address,filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
        return response.read()

def get_history(server_address,prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
        return json.loads(response.read())


def get_asset_list(history):
    asset_list = []
    for asset in history["outputs"].items():
        a = list(asset[1].values())[0][0]
        if a["type"] == "output":
            asset_list.append(a["filename"])
    return asset_list

def get_res(server_address,prompt,client_id):
    # print(queue_prompt(server_address,prompt,client_id))
    prompt_id = queue_prompt(server_address,prompt,client_id)['prompt_id']
    output_images = {}
    # while True:
    #     out = ws.recv()
    #     if isinstance(out, str):
    #         message = json.loads(out)
    #         # print(message)
    #         if message['type'] == 'executing':
    #             data = message['data']
    #             if data['node'] is None and data['prompt_id'] == prompt_id:
    #                 break #Execution is done
    #     else:
    #         continue #previews are binary data
    #
    # attempts = 0
    # while attempts < 3:
    #     try:
    #         history = get_history(server_address,prompt_id)[prompt_id]
    #         break
    #     except:
    #         time.sleep(1)
    #         print("try agaion")
    #         history = False
    #     attempts += 1
    #
    # if history:
    #     for o in history['outputs']:
    #         for node_id in history['outputs']:
    #             node_output = history['outputs'][node_id]
    #             if 'images' in node_output:
    #                 images_output = []
    #                 # for image in node_output['images']:
    #                     # image_data = get_image(server_address,image['filename'], image['subfolder'], image['type'])
    #                 image_data = get_asset_list(history)
    #                 # print(image_data)
    #                 images_output = images_output + image_data
    #                 print("!!!!!!!!!!!!!!!!!!!!ComfyUI done!!!!!!!!!!!!!!!!!!!!!")
    #                 return images_output
    #             elif 'tags' in node_output:
    #                 txt = []
    #                 for t in node_output['tags']:
    #                     txt.append(t)
    #                 return txt
    return prompt_id


def read_json(path = "workflow/test.json"):

    with open(file = path,encoding='utf-8', errors='ignore') as f:
        data = json.load(f)
    return data


def images_in_file(folder_path,condition = None):

    image_extensions = [".png", ".jpg", ".jpeg", ".gif"] if condition is None else [condition]
    file_list = []
    # Traverse through the files in the folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Check if the file has an image extension
        if os.path.isfile(file_path) and any(filename.lower().endswith(ext) for ext in image_extensions):
            file_list.append(filename)
    return file_list

def run_flow(comfyui_dir:str,prompt:dict,server_address:str):
    client_id = str(uuid.uuid4())
    # ws = websocket.WebSocket()
    # ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    prompt_id = get_res(server_address, prompt, client_id)
    return prompt_id

def comfyui_app(**kwargs):
    """
    Comfyui workflow progress
    """
    get_params = {}
    for key, value in kwargs.items():
        get_params = {**get_params, **{key: value}}
    workflow_json = gen_workflow(get_params['workflow_params'],get_params['workflow_name'])
    return run_flow(comfyui_dir = get_params['comfyui_dir'],prompt = workflow_json, server_address = get_params['comfyui_url'])

def gen_workflow(workflow_params,workflow_name):
    try:
        #Prepration
        path_workflow = os.path.join(os.path.dirname(os.path.abspath(__file__)),"workflow", f"{workflow_name}_api.json")
        with open(path_workflow, encoding='utf-8', errors='ignore') as f:
            workflow = f.read()
            workflow_new = workflow
            for p in workflow_params:
                target = "#" + p + "#"
                workflow_new = workflow_new.replace(target, str(workflow_params[p]))
            # print(workflow_new)
        workflow_new = workflow_new.replace("\\", "//")
        return json.loads(workflow_new)
    except Exception as ex:
        raise ValueError(f"Failed to gen workflow: {str(ex)}") from ex

if __name__ == "__main__":
    pass