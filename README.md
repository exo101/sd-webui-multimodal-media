# 多模态媒体（音频/视频）扩展

本扩展用于处理音频与视频相关功能，包括：
这些功能已从原 sd-webui-MultiModal 扩展中拆分出来，以降低内存占用。

## 功能说明

1. **Index-TTS 语音合成** —— 高质量语音克隆与文本转语音
2. **数字人唇形同步生成** —— 生成唇形与语音同步的视频
3. **视频帧提取** —— 从视频中提取关键帧
4. **wan 视频生成 API** —— 通过 API 使用模型生成视频

## 安装方法

本扩展为独立插件，只需与原始 MultiModal 扩展一同安装，即可使用多媒体处理功能。

## 插件模型目录
| 整合包目录 | 模型目录 | 子目录 |说明 |
|---------------------|--------|-----------|-----------|
| `sd-webui-forge-aki`|`models`|`LatentSync`| 数字人视频生成模型目录 |
| `sd-webui-forge-aki`|`models`|`index-tts2`| Index-TTS语音合成模型目录 |
| `C:`|`ffmpeg\`| 语音与视频合成依赖文件 |

语音合成

<img width="1792" height="892" alt="QQ20260123-173638" src="https://github.com/user-attachments/assets/676af2e8-0f54-4162-8ac2-94536cb1d3f9" />

数字人生成

<img width="1789" height="756" alt="QQ20260123-173659" src="https://github.com/user-attachments/assets/e4144be8-b530-48b0-b550-68db807b656c" />

视频关键帧提取

<img width="1802" height="807" alt="QQ20260123-173712" src="https://github.com/user-attachments/assets/ca4a5849-3c62-46fa-beb7-aa36ae309b85" />

视频生成wan系列

<img width="1774" height="796" alt="QQ20260123-173721" src="https://github.com/user-attachments/assets/e1c812d6-0163-41fa-8131-994862c82e30" />


## 使用方式

安装完成后，在 WebUI 中会出现“多媒体处理”标签页，可在其中使用上述所有功能。
