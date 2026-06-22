import { useMemo } from "react";
import { useNavigate } from "react-router-dom";

// 배경 장식용 지식그래프 별자리(결정적 — 새로고침에도 동일). 노드 흩뿌리고 가까운 것끼리 연결.
const BG_W = 1200;
const BG_H = 800;
const EDGE_MAX = 175; // 이 거리 미만 노드쌍만 연결(가까울수록 진하게)
function useConstellation() {
  return useMemo(() => {
    let s = 7; // 시드
    const rnd = () => {
      s = (s * 9301 + 49297) % 233280;
      return s / 233280;
    };
    const N = 30;
    const nodes = Array.from({ length: N }, () => ({
      x: rnd() * BG_W,
      y: rnd() * BG_H,
      r: 2 + rnd() * 3.5,
    }));
    const edges = [];
    for (let i = 0; i < N; i++) {
      for (let j = i + 1; j < N; j++) {
        const d = Math.hypot(nodes[i].x - nodes[j].x, nodes[i].y - nodes[j].y);
        if (d < EDGE_MAX) edges.push({ i, j, d });
      }
    }
    return { nodes, edges };
  }, []);
}

// [사용법] 페이지 — "뭘 물어볼 수 있나"를 평범한 말로 보여주고, 예시를 누르면
// 지형도(/graph)로 이동해 그 질문이 자동 실행된다(맵이 반응). 원리 설명은 docs/FEATURES.md.
// 도구 이름(focus_lineage 등) 노출 금지 — "하고 싶은 것" 기준.
const ROWS = [
  {
    want: "주제·아이디어로 관련 연구 찾기",
    hint: "이름 몰라도 됩니다",
    examples: ["검색하면서 추론하는 방법 있어?", "그래프 기반 검색 증강 생성"],
    effect: "비슷한 주제의 개념·논문을 지도에서 강조",
    action: "run",
  },
  {
    want: "한 방법의 계보 보기",
    hint: "무엇을 딛고 나왔고, 무엇이 갈라졌는지",
    examples: ["RAG 계보 보여줘", "ReAct는 뭘 딛고 나왔어?", "CoT에서 갈라진 것들"],
    effect: "그 방법의 조상·자손만 남겨 강조",
    action: "run",
  },
  {
    want: "조건으로 좁혀 보기",
    hint: "시점·분야",
    examples: ["2024년 이후 나온 것만", "의료 분야만"],
    effect: "조건에 맞는 것만 강조, 나머지는 흐리게",
    action: "run",
  },
  {
    want: "이름을 정확히 알 때",
    hint: "바로 그 노드로",
    examples: ["GraphRAG", "Toolformer"],
    effect: "그 노드로 바로 이동·강조",
    action: "run",
  },
  {
    want: "전체로 되돌리기",
    hint: null,
    examples: ["다 보여줘"],
    effect: "모든 강조·필터 해제",
    action: "run",
  },
  {
    want: "지도에 없는 새 논문 추가",
    hint: "arXiv에서 수집",
    examples: ["멀티에이전트 협업 논문 모아줘"],
    effect: "[수집] 탭에 주제가 채워집니다 — 확인 후 직접 시작",
    action: "collect",
  },
];

export default function Usage() {
  const navigate = useNavigate();
  const { nodes, edges } = useConstellation();

  function go(action, text) {
    if (action === "collect") {
      navigate("/graph", { state: { collectTopic: text } });
    } else {
      navigate("/graph", { state: { run: text } });
    }
  }

  return (
    <div className="usage-page">
      <div className="usage-bg" aria-hidden="true">
        <svg
          className="usage-bg-svg"
          viewBox={`0 0 ${BG_W} ${BG_H}`}
          preserveAspectRatio="xMidYMid slice"
        >
          <defs>
            <radialGradient id="ubgGlow" cx="80%" cy="12%" r="58%">
              <stop offset="0%" stopColor="#2563eb" stopOpacity="0.13" />
              <stop offset="100%" stopColor="#2563eb" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="ubgGlow2" cx="10%" cy="95%" r="48%">
              <stop offset="0%" stopColor="#2563eb" stopOpacity="0.07" />
              <stop offset="100%" stopColor="#2563eb" stopOpacity="0" />
            </radialGradient>
          </defs>
          <rect width={BG_W} height={BG_H} fill="url(#ubgGlow)" />
          <rect width={BG_W} height={BG_H} fill="url(#ubgGlow2)" />
          <g>
            {edges.map((e, k) => (
              <line
                key={k}
                x1={nodes[e.i].x}
                y1={nodes[e.i].y}
                x2={nodes[e.j].x}
                y2={nodes[e.j].y}
                stroke="#2563eb"
                strokeWidth="1"
                strokeOpacity={0.11 * (1 - e.d / EDGE_MAX)}
              />
            ))}
            {nodes.map((n, i) => (
              <circle key={i} cx={n.x} cy={n.y} r={n.r} fill="#2563eb" fillOpacity="0.2" />
            ))}
          </g>
        </svg>
      </div>
      <div className="usage-inner">
        <header className="usage-hero">
          <h1>이렇게 물어보세요</h1>
          <p>
            이 지도는 <b>LLM·RAG·에이전트</b> 연구의 지형도예요. 아래 예시를 누르면
            지형도로 이동해 바로 실행되고, 맵이 반응합니다.
          </p>
        </header>

        <div className="usage-grid">
          {ROWS.map((r) => (
            <section
              className={`usage-card${r.action === "collect" ? " collect" : ""}`}
              key={r.want}
            >
              <div className="usage-card-head">
                <h3>{r.want}</h3>
                <span className="usage-badge">
                  {r.action === "collect" ? "수집" : "보기"}
                </span>
              </div>
              {r.hint && <p className="usage-hint">{r.hint}</p>}
              <div className="usage-chips">
                {r.examples.map((ex) => (
                  <button
                    type="button"
                    key={ex}
                    className={`usage-chip${r.action === "collect" ? " collect" : ""}`}
                    onClick={() => go(r.action, ex)}
                    title="눌러서 지형도에서 실행"
                  >
                    {ex}
                  </button>
                ))}
              </div>
              <p className="usage-effect">{r.effect}</p>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}
