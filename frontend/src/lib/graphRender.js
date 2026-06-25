// 지형도 D3 force 렌더러. React state와 무관한 순수 D3.
// render(container, svgEl, data, setSelected, onSettled)
//   → {sim, focus, names, highlight, highlightLineage, resize, fitView}
import * as d3 from "d3";
import { TYPE_COLOR } from "./graphHelpers.js";

export function render(container, svgEl, data, setSelected, onSettled) {
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
    node.selectAll("text").attr("opacity", e.transform.k < 0.7 ? 0 : 1);
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
