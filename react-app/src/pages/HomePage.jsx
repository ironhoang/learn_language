import { Link } from 'react-router-dom';

const EPISODEN = [
  {
    setLabel: 'Set 1 — Giới thiệu cơ bản',
    cards: [
      {
        to: '/episoden/ask/1',
        icon: '🎯',
        type: 'ask',
        typeLabel: 'Câu hỏi',
        title: 'Ask Set 1',
        desc: '10 câu hỏi: tên, quê, nghề, sở thích, hôn nhân, đồ ăn, giải trí, ngôn ngữ, Việt Nam',
      },
      {
        to: '/episoden/introduce/1',
        icon: '💬',
        type: 'intro',
        typeLabel: 'Câu trả lời',
        title: 'Introduce Set 1',
        desc: '10 câu trả lời sẵn bằng 中文 + English, có copy button',
      },
    ],
  },
  {
    setLabel: 'Set 2 — Đời sống & suy nghĩ',
    cards: [
      {
        to: '/episoden/ask/2',
        icon: '🎯',
        type: 'ask',
        typeLabel: 'Câu hỏi',
        title: 'Ask Set 2',
        desc: '10 câu hỏi: anh chị em, phim, học ngôn ngữ, thú cưng, giờ giấc, du lịch, nhạc, bận gì',
      },
      {
        to: '/episoden/introduce/2',
        icon: '💬',
        type: 'intro',
        typeLabel: 'Câu trả lời',
        title: 'Introduce Set 2',
        desc: '10 câu trả lời sẵn bằng 中文 + English, có copy button',
      },
    ],
  },
];

const JOBS = [
  { to: '/jobs/teacher',      icon: '👩‍🏫', title: 'Giáo viên / 教师',        desc: '8 câu hỏi về dạy học, học sinh, áp lực nghề giáo' },
  { to: '/jobs/engineer',     icon: '👨‍💻', title: 'Kỹ sư / 工程师',          desc: '8 câu hỏi về lập trình, công ty, AI, làm thêm giờ' },
  { to: '/jobs/student',      icon: '📚', title: 'Sinh viên / 学生',          desc: '8 câu hỏi về trường, chuyên ngành, cuộc sống sinh viên' },
  { to: '/jobs/doctor',       icon: '🏥', title: 'Bác sĩ / 医生',            desc: '8 câu hỏi về khoa, ca trực, áp lực y tế, bệnh nhân' },
  { to: '/jobs/office-worker',icon: '💼', title: 'Nhân viên VP / 上班族',     desc: '8 câu hỏi về ngành, đi làm, đồng nghiệp, nhảy việc' },
  { to: '/jobs/business',     icon: '🏢', title: 'Chủ doanh nghiệp / 老板',  desc: '8 câu hỏi về khởi nghiệp, nhân viên, áp lực kinh doanh' },
  { to: '/jobs/chef',         icon: '👨‍🍳', title: 'Đầu bếp / 厨师',          desc: '8 câu hỏi về ẩm thực, giờ làm, món đặc trưng, bếp' },
  { to: '/jobs/sales',        icon: '📊', title: 'Sales / Marketing / 销售', desc: '8 câu hỏi về KPI, khách hàng, chốt đơn, online vs offline' },
  { to: '/jobs/civil-servant',icon: '🏛️', title: 'Công chức / 公务员',       desc: '8 câu hỏi về thi công chức, phúc lợi, sự ổn định' },
  { to: '/jobs/freelancer',   icon: '🎯', title: 'Freelancer / 自由职业者',   desc: '8 câu hỏi về thu nhập, tự do, tìm khách, tự kỷ luật' },
];

const HAN = [
  { to: '/han/with-kid', icon: '👶', title: 'Tiếng Hàn cùng con', desc: '40 câu cho bé 2 tuổi: chào hỏi, sinh hoạt, ăn uống, vui chơi' },
];

export default function HomePage() {
  return (
    <div className="home-page">
      <header>
        <div className="logo">Learn <span>EN</span> + 中文</div>
        <div className="tagline">Chuẩn bị cho cuộc trò chuyện 7 phút với người lạ</div>
      </header>

      <div className="home-content">
        <div className="timer-row">
          <div className="timer-icon">⏱</div>
          <div className="timer-text">
            Mỗi cuộc trò chuyện <strong>7 phút</strong>. Dùng <strong>Ask</strong> để hỏi đối phương,
            dùng <strong>Introduce</strong> để trả lời khi họ hỏi lại.
          </div>
        </div>

        {/* Episoden */}
        <div>
          <div className="section-header"><h2>Episoden</h2></div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            {EPISODEN.map(set => (
              <div key={set.setLabel} className="set-group">
                <div className="set-title">{set.setLabel}</div>
                <div className="set-cards">
                  {set.cards.map(c => (
                    <Link key={c.to} className="nav-card" to={c.to}>
                      <div className="card-icon">{c.icon}</div>
                      <div className={`card-type ${c.type}`}>{c.typeLabel}</div>
                      <div className="card-title">{c.title}</div>
                      <div className="card-desc">{c.desc}</div>
                      <div className="card-arrow">Mở →</div>
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Nghề nghiệp */}
        <div>
          <div className="section-header"><h2>Nghề nghiệp / 职业</h2></div>
          <div className="set-group">
            <div className="set-title">Câu hỏi theo nghề — dùng khi biết đối phương làm gì</div>
            <div className="set-cards">
              {JOBS.map(j => (
                <Link key={j.to} className="nav-card" to={j.to}>
                  <div className="card-icon">{j.icon}</div>
                  <div className="card-type job">Nghề</div>
                  <div className="card-title">{j.title}</div>
                  <div className="card-desc">{j.desc}</div>
                  <div className="card-arrow">Mở →</div>
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Hàn */}
        <div>
          <div className="section-header"><h2>한국어 / Tiếng Hàn</h2></div>
          <div className="set-cards">
            {HAN.map(h => (
              <Link key={h.to} className="nav-card" to={h.to}>
                <div className="card-icon">{h.icon}</div>
                <div className="card-type" style={{ color: '#fb923c' }}>Hàn</div>
                <div className="card-title">{h.title}</div>
                <div className="card-desc">{h.desc}</div>
                <div className="card-arrow">Mở →</div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
