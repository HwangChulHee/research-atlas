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
const CONF_RANK = { low: 0, med: 1, high: 2 };

const STATUSES = ["approved", "unreviewed", "pending", "rejected"];
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
  const [sortKey, setSortKey] = useState(null); // "name" | "status" | "source" | "first_seen"
  const [sortDir, setSortDir] = useState("asc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [showHelp, setShowHelp] = useState(true); // 상태 설명 펼침(기본 표시)
  const [mergeFrom, setMergeFrom] = useState(null); // 병합 모달 대상(개념명) 또는 null
  const [reviewCards, setReviewCards] = useState([]); // 검토 도우미 제안 카드(정적 스냅샷)
  const [rebuilding, setRebuilding] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [toast, setToast] = useState(null); // {msg, err}

  function toggleSort(key) {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

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

  // 상태 필터 + 이름 검색 → 정렬. 검색은 목록을 좁힌다(페이징과 자연스럽게 결합).
  const filtered = useMemo(() => {
    let arr = items.filter((it) => filter === "all" || it.status === filter);
    if (q) arr = arr.filter((it) => it.name.toLowerCase().includes(q));
    if (sortKey) {
      arr = [...arr].sort((a, b) => {
        const av = (a[sortKey] ?? "").toString().toLowerCase();
        const bv = (b[sortKey] ?? "").toString().toLowerCase();
        const cmp = av < bv ? -1 : av > bv ? 1 : 0;
        return sortDir === "asc" ? cmp : -cmp;
      });
    }
    return arr;
  }, [items, filter, q, sortKey, sortDir]);

  // 필터/검색/정렬/페이지크기가 바뀌면 1페이지로
  useEffect(() => {
    setPage(1);
  }, [filter, q, sortKey, sortDir, pageSize]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const safePage = Math.min(page, pageCount);
  const paged = filtered.slice((safePage - 1) * pageSize, safePage * pageSize);

  // 검토 도우미: 아직 pending/unreviewed인 개념의 카드만(처리된 건 자동으로 빠짐).
  const statusByName = useMemo(() => {
    const m = {};
    for (const it of items) m[it.name] = it.status;
    return m;
  }, [items]);
  const liveCards = useMemo(
    () =>
      reviewCards.filter((c) =>
        ["pending", "unreviewed"].includes(statusByName[c.concept])
      ),
    [reviewCards, statusByName]
  );
  const approvedNames = useMemo(
    () =>
      items
        .filter((it) => it.status === "approved")
        .map((it) => it.name)
        .sort(),
    [items]
  );

  // 정렬 가능한 헤더 셀
  const th = (key, label, width) => (
    <th
      style={{ width, cursor: "pointer" }}
      onClick={() => toggleSort(key)}
      title="클릭하여 정렬"
    >
      {label}
      {sortKey === key ? (sortDir === "asc" ? " ▲" : " ▼") : ""}
    </th>
  );

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

      {(counts.pending || 0) + (counts.unreviewed || 0) > 0 && (
        <ReviewPanel
          cards={liveCards}
          approvedNames={approvedNames}
          onDecision={applyDecision}
          onRebuild={doRebuild}
          rebuilding={rebuilding}
          onRegenerate={doRegenerate}
          regenerating={regenerating}
        />
      )}
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
        <table className="lex-table">
          <thead>
            <tr>
              {th("name", "개념명", "15%")}
              <th style={{ width: "20%" }}>aliases</th>
              {th("status", "status", "11%")}
              <th style={{ width: "24%" }}>definition</th>
              {th("source", "source", "7%")}
              {th("first_seen", "first_seen", "8%")}
              <th style={{ width: "15%" }}>액션</th>
            </tr>
          </thead>
          <tbody>
            {paged.map((it) => (
              <Row
                key={it.name}
                item={it}
                onPatch={applyPatch}
                onMerge={setMergeFrom}
              />
            ))}
          </tbody>
        </table>
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

function Row({ item, onPatch, onMerge }) {
  const [newAlias, setNewAlias] = useState("");
  const [def, setDef] = useState(item.definition || "");
  const defDirty = def !== (item.definition || "");

  function addAlias() {
    const a = newAlias.trim();
    if (!a || item.aliases.includes(a)) {
      setNewAlias("");
      return;
    }
    onPatch(item.name, { aliases: [...item.aliases, a] });
    setNewAlias("");
  }
  function removeAlias(a) {
    onPatch(item.name, { aliases: item.aliases.filter((x) => x !== a) });
  }

  return (
    <tr>
      <td>{item.name}</td>
      <td>
        {item.aliases.map((a) => (
          <span className="alias-chip" key={a}>
            {a}
            <button title="삭제" onClick={() => removeAlias(a)}>
              ×
            </button>
          </span>
        ))}
        <input
          placeholder="+ alias"
          value={newAlias}
          onChange={(e) => setNewAlias(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addAlias()}
          onBlur={addAlias}
          style={{ width: 80 }}
        />
      </td>
      <td>
        <select
          className={`badge st-${item.status}`}
          value={item.status}
          onChange={(e) => onPatch(item.name, { status: e.target.value })}
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </td>
      <td>
        <textarea
          className={`lex-def${defDirty ? " dirty" : ""}`}
          rows={2}
          style={{ width: "100%", resize: "vertical" }}
          value={def}
          onChange={(e) => setDef(e.target.value)}
          onBlur={() => defDirty && onPatch(item.name, { definition: def })}
          placeholder="(비어 있음)"
        />
        {defDirty && (
          <div className="lex-def-hint muted">변경됨 — 포커스 해제 시 저장</div>
        )}
      </td>
      <td className="muted">{item.source}</td>
      <td className="muted">{item.first_seen}</td>
      <td>
        <div className="lex-actions">
          <button
            className="lex-approve"
            disabled={item.status === "approved"}
            onClick={() => onPatch(item.name, { status: "approved" })}
            title="승인 → 그래프에 표시"
          >
            ✓ 승인
          </button>
          <button
            className="lex-reject"
            disabled={item.status === "rejected"}
            onClick={() => onPatch(item.name, { status: "rejected" })}
            title="거부 → 그래프에서 제거"
          >
            ✕ 거부
          </button>
          <button
            className="lex-merge-btn"
            onClick={() => onMerge(item.name)}
            title="다른 개념의 alias로 병합"
          >
            병합
          </button>
        </div>
      </td>
    </tr>
  );
}

// 검토 도우미 패널 — 제안 카드(정적 스냅샷)를 큐로 띄우고 카드별/일괄 적용.
// 적용은 onDecision(applyDecision) 하나로 dispatch. low/med는 개별만, high는 일괄 가능.
function ReviewPanel({
  cards,
  approvedNames,
  onDecision,
  onRebuild,
  rebuilding,
  onRegenerate,
  regenerating,
}) {
  const [open, setOpen] = useState(true);
  const [showHigh, setShowHigh] = useState(false);
  const [selected, setSelected] = useState(() => new Set());
  const [targets, setTargets] = useState({});
  const [busy, setBusy] = useState(false);

  const sorted = [...cards].sort(
    (a, b) =>
      CONF_RANK[a.suggestion.confidence] - CONF_RANK[b.suggestion.confidence]
  );
  const lowMed = sorted.filter((c) => c.suggestion.confidence !== "high");
  const high = sorted.filter((c) => c.suggestion.confidence === "high");

  const targetOf = (c) =>
    targets[c.concept] !== undefined ? targets[c.concept] : c.similar_existing || "";

  const applySuggestion = (c) => {
    const [act, tgt] = parseAction(c.suggestion.action);
    onDecision(c.concept, act, act === "merge" ? tgt : null);
  };

  function toggleSel(name) {
    setSelected((s) => {
      const n = new Set(s);
      if (n.has(name)) n.delete(name);
      else n.add(name);
      return n;
    });
  }

  async function applyBatch() {
    const chosen = high.filter((c) => selected.has(c.concept));
    if (chosen.length === 0) return;
    const counts = { approve: 0, reject: 0, merge: 0 };
    chosen.forEach((c) => (counts[parseAction(c.suggestion.action)[0]] += 1));
    if (
      !window.confirm(
        `approve ${counts.approve} · reject ${counts.reject} · merge ${counts.merge} 적용할까요?`
      )
    )
      return;
    setBusy(true);
    for (const c of chosen) {
      const [act, tgt] = parseAction(c.suggestion.action);
      // eslint-disable-next-line no-await-in-loop
      await onDecision(c.concept, act, act === "merge" ? tgt : null);
    }
    setSelected(new Set());
    setBusy(false);
  }

  const evidence = (c) => {
    const e = c.evidence || {};
    const empty =
      !e.definition && !(e.defined_in || []).length && !(e.cited_in || []).length;
    return (
      <div className="rv-evidence">
        {e.definition && <div>정의: {e.definition.slice(0, 220)}</div>}
        {(e.defined_in || []).length > 0 && (
          <div>정의 논문: {e.defined_in.map((d) => d.paper).join(", ")}</div>
        )}
        {(e.cited_in || []).length > 0 && (
          <div>조상 인용: {e.cited_in.join(", ")}</div>
        )}
        {empty && <div className="muted">근거 없음(이름만) — 확인 필요</div>}
      </div>
    );
  };

  const controls = (c, primary) => (
    <div className="rv-controls">
      <button
        className={`rv-apply${primary ? " primary" : ""}`}
        onClick={() => applySuggestion(c)}
      >
        이대로 적용 · {c.suggestion.action}
      </button>
      <span className="rv-manual">
        <button onClick={() => onDecision(c.concept, "approve", null)}>승인</button>
        <button onClick={() => onDecision(c.concept, "reject", null)}>거부</button>
        <button
          onClick={() => onDecision(c.concept, "merge", targetOf(c))}
          disabled={!targetOf(c)}
        >
          병합→
        </button>
        <select
          value={targetOf(c)}
          onChange={(e) => setTargets((t) => ({ ...t, [c.concept]: e.target.value }))}
        >
          <option value="">(대상)</option>
          {approvedNames.map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
      </span>
    </div>
  );

  const cardRow = (c, batch) => (
    <div className="rv-card" key={c.concept}>
      <div className="rv-head">
        {batch && (
          <input
            type="checkbox"
            checked={selected.has(c.concept)}
            onChange={() => toggleSel(c.concept)}
          />
        )}
        <b>{c.concept}</b>
        <span className={`badge st-${c.status}`}>{c.status}</span>
        <span className={`rv-conf rv-${c.suggestion.confidence}`}>
          {c.suggestion.confidence}
        </span>
      </div>
      {evidence(c)}
      <div className="rv-sugg">
        제안: <b>{c.suggestion.category}</b> — {c.suggestion.reason}
      </div>
      {controls(c, c.suggestion.confidence !== "low")}
    </div>
  );

  return (
    <section className="rv-panel">
      <div className="rv-panel-head">
        <button className="rv-toggle" onClick={() => setOpen((v) => !v)}>
          검토 도우미 제안 {cards.length}개 {open ? "▴" : "▾"}
        </button>
        <span className="muted">제안일 뿐 — 적용은 당신의 클릭</span>
        <span className="spacer" />
        <button
          onClick={onRegenerate}
          disabled={regenerating}
          title="카드 없는 신규 검토대기 개념만 제안 생성(LLM)"
        >
          {regenerating ? "제안 생성 중…" : "✦ 제안 새로고침"}
        </button>
        <button onClick={onRebuild} disabled={rebuilding} title="pending 승인분을 노드로 반영">
          {rebuilding ? "재빌드 중…" : "↻ 재빌드"}
        </button>
      </div>
      {open && (
        <>
          {cards.length === 0 && (
            <div className="muted rv-empty">
              제안 카드가 없습니다. 새 개념이 들어왔다면 [✦ 제안 새로고침]으로 생성하세요.
            </div>
          )}
          {cards.length > 0 && (
            <div className="rv-section-title">
              ⚠️ 확신 낮음·중간 — 한 장씩 검토 ({lowMed.length})
            </div>
          )}
          {cards.length > 0 && lowMed.length === 0 && (
            <div className="muted rv-empty">없음</div>
          )}
          {lowMed.map((c) => cardRow(c, false))}

          {high.length > 0 && (
          <div className="rv-high">
            <button className="rv-toggle" onClick={() => setShowHigh((v) => !v)}>
              ✅ 확신 높음 {high.length}개 {showHigh ? "접기 ▴" : "펼치기 ▾"}
            </button>
            {showHigh && (
              <>
                <div className="rv-batchbar">
                  <button
                    className="primary"
                    disabled={busy || selected.size === 0}
                    onClick={applyBatch}
                  >
                    선택 적용 ({selected.size})
                  </button>
                  <span className="muted">체크 후 일괄. low/med는 일괄 대상이 아니에요.</span>
                </div>
                {high.map((c) => cardRow(c, true))}
              </>
            )}
          </div>
          )}
        </>
      )}
    </section>
  );
}
