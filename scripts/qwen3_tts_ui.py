import gradio as gr
from modules import shared
from modules.paths_internal import default_output_dir
import os
import json
import time
from pathlib import Path
import warnings

# 忽略所有与音频处理相关的警告
warnings.filterwarnings("ignore", category=UserWarning)

# 获取 Qwen3-TTS模型路径
qwen_tts_path = os.path.join(shared.models_path, "qwen3-tts")
model_dir = qwen_tts_path  # 直接使用 models/qwen3-tts 目录，不需要 checkpoints 子目录
config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'qwen3_tts')

# 默认输出目录
default_qwen_tts_output = os.path.join(default_output_dir, "qwen3-tts")

# 确保目录存在
os.makedirs(qwen_tts_path, exist_ok=True)
os.makedirs(config_dir, exist_ok=True)

# 全局模型实例
qwen_tts_model = None

def open_output_directory(output_dir_path):
    """
    打开输出目录
    """
    try:
        import subprocess
        import sys
        
        # 确保目录存在
        os.makedirs(output_dir_path, exist_ok=True)
        
        # 根据操作系统打开目录
        if sys.platform == "win32":
            # Windows
            subprocess.run(["explorer", output_dir_path], check=True)
        elif sys.platform == "darwin":
            # macOS
            subprocess.run(["open", output_dir_path], check=True)
        else:
            # Linux
            subprocess.run(["xdg-open", output_dir_path], check=True)
        
        return f"✓ 已打开输出目录：{output_dir_path}"
    except Exception as e:
        error_msg = f"打开目录失败：{str(e)}"
        print(error_msg)
        return error_msg

