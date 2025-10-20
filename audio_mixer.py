import argparse
import logging

from mixer import mix_audio_to_file


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s - %(message)s",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CLI App untuk mix musik dengan voice, smooth dynamic ducking, fade-in/out, dan potong 10 detik setelah voice.")
    parser.add_argument("--music", required=True, help="Path ke file musik MP3")
    parser.add_argument("--voice", required=True, help="Path ke file voice (WAV/MP3/dll)")
    parser.add_argument("--output", default="output.mp3", help="Path output MP3")
    parser.add_argument("--delay", default=5, type=int, help="Delay voice dalam detik")
    parser.add_argument("--duck_db", default=-10, type=int, help="Pengurangan volume musik saat voice aktif (dB)")
    parser.add_argument("--silence_thresh", default=-30, type=int, help="Threshold silence (dB) - lebih rendah = lebih sensitif")
    parser.add_argument("--min_silence_ms", default=500, type=int, help="Minimal durasi silence (ms)")
    parser.add_argument("--fade_in_ms", default=2000, type=int, help="Durasi fade-in musik di awal (ms)")
    parser.add_argument("--fade_out_ms", default=2000, type=int, help="Durasi fade-out di akhir (ms)")
    parser.add_argument("--post_voice_duration", default=10000, type=int, help="Durasi setelah voice berhenti (ms)")
    parser.add_argument("--voice_boost_db", default=3, type=int, help="Boost volume voice (dB)")
    parser.add_argument("--transition_ms", default=200, type=int, help="Durasi transisi smooth ducking (ms)")
    parser.add_argument("--verbose", action="store_true", help="Tampilkan log debug detail")
    args = parser.parse_args()

    configure_logging(args.verbose)

    mix_audio_to_file(
        args.music,
        args.voice,
        args.output,
        delay_seconds=args.delay,
        duck_db=args.duck_db,
        silence_thresh=args.silence_thresh,
        min_silence_ms=args.min_silence_ms,
        fade_in_ms=args.fade_in_ms,
        fade_out_ms=args.fade_out_ms,
        post_voice_duration=args.post_voice_duration,
        voice_boost_db=args.voice_boost_db,
        transition_ms=args.transition_ms,
    )
