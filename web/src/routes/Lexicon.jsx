import { useEffect, useMemo, useState } from "react";
import { getLexicon, mergeLexicon, patchLexicon } from "../api.js";

const STATUSES = ["approved", "unreviewed", "pending", "rejected"];
const FILTERS = ["pending", "unreviewed", "approved", "rejected", "all"];
const PAGE_SIZE = 50;

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
  const [showHelp, setShowHelp] = useState(true); // 상태 설명 펼침(기본 표시)
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
  }, []);

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

  async function doMerge(from) {
    const into = window.prompt(
      `"${from}"을(를) 어느 개념의 alias로 병합할까요?\n대상 개념명을 정확히 입력하세요.`
    );
    if (!into) return;
    if (!items.some((it) => it.name === into)) {
      flash(`대상 개념 없음: ${into}`, true);
      return;
    }
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

  // 필터/검색/정렬이 바뀌면 1페이지로
  useEffect(() => {
    setPage(1);
  }, [filter, q, sortKey, sortDir]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount);
  const paged = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

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
        <span className="muted lex-total">
          총 {items.length}개 · 조건 {filtered.length}
        </span>
      </div>
      {!loading && filtered.length > 0 && (
        <div className="lex-pager">
          <span className="muted">
            {(safePage - 1) * PAGE_SIZE + 1}–
            {Math.min(safePage * PAGE_SIZE, filtered.length)} / {filtered.length}
          </span>
          {pageCount > 1 && (
            <span className="lex-pager-ctrl">
              <button disabled={safePage <= 1} onClick={() => setPage(safePage - 1)}>
                ‹ 이전
              </button>
              <span className="muted">
                {safePage} / {pageCount}
              </span>
              <button
                disabled={safePage >= pageCount}
                onClick={() => setPage(safePage + 1)}
              >
                다음 ›
              </button>
            </span>
          )}
        </div>
      )}

      {loading ? (
        <div className="muted">로딩 중…</div>
      ) : (
        <table className="lex-table">
          <thead>
            <tr>
              {th("name", "개념명", "16%")}
              <th style={{ width: "22%" }}>aliases</th>
              {th("status", "status", "12%")}
              <th style={{ width: "28%" }}>definition</th>
              {th("source", "source", "8%")}
              {th("first_seen", "first_seen", "8%")}
              <th style={{ width: "6%" }}>액션</th>
            </tr>
          </thead>
          <tbody>
            {paged.map((it) => (
              <Row
                key={it.name}
                item={it}
                onPatch={applyPatch}
                onMerge={doMerge}
              />
            ))}
          </tbody>
        </table>
      )}
      {!loading && filtered.length === 0 && (
        <div className="muted" style={{ padding: 20 }}>
          해당 조건의 개념이 없습니다.
        </div>
      )}

      {toast && (
        <div className={`toast${toast.err ? " err" : ""}`}>{toast.msg}</div>
      )}
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
          rows={2}
          style={{ width: "100%", resize: "vertical" }}
          value={def}
          onChange={(e) => setDef(e.target.value)}
          onBlur={() => defDirty && onPatch(item.name, { definition: def })}
          placeholder="(비어 있음)"
        />
      </td>
      <td className="muted">{item.source}</td>
      <td className="muted">{item.first_seen}</td>
      <td>
        <button
          className="lex-merge-btn"
          onClick={() => onMerge(item.name)}
          title="다른 개념의 alias로 병합"
        >
          병합
        </button>
      </td>
    </tr>
  );
}
