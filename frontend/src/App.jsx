import { Link, NavLink, Navigate, Route, Routes } from "react-router-dom";
import Graph from "./routes/Graph.jsx";
import Lexicon from "./routes/Lexicon.jsx";
import Usage from "./routes/Usage.jsx";

export default function App() {
  return (
    <>
      <nav className="nav">
        <Link to="/usage" className="brand" title="사용법으로">
          <svg
            className="brand-mark"
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
          >
            <line x1="6" y1="8" x2="18" y2="6.5" />
            <line x1="6" y1="8" x2="12" y2="18" />
            <line x1="18" y1="6.5" x2="12" y2="18" />
            <circle cx="6" cy="8" r="2.3" />
            <circle cx="18" cy="6.5" r="2.3" />
            <circle cx="12" cy="18" r="3" className="brand-node-accent" />
          </svg>
          <span className="brand-word">
            <span className="b-r">Research</span>
            <span className="b-a">Atlas</span>
          </span>
        </Link>
        <NavLink to="/usage">사용법</NavLink>
        <NavLink to="/graph">지형도</NavLink>
        <NavLink to="/lexicon">사전</NavLink>
      </nav>
      <Routes>
        <Route path="/" element={<Navigate to="/usage" replace />} />
        <Route path="/usage" element={<Usage />} />
        <Route path="/graph" element={<Graph />} />
        <Route path="/lexicon" element={<Lexicon />} />
      </Routes>
    </>
  );
}
