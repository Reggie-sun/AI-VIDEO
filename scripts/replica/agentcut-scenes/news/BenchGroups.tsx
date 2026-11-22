import { AbsoluteFill, useCurrentFrame } from "remotion";
import { RadialGlow, SPRING, mix, sp, type SceneProps } from "agentcut";

type Model = { name: string; color: string };
type Group = { label: string; values: (number | null)[] };
type Props = SceneProps & { title: string; source: string; models: Model[]; groups: Group[]; lead: number };

// Official benchmark table as rising grouped bars: the lead model's bar is tallest in every group.
export default function BenchGroups({ title, source, models, groups, lead, width, height }: Props) {
  const f = useCurrentFrame();
  const left = 120;
  const right = width - 120;
  const base = height - 330;
  const top = 300;
  const slot = (right - left) / groups.length;
  const inner = slot * 0.78;
  const bw = inner / models.length;
  const max = 100;
  const titleIn = sp(f, 0, SPRING.snappy);
  return (
    <AbsoluteFill style={{ background: "linear-gradient(170deg,#161015,#08080b)", fontFamily: "Noto Sans SC" }}>
      <RadialGlow x={0.5} y={0.55} radius={0.7} color="#d97757" opacity={0.16} />
      <div style={{ position: "absolute", left, top: 70, color: "#fff", fontSize: 72, fontWeight: 900, opacity: titleIn, transform: `translateY(${mix(20, 0, titleIn)}px)` }}>
        {title}
      </div>
      <div style={{ position: "absolute", left, top: 168, color: "rgba(255,255,255,0.55)", fontSize: 30, fontWeight: 500 }}>{source}</div>
      <div style={{ position: "absolute", right: 120, top: 92, display: "flex", gap: 28 }}>
        {models.map((m, i) => (
          <div key={m.name} style={{ display: "flex", alignItems: "center", gap: 10, color: i === lead ? "#fff" : "rgba(255,255,255,0.6)", fontSize: 28, fontWeight: i === lead ? 900 : 600 }}>
            <div style={{ width: 22, height: 22, borderRadius: 5, background: m.color }} />
            {m.name}
          </div>
        ))}
      </div>
      {groups.map((g, gi) => {
        const x0 = left + gi * slot + (slot - inner) / 2;
        return (
          <div key={g.label}>
            {g.values.map((v, mi) => {
              if (v === null) return null;
              const grow = sp(f, 6 + gi * 4 + mi * 2, SPRING.land);
              const h = ((base - top) * v) / max;
              const isLead = mi === lead;
              return (
                <div key={mi}>
                  <div
                    style={{
                      position: "absolute",
                      left: x0 + mi * bw + 3,
                      top: base - h * grow,
                      width: bw - 6,
                      height: h * grow,
                      borderRadius: "8px 8px 2px 2px",
                      background: models[mi].color,
                      opacity: isLead ? 1 : 0.55,
                      boxShadow: isLead ? `0 0 28px ${models[mi].color}` : "none",
                    }}
                  />
                  {isLead ? (
                    <div style={{ position: "absolute", left: x0 + mi * bw - 30, width: bw + 60, top: base - h * grow - 56, textAlign: "center", color: "#fff", fontSize: 40, fontWeight: 900, opacity: grow }}>
                      {v}
                    </div>
                  ) : null}
                </div>
              );
            })}
            <div style={{ position: "absolute", left: x0 - 20, width: inner + 40, top: base + 18, textAlign: "center", color: "rgba(255,255,255,0.8)", fontSize: 30, fontWeight: 700, lineHeight: 1.2 }}>
              {g.label}
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
}
