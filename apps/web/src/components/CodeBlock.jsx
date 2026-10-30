import { Highlight, themes } from "prism-react-renderer";

/**
 * Renders a verbatim excerpt from the running codebase with syntax highlighting.
 * Always dark-themed (the common "code editor" convention) so it doesn't need
 * to track the site's own light/dark toggle.
 */
export function CodeBlock({ code, language = "python", filename }) {
  return (
    <div className="overflow-hidden rounded-xl border border-border shadow-card">
      {filename && (
        <div className="flex items-center justify-between border-b border-white/10 bg-[#011627] px-4 py-2">
          <span className="font-mono-figures text-xs text-slate-300">{filename}</span>
          <span className="rounded bg-white/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
            {language}
          </span>
        </div>
      )}
      <Highlight theme={themes.nightOwl} code={code.trim()} language={language}>
        {({ className, style, tokens, getLineProps, getTokenProps }) => (
          <pre className={`${className} overflow-x-auto p-4 text-xs leading-relaxed`} style={{ ...style, margin: 0 }}>
            {tokens.map((line, i) => {
              const { key: lineKey, ...lineProps } = getLineProps({ line });
              return (
                <div key={i} {...lineProps}>
                  {line.map((token, key) => {
                    const { key: tokenKey, ...tokenProps } = getTokenProps({ token });
                    return <span key={key} {...tokenProps} />;
                  })}
                </div>
              );
            })}
          </pre>
        )}
      </Highlight>
    </div>
  );
}
