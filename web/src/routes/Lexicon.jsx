import { useEffect, useMemo, useState } from "react";
import {
  getLexicon,
  mergeLexicon,
  patchLexicon,
  rebuild,
  getReviewSuggestions,
  regenerateReviewSuggestions,
} from "../api.js";

// 제안 action 문자열 → (action, target). "merge_into:DPR" → ["merge","DPR"].
function parseAction(s) {
  if (s && s.startsWith("merge_into:")) return ["merge", s.slice(11)];
  return [s, null];
}
// 한글 표기(표시용 — 내부 로직은 원문 사용)
const CAT_KR = {
  lineage: "계보",
  component: "부품",
  generic: "일반어",
  substrate: "베이스모델",
  author_year: "저자-연도 인용",
  umbrella: "우산범주",
  duplicate: "중복",
};
function actionKr([act, tgt]) {
  if (act === "approve") return "승인";
  if (act === "reject") return "거부";
  if (act === "merge") return `병합 → ${tgt || "?"}`;
  return act;
}

const FILTERS = ["pending", "unreviewed", "approved", "rejected", "all"];
const PAGE_SIZES = [25, 50, 100];

// 각 상태가 뭘 의미하는지 — 그래프 표시 여부 포함(NODE_OK = approved/unreviewed).
const STATUS_INFO = [
  ["approved", "검토·승인됨 → 그래프에 표시"],
  ["unreviewed", "논문이 정의한 개념(자동 등록) → 그래프에 표시 · 검토 전"],
  ["pending", "참조(builds_on)로만 등장, 정의 없음 → 그래프 미표시 · 검토 대기"],
  ["rejected", "거부됨 → 그래프 미표시"],
];

