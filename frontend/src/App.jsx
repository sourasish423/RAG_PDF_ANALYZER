import React, { useRef, useState } from 'react'

const API_URL = 'http://localhost:8001'
const DEFAULT_FILENAME = 'Project_Overview.pdf'

async function getErrorMessage(response) {
  let body

  try {
    body = await response.json()
  } catch {
    body = null
  }

  const detail = body?.detail
  const message =
    typeof detail === 'string'
      ? detail
      : Array.isArray(detail)
        ? detail.map((item) => item.msg).filter(Boolean).join(', ')
        : body?.message

  return message || `The server returned an error (${response.status}).`
}

function SourceList({ sources }) {
  if (!sources.length) {
    return null
  }

  return (
    <section className="sources" aria-label="Answer sources">
      <h3 className="sources-title">
        <span className="sources-mark" aria-hidden="true">
          ↳
        </span>
        Sources
      </h3>
      <ul className="source-list">
        {sources.map((source, index) => (
          <li className="source-item" key={`${source.filename}-${source.page}-${index}`}>
            <span className="source-file">{source.filename}</span>
            <span className="source-page">Page {source.page}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}

function App() {
  const [file, setFile] = useState(null)
  const [filename, setFilename] = useState(DEFAULT_FILENAME)
  const [documents, setDocuments] = useState([DEFAULT_FILENAME])
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)
  const chatEndRef = useRef(null)

  function handleFileChange(event) {
    const selectedFile = event.target.files?.[0] || null
    setFile(selectedFile)
    setError('')
  }

  async function handleUpload(event) {
    event.preventDefault()
    setError('')

    if (!file) {
      setError('Choose a PDF file to upload.')
      return
    }

    if (
      file.type !== 'application/pdf' &&
      !file.name.toLowerCase().endsWith('.pdf')
    ) {
      setError('That file does not look like a PDF. Please choose a .pdf file.')
      return
    }

    const formData = new FormData()
    formData.append('file', file)
    setUploading(true)

    try {
      const response = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(await getErrorMessage(response))
      }

      const result = await response.json()
      if (typeof result.filename !== 'string' || !result.filename.trim()) {
        throw new Error('The server response did not include a valid filename.')
      }

      setFilename(result.filename)
      setDocuments((currentDocuments) =>
        currentDocuments.includes(result.filename)
          ? currentDocuments
          : [...currentDocuments, result.filename],
      )
      setFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (uploadError) {
      setError(
        uploadError instanceof TypeError
          ? 'Could not reach the backend. Check that it is running at http://localhost:8000.'
          : uploadError.message || 'The PDF could not be uploaded.',
      )
    } finally {
      setUploading(false)
    }
  }

  async function handleAsk(event) {
    event.preventDefault()
    const trimmedQuestion = question.trim()

    if (loading) {
      return
    }
    if (!trimmedQuestion) {
      setError('Type a question before sending it.')
      return
    }
    if (!filename) {
      setError('Select or upload a PDF before asking a question.')
      return
    }

    setError('')
    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: trimmedQuestion,
          filename,
        }),
      })

      if (!response.ok) {
        throw new Error(await getErrorMessage(response))
      }

      const result = await response.json()
      if (typeof result.answer !== 'string') {
        throw new Error('The server response did not include an answer.')
      }

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: `${Date.now()}-${currentMessages.length}`,
          question: trimmedQuestion,
          filename,
          answer: result.answer,
          sources: Array.isArray(result.sources) ? result.sources : [],
        },
      ])
      setQuestion('')
      requestAnimationFrame(() =>
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }),
      )
    } catch (askError) {
      setError(
        askError instanceof TypeError
          ? 'Could not reach the backend. Check that it is running at http://localhost:8000.'
          : askError.message || 'Your question could not be answered.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Papertrail home">
          <span className="brand-icon" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
          <span>papertrail</span>
        </a>
        <div className="topbar-right">
          <span className="topbar-caption">YOUR DOCUMENT, UNDERSTOOD</span>
          <span className="connection-status">
            <span className="status-dot" />
            Local workspace
          </span>
        </div>
      </header>

      <div className="workspace">
        <aside className="sidebar" aria-label="Documents">
          <div className="sidebar-heading">
            <span className="eyebrow">WORKSPACE</span>
            <h1>Documents</h1>
            <p>Your files, ready to explore.</p>
          </div>

          <section className="upload-card" aria-labelledby="upload-title">
            <div className="upload-symbol" aria-hidden="true">
              ↑
            </div>
            <h2 id="upload-title">Add a document</h2>
            <p>Upload a PDF to start asking questions about it.</p>
            <input
              ref={fileInputRef}
              id="pdf-file"
              className="visually-hidden"
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              aria-label="Choose a PDF file"
              disabled={uploading}
            />
            <label className="file-picker" htmlFor="pdf-file">
              {file ? 'Choose a different PDF' : 'Choose PDF'}
            </label>
            {file && <p className="selected-file">{file.name}</p>}
            <button
              className="upload-button"
              type="button"
              onClick={handleUpload}
              disabled={!file || uploading}
            >
              {uploading ? (
                <>
                  <span className="button-spinner" aria-hidden="true" />
                  Uploading…
                </>
              ) : (
                'Upload document'
              )}
            </button>
            <span className="upload-note">PDF files only</span>
          </section>

          <div className="document-section">
            <div className="section-label">
              <span>YOUR LIBRARY</span>
              <span className="document-count">{documents.length}</span>
            </div>
            <div className="document-list" aria-live="polite">
              {documents.map((documentName) => (
                <button
                  className={`document-row${filename === documentName ? ' active' : ''}`}
                  type="button"
                  aria-current={filename === documentName ? 'true' : undefined}
                  key={documentName}
                  onClick={() => setFilename(documentName)}
                >
                  <span className="pdf-icon" aria-hidden="true">
                    PDF
                  </span>
                  <span className="document-info">
                    <span className="document-name" title={documentName}>
                      {documentName}
                    </span>
                    <span className="document-subtitle">
                      {filename === documentName ? 'Selected document' : 'In your library'}
                    </span>
                  </span>
                  {filename === documentName && (
                    <span className="active-indicator" aria-label="Selected" />
                  )}
                </button>
              ))}
            </div>
          </div>

          <div className="sidebar-footer">
            <span className="footer-sparkle" aria-hidden="true">
              ✳
            </span>
            <p>
              Answers are grounded in your document, with page references to help
              you verify.
            </p>
          </div>
        </aside>

        <section className="chat-panel" aria-label="Chat">
          <div className="chat-header">
            <div>
              <span className="eyebrow">DOCUMENT CHAT</span>
              <h2>Ask your document</h2>
            </div>
            <div className="chat-document">
              <span className="chat-document-dot" />
              <span className="chat-document-name" title={filename}>
                {filename}
              </span>
            </div>
          </div>

          <div className="conversation" aria-live="polite" aria-busy={loading}>
            {messages.length === 0 && !loading ? (
              <div className="empty-state">
                <div className="empty-illustration" aria-hidden="true">
                  <div className="illustration-page">
                    <span />
                    <span />
                    <span />
                    <span />
                  </div>
                  <div className="illustration-chat">?</div>
                </div>
                <span className="eyebrow">A LITTLE MORE CLARITY</span>
                <h3>Every good question starts somewhere.</h3>
                <p>
                  Ask about <strong>{filename}</strong> and get a clear answer
                  backed by page references.
                </p>
                <div className="suggestion">
                  <span aria-hidden="true">↗</span>
                  <span>Try: “What is this document about?”</span>
                </div>
              </div>
            ) : (
              <div className="message-list">
                {messages.map((message) => (
                  <article className="conversation-turn" key={message.id}>
                    <div className="user-message">
                      <span className="message-avatar user-avatar" aria-hidden="true">
                        Y
                      </span>
                      <div>
                        <div className="message-meta">
                          <strong>You</strong>
                          <span>{message.filename}</span>
                        </div>
                        <p>{message.question}</p>
                      </div>
                    </div>
                    <div className="assistant-message">
                      <span className="message-avatar assistant-avatar" aria-hidden="true">
                        <span className="brand-icon small">
                          <span />
                          <span />
                          <span />
                        </span>
                      </span>
                      <div className="assistant-content">
                        <div className="message-meta">
                          <strong>Papertrail</strong>
                          <span>Answer</span>
                        </div>
                        <p className="answer-text">{message.answer}</p>
                        <SourceList sources={message.sources} />
                      </div>
                    </div>
                  </article>
                ))}
                {loading && (
                  <div className="assistant-message thinking-message">
                    <span className="message-avatar assistant-avatar" aria-hidden="true">
                      <span className="brand-icon small">
                        <span />
                        <span />
                        <span />
                      </span>
                    </span>
                    <div className="thinking-content" role="status">
                      <span className="thinking-dots">
                        <i />
                        <i />
                        <i />
                      </span>
                      Thinking through your document…
                    </div>
                  </div>
                )}
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {error && (
            <div className="error-banner" role="alert">
              <span className="error-icon" aria-hidden="true">
                !
              </span>
              <span>{error}</span>
              <button
                type="button"
                className="dismiss-error"
                aria-label="Dismiss error"
                onClick={() => setError('')}
              >
                ×
              </button>
            </div>
          )}

          <form className="composer-area" onSubmit={handleAsk}>
            <label className="visually-hidden" htmlFor="question-input">
              Ask a question about {filename}
            </label>
            <div className="composer">
              <textarea
                id="question-input"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault()
                    event.currentTarget.form.requestSubmit()
                  }
                }}
                placeholder="Ask anything about your document…"
                rows={1}
                disabled={loading || uploading}
              />
              <button
                className="send-button"
                type="submit"
                disabled={loading || uploading || !question.trim() || !filename}
                aria-label="Send question"
              >
                <span aria-hidden="true">↑</span>
              </button>
            </div>
            <div className="composer-hint">
              <span>
                <kbd>Enter</kbd> to send <span className="hint-divider">·</span>{' '}
                <kbd>Shift</kbd> + <kbd>Enter</kbd> for a new line
              </span>
              <span className="powered-note">Powered by your local AI</span>
            </div>
          </form>
        </section>
      </div>
    </main>
  )
}

export default App
