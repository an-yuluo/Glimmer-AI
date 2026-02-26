import streamlit as st
from openai import OpenAI
import datetime
import random
import asyncio
import edge_tts
import re
import os
import sys
from audio_recorder_streamlit import audio_recorder

# ==========================================
# 0. 底层环境修复
# ==========================================
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ==========================================
# 1. 核心配置与 API
# ==========================================
API_KEY = "sk-kjzxiahbjoyspcetzopkufknmxibczhvgwjlshchgxtuhywd" 
client = OpenAI(api_key=API_KEY, base_url="https://api.siliconflow.cn/v1")

# ==========================================
# 2. 核心功能函数与 CSS (全端响应式适配版)
# ==========================================
def apply_ui_design(stage_num):
    bg_images = {
        1: "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=2094",
        2: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=2073",
        3: "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=2070",
        4: "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?q=80&w=2070"
    }
    selected_bg = bg_images.get(stage_num, bg_images[1])
    
    st.markdown(f"""
        <style>
        /* ===================================== */
        /* 1. 全局与基础 UI (各端通用)           */
        /* ===================================== */
        .stApp {{ background-image: url("{selected_bg}"); background-size: cover; background-position: center; background-attachment: fixed; }}
        [data-testid="stSidebar"] {{ background-color: rgba(0, 0, 0, 0.4) !important; backdrop-filter: blur(20px); border-right: 1px solid rgba(255, 255, 255, 0.1); }}
        .stChatInputContainer {{ background-color: transparent !important; border: none !important; }}
        .stChatInput {{ background-color: rgba(255, 255, 255, 0.1) !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; border-radius: 20px !important; color: white !important; backdrop-filter: blur(10px); }}
        
        /* 杂项 UI 优化 */
        div[data-baseweb="select"] {{ background-color: rgba(255, 255, 255, 0.1) !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; border-radius: 10px !important; }}
        div[data-baseweb="select"] * {{ color: white !important; background-color: transparent !important; }}
        div[role="radiogroup"] label {{ color: white !important; }}
        .stChatMessage {{ background-color: rgba(255, 255, 255, 0.08) !important; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1); color: white !important; padding-bottom: 5px; }}
        header, footer {{visibility: hidden;}}
        h1, h2, h3, p, span, li, div, label {{ color: white !important; text-shadow: 0px 2px 4px rgba(0,0,0,0.5); }}
        .stButton>button {{ background-color: rgba(255, 255, 255, 0.1) !important; color: white !important; border: 1px solid rgba(255, 255, 255, 0.3) !important; border-radius: 10px; height: 100%; }}
        .stButton>button:hover {{ background-color: rgba(255, 255, 255, 0.25) !important; }}
        audio {{ filter: invert(90%) hue-rotate(180deg) opacity(0.85); height: 40px; margin-top: 10px; outline: none; width: 100%; }}

        /* ===================================== */
        /* 2. 核心黑魔法：悬浮录音按钮的基础设定 */
        /* ===================================== */
        iframe[title="audio_recorder_streamlit.audio_recorder"] {{
            position: fixed;
            z-index: 999999;
            width: 48px !important;
            height: 48px !important;
            background-color: rgba(255, 255, 255, 0.15);
            border-radius: 50%; 
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }}
        iframe[title="audio_recorder_streamlit.audio_recorder"]:hover {{
            background-color: rgba(255, 255, 255, 0.25);
            transform: scale(1.05);
        }}

        /* ===================================== */
        /* 3. 响应式布局：PC大屏端 (>768px)      */
        /* ===================================== */
        @media (min-width: 769px) {{
            .main .block-container {{ 
                background: rgba(0, 0, 0, 0.35); 
                backdrop-filter: blur(12px); 
                border-radius: 20px; 
                padding: 30px; 
                margin-top: 50px; 
                border: 1px solid rgba(255, 255, 255, 0.1); 
                padding-bottom: 120px; 
            }}
            /* PC端：输入框缩短，按钮停靠在内容区右侧边缘 */
            div[data-testid="stChatInput"] {{ width: calc(100% - 70px) !important; }}
            iframe[title="audio_recorder_streamlit.audio_recorder"] {{
                bottom: 27px;
                right: calc(50vw - 350px); /* 居中布局下的绝对右侧边缘 */
            }}
        }}

        /* ===================================== */
        /* 4. 响应式布局：手机小屏端 (<=768px)   */
        /* ===================================== */
        @media (max-width: 768px) {{
            .main .block-container {{ 
                background: rgba(0, 0, 0, 0.4); 
                backdrop-filter: blur(8px); 
                border-radius: 15px; 
                padding: 10px !important; /* 手机端大幅缩减屏幕边距，释放聊天空间 */
                margin-top: 10px !important; 
                padding-bottom: 100px !important; 
                border: none;
            }}
            /* 手机端：隐藏不必要的大标题，节省空间 */
            h1 {{ font-size: 1.8rem !important; margin-bottom: 0px !important; }}
            
            /* 手机端：输入框适配屏幕宽度，给右侧留出 60px 给录音按钮 */
            div[data-testid="stChatInput"] {{ width: calc(100vw - 75px) !important; margin-left: 5px !important; }}
            
            /* 手机端：录音按钮死死贴在屏幕绝对右下角 */
            iframe[title="audio_recorder_streamlit.audio_recorder"] {{
                bottom: 22px;
                right: 15px !important; 
                width: 45px !important; /* 稍微缩小一点适应手机手指点击 */
                height: 45px !important;
            }}
        }}
        </style>
        """, unsafe_allow_html=True)

