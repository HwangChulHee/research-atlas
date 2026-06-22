import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import * as d3 from "d3";
import {
  getGraph,
  postCommand,
  collectStart,
  collectResume,
  collectGetState,
  postReviewed,
} from "../api.js";

// 대화 이력 localStorage 복원(chatWidth 패턴). 파싱 실패 시 빈 배열.
// key별로 분리: "chatMessages"=명령 탭 / "collectMessages"=수집 탭.
function loadMessages(key) {
  try {
    const raw = localStorage.getItem(key);
    const arr = raw ? JSON.parse(raw) : [];
    return Array.isArray(arr) ? arr : [];
  } catch {
    return [];
  }
}

const TYPE_COLOR = {
  technique: "#2563eb",
  benchmark: "#d97706",
  analysis: "#7c3aed",
  survey: "#059669",
  other: "#888",
};

// arXiv ID "2502.14192" → 등장 연월 "2025-02". 형식이 다르면 null.
function arxivMonth(id) {
  const m = String(id).slice(0, 4);
  if (!/^\d{4}$/.test(m)) return null;
  return `20${m.slice(0, 2)}-${m.slice(2, 4)}`;
}

// 노드 등장 시점 = papers 중 가장 이른 연월. papers 없으면 null(시점 불명).
function nodeMonth(node) {
  if (!node.papers || node.papers.length === 0) return null;
  let earliest = null;
  for (const id of node.papers) {
    const ym = arxivMonth(id);
    if (ym && (!earliest || ym < earliest)) earliest = ym;
  }
  return earliest;
}

// 채팅 폭 제약: min 300px(카드 가독성) ~ max min(창폭*0.55, 720)(그래프 안 사라지게)
const CHAT_MIN = 300;
function clampChat(w) {
  const max = Math.min(window.innerWidth * 0.55, 720);
  return Math.max(CHAT_MIN, Math.min(w, max));
}

