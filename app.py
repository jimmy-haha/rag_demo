import streamlit as st
import ollama
import time

# --- 配置 ---
MODEL_NAME = "gemma3:12b"  # 使用你下载的模型

# --- 模拟构建简单的知识库 (RAG 的 "R" 部分) ---
# 在真实场景中，这里会是读取 PDF 或数据库
# 我们这里用一个简单的字符串字典来模拟“私有知识”
knowledge_base = [
    "我们公司的请假流程是：登录 HR 系统 -> 选择'休假管理' -> 填写天数 -> 提交给直属领导审批。",
    "公司的报销规定：每月 25 号前提交发票，打车票需要注明时间地点，超过 200 元需要主管签字。",
    "IT 部门的 Wifi 密码是 'HelloRAG2024'，访客网络不需要密码。",
    "公司的核心价值观是：用户至上，技术驱动，简单开放。",
    "你是 Antigravity 智能助手，由 Google Deepmind 的团队设计。"
]

def retrieve_knowledge(query):
    """
    简单的检索函数。
    会在知识库里搜索跟 query 最相关的关键词。
    (真实项目会用 Vector Database 向量数据库)
    """
    relevant_docs = []
    query_terms = set(query.lower())
    
    for doc in knowledge_base:
        # 非常简单的关键词匹配逻辑，模拟检索过程
        if any(term in doc.lower() for term in ["请假", "流程"] if term in query.lower()) and "流程" in doc:
             relevant_docs.append(doc)
        elif any(term in doc.lower() for term in ["报销", "发票", "打车"] if term in query.lower()) and "报销" in doc:
             relevant_docs.append(doc)
        elif any(term in doc.lower() for term in ["wifi", "密码", "网络"] if term in query.lower()) and "Wifi" in doc:
             relevant_docs.append(doc)
        elif any(term in doc.lower() for term in ["价值观", "口号"] if term in query.lower()) and "价值观" in doc:
             relevant_docs.append(doc)
             
    return relevant_docs

def generate_response(prompt):
    """调用 Ollama 生成回答"""
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{'role': 'user', 'content': prompt}],
            stream=True, # 流式输出，像打字机一样
        )
        return response
    except Exception as e:
        return f"Error: 无法连接 Ollama，请确认它是否正在运行。错误信息: {e}"

# --- 页面 UI (Streamlit) ---
st.set_page_config(page_title="本地 RAG 演示", page_icon="🤖")

st.title("🤖 本地 RAG 助手 (Gemma3)")
st.caption(f"当前模型: {MODEL_NAME} | 只有我知道公司的秘密哦！")

# 侧边栏：展示知识库内容
with st.sidebar:
    st.header("📚 当前挂载的知识库")
    st.markdown("---")
    for idx, doc in enumerate(knowledge_base):
        st.info(f"📄 文档 {idx+1}: {doc}")
    st.markdown("---")
    st.markdown("**测试问题建议：**")
    st.code("WiFi密码是多少？")
    st.code("报销有什么规定？")
    st.code("请假流程是什么？")

# 初始化聊天历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 处理用户输入
if prompt := st.chat_input("请输入你的问题..."):
    # 1. 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. RAG 关键步骤：检索
    with st.spinner("正在检索知识库..."):
        retrieved_docs = retrieve_knowledge(prompt)
        time.sleep(0.5) # 假装检索需要一点时间

    # 3. RAG 关键步骤：增强 (构建 Prompt)
    if retrieved_docs:
        context_str = "\n".join(retrieved_docs)
        # 告诉 AI 基于资料回答
        final_prompt = f"""
你是一个企业内部助手。请务必根据以下【已知信息】回答用户的问题。
如果已知信息里没有答案，就诚实地说“资料里没提到”。

【已知信息】：
{context_str}

【用户问题】：
{prompt}
"""
        st.toast(f"已找到 {len(retrieved_docs)} 条相关资料！", icon="✅")
    else:
        # 如果没搜到，就让 AI 自由发挥（或者告诉用户不知道）
        final_prompt = prompt
        st.toast("未找到相关内部资料，模型将依靠自身知识回答。", icon="⚠️")

    # 4. 生成回答
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # 调用 Ollama
        stream = generate_response(final_prompt)
        
        if isinstance(stream, str): # 报错了
            st.error(stream)
        else:
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    content = chunk['message']['content']
                    full_response += content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
