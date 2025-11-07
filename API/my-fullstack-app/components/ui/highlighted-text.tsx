interface HighlightedTextProps {
  text: string
  highlights?: Array<{
    path: string
    texts: Array<{
      value: string
      type: 'hit' | 'text'
    }>
  }>
  path: string
  className?: string
}

export function HighlightedText({ text, highlights, path, className = '' }: HighlightedTextProps) {
  // Buscar el highlight para este path específico
  const highlight = highlights?.find((h) => h.path === path)

  if (!highlight || !highlight.texts) {
    return <span className={className}>{text}</span>
  }

  return (
    <span className={className}>
      {highlight.texts.map((segment, index) => (
        segment.type === 'hit' ? (
          <mark
            key={index}
            className="bg-yellow-200 dark:bg-yellow-800 font-semibold px-0.5 rounded"
          >
            {segment.value}
          </mark>
        ) : (
          <span key={index}>{segment.value}</span>
        )
      ))}
    </span>
  )
}