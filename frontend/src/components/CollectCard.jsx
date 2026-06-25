// 수집 흐름 interrupt 카드 — stage별 버튼. resume은 onResume(decision)로.

const STAGE_LABELS = {
  interpret: "해석 확인",
  approve: "물량 승인",
  extract_confirm: "추출 승인",
};
const stageLabel = (stage) => STAGE_LABELS[stage] || "수집";

export default function CollectCard({
  collect,
  onResume,
  reviseOpen,
  setReviseOpen,
  reviseText,
  setReviseText,
}) {
  const { stage, data, busy, timedOut } = collect;

  if (busy) {
    // 직전 단계 맥락 한 줄 유지 — busy 중 "어느 단계였는지" 사라지지 않게(④)
    const passed = (data.gate_summary || []).filter((s) => s.passed).length;
    const nExtract = (data.to_extract || []).length;
    const ctx =
      stage === "extract_confirm"
        ? `통과 ${passed}편 → ${nExtract}편 추출 중… (최대 수 분 걸릴 수 있어요)`
        : "처리 중…";
    return (
      <div className="collect-card">
        <div className="collect-stage">{stageLabel(stage)}</div>
        <div className="collect-busy">
          <span className="spinner" /> {ctx}
        </div>
      </div>
    );
  }

  if (stage === "interpret") {
    return (
      <div className="collect-card">
        <div className="collect-stage">해석 확인</div>
        <div className="collect-report">{data.report}</div>
        {reviseOpen ? (
          <form
            className="collect-revise"
            onSubmit={(e) => {
              e.preventDefault();
              const t = reviseText.trim();
              if (!t) return;
              onResume(`revise:${t}`);
              setReviseText("");
            }}
          >
            <input
              autoFocus
              placeholder="어떻게 좁힐까요… (예: 검색 노이즈 쪽으로)"
              value={reviseText}
              onChange={(e) => setReviseText(e.target.value)}
            />
            <button type="submit">적용</button>
            <button
              type="button"
              className="ghost"
              onClick={() => {
                setReviseOpen(false);
                setReviseText("");
              }}
            >
              뒤로
            </button>
          </form>
        ) : (
          <div className="collect-actions">
            <button onClick={() => onResume("proceed")}>진행</button>
            <button onClick={() => setReviseOpen(true)}>수정</button>
            <button className="ghost" onClick={() => onResume("cancel")}>
              취소
            </button>
          </div>
        )}
      </div>
    );
  }

  if (stage === "approve") {
    const c = data.counts || {};
    return (
      <div className="collect-card">
        <div className="collect-stage">물량 승인</div>
        <div className="collect-counts">
          발견 {c.found ?? 0} · 신규 <b>{c.new ?? 0}</b> · 보유제외 {c.owned_excluded ?? 0}
        </div>
        <div className="collect-actions">
          <button onClick={() => onResume("proceed")}>진행</button>
          <button className="ghost" onClick={() => onResume("cancel")}>
            취소
          </button>
        </div>
      </div>
    );
  }

  if (stage === "extract_confirm") {
    const summary = data.gate_summary || [];
    const passed = summary.filter((s) => s.passed);
    const failed = summary.filter((s) => !s.passed);
    const toExtract = data.to_extract || [];
    return (
      <div className="collect-card">
        <div className="collect-stage">추출 승인</div>
        <div className="collect-counts">
          통과 <b>{passed.length}</b>편 · {toExtract.length}편 추출 예정
        </div>
        <ul className="collect-gate">
          {passed.map((s) => (
            <li key={s.id} className="pass">
              ✓ {s.id} <span className="muted">{s.verdict}</span>
            </li>
          ))}
        </ul>
        {failed.length > 0 && (
          <div className="muted collect-failed">
            그 외 {failed.length}편 미통과 (benchmark/analysis/survey 등)
          </div>
        )}
        {timedOut ? (
          <div className="collect-actions">
            <button onClick={() => onResume("proceed")}>재시도</button>
            <button className="ghost" onClick={() => onResume("cancel")}>
              취소
            </button>
          </div>
        ) : (
          <div className="collect-actions">
            <button onClick={() => onResume("proceed")}>추출</button>
            <button className="ghost" onClick={() => onResume("cancel")}>
              그만
            </button>
          </div>
        )}
      </div>
    );
  }
  return null;
}
