import { useEffect, useState } from "react";
import StudyList from "./components/StudyList";
import StudyView from "./components/StudyView";

/** Tiny hash router: "#/" -> list, "#/study/<sid>" -> viewer. */
function useRoute() {
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const on = () => setHash(window.location.hash);
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  const m = hash.match(/^#\/study\/(.+)$/);
  return m ? { name: "study" as const, sid: decodeURIComponent(m[1]) } : { name: "list" as const };
}

export default function App() {
  const route = useRoute();
  return (
    <div className="app">
      <header className="topbar">
        <a className="brand" href="#/">
          <span className="brand-mark">PK</span>
          <span className="brand-text">
            PK-DB <em>Viewer</em>
          </span>
        </a>
        <div className="topbar-sub">
          paper &nbsp;·&nbsp; extracted data, side&nbsp;by&nbsp;side
        </div>
      </header>
      {route.name === "list" ? <StudyList /> : <StudyView sid={route.sid} />}
    </div>
  );
}
