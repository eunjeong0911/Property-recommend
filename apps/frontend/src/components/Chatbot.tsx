'use client'

import { useState, useEffect, useRef } from 'react'
import { sendChatQuestion } from '../api/chatApi'
import ReactMarkdown from 'react-markdown'

interface Message {
  id: string
  type: 'user' | 'ai'
  content: string
  timestamp: Date
}

interface ChatSession {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
  updatedAt: Date
}

interface ChatbotProps {
  onRecommendLands?: (landIds: number[]) => void
}

export default function Chatbot({ onRecommendLands }: ChatbotProps = {}) {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showHistoryModal, setShowHistoryModal] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 초기 마운트 시 저장된 세션 복원
  useEffect(() => {
    const savedSessions = localStorage.getItem('chatSessions')
    const savedCurrentId = localStorage.getItem('currentSessionId')

    if (!savedSessions) return

    const parsed: ChatSession[] = JSON.parse(savedSessions).map((session: any) => ({
      ...session,
      createdAt: new Date(session.createdAt),
      updatedAt: new Date(session.updatedAt),
      messages: session.messages.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp),
      })),
    }))

    setSessions(parsed)

    if (savedCurrentId) {
      setCurrentSessionId(savedCurrentId)
      const current = parsed.find(s => s.id === savedCurrentId)
      if (current) {
        setMessages(current.messages)
      }
    }
  }, [])

  // 세션 변경 시 LocalStorage 반영
  useEffect(() => {
    if (sessions.length === 0) {
      localStorage.removeItem('chatSessions')
      return
    }
    localStorage.setItem('chatSessions', JSON.stringify(sessions))
  }, [sessions])

  // 현재 세션 ID 변경 시 LocalStorage 반영
  useEffect(() => {
    if (currentSessionId) {
      localStorage.setItem('currentSessionId', currentSessionId)
    }
  }, [currentSessionId])

  // 메시지 변경 시 자동 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const formatTime = (date: Date) => {
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    return `${hours}:${minutes}`
  }

  const formatDate = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const diffDays = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return '오늘'
    if (diffDays === 1) return '어제'
    if (diffDays < 7) return `${diffDays}일 전`

    return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })
  }

  // 새 채팅 세션 생성 (+ 버튼)
  const startNewChat = () => {
    const newId = Date.now().toString()

    const newSession: ChatSession = {
      id: newId,
      title: '새 대화',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    }

    setSessions(prev => [newSession, ...prev])
    setCurrentSessionId(newId)
    setMessages([])
  }

  // 메시지 전송
  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    let sessionId = currentSessionId

    // 세션이 없으면 자동으로 새 세션 생성
    if (!sessionId) {
      sessionId = Date.now().toString()
      const newSession: ChatSession = {
        id: sessionId,
        title: '새 대화',
        messages: [],
        createdAt: new Date(),
        updatedAt: new Date(),
      }
      setSessions(prev => [newSession, ...prev])
      setCurrentSessionId(sessionId)
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      const answer = await sendChatQuestion(userMessage.content, sessionId)

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: answer,
        timestamp: new Date(),
      }

      setMessages(prev => [...prev, aiMessage])

      // AI 응답에서 /landDetail/{id} 형태의 링크를 찾아 매물 ID 추천
      if (onRecommendLands) {
        const landIds = [...answer.matchAll(/\/landDetail\/(\d+)/g)]
          .map(match => Number(match[1]))
          .filter(Boolean)

        if (landIds.length > 0) {
          onRecommendLands(landIds)
        }
      }
    } catch (error) {
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 2).toString(),
          type: 'ai',
          content: '응답 중 오류가 발생했습니다. 다시 시도해주세요.',
          timestamp: new Date(),
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  // 메시지 변경 시 세션 내용/제목 업데이트
  useEffect(() => {
    if (!currentSessionId || messages.length === 0) return

    setSessions(prev =>
      prev.map(session =>
        session.id === currentSessionId
          ? {
            ...session,
            messages,
            updatedAt: new Date(),
            title:
              session.title === '새 대화'
                ? messages[0].content.slice(0, 30) +
                (messages[0].content.length > 30 ? '...' : '')
                : session.title,
          }
          : session,
      ),
    )
  }, [messages, currentSessionId])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // 과거 세션 선택
  const handleSelectSession = (sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId)
    if (!session) return
    setCurrentSessionId(sessionId)
    setMessages(session.messages)
    setShowHistoryModal(false)
  }

  // 과거 세션 삭제
  const handleDeleteSession = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm('이 대화를 삭제하시겠습니까?')) return

    setSessions(prev => {
      const filtered = prev.filter(s => s.id !== sessionId)

      if (currentSessionId === sessionId) {
        setCurrentSessionId(null)
        setMessages([])
      }

      return filtered
    })
  }

  return (
    <>
      <div className="flex flex-col h-full bg-white rounded-xl border"
        style={{ height: 'calc(100vh - 120px)' }}
      >

        {/* 헤더 */}
        <div className="flex justify-between p-4 border-b">
          <h2 className="text-lg font-bold">매물 추천 챗봇</h2>

          <div className="flex items-center gap-2">
            {/* 새 채팅(+ 버튼) */}
            <button
              onClick={startNewChat}
              className="w-9 h-9 flex items-center justify-center rounded-full border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)] transition-colors"
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M12 5v14M5 12h14" strokeLinecap="round" />
              </svg>
            </button>

            {/* 과거 대화보기 버튼 */}
            <button
              onClick={() => setShowHistoryModal(true)}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-[var(--color-text-secondary)] border border-[var(--color-border)] rounded-lg hover:bg-[var(--color-bg-hover)] transition-colors"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 20 20"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M10 18C14.4183 18 18 14.4183 18 10C18 5.58172 14.4183 2 10 2C5.58172 2 2 5.58172 2 10C2 14.4183 5.58172 18 10 18Z"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  d="M10 6V10L13 13"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              채팅 내역
            </button>
          </div>
        </div>

        {/* 메시지 영역 */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && !isLoading ? (
            /* 초기 화면 - 환영 메시지 및 추천 질문 */
            <div className="flex flex-col items-center justify-center h-full space-y-6">
              {/* 환영 메시지 */}
              <div className="text-center">
                <h3 className="text-2xl font-bold text-[var(--color-primary)] mb-2">안녕하세요!</h3>
                <p className="text-sm text-[var(--color-text-secondary)]">AI 매물 상담사가 도와드릴게요</p>
              </div>

              {/* 추천 질문 버튼 */}
              <div className="flex flex-wrap gap-3 justify-center max-w-md">
                <button
                  onClick={() => {
                    const question = '강남 원룸 추천해줘';
                    setInputValue(question);
                    handleSendMessage();
                  }}
                  className="px-4 py-2 bg-white border-2 border-purple-200 text-purple-600 rounded-full text-sm font-medium hover:bg-purple-50 hover:border-purple-300 transition-all shadow-sm"
                >
                  강남 원룸 추천해줘
                </button>
                <button
                  onClick={() => {
                    const question = '전세 매물 알려줘';
                    setInputValue(question);
                    handleSendMessage();
                  }}
                  className="px-4 py-2 bg-white border-2 border-purple-200 text-purple-600 rounded-full text-sm font-medium hover:bg-purple-50 hover:border-purple-300 transition-all shadow-sm"
                >
                  전세 매물 알려줘
                </button>
                <button
                  onClick={() => {
                    const question = '교통 좋은 곳 어디야?';
                    setInputValue(question);
                    handleSendMessage();
                  }}
                  className="px-4 py-2 bg-white border-2 border-purple-200 text-purple-600 rounded-full text-sm font-medium hover:bg-purple-50 hover:border-purple-300 transition-all shadow-sm"
                >
                  교통 좋은 곳 어디야?
                </button>
              </div>
            </div>
          ) : (
            /* 기존 메시지 표시 */
            <>
              {messages.map(message => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                >
                  <div
                    className={`max-w-[75%] p-4 rounded-lg ${message.type === 'user'
                      ? 'bg-[#16375B] text-white'
                      : 'bg-gray-100'
                      }`}
                  >
                    {message.type === 'ai' ? (
                      <div className="prose prose-sm max-w-none">
                        <ReactMarkdown>{message.content}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-sm whitespace-pre-wrap break-words">
                        {message.content}
                      </p>
                    )}
                    <p className="text-xs mt-2 text-gray-500">
                      {formatTime(message.timestamp)}
                    </p>
                  </div>
                </div>
              ))}

              {isLoading && (
                <p className="text-sm text-gray-400">AI가 답변을 생성 중입니다...</p>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* 입력 영역 */}
        <div className="p-4 border-t flex gap-2">
          <input
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 border rounded px-3 py-2 text-sm"
            placeholder="궁금한 매물 정보를 물어보세요"
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading || !inputValue.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50 text-sm"
          >
            전송
          </button>
        </div>
      </div>

      {/* 과거 대화 모달 */}
      {showHistoryModal && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/70 backdrop-blur-md"
            onClick={() => setShowHistoryModal(false)}
          />
          <div className="relative bg-white rounded-xl shadow-[var(--shadow-xl)] w-full max-w-2xl max-h-[80vh] flex flex-col z-[10000]">
            <div className="flex items-center justify-between p-6 border-b">
              <h3 className="text-xl font-semibold text-[var(--color-primary)]">
                과거 대화 내역
              </h3>
              <button
                onClick={() => setShowHistoryModal(false)}
                className="p-2 hover:bg-[var(--color-bg-hover)] rounded-lg transition-colors"
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M18 6L6 18M6 6L18 18"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </svg>
              </button>
            </div>
            <div className="p-6 overflow-y-auto">
              {sessions.length === 0 ? (
                <p className="text-sm text-[var(--color-text-tertiary)] text-center py-8">
                  저장된 대화가 없습니다
                </p>
              ) : (
                <div className="space-y-3">
                  {sessions.map(session => (
                    <div
                      key={session.id}
                      onClick={() => handleSelectSession(session.id)}
                      className={`p-4 rounded-lg cursor-pointer transition-colors border ${currentSessionId === session.id
                        ? 'bg-blue-50 border-[var(--color-primary)]'
                        : 'bg-white hover:bg-[var(--color-bg-hover)] border-[var(--color-border-light)]'
                        }`}
                    >
                      <div className="flex justify-between items-start gap-3">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-[var(--color-text-primary)] truncate">
                            {session.title}
                          </p>
                          <p className="text-xs text-[var(--color-text-tertiary)] mt-1">
                            {formatDate(session.updatedAt)}
                          </p>
                        </div>
                        <button
                          onClick={e => handleDeleteSession(session.id, e)}
                          className="flex-shrink-0 text-[var(--color-text-tertiary)] hover:text-red-600 transition-colors p-1"
                        >
                          <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                            />
                          </svg>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )
      }
    </>
  )
}
