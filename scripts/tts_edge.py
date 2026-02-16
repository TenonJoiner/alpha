#!/usr/bin/env python3
"""
使用 Microsoft Edge TTS 生成播客音频
免费、无需API Key
"""

import argparse
import sys
import os
import asyncio
import subprocess
from pathlib import Path

def split_text(text, max_chars=2800):
    """将长文本按段落分割成小块"""
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        if len(current_chunk) + len(para) > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

async def generate_audio_edge(text, output_file, voice="zh-CN-YunxiNeural"):
    """使用 Edge TTS 生成音频"""
    try:
        import edge_tts
    except ImportError:
        print("错误：请安装 edge-tts: pip install edge-tts")
        return False
    
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)
        return True
    except Exception as e:
        print(f"Edge TTS 错误: {e}")
        return False

def merge_audio_files(input_files, output_file):
    """合并多个音频文件"""
    if len(input_files) == 1:
        os.rename(input_files[0], output_file)
        return True
    
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
    parser = argparse.ArgumentParser(description='Edge TTS 播客生成脚本')
    parser.add_argument('-f', '--file', required=True, help='输入文本文件')
    parser.add_argument('-o', '--output', required=True, help='输出 MP3 文件')
    parser.add_argument('-v', '--voice', default='zh-CN-YunxiNeural', 
                        help='音色 (默认: zh-CN-YunxiNeural 男声)')
    parser.add_argument('--max-chars', type=int, default=2800, help='每段最大字符数')
    
    args = parser.parse_args()
    
    with open(args.file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"读取文本: {len(text)} 字符")
    
    if len(text) <= args.max_chars:
        chunks = [text]
    else:
        chunks = split_text(text, args.max_chars)
    
    print(f"分割为 {len(chunks)} 段")
    
    output_dir = os.path.dirname(args.output) or "."
    os.makedirs(output_dir, exist_ok=True)
    
    base_name = Path(args.output).stem
    audio_files = []
    
    for i, chunk in enumerate(chunks):
        chunk_file = f"{output_dir}/{base_name}_part{i+1}.mp3"
        print(f"生成第 {i+1}/{len(chunks)} 段音频 ({len(chunk)} 字符)...")
        
        success = asyncio.run(generate_audio_edge(chunk, chunk_file, args.voice))
        
        if success:
            print(f"  ✓ 已保存: {chunk_file}")
            audio_files.append(chunk_file)
        else:
            print(f"  ✗ 生成失败")
            return 1
    
    if len(audio_files) > 1:
        print(f"合并 {len(audio_files)} 个音频文件...")
        if merge_audio_files(audio_files, args.output):
            print(f"✓ 已保存完整音频: {args.output}")
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
