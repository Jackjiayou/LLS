from pydub import AudioSegment
import os
import librosa
import numpy as np

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
    return  output_path

# 示例用法：
# combine_audios_in_folder('/path/to/folder', '/path/to/output/combined.wav')


def extract_fluency_features(audio_path):
    # 加载音频文件
    y, sr = librosa.load(audio_path, sr=None)

    # 帧级参数（帧长 2048，跳帧 512）
    hop_length = 512
    frame_length = 2048

    # 1. MFCC（可用于分析发音清晰度、音素变化）
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_delta = librosa.feature.delta(mfccs)
    mfcc_delta_std = np.std(mfcc_delta)

    # 2. 能量（RMS）用于估算停顿
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    avg_rms = np.mean(rms)
    num_pauses = np.sum(rms < 0.02)  # 低能量帧数，估算停顿

    # 3. Zero-Crossing Rate（用于无声段检测、修正语音等）
    zcr = librosa.feature.zero_crossing_rate(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    avg_zcr = np.mean(zcr)

    # 4. 语速（估算发声段总长度 vs 整体长度）
    duration = librosa.get_duration(y=y, sr=sr)
    voiced_ratio = np.sum(rms > 0.02) * hop_length / sr / duration  # 发声段占比
    speech_rate_estimate = voiced_ratio / duration  # 越大可能越流利

    # 输出特征
    return {
        'mfcc_delta_std': mfcc_delta_std,
        'avg_rms': avg_rms,
        'num_pauses': num_pauses,
        'avg_zcr': avg_zcr,
        'voiced_ratio': voiced_ratio,
        'speech_rate_estimate': speech_rate_estimate,
        'duration_sec': duration
    }

# 示例使用
# audio_path = r"/uploads/voice/介绍双迪标准.wav"
# features = extract_fluency_features(audio_path)
#
# for k, v in features.items():
#     print(f"{k}: {v:.4f}")