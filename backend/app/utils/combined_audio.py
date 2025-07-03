from pydub import AudioSegment
import os
# 加载多个音频
audio1 = AudioSegment.from_wav(r"/uploads/voice/介绍双迪标准.wav")
audio2 = AudioSegment.from_wav(r"/uploads/voice/卡曼公司是双迪.wav")
audio3 = AudioSegment.from_wav(r"/uploads/voice/今天天气怎么样标准的.wav")

# 合并音频（顺序拼接）
combined = audio1 + audio2 + audio3

# 导出为新文件
combined.export(r"E:\work\code\test_uniapp\test_0424\backend\uploads\combined\combined.wav", format="wav")

def combine_audios_in_folder(folder_path, output_path):
    """
    合并指定文件夹下所有的 wav 和 mp3 音频文件（按文件名排序），并导出为 output_path。
    :param folder_path: 包含音频文件的文件夹路径
    :param output_path: 合并后音频的输出路径（含文件名）
    """
    # 获取所有 wav 和 mp3 文件，按文件名排序
    audio_files = sorted([
        f for f in os.listdir(folder_path)
        if f.lower().endswith('.wav') or f.lower().endswith('.mp3')
    ])

    if not audio_files:
        raise ValueError(f"文件夹 {folder_path} 中没有找到音频文件")

    combined = AudioSegment.empty()
    for filename in audio_files:
        file_path = os.path.join(folder_path, filename)
        if filename.lower().endswith('.wav'):
            audio = AudioSegment.from_wav(file_path)
        elif filename.lower().endswith('.mp3'):
            audio = AudioSegment.from_mp3(file_path)
        else:
            continue
        combined += audio
        print(f"已添加: {filename}")

    # 导出合并后的音频
    combined.export(output_path, format=output_path.split('.')[-1])
    print(f"\n合并完成，输出文件: {output_path}")

# 示例用法：
# combine_audios_in_folder('/path/to/folder', '/path/to/output/combined.wav')
