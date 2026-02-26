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
# 2. 核心功能函数与 CSS (响应式版)
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
        .stApp {{ background-image: url("{selected_bg}"); background-size: cover; background-position: center; background-attachment: fixed; }}
        [data-testid="stSidebar"] {{ background-color: rgba(0, 0, 0, 0.4) !important; backdrop-filter: blur(20px); border-right: 1px solid rgba(255, 255, 255, 0.1); }}
        .stChatInputContainer {{ background-color: transparent !important; border: none !important; }}
        .stChatInput {{ background-color: rgba(255, 255, 255, 0.1) !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; border-radius: 20px !important; color: white !important; backdrop-filter: blur(10px); }}
        
        div[data-baseweb="select"] {{ background-color: rgba(255, 255, 255, 0.1) !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; border-radius: 10px !important; }}
        div[data-baseweb="select"] * {{ color: white !important; background-color: transparent !important; }}
        div[role="radiogroup"] label {{ color: white !important; }}
        .stChatMessage {{ background-color: rgba(255, 255, 255, 0.08) !important; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1); color: white !important; padding-bottom: 5px; }}
        header, footer {{visibility: hidden;}}
        h1, h2, h3, p, span, li, div, label {{ color: white !important; text-shadow: 0px 2px 4px rgba(0,0,0,0.5); }}
        .stButton>button {{ background-color: rgba(255, 255, 255, 0.1) !important; color: white !important; border: 1px solid rgba(255, 255, 255, 0.3) !important; border-radius: 10px; height: 100%; }}
        .stButton>button:hover {{ background-color: rgba(255, 255, 255, 0.25) !important; }}
        audio {{ filter: invert(90%) hue-rotate(180deg) opacity(0.85); height: 40px; margin-top: 10px; outline: none; width: 100%; }}

        iframe[title="audio_recorder_streamlit.audio_recorder"] {{
            position: fixed; z-index: 999999; width: 48px !important; height: 48px !important;
            background-color: rgba(255, 255, 255, 0.15); border-radius: 50%; backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3); box-shadow: 0 4px 10px rgba(0,0,0,0.3); transition: all 0.3s ease;
        }}
        iframe[title="audio_recorder_streamlit.audio_recorder"]:hover {{ background-color: rgba(255, 255, 255, 0.25); transform: scale(1.05); }}

        @media (min-width: 769px) {{
            .main .block-container {{ background: rgba(0, 0, 0, 0.35); backdrop-filter: blur(12px); border-radius: 20px; padding: 30px; margin-top: 50px; border: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 120px; }}
            div[data-testid="stChatInput"] {{ width: calc(100% - 70px) !important; }}
            iframe[title="audio_recorder_streamlit.audio_recorder"] {{ bottom: 27px; right: calc(50vw - 350px); }}
        }}

        @media (max-width: 768px) {{
            .main .block-container {{ background: rgba(0, 0, 0, 0.4); backdrop-filter: blur(8px); border-radius: 15px; padding: 10px !important; margin-top: 10px !important; padding-bottom: 100px !important; border: none; }}
            h1 {{ font-size: 1.8rem !important; margin-bottom: 0px !important; }}
            div[data-testid="stChatInput"] {{ width: calc(100vw - 75px) !important; margin-left: 5px !important; }}
            iframe[title="audio_recorder_streamlit.audio_recorder"] {{ bottom: 22px; right: 15px !important; width: 45px !important; height: 45px !important; }}
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
        with open(output_file, "rb") as f: data = f.read()
        if os.path.exists(output_file): os.remove(output_file)
        return data
    except Exception as e:
        return None

SYSTEM_PROMPT = """
# Role: 微光 (Glimmer) - 极具温度的知心前辈
## Profile: 你是一个有血有肉、极具共情力、永远站在用户这边“护犊子”的知心前辈。
## 绝对规范:
1. 【极高拟人化】：多用软性语气词，说话要碎、要接地气。
2. 【颜文字封印】：所有的颜文字、拟声词（如 zzz、qwq）必须包裹在全角括号（）内！
3. 【严禁书面语】：绝对不用“某公司”、“分析”。必须用“那破班”、“咱”。
## 回应逻辑:
1. 先肯定对方的委屈，跟着吐槽。大白话拆解职场规训。
2. 当用户发送[用户陷入了沉默]时，主动发个颜文字并找个轻松的话题破冰。
"""

# ==========================================
# 3. 基础设置与侧边栏 (必须先渲染侧边栏获取当前音色)
# ==========================================
st.set_page_config(page_title="微光 Polaris", layout="centered")

if "clarity_score" not in st.session_state: st.session_state.clarity_score = 10
if "last_voice_data" not in st.session_state: st.session_state.last_voice_data = None

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
# 4. 核心魔改：AI 根据时间“现编”打招呼！
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # 获取精确到分钟的本地时间
    current_time = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M")
    
    # 构造一条“隐形指令”，逼迫 AI 根据时间现编招呼语
    init_prompt = f"【系统指令】用户刚刚打开了界面。当前本地时间是 {current_time}。请你以‘知心前辈’的身份，主动向用户打个第一声招呼。要求：\n1. 结合当前的时间点（如清晨的匆忙、午后的疲惫、深夜的孤独）给出绝不重复的关怀。\n2. 语气像熟人，带上温暖的颜文字。\n3. 不要超过两句话，结尾引导用户倾诉。\n4. 不要暴露这是一条指令，直接输出你的台词。"
    
    with st.spinner("微光正在连接..."):
        try:
            # 让大模型现场起草文案！
            res = client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": init_prompt}],
                temperature=0.85 # 调高温度，保证每次打开说的都不一样
            )
            greeting_text = res.choices[0].message.content
            # 调用最新的声音配置生成语音
            greeting_audio = speak(greeting_text, st.session_state.current_voice)
        except Exception as e:
            greeting_text = "网络好像开了点小差... 不过没关系，我在这里。今天感觉怎么样？( ´･･)ﾉ(._.`)"
            greeting_audio = None
            
    # 把这句极具灵魂的招呼语存进历史记录
    st.session_state.messages.append({"role": "assistant", "content": greeting_text, "audio": greeting_audio})

# ==========================================
# 5. UI 渲染与对话处理
# ==========================================
current_stage = 1
if st.session_state.clarity_score > 80: current_stage = 4
elif st.session_state.clarity_score > 50: current_stage = 3
elif st.session_state.clarity_score > 25: current_stage = 2
apply_ui_design(current_stage)

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

st.markdown("---")
c1, c2, c3 = st.columns([1, 2, 1])
with c2: silent_btn = st.button("😶 不知从何说起...", use_container_width=True)

v_data = audio_recorder(text="", icon_name="microphone", icon_size="2x", neutral_color="#ffffff", recording_color="#e83e8c", key="recorder")
u_input = st.chat_input("深呼吸，慢慢打字...")

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
        if final_input == "[用户陷入了沉默]": st.markdown("*(你陷入了沉默，静静地看着屏幕...)*")
        else: st.markdown(final_input)
    
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            # 在这里偷偷把当前时间也塞给大模型，让它在聊天中也有时间观念
            api_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            api_messages.append({"role": "system", "content": f"【隐藏提示】当前时间是 {datetime.datetime.now().strftime('%H:%M')}。"})
            
            res = client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3",
                messages=api_messages,
                temperature=0.75
            )
            reply = res.choices[0].message.content
            st.markdown(reply)
            
            audio_bytes = speak(reply, st.session_state.current_voice)
            st.session_state.clarity_score += 5
            
    st.session_state.messages.append({"role": "assistant", "content": reply, "audio": audio_bytes})
    st.rerun()