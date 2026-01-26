import os

def find_json_files(root_dir):
    """查找目录中的所有JSON文件"""
    json_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.json'):
                full_path = os.path.join(dirpath, filename)
                json_files.append(full_path)
                print(f"Found JSON file: {full_path}")
    return json_files

if __name__ == "__main__":
    model_dir = r"d:\sd-webui-forge-aki-v5.1\models\HeartMuLa"
    print(f"Searching for JSON files in: {model_dir}")
    json_files = find_json_files(model_dir)
    
    print(f"\nTotal JSON files found: {len(json_files)}")
    
    # 检查是否已有tokenizer.json或gen_config.json
    tokenizer_exists = any('tokenizer.json' in f for f in json_files)
    gen_config_exists = any('gen_config.json' in f for f in json_files)
    
    print(f"tokenizer.json exists: {tokenizer_exists}")
    print(f"gen_config.json exists: {gen_config_exists}")