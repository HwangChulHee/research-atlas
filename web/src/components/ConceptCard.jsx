import { useState } from "react";
import { CAT_KR, STATUSES, actionKr, parseAction } from "../lib/lexiconConstants.js";

// arXiv id → 링크
function PaperLinks({ ids }) {
  return ids.map((p, i) => (
    <span key={p}>
      {i > 0 ? " · " : ""}
      <a href={`https://arxiv.org/abs/${p}`} target="_blank" rel="noreferrer">
        {p}
      </a>
    </span>
  ));
}

// 개념 카드 — 결정(승인/거부/병합) 중심. 근거(정의·출처 논문)를 항상 보여주고,
// 도우미 제안은 가이드로. definition/first_seen/source 같은 메타는 노출하지 않음
// (정의 정본은 논문 추출이라 여기서 편집 안 함 — 사전은 자격·동일성 판정만).
export default function ConceptCard({ item, card, onPatch, onDecision, onSetStatus, onMerge }) {
  const [aliasOpen, setAliasOpen] = useState(false);
  const [newAlias, setNewAlias] = useState("");

  const pending = ["pending", "unreviewed"].includes(item.status);
  const sugg = card && pending ? card.suggestion : null;
  const ev = (card && card.evidence) || {};
  const definition = item.definition || ev.definition || "";
  const defPapers = (ev.defined_in || []).map((d) => d.paper);
  const citePapers = ev.cited_in || [];
  const noEvidence = !definition && defPapers.length === 0 && citePapers.length === 0;

  function addAlias() {
    const a = newAlias.trim();
    setNewAlias("");
    setAliasOpen(false);
    if (!a || item.aliases.includes(a)) return;
    onPatch(item.name, { aliases: [...item.aliases, a] });
  }
  function removeAlias(a) {
    onPatch(item.name, { aliases: item.aliases.filter((x) => x !== a) });
  }
  function applySuggestion() {
    const [act, tgt] = parseAction(sugg.action);
    if (act === "merge" && !tgt) onMerge(item.name); // target 모르면 모달
    else onDecision(item.name, act, tgt);
  }

  return (
    <div className={`cc${pending ? " cc-pending" : ""}`}>
      <div className="cc-top">
        <span className="cc-name">{item.name}</span>
        <select
          className={`badge st-${item.status} cc-status`}
          value={item.status}
          onChange={(e) => onSetStatus(item.name, e.target.value)}
          title="상태 수동 변경"
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <span className="cc-spacer" />
        <div className="cc-actions">
          <button onClick={() => onMerge(item.name)} title="다른 개념의 alias로 병합">
            ⤳ 병합
          </button>
        </div>
      </div>

      {/* 근거 — 항상 보임(판단 1초) */}
      <div className="cc-evidence">
        {definition ? (
          <p className="cc-def" title={definition}>
            {definition}
          </p>
        ) : (
          <p className="cc-def muted">정의 없음(원논문 미수록)</p>
        )}
        <div className="cc-papers muted">
          {defPapers.length > 0 && (
            <span>
              정의 <PaperLinks ids={defPapers} />
            </span>
          )}
          {defPapers.length > 0 && citePapers.length > 0 && <span> · </span>}
          {citePapers.length > 0 && (
            <span>
              조상으로 인용 <PaperLinks ids={citePapers} />
            </span>
          )}
          {noEvidence && <span>출처 논문 없음 — 이름만 등장</span>}
        </div>
      </div>

      {/* 도우미 제안 — 가이드. 적용은 [이대로] */}
      {sugg && (
        <div className="cc-sugg">
          <span className={`rv-conf rv-${sugg.confidence}`}>{sugg.confidence}</span>
          <span className="cc-sugg-text">
            <b>제안: {actionKr(parseAction(sugg.action))}</b> (
            {CAT_KR[sugg.category] || sugg.category}) — {sugg.reason}
          </span>
          <button className="cc-apply" onClick={applySuggestion}>
            이대로 적용
          </button>
        </div>
      )}

      {/* 별칭 — 동일성 관리(보조) */}
      <div className="cc-aliases">
        <span className="muted">별칭:</span>
        {item.aliases.length === 0 && !aliasOpen && (
          <span className="muted cc-none">없음</span>
        )}
        {item.aliases.map((a) => (
          <span className="alias-chip" key={a}>
            {a}
            <button title="삭제" onClick={() => removeAlias(a)}>
              ×
            </button>
          </span>
        ))}
        {aliasOpen ? (
          <input
            autoFocus
            placeholder="별칭 입력 후 Enter"
            value={newAlias}
            onChange={(e) => setNewAlias(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addAlias()}
            onBlur={addAlias}
            style={{ width: 140 }}
          />
        ) : (
          <button className="cc-alias-add" onClick={() => setAliasOpen(true)}>
            + 별칭
          </button>
        )}
      </div>
    </div>
  );
}
