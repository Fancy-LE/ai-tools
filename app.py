"""
带Web界面的LLM对话程序
支持多会话管理和切换
"""
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import requests
import json
from datetime import datetime
import uuid

app = Flask(__name__)

# 配置
API_KEY = "sk-qv1SVWJ5RCyd53i6VbNlhpXPrTluPuMfmLcxasjXEDtmFtHb"
BASE_URL = "https://api.huiyan-ai.cn/v1"

# 可用模型列表
AVAILABLE_MODELS = [
    {"id": "gpt-4o", "name": "GPT-4o", "description": "强大的通用模型"},
    {"id": "gemini-2.5-pro-exp-03-25", "name": "gemini 2.5 pro exp 03-25", "description": "思维链推理模型"}
]

# 存储所有会话
sessions = {}


class ChatSession:
    """聊天会话类"""

    def __init__(self, session_id, title="新对话", model="gpt-4o"):
        self.session_id = session_id
        self.title = title
        self.model = model  # 每个会话可以有自己的模型
        self.messages = []
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = self.created_at

    def add_message(self, role, content):
        """添加消息"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        self.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_api_messages(self):
        """获取API格式的消息列表（不包含timestamp）"""
        return [{"role": msg["role"], "content": msg["content"]}
                for msg in self.messages]

    def to_dict(self):
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "title": self.title,
            "model": self.model,
            "messages": self.messages,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


def chat_stream(session_id, user_input):
    """流式聊天生成器"""
    session = sessions.get(session_id)
    if not session:
        yield "data: " + json.dumps({"error": "会话不存在"}) + "\n\n"
        return

    # 添加用户消息
    session.add_message("user", user_input)

    # 构建请求
    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": session.model,  # 使用会话的模型
        "messages": session.get_api_messages(),
        "stream": True
    }

    try:
        # 增加超时时间：连接超时10秒，读取超时300秒（5分钟）
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            stream=True,
            timeout=(10, 300)  # (connect timeout, read timeout)
        )

        if response.status_code != 200:
            error_msg = f"API错误: {response.status_code} - {response.text}"
            yield "data: " + json.dumps({"error": error_msg}) + "\n\n"
            session.messages.pop()  # 移除失败的用户消息
            return

        full_response = ""
        has_content = False  # 标记是否收到内容

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
                                full_response += content
                                has_content = True
                                yield f"data: {json.dumps({'content': content})}\n\n"
                    except json.JSONDecodeError:
                        continue

        # 保存助手回复
        if has_content:
            session.add_message("assistant", full_response)
            yield "data: [DONE]\n\n"
        else:
            # 如果没有收到任何内容，说明可能超时了
            error_msg = "API响应超时或无内容返回，请稍后重试"
            yield "data: " + json.dumps({"error": error_msg}) + "\n\n"
            session.messages.pop()  # 移除失败的用户消息

    except requests.exceptions.Timeout:
        error_msg = "请求超时：API响应时间过长，请稍后重试或尝试缩短输入内容"
        yield "data: " + json.dumps({"error": error_msg}) + "\n\n"
        if session.messages:
            session.messages.pop()
    except requests.exceptions.ConnectionError:
        error_msg = "连接错误：无法连接到API服务器，请检查网络连接"
        yield "data: " + json.dumps({"error": error_msg}) + "\n\n"
        if session.messages:
            session.messages.pop()
    except Exception as e:
        error_msg = f"请求失败: {str(e)}"
        yield "data: " + json.dumps({"error": error_msg}) + "\n\n"
        if session.messages:
            session.messages.pop()


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/models', methods=['GET'])
def get_models():
    """获取可用模型列表"""
    return jsonify(AVAILABLE_MODELS)


@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """获取所有会话列表"""
    session_list = [
        {
            "session_id": s.session_id,
            "title": s.title,
            "model": s.model,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
            "message_count": len(s.messages)
        }
        for s in sessions.values()
    ]
    # 按更新时间倒序排列
    session_list.sort(key=lambda x: x['updated_at'], reverse=True)
    return jsonify(session_list)


@app.route('/api/sessions', methods=['POST'])
def create_session():
    """创建新会话"""
    session_id = str(uuid.uuid4())
    data = request.json or {}
    title = data.get('title', '新对话')
    model = data.get('model', 'gpt-4o')  # 支持指定模型
    session = ChatSession(session_id, title, model)
    sessions[session_id] = session
    return jsonify(session.to_dict())


@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """获取指定会话"""
    session = sessions.get(session_id)
    if not session:
        return jsonify({"error": "会话不存在"}), 404
    return jsonify(session.to_dict())


@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除会话"""
    if session_id in sessions:
        del sessions[session_id]
        return jsonify({"success": True})
    return jsonify({"error": "会话不存在"}), 404


@app.route('/api/sessions/<session_id>/title', methods=['PUT'])
def update_session_title(session_id):
    """更新会话标题"""
    session = sessions.get(session_id)
    if not session:
        return jsonify({"error": "会话不存在"}), 404

    title = request.json.get('title')
    if title:
        session.title = title
        return jsonify({"success": True})
    return jsonify({"error": "标题不能为空"}), 400


@app.route('/api/sessions/<session_id>/model', methods=['PUT'])
def update_session_model(session_id):
    """更新会话模型"""
    session = sessions.get(session_id)
    if not session:
        return jsonify({"error": "会话不存在"}), 404

    model = request.json.get('model')
    if model:
        session.model = model
        return jsonify({"success": True})
    return jsonify({"error": "模型不能为空"}), 400


@app.route('/api/chat', methods=['POST'])
def chat():
    """发送聊天消息（流式）"""
    data = request.json
    session_id = data.get('session_id')
    user_input = data.get('message')

    if not session_id or not user_input:
        return jsonify({"error": "缺少必要参数"}), 400

    return Response(
        stream_with_context(chat_stream(session_id, user_input)),
        mimetype='text/event-stream'
    )


@app.route('/api/sessions/<session_id>/clear', methods=['POST'])
def clear_session(session_id):
    """清空会话历史"""
    session = sessions.get(session_id)
    if not session:
        return jsonify({"error": "会话不存在"}), 404

    session.messages = []
    return jsonify({"success": True})


if __name__ == '__main__':
    # 创建默认会话
    default_session = ChatSession(str(uuid.uuid4()), "默认对话")
    sessions[default_session.session_id] = default_session

    PORT = 5001  # 修改端口为5001
    print("=" * 50)
    print("LLM Web对话程序已启动")
    print(f"请在浏览器中访问: http://127.0.0.1:{PORT}")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=PORT)