def initialize_qwen_tts_model(model_name):
    """
    初始化 Qwen3-TTS 模型
    """
    global qwen_tts_model
    try:
        import torch
        
        # 在导入 qwen_tts 之前抑制 sox（因为 qwen_tts 可能依赖 sox）
        import warnings
        import logging
        warnings.filterwarnings("ignore", category=UserWarning, module="sox")
        logging.getLogger("sox").setLevel(logging.CRITICAL)
        
        # 首先检查 qwen_tts 库的兼容性
        try:
            from qwen_tts import Qwen3TTSModel
        except TypeError as e:
            if "check_model_inputs" in str(e):
                error_msg = (
                    "❌ qwen_tts 库兼容性问题！\n\n"
                    f"错误详情：{str(e)}\n\n"
                    "解决方案：\n"
                    "1. 升级 qwen-tts 库到最新版本：\n"
                    "   pip install --upgrade qwen-tts\n\n"
                    "2. 如果已最新版，尝试重新安装：\n"
                    "   pip uninstall -y qwen-tts\n"
                    "   pip install qwen-tts\n\n"
                    "3. 检查 Python 版本（推荐 3.10-3.12）：\n"
                    f"   当前 Python 版本：{torch.__version__ if hasattr(torch, '__version__') else '未知'}\n\n"
                    "4. 重启 WebUI 后重试"
                )
                print(error_msg)
                return error_msg
            raise
        
        # 模型映射 - 支持多个版本
        model_map = {
            "Base": {
                "1.7B": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
                "0.6B": "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
            },
            "CustomVoice": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
            "VoiceDesign": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
        }
        
        if model_name not in model_map:
            return f"错误：未知的模型类型 {model_name}"
        
        # 处理 Base模型的多个版本
        if model_name == "Base":
            # 优先检查本地存在的版本
            base_versions = ["0.6B", "1.7B"]
            found_version = None
            
            for version in base_versions:
                test_path = os.path.join(model_dir, f"Qwen3-TTS-12Hz-{version}-{model_name}")
                if os.path.exists(test_path):
                    found_version = version
                    remote_model_path = model_map[model_name][version]
                    print(f"✓ 检测到 Base模型版本：{version}")
                    break
            
            if not found_version:
                # 默认使用 1.7B
                remote_model_path = model_map["Base"]["1.7B"]
                print("未找到本地 Base模型，将尝试加载 1.7B 版本")
        else:
            remote_model_path = model_map[model_name]
        
        # 检查本地是否有模型 - 增强的路径匹配逻辑
        local_model_path = os.path.join(model_dir, model_name)
        
        # 优先使用本地模型，支持多种目录结构
        possible_local_paths = []
        
        # 根据已确定的 remote_model_path 构建可能的本地路径
        if isinstance(model_map[model_name], dict):
            # Base模型有多个版本，需要检查所有版本
            for version in ["0.6B", "1.7B"]:
                # 完整 HuggingFace 格式（优先级最高）
                possible_local_paths.append(os.path.join(model_dir, f"Qwen3-TTS-12Hz-{version}-{model_name}"))
                # HuggingFace 路径格式转换
                hf_path = model_map[model_name][version]
                possible_local_paths.append(os.path.join(model_dir, hf_path.replace("/", "_")))
                possible_local_paths.append(os.path.join(model_dir, hf_path.replace("/", "--")))
        else:
            # 其他单一版本模型
            # 完整 HuggingFace 格式（优先级最高）
            possible_local_paths.append(os.path.join(model_dir, f"Qwen3-TTS-12Hz-1.7B-{model_name}"))
            # HuggingFace 路径格式转换
            possible_local_paths.append(os.path.join(model_dir, remote_model_path.replace("/", "_")))
            possible_local_paths.append(os.path.join(model_dir, remote_model_path.replace("/", "--")))
        
        # 添加简化格式路径
        possible_local_paths.extend([
            local_model_path,
            os.path.join(model_dir, model_name.lower()),
            os.path.join(model_dir, f"Qwen3-TTS-{model_name}"),
        ])
        
        found_local = False
        for path in possible_local_paths:
            if os.path.exists(path):
                local_model_path = path
                found_local = True
                print(f"✓ 找到本地模型路径：{local_model_path}")
                break
        
        if found_local:
            model_path = local_model_path
            print(f"将使用本地模型加载")
        else:
            model_path = remote_model_path
            print(f"警告：本地未找到模型，将尝试从远程加载")
            print(f"搜索的本地路径：{local_model_path}")
            print(f"远程模型ID: {remote_model_path}")
            print(f"\n提示：请确保模型文件在以下目录之一:")
            for path in possible_local_paths:
                print(f"  - {path}")
        
        print(f"\n正在加载 Qwen3-TTS-{model_name} 模型...")
        print(f"加载路径：{model_path}")
        
        # 准备加载参数 - 始终使用离线模式
        load_kwargs = {
            "device_map": "cuda:0" if torch.cuda.is_available() else "cpu",
            "local_files_only": True,  # 优先使用本地文件
            "low_cpu_mem_usage": True,
            "use_safetensors": True,
        }
        
        # 仅当 CUDA 可用时设置 dtype 和 attention 实现
        if torch.cuda.is_available():
            load_kwargs["torch_dtype"] = torch.bfloat16
            # 检查是否支持 flash attention
            try:
                import flash_attn
                load_kwargs["attn_implementation"] = "flash_attention_2"
                print("启用 Flash Attention 2 加速")
            except ImportError:
                load_kwargs["attn_implementation"] = "sdpa"
                print("未检测到 Flash Attention，使用 SDPA 注意力机制")
        else:
            load_kwargs["torch_dtype"] = torch.float32
        
        # 加载模型
        try:
            model = Qwen3TTSModel.from_pretrained(model_path, **load_kwargs)
        except Exception as local_load_error:
            # 如果本地加载失败，且找到了本地路径，说明是格式问题
            if found_local:
                print(f"本地模型加载失败：{str(local_load_error)}")
                print(f"\n请检查模型目录结构是否正确:")
                print(f"模型目录应包含：config.json, model.safetensors, tokenizer_config.json 等文件")
                raise
            # 否则可能是网络问题，给出明确提示
            else:
                error_str = str(local_load_error)
                if "connect" in error_str.lower() or "timeout" in error_str.lower() or "network" in error_str.lower():
                    raise ConnectionError(
                        f"无法连接到 HuggingFace 服务器。\n"
                        f"请手动下载模型到本地目录"
                    )
                else:
                    raise
        
        qwen_tts_model = {
            "model": model,
            "name": model_name
        }
        
        print(f"\n✓ Qwen3-TTS-{model_name} 模型加载完成！")
        return f"成功加载 Qwen3-TTS-{model_name} 模型"
        
    except ConnectionError as e:
        import traceback
        error_msg = f"网络连接错误：{str(e)}"
        print(error_msg)
        traceback.print_exc()
        return error_msg
    except Exception as e:
        import traceback
        error_msg = f"模型加载失败：{str(e)}"
        print(error_msg)
        traceback.print_exc()
        return error_msg

