#!/usr/bin/env python3
"""
阿里云 NLS TTS 脚本 - 长文本分段生成
支持：知达(zhida)、知猫(zhimao)、知说(zhishuo)等音色
"""

import argparse
import sys
import os
import json
import time
import subprocess
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def split_text(text, max_chars=2800):
    """将长文本按段落分割成小块"""
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # 如果当前段落加上已有内容超过限制，保存当前块
        if len(current_chunk) + len(para) > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
    
    # 添加最后一个块
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def generate_audio_nls(text, output_file, voice="zhida", speech_rate=50, pitch_rate=30, volume=50, app_key=None, access_key=None):
    """使用阿里云 NLS 生成音频"""
    try:
        import nls
    except ImportError:
        print("错误：请先安装阿里云 NLS SDK: pip install alibabacloud-nls-python-sdk")
        return False
    
    if not app_key or not access_key:
        # 尝试从环境变量读取
        app_key = os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_ID')
        access_key = os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
        
        if not app_key or not access_key:
            print("错误：需要提供阿里云 AppKey 和 AccessKey")
            print("设置环境变量：")
            print("  export ALIBABA_CLOUD_ACCESS_KEY_ID=your_key_id")
            print("  export ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_key_secret")
            return False
    
    # 音色映射
    voice_map = {
        "zhida": "zhida",
        "zhimao": "zhimao",
        "zhishuo": "zhishuo",
        "zhixiang": "zhixiang",
        "zhichu": "zhichu",
        "zhide": "zhide",
        "zhigang": "zhigang"
    }
    
    voice_name = voice_map.get(voice, voice)
    
    URL = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1"
    
    class NlsResult:
        def __init__(self):
            self.audio_data = bytearray()
            self.complete = False
        
        def on_message(self, message, *args):
            try:
                result = json.loads(message)
                if result.get("name") == "SynthesisCompleted":
                    self.complete = True
                elif "payload" in result and "audio" in result["payload"]:
                    import base64
                    audio = base64.b64decode(result["payload"]["audio"])
                    self.audio_data.extend(audio)
            except Exception as e:
                print(f"处理消息错误: {e}")
        
        def on_error(self, message, *args):
            print(f"NLS 错误: {message}")
        
        def on_close(self, *args):
            pass
        
        def on_open(self, *args):
            pass
    
    result = NlsResult()
    
    # 构建 TTS 参数
    tts = nls.NlsSpeechSynthesizer(
        url=URL,
        akid=app_key,
        aksecret=access_key,
        appkey="default",
        on_message=result.on_message,
        on_error=result.on_error,
        on_close=result.on_close,
        on_open=result.on_open
    )
    
    # 开始合成
    tts.start(
        text=text,
        voice=voice_name,
        aformat="mp3",
        sample_rate=16000,
        speech_rate=speech_rate,
        pitch_rate=pitch_rate,
        volume=volume
    )
    
    # 等待完成
    timeout = 60
    start_time = time.time()
    while not result.complete and time.time() - start_time < timeout:
        time.sleep(0.1)
    
    if result.audio_data:
        with open(output_file, 'wb') as f:
            f.write(result.audio_data)
        return True
    
    return False

def generate_audio_dashscope(text, output_file, voice="zhida", speech_rate=50, volume=50):
    """使用 DashScope API 生成音频"""
    try:
        import dashscope
    except ImportError:
        print("错误：请先安装 dashscope: pip install dashscope")
        return False
    
    # 从环境变量获取 API key
    api_key = os.environ.get('DASHSCOPE_API_KEY')
    if not api_key:
        print("错误：需要设置 DASHSCOPE_API_KEY 环境变量")
        return False
    
    dashscope.api_key = api_key
    
    # 音色映射
    voice_map = {
        "zhida": "sambert-zhida-v1",
        "zhimao": "sambert-zhimao-v1",
        "zhishuo": "sambert-zhishuo-v1",
        "zhixiang": "sambert-zhixiang-v1",
        "zhichu": "sambert-zhichu-v1",
        "zhide": "sambert-zhide-v1",
    }
    
    voice_name = voice_map.get(voice, f"sambert-{voice}-v1")
    
    # 语速转换：50是正常，范围-500到500
    rate_str = f"{speech_rate - 50}"
    
    try:
        result = dashscope.audio.tts.call(
            model=voice_name,
            text=text,
            sample_rate=48000,
            rate=rate_str,
            volume=volume
        )
        
        if result.get_audio_data():
            with open(output_file, 'wb') as f:
                f.write(result.get_audio_data())
            return True
        else:
            print(f"生成失败: {result}")
            return False
    except Exception as e:
        print(f"DashScope 错误: {e}")
        return False