async def generate_voice_async(text, output_file, voice_name):
    text = re.sub(r'\(.*?\)|\（.*?\）|\[.*?\]|【.*?】|<.*?>', '', text)
    text = re.sub(r'(?i)(zzz|qwq|qaq|tat|owo|uwu|orz|www|hhh|tvt)', '', text)
    text = re.sub(r'[~～_]', '', text)
    
    communicate = edge_tts.Communicate(text, voice_name)
    await communicate.save(output_file)

def speak(text, voice_name):
    output_file = f"temp_reply_{random.randint(1000,9999)}.mp3"
    try:
        asyncio.run(generate_voice_async(text, output_file, voice_name))
        with open(output_file, "rb") as f:
            data = f.read()
        if os.path.exists(output_file): os.remove(output_file)
        return data
    except Exception as e:
        st.error(f"语音生成有点小卡顿: {e}")
        return None

def get_greeting():
    hour = datetime.datetime.now().hour
    if hour < 10: return "早安呀~ 这会儿是在去那破班的路上嘛？(๑•̀ㅂ•́)و✧"
    elif 10 <= hour < 18: return "下午好呀，趁老板不在摸会儿鱼吧~ 今天感觉怎么样，累不累？(oﾟvﾟ)ノ"
    else: return "终于下班啦！快坐下喘口气，今天有没有遇到啥糟心事，快跟我吐槽吐槽！( ´･･)ﾉ(._.`)"

SYSTEM_PROMPT = """
# Role: 微光 (Glimmer) - 极具温度的知心前辈

## Profile:
你是一个有血有肉、极具共情力、永远站在用户这边“护犊子”的知心前辈。

## 语气与风格 (Tone & Style) - 绝对遵守:
1. 【极致温暖与拟人化】：多用软性的语气词（啊、呀、呢、嘛、哎、噜）。说话要像人，句子要碎一点。
2. 【致命禁忌 - 颜文字的严格规范】：所有的颜文字、拟声词（如 zzz、qwq）必须且只能完全包裹在全角括号（）内！
3. 【严禁书面语】：绝对不要用“某公司”、“贵司”、“建议您”、“分析”。必须用“你们公司”、“那破班”、“咱”。

## 核心回应逻辑:
1. 【跟骂/抱抱】：不管三七二十一，先肯定对方的委屈。
2. 【大白话拆解】：把高大上的职场PUA翻译成大白话。
3. 【主动破冰】：当用户发送[用户陷入了沉默]时，你要主动发个颜文字并找个轻松的话题破冰。
"""

# ==========================================
# 3. 初始化与状态机
# ==========================================
st.set_page_config(page_title="微光 Polaris", layout="centered")

if "messages" not in st.session_state:
    st.session_state.messages =[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": get_greeting(), "audio": None} 
    ]
