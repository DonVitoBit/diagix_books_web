import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import {
  BookOpen,
  FileText,
  ClipboardList,
  Image,
  Settings,
  Users,
  LogOut,
  Sparkles,
} from "lucide-react";
import { motion } from "framer-motion";

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
  adminOnly?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { path: "/books", label: "Книги", icon: <BookOpen size={20} /> },
  { path: "/paraphrasing", label: "Перефразирование", icon: <FileText size={20} />, adminOnly: true },
  { path: "/results", label: "Результаты", icon: <ClipboardList size={20} />, adminOnly: true },
  { path: "/images", label: "Иллюстрации", icon: <Image size={20} />, adminOnly: true },
  { path: "/settings", label: "Настройки", icon: <Settings size={20} />, adminOnly: true },
  { path: "/moderators", label: "Модераторы", icon: <Users size={20} />, adminOnly: true },
];

const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout, isAdmin } = useAuth();
  const location = useLocation();

  const visibleItems = NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 bg-sidebar sidebar-glow flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-sidebar-border">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-accent flex items-center justify-center">
              <Sparkles size={18} className="text-accent-foreground" />
            </div>
            <div>
              <h1 className="font-display text-base font-bold text-sidebar-accent-foreground leading-tight">
                Text Rephraser
              </h1>
              <p className="text-[11px] text-sidebar-foreground leading-tight">
                Обработка текстов
              </p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {visibleItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className="block"
              >
                <div
                  className={`relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? "bg-sidebar-accent text-sidebar-accent-foreground"
                      : "text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
                  }`}
                >
                  {isActive && (
                    <motion.div
                      layoutId="nav-indicator"
                      className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-accent rounded-r-full"
                    />
                  )}
                  {item.icon}
                  {item.label}
                </div>
              </NavLink>
            );
          })}
        </nav>

        {/* User info */}
        <div className="p-4 border-t border-sidebar-border">
          <div className="flex items-center justify-between">
            <div className="min-w-0">
              <p className="text-sm font-medium text-sidebar-accent-foreground truncate">
                {user?.name}
              </p>
              <p className="text-xs text-sidebar-foreground capitalize">
                {user?.role}
              </p>
            </div>
            <button
              onClick={logout}
              className="p-2 rounded-lg text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
              title="Выйти"
            >
              <LogOut size={18} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="p-8 max-w-6xl"
        >
          {children}
        </motion.div>
      </main>
    </div>
  );
};

export default AppLayout;
