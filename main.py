from email import message
import pprint
import uuid
import platform
from typing import Annotated, TypedDict, Literal
from langchain_core.tools import tool
from langchain_community.tools import HumanInputRun
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AnyMessage, AIMessage
from dotenv import load_dotenv
from tools.CommandExecutor import CommandExecutor
from utils.get_input import get_input, agree_to_continue
from langgraph.types import Interrupt, interrupt, Command


load_dotenv()

# tools
executor = CommandExecutor()
# 注册工具
@tool
def execute_command(command: str) -> str:
    """Execute system commands and return output. Use for file operations, system info, etc."""
    return executor.run(command)
@tool
def change_directory(path: str) -> str:
    """Change current working directory for subsequent commands."""
    return executor.change_dir(path)
# Human as a tool 
human = HumanInputRun(input_func=get_input)

tools = [execute_command, change_directory, human]

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    system_info: str

class Agent:
    def __init__(self, model, tools,checkpointer, system=""):
        self.system = system
        graph = StateGraph(AgentState)
        graph.add_node("get_system_info", self.get_system_info)
        graph.add_node("llm", self.call_openai)
        graph.add_node("ask_human", self.ask_human)
        graph.add_node("action", self.take_action)
        graph.add_node("add_tools_respond", self.add_tools_respond)

        graph.add_edge(START, "get_system_info")
        graph.add_edge("get_system_info", "llm")
        graph.add_conditional_edges(
            "llm",
            self.human_approval,
            {"ask_human", "action"} 
        )
        graph.add_edge("add_tools_respond", "ask_human")
        graph.add_edge("action","llm")
        # 添加持久化功能
        self.graph = graph.compile(checkpointer=checkpointer)
        self.tools = { t.name: t for t in tools }
        self.model = model.bind_tools(tools)
        
    def get_system_info(self, state: AgentState) -> AgentState:
        """ 获取当前项目运行的系统平台信息 """
        system_platform = platform.system()
        system_version = platform.version()
        state['system_info'] = f"当前运行平台: {system_platform}, 版本: {system_version}"
        print(f"系统信息: {state['system_info']}")
        return state
    
    def call_openai(self, state: AgentState) -> AgentState:
        """调用LLM (deepseek)"""
        messages = state['messages']
        # print(f"messages: {messages}")
        system_info = state['system_info']
        # 将系统信息添加到系统提示中
        system_message = self.system
        if system_info:
            system_message = f"{system_message}\n\n{system_info}"
        
        if system_message:
            messages = [SystemMessage(content=system_message)] + messages
        response = self.model.invoke(messages)
        print(f'Assistant:{response.content}')
        return {'messages': [response]}


    def human_approval(self, state: AgentState) -> str in ["action", "ask_human", "add_tools_respond"]:
        message = state['messages'][-1]
        # 1 没有工具调用 -> 寻求人工指示
        if type(message) != AIMessage or message.tool_calls == []:
            return "ask_human"
        # 2 有工具调用但只有human -> 直接调用
        if len(message.tool_calls) == 1 and message.tool_calls[0]['name'] == 'human':
            print("需要用户输入，不自动审批。")
            return "action"
        # 3 正常工具调用 -> 通知用户 / 询问是否执行
        for call in message.tool_calls:
            print(f"即将调用工具：{call['name']}，调用参数：{call['args']}")
        while True:
            is_approved = input("是否继续执行？(y/n)")
            if is_approved:
                if is_approved.lower() in ('y', 'yes', '是', '继续'):
                    print("程序将继续执行！")
                    return "action"
                if is_approved.lower() in ('n', 'no', '否', '不', '退出', 'q'):
                    # messages中添加HumanMessage，让用户决定下一步走向
                    return "add_tools_respond"


            else:
                print("输入无效，请输入 y 或 n。")

    def add_tools_respond(self, state: AgentState) -> AgentState:
        message = state['messages'][-1]
        for call in message.tool_calls:
            state['messages'].append(ToolMessage(tool_call_id=call['id'], name=call['name'], content="请求拒绝"))
        content = "用户拒绝执行此命令。请遵循下一指示。"
        next_message = HumanMessage(content=content)
        state['messages'].append(next_message)
        return state

    def ask_human(self, state: AgentState) -> Command[Literal["action", END]]:
        message = state['messages'][-1]
        # pprint.pprint(message)
        next = interrupt(
        {
            "question": "下一步怎么做？(q:退出)"
        })
        if next.lower() in ["q", "exit", "退出"]:
            print("用户终止程序，退出！")
            return Command(goto=END)
        state['messages'].append(HumanMessage(content=next))
        return Command(goto="llm")
        # 如果有调用工具
        # 如果调用工具为human，直接通过
        # 审批工具调用






    def take_action(self, state: AgentState) -> AgentState:
        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            # print(f"Calling: {t}")
            result = self.tools[t["name"]].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        # print("Back to the model!")
        return {'messages': results}
        
    def generate_workflow_diagram(self):
        from IPython.display import Image, display
        display(Image(self.graph.get_graph().draw_mermaid_png()))

if __name__ == "__main__":
    prompt = """ 你是一位精通运维的程序员 \
        你可以使用shell命令来执行运维任务 \
        现在你需要运用你手中的工具 \
        来实现用户交给你的任务 \
        对于复杂的任务，你可以一步一步来 \
        1, 先说出能够实现此任务的计划 \
        2, 需要用户的指导可调用“human”工具，否则对话将结束  \
        3, 调用工具执行被采纳的计划 \
        注意： \
        1,如果信息不全可以利用工具搜集你想搜集的信息 \
        2,再根据你搜集到的信息做出下一步行动 \
        3,最后一步，你需要输出你的结果 \
        4, 生成的可执行的shell不能使shell输出过多,否则只输出有限的内容 \
    """
    with SqliteSaver.from_conn_string("shell_agent.db") as memory:
        model = init_chat_model("deepseek-chat", model_provider="deepseek")
        agent = Agent(model, tools,checkpointer=memory, system=prompt)
        # agent.generate_workflow_diagram()
        checkpoint_key = input("请输入对话ID以加载历史记录（直接回车创建新对话）: ").strip()
        if checkpoint_key:
            # 加载现有对话
            thread = {"configurable": {"thread_id": checkpoint_key}}
            print(f"加载对话: {checkpoint_key}")
        else:
            # 创建新对话
            checkpoint_key = f"对话_{uuid.uuid4()}"
            thread = {"configurable": {"thread_id": checkpoint_key}}
            print(f"创建新对话: {checkpoint_key}")
        messages = {"messages": [HumanMessage(content=input("请输入指令："))]}
        # 首次运行，传入HumanMessage
        #后面运行：messages和interrupt分开处理
        while True:
            
            for event in agent.graph.stream(messages, config=thread):
                for v in event.values():
                    # 如果有LLM输出，则打印
                    if type(v) == dict and "messages" in v and v["messages"][-1].type == AIMessage:
                        print(v["messages"][-1].content)
                    # 如果是中断
                    elif type(v) == tuple and type(v[0]) == Interrupt:
                        messages = None
                        # 获取问题内容
                        question = v[0].value.get('question')
                        # 这里可以添加你的处理逻辑，比如获取用户输入
                        user_input = input(question)
                        # 将用户输入传递给图
                        result = agent.graph.invoke(Command(resume=user_input), config=thread) 
            # 终止条件
            if not agent.graph.get_state(thread).next:
                print(f"当前对话ID: {checkpoint_key}\n下次可使用此ID继续对话")
                break



