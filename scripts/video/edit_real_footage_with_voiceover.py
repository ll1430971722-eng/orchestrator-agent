"""Edit real sample room footage with AI voiceover and text overlays.

Creates the final 9:16 vertical video:
- Real DJI sample room footage (not AI generated)
- edge-tts voiceover (zh-CN-XiaoxiaoNeural)
- Text overlays for the interactive question
"""
import subprocess, sys, json, shutil, os
from pathlib import Path

FOOTAGE = "input/tasks/公司号第一条互动视频/assets/DJI_20260526110800_0202_D.MP4"
VOICEOVER = "input/tasks/公司号第一条互动视频/output/voiceover_final.mp3"
OUTPUT_DIR = Path("output/pending_review/抖音/公司主账号/第一条互动AI视频_员工讨论样品间版")
FONT = "/System/Library/Fonts/STHeiti Medium.ttc"

# Text overlays with timings
# Format: (start_sec, end_sec, text, font_size, y_position)
TEXTS = [
    (0.0, 2.0, "公司第一次发抖音，先问问大家", 52, "h-th-200"),
    (2.0, 5.0, "你们想看文具笔袋公司里的什么？", 48, "h-th-200"),
    (5.0, 7.0, "样品间？设计打样？员工日常？行业内幕？", 42, "h-th-300"),
    (7.0, 8.6, "评论区告诉我们", 56, "h-th-200"),
]

def run(cmd, desc=""):
    print(f"[{desc}] Running...")
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print(f"STDERR: {result.stderr}")
        print(f"STDOUT: {result.stdout}")
        print(f"[FAIL] {desc}")
        return False
    print(f"[OK] {desc}")
    return True

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Get voiceover duration
    vo_result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", VOICEOVER],
        capture_output=True, text=True
    )
    vo_dur = float(json.loads(vo_result.stdout)["format"]["duration"])
    print(f"Voiceover duration: {vo_dur:.2f}s")

    # Get footage duration
    foot_result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", FOOTAGE],
        capture_output=True, text=True
    )
    footage_dur = float(json.loads(foot_result.stdout)["format"]["duration"])
    print(f"Footage duration: {footage_dur:.2f}s")

    # Build drawtext filter for each text overlay
    drawtexts = []
    for i, (start, end, text, size, y_pos) in enumerate(TEXTS):
        # enable expression: show text only between start and end
        enable = f"between(t,{start},{end})"
        # Escape special characters for ffmpeg
        escaped = text.replace("：", ":").replace("？", "?").replace("，", ",")
        dt = (
            f"drawtext=fontfile='{FONT}':text='{escaped}':"
            f"fontsize={size}:fontcolor=white:borderw=3:bordercolor=black@0.6:"
            f"x=(w-text_w)/2:y={y_pos}:enable='{enable}'"
        )
        drawtexts.append(dt)

    # Build the full filtergraph
    # Split video: original for blurred bg, scaled for main content
    # [0:v] is the main clip

    # First, trim footage to ~8.6s total from 3 segments
    # Segment 1: 3-5s (2s) - entering room
    # Segment 2: 12-16s (3s) - room details
    # Segment 3: 25-28.6s (3.6s) - wider establishing shot

    filter_parts = []

    # Trim clips from source
    filter_parts.append("[0:v] split=3 [s1][s2][s3]")
    filter_parts.append(f"[s1] trim=3:5, setpts=PTS-STARTPTS [c1]")
    filter_parts.append(f"[s2] trim=12:15, setpts=PTS-STARTPTS [c2]")
    filter_parts.append(f"[s3] trim=25:28.6, setpts=PTS-STARTPTS [c3]")

    # Concat clips
    filter_parts.append("[c1][c2][c3] concat=n=3:v=1:a=0 [main]")

    # Create 9:16 vertical: blurred background + centered main
    filter_parts.append("[main] split [orig][copy]")
    filter_parts.append(
        "[copy] scale=720:1280:force_original_aspect_ratio=increase,"
        "crop=720:1280, boxblur=20:10 [blurred]"
    )
    filter_parts.append(
        "[orig] scale=720:-2 [scaled]"
    )
    filter_parts.append(
        "[blurred][scaled] overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2 [withbg]"
    )

    # Add text overlays
    for dt in drawtexts:
        filter_parts.append(f"[withbg] {dt} [withbg]")

    filter_complex = "; ".join(filter_parts)

    output = str(OUTPUT_DIR / "generated_video_raw.mp4")

    # Build ffmpeg command
    cmd = (
        f"ffmpeg -i '{FOOTAGE}' -i '{VOICEOVER}' "
        f"-filter_complex \"{filter_complex}\" "
        f"-map '[withbg]' -map 1:a "
        f"-c:v libx264 -crf 20 -preset medium "
        f"-c:a aac -b:a 128k "
        f"-t {vo_dur} "
        f"-movflags +faststart "
        f"'{output}' -y"
    )

    print("\n--- FFmpeg Command ---")
    print(cmd[:500] + "...")
    print("---")

    import os
    ret = os.system(cmd)
    if ret != 0:
        print(f"[FAIL] FFmpeg exited with code {ret}")
        sys.exit(1)

    print(f"\n[OK] Video saved to: {output}")

    # Copy to final name
    final = str(OUTPUT_DIR / "generated_video.mp4")
    shutil.copy(output, final)
    print(f"[OK] Final video: {final}")

if __name__ == "__main__":
    main()
