import { useNavigate } from "react-router-dom";

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

  function go(action, text) {
    if (action === "collect") {
      navigate("/graph", { state: { collectTopic: text } });
    } else {
      navigate("/graph", { state: { run: text } });
    }
  }

  return (
    <div className="usage-page">
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
