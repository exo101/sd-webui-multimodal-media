import gradio as gr
from modules import script_callbacks

def multimodal_media_tab():
    with gr.Blocks(analytics_enabled=False) as ui:
        with gr.Tabs():
            # Index-TTS语音合成标签页
            with gr.TabItem("1.Index-TTS语音合成"):
                try:
                    from scripts.index_tts_ui import create_index_tts_ui
                    # 创建并添加Index-TTS功能
                    index_tts_components = create_index_tts_ui()
                except Exception as e:
                    gr.Markdown(f"Index-TTS模块初始化错误: {e}")
                    import traceback
                    traceback.print_exc()

            # 数字人视频生成标签页
            with gr.TabItem("2.数字人对口型生成"):
                try:
                    from scripts.latent_sync_ui import create_latent_sync_ui
                    # 创建并添加数字人视频生成功能
                    latent_sync_components = create_latent_sync_ui()
                except Exception as e:
                    gr.Markdown(f"数字人视频生成模块初始化错误: {e}")
                    import traceback
                    traceback.print_exc()

            # 视频关键帧提取标签页
            with gr.TabItem("3.视频关键帧提取"):
                try:
                    from scripts.video_frame_extractor import create_video_frame_extractor
                    # 创建并添加视频分帧组件
                    video_frame_components = create_video_frame_extractor()
                    
                    # 将视频分帧组件解包
                    video_input = video_frame_components["video_input"]
                    frame_output = video_frame_components["frame_output"]
                    frame_quality = video_frame_components["frame_quality"]
                    frame_mode = video_frame_components["frame_mode"]
                    frame_preview = video_frame_components["frame_preview"]
                    extract_video_frames = video_frame_components["extract_video_frames"]
                    
                    # 绑定按钮点击事件
                    extract_button = gr.Button("提取关键帧")
                    extract_button.click(
                        fn=extract_video_frames,
                        inputs=[video_input, frame_output, frame_quality, frame_mode],
                        outputs=[gr.File(label="提取的帧文件"), frame_preview]
                    )
                except Exception as e:
                    gr.Markdown(f"视频关键帧提取模块初始化错误: {e}")
                    import traceback
                    traceback.print_exc()

            # Qwen视频生成API调用标签页
            with gr.TabItem("4.wan系列视频生成API调用"):
                try:
                    from scripts.qwen_video.main_ui import create_qwen_video_gen_ui
                    # 创建 wan 系列视频生成 UI 组件
                    qwen_video_gen_components = create_qwen_video_gen_ui()
                    
                    # 组件已经自动显示，无需额外处理
                    if not qwen_video_gen_components:
                        gr.Markdown("wan系列视频生成模块加载失败")
                except Exception as e:
                    gr.Markdown(f"wan系列视频生成模块初始化错误: {e}")
                    import traceback
                    traceback.print_exc()

    return [(ui, "多媒体处理", "multimodal_media_tab")]

# 注册UI标签页
script_callbacks.on_ui_tabs(multimodal_media_tab)