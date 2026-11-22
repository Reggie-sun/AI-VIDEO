import { AbsoluteFill, useCurrentFrame } from "remotion";
import { sp, SPRING, mix, type SceneProps } from "agentcut";
import { FONT, YELLOW } from "./lib/theme";

type Tile = { label: string; from: number; icon: "app" | "game" | "vip" };
type Props = SceneProps & { tiles: Tile[] };

function Icon({ kind }: { kind: Tile["icon"] }) {
  const c = "#fff";
  if (kind === "app")
    return (<svg width="120" height="120" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="2" fill={c} /><rect x="14" y="3" width="7" height="7" rx="2" fill={c} /><rect x="3" y="14" width="7" height="7" rx="2" fill={c} /><rect x="14" y="14" width="7" height="7" rx="2" fill={c} opacity=".5" /></svg>);
  if (kind === "game")
    return (<svg width="120" height="120" viewBox="0 0 24 24"><path d="M6 8h12a4 4 0 0 1 4 4v3a3 3 0 0 1-5.4 1.8L15 15H9l-1.6 1.8A3 3 0 0 1 2 15v-3a4 4 0 0 1 4-4z" fill={c} /><path d="M7 10.5v3M5.5 12h3" stroke="#1b1d22" strokeWidth="1.5" strokeLinecap="round" /><circle cx="16" cy="11" r="1" fill="#1b1d22" /><circle cx="18" cy="13" r="1" fill="#1b1d22" /></svg>);
  return (<svg width="120" height="120" viewBox="0 0 24 24"><path d="M3 8l4.5 3.5L12 5l4.5 6.5L21 8l-2 11H5z" fill={c} /></svg>);
}

// 有了日元 → 购买软件 / 充值游戏 / 订阅会员
export default function Uses({ tiles, clip }: Props) {
  const f = useCurrentFrame();
  const a = sp(f, 0, SPRING.smooth);
  const colors = ["linear-gradient(160deg,#3fa7ff,#1f5bff)", "linear-gradient(160deg,#ff8a3d,#ff3b6b)", "linear-gradient(160deg,#9b6bff,#5b3bff)"];
  const out = Math.max(0, Math.min(1, (f - (clip.duration - 6)) / 6));
  return (
    <AbsoluteFill style={{ fontFamily: FONT, opacity: 1 - out }}>
      <div style={{ position: "absolute", top: 170, width: "100%", textAlign: "center", color: "#fff", fontSize: 70, fontWeight: 900, opacity: a }}>
        有了<span style={{ color: YELLOW }}>账户余额</span>，日区 ID 就能
      </div>
      <div style={{ position: "absolute", top: 380, width: "100%", display: "flex", justifyContent: "center", gap: 70 }}>
        {tiles.map((t, i) => {
          const s = sp(f, t.from, SPRING.pop);
          return (
            <div key={i} style={{ width: 380, height: 400, borderRadius: 40, background: colors[i % 3], display: "flex", flexDirection: "column",
                                  alignItems: "center", justifyContent: "center", gap: 30, transform: `translateY(${mix(80, 0, s)}px) scale(${mix(0.8, 1, s)})`,
                                  opacity: f >= t.from ? s : 0.12, boxShadow: "0 30px 60px rgba(0,0,0,0.45)" }}>
              <Icon kind={t.icon} />
              <div style={{ color: "#fff", fontSize: 58, fontWeight: 900 }}>{t.label}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
}