export default function Lexicon() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("pending"); // 대기열 처리가 주 작업
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [showHelp, setShowHelp] = useState(true); // 상태 설명 펼침(기본 표시)
  const [mergeFrom, setMergeFrom] = useState(null); // 병합 모달 대상(개념명) 또는 null
  const [reviewCards, setReviewCards] = useState([]); // 검토 도우미 제안 카드(정적 스냅샷)
  const [rebuilding, setRebuilding] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [toast, setToast] = useState(null); // {msg, err}

  const flash = (msg, err = false) => {
    setToast({ msg, err });
    setTimeout(() => setToast(null), 3000);
  };

  async function reload() {
    setLoading(true);
    try {
      setItems(await getLexicon());
    } catch (e) {
      flash(`로드 실패: ${e.message}`, true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    reload();
    getReviewSuggestions()
      .then((r) => setReviewCards(r.cards || []))
      .catch(() => setReviewCards([])); // 제안 파일 없으면 패널 자체가 안 뜸
  }, []);

  // 결정 튜플(action,target) → 기존 엔드포인트로 dispatch. 새 적용 로직 없음.
  // "이대로 적용"과 수동 오버라이드가 같은 함수 — 차이는 넣는 튜플뿐.
  async function applyDecision(name, action, target) {
    try {
      if (action === "approve") {
        const wasPending = items.find((it) => it.name === name)?.status === "pending";
        await patchLexicon(name, { status: "approved" });
        setItems((prev) =>
          prev.map((it) => (it.name === name ? { ...it, status: "approved" } : it))
        );
        flash(wasPending ? `승인됨: ${name} · 재빌드 시 노드화` : `승인됨: ${name}`);
      } else if (action === "reject") {
        await patchLexicon(name, { status: "rejected" });
        setItems((prev) =>
          prev.map((it) => (it.name === name ? { ...it, status: "rejected" } : it))
        );
        flash(`거부됨: ${name}`);
      } else if (action === "merge") {
        if (!target) {
          flash(`병합 대상 없음: ${name}`, true);
          return false;
        }
        await mergeLexicon(name, target);
        setItems((prev) => prev.filter((it) => it.name !== name)); // src 삭제됨
        flash(`병합됨: ${name} → ${target}`);
      }
      return true;
    } catch (e) {
      flash(`적용 실패(${name}): ${e.message}`, true);
      return false;
    }
  }

  async function doRebuild() {
    setRebuilding(true);
    try {
      const r = await rebuild();
      flash(`재빌드 완료 — 노드 ${r.nodes} / 계보 ${r.builds_on}`);
    } catch (e) {
      flash(`재빌드 실패: ${e.message}`, true);
    } finally {
      setRebuilding(false);
    }
  }

  // 증분 재생성 — 카드 없는 신규 검토대기 개념만 제안 생성(LLM). 새 수집/재빌드 후 사용.
  async function doRegenerate() {
    setRegenerating(true);
    flash("새 개념 제안 생성 중… (LLM)");
    try {
      const r = await regenerateReviewSuggestions();
      setReviewCards(r.cards || []);
      flash(`제안 갱신됨 — 카드 ${(r.cards || []).length}개`);
    } catch (e) {
      flash(`제안 생성 실패: ${e.message}`, true);
    } finally {
      setRegenerating(false);
    }
  }

  // 한 항목의 필드를 PATCH하고 로컬 상태도 갱신
  async function applyPatch(name, patch) {
    try {
      await patchLexicon(name, patch);
      setItems((prev) =>
        prev.map((it) => (it.name === name ? { ...it, ...patch } : it))
      );
    } catch (e) {
      flash(`저장 실패: ${e.message}`, true);
    }
  }

  async function confirmMerge(from, into) {
    setMergeFrom(null);
    try {
      await mergeLexicon(from, into);
      flash(`병합됨: ${from} → ${into}`);
      reload();
    } catch (e) {
      flash(`병합 실패: ${e.message}`, true);
    }
  }

  const counts = useMemo(() => {
    const c = {};
    for (const it of items) c[it.status] = (c[it.status] || 0) + 1;
    return c;
  }, [items]);

  const q = query.trim().toLowerCase();

  // 검토 도우미 제안을 개념명으로 인덱싱 → 카드에 근거·제안 인라인.
  const cardByName = useMemo(() => {
    const m = {};
    for (const c of reviewCards) m[c.concept] = c;
    return m;
  }, [reviewCards]);

  // 상태 필터 + 이름 검색 → "불확실한 것 먼저"로 정렬(검토 도구의 의도).
  // 검토대기 행은 제안 확신 낮은 순(low→med→high) → 그 외는 이름순. 검색은 목록을 좁힌다.
  const CONF = { low: 0, med: 1, high: 2 };
  const filtered = useMemo(() => {
    let arr = items.filter((it) => filter === "all" || it.status === filter);
    if (q) arr = arr.filter((it) => it.name.toLowerCase().includes(q));
    const rank = (it) => {
      const c = cardByName[it.name];
      if (c && ["pending", "unreviewed"].includes(it.status))
        return CONF[c.suggestion.confidence] ?? 3;
      return 9; // 제안 없는 건 뒤로
    };
    return [...arr].sort(
      (a, b) => rank(a) - rank(b) || a.name.localeCompare(b.name)
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items, filter, q, cardByName]);

  // 필터/검색/페이지크기가 바뀌면 1페이지로
  useEffect(() => {
    setPage(1);
  }, [filter, q, pageSize]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const safePage = Math.min(page, pageCount);
  const paged = filtered.slice((safePage - 1) * pageSize, safePage * pageSize);

  return (
    <div className="lex-wrap">
      <header className="lex-header">
        <div className="lex-header-top">
          <h1>사전</h1>
          <button
            className="lex-help-toggle"
            onClick={() => setShowHelp((v) => !v)}
            title="상태 값 설명"
          >
            상태 설명 {showHelp ? "▴" : "▾"}
          </button>
        </div>
        <p>
          개념(노드)의 표기·별칭·정의·상태를 검토하고 정리합니다. 대기열(pending)을
          승인/거부하는 게 주 작업이에요.
        </p>
        {showHelp && (
          <ul className="lex-legend">
            {STATUS_INFO.map(([s, desc]) => (
              <li key={s}>
                <span className={`badge st-${s}`}>{s}</span>
                <span className="muted">{desc}</span>
              </li>
            ))}
          </ul>
        )}
      </header>

      <div className="lex-toolbar">
        <div className="lex-filters">
          {FILTERS.map((f) => (
            <button
              key={f}
              className={`filter-btn${filter === f ? " active" : ""}`}
              onClick={() => setFilter(f)}
            >
              {f}
              {f !== "all" && counts[f] ? ` ${counts[f]}` : ""}
            </button>
          ))}
        </div>
        <input
          className="lex-search"
          placeholder="개념명 검색…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {q && <span className="muted">{filtered.length}건</span>}
        <span className="spacer" />
        <button
          onClick={doRegenerate}
          disabled={regenerating}
          title="카드 없는 신규 검토대기 개념만 제안 생성(LLM)"
        >
          {regenerating ? "제안 생성 중…" : "✦ 제안 새로고침"}
        </button>
        <button onClick={doRebuild} disabled={rebuilding} title="pending 승인분을 노드로 반영">
          {rebuilding ? "재빌드 중…" : "↻ 재빌드"}
        </button>
        <select
          className="lex-pagesize"
          value={pageSize}
          onChange={(e) => setPageSize(Number(e.target.value))}
          title="페이지당 개수"
        >
          {PAGE_SIZES.map((n) => (
            <option key={n} value={n}>
              {n}/쪽
            </option>
          ))}
        </select>
        <span className="muted lex-total">
          총 {items.length}개 · 조건 {filtered.length}
        </span>
      </div>
      {!loading && filtered.length > 0 && (
        <Pager
          page={safePage}
          pageCount={pageCount}
          pageSize={pageSize}
          total={filtered.length}
          onPage={setPage}
        />
      )}

      {loading ? (
        <div className="lex-loading">
          <span className="spinner" /> 사전 불러오는 중…
        </div>
      ) : (
        <div className="lex-list">
          {paged.map((it) => (
            <ConceptCard
              key={it.name}
              item={it}
              card={cardByName[it.name]}
              onPatch={applyPatch}
              onDecision={applyDecision}
              onMerge={setMergeFrom}
            />
          ))}
        </div>
      )}
      {!loading && filtered.length > pageSize && (
        <Pager
          page={safePage}
          pageCount={pageCount}
          pageSize={pageSize}
          total={filtered.length}
          onPage={setPage}
        />
      )}
      {!loading && filtered.length === 0 && (
        <div className="muted" style={{ padding: 20 }}>
          해당 조건의 개념이 없습니다.
        </div>
      )}

      {mergeFrom && (
        <MergeModal
          from={mergeFrom}
          items={items}
          onCancel={() => setMergeFrom(null)}
          onConfirm={(into) => confirmMerge(mergeFrom, into)}
        />
      )}

      {toast && (
        <div className={`toast${toast.err ? " err" : ""}`}>{toast.msg}</div>
      )}
    </div>
  );
}

// 페이저 — 상·하단 재사용.
function Pager({ page, pageCount, pageSize, total, onPage }) {
  return (
    <div className="lex-pager">
      <span className="muted">
        {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} / {total}
      </span>
      {pageCount > 1 && (
        <span className="lex-pager-ctrl">
          <button disabled={page <= 1} onClick={() => onPage(page - 1)}>
            ‹ 이전
          </button>
          <span className="muted">
            {page} / {pageCount}
          </span>
          <button disabled={page >= pageCount} onClick={() => onPage(page + 1)}>
            다음 ›
          </button>
        </span>
      )}
    </div>
  );
}

// 병합 모달 — window.prompt 대체. 대상 개념을 검색해 클릭하면 병합.
function MergeModal({ from, items, onCancel, onConfirm }) {
  const [q, setQ] = useState("");
  const ql = q.trim().toLowerCase();
  const candidates = items
    .filter((it) => it.name !== from)
    .filter((it) => !ql || it.name.toLowerCase().includes(ql))
    .slice(0, 50);

  return (
    <div className="modal-backdrop" onClick={onCancel}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>
          <b>{from}</b> 을(를) 다른 개념의 alias로 병합
        </h3>
        <p className="muted">
          대상 개념을 고르면 <b>{from}</b> 이(가) 그 개념의 alias로 흡수되고 삭제됩니다.
        </p>
        <input
          autoFocus
          className="modal-search"
          placeholder="대상 개념 검색…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <div className="modal-list">
          {candidates.length === 0 ? (
            <div className="muted" style={{ padding: 10 }}>
              일치하는 개념 없음
            </div>
          ) : (
            candidates.map((it) => (
              <button
                key={it.name}
                className="modal-item"
                onClick={() => onConfirm(it.name)}
              >
                <span>{it.name}</span>
                <span className={`badge st-${it.status}`}>{it.status}</span>
              </button>
            ))
          )}
        </div>
        <div className="modal-actions">
          <button onClick={onCancel}>취소</button>
        </div>
      </div>
    </div>
  );
}

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
function ConceptCard({ item, card, onPatch, onDecision, onMerge }) {
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
        <span className={`badge st-${item.status}`}>{item.status}</span>
        <span className="cc-spacer" />
        <div className="cc-actions">
          <button
            className="cc-approve"
            disabled={item.status === "approved"}
            onClick={() => onDecision(item.name, "approve", null)}
            title="승인 → 그래프에 표시"
          >
            ✓ 승인
          </button>
          <button
            className="cc-reject"
            disabled={item.status === "rejected"}
            onClick={() => onDecision(item.name, "reject", null)}
            title="거부 → 그래프에서 제거"
          >
            ✕ 거부
          </button>
          <button onClick={() => onMerge(item.name)} title="다른 개념의 alias로 병합">
            ⤳ 병합
          </button>
        </div>
      </div>

      {/* 근거 — 항상 보임(판단 1초) */}
      <div className="cc-evidence">
        {definition ? (
          <p className="cc-def">{definition}</p>
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
