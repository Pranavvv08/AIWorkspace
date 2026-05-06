"use client";

import { useState, useEffect } from 'react';
import { Send, Database, CheckSquare, PlusCircle, MessageSquare, LogOut, CheckCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

type Message = { id: string; role: 'user' | 'ai'; content: string; };
type Task = { id: number; title: string; priority: string; status: string; };

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [authMode, setAuthMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [authError, setAuthError] = useState('');
  const [activeModule, setActiveModule] = useState<'chat' | 'tasks' | 'repo' | 'knowledge'>('chat');
  const [repoUrl, setRepoUrl] = useState('');
  const [repoQuery, setRepoQuery] = useState('');
  const [repoAnswer, setRepoAnswer] = useState('');
  const [knowledgeQuery, setKnowledgeQuery] = useState('');
  const [knowledgeAnswer, setKnowledgeAnswer] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [isIndexing, setIsIndexing] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);

  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    if (savedToken) {
      setToken(savedToken);
      fetchHistory(savedToken);
      fetchTasks(savedToken);
    }
  }, []);

  const fetchHistory = async (authToken: string) => {
    try {
      const res = await fetch('http://localhost:8000/history', { headers: { 'Authorization': `Bearer ${authToken}` } });
      if (res.ok) {
        const data = await res.json();
        setMessages(data.length > 0 ? data.map((m: any) => ({ ...m, id: m.id.toString() })) : [{ id: '1', role: 'ai', content: 'Welcome to your Agent Workspace!' }]);
      } else if (res.status === 401) {
        handleLogout();
      }
    } catch (err) {}
  };

  const fetchTasks = async (authToken: string) => {
    try {
      const res = await fetch('http://localhost:8000/tasks', { headers: { 'Authorization': `Bearer ${authToken}` } });
      if (res.ok) setTasks(await res.json());
    } catch (err) {}
  };

  const handleIndexRepo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl || !token) return;
    setIsIndexing(true);
    try {
      const res = await fetch('http://localhost:8000/repo/index', {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ repo_url: repoUrl })
      });
      if (res.ok) alert("Repository successfully indexed into ChromaDB!");
      else alert("Failed to index repository.");
    } catch (err) {} finally { setIsIndexing(false); }
  };

  const handleQueryRepo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoQuery || !token) return;
    setIsQuerying(true); setRepoAnswer('');
    try {
      const res = await fetch('http://localhost:8000/repo/query', {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ query: repoQuery })
      });
      if (res.ok) setRepoAnswer((await res.json()).answer);
    } catch (err) {} finally { setIsQuerying(false); }
  };

  const handleUploadKnowledge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !token) return;
    setIsIndexing(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch('http://localhost:8000/knowledge/upload', {
        method: 'POST', headers: { 'Authorization': `Bearer ${token}` }, body: formData
      });
      if (res.ok) {
        alert("Document successfully processed and indexed!");
        setFile(null);
      } else alert("Failed to index document.");
    } catch (err) {} finally { setIsIndexing(false); }
  };

  const handleQueryKnowledge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!knowledgeQuery || !token) return;
    setIsQuerying(true); setKnowledgeAnswer('');
    try {
      const res = await fetch('http://localhost:8000/knowledge/query', {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ query: knowledgeQuery })
      });
      if (res.ok) setKnowledgeAnswer((await res.json()).answer);
    } catch (err) {} finally { setIsQuerying(false); }
  };

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError('');
    try {
      if (authMode === 'signup') {
        const res = await fetch('http://localhost:8000/signup', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) });
        if (!res.ok) throw new Error('Signup failed. Email might be in use.');
        setAuthMode('login'); setAuthError('Signup successful! Please log in.');
      } else {
        const formData = new URLSearchParams(); formData.append('username', email); formData.append('password', password);
        const res = await fetch('http://localhost:8000/token', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: formData });
        if (!res.ok) throw new Error('Invalid credentials.');
        const data = await res.json();
        localStorage.setItem('token', data.access_token); setToken(data.access_token);
        fetchHistory(data.access_token); fetchTasks(data.access_token);
      }
    } catch (err: any) { setAuthError(err.message); }
  };

  const handleLogout = () => { localStorage.removeItem('token'); setToken(null); setMessages([]); setTasks([]); };

  const handleNewChat = async () => {
    setActiveModule('chat');
    if (!token) return;
    if (confirm("Are you sure you want to start a new chat? This will permanently clear your current conversation memory.")) {
      try {
        await fetch('http://localhost:8000/history/clear', { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } });
        setMessages([{ id: '1', role: 'ai', content: 'Welcome to your new chat! How can I help you today?' }]);
      } catch (err) {}
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !token) return;
    const userMessage: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]); setInput(''); setIsTyping(true);
    try {
      const res = await fetch('http://localhost:8000/chat', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body: JSON.stringify({ content: userMessage.content }) });
      if (res.ok) {
        const aiData = await res.json();
        setMessages(prev => [...prev, { id: aiData.id.toString(), role: 'ai', content: aiData.content }]);
        fetchTasks(token);
      }
    } catch (err) {} finally { setIsTyping(false); }
  };

  if (!token) {
    return (
      <div className="app-container" style={{ alignItems: 'center', justifyContent: 'center' }}>
        <div className="glass" style={{ padding: '40px', borderRadius: '16px', width: '100%', maxWidth: '400px' }}>
          <h2 style={{ textAlign: 'center', marginBottom: '24px' }}>{authMode === 'login' ? 'Welcome Back' : 'Create Account'}</h2>
          {authError && <div style={{ color: '#ef4444', marginBottom: '16px', textAlign: 'center', fontSize: '14px' }}>{authError}</div>}
          <form onSubmit={handleAuth} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <input type="email" placeholder="Email address" value={email || ''} onChange={(e) => setEmail(e.target.value)} style={{ padding: '12px', borderRadius: '8px', border: '1px solid var(--surface-border)', background: 'rgba(0,0,0,0.2)', color: 'var(--foreground)' }} required />
            <input type="password" placeholder="Password" value={password || ''} onChange={(e) => setPassword(e.target.value)} style={{ padding: '12px', borderRadius: '8px', border: '1px solid var(--surface-border)', background: 'rgba(0,0,0,0.2)', color: 'var(--foreground)' }} required />
            <button type="submit" style={{ padding: '12px', borderRadius: '8px', background: 'var(--primary)', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}>{authMode === 'login' ? 'Login' : 'Sign Up'}</button>
          </form>
          <div style={{ textAlign: 'center', marginTop: '16px', fontSize: '14px', color: '#888' }}>
            {authMode === 'login' ? "Don't have an account? " : "Already have an account? "}
            <span style={{ color: 'var(--primary)', cursor: 'pointer' }} onClick={() => setAuthMode(authMode === 'login' ? 'signup' : 'login')}>{authMode === 'login' ? 'Sign up' : 'Login'}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <aside className="sidebar glass">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '30px', fontWeight: 'bold', fontSize: '18px' }}>
          <div style={{ background: 'var(--primary)', padding: '6px', borderRadius: '8px' }}><Database size={20} color="white" /></div>
          Agent Workspace
        </div>
        
        <button onClick={handleNewChat} style={{ background: 'var(--primary)', color: 'white', border: 'none', padding: '12px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', marginBottom: '20px' }}><PlusCircle size={18} /> New Chat</button>

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ fontSize: '12px', textTransform: 'uppercase', color: '#888', marginTop: '10px', marginBottom: '5px' }}>Modules</div>
          
          <button onClick={() => setActiveModule('chat')} style={{ background: activeModule === 'chat' ? 'rgba(255,255,255,0.05)' : 'transparent', color: activeModule === 'chat' ? 'var(--foreground)' : '#888', border: 'none', padding: '10px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', textAlign: 'left', transition: '0.2s' }}>
            <MessageSquare size={16} /> Chat Workspace
          </button>
          
          <button onClick={() => setActiveModule('tasks')} style={{ background: activeModule === 'tasks' ? 'rgba(255,255,255,0.05)' : 'transparent', color: activeModule === 'tasks' ? 'var(--foreground)' : '#888', border: 'none', padding: '10px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', textAlign: 'left', transition: '0.2s' }}>
            <CheckSquare size={16} /> Tasks Agent
          </button>

          <button onClick={() => setActiveModule('repo')} style={{ background: activeModule === 'repo' ? 'rgba(255,255,255,0.05)' : 'transparent', color: activeModule === 'repo' ? 'var(--foreground)' : '#888', border: 'none', padding: '10px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', textAlign: 'left', transition: '0.2s' }}>
            <Database size={16} /> Repo Intelligence
          </button>
          
          <button onClick={() => setActiveModule('knowledge')} style={{ background: activeModule === 'knowledge' ? 'rgba(255,255,255,0.05)' : 'transparent', color: activeModule === 'knowledge' ? 'var(--foreground)' : '#888', border: 'none', padding: '10px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', textAlign: 'left', transition: '0.2s' }}>
            <Database size={16} /> Personal Knowledge
          </button>
        </div>

        <button onClick={handleLogout} style={{ background: 'transparent', color: '#888', border: 'none', padding: '10px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
          <LogOut size={16} /> Logout
        </button>
      </aside>

      <main className="main-content">
        {activeModule === 'chat' ? (
          <>
            <div className="chat-container">
              {messages.map((msg) => (
                <div key={msg.id} className={`message ${msg.role}`}>
                  {msg.role === 'ai' ? <ReactMarkdown>{msg.content}</ReactMarkdown> : msg.content}
                </div>
              ))}
              {isTyping && <div className="message ai typing-indicator"><div className="dot"></div><div className="dot"></div><div className="dot"></div></div>}
            </div>
            <div className="input-area">
              <form className="input-box glass" onSubmit={handleSend}>
                <input type="text" placeholder="Ask anything about your code, notes, or tasks..." value={input || ''} onChange={(e) => setInput(e.target.value)} />
                <button type="submit" className="send-btn" disabled={!input.trim()}><Send size={18} /></button>
              </form>
            </div>
          </>
        ) : activeModule === 'tasks' ? (
          <div style={{ padding: '40px', overflowY: 'auto', flex: 1 }}>
            <h2 style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <CheckSquare size={24} color="var(--primary)" /> Extracted Tasks
            </h2>
            {tasks.length === 0 ? (
              <div style={{ color: '#888' }}>No tasks found. Try asking the agent to create a task in the Chat Workspace!</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {tasks.map(task => (
                  <div key={task.id} className="glass" style={{ padding: '20px', borderRadius: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      <CheckCircle size={20} color={task.status === 'Done' ? '#10b981' : '#888'} />
                      <span style={{ fontSize: '18px', textDecoration: task.status === 'Done' ? 'line-through' : 'none', color: task.status === 'Done' ? '#888' : 'var(--foreground)' }}>{task.title}</span>
                    </div>
                    <div style={{ padding: '6px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: 'bold', background: task.priority === 'High' ? 'rgba(239,68,68,0.2)' : task.priority === 'Medium' ? 'rgba(245,158,11,0.2)' : 'rgba(59,130,246,0.2)', color: task.priority === 'High' ? '#ef4444' : task.priority === 'Medium' ? '#f59e0b' : '#3b82f6' }}>
                      {task.priority} Priority
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : activeModule === 'repo' ? (
          <div style={{ padding: '40px', overflowY: 'auto', flex: 1 }}>
            <h2 style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Database size={24} color="var(--primary)" /> Repo Intelligence
            </h2>
            
            <div className="glass" style={{ padding: '24px', borderRadius: '12px', marginBottom: '32px' }}>
              <h3 style={{ marginTop: 0, marginBottom: '16px' }}>1. Index a Repository</h3>
              <form onSubmit={handleIndexRepo} style={{ display: 'flex', gap: '12px' }}>
                <input type="text" placeholder="https://github.com/user/repo" value={repoUrl || ''} onChange={(e) => setRepoUrl(e.target.value)} style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid var(--surface-border)', background: 'rgba(0,0,0,0.2)', color: 'white' }} />
                <button type="submit" disabled={isIndexing} style={{ padding: '0 24px', borderRadius: '8px', background: 'var(--primary)', color: 'white', border: 'none', cursor: 'pointer' }}>
                  {isIndexing ? 'Indexing...' : 'Index Repo'}
                </button>
              </form>
            </div>

            <div className="glass" style={{ padding: '24px', borderRadius: '12px' }}>
              <h3 style={{ marginTop: 0, marginBottom: '16px' }}>2. Ask Questions</h3>
              <form onSubmit={handleQueryRepo} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <input type="text" placeholder="e.g. How does authentication work in this repo?" value={repoQuery || ''} onChange={(e) => setRepoQuery(e.target.value)} style={{ padding: '12px', borderRadius: '8px', border: '1px solid var(--surface-border)', background: 'rgba(0,0,0,0.2)', color: 'white' }} />
                <button type="submit" disabled={isQuerying} style={{ padding: '12px', borderRadius: '8px', background: 'var(--primary)', color: 'white', border: 'none', cursor: 'pointer' }}>
                  {isQuerying ? 'Querying...' : 'Ask AI'}
                </button>
              </form>
              
              {repoAnswer && (
                <div style={{ marginTop: '24px', padding: '20px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', border: '1px solid var(--surface-border)' }}>
                  <ReactMarkdown>{repoAnswer}</ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div style={{ padding: '40px', overflowY: 'auto', flex: 1 }}>
            <h2 style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Database size={24} color="var(--primary)" /> Personal Knowledge RAG
            </h2>
            
            <div className="glass" style={{ padding: '24px', borderRadius: '12px', marginBottom: '32px' }}>
              <h3 style={{ marginTop: 0, marginBottom: '16px' }}>1. Upload a Document (.pdf, .txt, .md)</h3>
              <form onSubmit={handleUploadKnowledge} style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} style={{ flex: 1, padding: '10px' }} accept=".pdf,.txt,.md" />
                <button type="submit" disabled={isIndexing || !file} style={{ padding: '12px 24px', borderRadius: '8px', background: 'var(--primary)', color: 'white', border: 'none', cursor: 'pointer' }}>
                  {isIndexing ? 'Uploading...' : 'Upload & Index'}
                </button>
              </form>
            </div>

            <div className="glass" style={{ padding: '24px', borderRadius: '12px' }}>
              <h3 style={{ marginTop: 0, marginBottom: '16px' }}>2. Query your Knowledge Base</h3>
              <form onSubmit={handleQueryKnowledge} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <input type="text" placeholder="e.g. What does the uploaded document say about X?" value={knowledgeQuery || ''} onChange={(e) => setKnowledgeQuery(e.target.value)} style={{ padding: '12px', borderRadius: '8px', border: '1px solid var(--surface-border)', background: 'rgba(0,0,0,0.2)', color: 'white' }} />
                <button type="submit" disabled={isQuerying} style={{ padding: '12px', borderRadius: '8px', background: 'var(--primary)', color: 'white', border: 'none', cursor: 'pointer' }}>
                  {isQuerying ? 'Searching...' : 'Search Documents'}
                </button>
              </form>
              
              {knowledgeAnswer && (
                <div style={{ marginTop: '24px', padding: '20px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', border: '1px solid var(--surface-border)' }}>
                  <ReactMarkdown>{knowledgeAnswer}</ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
