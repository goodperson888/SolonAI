'use client'

export default function GlobalError() {
  return (
    <html lang="zh-CN">
      <head>
        <title>500 - 服务器错误</title>
      </head>
      <body style={{ margin: 0, padding: 0, fontFamily: 'system-ui, sans-serif' }}>
        <div
          style={{
            display: 'flex',
            minHeight: '100vh',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(to bottom right, #111827, #312e81, #581c87)',
          }}
        >
          <div style={{ textAlign: 'center', padding: '1rem' }}>
            <h1
              style={{
                fontSize: '3.75rem',
                fontWeight: 'bold',
                color: 'white',
                marginBottom: '1rem',
              }}
            >
              500
            </h1>
            <h2
              style={{
                fontSize: '1.5rem',
                fontWeight: '600',
                color: '#e5e7eb',
                marginBottom: '1rem',
              }}
            >
              服务器错误
            </h2>
            <p style={{ color: '#9ca3af', marginBottom: '2rem' }}>抱歉，服务器遇到了问题</p>
            <a
              href="/"
              style={{
                display: 'inline-block',
                padding: '0.75rem 1.5rem',
                backgroundColor: '#4f46e5',
                color: 'white',
                borderRadius: '0.5rem',
                textDecoration: 'none',
                transition: 'background-color 0.2s',
              }}
            >
              返回首页
            </a>
          </div>
        </div>
      </body>
    </html>
  )
}
