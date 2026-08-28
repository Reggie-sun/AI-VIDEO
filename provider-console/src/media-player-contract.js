export function mediaHasAudioTrack(media) {
  if (!media) return null;
  if (media.audioTracks && Number.isInteger(media.audioTracks.length)) {
    return media.audioTracks.length > 0;
  }
  if (typeof media.captureStream !== "function") return null;

  try {
    const stream = media.captureStream();
    const audioTracks = typeof stream.getAudioTracks === "function" ? stream.getAudioTracks() : [];
    const tracks = typeof stream.getTracks === "function"
      ? stream.getTracks()
      : [...audioTracks, ...(typeof stream.getVideoTracks === "function" ? stream.getVideoTracks() : [])];
    for (const track of tracks) track?.stop?.();
    return audioTracks.length > 0;
  } catch {
    return null;
  }
}

export async function enableMediaSound(media) {
  if (!media || typeof media.play !== "function") throw new TypeError("video element is required");
  media.defaultMuted = false;
  media.muted = false;
  media.volume = 1;
  await media.play();
}
