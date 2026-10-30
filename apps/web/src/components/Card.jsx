export function Card({ title, subtitle, icon: Icon, actions, children, className = "", bodyClassName = "p-5" }) {
  return (
    <div className={`rounded-xl border border-border bg-surface shadow-card ${className}`}>
      {(title || actions) && (
        <div className="flex items-center justify-between gap-3 border-b border-border px-5 py-4">
          <div className="flex items-center gap-2.5">
            {Icon && (
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent-wash text-accent">
                <Icon size={15} />
              </div>
            )}
            <div>
              {title && <h2 className="text-sm font-semibold text-ink-primary">{title}</h2>}
              {subtitle && <p className="text-xs text-ink-muted">{subtitle}</p>}
            </div>
          </div>
          {actions}
        </div>
      )}
      <div className={bodyClassName}>{children}</div>
    </div>
  );
}
