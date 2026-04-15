import React from 'react'

interface CardProps {
  children: React.ReactNode
  className?: string
  hover?: boolean
}

export const Card: React.FC<CardProps> = ({ children, className = '', hover = false }) => {
  const hoverStyles = hover
    ? 'hover:border-indigo-500/50 hover:shadow-xl hover:shadow-indigo-500/10 transition-all duration-300'
    : ''

  return (
    <div
      className={`rounded-xl border border-gray-800 bg-gray-900 p-6 ${hoverStyles} ${className}`}
    >
      {children}
    </div>
  )
}
