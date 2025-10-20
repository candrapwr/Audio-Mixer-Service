import logging
from typing import Dict, List, Tuple

from pydub import AudioSegment
from pydub.silence import detect_nonsilent

logger = logging.getLogger(__name__)


def _ensure_music_length(music: AudioSegment, total_duration: int) -> AudioSegment:
    """Loop and trim music so it matches the requested total duration."""
    if len(music) < total_duration:
        # Repeat the music enough times to cover the target duration
        repeat_count = total_duration // len(music) + 1
        music = music * repeat_count
    return music[:total_duration]


def mix_audio_segments(
    music: AudioSegment,
    voice: AudioSegment,
    *,
    delay_seconds: int = 5,
    duck_db: int = -10,
    silence_thresh: int = -30,
    min_silence_ms: int = 500,
    fade_in_ms: int = 2000,
    fade_out_ms: int = 2000,
    post_voice_duration: int = 10000,
    voice_boost_db: int = 3,
    transition_ms: int = 200,
) -> Tuple[AudioSegment, Dict[str, object]]:
    """
    Mix music and voice segments together with ducking and fading effects.

    Returns the mixed AudioSegment together with debug metadata describing the mix.
    """
    # Boost voice volume to make it more dominant by default
    boosted_voice = voice + voice_boost_db

    # Detect non-silent segments within the voice track
    nonsilent_segments: List[Tuple[int, int]] = detect_nonsilent(
        boosted_voice,
        min_silence_len=min_silence_ms,
        silence_thresh=silence_thresh,
    )

    if not nonsilent_segments:
        logger.warning(
            "Tidak ada segmen voice aktif terdeteksi. Coba kurangi silence_thresh (misal -25)."
        )

    # Total duration accounts for the opening delay and trailing duration after voice ends
    total_duration = len(boosted_voice) + (delay_seconds * 1000) + post_voice_duration

    prepared_music = _ensure_music_length(music, total_duration).fade_in(fade_in_ms)

    mixed = AudioSegment.silent(duration=0)
    current_pos = 0

    for start, end in nonsilent_segments:
        adj_start = start + (delay_seconds * 1000)
        adj_end = end + (delay_seconds * 1000)

        # Keep full-volume music before ducking
        if current_pos < adj_start:
            mixed += prepared_music[current_pos:adj_start]
            current_pos = adj_start

        # Smooth transition into the duck segment
        if transition_ms > 0:
            transition_end = current_pos + transition_ms
            fade_out_seg = prepared_music[current_pos:transition_end] + duck_db
            fade_out_seg = fade_out_seg.fade_out(transition_ms)
            mixed += fade_out_seg
            current_pos = transition_end

        # Main ducked segment where voice is active
        duck_end = max(current_pos, adj_end - transition_ms)
        if duck_end > current_pos:
            mixed += prepared_music[current_pos:duck_end] + duck_db
            current_pos = duck_end

        # Smooth transition back to full volume
        if transition_ms > 0:
            transition_end = current_pos + transition_ms
            fade_in_seg = prepared_music[current_pos:transition_end]
            fade_in_seg = fade_in_seg.fade_in(transition_ms)
            mixed += fade_in_seg
            current_pos = transition_end

    # Append remaining full-volume music segment
    if current_pos < total_duration:
        mixed += prepared_music[current_pos:total_duration]

    # Overlay voice with configured delay and apply fade-out at the end
    voice_with_delay = AudioSegment.silent(duration=delay_seconds * 1000) + boosted_voice
    mixed = mixed.overlay(voice_with_delay).fade_out(fade_out_ms)

    metadata: Dict[str, object] = {
        "voice_duration_seconds": len(voice) / 1000,
        "nonsilent_segments": [
            {
                "index": idx + 1,
                "start_seconds": start / 1000,
                "end_seconds": end / 1000,
                "duration_seconds": (end - start) / 1000,
            }
            for idx, (start, end) in enumerate(nonsilent_segments)
        ],
        "total_duration_seconds": total_duration / 1000,
        "delay_seconds": delay_seconds,
        "duck_db": duck_db,
        "voice_boost_db": voice_boost_db,
    }

    return mixed, metadata


def mix_audio_to_file(
    music_path: str,
    voice_path: str,
    output_path: str,
    **kwargs,
) -> Dict[str, object]:
    """Convenience helper that loads audio files and writes the mixed result."""
    music = AudioSegment.from_file(music_path)
    voice = AudioSegment.from_file(voice_path)

    mixed, metadata = mix_audio_segments(music, voice, **kwargs)
    mixed.export(output_path, format="mp3")

    logger.info("File output disimpan di: %s", output_path)

    return {
        "output_path": output_path,
        **metadata,
    }