def transcribe_audio(audio_path):
    """
    使用 Whisper 自动识别参考音频中的文本
    返回识别的文本内容
    """
    try:
        import torch
        from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
        
        # 检查是否已有 Whisper 模型实例
        global whisper_pipe
        if 'whisper_pipe' not in globals() or whisper_pipe is None:
            print("正在加载 Whisper 模型进行语音识别...")
            
            model_id = "openai/whisper-tiny"  # 使用轻量级模型
            
            # 检查本地是否有 Whisper 模型 - 支持多个可能的位置
            possible_paths = [
                os.path.join(shared.models_path, "whisper-tiny"),  # models/whisper-tiny
                os.path.join(shared.models_path, "whisper", "whisper-tiny"),  # models/whisper/whisper-tiny
                os.path.join(shared.models_path, "ASR", "whisper-tiny"),  # models/ASR/whisper-tiny (通用 ASR 模型目录)
            ]
            
            # 优先使用本地模型
            use_local = False
            local_model_path = None
            
            for path in possible_paths:
                if os.path.exists(path):
                    local_model_path = path
                    use_local = True
                    print(f"✓ 找到本地 Whisper 模型：{local_model_path}")
                    break
            
            if not use_local:
                print(f"警告：本地未找到 Whisper 模型，将尝试从远程下载")
                print(f"远程模型 ID: {model_id}")
                print(f"建议手动下载模型到以下位置之一:")
                for path in possible_paths:
                    print(f"  - {path}")
                print(f"\n下载地址：https://huggingface.co/openai/whisper-tiny")
                local_model_path = model_id
            else:
                print(f"将使用本地模型加载")
            
            # 加载处理器和模型
            print(f"\n正在加载 Whisper 处理器...")
            processor = AutoProcessor.from_pretrained(
                local_model_path,
                local_files_only=use_local,  # 本地模式
            )
            
            print(f"正在加载 Whisper 模型权重...")
            model = AutoModelForSpeechSeq2Seq.from_pretrained(
                local_model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                low_cpu_mem_usage=True,
                use_safetensors=True,
                local_files_only=use_local,  # 本地模式
            )
            
            if torch.cuda.is_available():
                model.to("cuda")
            
            whisper_pipe = pipeline(
                "automatic-speech-recognition",
                model=model,
                tokenizer=processor.tokenizer,
                feature_extractor=processor.feature_extractor,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device="cuda" if torch.cuda.is_available() else "cpu",
            )
            print("Whisper 模型加载完成！\n")
        
        # 执行语音识别
        result = whisper_pipe(audio_path)
        recognized_text = result["text"].strip()
        
        print(f"语音识别结果：{recognized_text}")
        return recognized_text
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"语音识别失败：{str(e)}")
        print("\n可能的解决方案:")
        print("1. 检查模型文件是否完整")
        print("2. 确保模型目录包含：config.json, model.safetensors, preprocessor_config.json 等文件")
        print("3. 重启 WebUI 后重试")
        return ""

