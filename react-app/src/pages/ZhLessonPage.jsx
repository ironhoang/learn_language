import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import HomeBtn from '../components/HomeBtn';
import AudioBtn from '../components/AudioBtn';
import PlayerBar from '../components/PlayerBar';

export default function ZhLessonPage() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [step, setStep] = useState(0);

  useEffect(() => {
    setData(null);
    setStep(0);
    fetch(`/data/zh-lesson-${id}.json`)
      .then(r => r.json())
      .then(setData)
      .catch(console.error);
  }, [id]);

  if (!data) return <div className="loading">Đang tải…</div>;

  const { meta, paragraphs } = data;
  const total = paragraphs.length;
  const para = paragraphs[step];

  return (
    <div className="inner-page">
      <HomeBtn />
      <header>
        <h1>{meta.title_vi} · {meta.title_zh}</h1>
        <div className="timer-badge">{meta.level}</div>
      </header>

      <div className="cards">
        <div className="q-card" key={para.id}>
          <div className="card-main">
            <div className="num">{step + 1}</div>
            <div className="card-body zl-sentences">
              {para.sentences.map(s => (
                <div key={s.id} className="zl-sentence">
                  <div className="zh">
                    {s.zh}
                    <AudioBtn src={s.audio} />
                  </div>
                  <div className="pinyin">{s.pinyin}</div>
                  <div className="zl-phrases">
                    {s.phrases.map(p => (
                      <span key={p.id} className="zl-phrase-chip">
                        {p.text}
                        <AudioBtn src={p.audio} />
                      </span>
                    ))}
                  </div>
                  <div className="a-vi">{s.vi}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="zl-step-nav">
        <button className="pa-btn" disabled={step === 0} onClick={() => setStep(s => s - 1)}>
          ← Đoạn trước
        </button>
        <span className="zl-step-status">Đoạn {step + 1} / {total}</span>
        <button className="pa-btn" disabled={step === total - 1} onClick={() => setStep(s => s + 1)}>
          Đoạn tiếp →
        </button>
      </div>

      <PlayerBar />
    </div>
  );
}
