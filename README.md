# LangChain + LangGraph Shell Agent

## 项目简介
这个项目实现了一个基于 LangGraph 的智能代理(Agent)，能够调用 自定义的 Windows 命令提示符工具来执行运维任务。Agent 可以根据用户指令，通过大语言模型(LLM)生成计划并执行命令，同时支持与用户交互获取反馈。

## 功能特点
1. **命令执行**：通过自定义的 `CommandExecutor` 类执行 Windows 命令行指令
2. **目录切换**：支持在执行命令前切换工作目录
3. **用户交互**：集成 `human` 工具，允许在执行过程中向用户请求输入和确认
4. **状态持久化**：使用 SQLite 保存对话历史和状态，支持对话恢复
5. **工作流管理**：基于 LangGraph 构建的状态图，管理 Agent 的决策流程

## 代码结构
execute_shell_command/
├── .env                     # 环境变量配置
├── .vscode\                 # VS Code 配置
│   └── settings.json
├── README.md                # 项目文档
├── pycache \             # Python 编译缓存
│   └── sqlite_checkpoint_saver.cpython-312.pyc
├── main.py                  # 主程序入口
├── requirements.txt         # 项目依赖
├── shell_agent.db           # SQLite 数据库文件
├── shell_agent.py           # Agent 实现
├── tools/                   # 工具实现
│   ├── CommandExecutor.py   # 命令执行工具实现
│   └── pycache │       └── CommandExecutor.cpython-312.pyc
└── utils/                   # 工具函数
├── pycache │   └── get_input.cpython-312.pyc
├── get_input.py         # 用户输入处理工具
└── run_command.py       # 命令运行工具

## 核心组件

### 1. CommandExecutor (自定义命令提示符工具)
```python:tools%2FCommandExecutor.py
class CommandExecutor:
    def __init__(self):
        self.work_dir = os.getcwd()  # 跟踪当前工作目录
    
    def run(self, command: str) -> str:
        # 执行命令并返回结果
        # 包含错误处理和输出长度限制
    
    def change_dir(self, path: str) -> str:
        # 切换工作目录
```

### 2. Agent 类
```python:shell_agent.py
class Agent:
    def __init__(self, model, tools, checkpointer, system=""):
        # 初始化状态图和节点
    
    def get_system_info(self, state: AgentState):
        # 获取系统信息
    
    def call_openai(self, state: AgentState):
        # 调用 LLM 生成响应
    
    def ask_human(self, state: AgentState) -> Command:
        # 决定是否需要向用户请求输入
    
    def human_approval(self, state: AgentState) -> Command:
        # 获取用户对命令执行的批准
    
    def take_action(self, state: AgentState):
        # 执行工具调用
```

## 使用方法
1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 配置环境变量
在 `.env` 文件中配置必要的环境变量，如 API 密钥等。

3. 运行程序
```bash
python main.py
```

4. 使用流程
- 程序启动后，会提示您输入对话 ID 或创建新对话
- 输入您的指令，Agent 会生成计划并执行
- 在需要时，Agent 会向您请求确认或输入

## 示例

$ python main.py
请输入对话ID以加载历史记录（直接回车创建新对话）:
创建新对话: 对话_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
请输入指令：列出当前目录下的文件
系统信息: 当前运行平台: Windows, 版本: 10.0.19045
Assistant: 我需要列出当前目录下的文件，我将使用 execute_command 工具执行 dir 命令。
即将调用工具：execute_command，调用参数：{'command': 'dir'}
是否继续执行？(y/n)y
程序将继续执行！
执行命令: dir
命令执行结果:  Volume in drive C is OS
Volume Serial Number is XXXX-XXXX

Directory of XXX

[文件列表输出...]


## 依赖项
项目依赖已在 `requirements.txt` 中定义，主要包括:
- langchain==0.3.27
- langchain-community==0.3.27
- langchain-core==0.3.72
- langchain-deepseek==0.1.4
- langchain-openai==0.3.28
- langgraph==0.6.2
- openai==1.98.0
- python-dotenv==1.0.1
- uuid==1.30

## 注意事项
1. 程序仅支持 Windows 系统，因为使用了 Windows 特有的命令和路径处理方式
2. 执行命令时请谨慎，避免执行可能造成系统损害的命令
3. 默认情况下，命令输出会被限制在 200 个字符以内