def generate_speech_base(text, language, ref_audio_path, ref_text, output_dir, use_batch_mode=False, auto_transcribe=False):
    """
    Base 模型 - 语音克隆功能
    支持单次和批量推理，支持自动语音识别
    """
    global qwen_tts_model
    
    if qwen_tts_model is None or qwen_tts_model["name"] != "Base":
        msg = initialize_qwen_tts_model("Base")
        if not msg.startswith("成功"):
            return None, msg
    
    try:
        import torch
        import soundfile as sf
        
        # 如果启用自动识别且未提供参考文本，则自动识别
        actual_ref_text = ref_text
        if auto_transcribe and not ref_text.strip():
            print("正在自动识别参考音频文本...")
            actual_ref_text = transcribe_audio(ref_audio_path)
            
            if not actual_ref_text:
                return None, "语音识别失败，请手动输入参考音频文本"
            
            print(f"✓ 自动识别文本：{actual_ref_text}")
        
        model = qwen_tts_model["model"]
        
        # 打印调试信息
        print(f"\n=== Base模型生成参数 ===")
        print(f"文本：{text[:50]}...")
        print(f"语言：{language}")
        print(f"参考音频：{ref_audio_path}")
        print(f"参考文本：{actual_ref_text[:50] if actual_ref_text else 'None'}...")
        print(f"========================\n")
        
        # 生成语音克隆
        with torch.no_grad():
            wavs, sr = model.generate_voice_clone(
                text=text,
                language=language,
                ref_audio=ref_audio_path,
                ref_text=actual_ref_text,
            )
            
            # 保存音频文件
            os.makedirs(output_dir, exist_ok=True)
            timestamp = int(time.time())
            
            if use_batch_mode and len(wavs) > 1:
                # 批量模式：保存多个文件
                output_files = []
                for i, wav in enumerate(wavs):
                    output_filename = os.path.join(output_dir, f"speech_base_clone_{timestamp}_{i}.wav")
                    sf.write(output_filename, wav, sr)
                    output_files.append(output_filename)
                return output_files[0], f"批量语音克隆成功！已保存 {len(wavs)} 个文件到：{output_dir}"
            else:
                # 单次模式：保存一个文件
                output_filename = os.path.join(output_dir, f"speech_base_clone_{timestamp}.wav")
                sf.write(output_filename, wavs[0], sr)
                return output_filename, f"语音克隆成功！已保存到：{output_filename}"
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"语音克隆失败：{str(e)}"

def generate_speech_customvoice(text, language, speaker, instruct, output_dir, use_batch_mode=False):
    """
    CustomVoice 模型 - 自定义音色功能
    支持 9 种预设说话人和批量推理
    """
    global qwen_tts_model
    
    if qwen_tts_model is None or qwen_tts_model["name"] != "CustomVoice":
        msg = initialize_qwen_tts_model("CustomVoice")
        if not msg.startswith("成功"):
            return None, msg
    
    try:
        import torch
        import soundfile as sf
        
        model = qwen_tts_model["model"]
        
        # 打印调试信息
        print(f"\n=== CustomVoice 生成参数 ===")
        print(f"文本：{text[:50]}...")
        print(f"语言：{language}")
        print(f"说话人：{speaker}")
        print(f"语气指令：{instruct}")
        print(f"========================\n")
        
        # 生成自定义音色
        with torch.no_grad():
            wavs, sr = model.generate_custom_voice(
                text=text,
                language=language,
                speaker=speaker,
                instruct=instruct,
            )
            
            # 保存音频文件
            os.makedirs(output_dir, exist_ok=True)
            timestamp = int(time.time())
            
            if use_batch_mode and len(wavs) > 1:
                # 批量模式：保存多个文件
                output_files = []
                for i, wav in enumerate(wavs):
                    output_filename = os.path.join(output_dir, f"speech_custom_{timestamp}_{i}.wav")
                    sf.write(output_filename, wav, sr)
                    output_files.append(output_filename)
                return output_files[0], f"批量自定义音色成功！已保存 {len(wavs)} 个文件到：{output_dir}"
            else:
                # 单次模式：保存一个文件
                output_filename = os.path.join(output_dir, f"speech_custom_{timestamp}.wav")
                sf.write(output_filename, wavs[0], sr)
                return output_filename, f"自定义音色生成成功！已保存到：{output_filename}"
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"自定义音色生成失败：{str(e)}"