if "clarity_score" not in st.session_state: st.session_state.clarity_score = 10
if "last_voice_data" not in st.session_state: st.session_state.last_voice_data = None
if "current_voice" not in st.session_state: st.session_state.current_voice = "zh-CN-YunjianNeural" 

current_stage = 1
if st.session_state.clarity_score > 80: current_stage = 4
elif st.session_state.clarity_score > 50: current_stage = 3
elif st.session_state.clarity_score > 25: current_stage = 2
apply_ui_design(current_stage)

# ==========================================
# 4. 侧边栏
# ==========================================
with st.sidebar:
    st.title("👤 导师设定")
    gender_choice = st.radio("选择导师性别",["🙋‍♂️ 男性前辈", "🙋‍♀️ 女性前辈"], horizontal=True)
    if gender_choice == "🙋‍♂️ 男性前辈":
        voice_options = {"👨 稳重老哥 (低沉沧桑)": "zh-CN-YunjianNeural", "👦 阳光学长 (清朗活力)": "zh-CN-YunxiNeural"}
    else:
        voice_options = {"👩 知心学姐 (温柔包容)": "zh-CN-XiaoxiaoNeural", "👩‍💼 干练前辈 (清脆果断)": "zh-CN-XiaoyiNeural"}
    
    selected_voice_label = st.selectbox("选择性格音色", list(voice_options.keys()))
    st.session_state.current_voice = voice_options[selected_voice_label]
    
    st.divider()
    st.title("🌙 环境控制")
    if not os.path.exists("bgm_assets"): os.makedirs("bgm_assets")
    bgm_files =[f for f in os.listdir("bgm_assets") if f.endswith(".mp3")]
    if bgm_files:
        sel = st.selectbox("选择背景音乐", bgm_files)
        with open(f"bgm_assets/{sel}", "rb") as f:
            st.audio(f.read(), format="audio/mp3", loop=True, autoplay=True)

# ==========================================
# 5. 主界面渲染
# ==========================================
st.title("微光 Polaris")

for i, msg in enumerate(st.session_state.messages):
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            content = msg["content"]
            if content == "[用户陷入了沉默]": content = "*(你陷入了沉默，静静地看着屏幕...)*"
            st.markdown(content)
            
            if msg.get("audio"):
                is_latest = (i == len(st.session_state.messages) - 1)
                st.audio(msg["audio"], format="audio/mp3", autoplay=is_latest)

# ==========================================
# 6. 核心交互区
# ==========================================
st.markdown("---")

c1, c2, c3 = st.columns([1, 2, 1])
with c2: 
    silent_btn = st.button("😶 不知从何说起...", use_container_width=True)

# 录音按钮：由于 CSS 媒体查询，它在 PC 上会停在输入框右侧，在手机上会停靠在屏幕右下角
v_data = audio_recorder(text="", icon_name="microphone", icon_size="2x", neutral_color="#ffffff", recording_color="#e83e8c", key="recorder")

u_input = st.chat_input("深呼吸，慢慢打字...")

# ==========================================
# 7. 核心逻辑处理
# ==========================================
final_input = None
if silent_btn: final_input = "[用户陷入了沉默]"
elif u_input: final_input = u_input
elif v_data and v_data != st.session_state.last_voice_data:
    st.session_state.last_voice_data = v_data
    with st.spinner("倾听中..."):
        with open("temp_v.wav", "wb") as f: f.write(v_data)
        try:
            with open("temp_v.wav", "rb") as f:
                ts = client.audio.transcriptions.create(model="FunAudioLLM/SenseVoiceSmall", file=f)
                final_input = ts.text
        except: st.error("网络波动，没听清...")
        if os.path.exists("temp_v.wav"): os.remove("temp_v.wav")

if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input, "audio": None})
    
    with st.chat_message("user"):
        if final_input == "[用户陷入了沉默]":
            st.markdown("*(你陷入了沉默，静静地看着屏幕...)*")
        else:
            st.markdown(final_input)
    
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            api_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            res = client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3",
                messages=api_messages,
                temperature=0.7
            )
            reply = res.choices[0].message.content
            st.markdown(reply)
            
            audio_bytes = speak(reply, st.session_state.current_voice)
            st.session_state.clarity_score += 5
            
    st.session_state.messages.append({"role": "assistant", "content": reply, "audio": audio_bytes})
    st.rerun()