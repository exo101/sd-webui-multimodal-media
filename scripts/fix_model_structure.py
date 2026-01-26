import os
import shutil
from pathlib import Path

def fix_model_structure():
    """
    修复HeartMuLa模型结构，将必要的文件从子目录复制到父目录
    """
    model_base_path = Path("d:/sd-webui-forge-aki-v5.1/models/HeartMuLa")
    mula_model_path = model_base_path / "HeartMuLa-oss-3B"
    
    # 检查模型目录是否存在
    if not model_base_path.exists():
        print(f"模型基础路径不存在: {model_base_path}")
        return False
    
    if not mula_model_path.exists():
        print(f"HeartMuLa模型路径不存在: {mula_model_path}")
        return False
    
    # 查找可能的tokenizer文件
    tokenizer_candidates = [
        "tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt"
    ]
    
    found_tokenizer = False
    for candidate in tokenizer_candidates:
        source_path = mula_model_path / candidate
        target_path = model_base_path / "tokenizer.json"
        if source_path.exists():
            print(f"复制 {source_path} -> {target_path}")
            shutil.copy2(source_path, target_path)
            found_tokenizer = True
            break
    
    if not found_tokenizer:
        print("警告: 未找到tokenizer文件")
    
    # 查找可能的配置文件作为gen_config.json
    config_candidates = [
        "config.json", "generation_config.json", "special_tokens_map.json"
    ]
    
    found_config = False
    for candidate in config_candidates:
        source_path = mula_model_path / candidate
        target_path = model_base_path / "gen_config.json"
        if source_path.exists():
            print(f"复制 {source_path} -> {target_path}")
            shutil.copy2(source_path, target_path)
            found_config = True
            break
    
    if not found_config:
        print("警告: 未找到生成配置文件")
    
    print("模型结构修复完成")
    return True

if __name__ == "__main__":
    fix_model_structure()