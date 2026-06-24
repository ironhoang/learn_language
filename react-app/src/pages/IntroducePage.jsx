import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import HomeBtn from '../components/HomeBtn';
import PlayerBar from '../components/PlayerBar';
import AudioBtn from '../components/AudioBtn';

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

function CopyBtn({ text }) {
  const [copied, setCopied] = useState(false);
  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    });
  }
  return (
    <button className={`copy-btn${copied ? ' copied' : ''}`} onClick={handleCopy}>
      {copied ? '✓ Copied' : '📋 Copy'}
    </button>
  );
}

function AnswerCard({ ans }) {
  return (
    <div className="intro-card">
      <div className="card-question">
        <div className="q-label">Họ sẽ hỏi</div>
        <div className="q-zh">
          {ans.questionZh}
          <AudioBtn src={ans.questionZhAudio} />
        </div>
        {ans.questionVi && <div className="q-vi">{ans.questionVi}</div>}
      </div>

      <div className="card-answer">
        {/* Chinese answer */}
        <div className="lang-block zh-block">
          <div className="lang-header zh-h">
            <span className="lang-tag zh">中文</span>
            <CopyBtn text={ans.answerZh} />
          </div>
          <div className="lang-body">
            <div className="a-zh">
              {ans.answerZh}
              <AudioBtn src={ans.answerZhAudio} />
            </div>
            {ans.pinyin && <div className="a-pinyin">{ans.pinyin}</div>}
          </div>
        </div>

        {/* English answer */}
        <div className="lang-block en-block">
          <div className="lang-header en-h">
            <span className="lang-tag en">English</span>
            <CopyBtn text={ans.answerEn} />
          </div>
          <div className="lang-body">
            <div className="a-en">
              {ans.answerEn}
              <AudioBtn src={ans.answerEnAudio} />
            </div>
          </div>
        </div>

        {ans.note && <div className="a-vi">{ans.note}</div>}

        {ans.keywords && ans.keywords.length > 0 && (
          <div className="keywords">
            {ans.keywords.map((kw, i) => <span key={i} className="kw">{kw}</span>)}
          </div>
        )}
      </div>
    </div>
  );
}

export default function IntroducePage() {
  const { setId } = useParams();
  const data = usePageData(`episoden-introduce-${setId}`);

  if (!data) return <div className="loading">Đang tải…</div>;
  const { meta, answers } = data;

  return (
    <div className="inner-page">
      <HomeBtn />
      <header>
        <h1>{meta.title}</h1>
        {meta.sub && <div style={{ marginTop: 6, fontSize: '0.8rem', color: '#475569' }}>{meta.sub}</div>}
      </header>
      <div className="cards">
        {answers.map(ans => <AnswerCard key={ans.id} ans={ans} />)}
      </div>
      <PlayerBar />
    </div>
  );
}
