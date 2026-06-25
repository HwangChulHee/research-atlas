import { useEffect, useMemo, useState } from "react";
import {
  getLexicon,
  mergeLexicon,
  patchLexicon,
  rebuild,
  getReviewSuggestions,
  regenerateReviewSuggestions,
} from "../api.js";
import { CONF, FILTERS, PAGE_SIZES, STATUS_INFO } from "../lib/lexiconConstants.js";
import Pager from "../components/Pager.jsx";
import MergeModal from "../components/MergeModal.jsx";
import ConceptCard from "../components/ConceptCard.jsx";

export default function Lexicon() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("pending"); // 대기열 처리가 주 작업
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [showHelp, setShowHelp] = useState(true); // 상태 설명 펼침(기본 표시)
  const [mergeFrom, setMergeFrom] = useState(null); // 병합 모달 대상(개념명) 또는 null
  const [reviewCards, setReviewCards] = useState([]); // 검토 도우미 제안 카드(정적 스냅샷)
  const [rebuilding, setRebuilding] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [toast, setToast] = useState(null); // {msg, err}

  const flash = (msg, err = false) => {
    setToast({ msg, err });
    if (!err) setTimeout(() => setToast(null), 3000); // 에러는 수동으로 닫을 때까지 유지
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

  // 수동 상태 변경(4개 중 아무거나). approved/rejected는 applyDecision으로(토스트·노드 동기),
  // pending/unreviewed로 되돌리기는 단순 status 패치.
  function setStatus(name, status) {
    if (status === "approved") return applyDecision(name, "approve", null);
    if (status === "rejected") return applyDecision(name, "reject", null);
    return applyPatch(name, { status });
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
        <p>개념 후보를 승인·거부·병합해 정리합니다 — 대기열(pending) 처리가 주 작업이에요.</p>
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
          className="lex-op"
          onClick={doRegenerate}
          disabled={regenerating}
          title="카드 없는 신규 검토대기 개념만 제안 생성(LLM)"
        >
          {regenerating ? "제안 생성 중…" : "✦ 제안 새로고침"}
        </button>
        <button
          className="lex-op"
          onClick={doRebuild}
          disabled={rebuilding}
          title="pending 승인분을 노드로 반영(그래프 재빌드)"
        >
          {rebuilding ? "재빌드 중…" : "↻ 재빌드"}
        </button>
        <span className="lex-tb-sep" />
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
              onSetStatus={setStatus}
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
        <div className={`toast${toast.err ? " err" : ""}`}>
          {toast.msg}
          <button className="toast-x" onClick={() => setToast(null)} title="닫기">
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
