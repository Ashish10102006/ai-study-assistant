import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import SourceBadge from '../components/SourceBadge';
import Loading3D from '../components/3d/Loading3D';
import {
  Sparkles,
  Send,
  Globe,
  Upload,
  BookOpen,
  FileText,
  Copy,
  Check,
  RotateCcw,
  ListOrdered,
  BookMarked,
  CheckSquare,
  HelpCircle,
  AlertCircle,
  FileSearch,
  ExternalLink,
  ChevronDown
} from 'lucide-react';
import confetti from 'canvas-confetti';

const EXPLANATION_MODES = [
  { id: 'simple', label: 'Simple & Analogies', icon: '💡' },
  { id: 'detailed', label: 'Detailed & Rigorous', icon: '📖' },
  { id: 'step_by_step', label: 'Step-by-Step Flow', icon: '🪜' },
  { id: 'examples', label: 'Code & Worked Examples', icon: '💻' },
  { id: 'revision', label: 'Revision & Cheat Sheet', icon: '⚡' },
  { id: 'exam_oriented', label: 'Exam High-Yield Format', icon: '🎓' },
];

export default function StudyAssistant() {
  const location = useLocation();
  const navigate = useNavigate();

  // State
  const [question, setQuestion] = useState('');
  const [subject, setSubject] = useState('Computer Science');
  const [customTopic, setCustomTopic] = useState('');
  const [explanationMode, setExplanationMode] = useState('simple');
  const [useWebSearch, setUseWebSearch] = useState(false);
  const [selectedDocumentId, setSelectedDocumentId] = useState('');
  const [uploadedDocuments, setUploadedDocuments] = useState([]);

  // Active Chat / Response State
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [activeSources, setActiveSources] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [warningMessage, setWarningMessage] = useState(null);
  const [copiedId, setCopiedId] = useState(null);

  // Active Tool Mode (assistant vs notes vs quiz vs questions)
  const [activeTab, setActiveTab] = useState('assistant'); // 'assistant', 'notes', 'quiz', 'questions'
  const [generatedNotes, setGeneratedNotes] = useState(null);
  const [quizData, setQuizData] = useState(null);
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [practiceQuestions, setPracticeQuestions] = useState(null);

  const messagesEndRef = useRef(null);

  // Load uploaded documents on mount
  useEffect(() => {
    api.get('/api/documents')
      .then(docs => setUploadedDocuments(docs))
      .catch(() => {});
  }, []);

  // Handle incoming query from location state (e.g. from Home page or URL parameters)
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const modeParam = searchParams.get('mode');
    const tabParam = searchParams.get('tab');
    const subjectParam = searchParams.get('subject');

    if (modeParam) setExplanationMode(modeParam);
    if (tabParam) setActiveTab(tabParam);
    if (subjectParam) setSubject(subjectParam);

    if (location.state?.initialQuestion) {
      setQuestion(location.state.initialQuestion);
      if (location.state.subject) setSubject(location.state.subject);
      if (location.state.customTopic) setCustomTopic(location.state.customTopic);
      // Auto submit initial question
      executeAsk(location.state.initialQuestion, location.state.subject, location.state.customTopic);
    }
  }, [location]);

  // Scroll chat into view
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const executeAsk = async (qText, sub, custTopic) => {
    const query = qText || question;
    if (!query.trim()) return;

    setLoading(true);
    setWarningMessage(null);

    // Optimistically append user message
    const userMessage = {
      id: 'user_' + Date.now(),
      role: 'USER',
      content: query,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    setQuestion('');

    try {
      const res = await api.post('/api/ask', {
        question: query,
        subject: sub || subject,
        custom_topic: (custTopic || customTopic).trim() || undefined,
        explanation_mode: explanationMode,
        use_web_search: useWebSearch,
        document_id: selectedDocumentId || undefined,
        conversation_id: conversationId || undefined
      });

      setConversationId(res.conversation_id);
      setActiveSources(res.sources || []);
      if (res.warning) setWarningMessage(res.warning);

      const aiMessage = {
        id: res.message_id || 'ai_' + Date.now(),
        role: 'ASSISTANT',
        content: res.answer,
        sources: res.sources || [],
        web_search_used: res.web_search_used,
        document_used: res.document_used,
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, aiMessage]);

    } catch (err) {
      console.error('Ask error:', err);
      const errorMessage = {
        id: 'err_' + Date.now(),
        role: 'ASSISTANT',
        content: 'AI service is temporarily unavailable. Please try again.',
        is_error: true,
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
      setWarningMessage('AI service is temporarily unavailable. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleFollowUp = (e) => {
    e.preventDefault();
    executeAsk();
  };

  const copyContent = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Study Tools Generators
  const handleGenerateNotes = async () => {
    const targetTopic = customTopic.trim() || subject;
    setLoading(true);
    try {
      const res = await api.post('/api/study/notes', {
        topic: targetTopic,
        subject: subject,
        document_id: selectedDocumentId || undefined
      });
      setGeneratedNotes(res.notes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateQuiz = async () => {
    const targetTopic = customTopic.trim() || subject;
    setLoading(true);
    setQuizSubmitted(false);
    setQuizAnswers({});
    try {
      const res = await api.post('/api/study/quiz', {
        topic: targetTopic,
        subject: subject,
        num_questions: 5,
        difficulty: 'medium',
        document_id: selectedDocumentId || undefined
      });
      setQuizData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectQuizAnswer = (questionId, key) => {
    if (quizSubmitted) return;
    setQuizAnswers(prev => ({ ...prev, [questionId]: key }));
  };

  const handleSubmitQuiz = () => {
    setQuizSubmitted(true);
    // Trigger confetti
    confetti({
      particleCount: 80,
      spread: 70,
      origin: { y: 0.6 }
    });
  };

  const handleGenerateQuestions = async () => {
    const targetTopic = customTopic.trim() || subject;
    setLoading(true);
    try {
      const res = await api.post('/api/study/questions', {
        topic: targetTopic,
        subject: subject,
        count: 5,
        document_id: selectedDocumentId || undefined
      });
      setPracticeQuestions(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ padding: '2.5rem 1.5rem', minHeight: 'calc(100vh - var(--navbar-height))' }}>
      {/* Top Controls Bar */}
      <div
        className="glass-card"
        style={{
          padding: '1.25rem 1.75rem',
          marginBottom: '2rem',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '1.25rem',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <span style={{ fontWeight: '700', color: 'var(--brand-cyan)', fontSize: '0.9rem' }}>
            STUDY CONTEXT:
          </span>

          {/* Subject Dropdown */}
          <select
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            style={{ width: 'auto', minWidth: '170px', padding: '0.5rem 0.85rem' }}
          >
            <option value="Computer Science">Computer Science</option>
            <option value="Data Structures">Data Structures</option>
            <option value="Algorithms">Algorithms</option>
            <option value="Operating Systems">Operating Systems</option>
            <option value="DBMS">DBMS</option>
            <option value="Computer Networks">Computer Networks</option>
            <option value="Cybersecurity">Cybersecurity</option>
            <option value="Artificial Intelligence">Artificial Intelligence</option>
            <option value="Mathematics">Mathematics</option>
            <option value="Physics">Physics</option>
            <option value="Chemistry">Chemistry</option>
            <option value="Other">Other Academic Subject</option>
          </select>

          {/* Custom Topic Input */}
          <input
            type="text"
            value={customTopic}
            onChange={(e) => setCustomTopic(e.target.value)}
            placeholder="Custom Topic (e.g. TCP Handshake, Normalization...)"
            style={{ width: 'auto', minWidth: '260px', padding: '0.5rem 0.85rem' }}
          />

          {/* Attached Document Filter */}
          <select
            value={selectedDocumentId}
            onChange={(e) => setSelectedDocumentId(e.target.value)}
            style={{ width: 'auto', minWidth: '180px', padding: '0.5rem 0.85rem' }}
          >
            <option value="">No Document Attached</option>
            {uploadedDocuments.map(doc => (
              <option key={doc.id} value={doc.id}>
                📄 {doc.file_name} ({doc.chunks_count} chunks)
              </option>
            ))}
          </select>
        </div>

        {/* Web Search & Modes Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button
            onClick={() => setUseWebSearch(!useWebSearch)}
            className="btn"
            style={{
              padding: '0.5rem 1rem',
              fontSize: '0.85rem',
              background: useWebSearch ? 'rgba(0, 242, 254, 0.15)' : 'rgba(255, 255, 255, 0.05)',
              border: `1px solid ${useWebSearch ? 'var(--brand-cyan)' : 'var(--border-medium)'}`,
              color: useWebSearch ? 'var(--brand-cyan)' : 'var(--text-secondary)'
            }}
          >
            <Globe size={15} />
            <span>Web Search {useWebSearch ? 'ON' : 'OFF'}</span>
          </button>
        </div>
      </div>

      {/* Tabs Navigation (Assistant vs Notes vs Quiz vs Practice Questions) */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.75rem' }}>
        {[
          { id: 'assistant', label: 'AI Study Chat', icon: <Sparkles size={16} /> },
          { id: 'notes', label: 'Structured Notes', icon: <BookMarked size={16} /> },
          { id: 'quiz', label: 'Quiz Arena', icon: <CheckSquare size={16} /> },
          { id: 'questions', label: 'Practice Problems', icon: <HelpCircle size={16} /> }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.65rem 1.25rem',
              borderRadius: '12px',
              fontWeight: '600',
              fontSize: '0.9rem',
              background: activeTab === tab.id ? 'rgba(0, 242, 254, 0.1)' : 'transparent',
              color: activeTab === tab.id ? 'var(--brand-cyan)' : 'var(--text-secondary)',
              border: activeTab === tab.id ? '1px solid rgba(0, 242, 254, 0.3)' : '1px solid transparent',
              cursor: 'pointer'
            }}
          >
            {tab.icon}
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Warning Notice if Web or AI had fallbacks */}
      {warningMessage && (
        <div
          style={{
            background: 'rgba(245, 158, 11, 0.12)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            borderRadius: '12px',
            padding: '0.85rem 1.25rem',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            color: '#fbbf24',
            fontSize: '0.9rem'
          }}
        >
          <AlertCircle size={18} />
          <span>{warningMessage}</span>
        </div>
      )}

      {/* ==========================================================
          TAB 1: AI STUDY CONVERSATIONAL CHAT
          ========================================================== */}
      {activeTab === 'assistant' && (
        <div style={{ display: 'grid', gridTemplateColumns: activeSources.length > 0 ? '1fr 340px' : '1fr', gap: '1.5rem' }}>
          {/* Main Chat Area */}
          <div style={{ display: 'flex', flexDirection: 'column', height: '650px' }} className="glass-card">
            {/* Explanation Mode Selector Bar */}
            <div
              style={{
                padding: '0.75rem 1.25rem',
                borderBottom: '1px solid var(--border-subtle)',
                display: 'flex',
                gap: '0.5rem',
                overflowX: 'auto'
              }}
            >
              {EXPLANATION_MODES.map(mode => (
                <button
                  key={mode.id}
                  onClick={() => setExplanationMode(mode.id)}
                  style={{
                    padding: '0.4rem 0.85rem',
                    borderRadius: '8px',
                    fontSize: '0.8rem',
                    fontWeight: explanationMode === mode.id ? '700' : '500',
                    background: explanationMode === mode.id ? 'var(--grad-primary)' : 'rgba(255, 255, 255, 0.04)',
                    color: explanationMode === mode.id ? '#030712' : 'var(--text-secondary)',
                    whiteSpace: 'nowrap',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <span style={{ marginRight: '0.35rem' }}>{mode.icon}</span>
                  <span>{mode.label}</span>
                </button>
              ))}
            </div>

            {/* Messages Scroll Area */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {messages.length === 0 && !loading && (
                <div style={{ textAlign: 'center', margin: 'auto', maxWidth: '480px' }}>
                  <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🎓</div>
                  <h3 style={{ fontSize: '1.4rem', color: '#fff', marginBottom: '0.5rem' }}>
                    AI Academic Study Assistant
                  </h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', lineHeight: '1.5' }}>
                    Ask any question regarding <strong>{customTopic || subject}</strong>. Select your preferred explanation style above (Simple, Step-by-Step, or Exam-grade).
                  </p>
                </div>
              )}

              {messages.map((m) => {
                const isUser = m.role === 'USER';
                return (
                  <div
                    key={m.id}
                    style={{
                      alignSelf: isUser ? 'flex-end' : 'flex-start',
                      maxWidth: isUser ? '80%' : '90%',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.4rem'
                    }}
                  >
                    <div
                      style={{
                        padding: '1.25rem 1.5rem',
                        borderRadius: '18px',
                        background: isUser
                          ? 'linear-gradient(135deg, rgba(0, 242, 254, 0.15) 0%, rgba(79, 172, 254, 0.2) 100%)'
                          : 'rgba(15, 22, 36, 0.85)',
                        border: `1px solid ${isUser ? 'rgba(0, 242, 254, 0.3)' : 'rgba(255, 255, 255, 0.08)'}`,
                        color: '#f8fafc',
                        lineHeight: '1.65',
                        fontSize: '0.96rem',
                        position: 'relative'
                      }}
                    >
                      {/* Meta header for AI answers */}
                      {!isUser && (
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem', paddingBottom: '0.6rem', borderBottom: '1px solid rgba(255, 255, 255, 0.06)' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.78rem', color: 'var(--brand-cyan)', fontWeight: '700' }}>
                            <Sparkles size={14} />
                            <span>AI STUDY ASSISTANT (Gemini)</span>
                            {m.document_used && (
                              <span style={{ color: '#c084fc', background: 'rgba(192, 132, 252, 0.1)', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>
                                Document Grounded
                              </span>
                            )}
                            {m.web_search_used && (
                              <span style={{ color: '#38bdf8', background: 'rgba(56, 189, 248, 0.1)', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>
                                Verified Web Sources
                              </span>
                            )}
                          </div>
                          <button
                            onClick={() => copyContent(m.content, m.id)}
                            style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem' }}
                          >
                            {copiedId === m.id ? <Check size={13} color="#10b981" /> : <Copy size={13} />}
                            <span>{copiedId === m.id ? 'Copied' : 'Copy'}</span>
                          </button>
                        </div>
                      )}

                      {/* Content with pre-wrap */}
                      <div style={{ whiteSpace: 'pre-wrap' }}>
                        {m.content}
                      </div>
                    </div>
                  </div>
                );
              })}

              {loading && <Loading3D />}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Box Bar */}
            <div style={{ padding: '1.25rem', borderTop: '1px solid var(--border-subtle)', background: 'rgba(7, 10, 16, 0.7)' }}>
              <form onSubmit={handleFollowUp} style={{ display: 'flex', gap: '0.75rem' }}>
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask follow-up question or new concept..."
                  disabled={loading}
                  style={{ borderRadius: '14px', height: '50px' }}
                />
                <button
                  type="submit"
                  disabled={loading || !question.trim()}
                  className="btn btn-primary"
                  style={{ height: '50px', padding: '0 1.5rem', borderRadius: '14px' }}
                >
                  <Send size={18} />
                </button>
              </form>
            </div>
          </div>

          {/* Right Sidebar: Real Web Sources (Tavily) */}
          {activeSources.length > 0 && (
            <div className="glass-card" style={{ padding: '1.25rem', height: '650px', overflowY: 'auto' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: 'var(--brand-cyan)' }}>
                <Globe size={18} />
                <h4 style={{ fontSize: '1rem', color: '#fff' }}>Verified Web Sources</h4>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
                Retrieved live via Tavily Search. Real academic references and documentation.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {activeSources.map((src, idx) => (
                  <SourceBadge key={idx} source={src} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ==========================================================
          TAB 2: STRUCTURED STUDY NOTES
          ========================================================== */}
      {activeTab === 'notes' && (
        <div className="glass-card" style={{ padding: '2.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
            <div>
              <h3 style={{ fontSize: '1.6rem', color: '#fff' }}>
                Structured Study Notes Generator
              </h3>
              <p style={{ color: 'var(--text-secondary)' }}>
                Generates high-yield academic study notes on <strong>{customTopic || subject}</strong> with definitions, proofs, code, and exam checklists.
              </p>
            </div>
            <button onClick={handleGenerateNotes} disabled={loading} className="btn btn-primary">
              <Sparkles size={16} />
              <span>Generate Notes</span>
            </button>
          </div>

          {loading && <Loading3D message="Synthesizing academic notes..." />}

          {generatedNotes ? (
            <div
              style={{
                background: 'rgba(10, 14, 23, 0.85)',
                padding: '2rem',
                borderRadius: '16px',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                whiteSpace: 'pre-wrap',
                lineHeight: '1.7',
                fontSize: '1rem'
              }}
            >
              {generatedNotes}
            </div>
          ) : !loading && (
            <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>
              Click "Generate Notes" above to create publication-grade revision notes.
            </div>
          )}
        </div>
      )}

      {/* ==========================================================
          TAB 3: QUIZ ARENA
          ========================================================== */}
      {activeTab === 'quiz' && (
        <div className="glass-card" style={{ padding: '2.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
            <div>
              <h3 style={{ fontSize: '1.6rem', color: '#fff' }}>
                Academic Quiz Arena
              </h3>
              <p style={{ color: 'var(--text-secondary)' }}>
                Test your mastery on <strong>{customTopic || subject}</strong> with multiple-choice questions and instant feedback.
              </p>
            </div>
            <button onClick={handleGenerateQuiz} disabled={loading} className="btn btn-primary">
              <CheckSquare size={16} />
              <span>New Quiz</span>
            </button>
          </div>

          {loading && <Loading3D message="Formulating pedagogical quiz questions..." />}

          {quizData && !loading && (
            <div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', marginBottom: '2rem' }}>
                {quizData.questions.map((q, idx) => (
                  <div
                    key={q.id}
                    style={{
                      background: 'rgba(15, 23, 42, 0.6)',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                      borderRadius: '16px',
                      padding: '1.5rem'
                    }}
                  >
                    <div style={{ fontWeight: '700', fontSize: '1.1rem', color: '#f8fafc', marginBottom: '1rem' }}>
                      Question {idx + 1}: {q.question}
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.75rem' }}>
                      {q.options.map((opt) => {
                        const isChosen = quizAnswers[q.id] === opt.key;
                        const isCorrect = q.correct_answer === opt.key;
                        let optBg = 'rgba(255, 255, 255, 0.04)';
                        let optBorder = 'rgba(255, 255, 255, 0.1)';

                        if (quizSubmitted) {
                          if (isCorrect) {
                            optBg = 'rgba(16, 185, 129, 0.2)';
                            optBorder = '#10b981';
                          } else if (isChosen && !isCorrect) {
                            optBg = 'rgba(239, 68, 68, 0.2)';
                            optBorder = '#ef4444';
                          }
                        } else if (isChosen) {
                          optBg = 'rgba(0, 242, 254, 0.15)';
                          optBorder = 'var(--brand-cyan)';
                        }

                        return (
                          <div
                            key={opt.key}
                            onClick={() => handleSelectQuizAnswer(q.id, opt.key)}
                            style={{
                              padding: '0.85rem 1.25rem',
                              borderRadius: '12px',
                              background: optBg,
                              border: `1px solid ${optBorder}`,
                              cursor: quizSubmitted ? 'default' : 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.85rem',
                              transition: 'all 0.2s ease'
                            }}
                          >
                            <span style={{ fontWeight: '700', color: 'var(--brand-cyan)' }}>{opt.key}.</span>
                            <span>{opt.text}</span>
                          </div>
                        );
                      })}
                    </div>

                    {quizSubmitted && (
                      <div
                        style={{
                          marginTop: '1.25rem',
                          padding: '1rem',
                          borderRadius: '12px',
                          background: 'rgba(0, 242, 254, 0.06)',
                          border: '1px solid rgba(0, 242, 254, 0.2)',
                          fontSize: '0.9rem',
                          color: '#e2e8f0'
                        }}
                      >
                        <strong>Explanation:</strong> {q.explanation}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {!quizSubmitted ? (
                <button
                  onClick={handleSubmitQuiz}
                  className="btn btn-primary"
                  style={{ padding: '0.85rem 2rem', fontSize: '1rem', borderRadius: '14px' }}
                >
                  Submit & Check Answers
                </button>
              ) : (
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                  <button
                    onClick={handleGenerateQuiz}
                    className="btn btn-secondary"
                  >
                    Try Another Quiz
                  </button>
                </div>
              )}
            </div>
          )}

          {!quizData && !loading && (
            <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>
              Click "New Quiz" to generate interactive questions on your active topic.
            </div>
          )}
        </div>
      )}

      {/* ==========================================================
          TAB 4: PRACTICE PROBLEMS
          ========================================================== */}
      {activeTab === 'questions' && (
        <div className="glass-card" style={{ padding: '2.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
            <div>
              <h3 style={{ fontSize: '1.6rem', color: '#fff' }}>
                Practice Problem Sets
              </h3>
              <p style={{ color: 'var(--text-secondary)' }}>
                Exam-grade conceptual, algorithmic, and numerical questions with model solutions for <strong>{customTopic || subject}</strong>.
              </p>
            </div>
            <button onClick={handleGenerateQuestions} disabled={loading} className="btn btn-primary">
              <HelpCircle size={16} />
              <span>Generate Problems</span>
            </button>
          </div>

          {loading && <Loading3D message="Drafting exam-grade problems and hints..." />}

          {practiceQuestions && !loading && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {practiceQuestions.questions.map((item, idx) => (
                <div
                  key={item.id}
                  style={{
                    background: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '16px',
                    padding: '1.75rem'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                    <span className="badge badge-purple">{item.type}</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Problem #{idx + 1}</span>
                  </div>

                  <h4 style={{ fontSize: '1.15rem', color: '#fff', marginBottom: '1rem' }}>
                    {item.question}
                  </h4>

                  {item.hints && item.hints.length > 0 && (
                    <div style={{ marginBottom: '1rem', background: 'rgba(255, 255, 255, 0.03)', padding: '0.85rem', borderRadius: '10px' }}>
                      <div style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--brand-cyan)', marginBottom: '0.35rem' }}>
                        HINTS FOR SOLVING:
                      </div>
                      <ul style={{ paddingLeft: '1.25rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        {item.hints.map((h, i) => <li key={i}>{h}</li>)}
                      </ul>
                    </div>
                  )}

                  <details style={{ marginTop: '0.75rem', cursor: 'pointer' }}>
                    <summary style={{ fontSize: '0.9rem', fontWeight: '600', color: 'var(--brand-cyan)' }}>
                      View Model Answer & Detailed Steps
                    </summary>
                    <div
                      style={{
                        marginTop: '0.75rem',
                        padding: '1rem',
                        borderRadius: '10px',
                        background: 'rgba(0, 0, 0, 0.4)',
                        border: '1px solid rgba(255, 255, 255, 0.06)',
                        whiteSpace: 'pre-wrap',
                        fontSize: '0.92rem',
                        color: '#f8fafc'
                      }}
                    >
                      {item.model_answer}
                    </div>
                  </details>
                </div>
              ))}
            </div>
          )}

          {!practiceQuestions && !loading && (
            <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>
              Click "Generate Problems" to formulate exam practice challenges.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
