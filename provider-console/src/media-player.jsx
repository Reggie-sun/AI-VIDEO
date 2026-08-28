import React, { useEffect, useRef, useState } from "react";
import { SpeakerHigh, SpeakerSlash } from "@phosphor-icons/react";

import { enableMediaSound, mediaHasAudioTrack } from "./media-player-contract.js";

export function AudibleVideo({ src, compact = false, onLoadedMetadata, onVolumeChange, ...props }) {
  const videoRef = useRef(null);
  const [trackState, setTrackState] = useState("unknown");
  const [audible, setAudible] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    setTrackState("unknown");
    setAudible(true);
    setMessage("");
  }, [src]);

  const syncVolume = (media) => setAudible(!media.muted && media.volume > 0);
  const inspectAudio = (event) => {
    const media = event.currentTarget;
    media.defaultMuted = false;
    media.muted = false;
    if (media.volume === 0) media.volume = 1;
    const detected = mediaHasAudioTrack(media);
    setTrackState(detected === true ? "present" : detected === false ? "absent" : "unknown");
    syncVolume(media);
    onLoadedMetadata?.(event);
  };
  const handleVolumeChange = (event) => {
    syncVolume(event.currentTarget);
    onVolumeChange?.(event);
  };
  const enableSound = async () => {
    try {
      await enableMediaSound(videoRef.current);
      setAudible(true);
      setMessage("声音已开启并开始播放");
    } catch {
      setMessage("浏览器阻止了播放，请再点一次视频播放键");
    }
  };

  const label = trackState === "absent"
    ? "该视频文件没有音轨"
    : trackState === "present"
      ? (audible ? "已检测到音轨 · 当前未静音" : "已检测到音轨 · 当前静音")
      : "音轨状态未知 · 可用原生音量控制";

  return (
    <div className={`audible-video${compact ? " audible-video--compact" : ""}`}>
      <video {...props} ref={videoRef} src={src} controls playsInline onLoadedMetadata={inspectAudio} onVolumeChange={handleVolumeChange} />
      <div className="audible-video__sound" aria-live="polite">
        {!compact && <span>{trackState === "absent" || !audible ? <SpeakerSlash size={16} /> : <SpeakerHigh size={16} />}{message || label}</span>}
        <button type="button" onClick={enableSound} disabled={trackState === "absent"} title={compact ? (message || label) : undefined}>{compact ? "开启声音" : "开启声音并播放"}</button>
      </div>
    </div>
  );
}
