import { useEffect, useState, useRef, useCallback } from 'react';
import HomeBtn from '../components/HomeBtn';
import PlayerBar from '../components/PlayerBar';
import AudioBtn from '../components/AudioBtn';

const KO_MODES = {
  all: { idle: '▶ Tất cả', running: '⏸ Tất cả', selector: '.audio-btn[data-src]' },
  ko:  { idle: '▶ 한국어', running: '⏸ 한국어', selector: '.ko .audio-btn[data-src]' },
  vn:  { idle: '▶ Tiếng Việt', running: '⏸ VN',  selector: '.ko-vn .audio-btn[data-src]' },
};

function KoCard({ item }) {
  return (
    <div className="ko-card">
      <div className="card-main">
        <div className="card-body">
          <div className="ko">
            {item.ko}
            <AudioBtn src={item.koAudio} />
          </div>
          {item.romaja && <div className="romaja">{item.romaja}</div>}
          <div className="ko-vn">
            {item.vn}
            <AudioBtn src={item.vnAudio} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function WithKidPage() {
  const [data, setData] = useState(null);
  const [collapsedSections, setCollapsedSections] = useState(new Set());
  const cardRefs = useRef({});
  const dataRef = useRef(null);

  useEffect(() => {
    fetch('/data/han-with-kid.json')
      .then(r => r.json())
      .then(d => { dataRef.current = d; setData(d); })
      .catch(console.error);
  }, []);

  const handlePlay = useCallback((src) => {
    const d = dataRef.current;
    if (!d || !src) return;

    for (let si = 0; si < d.sections.length; si++) {
      const items = d.sections[si].items;
      for (let ii = 0; ii < items.length; ii++) {
        const item = items[ii];
        if (item.koAudio !== src && item.vnAudio !== src) continue;

        const el = cardRefs.current[`${si}-${ii}`];
        if (el) {
          // Expand tất cả card trong section trực tiếp qua DOM (không chờ React)
          const sectionDiv = el.parentElement;
          if (sectionDiv) {
            Array.from(sectionDiv.children).forEach(child => {
              if (!child.classList.contains('ko-section-label')) {
                child.style.removeProperty('display');
              }
            });
          }
          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        // Đồng bộ React state (cho section label icon)
        setCollapsedSections(prev => {
          if (!prev.has(si)) return prev;
          const next = new Set(prev);
          next.delete(si);
          return next;
        });
        return;
      }
    }
  }, []);

  function toggleSection(si) {
    setCollapsedSections(prev => {
      const next = new Set(prev);
      if (next.has(si)) next.delete(si);
      else next.add(si);
      return next;
    });
  }

  if (!data) return <div className="loading">Đang tải…</div>;
  const { meta, sections } = data;

  return (
    <div className="inner-page">
      <HomeBtn />
      <header>
        <h1>{meta.title}</h1>
        <div className="timer-badge">{meta.badge}</div>
      </header>
      <div className="cards">
        {sections.map((sec, si) => (
          <div key={si}>
            {sec.label && (
              <div
                className={`ko-section-label${collapsedSections.has(si) ? ' collapsed' : ''}`}
                onClick={() => toggleSection(si)}
              >
                {sec.label}
              </div>
            )}
            {sec.items.map((item, ii) => (
              <div
                key={ii}
                ref={el => { cardRefs.current[`${si}-${ii}`] = el; }}
                style={collapsedSections.has(si) ? { display: 'none' } : undefined}
              >
                <KoCard item={item} />
              </div>
            ))}
          </div>
        ))}
      </div>
      <PlayerBar extraModes={KO_MODES} onPlay={handlePlay} />
    </div>
  );
}
