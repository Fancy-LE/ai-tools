"""
简单的LLM对话程序
"""
import requests
import json


class SimpleLLMChat:
    """简单的LLM对话类"""

    def __init__(self, api_key: str, base_url: str = "https://api.huiyan-ai.cn/v1", model: str = "gpt-4o"):
        """
        初始化对话

        Args:
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称
        """
        self.api_key = api_key.strip()  # 去除可能的空格
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.messages = []  # 存储对话历史

    def add_message(self, role: str, content: str):
        """添加消息到对话历史"""
        self.messages.append({"role": role, "content": content})

    def chat(self, user_input: str, stream: bool = True):
        """
        发送对话请求

        Args:
            user_input: 用户输入
            stream: 是否使用流式输出（默认True）

        Returns:
            助手回复内容
        """
        # 添加用户消息
        self.add_message("user", user_input)

        # 构建请求
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": self.messages,
            "stream": stream
        }

        try:
            if stream:
                # 流式输出
                print(f"[调试] 请求URL: {url}")
                response = requests.post(url, headers=headers, json=payload, stream=True)

                # 如果请求失败，打印详细错误信息
                if response.status_code != 200:
                    print(f"[错误] 状态码: {response.status_code}")
                    print(f"[错误] 响应内容: {response.text}")

                response.raise_for_status()

                print("助手: ", end='', flush=True)
                full_response = ""

                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]
                            if data_str == '[DONE]':
                                break
                            try:
                                data = json.loads(data_str)
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        content = delta['content']
                                        print(content, end='', flush=True)
                                        full_response += content
                            except json.JSONDecodeError:
                                continue

                print()  # 换行

                # 保存助手回复
                self.add_message("assistant", full_response)
                return full_response

            else:
                # 非流式输出
                print(f"[调试] 请求URL: {url}")
                response = requests.post(url, headers=headers, json=payload)

                # 如果请求失败，打印详细错误信息
                if response.status_code != 200:
                    print(f"[错误] 状态码: {response.status_code}")
                    print(f"[错误] 响应内容: {response.text}")

                response.raise_for_status()

                data = response.json()
                assistant_message = data['choices'][0]['message']['content']

                print(f"助手: {assistant_message}")

                # 保存助手回复
                self.add_message("assistant", assistant_message)
                return assistant_message

        except Exception as e:
            print(f"请求失败: {str(e)}")
            # 移除失败的用户消息
            if self.messages:
                self.messages.pop()
            return None

    def clear_history(self):
        """清空对话历史"""
        self.messages = []
        print("对话历史已清空")


def main():
    """主函数"""
    print("=== LLM 对话程序 ===")
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'clear' 清空对话历史")
    print("=" * 30)

    # 请在这里填写你的API密钥
    API_KEY = "sk-qv1SVWJ5RCyd53i6VbNlhpXPrTluPuMfmLcxasjXEDtmFtHb"  # 替换为你的实际API密钥

    # 创建对话实例
    chat = SimpleLLMChat(
        api_key=API_KEY,
        base_url="https://api.huiyan-ai.cn/v1",
        model="gpt-4o"
    )
    print()

    # 开始对话循环
    while True:
        try:
            user_input = input("\n你: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', '退出']:
                print("再见！")
                break

            if user_input.lower() in ['clear', '清空']:
                chat.clear_history()
                continue

            # 发送对话请求（使用流式输出）
            chat.chat(user_input, stream=True)

        except KeyboardInterrupt:
            print("\n\n程序已中断，再见！")
            break
        except Exception as e:
            print(f"发生错误: {str(e)}")


if __name__ == "__main__":
    main()
