/**
 * Chatbot 컴포넌트
 *
 * AI 챗봇 인터페이스를 담당하는 컴포넌트
 *
 * 주요 기능:
 * - 사용자 메시지 입력 및 전송
 *      - 입력창
 *      - 전송 버튼
 *      - 시간 표시
 * - AI 응답 표시(대화창)
 *      - 로딩 상태 표시
 *      - 시간 표시
 * - 대화 히스토리 관리
 *      - 이전 대화 불러오기
 *      - 대화 내용 스크롤 관리
 *      - 대화 내용 자동 스크롤
 *      - 최신 대화 내용 맨 위로
 * - 챗봇 아이콘 클릭 시 챗봇 열기/닫기 애니메이션
 * - 대화 세션 관리
 *      - 여러 대화 세션 저장 및 불러오기
 *      - 세션 전환
 *      - 세션 삭제
 */

'use client'

import { useState, useEffect, useRef } from 'react'
import { sendChatQuestion } from '../api/chatApi'

interface Message {
  id: string
  type: 'user' | 'ai'
  content: string
  timestamp: Date
  feedback?: 'like' | 'dislike' | null
}

interface ChatSession {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
  updatedAt: Date
}

export default function Chatbot() {
  const [isOpen, setIsOpen] = useState(false)
  const [showSidebar, setShowSidebar] = useState(false)
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const chatContainerRef = useRef<HTMLDivElement>(null)

  // 컴포넌트 마운트 시 세션 불러오기
  useEffect(() => {
    const savedSessions = localStorage.getItem('chatSessions')
    const savedCurrentSessionId = localStorage.getItem('currentSessionId')

    if (savedSessions) {
      const parsed = JSON.parse(savedSessions)
      const sessionsWithDates = parsed.map((session: any) => ({
        ...session,
        createdAt: new Date(session.createdAt),
        updatedAt: new Date(session.updatedAt),
        messages: session.messages.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }))
      }))
      setSessions(sessionsWithDates)

      if (savedCurrentSessionId) {
        setCurrentSessionId(savedCurrentSessionId)
        const currentSession = sessionsWithDates.find((s: ChatSession) => s.id === savedCurrentSessionId)
        if (currentSession) {
          setMessages(currentSession.messages)
        }
      }
    }
  }, [])

  // 세션 저장
  useEffect(() => {
    if (sessions.length > 0) {
      localStorage.setItem('chatSessions', JSON.stringify(sessions))
    }
  }, [sessions])

  // 현재 세션 ID 저장
  useEffect(() => {
    if (currentSessionId) {
      localStorage.setItem('currentSessionId', currentSessionId)
    }
  }, [currentSessionId])

  // 메시지 변경 시 현재 세션 업데이트
  useEffect(() => {
    if (currentSessionId && messages.length > 0) {
      setSessions(prev => prev.map(session =>
        session.id === currentSessionId
          ? {
              ...session,
              messages,
              updatedAt: new Date(),
              title: session.title === '새 대화'
                ? messages[0]?.content.slice(0, 30) + (messages[0]?.content.length > 30 ? '...' : '')
                : session.title
            }
          : session
      ))
    }
  }, [messages, currentSessionId])

  // 대화 내용 자동 스크롤
  useEffect(() => {
    if (messagesEndRef.current && isOpen) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isOpen])

  // 시간 포맷 함수
  const formatTime = (date: Date) => {
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    return `${hours}:${minutes}`
  }

  // 날짜 포맷 함수
  const formatDate = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const diffDays = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return '오늘'
    if (diffDays === 1) return '어제'
    if (diffDays < 7) return `${diffDays}일 전`

    return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })
  }

  // 메시지 전송 핸들러
  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    // 현재 세션이 없으면 새 세션 생성
    if (!currentSessionId) {
      handleNewChat()
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      // Real API call
      const answer = await sendChatQuestion(inputValue.trim())

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: answer,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('AI 응답 오류:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: '죄송합니다. 응답 중 오류가 발생했습니다. 다시 시도해주세요.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  // Enter 키로 메시지 전송
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // 새 채팅 시작 핸들러
  const handleNewChat = () => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: '새 대화',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date()
    }

    setSessions(prev => [newSession, ...prev])
    setCurrentSessionId(newSession.id)
    setMessages([])
    setInputValue('')
    setShowSidebar(false)
  }

  // 세션 선택 핸들러
  const handleSelectSession = (sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId)
    if (session) {
      setCurrentSessionId(sessionId)
      setMessages(session.messages)
      setShowSidebar(false)
    }
  }

  // 세션 삭제 핸들러
  const handleDeleteSession = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()

    if (confirm('이 대화를 삭제하시겠습니까?')) {
      setSessions(prev => {
        const filtered = prev.filter(s => s.id !== sessionId)

        // 삭제된 세션이 현재 세션이면 초기화
        if (currentSessionId === sessionId) {
          setCurrentSessionId(null)
          setMessages([])
        }

        // 세션이 모두 삭제되면 localStorage도 정리
        if (filtered.length === 0) {
          localStorage.removeItem('chatSessions')
          localStorage.removeItem('currentSessionId')
        }

        return filtered
      })
    }
  }

  // 피드백 핸들러
  const handleFeedback = (messageId: string, feedbackType: 'like' | 'dislike') => {
    setMessages(prev => prev.map(msg =>
      msg.id === messageId
        ? { ...msg, feedback: msg.feedback === feedbackType ? null : feedbackType }
        : msg
    ))
  }

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* 챗봇 플로팅 버튼 - 화려한 디자인 */}
      <div
        className={`
          flex flex-col items-end gap-2
          transition-all duration-300
          ${isOpen ? 'scale-0 opacity-0 pointer-events-none' : 'scale-100 opacity-100'}
        `}
      >
        {/* 말풍선 문구 */}
        <div className="relative animate-bounce-slow">
          <div className="bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-500 text-white px-4 py-2 rounded-2xl shadow-lg text-sm font-semibold whitespace-nowrap">
            <span className="mr-1">✨</span>
            취향저격 AI 매물추천
            <span className="ml-1">🏠</span>
          </div>
          {/* 말풍선 꼬리 */}
          <div className="absolute -bottom-2 right-6 w-4 h-4 bg-gradient-to-br from-blue-600 to-cyan-500 rotate-45 rounded-sm"></div>
        </div>
        
        {/* 챗봇 아이콘 버튼 */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="
            relative w-16 h-16 rounded-full
            bg-gradient-to-br from-purple-600 via-blue-600 to-cyan-500
            text-white shadow-2xl
            flex items-center justify-center
            hover:scale-110 hover:shadow-purple-500/50
            transition-all duration-300
            group
          "
          aria-label="챗봇 열기"
        >
          {/* 글로우 이펙트 */}
          <div className="absolute inset-0 rounded-full bg-gradient-to-br from-purple-400 via-blue-400 to-cyan-400 opacity-0 group-hover:opacity-50 blur-xl transition-opacity duration-300"></div>
          {/* 펄스 링 애니메이션 */}
          <div className="absolute inset-0 rounded-full border-2 border-white/30 animate-ping"></div>
          <div className="absolute inset-[-4px] rounded-full border-2 border-purple-400/50 animate-pulse"></div>
          {/* 아이콘 */}
          <svg
            className="w-8 h-8 relative z-10 drop-shadow-lg"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
          {/* 스파클 이펙트 */}
          <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full animate-pulse shadow-lg shadow-yellow-400/50"></div>
        </button>
      </div>

      {/* 챗봇 창 */}
      <div
        className={`
          absolute bottom-0 right-0
          w-[500px] h-[650px] rounded-2xl shadow-2xl
          flex flex-col overflow-hidden
          transition-all duration-300 ease-in-out
          border border-white/20
          ${isOpen
            ? 'scale-100 opacity-100 pointer-events-auto'
            : 'scale-0 opacity-0 pointer-events-none origin-bottom-right'
          }
        `}
      >
        {/* 헤더 - 그라데이션 적용 */}
        <div className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-500 text-white">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="hover:bg-white/20 rounded-lg p-1.5 transition-colors"
              aria-label="대화 목록"
              title="대화 목록 토글"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d={showSidebar ? "M5 15l7-7 7 7" : "M19 9l-7 7-7-7"}
                />
              </svg>
            </button>
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse shadow-lg shadow-green-400/50"></div>
            <h3 className="font-bold text-lg">🏠 AI 매물 상담</h3>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleNewChat}
              className="hover:bg-white/20 rounded-lg px-2 py-1.5 transition-colors text-sm"
              aria-label="새 채팅"
              title="새 채팅"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="hover:bg-white/20 rounded-full p-1.5 transition-colors"
              aria-label="챗봇 닫기"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>

        {/* 대화 목록 - 토글 영역 */}
        <div
          className={`
            ${showSidebar ? 'max-h-32' : 'max-h-0'}
            transition-all duration-300 ease-in-out
            overflow-hidden
            bg-gray-50
            border-b border-gray-200
          `}
        >
          <div className="p-3 overflow-y-auto" style={{ maxHeight: '128px' }}>
            {sessions.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">
                저장된 대화가 없습니다
              </p>
            ) : (
              <div className="space-y-2">
                {sessions.map(session => (
                  <div
                    key={session.id}
                    onClick={() => handleSelectSession(session.id)}
                    className={`
                      p-2 rounded-lg cursor-pointer
                      transition-colors
                      ${currentSessionId === session.id
                        ? 'bg-blue-100 border border-blue-300'
                        : 'bg-white hover:bg-gray-100 border border-gray-200'
                      }
                    `}
                  >
                    <div className="flex justify-between items-start gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-gray-800 truncate">
                          {session.title}
                        </p>
                        <p className="text-[10px] text-gray-500 mt-0.5">
                          {formatDate(session.updatedAt)}
                        </p>
                      </div>
                      <button
                        onClick={(e) => handleDeleteSession(session.id, e)}
                        className="flex-shrink-0 text-gray-400 hover:text-red-600 transition-colors"
                        aria-label="대화 삭제"
                      >
                        <svg
                          className="w-3.5 h-3.5"
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

        {/* 대화창 */}
        <div
          ref={chatContainerRef}
          className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-slate-50 to-blue-50/30"
        >
          {messages.length === 0 ? (
            <div className="text-center mt-8 space-y-4">
              <div className="w-20 h-20 mx-auto bg-gradient-to-br from-purple-100 to-blue-100 rounded-full flex items-center justify-center">
                <span className="text-4xl">🏠</span>
              </div>
              <div>
                <p className="text-lg font-semibold text-slate-700">안녕하세요!</p>
                <p className="text-slate-500 text-sm mt-1">AI 매물 상담사가 도와드릴게요</p>
              </div>
              <div className="flex flex-wrap justify-center gap-2 mt-4">
                {['강남 원룸 추천해줘', '전세 매물 알려줘', '교통 좋은 곳 어디야?'].map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => setInputValue(suggestion)}
                    className="px-3 py-1.5 bg-white border border-purple-200 text-purple-600 rounded-full text-xs hover:bg-purple-50 hover:border-purple-300 transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[80%] ${message.type === 'ai' ? 'space-y-2' : ''}`}>
                  <div
                    className={`
                      rounded-2xl p-3 shadow-sm
                      ${message.type === 'user'
                        ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white'
                        : 'bg-white text-gray-800 border border-gray-100 shadow-md'
                      }
                    `}
                  >
                    <p className="text-sm whitespace-pre-wrap break-words">
                      {message.content}
                    </p>
                    <p
                      className={`
                        text-xs mt-1
                        ${message.type === 'user' ? 'text-blue-100' : 'text-gray-500'}
                      `}
                    >
                      {formatTime(message.timestamp)}
                    </p>
                  </div>

                  {/* AI 메시지에만 피드백 버튼 표시 */}
                  {message.type === 'ai' && (
                    <div className="flex gap-2 px-1">
                      <button
                        onClick={() => handleFeedback(message.id, 'like')}
                        className={`
                          p-1 rounded transition-colors
                          ${message.feedback === 'like'
                            ? 'text-blue-600 bg-blue-50'
                            : 'text-gray-400 hover:text-blue-600 hover:bg-blue-50'
                          }
                        `}
                        aria-label="좋아요"
                        title="좋아요"
                      >
                        <svg
                          className="w-4 h-4"
                          fill={message.feedback === 'like' ? 'currentColor' : 'none'}
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"
                          />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleFeedback(message.id, 'dislike')}
                        className={`
                          p-1 rounded transition-colors
                          ${message.feedback === 'dislike'
                            ? 'text-red-600 bg-red-50'
                            : 'text-gray-400 hover:text-red-600 hover:bg-red-50'
                          }
                        `}
                        aria-label="싫어요"
                        title="싫어요"
                      >
                        <svg
                          className="w-4 h-4"
                          fill={message.feedback === 'dislike' ? 'currentColor' : 'none'}
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5"
                          />
                        </svg>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {/* 로딩 상태 표시 */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white text-gray-800 border border-gray-100 rounded-2xl p-4 shadow-md">
                <div className="flex items-center gap-3">
                  <div className="flex gap-1">
                    <div className="w-2.5 h-2.5 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2.5 h-2.5 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2.5 h-2.5 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                  <span className="text-sm text-slate-500 font-medium">AI가 답변을 준비 중...</span>
                </div>
              </div>
            </div>
          )}

          {/* 스크롤 타겟 */}
          <div ref={messagesEndRef} />
        </div>

        {/* 입력창 */}
        <div className="p-4 border-t border-gray-100 bg-white">
          <div className="flex gap-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="궁금한 매물 정보를 물어보세요..."
              disabled={isLoading}
              className="
                flex-1 px-4 py-3 border border-gray-200 rounded-xl
                focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent
                disabled:bg-gray-100 disabled:cursor-not-allowed
                text-sm bg-gray-50
              "
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              className="
                px-5 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl
                hover:from-purple-700 hover:to-blue-700 transition-all
                disabled:from-gray-300 disabled:to-gray-300 disabled:cursor-not-allowed
                font-semibold text-sm shadow-lg shadow-purple-500/25
                hover:shadow-purple-500/40
              "
              aria-label="메시지 전송"
            >
              전송
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