def generate_speech_voicedesign(text, language, instruct, output_dir, use_batch_mode=False):
    """
    VoiceDesign 模型 - 声音设计功能
    支持基于描述的精细控制和批量推理
    """
    global qwen_tts_model
    
    if qwen_tts_model is None or qwen_tts_model["name"] != "VoiceDesign":
        msg = initialize_qwen_tts_model("VoiceDesign")
        if not msg.startswith("成功"):
            return None, msg
    
    try:
        import torch
        import soundfile as sf
        
        model = qwen_tts_model["model"]
        
        # 打印调试信息
        print(f"\n=== VoiceDesign生成参数 ===")
        print(f"文本：{text[:50]}...")
        print(f"语言：{language}")
        print(f"音色描述：{instruct[:100] if instruct else 'None'}...")
        print(f"===========================\n")
        
        # 生成声音设计
        with torch.no_grad():
            wavs, sr = model.generate_voice_design(
                text=text,
                language=language,
                instruct=instruct,
            )
            
            # 保存音频文件
            os.makedirs(output_dir, exist_ok=True)
            timestamp = int(time.time())
            
            if use_batch_mode and len(wavs) > 1:
                # 批量模式：保存多个文件
                output_files = []
                for i, wav in enumerate(wavs):
                    output_filename = os.path.join(output_dir, f"speech_design_{timestamp}_{i}.wav")
                    sf.write(output_filename, wav, sr)
                    output_files.append(output_filename)
                return output_files[0], f"批量声音设计成功！已保存 {len(wavs)} 个文件到：{output_dir}"
            else:
                # 单次模式：保存一个文件
                output_filename = os.path.join(output_dir, f"speech_design_{timestamp}.wav")
                sf.write(output_filename, wavs[0], sr)
                return output_filename, f"声音设计生成成功！已保存到：{output_filename}"
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"声音设计生成失败：{str(e)}"

def generate_speech(text, language, voice_style, model_choice, output_dir, use_batch_mode=False):
    """
    生成语音 - 统一入口函数
    根据选择的模型类型调用相应的生成函数
    """
    if model_choice == "Base":
        return generate_speech_base(text, language, None, voice_style, output_dir, use_batch_mode)
    elif model_choice == "CustomVoice":
        # 对于 CustomVoice，voice_style 作为 speaker 名称
        return generate_speech_customvoice(text, language, voice_style, "", output_dir, use_batch_mode)
    elif model_choice == "VoiceDesign":
        # 对于 VoiceDesign，voice_style 作为 instruct 描述
        return generate_speech_voicedesign(text, language, voice_style, output_dir, use_batch_mode)
    else:
        return None, f"不支持的模型类型：{model_choice}"

