import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import HomeBtn from '../components/HomeBtn';
import PlayerBar from '../components/PlayerBar';
import AudioBtn from '../components/AudioBtn';

// dataKey: 'episoden-ask-1', 'episoden-ask-2', 'jobs-teacher', etc.
function usePageData(dataKey) {
  const [data, setData] = useState(null);
  useEffect(() => {
    setData(null);
    fetch(`/data/${dataKey}.json`)
      .then(r => r.json())
      .then(setData)
      .catch(console.error);
  }, [dataKey]);
  return data;
}

function VocabChip({ chip }) {
  return (
    <div className="vocab-chip">
      {chip.zh}
      <span className="py">{chip.py}</span>
      <span className="vn">{chip.vn}</span>
      {chip.zhAudio && <AudioBtn src={chip.zhAudio} />}
      {chip.ve && (
        <span className="ve">
          {chip.ve}
          {chip.veAudio && <AudioBtn src={chip.veAudio} />}
        </span>
      )}
    </div>
  );
}

function QuestionCard({ q }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="q-card">
      <div className="card-main">
        <div className="num">{q.id}</div>
        <div className="card-body">
          <div className="zh">
            {q.zh}
            <AudioBtn src={q.zhAudio} />
          </div>
          {q.pinyin && <div className="pinyin">{q.pinyin}</div>}
          <div className="en">
            {q.en}
            <AudioBtn src={q.enAudio} />
          </div>
        </div>
      </div>

      {(q.vocab.length > 0 || q.followup.length > 0) && (
        <>
          <button
            className={`toggle-btn${open ? ' open' : ''}`}
            onClick={() => setOpen(v => !v)}
          >
            Gợi ý <span className="arrow">▼</span>
          </button>
          <div className={`hint-panel${open ? ' open' : ''}`}>
            {q.vocab.length > 0 && (
              <div className="hint-section">
                <div className="hint-label vocab">Từ cần nghe</div>
                <div className="vocab-list">
                  {q.vocab.map((chip, i) => <VocabChip key={i} chip={chip} />)}
                </div>
              </div>
            )}
            {q.followup.length > 0 && (
              <div className="hint-section">
                <div className="hint-label followup">Hỏi tiếp</div>
                <div className="followup-list">
                  {q.followup.map((fu, i) => (
                    <div key={i} className="followup-item">
                      <div className="fq-zh">
                        {fu.zh}<AudioBtn src={fu.zhAudio} />
                      </div>
                      <div className="fq-en">
                        {fu.en}<AudioBtn src={fu.enAudio} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

// ── Ask page (episoden sets) ─────────────────────────────────────────────────

export function AskPage() {
  const { setId } = useParams();
  const data = usePageData(`episoden-ask-${setId}`);

  if (!data) return <div className="loading">Đang tải…</div>;
  const { meta, questions } = data;

  return (
    <div className="inner-page">
      <HomeBtn />
      <header>
        <h1>{meta.title}</h1>
        <div className="timer-badge">{meta.timerBadge}</div>
        {meta.setBadge && <span className="set-badge">{meta.setBadge}</span>}
      </header>
      <div className="cards">
        {questions.map(q => <QuestionCard key={q.id} q={q} />)}
      </div>
      <PlayerBar />
    </div>
  );
}

// ── Job page (uses same card structure) ────────────────────────────────────

export function JobPage() {
  const { jobId } = useParams();
  const data = usePageData(`jobs-${jobId}`);

  if (!data) return <div className="loading">Đang tải…</div>;
  const { meta, questions } = data;

  return (
    <div className="inner-page">
      <HomeBtn />
      <header>
        <h1>{meta.title}</h1>
        {meta.jobBadge && <div className="job-badge">{meta.jobBadge}</div>}
        <div className="timer-badge">{meta.timerBadge}</div>
      </header>
      <div className="cards">
        {questions.map(q => <QuestionCard key={q.id} q={q} />)}
      </div>
      <PlayerBar />
    </div>
  );
}
