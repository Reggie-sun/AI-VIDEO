import React from "react";
import { FONT } from "./theme";

// Generic gift card drawing (no brand logo): white face, colour ribbon, code strip.
export function GiftCard({ w = 520, code, amount = "¥1,000", style }: { w?: number; code?: string; amount?: string; style?: React.CSSProperties }) {
  const h = w * 0.63;
  return (
    <div style={{ width: w, height: h, borderRadius: w * 0.05, position: "relative", overflow: "hidden", fontFamily: FONT,
                  background: "linear-gradient(140deg,#ffffff 0%,#f2f3f7 100%)", boxShadow: "0 30px 60px rgba(0,0,0,0.5)", ...style }}>
      <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: w * 0.42,
                    background: "linear-gradient(160deg,#ff5f6d 0%,#ffc371 30%,#47e891 55%,#3fa7ff 78%,#a26bff 100%)" }} />
      <div style={{ position: "absolute", left: w * 0.08, top: h * 0.12, width: w * 0.24, height: w * 0.24, borderRadius: "50%",
                    background: "rgba(255,255,255,0.9)", display: "flex", alignItems: "center", justifyContent: "center",
                    color: "#1d1d1f", fontSize: w * 0.06, fontWeight: 900 }}>GIFT</div>
      <div style={{ position: "absolute", right: w * 0.06, top: h * 0.09, textAlign: "right", color: "#1d1d1f" }}>
        <div style={{ fontSize: w * 0.06, fontWeight: 900, letterSpacing: 1 }}>Apple Gift Card</div>
        <div style={{ fontSize: w * 0.045, fontWeight: 700, color: "#6e6e73", marginTop: 4 }}>日本 · 日元</div>
        <div style={{ fontSize: w * 0.1, fontWeight: 900, marginTop: h * 0.06 }}>{amount}</div>
      </div>
      {code !== undefined && (
        <div style={{ position: "absolute", left: w * 0.06, right: w * 0.06, bottom: h * 0.08, height: h * 0.2, borderRadius: 10,
                      background: "#1d1d1f", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center",
                      fontFamily: "monospace", fontSize: w * 0.058, fontWeight: 700, letterSpacing: 3 }}>{code}</div>
      )}
    </div>
  );
}
