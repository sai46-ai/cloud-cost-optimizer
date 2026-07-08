import { useEffect, useState, useRef } from 'react';
import { anomalyService, aiService } from '../services/api';
import { formatCurrency, formatDate } from '../lib/utils';
import { Sparkles, Send, Bot, User, AlertTriangle, AlertCircle, Info, Activity, Check } from 'lucide-react';
import Badge from '../components/ui/Badge';
import PageTransition from '../components/layout/PageTransition';
import { Skeleton, SkeletonChat } from '../components/ui/Skeleton';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';

export default function AIInsights() {
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [messages, setMessages] = useState<{role: 'user'|'assistant', content: string, source?: string, suggestions?: string[], timestamp?: string}[]>([
    {
      role: 'assistant',
      content: "👋 Hi! I'm your AI FinOps Assistant. I can help you understand your AWS costs, analyze anomalies, and find savings opportunities. What would you like to know?",
      source: 'system',
      suggestions: ['Why did EC2 costs spike?', 'How can I reduce costs?', 'Show my current spending'],
      timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [loading, setLoading] = useState(true);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await anomalyService.getAnomalies();
        setAnomalies(data.filter((a: any) => !a.is_resolved));
      } catch {
        // Silently handle error
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  useEffect(() => {
    // Auto-scroll chat
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = async (text: string = input) => {
    if (!text.trim()) return;
    
    const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: text, timestamp: time }]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await aiService.chat(text);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.response,
        source: response.source,
        suggestions: response.suggestions,
        timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
      }]);
    } catch {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "I'm having trouble connecting to the AI service right now. Please try again later.",
        timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch(severity) {
      case 'critical': return <AlertCircle size={20} className="text-danger" />;
      case 'high': return <AlertTriangle size={20} className="text-warning" />;
      case 'medium': return <AlertTriangle size={20} className="text-warning" />;
      default: return <Info size={20} className="text-info" />;
    }
  };

  // Simple markdown parser for chat messages
  const formatMessage = (text: string) => {
    // Bold
    let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Bullet points
    formatted = formatted.replace(/^- (.*)$/gm, '<li>$1</li>');
    // Wrap consecutive lists in ul
    formatted = formatted.replace(/(<li>.*<\/li>(\n)?)+/g, '<ul class="list-disc pl-5 my-2">$&</ul>');
    // Paragraphs
    formatted = formatted.replace(/\n\n/g, '<br/><br/>');
    
    return <div dangerouslySetInnerHTML={{ __html: formatted }} />;
  };

  if (loading) {
    return (
      <div className="h-[calc(100vh-140px)] flex flex-col md:flex-row gap-6">
        {/* Active Anomalies Panel skeleton */}
        <div className="w-full md:w-1/3 flex flex-col gap-6 h-full overflow-hidden">
          <div className="space-y-2">
            <Skeleton className="h-8 w-[150px]" />
            <Skeleton className="h-4 w-[220px]" />
          </div>
          <Card className="flex-1 flex flex-col">
            <CardContent className="p-4 space-y-4">
              <Skeleton className="h-6 w-[120px]" />
              <div className="space-y-3">
                <Skeleton className="h-20 w-full rounded-lg" />
                <Skeleton className="h-20 w-full rounded-lg" />
                <Skeleton className="h-20 w-full rounded-lg" />
              </div>
            </CardContent>
          </Card>
        </div>
        {/* Chat skeleton */}
        <Card className="w-full md:w-2/3 flex flex-col h-full">
          <CardContent className="p-4 space-y-4 flex flex-col h-full">
            <div className="flex items-center gap-3 border-b border-border-primary pb-4">
              <Skeleton className="w-10 h-10 rounded-xl" />
              <div className="space-y-2">
                <Skeleton className="h-4 w-[120px]" />
                <Skeleton className="h-3 w-[60px]" />
              </div>
            </div>
            <div className="flex-1 flex flex-col justify-between">
              <SkeletonChat />
              <div className="space-y-2 pt-4">
                <Skeleton className="h-10 w-full rounded-lg" />
                <Skeleton className="h-3 w-[250px] mx-auto" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <PageTransition className="min-h-[calc(100vh-140px)] md:h-[calc(100vh-140px)] flex flex-col md:flex-row gap-6">
      {/* Active Anomalies Panel */}
      <div className="w-full md:w-1/3 flex flex-col gap-6 h-auto md:h-full shrink-0">
        <div>
          <h2 className="text-3xl font-bold tracking-tight mb-2">AI Insights</h2>
          <p className="text-text-secondary font-medium mb-0">Anomaly detection and AI assistant.</p>
        </div>

        <Card className="flex-1 flex flex-col overflow-hidden">
          <CardHeader className="pb-3 border-b border-border-primary flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Activity size={16} /> Active Anomalies
            </CardTitle>
            <Badge variant="critical">{anomalies.length}</Badge>
          </CardHeader>
          
          <CardContent className="overflow-y-auto flex-1 p-2">
            {anomalies.length > 0 ? (
              <div className="flex flex-col gap-3">
                {anomalies.map(anomaly => (
                  <div key={anomaly.id} className="p-3 rounded-lg bg-background-elevated border border-border-primary hover:border-accent-primary/50 transition-colors cursor-pointer" onClick={() => handleSend(`Tell me more about the anomaly on ${anomaly.service}`)}>
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2">
                        {getSeverityIcon(anomaly.severity)}
                        <span className="font-semibold text-sm">{anomaly.service}</span>
                      </div>
                      <Badge variant={anomaly.severity === 'critical' ? 'critical' : anomaly.severity === 'high' ? 'high' : 'warning'}>
                        {anomaly.severity}
                      </Badge>
                    </div>
                    <div className="text-xs text-text-secondary mb-2 line-clamp-2">
                      {anomaly.root_cause}
                    </div>
                    <div className="flex justify-between items-end">
                      <span className="text-xs text-text-muted">{formatDate(anomaly.date)}</span>
                      <span className="text-sm font-bold text-danger">+{formatCurrency(anomaly.impact_amount)}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-text-muted text-center p-6">
                <Check size={32} className="text-success mb-2" />
                <p>No active anomalies detected.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* AI Chat Interface */}
      <Card className="w-full md:w-2/3 flex flex-col h-[500px] md:h-full p-0 overflow-hidden relative">
        <div className="p-4 border-b border-border-primary bg-background-card flex items-center gap-3 z-10">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-[#FAFAFA] shadow-lg shadow-indigo-500/20">
            <Sparkles size={20} />
          </div>
          <div>
            <h3 className="font-semibold text-text-primary">CloudWise FinOps AI</h3>
            <p className="text-xs text-text-secondary flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-success"></span> Online
            </p>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4 relative bg-background-primary scrollbar-thin scrollbar-thumb-border-primary scrollbar-track-transparent">
          {/* Decorative background */}
          <div className="absolute inset-0 z-0 opacity-[0.02] pointer-events-none flex items-center justify-center">
             <Sparkles size={200} />
          </div>

          <div className="z-10 flex flex-col gap-4 relative">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex gap-3 ${msg.role === 'assistant' ? 'justify-start' : 'justify-end'} animate-slide-in`}>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1 bg-accent-primary/10 text-accent-primary">
                    <Bot size={16} />
                  </div>
                )}
                
                <div className={`flex flex-col gap-2 max-w-[80%] ${msg.role === 'assistant' ? 'items-start' : 'items-end'}`}>
                  <div className={`px-4 py-3 rounded-2xl text-[15px] leading-relaxed shadow-sm ${
                    msg.role === 'assistant' 
                      ? 'bg-background-card border border-border-primary text-text-primary rounded-tl-sm' 
                      : 'bg-accent-primary text-white rounded-tr-sm'
                  }`}>
                    {msg.role === 'assistant' ? formatMessage(msg.content) : msg.content}
                  </div>
                  
                  {/* Suggestions (only on the last assistant message) */}
                  {msg.suggestions && idx === messages.length - 1 && (
                    <div className="flex flex-wrap gap-2 mt-2 animate-fade-in" style={{animationDelay: '0.3s'}}>
                      {msg.suggestions.map((suggestion, sIdx) => (
                        <button 
                          key={sIdx} 
                          className="px-3 py-1.5 rounded-full text-xs font-medium border border-border-primary bg-background-card text-text-secondary hover:text-accent-primary hover:border-accent-primary/30 hover:bg-accent-primary/5 transition-colors shadow-sm"
                          onClick={() => handleSend(suggestion)}
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  )}
                  
                  <div className="flex items-center gap-2 mt-0.5 px-1">
                    {msg.timestamp && (
                      <span className="text-[10px] text-text-muted font-medium">{msg.timestamp}</span>
                    )}
                    {msg.source && msg.role === 'assistant' && (
                      <>
                        <span className="text-[10px] text-text-muted">•</span>
                        <span className="text-[10px] text-text-muted font-medium">
                          Powered by {msg.source === 'ai' ? 'OpenAI' : msg.source === 'system' ? 'System Guide' : 'CloudWise KB'}
                        </span>
                      </>
                    )}
                  </div>
                </div>

                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1 bg-background-elevated text-text-primary border border-border-primary">
                    <User size={16} />
                  </div>
                )}
              </div>
            ))}
            
            {isTyping && (
              <div className="flex gap-3 justify-start animate-fade-in">
                <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1 bg-accent-primary/10 text-accent-primary">
                  <Bot size={16} />
                </div>
                <div className="px-4 py-3 rounded-2xl bg-background-card border border-border-primary rounded-tl-sm flex items-center gap-1 min-w-[60px] shadow-sm">
                  <div className="w-1.5 h-1.5 rounded-full bg-text-muted animate-bounce" style={{animationDelay: '0ms'}}></div>
                  <div className="w-1.5 h-1.5 rounded-full bg-text-muted animate-bounce" style={{animationDelay: '150ms'}}></div>
                  <div className="w-1.5 h-1.5 rounded-full bg-text-muted animate-bounce" style={{animationDelay: '300ms'}}></div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="p-4 border-t border-border-primary bg-background-card z-10">
          <form 
            className="relative flex items-center"
            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
          >
            <input 
              type="text" 
              className="w-full h-12 pl-4 pr-12 rounded-xl border border-border-primary bg-background-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary/50 focus:border-accent-primary transition-all shadow-sm placeholder:text-text-muted" 
              placeholder="Ask me about your AWS costs or optimization..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isTyping}
            />
            <button 
              type="submit" 
              className={`absolute right-2 p-2 rounded-lg transition-colors ${input.trim() ? 'bg-accent-primary text-[#FAFAFA] hover:bg-accent-primary/90' : 'text-text-muted hover:bg-background-elevated'}`}
              disabled={!input.trim() || isTyping}
            >
              <Send size={18} />
            </button>
          </form>
          <div className="text-center text-[11px] text-text-muted mt-3 font-medium">
            AI responses may vary. Please verify configuration changes in the AWS Console.
          </div>
        </div>
      </Card>
    </PageTransition>
  );
}
