import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import SourceBadge from '../components/SourceBadge';
import Loading3D from '../components/3d/Loading3D';
import MarkdownRenderer from '../components/MarkdownRenderer';
import {
  ArrowLeft,
  Send,
  Sparkles,
  Globe,
  Copy,
  Check,
  MessageSquare
} from 'lucide-react';

export default function ConversationView() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [conversation, setConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [answering, setAnswering] = useState(false);
  const [copiedId, setCopiedId] = useState(null);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadConversation();
  }, [id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, answering]);

  const loadConversation = async () => {
    try {
      const data = await api.get(`/api/conversations/${id}`);
      setConversation(data);
      setMessages(data.messages || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || answering) return;

    const userText = inputMessage.trim();
    setInputMessage('');

    // Optimistically append user message
    const userMsg = {
      id: 'usr_' + Date.now(),
      role: 'USER',
      content: userText,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMsg]);
    setAnswering(true);

    try {
      const res = await api.post('/api/chat', {
        conversation_id: id,
        message: userText
      });

      const aiMsg = {
        id: res.message_id || 'ai_' + Date.now(),
        role: 'ASSISTANT',
        content: res.answer,
        source_metadata: {
          sources: res.sources || [],
          web_search_used: res.web_search_used,
          document_used: res.document_used
        },
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        id: 'err_' + Date.now(),
        role: 'ASSISTANT',
        content: 'AI service is temporarily unavailable. Please try again.',
        is_error: true
      }]);
    } finally {
      setAnswering(false);
    }
  };

  const copyText = (content, msgId) => {
    navigator.clipboard.writeText(content);
    setCopiedId(msgId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (loading) {
    return <Loading3D message="Loading conversation history..." />;
  }

  if (!conversation) {
    return (
      <div className="container" style={{ padding: '4rem 1.5rem', textAlign: 'center' }}>
        <h2>Conversation not found.</h2>
        <button onClick={() => navigate('/conversations')} className="btn btn-secondary" style={{ marginTop: '1rem' }}>
          Back to Conversations
        </button>
      </div>
    );
  }

  return (
    <div className="container" style={{ padding: 'clamp(1rem, 2.5vw, 2.5rem) var(--container-pad, 1.5rem)', minHeight: '85vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', gap: '0.75rem', flexWrap: 'wrap' }}>
        <button
          onClick={() => navigate('/conversations')}
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)', background: 'none', cursor: 'pointer', padding: '0.4rem 0', minHeight: '44px' }}
        >
          <ArrowLeft size={16} />
          <span style={{ fontSize: '0.9rem' }}>All Conversations</span>
        </button>

        <span className="badge badge-cyan" style={{ fontSize: '0.78rem' }}>
          {conversation.subject || 'Academic Session'}
        </span>
      </div>

      {/* Main Chat Box */}
      <div className="glass-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', height: 'clamp(460px, 72vh, 680px)', overflow: 'hidden', borderRadius: '18px' }}>
        {/* Chat Title Bar */}
        <div style={{ padding: '0.9rem clamp(1rem, 2.5vw, 1.5rem)', borderBottom: '1px solid var(--border-subtle)', background: 'rgba(10, 14, 23, 0.7)' }}>
          <h2 style={{ fontSize: 'clamp(1.05rem, 2.5vw, 1.25rem)', color: '#fff', margin: 0, wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
            {conversation.title}
          </h2>
        </div>

        {/* Message Log */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 'clamp(0.9rem, 2.5vw, 1.5rem)', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {messages.map((m) => {
            const isUser = m.role === 'USER';
            const meta = m.source_metadata || {};
            const sources = meta.sources || [];

            return (
              <div
                key={m.id}
                style={{
                  alignSelf: isUser ? 'flex-end' : 'flex-start',
                  maxWidth: isUser ? '88%' : '96%',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.35rem'
                }}
              >
                <div
                  style={{
                    padding: 'clamp(0.85rem, 2.5vw, 1.25rem) clamp(1rem, 3vw, 1.5rem)',
                    borderRadius: '16px',
                    background: isUser
                      ? 'linear-gradient(135deg, rgba(0, 242, 254, 0.15) 0%, rgba(79, 172, 254, 0.2) 100%)'
                      : 'rgba(15, 22, 36, 0.85)',
                    border: `1px solid ${isUser ? 'rgba(0, 242, 254, 0.3)' : 'rgba(255, 255, 255, 0.08)'}`,
                    color: '#f8fafc',
                    lineHeight: '1.6',
                    fontSize: 'clamp(0.88rem, 2vw, 0.96rem)',
                    wordBreak: 'break-word',
                    overflowWrap: 'anywhere'
                  }}
                >
                  {!isUser && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem', paddingBottom: '0.45rem', borderBottom: '1px solid rgba(255, 255, 255, 0.06)' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--brand-cyan)' }}>
                        AI STUDY ASSISTANT
                      </span>
                      <button
                        onClick={() => copyText(m.content, m.id)}
                        style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', minHeight: '36px', padding: '0 0.4rem' }}
                      >
                        {copiedId === m.id ? <Check size={13} color="#10b981" /> : <Copy size={13} />}
                        <span>{copiedId === m.id ? 'Copied' : 'Copy'}</span>
                      </button>
                    </div>
                  )}

                  {isUser ? (
                    <div style={{ whiteSpace: 'pre-wrap' }}>
                      {m.content}
                    </div>
                  ) : (
                    <MarkdownRenderer content={m.content} />
                  )}

                  {sources.length > 0 && (
                    <div style={{ marginTop: '0.85rem', paddingTop: '0.65rem', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--brand-cyan)', marginBottom: '0.4rem' }}>
                        VERIFIED SOURCES CONSULTED:
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                        {sources.map((s, idx) => (
                          <SourceBadge key={idx} source={s} />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {answering && <Loading3D message="Thinking & formulating response..." />}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div style={{ padding: 'clamp(0.75rem, 2vw, 1.25rem)', borderTop: '1px solid var(--border-subtle)', background: 'rgba(7, 10, 16, 0.8)' }}>
          <form onSubmit={handleSend} style={{ display: 'flex', gap: '0.65rem' }}>
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Ask a follow-up question..."
              disabled={answering}
              style={{ borderRadius: '14px', height: '48px', flex: 1 }}
            />
            <button
              type="submit"
              disabled={answering || !inputMessage.trim()}
              className="btn btn-primary"
              style={{ height: '48px', minWidth: '48px', padding: '0 1.25rem', borderRadius: '14px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            >
              <Send size={18} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
