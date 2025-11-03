# LLM 对话程序

一个简单的命令行LLM对话程序，支持与GPT-4o模型进行流式对话。

## 功能特点

- 支持流式输出（实时显示回复）
- 保留对话历史上下文
- 可以清空对话历史
- 简洁易用的命令行界面

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 打开 `main.py` 文件
2. 将 `API_KEY = "your-api-key-here"` 替换为你的实际API密钥
3. 运行程序：

```bash
python main.py
```

## 命令说明

- 直接输入文本：与LLM对话
- `clear` 或 `清空`：清空对话历史
- `quit`、`exit` 或 `退出`：退出程序

## 配置说明

程序默认配置：
- API地址：`https://api.huiyan-ai.cn/v1`
- 模型：`gpt-4o`
- 输出模式：流式输出（stream=True）

如需修改配置，可在 `main()` 函数中调整 `SimpleLLMChat` 的参数。

## 示例

```
=== LLM 对话程序 ===
输入 'quit' 或 'exit' 退出
输入 'clear' 清空对话历史
==============================

你: 你好
助手: 你好！很高兴见到你。有什么我可以帮助你的吗？

你: 介绍一下Python
助手: Python是一种高级编程语言...
```
# ai-tools
