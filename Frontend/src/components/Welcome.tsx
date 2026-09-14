import { useState, type CSSProperties } from 'react';
import { ArrowDown, ArrowUpRight, ArrowRight, FileText, Search, Quote, Pause, Play, Settings2 } from 'lucide-react';
import { useI18n } from '../i18n/context';
import './welcome.css';

interface Props {
  onStart: () => void;
  onWorkspace: () => void;
  onAuth: () => void;
  onSettings: () => void;
  signedIn: boolean;
}

export function Welcome({ onStart, onWorkspace, onAuth, onSettings, signedIn }: Props) {
  const { language, setLanguage } = useI18n();
  const vi = language === 'vi';
  const [paused, setPaused] = useState(false);
  const copy = vi ? {
    process: 'Cách hoạt động', workspace: 'Không gian nghiên cứu', login: 'Đăng nhập',
    title: 'Một câu hỏi.', title2: 'Mở ngàn hướng đi.',
    desc: 'Tìm tài liệu, kết nối ý tưởng và xây dựng báo cáo cùng đội ngũ AI Agent. Bạn đặt câu hỏi. PaperFlow giúp bạn đi sâu hơn.',
    start: 'Bắt đầu nghiên cứu', explore: 'Khám phá quy trình',
    label: 'KHÔNG GIAN CHO NHỮNG Ý TƯỞNG LỚN',
    next: 'Từ tò mò đến hiểu biết.', nextDesc: 'Một quy trình liền mạch. Bạn luôn nắm quyền xem, chọn và kiểm tra kết quả.',
    steps: [['01', 'Tìm đúng tài liệu', 'Bắt đầu với chủ đề của bạn. Tìm bài báo học thuật hoặc thêm PDF có sẵn.'], ['02', 'Kết nối tri thức', 'Theo dõi các Agent đọc, tổng hợp và so sánh những nghiên cứu bạn đã chọn.'], ['03', 'Viết có căn cứ', 'Xem bản thảo, trích dẫn và phản hồi kiểm định trước khi xuất báo cáo.']],
    end: 'Câu hỏi tiếp theo của bạn là gì?', endSub: 'Dành ít thời gian sắp xếp. Dành nhiều thời gian suy nghĩ.',
  } : {
    process: 'How it works', workspace: 'Research workspace', login: 'Sign in',
    title: 'One question.', title2: 'Endless directions.',
    desc: 'Discover papers, connect ideas and develop your report with a team of AI agents. You ask the questions. PaperFlow helps you go deeper.',
    start: 'Start researching', explore: 'Explore the process', label: 'ROOM FOR YOUR NEXT BIG IDEA',
    next: 'From curiosity to clarity.', nextDesc: 'One connected process. You stay in control of what to select, read and verify.',
    steps: [['01', 'Find your sources', 'Start with a topic. Discover academic papers or add your own PDFs.'], ['02', 'Connect the knowledge', 'Follow agents as they read, synthesize and compare your selected research.'], ['03', 'Write with context', 'Review drafts, citations and evaluation feedback before exporting your report.']],
    end: 'What will you explore next?', endSub: 'Less time organizing. More room for thinking.',
  };

  return (
    <div className={`pf-welcome ${paused ? 'pf-paused' : ''}`}>
      <a className="pf-skip" href="#research-start">{vi ? 'Đến nội dung chính' : 'Skip to content'}</a>
      <nav className="pf-nav" aria-label={vi ? 'Điều hướng chính' : 'Main navigation'}>
        <a href="#" className="pf-brand" aria-label="PaperFlow"><span className="pf-mark" aria-hidden="true"><i /><i /><i /></span>PaperFlow<span className="pf-beta">LAB</span></a>
        <div className="pf-nav-links"><a href="#how-it-works">{copy.process}</a><button onClick={onWorkspace}>{copy.workspace}<ArrowUpRight size={14} /></button></div>
        <div className="pf-nav-actions">
          <button className="pf-icon" onClick={() => setLanguage(vi ? 'en' : 'vi')} aria-label={vi ? 'Switch to English' : 'Chuyển sang tiếng Việt'}>{vi ? 'EN' : 'VI'}</button>
          <button className="pf-icon" onClick={onSettings} aria-label={vi ? 'Cài đặt' : 'Settings'}><Settings2 size={18} /></button>
          <button className="pf-pill pf-small" onClick={signedIn ? onWorkspace : onAuth}>{signedIn ? (vi ? 'Vào workspace' : 'Open workspace') : copy.login}<ArrowUpRight size={15} /></button>
        </div>
      </nav>

      <main>
        <section className="pf-hero" id="research-start">
          <div className="pf-hero-copy">
            <p className="pf-eyebrow"><span />{copy.label}</p>
            <h1><span>{copy.title}</span><span className="pf-title-second">{copy.title2}</span></h1>
            <p className="pf-description">{copy.desc}</p>
            <div className="pf-hero-actions"><button onClick={onStart} className="pf-pill">{copy.start}<ArrowUpRight size={20} /></button><a href="#how-it-works" className="pf-text-link">{copy.explore}<ArrowDown size={17} /></a></div>
            <div className="pf-caption"><span className="pf-caption-line" />PAPERFLOW / MULTI-AGENT RESEARCH</div>
          </div>

          <div className="pf-art" aria-hidden="true">
            <div className="pf-orbit pf-orbit-one" /><div className="pf-orbit pf-orbit-two" />
            <div className="pf-dot pf-dot-one" /><div className="pf-dot pf-dot-two" /><div className="pf-dot pf-dot-three" />
            <div className="pf-paper pf-paper-back" /><div className="pf-paper pf-paper-middle" />
            <div className="pf-paper pf-paper-front">
              <div className="pf-paper-top"><span>FIELD NOTES</span><FileText size={20} /></div>
              <div className="pf-paper-title">Ideas, in<br />good company.</div>
              <div className="pf-paper-rule" /><div className="pf-paper-rule pf-short" />
              <div className="pf-chart">{[40,65,48,82,62,95,76].map((v,i) => <i key={i} style={{'--bar-height':`${v}%`,'--bar-delay':`${i*.12}s`} as CSSProperties} />)}</div>
              <div className="pf-paper-bottom"><span>RESEARCH IN MOTION</span><span>↗</span></div>
            </div>
            <div className="pf-float-label pf-label-search"><Search size={16} /><span>{vi ? 'Khám phá' : 'Discover'}</span></div>
            <div className="pf-float-label pf-label-cite"><Quote size={16} /><span>{vi ? 'Kết nối ý tưởng' : 'Connect ideas'}</span></div>
            <span className="pf-art-index">FIG. 01 — THE FLOW OF IDEAS</span>
          </div>
          <button className="pf-motion-toggle" onClick={() => setPaused(!paused)} aria-pressed={paused} aria-label={paused ? (vi ? 'Bật chuyển động' : 'Play animation') : (vi ? 'Tạm dừng chuyển động' : 'Pause animation')}>{paused ? <Play size={14} /> : <Pause size={14} />}{vi ? 'Chuyển động' : 'Motion'}</button>
        </section>

        <section className="pf-process" id="how-it-works">
          <div className="pf-section-head"><p className="pf-eyebrow">01 / {vi ? 'QUY TRÌNH NGHIÊN CỨU' : 'THE RESEARCH PROCESS'}</p><h2>{copy.next}</h2><p>{copy.nextDesc}</p></div>
          <div className="pf-steps">{copy.steps.map(([number,title,desc],i) => <article className="pf-step" key={number}><div className="pf-step-number">{number}<span>{[<Search key="s" size={23} />,<FileText key="f" size={23} />,<Quote key="q" size={23} />][i]}</span></div><h3>{title}</h3><p>{desc}</p></article>)}</div>
          <p className="pf-research-note">{vi ? 'AI hỗ trợ nghiên cứu, không thay thế việc kiểm chứng nguồn và đánh giá học thuật của bạn.' : 'AI supports research. It does not replace source verification and your academic judgment.'}</p>
        </section>
        <section className="pf-closing"><div><p className="pf-eyebrow">MAKE ROOM FOR DISCOVERY</p><h2>{copy.end}</h2><p>{copy.endSub}</p></div><button className="pf-round-cta" onClick={onStart} aria-label={copy.start}><ArrowRight size={38} /></button></section>
      </main>
      <footer className="pf-footer"><span>PaperFlow — Research, connected.</span><button onClick={onWorkspace}>{copy.workspace}<ArrowUpRight size={15} /></button></footer>
    </div>
  );
}
