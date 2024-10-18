# WeChatCom
本项目基于 WeChatRobot (https://github.com/lich0821/WeChatRobot) 修改，旨在提供Comfyui图生图工作流应用套壳服务。

**声明:** 此项目不对使用者微信账号风控负责，请自行考量！
## Demo
https://github.com/user-attachments/assets/6f83ed22-1345-4094-8c22-a42466465863

## Quick Start
0. 本项目已删除原项目（WeChatRobot）包括ChatGLM等在线ai功能，无需安装kernel。步骤1-6可参考原项目安装指南。
1. 安装 Python>=3.9（Python 12 需要自己编译依赖，慎选），例如 [3.10.11](https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe)
2. 安装微信 `3.9.10.27`，下载地址在 [这里](https://github.com/lich0821/WeChatRobot/releases/latest) 找到。
3. 克隆项目
```sh
git clone https://github.com/superyoman/WeChatCom.git
```
4. 安装依赖
```sh
# 升级 pip
python -m pip install -U pip
# 安装必要依赖
pip install -r requirements.txt
```
5. 运行

我们需要运行两次 `main.py` 第一次是生成配置文件 `config.yaml`, 第二次是真正跑你的机器人。
直接运行程序会自动拉起微信，如果微信未打开，会自动打开微信；如果版本不对，也会有提示；其他报错，请进群交流。

下面代码为第一次运行：第一次运行 `main.py` 会在 WeChatRobot 目录下生成一个 `config.yaml` 文件，参照修改配置进行修改。

```sh
python main.py

# 需要停止按 Ctrl+C
```

启动之后，可以正常接收消息但不会响应群消息。参考下方 [修改配置](#config) 进行配置，以便响应特定群聊。

下面代码为第二次运行：你可以通过命令行参数选择模型，默认是不选择，这样你配置了什么参数就跑什么模型。正因如此你需要配置前面所说四种模型中的至少一种（当然也可以都配置，想跑那个模型就选什么参数）, 然后就可以开始使用你的机器人了。
```sh
python main.py

# 需要停止按 Ctrl+C
```

6. 停止
输入：`Ctrl+C`。

### <a name="config"></a>修改配置
*修改配置后，需要重新启动，以便让配置生效。*

配置文件 `config.yaml` 是运行程序后自动从模板复制过来的，功能默认关闭。

#### 响应被 @ 消息
为了响应群聊消息，需要添加相应的 `roomId`。

第一次运行的时候，可以在手机上往需要响应的群里发消息，打印的消息中方括号里的就是；多个群用 `,` 分隔。
```yaml
groups:
  enable: [] # 允许响应的群 roomId，大概长这样：2xxxxxxxxx3@chatroom, 多个群用 `,` 分隔
```

7.填写comfyui配置

打开 "app.json",填上comfyui_port (端口)， comfyui_dir (comfyui 主目录，即run_cpu.bat所在文件夹)
```sh
{
  "config": {
  "comfyui_port": 8818,
  "comfyui_dir": "your comfyui fordler"
      }
}
```

8.启动comfyui

9.通过微信机器人，使用comfyui工作流服务

本项目只封装 “换脸”，“表情控制”工作流，请先确保工作流节点能正常在comfyui上运行，工作流所在文件夹：comfy/workflow


## Help
如有问题，可进群交流。

![1](wechat.png)