def save_voice_preset(preset_name, voice_style, language, model_choice):
    """
    保存音色预设
    """
    try:
        preset_file = os.path.join(config_dir, f"{preset_name}.json")
        preset_data = {
            "name": preset_name,
            "voice_style": voice_style,
            "language": language,
            "model": model_choice,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(preset_file, 'w', encoding='utf-8') as f:
            json.dump(preset_data, f, ensure_ascii=False, indent=2)
        
        return f"音色预设 '{preset_name}' 保存成功！"
    except Exception as e:
        return f"保存失败：{str(e)}"

def load_voice_presets():
    """
    加载已保存的音色预设列表
    """
    try:
        presets = []
        if os.path.exists(config_dir):
            for file in os.listdir(config_dir):
                if file.endswith('.json'):
                    preset_name = file[:-5]  # 去掉 .json 后缀
                    presets.append(preset_name)
        return presets
    except Exception as e:
        return []

def load_preset_data(preset_name):
    """
    加载指定音色预设的数据
    """
    try:
        preset_file = os.path.join(config_dir, f"{preset_name}.json")
        if os.path.exists(preset_file):
            with open(preset_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return {
                "speaker": data.get("speaker", "Vivian"),
                "instruct": data.get("instruct", ""),
                "language": data.get("language", "Chinese"),
                "model": data.get("model", "CustomVoice")
            }
        return {"speaker": "Vivian", "instruct": "", "language": "Chinese", "model": "CustomVoice"}
    except Exception as e:
        return {"speaker": "Vivian", "instruct": "", "language": "Chinese", "model": "CustomVoice"}

def create_qwen3_tts_ui():
    """
    创建 Qwen3-TTS 语音合成 UI
    """
    import time
    
    with gr.Blocks(analytics_enabled=False) as ui:
        # 模型选择
        with gr.Row():
            model_choice = gr.Dropdown(
                label="选择模型",
                choices=[
                    ("Base - 基础模型（支持音频克隆）", "Base"),
                    ("CustomVoice - 自定义音色（9 种预设）", "CustomVoice"),
                    ("VoiceDesign - 声音设计（精细控制）", "VoiceDesign")
                ],
                value="Base",
                info="Base: 基础通用 | CustomVoice: 9 种预设音色 | VoiceDesign: 描述生成"
            )
        
        # Base 模型专用组件
        with gr.Group(visible=True) as base_group:
            gr.Markdown("### 📢 语音克隆模式（Base）")
            ref_audio_input = gr.Audio(
                label="参考音频（3 秒左右）", 
                type="filepath"
            )
            
            with gr.Row():
                auto_transcribe_checkbox = gr.Checkbox(
                    label="🎤 自动识别音频文本（推荐）",
                    value=True,
                    info="启用后将使用 AI 自动识别参考音频中的文字，无需手动输入"
                )
            
            ref_text_input = gr.Textbox(
                label="参考音频文本（可选）",
                placeholder="如果不启用自动识别，请手动输入参考音频对应的文本内容...",
                lines=2,
                info="参考音频中说的内容，用于帮助模型学习音色。启用自动识别后可留空"
            )
        
        # CustomVoice 模型专用组件
        with gr.Group(visible=False) as customvoice_group:
            gr.Markdown("### 🎤 自定义音色模式（CustomVoice）")
            speaker_dropdown = gr.Dropdown(
                label="选择说话人",
                choices=[
                    ("Vivian - 明亮、略带锐气的年轻女声（中文）", "Vivian"),
                    ("Serena - 温暖柔和的年轻女声（中文）", "Serena"),
                    ("Uncle_Fu - 音色低沉醇厚的成熟男声（中文）", "Uncle_Fu"),
                    ("Dylan - 清晰自然的北京青年男声（中文·北京方言）", "Dylan"),
                    ("Eric - 活泼、略带沙哑明亮感的成都男声（中文·四川方言）", "Eric"),
                    ("Ryan - 富有节奏感的动态男声（英语）", "Ryan"),
                    ("Aiden - 清晰中频的阳光美式男声（英语）", "Aiden"),
                    ("Ono_Anna - 轻快灵活的俏皮日语女声（日语）", "Ono_Anna"),
                    ("Sohee - 富含情感的温暖韩语女声（韩语）", "Sohee"),
                ],
                value="Vivian",
                info="建议选择对应说话人的母语以获得最佳音质"
            )
            custom_instruct = gr.Textbox(
                label="语气指令（可选）",
                placeholder="例如：用特别愤怒的语气说、非常开心地说、低声细语...",
                lines=2,
                info="控制说话的语气和情感，留空则使用自然语气"
            )
        
        # VoiceDesign 模型专用组件
        with gr.Group(visible=False) as voicedesign_group:
            gr.Markdown("### 🎨 声音设计模式（VoiceDesign）")
            design_instruct = gr.Textbox(
                label="音色描述",
                placeholder="例如：体现撒娇稚嫩的萝莉女声，音调偏高且起伏明显，营造出黏人、做作又刻意卖萌的听觉效果。",
                lines=3,
                info="详细描述你想要的音色特征，包括年龄、性别、情感、语调等"
            )
        
        # 通用组件
        with gr.Row():
            with gr.Column(scale=2):
                text_input = gr.Textbox(
                    label="输入文本",
                    placeholder="请输入要合成的文本（支持多语言，最多 2000 字符）",
                    lines=4,
                    max_lines=8
                )
                
                language = gr.Dropdown(
                    label="语言",
                    choices=[
                        ("中文", "Chinese"),
                        ("英文", "English"),
                        ("日文", "Japanese"),
                        ("韩文", "Korean"),
                        ("德文", "German"),
                        ("法文", "French"),
                        ("俄文", "Russian"),
                        ("葡萄牙文", "Portuguese"),
                        ("西班牙文", "Spanish"),
                        ("意大利文", "Italian"),
                    ],
                    value="Chinese",
                    info="Auto 可自动检测，但建议明确指定以获得最佳效果"
                )
            
            with gr.Column(scale=1):
                # 输出目录显示和打开按钮
                with gr.Group():
                    output_dir_display = gr.Textbox(
                        label="输出目录路径",
                        value=default_qwen_tts_output,
                        interactive=False,
                        info="生成的音频文件将保存在此目录"
                    )
                    
                    open_dir_btn = gr.Button(
                        "📁 打开输出目录",
                        variant="secondary",
                        size="sm"
                    )
                
                batch_mode = gr.Checkbox(
                    label="批量模式（实验性）",
                    value=False,
                    info="启用后可一次性生成多个音频文件"
                )
        
        # 生成按钮
        generate_btn = gr.Button("🎵 生成语音", variant="primary", size="lg")
        
        # 结果展示
        with gr.Row():
            audio_output = gr.Audio(label="生成的音频", type="filepath")
            status_info = gr.Textbox(
                label="操作状态",
                lines=2,
                interactive=False
            )
        
        # 音色预设
        with gr.Accordion("💾 音色预设管理", open=False):
            preset_name_input = gr.Textbox(
                label="预设名称",
                placeholder="输入预设名称，如：温柔女声 - 愤怒",
                lines=1
            )
            
            with gr.Row():
                save_preset_btn = gr.Button("保存当前配置为预设", variant="secondary")
            
            preset_list = gr.Dropdown(
                label="加载已有预设",
                choices=[],
                value=None,
                info="选择预设将自动填充下方配置"
            )
        
        # 使用说明
        with gr.Accordion("📖 使用说明", open=False):
            gr.Markdown("""
            ### Base 模型 - 语音克隆
            1. 上传 3 秒左右的参考音频
            2. ✅ **推荐**：启用"自动识别音频文本"，AI 会自动识别音频中的内容
            3. 如果不启用自动识别，需要手动输入参考音频的文本内容
            4. 输入要生成的新文本
            5. 点击生成即可克隆音色
            
            **自动识别优势**：
            - 🎯 无需手动输入，节省时间
            - 🔍 AI 精准识别，准确率高
            - 🌍 支持多语言自动检测
            - ⚡ 使用轻量级 Whisper-tiny 模型，速度快
            
            ### CustomVoice 模型 - 自定义音色
            1. 从 9 种预设说话人中选择
            2. 可选：输入语气指令控制情感
            3. 输入要生成的文本
            4. 点击生成即可获得定制化音色
            
            ### VoiceDesign 模型 - 声音设计
            1. 详细描述想要的音色特征
            2. 描述越详细，效果越精准
            3. 示例："体现撒娇稚嫩的萝莉女声，音调偏高且起伏明显"
            4. 输入要生成的文本
            5. 点击生成即可创造独特音色
            
            ### 批量推理
            - 在文本框中输入多行文本，每行作为一句
            - 启用"批量模式"复选框
            - 生成的多个音频文件会分别保存
            
            **提示**：首次生成需要下载模型（约 3-4GB），请耐心等待。
            """)
        
        # 切换模型时显示/隐藏对应组件
        def on_model_change(model_type):
            base_visible = model_type == "Base"
            custom_visible = model_type == "CustomVoice"
            design_visible = model_type == "VoiceDesign"
            
            return (
                gr.update(visible=base_visible),
                gr.update(visible=custom_visible),
                gr.update(visible=design_visible)
            )
        
        model_choice.change(
            fn=on_model_change,
            inputs=[model_choice],
            outputs=[base_group, customvoice_group, voicedesign_group]
        )
        
        # 生成逻辑
        def on_generate(text, language, model_type, ref_audio, ref_text, 
                       speaker, custom_instruct, design_instruct, 
                       output_dir, batch_mode, auto_transcribe):
            if not text.strip():
                return None, "错误：请输入要合成的文本"
            
            if model_type == "Base":
                if not ref_audio:
                    return None, "错误：Base 模型需要上传参考音频"
                
                # 如果未启用自动识别且没有手动输入文本，则报错
                if not auto_transcribe and not ref_text.strip():
                    return None, "错误：请启用自动识别或手动输入参考音频文本"
                
                return generate_speech_base(
                    text=text,
                    language=language,
                    ref_audio_path=ref_audio,
                    ref_text=ref_text if not auto_transcribe else "",
                    output_dir=output_dir,
                    use_batch_mode=batch_mode,
                    auto_transcribe=auto_transcribe
                )
            elif model_type == "CustomVoice":
                instruct_text = custom_instruct.strip() if custom_instruct else ""
                return generate_speech_customvoice(
                    text=text,
                    language=language,
                    speaker=speaker,
                    instruct=instruct_text,
                    output_dir=output_dir,
                    use_batch_mode=batch_mode
                )
            elif model_type == "VoiceDesign":
                if not design_instruct.strip():
                    return None, "错误：VoiceDesign 模型需要输入音色描述"
                return generate_speech_voicedesign(
                    text=text,
                    language=language,
                    instruct=design_instruct.strip(),
                    output_dir=output_dir,
                    use_batch_mode=batch_mode
                )
            else:
                return None, f"错误：不支持的模型类型 {model_type}"
        
        generate_btn.click(
            fn=on_generate,
            inputs=[
                text_input, language, model_choice, 
                ref_audio_input, ref_text_input,
                speaker_dropdown, custom_instruct, design_instruct,
                output_dir_display, batch_mode, auto_transcribe_checkbox
            ],
            outputs=[audio_output, status_info]
        )
        
        # 打开输出目录按钮事件
        open_dir_btn.click(
            fn=open_output_directory,
            inputs=[output_dir_display],
            outputs=[status_info]
        )
        
        # 预设功能
        def update_preset_list():
            presets = load_voice_presets()
            return gr.update(choices=presets)
        
        def on_preset_selected(preset_name):
            if preset_name:
                data = load_preset_data(preset_name)
                return (
                    data.get("speaker", "Vivian"),
                    data.get("instruct", ""),
                    data.get("language", "Chinese"),
                    f"已加载预设：{preset_name}"
                )
            return "Vivian", "", "Chinese", ""
        
        ui.load(fn=update_preset_list, outputs=[preset_list])
        
        save_preset_btn.click(
            fn=lambda name, speaker, instruct, lang, model: save_voice_preset(
                name, instruct, lang, model, {"speaker": speaker}
            ),
            inputs=[preset_name_input, speaker_dropdown, custom_instruct, language, model_choice],
            outputs=[status_info]
        ).then(
            fn=update_preset_list,
            outputs=[preset_list]
        )
        
        preset_list.change(
            fn=on_preset_selected,
            inputs=[preset_list],
            outputs=[speaker_dropdown, custom_instruct, language, status_info]
        )
    
    return ui