def generate_audio_curl(text, output_file, voice="zhida", speech_rate=0, volume=50):
    """使用 curl 调用 DashScope API 生成音频"""
    api_key = os.environ.get('DASHSCOPE_API_KEY')
    if not api_key:
        print("错误：需要设置 DASHSCOPE_API_KEY 环境变量")
        return False
    
    voice_map = {
        "zhida": "sambert-zhida-v1",
        "zhimao": "sambert-zhimao-v1",
        "zhishuo": "sambert-zhishuo-v1",
        "zhixiang": "sambert-zhixiang-v1",
    }
    voice_name = voice_map.get(voice, f"sambert-{voice}-v1")
    
    # 转义文本中的特殊字符
    text_escaped = json.dumps(text)
    
    # 构建请求
    url = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/speech"
    
    payload = {
        "model": voice_name,
        "input": {"text": text},
        "parameters": {
            "sample_rate": 48000,
            "volume": volume
        }
    }
    
    if speech_rate != 0:
        payload["parameters"]["rate"] = speech_rate
    
    # 保存 payload 到临时文件
    temp_json = "/tmp/tts_payload.json"
    with open(temp_json, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False)
    
    cmd = [
        "curl", "-s", "-X", "POST",
        "-H", f"Authorization: Bearer {api_key}",
        "-H", "Content-Type: application/json",
        "-d", f"@{temp_json}",
        url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        
        # 检查是否是音频数据
        if result.stdout[:4] == b'\xff\xfb' or result.stdout[:4] == b'ID3\x03':
            with open(output_file, 'wb') as f:
                f.write(result.stdout)
            return True
        else:
            # 可能是 JSON 错误
            try:
                error_json = json.loads(result.stdout)
                print(f"API 错误: {error_json}")
            except:
                print(f"响应: {result.stdout[:500]}")
            return False
    except Exception as e:
        print(f"curl 错误: {e}")
        return False

def merge_audio_files(input_files, output_file):
    """合并多个音频文件"""
    if len(input_files) == 1:
        os.rename(input_files[0], output_file)
        return True
    
    # 使用 ffmpeg 合并
    list_file = "/tmp/audio_list.txt"
    with open(list_file, 'w') as f:
        for audio_file in input_files:
            f.write(f"file '{audio_file}'\n")
    
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-acodec", "libmp3lame",
        "-q:a", "2",
        output_file
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        return result.returncode == 0
    except Exception as e:
        print(f"ffmpeg 错误: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='阿里云 TTS 生成脚本')
    parser.add_argument('-f', '--file', required=True, help='输入文本文件')
    parser.add_argument('-o', '--output', required=True, help='输出 MP3 文件')
    parser.add_argument('-v', '--voice', default='zhida', help='音色 (zhida/zhimao/zhishuo/zhixiang)')
    parser.add_argument('-s', '--speech-rate', type=int, default=50, help='语速 (0-100, 默认50)')
    parser.add_argument('-p', '--pitch-rate', type=int, default=30, help='语调 (0-100, 默认30)')
    parser.add_argument('--volume', type=int, default=50, help='音量 (0-100, 默认50)')
    parser.add_argument('--method', default='dashscope', help='方法: dashscope/curl')
    parser.add_argument('--max-chars', type=int, default=2800, help='每段最大字符数')
    parser.add_argument('--no-split', action='store_true', help='不分割文本')
    
    args = parser.parse_args()
    
    # 读取输入文件
    with open(args.file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"读取文本: {len(text)} 字符")
    
    # 分割文本
    if args.no_split or len(text) <= args.max_chars:
        chunks = [text]
    else:
        chunks = split_text(text, args.max_chars)
    
    print(f"分割为 {len(chunks)} 段")
    
    # 生成每段音频
    output_dir = os.path.dirname(args.output) or "."
    os.makedirs(output_dir, exist_ok=True)
    
    base_name = Path(args.output).stem
    audio_files = []
    
    for i, chunk in enumerate(chunks):
        chunk_file = f"{output_dir}/{base_name}_part{i+1}.mp3"
        print(f"生成第 {i+1}/{len(chunks)} 段音频 ({len(chunk)} 字符)...")
        
        # 显示部分内容
        preview = chunk[:100].replace('\n', ' ')
        print(f"  内容: {preview}...")
        
        if args.method == 'dashscope':
            success = generate_audio_dashscope(chunk, chunk_file, args.voice, args.speech_rate, args.volume)
        elif args.method == 'curl':
            success = generate_audio_curl(chunk, chunk_file, args.voice, args.speech_rate - 50, args.volume)
        else:
            success = generate_audio_nls(chunk, chunk_file, args.voice, args.speech_rate, args.pitch_rate, args.volume)
        
        if success:
            print(f"  ✓ 已保存: {chunk_file}")
            audio_files.append(chunk_file)
        else:
            print(f"  ✗ 生成失败")
            return 1
        
        time.sleep(1)  # 避免请求过快
    
    # 合并音频
    if len(audio_files) > 1:
        print(f"合并 {len(audio_files)} 个音频文件...")
        if merge_audio_files(audio_files, args.output):
            print(f"✓ 已保存完整音频: {args.output}")
            # 清理临时文件
            for f in audio_files:
                os.remove(f)
        else:
            print("✗ 合并失败")
            return 1
    else:
        os.rename(audio_files[0], args.output)
        print(f"✓ 已保存: {args.output}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
