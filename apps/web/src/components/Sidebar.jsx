import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Bell, HeartPulse, LogOut, Menu, Moon, Sun, Users, X, BookOpen } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { useTheme } from "../hooks/useTheme";

const NAV = [
  { to: "/", label: "Project overview", icon: BookOpen, exact: true },
  { to: "/patients", label: "Patients", icon: Users, exact: false },
  { to: "/alerts", label: "Alerts", icon: Bell, exact: false },
];

function Brand() {
  return (
    <div className="flex items-center gap-2.5 px-5 py-5">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent text-white">
        <HeartPulse size={18} />
      </div>
      <div className="min-w-0 leading-tight">
        <div className="truncate text-sm font-bold text-ink-primary">ECG Context Guard</div>
        <div className="truncate text-[11px] text-ink-muted">Semantic attack detection</div>
      </div>
    </div>
  );
}

function NavLinks({ onNavigate }) {
  const location = useLocation();
  return (
    <nav className="flex flex-1 flex-col gap-1 px-3">
      {NAV.map(({ to, label, icon: Icon, exact }) => {
        const active = exact ? location.pathname === to : location.pathname.startsWith(to);
        return (
          <Link
            key={to}
            to={to}
            onClick={onNavigate}
            className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
              active ? "bg-accent-wash text-accent" : "text-ink-secondary hover:bg-accent-wash/60 hover:text-ink-primary"
            }`}
          >
            <Icon size={18} />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

function SidebarFooter() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <div className="border-t border-border px-3 py-3">
      <button
        onClick={toggleTheme}
        className="mb-1 flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-ink-secondary hover:bg-accent-wash/60"
      >
        {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
        {theme === "light" ? "Dark mode" : "Light mode"}
      </button>
      <div className="flex items-center justify-between rounded-lg px-3 py-2">
        <div className="truncate text-sm text-ink-secondary">{user?.name}</div>
        <button onClick={handleLogout} title="Log out" className="shrink-0 text-ink-muted hover:text-critical">
          <LogOut size={16} />
        </button>
      </div>
    </div>
  );
}

export function Sidebar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      {/* Mobile top bar */}
      <div className="sticky top-0 z-30 flex items-center justify-between border-b border-border bg-surface px-4 py-3 md:hidden">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-white">
            <HeartPulse size={16} />
          </div>
          <span className="text-sm font-bold text-ink-primary">ECG Context Guard</span>
        </div>
        <button onClick={() => setMobileOpen(true)} className="text-ink-secondary" aria-label="Open menu">
          <Menu size={22} />
        </button>
      </div>

      {/* Mobile slide-over */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMobileOpen(false)} />
          <div className="absolute inset-y-0 left-0 flex w-72 flex-col bg-surface">
            <div className="flex items-center justify-between">
              <Brand />
              <button onClick={() => setMobileOpen(false)} className="mr-4 text-ink-muted" aria-label="Close menu">
                <X size={20} />
              </button>
            </div>
            <NavLinks onNavigate={() => setMobileOpen(false)} />
            <SidebarFooter />
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-border bg-surface md:flex">
        <Brand />
        <NavLinks />
        <SidebarFooter />
      </aside>
    </>
  );
}
