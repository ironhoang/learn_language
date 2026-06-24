import { useAudioPlayer } from '../hooks/useAudioPlayer';

export default function AudioBtn({ src }) {
  const { activeSrc, toggle } = useAudioPlayer();
  if (!src) return null;
  const playing = activeSrc === src;
  return (
    <button
      className={`audio-btn${playing ? ' playing' : ''}`}
      data-src={src}
      onClick={() => toggle(src)}
      title="Phát âm"
    >
      🔊
    </button>
  );
}
