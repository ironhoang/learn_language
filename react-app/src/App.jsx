import { HashRouter, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import { AskPage, JobPage } from './pages/AskPage';
import IntroducePage from './pages/IntroducePage';
import WithKidPage from './pages/WithKidPage';

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/episoden/ask/:setId" element={<AskPage />} />
        <Route path="/episoden/introduce/:setId" element={<IntroducePage />} />
        <Route path="/jobs/:jobId" element={<JobPage />} />
        <Route path="/han/with-kid" element={<WithKidPage />} />
      </Routes>
    </HashRouter>
  );
}