export default function Graph() {
  const svgRef = useRef(null);
  const areaRef = useRef(null); // 그래프 영역 div (크기 측정용)
  const apiRef = useRef(null); // render()가 돌려준 {sim, focus, names, highlight, resize}
  const dataRef = useRef(null); // 원본 그래프 데이터 {nodes, builds_on}
  const lastQ = useRef(""); // 같은 검색어 Enter → 다음 매칭 순회
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState(null);
  const [showPapers, setShowPapers] = useState(false); // "논문 보기" 토글
  const [query, setQuery] = useState("");
  const [matches, setMatches] = useState([]); // [{id, canonical}]
  const [matchIdx, setMatchIdx] = useState(0);
  const [searchMsg, setSearchMsg] = useState(""); // "없음" 등

  // --- 채팅 패널 상태 ---
  const [collapsed, setCollapsed] = useState(false);
  const [chatWidth, setChatWidth] = useState(() => {
    const saved = Number(localStorage.getItem("chatWidth"));
    return clampChat(saved > 0 ? saved : 420);
  });
  const [dragging, setDragging] = useState(false);
  const [activeTab, setActiveTab] = useState("command"); // "command" | "collect"
  const [messages, setMessages] = useState(() => loadMessages("chatMessages")); // 명령 탭 [{role,text}]
  const [collectMessages, setCollectMessages] = useState(() => loadMessages("collectMessages")); // 수집 탭
  const [chatInput, setChatInput] = useState("");
  const [collectInput, setCollectInput] = useState("");
  const [pending, setPending] = useState(false);
  const [chips, setChips] = useState([]); // 활성 조건 칩 라벨들
  const [filterState, setFilterState] = useState({}); // filter 차원의 단일 진실원 {ptype?,domain?,date_after?}
  const msgEndRef = useRef(null);

  // --- 수집 에이전트 흐름 상태 ---
  // null = 수집중 아님 / {thread_id, stage, data, busy, timedOut}
  const [collect, setCollect] = useState(null);
  const [reviseOpen, setReviseOpen] = useState(false);
  const [reviseText, setReviseText] = useState("");
  const EXTRACT_TIMEOUT_MS = 120000;

  // [사용법] 페이지에서 넘어온 질의 자동 실행용. apiRef 준비(ready) 후 1회만 소비.
  const location = useLocation();
  const navigate = useNavigate();
  const [ready, setReady] = useState(false);
  const consumedRef = useRef(false);

  // 최초 로드 + "논문 보기" 토글 시 재로드/재렌더. 토글은 개념 강조/선택을 초기화.
  useEffect(() => {
    setSelected(null);
    setChips([]);
    setReady(false); // 안정될 때까지 로딩 오버레이로 가림(휘날리는 모션 숨김)
    getGraph(showPapers)
      .then((data) => {
        dataRef.current = data;
        // ready는 시뮬레이션이 안정(settle)된 뒤에 — 그제서야 정돈된 그래프를 보여줌.
        apiRef.current = render(areaRef.current, svgRef.current, data, setSelected,
          () => setReady(true));
      })
      .catch((e) => setError(e.message));
    return () => apiRef.current && apiRef.current.sim.stop();
  }, [showPapers]);

  // 그래프 영역 크기 변화(패널 접기/펴기, 윈도우 리사이즈) → svg/force 갱신
  useEffect(() => {
    if (!areaRef.current) return;
    const ro = new ResizeObserver(() => apiRef.current && apiRef.current.resize());
    ro.observe(areaRef.current);
    return () => ro.disconnect();
  }, []);

  // 메시지/대기/수집카드(단계 전환·busy)·탭 전환 시 맨 아래로 — 새 카드가 화면 밖에 안 묻히게
  useEffect(() => {
    msgEndRef.current && msgEndRef.current.scrollIntoView({ block: "end" });
  }, [messages, collectMessages, pending, collect, activeTab]);

  // 채팅 폭 변경 시 localStorage 저장(새로고침에도 유지)
  useEffect(() => {
    localStorage.setItem("chatWidth", String(chatWidth));
  }, [chatWidth]);

  // 대화 이력 저장(새로고침/브라우저 재시작에 대화 유지). chips는 그래프 상태와 연동돼 미복원.
  useEffect(() => {
    localStorage.setItem("chatMessages", JSON.stringify(messages));
  }, [messages]);

  // 수집 탭 이력 저장(명령 탭과 분리된 별도 키).
  useEffect(() => {
    localStorage.setItem("collectMessages", JSON.stringify(collectMessages));
  }, [collectMessages]);

  // 부팅 시 수집 세션 복원 — 저장된 thread_id로 서버 체크포인터 상태 조회.
  // 성공 시 카드 복원, 404(만료) 면 localStorage에서 제거. 마운트 1회.
  useEffect(() => {
    const tid = localStorage.getItem("collectThread");
    if (!tid) return;
    collectGetState(tid)
      .then((res) => {
        applyCollectResponse(res);
        if (!res.done) setActiveTab("collect"); // 복원된 흐름이 살아있으면 수집 탭으로 — "사라진 듯" 방지
      })
      .catch(() => localStorage.removeItem("collectThread"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // [사용법]에서 넘어온 질의 자동 실행 — 그래프 준비(ready) 후 1회. state는 비워 재실행 방지.
  // run 계열은 읽기전용 하이라이트라 즉시 실행. collect는 destructive라 주제만 prefill(자동 시작 X).
  // 들어온 질의가 없으면 기본 뷰 = RAG 계보(전체 헤어볼 대신 한 줄기만 — 임시 기본).
  useEffect(() => {
    if (!ready || consumedRef.current) return;
    const st = location.state || {};
    if (st.run) {
      consumedRef.current = true;
      runCommand(st.run);
      navigate("/graph", { replace: true, state: null });
    } else if (st.collectTopic) {
      consumedRef.current = true;
      setActiveTab("collect");
      setCollectInput(st.collectTopic); // 수집 입력창 prefill, 사람이 [시작] 눌러야 함
      navigate("/graph", { replace: true, state: null });
    } else {
      consumedRef.current = true;
      const r = lineageSets("RAG", "both"); // 기본: RAG 계보로 시작
      if (r) {
        apiRef.current.highlightLineage(r.key, r.ancSet, r.descSet);
        setChips([`기본: RAG 계보`]);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, location.state]);

  // divider 드래그: chat 폭 = 창 오른쪽 끝 − 마우스X. mouseup에 리스너 해제.
  function onDividerDown(e) {
    e.preventDefault();
    setDragging(true);
    document.body.classList.add("resizing-pane");
    const onMove = (ev) => setChatWidth(clampChat(window.innerWidth - ev.clientX));
    const onUp = () => {
      setDragging(false);
      document.body.classList.remove("resizing-pane");
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
  }

  function goTo(id, list, idx) {
    apiRef.current.focus(id);
    setMatches(list);
    setMatchIdx(idx);
    setSearchMsg("");
  }

  function runSearch(e) {
    e.preventDefault();
    const api = apiRef.current;
    if (!api) return;
    const q = query.trim().toLowerCase();
    if (!q) {
      setMatches([]);
      setSearchMsg("");
      return;
    }
    const found = api.names.filter((n) =>
      n.canonical.toLowerCase().includes(q)
    );
    if (found.length === 0) {
      setMatches([]);
      setSearchMsg("없음");
      lastQ.current = q;
      return;
    }
    // 같은 검색어로 다시 Enter → 다음 매칭으로 순회
    const advance = q === lastQ.current && found.length > 1;
    const idx = advance ? (matchIdx + 1) % found.length : 0;
    lastQ.current = q;
    goTo(found[idx].id, found, idx);
  }

  // --- 채팅: tool 실행 의미론 ---
  function applyFilter(args) {
    const nodes = dataRef.current.nodes;
    const ids = new Set();
    for (const [id, n] of Object.entries(nodes)) {
      if (n.type === "paper") continue; // 필터/계보는 개념만 대상(논문은 표시용)
      if (args.ptype && n.ptype !== args.ptype) continue;
      if (args.domain && n.domain !== args.domain) continue;
      if (args.unreviewed_only && n.reviewed) continue; // 이미 본 것 제외
      if (args.date_after) {
        const ym = nodeMonth(n);
        if (!ym || ym < args.date_after) continue;
      }
      ids.add(id);
    }
    return ids;
  }

  function lineageSets(node, direction) {
    const nodes = dataRef.current.nodes;
    const builds = dataRef.current.builds_on;
    // 들어온 node를 노드 id(rk)로 해소한다. focus_lineage는 canonical("Self-RAG")로 들어오는데
    // rk는 canonical에서 하이픈→공백·소문자화로 생성되므로("self rag") 단순 toLowerCase로는 불일치.
    // 직접 키 우선 → 소문자 키 → canonical 소문자 매칭 순. 못 찾으면 null.
    const raw = String(node);
    const lower = raw.toLowerCase();
    let key = null;
    if (nodes[raw]) key = raw;
    else if (nodes[lower]) key = lower;
    else {
      for (const [id, n] of Object.entries(nodes)) {
        if (n.canonical && n.canonical.toLowerCase() === lower) {
          key = id;
          break;
        }
      }
    }
    if (!key) return null;
    // 사이클 방지 visited 사용. start 자신은 결과 집합에 미포함(개수 분리용).
    const walk = (next) => {
      const out = new Set();
      const visited = new Set([key]);
      const stack = [key];
      while (stack.length) {
        const cur = stack.pop();
        for (const nx of next(cur)) {
          if (!visited.has(nx)) {
            visited.add(nx);
            out.add(nx);
            stack.push(nx);
          }
        }
      }
      return out;
    };
    // builds_on {from, to}: from이 to 위에 지어짐 = to가 조상.
    const ancestors = walk((cur) =>
      builds.filter((b) => b.from === cur).map((b) => b.to)
    );
    const descendants = walk((cur) =>
      builds.filter((b) => b.to === cur).map((b) => b.from)
    );
    const ancSet = direction === "descendants" ? new Set() : new Set(ancestors);
    const descSet = direction === "ancestors" ? new Set() : new Set(descendants);
    const ids = new Set([...ancSet, ...descSet, key]);
    return {
      ids,
      key,
      ancSet,
      descSet,
      ancestors: ancSet.size,
      descendants: descSet.size,
    };
  }

  function filterChips(args) {
    const c = [];
    if (args.ptype) c.push(`ptype=${args.ptype}`);
    if (args.domain) c.push(`domain=${args.domain}`);
    if (args.date_after) c.push(`date_after=${args.date_after}`);
    if (args.unreviewed_only) c.push("안 본 것만");
    return c;
  }

  function addAgent(text) {
    setMessages((m) => [...m, { role: "agent", text }]);
  }

  // filter 차원의 단일 진실원. 드롭다운·채팅 filter·초기화 모두 이걸 호출(effect 경쟁 회피).
  // 빈 값(undefined) 키는 정리해서, 모두 비면 전체 복원으로 취급.
  function setFilter(next) {
    const clean = {};
    if (next.ptype) clean.ptype = next.ptype;
    if (next.domain) clean.domain = next.domain;
    if (next.date_after) clean.date_after = next.date_after;
    if (next.unreviewed_only) clean.unreviewed_only = true;
    setFilterState(clean);
    if (Object.keys(clean).length === 0) {
      apiRef.current && apiRef.current.highlight(null);
      setChips([]);
      return;
    }
    const ids = applyFilter(clean);
    if (ids.size === 0) {
      addAgent("조건에 맞는 노드가 없음"); // 강조 변경 없이 유지
      return;
    }
    apiRef.current.highlight(ids);
    setChips(filterChips(clean));
  }

  // 노드 클릭 → 디테일 패널의 계보 버튼. selected.id는 이미 rk(노드 id)라 하이픈 이슈 무관.
  function runLineageFromNode(id, dir) {
    const r = lineageSets(id, dir);
    if (!r) return;
    apiRef.current.highlightLineage(r.key, r.ancSet, r.descSet);
    const canonical = dataRef.current.nodes[r.key].canonical;
    setChips([`lineage=${canonical}`]);
    setFilterState({}); // 드롭다운 표시만 비움(highlight는 위에서 직접 세팅 — effect 안 터짐)
    addAgent(`'${canonical}' 계보 — 조상 ${r.ancestors}(파랑) · 자손 ${r.descendants}(주황)`);
  }

  // 수집 탭 전용 에이전트 메시지(명령 탭 이력과 분리).
  function addCollectMsg(text) {
    setCollectMessages((m) => [...m, { role: "agent", text }]);
  }

  function handleResult(res) {
    if (!res.tool) {
      addAgent(res.message || "처리할 수 없는 요청입니다.");
      return;
    }
    if (res.tool === "filter") {
      setFilter(res.args || {}); // 드롭다운과 단일 진실원 공유
      return;
    }
    if (res.tool === "focus_lineage") {
      const args = res.args || {};
      const r = lineageSets(args.node, args.direction);
      if (!r) {
        addAgent(`'${args.node}' 노드를 찾지 못함`);
        return;
      }
      apiRef.current.highlightLineage(r.key, r.ancSet, r.descSet);
      const canonical = dataRef.current.nodes[r.key].canonical;
      setChips([`lineage=${canonical}`]);
      setFilterState({}); // 드롭다운 표시 동기(highlight는 위에서 직접 세팅)
      addAgent(
        `'${canonical}' 계보 — 조상 ${r.ancestors}(파랑) · 자손 ${r.descendants}(주황)`
      );
      return;
    }
    if (res.tool === "reset") {
      setFilter({}); // 필터·계보·의미검색 강조 모두 해제
      return;
    }
    if (res.tool === "semantic_search") {
      const a = res.args || {};
      const concepts = a.concepts || [];
      const papers = a.papers || [];
      // reviewed로 가르기(②-b). 논문은 reviewed 없음 → 항상 '안 본 것' 취급.
      const all = [...concepts, ...papers];
      const seen = [];
      const unseen = [];
      for (const h of all) {
        (dataRef.current.nodes[h.id]?.reviewed ? seen : unseen).push(h.id);
      }
      const lens = !!filterState.unreviewed_only;
      // 렌즈 ON이면 안 본 것만, OFF면 전부 강조(cosine 순서 유지 — 재정렬 안 함).
      const ids = new Set(lens ? unseen : [...unseen, ...seen]);
      if (ids.size === 0) {
        addAgent(`'${a.query}'${lens ? " 안 본 결과 없음" : "와(과) 유사한 노드 없음"}`);
        return;
      }
      apiRef.current.highlight(ids);
      setChips([`검색="${a.query}"`, ...(lens ? ["안 본 것만"] : [])]);
      setFilterState(lens ? { unreviewed_only: true } : {}); // 필터 표시 비우되 렌즈는 유지
      addAgent(
        `'${a.query}' 의미검색 · 안 본 것 ${unseen.length} · 이미 본 것 ${seen.length}` +
          (lens ? " (안 본 것만 강조)" : "")
      );
      // 논문 hit가 있는데 논문 표시가 꺼져 있으면 안내(토글은 사용자 몫 — 자동 변경 안 함).
      if (papers.length > 0 && !showPapers) {
        addAgent(`논문 ${papers.length}개도 매칭됨 — '논문 보기'를 켜면 보입니다.`);
      }
      return;
    }
    addAgent(`알 수 없는 도구: ${res.tool}`);
  }

  async function runCommand(text) {
    if (!text || pending || !apiRef.current) return; // 명령 탭은 수집과 독립(잠금 제거)
    setMessages((m) => [...m, { role: "user", text }]);
    setPending(true);
    try {
      const res = await postCommand(text);
      handleResult(res); // collect 라우팅 제거 — fetch 의도는 {tool:null, message} 안내로 옴
    } catch (err) {
      addAgent(`요청 실패: ${err.message}`);
    } finally {
      setPending(false);
    }
  }

  // --- 수집 흐름: start → interrupt 카드 → resume … ---
  function applyCollectResponse(res) {
    if (res.done) {
      addCollectMsg(res.summary || "수집 종료");
      if ((res.extracted || []).length) {
        addCollectMsg(`추출 ${res.extracted.length}편 — 지도에 반영하려면 재빌드가 필요해요.`);
      }
      setCollect(null);
      setReviseOpen(false);
      localStorage.removeItem("collectThread"); // 흐름 종료 → 복원 대상 제거
      return;
    }
    // thread_id 저장 → 새로고침/재접속 시 부팅 복원(chatWidth 패턴)
    localStorage.setItem("collectThread", res.thread_id);
    setCollect({ thread_id: res.thread_id, stage: res.stage, data: res, busy: false });
  }

  async function startCollect(text) {
    setActiveTab("collect"); // 수집 시작 → 수집 탭으로
    try {
      applyCollectResponse(await collectStart(text));
    } catch (err) {
      addCollectMsg(`수집 시작 실패: ${err.message}`);
      setCollect(null);
    }
  }

  async function resumeCollect(decision) {
    if (!collect || collect.busy) return;
    setReviseOpen(false);
    setReviseText(""); // ② 폼 닫으며 입력 잔류 제거
    const isExtract = collect.stage === "extract_confirm" && decision === "proceed";
    setCollect((c) => ({ ...c, busy: true, timedOut: false }));

    let signal, timer;
    if (isExtract) {
      const ctrl = new AbortController();
      signal = ctrl.signal;
      timer = setTimeout(() => ctrl.abort(), EXTRACT_TIMEOUT_MS);
    }
    try {
      const res = await collectResume(collect.thread_id, decision, signal);
      if (timer) clearTimeout(timer);
      applyCollectResponse(res);
    } catch (err) {
      if (timer) clearTimeout(timer);
      if (err.name === "AbortError") {
        // 타임아웃 — 흐름은 살아있음(서버는 계속 추출 중일 수 있음). 안내 후 재시도/취소.
        addCollectMsg("추출이 지연됩니다. 서버에서 계속 진행 중일 수 있어요. 잠시 후 [재시도] 또는 [취소].");
        setCollect((c) => ({ ...c, busy: false, timedOut: true }));
      } else {
        addCollectMsg(`수집 재개 실패: ${err.message}`);
        setCollect(null);
        localStorage.removeItem("collectThread");
      }
    }
  }

  function sendCommand(e) {
    e.preventDefault();
    const text = chatInput.trim();
    if (!text) return;
    setChatInput("");
    runCommand(text);
  }

  // 수집 탭 입력 → 새 수집 흐름 시작. 진행 중인 흐름이 있으면(카드로 응답) 무시.
  function sendCollect(e) {
    e.preventDefault();
    const text = collectInput.trim();
    if (!text || collect) return;
    setCollectInput("");
    setCollectMessages((m) => [...m, { role: "user", text }]);
    startCollect(text);
  }

  function clearHighlight() {
    setFilter({}); // 전체 복원 — highlight·chips·드롭다운 모두 해제
  }

  // 탭별 비우기. 명령 탭: messages+chips+highlight 초기화. 수집 탭: collectMessages+흐름 초기화.
  // (수집 흐름 활성 중엔 수집 탭 비우기 버튼이 disabled — 고아 thread 방지.)
  function clearActiveChat() {
    if (activeTab === "command") {
      setMessages([]);
      setChips([]);
      setFilterState({});
      apiRef.current && apiRef.current.highlight(null);
      localStorage.removeItem("chatMessages");
    } else {
      setCollectMessages([]);
      setCollect(null);
      setReviseOpen(false);
      setReviseText("");
      localStorage.removeItem("collectMessages");
      localStorage.removeItem("collectThread");
    }
  }

  // filter 드롭다운 옵션 — 로드된 개념 노드에서 동적 생성(그래프 실제 값과 항상 일치).
  const concepts = Object.values(dataRef.current?.nodes || {}).filter(
    (n) => n.type !== "paper"
  );
  const ptypeOpts = [...new Set(concepts.map((n) => n.ptype).filter(Boolean))].sort();
  const domainOpts = [...new Set(concepts.map((n) => n.domain).filter(Boolean))].sort();
  const yearOpts = [
    ...new Set(
      concepts
        .map((n) => {
          const ym = nodeMonth(n);
          return ym ? ym.slice(0, 4) : null;
        })
        .filter(Boolean)
    ),
  ].sort();

  return (
    <div className="graph-page">
      <div className="graph-area" ref={areaRef}>
        <svg id="graph-svg" ref={svgRef} />
        {!ready && !error && (
          <div className="graph-loading">
            <span className="spinner" /> 지형도 불러오는 중…
          </div>
        )}
        <button
          className="graph-fit"
          title="전체 보기"
          onClick={() => apiRef.current && apiRef.current.fitView()}
        >
          ⤢ 전체 보기
        </button>
        {chips.length > 0 && (
          <div className="graph-chips">
            {chips.map((c) => (
              <span className="graph-chip" key={c}>
                {c}
                <button type="button" onClick={clearHighlight} title="전체 복원">
                  ✕
                </button>
              </span>
            ))}
          </div>
        )}
        {chips.some((c) => c.startsWith("lineage=") || c.includes("계보")) && (
          <div className="graph-lineage-key">
            <span>
              <i style={{ background: "#2563eb" }} /> 조상
            </span>
            <span>
              <i style={{ background: "#d97706" }} /> 자손
            </span>
            <span>
              <i style={{ background: "#111827" }} /> 기준
            </span>
          </div>
        )}
        <form className="graph-search" onSubmit={runSearch}>
          <input
            placeholder="노드 검색 (예: RLHF)…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {searchMsg && <div className="muted">{searchMsg}</div>}
          {matches.length > 1 && (
            <div className="match-list">
              {matches.map((m, i) => (
                <button
                  type="button"
                  key={m.id}
                  className={i === matchIdx ? "active" : ""}
                  onClick={() => goTo(m.id, matches, i)}
                >
                  {m.canonical}
                </button>
              ))}
            </div>
          )}
        </form>
        <div className="graph-controls">
          <select
            value={filterState.ptype || ""}
            onChange={(e) =>
              setFilter({ ...filterState, ptype: e.target.value || undefined })
            }
            title="유형으로 필터"
          >
            <option value="">유형 전체</option>
            {ptypeOpts.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <select
            value={filterState.domain || ""}
            onChange={(e) =>
              setFilter({ ...filterState, domain: e.target.value || undefined })
            }
            title="분야로 필터"
          >
            <option value="">분야 전체</option>
            {domainOpts.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
          <select
            value={filterState.date_after || ""}
            onChange={(e) =>
              setFilter({ ...filterState, date_after: e.target.value || undefined })
            }
            title="시점으로 필터"
          >
            <option value="">시점 전체</option>
            {yearOpts.map((y) => (
              <option key={y} value={`${y}-01`}>
                {y} 이후
              </option>
            ))}
          </select>
          <label
            className="graph-controls-toggle"
            title="검토함 표시한 개념은 숨김(나에게 새로운 것만)"
          >
            <input
              type="checkbox"
              checked={!!filterState.unreviewed_only}
              onChange={(e) =>
                setFilter({
                  ...filterState,
                  unreviewed_only: e.target.checked || undefined,
                })
              }
            />
            안 본 것만
          </label>
          <button
            className="graph-controls-reset"
            onClick={() => setFilter({})}
            title="필터·강조 초기화"
          >
            초기화
          </button>
          <label className="graph-controls-toggle" title="논문 노드도 함께 표시">
            <input
              type="checkbox"
              checked={showPapers}
              onChange={(e) => setShowPapers(e.target.checked)}
            />
            논문 보기
          </label>
        </div>
        <div className="graph-legend">
          <div>
            <span className="dot" style={{ background: TYPE_COLOR.technique }} />
            technique
          </div>
          <div>
            <span className="dot" style={{ background: TYPE_COLOR.benchmark }} />
            benchmark
          </div>
          <div>
            <span className="dot" style={{ background: TYPE_COLOR.analysis }} />
            analysis
          </div>
          <div>
            <span className="dot" style={{ background: TYPE_COLOR.survey }} />
            survey
          </div>
          <div style={{ marginTop: 3 }}>
            <span
              className="dot"
              style={{ background: "#fff", border: "2px dashed #64748b" }}
            />
            빈 원(점선) = 정의 없음
          </div>
        </div>
        {error && (
          <div className="graph-panel">
            <div className="toast err">{error}</div>
          </div>
        )}
        {!error && selected && (
          <div className="graph-panel">
            <button
              className="detail-close"
              title="닫기"
              onClick={() => setSelected(null)}
            >
              ✕
            </button>
            {selected.type === "paper" ? (
              <>
                <h3>{selected.title}</h3>
                <div className="detail-meta">
                  <span
                    className="type-badge"
                    style={{ background: TYPE_COLOR[selected.paper_type] || "#888" }}
                  >
                    {selected.paper_type}
                  </span>
                  {selected.domain && selected.domain !== "general" && (
                    <span className="muted">domain: {selected.domain}</span>
                  )}
                </div>
                <div className="detail-def">
                  {selected.problem || "문제 설명 없음"}
                </div>
                <div className="muted detail-papers">
                  논문:{" "}
                  <a
                    href={`https://arxiv.org/abs/${selected.id.replace("paper:", "")}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {selected.id.replace("paper:", "")}
                  </a>
                </div>
              </>
            ) : (
              <>
                <h3>{selected.canonical}</h3>
                <div className="detail-meta">
                  <span
                    className="type-badge"
                    style={{ background: TYPE_COLOR[selected.ptype] || "#888" }}
                  >
                    {selected.ptype}
                  </span>
                  {selected.domain && selected.domain !== "general" && (
                    <span className="muted">domain: {selected.domain}</span>
                  )}
                </div>
                <label className="detail-reviewed">
                  <input
                    type="checkbox"
                    checked={!!selected.reviewed}
                    onChange={async (e) => {
                      const v = e.target.checked;
                      await postReviewed(selected.id, v);
                      dataRef.current.nodes[selected.id].reviewed = v; // 즉시 반영(필터·검색용)
                      setSelected({ ...selected, reviewed: v });
                    }}
                  />
                  검토함 (이미 아는 기법)
                </label>
                <div className="detail-lineage">
                  <span className="muted">계보</span>
                  <button onClick={() => runLineageFromNode(selected.id, "ancestors")}>
                    조상
                  </button>
                  <button onClick={() => runLineageFromNode(selected.id, "descendants")}>
                    자손
                  </button>
                  <button onClick={() => runLineageFromNode(selected.id, "both")}>
                    양쪽
                  </button>
                </div>
                <div className="detail-def">
                  {selected.definition ||
                    (selected.def_status === "placeholder"
                      ? "정의 없음 — 원논문 미수록"
                      : "정의 없음")}
                </div>
                <div className="muted detail-papers">
                  등장 {selected.papers.length}편:{" "}
                  {selected.papers.map((p, i) => (
                    <span key={p}>
                      {i > 0 ? ", " : ""}
                      <a
                        href={`https://arxiv.org/abs/${p}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {p}
                      </a>
                    </span>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {collapsed ? (
        <button
          className="chat-toggle collapsed"
          onClick={() => setCollapsed(false)}
          title="채팅 열기"
        >
          {"<"}
        </button>
      ) : (
        <>
        <div
          className={`pane-divider${dragging ? " dragging" : ""}`}
          onMouseDown={onDividerDown}
          title="드래그로 채팅 폭 조절"
        />
        <div className="chat-panel" style={{ "--chat-width": `${chatWidth}px` }}>
          <div className="chat-head">
            <button
              className="chat-toggle"
              onClick={() => setCollapsed(true)}
              title="채팅 접기"
            >
              {">"}
            </button>
            <div className="chat-tabs">
              <button
                className={`chat-tab${activeTab === "command" ? " active" : ""}`}
                onClick={() => setActiveTab("command")}
              >
                명령
              </button>
              <button
                className={`chat-tab${activeTab === "collect" ? " active" : ""}`}
                onClick={() => setActiveTab("collect")}
              >
                수집
                {collect && activeTab !== "collect" && <span className="tab-dot">●</span>}
              </button>
            </div>
            <button
              className="chat-clear"
              onClick={clearActiveChat}
              disabled={activeTab === "collect" && !!collect}
              title={
                activeTab === "collect" && collect
                  ? "수집 진행 중엔 비울 수 없어요"
                  : "대화 비우기"
              }
            >
              비우기
            </button>
          </div>
          <div className="chat-msgs">
            {activeTab === "command" ? (
              <>
                {messages.length === 0 && (
                  <div className="chat-examples">
                    <div className="muted chat-hint">예시 — 눌러서 실행:</div>
                    {[
                      "벤치마크만 보여줘",
                      "RAG 계보만 보여줘",
                      "검색하면서 추론하는 방법 있어?",
                      "다 보여줘",
                    ].map((ex) => (
                      <button
                        type="button"
                        key={ex}
                        className="example-chip"
                        onClick={() => runCommand(ex)}
                        disabled={pending}
                      >
                        {ex}
                      </button>
                    ))}
                  </div>
                )}
                {messages.map((m, i) => (
                  <div key={i} className={`chat-bubble ${m.role}`}>
                    {m.text}
                  </div>
                ))}
                {pending && <div className="chat-bubble agent">…</div>}
              </>
            ) : (
              <>
                {collectMessages.length === 0 && !collect && (
                  <div className="chat-examples">
                    <div className="muted chat-hint">
                      arXiv에서 새 논문을 수집해 지도에 추가합니다. 주제를 입력하세요.
                    </div>
                  </div>
                )}
                {collectMessages.map((m, i) => (
                  <div key={i} className={`chat-bubble ${m.role}`}>
                    {m.text}
                  </div>
                ))}
                {collect && <CollectCard
                  collect={collect}
                  onResume={resumeCollect}
                  reviseOpen={reviseOpen}
                  setReviseOpen={setReviseOpen}
                  reviseText={reviseText}
                  setReviseText={setReviseText}
                />}
              </>
            )}
            <div ref={msgEndRef} />
          </div>
          {activeTab === "command" ? (
            <form className="chat-input" onSubmit={sendCommand}>
              <input
                placeholder="명령을 입력…"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                disabled={pending}
              />
              <button type="submit" disabled={pending}>
                전송
              </button>
            </form>
          ) : (
            <form className="chat-input" onSubmit={sendCollect}>
              <input
                placeholder={collect ? "수집 흐름 중 — 카드 버튼으로 응답하세요" : "수집할 주제를 입력…"}
                value={collectInput}
                onChange={(e) => setCollectInput(e.target.value)}
                disabled={!!collect}
              />
              <button type="submit" disabled={!!collect}>
                시작
              </button>
            </form>
          )}
        </div>
        </>
      )}
    </div>
  );
}

const STAGE_LABELS = {
  interpret: "해석 확인",
  approve: "물량 승인",
  extract_confirm: "추출 승인",
};
const stageLabel = (stage) => STAGE_LABELS[stage] || "수집";

// 수집 흐름 interrupt 카드 — stage별 버튼. resume은 onResume(decision)로.
function CollectCard({ collect, onResume, reviseOpen, setReviseOpen, reviseText, setReviseText }) {
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

function render(container, svgEl, data, setSelected, onSettled) {
  const W = container.clientWidth;
  const H = container.clientHeight;
  const isPaper = (d) => d.type === "paper";
  const radius = (d) => (isPaper(d) ? 6 : 12);
  const fill = (d) =>
    isPaper(d)
      ? "#9ca3af"
      : d.def_status === "placeholder"
      ? "#ffffff"
      : TYPE_COLOR[d.ptype] || "#2563eb";
  const stroke = (d) => (isPaper(d) ? "#6b7280" : TYPE_COLOR[d.ptype] || "#2563eb");
  const dash = (d) =>
    !isPaper(d) && d.def_status === "placeholder" ? "3 2" : null;

  // normalized_v2 변환본(객체 nodes + builds_on[, defines]) → d3 배열 형태로 변환
  const nodes = Object.entries(data.nodes).map(([id, n]) => ({ id, ...n }));
  const nodeIds = new Set(nodes.map((n) => n.id));
  const links = data.builds_on
    .filter((b) => nodeIds.has(b.from) && nodeIds.has(b.to))
    .map((b) => ({
      source: b.from,
      target: b.to,
      kind: "builds_on",
      from_type: data.nodes[b.from].ptype || "technique",
    }));
  // 논문 보기 ON: 논문→개념 엣지(defines, 그리고 정의없는 논문의 builds_on)를 옅은 점선으로 추가
  for (const key of ["defines", "paper_builds_on"]) {
    if (!data[key]) continue;
    for (const e of data[key]) {
      if (nodeIds.has(e.from) && nodeIds.has(e.to))
        links.push({ source: e.from, target: e.to, kind: key });
    }
  }

  const svg = d3.select(svgEl).attr("width", W).attr("height", H);
  svg.selectAll("*").remove();

  // 화살표 마커(ptype별)
  const defs = svg.append("defs");
  for (const [type, color] of Object.entries(TYPE_COLOR)) {
    defs
      .append("marker")
      .attr("id", `arr-${type}`)
      .attr("markerWidth", 10)
      .attr("markerHeight", 10)
      .attr("refX", 20)
      .attr("refY", 3)
      .attr("orient", "auto")
      .attr("markerUnits", "strokeWidth")
      .append("path")
      .attr("d", "M0,0L0,6L9,3z")
      .attr("fill", color);
  }

  const root = svg.append("g");
  // 줌 아웃 시 라벨 숨김(겹침 방지) — 가까이 볼 때만 텍스트 표시
  const zoom = d3.zoom().on("zoom", (e) => {
    root.attr("transform", e.transform);
    node.selectAll("text").attr("opacity", e.transform.k < 0.6 ? 0 : 1);
  });
  svg.call(zoom);

  const link = root
    .append("g")
    .selectAll("line")
    .data(links)
    .join("line")
    // 개념↔개념 builds_on은 색 실선+화살표, 논문→개념(defines·paper_builds_on)은 옅은 점선
    .attr("stroke", (d) =>
      d.kind === "builds_on" ? TYPE_COLOR[d.from_type] || "#888" : "#cbd5e1"
    )
    .attr("stroke-width", (d) => (d.kind === "builds_on" ? 1.4 : 1))
    .attr("stroke-opacity", (d) => (d.kind === "builds_on" ? 0.42 : 0.4))
    .attr("stroke-dasharray", (d) => (d.kind === "builds_on" ? null : "2 3"))
    .attr("marker-end", (d) =>
      d.kind === "builds_on" ? `url(#arr-${d.from_type || "technique"})` : null
    );

  const node = root
    .append("g")
    .selectAll("g")
    .data(nodes)
    .join("g")
    .call(
      d3
        .drag()
        .on("start", (e, d) => {
          if (!e.active) sim.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on("drag", (e, d) => {
          d.fx = e.x;
          d.fy = e.y;
        })
        .on("end", (e, d) => {
          if (!e.active) sim.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
    );

  node
    .append("circle")
    .attr("r", radius)
    .attr("fill", fill)
    .attr("stroke", stroke)
    .attr("stroke-width", (d) => (isPaper(d) ? 1.5 : 2.5))
    .attr("stroke-dasharray", dash)
    .on("click", (e, d) => setSelected(d));

  node
    .append("text")
    .text((d) => (isPaper(d) ? "" : d.canonical)) // 논문 노드는 라벨 없이(점만)
    .attr("x", 16)
    .attr("y", 4);

  const sim = d3
    .forceSimulation(nodes)
    .alphaDecay(0.05) // 기본(0.0228)보다 빠르게 안정 → 로드 후 빠른 자동 맞춤
    .force(
      "link",
      d3
        .forceLink(links)
        .id((d) => d.id)
        .distance(160)
        .strength(0.3)
    )
    .force("charge", d3.forceManyBody().strength(-900))
    .force("center", d3.forceCenter(W / 2, H / 2))
    .force("collide", d3.forceCollide(30))
    .on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);
      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

  // 전체 노드가 화면에 들어오도록 줌 자동 맞춤(라벨 여백 고려해 우측 패딩 더 줌)
  function fitView(animate = true) {
    if (!nodes.length) return;
    const xs = nodes.map((n) => n.x);
    const ys = nodes.map((n) => n.y);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const w = container.clientWidth;
    const h = container.clientHeight;
    const gw = maxX - minX || 1;
    const gh = maxY - minY || 1;
    const padX = 160; // 라벨이 노드 오른쪽으로 뻗으므로 가로 여백 넉넉히
    const padY = 90;
    const k = Math.min((w - padX) / gw, (h - padY) / gh, 1.6);
    const cx = (minX + maxX) / 2;
    const cy = (minY + maxY) / 2;
    const t = d3.zoomIdentity
      .translate(w / 2 - k * cx, h / 2 - k * cy)
      .scale(k);
    (animate ? svg.transition().duration(500) : svg).call(zoom.transform, t);
  }

  // 초기 시뮬레이션이 안정되면(약 2초) 전체가 보이도록 자동 맞춤 + onSettled로 노출 신호.
  // 드래그 후 재안정 때는 재맞춤하지 않음(사용자 시점 보존).
  let didFit = false;
  sim.on("end", () => {
    if (didFit) return;
    didFit = true;
    fitView(false); // 즉시 맞춤(애니메이션 없이) — 노출 직전이라 부드럽게
    onSettled && onSettled();
  });
  // 안전장치: 혹시 end가 안 와도 일정 시간 뒤 노출(무한 로딩 방지)
  setTimeout(() => {
    if (!didFit) {
      didFit = true;
      fitView(false);
    }
    onSettled && onSettled();
  }, 4000);

  // 검색→포커스: 노드를 화면 중앙으로 이동(transition)하고 강조
  const nodeById = new Map(nodes.map((n) => [n.id, n]));
  function focus(id) {
    const d = nodeById.get(id);
    if (!d) return;
    const w = container.clientWidth;
    const h = container.clientHeight;
    const k = 1.5; // 적당한 확대
    const t = d3.zoomIdentity
      .translate(w / 2 - k * d.x, h / 2 - k * d.y)
      .scale(k);
    svg.transition().duration(500).call(zoom.transform, t);
    node
      .select("circle")
      .attr("stroke-width", (c) =>
        c.id === id ? 5 : isPaper(c) ? 1.5 : 2.5
      )
      .attr("r", (c) => (c.id === id ? 18 : radius(c)));
    setSelected(d); // 사이드 패널도 갱신
  }

  // 원의 테두리/크기를 기본값으로 복원(계보 강조 후 일반 강조로 돌아올 때).
  function resetStrokes() {
    node
      .select("circle")
      .attr("stroke", (d) => stroke(d))
      .attr("stroke-width", (d) => (isPaper(d) ? 1.5 : 2.5))
      .attr("r", (d) => radius(d));
  }

  // 강조/흐리게: 매칭 노드 opacity 1, 비매칭은 흐리게(숨기지 않음).
  // 엣지는 양 끝 모두 매칭일 때만 표시, 아니면 완전 숨김(화살촉 포함).
  // ids === null → 전체 복원.
  function highlight(ids) {
    resetStrokes();
    if (!ids) {
      node.attr("opacity", 1);
      link.style("display", null).attr("stroke-opacity", 0.42);
      return;
    }
    node.attr("opacity", (d) => (ids.has(d.id) ? 1 : 0.18));
    link.style("display", (d) =>
      ids.has(d.source.id) && ids.has(d.target.id) ? null : "none"
    );
  }

  // 계보 강조: 조상=파랑 테두리·자손=주황 테두리·시작 노드=강조(크게). 방향에 따라 한쪽은 빈 집합.
  function highlightLineage(start, ancestors, descendants) {
    const all = new Set([start, ...ancestors, ...descendants]);
    node.attr("opacity", (d) => (all.has(d.id) ? 1 : 0.12));
    node
      .select("circle")
      .attr("stroke", (d) =>
        d.id === start
          ? "#111827"
          : ancestors.has(d.id)
          ? "#2563eb"
          : descendants.has(d.id)
          ? "#d97706"
          : stroke(d)
      )
      .attr("stroke-width", (d) =>
        d.id === start ? 5 : all.has(d.id) ? 3.4 : isPaper(d) ? 1.5 : 2.5
      )
      .attr("r", (d) => (d.id === start ? 16 : radius(d)));
    link.style("display", (d) =>
      all.has(d.source.id) && all.has(d.target.id) ? null : "none"
    );
  }

  // 컨테이너 크기 변화 시 svg/force 갱신
  function resize() {
    const w = container.clientWidth;
    const h = container.clientHeight;
    if (!w || !h) return;
    svg.attr("width", w).attr("height", h);
    sim.force("center", d3.forceCenter(w / 2, h / 2));
    sim.alpha(0.2).restart();
  }

  // 검색 대상은 개념만(논문 노드 제외)
  const names = nodes
    .filter((n) => !isPaper(n))
    .map((n) => ({ id: n.id, canonical: n.canonical }));
  return { sim, focus, names, highlight, highlightLineage, resize, fitView };
}
