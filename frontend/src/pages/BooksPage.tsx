import React, { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { MOCK_BOOKS, MOCK_VERSIONS, MOCK_COMMENTS, MOCK_MODERATORS, MOCK_MODERATOR_ACCESS } from "@/data/mockData";
import { Book } from "@/types/models";
import { BookOpen, Download, Save, MessageSquare, History, ChevronDown, ChevronRight, RotateCcw } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const BooksPage: React.FC = () => {
  const { isAdmin, user } = useAuth();
  const [selectedBookId, setSelectedBookId] = useState<number | null>(null);
  const [showVersions, setShowVersions] = useState(false);
  const [showComments, setShowComments] = useState(false);
  const [showText, setShowText] = useState(false);
  const [newComment, setNewComment] = useState("");

  const books = isAdmin
    ? MOCK_BOOKS
    : MOCK_BOOKS.filter((b) => MOCK_MODERATOR_ACCESS[b.id]?.includes(user?.username || ""));

  const selectedBook = books.find((b) => b.id === selectedBookId);
  const versions = MOCK_VERSIONS.filter((v) => v.book_id === selectedBookId);
  const comments = MOCK_COMMENTS.filter((c) => c.book_id === selectedBookId);

  return (
    <div>
      <h1 className="font-display text-2xl font-bold text-foreground mb-6">Книги</h1>

      {/* Book selector */}
      <div className="glass-card rounded-xl p-5 mb-6">
        <label className="block text-sm font-medium text-foreground mb-2">
          {isAdmin ? "Все книги" : "Доступные вам книги"}
        </label>
        <select
          value={selectedBookId ?? ""}
          onChange={(e) => setSelectedBookId(e.target.value ? Number(e.target.value) : null)}
          className="w-full max-w-md px-4 py-2.5 rounded-lg border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="">Выберите книгу...</option>
          {books.map((b) => (
            <option key={b.id} value={b.id}>
              #{b.id} — {b.title}
            </option>
          ))}
        </select>
      </div>

      {/* Selected book details */}
      {selectedBook && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          {/* Book info card */}
          <div className="glass-card rounded-xl p-5">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="font-display text-lg font-semibold text-foreground flex items-center gap-2">
                  <BookOpen size={20} className="text-accent" />
                  {selectedBook.title}
                </h2>
                <div className="flex gap-4 mt-2 text-sm text-muted-foreground">
                  <span>Создана: {new Date(selectedBook.created_at).toLocaleDateString("ru")}</span>
                  <span>Автор: {selectedBook.created_by}</span>
                  {selectedBook.source_filename && <span>Файл: {selectedBook.source_filename}</span>}
                </div>
              </div>
              <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition-opacity">
                <Download size={16} />
                Скачать
              </button>
            </div>

            {isAdmin && (
              <div className="flex items-center gap-2 mt-4 pt-4 border-t border-border">
                <input
                  type="text"
                  defaultValue={selectedBook.title}
                  className="flex-1 max-w-sm px-3 py-2 rounded-lg border border-input bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <button className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-accent text-accent-foreground text-sm font-medium hover:opacity-90 transition-opacity">
                  <Save size={14} />
                  Сохранить название
                </button>
              </div>
            )}
          </div>

          {/* Moderator access (admin) */}
          {isAdmin && (
            <div className="glass-card rounded-xl p-5">
              <h3 className="font-display text-sm font-semibold text-foreground mb-3">Доступ модераторов</h3>
              <div className="space-y-2">
                {MOCK_MODERATORS.map((mod) => (
                  <label key={mod.username} className="flex items-center gap-2 text-sm text-foreground">
                    <input
                      type="checkbox"
                      defaultChecked={MOCK_MODERATOR_ACCESS[selectedBook.id]?.includes(mod.username)}
                      className="rounded border-input text-accent focus:ring-ring"
                    />
                    {mod.name || mod.username}
                  </label>
                ))}
              </div>
              <button className="mt-3 px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition-opacity">
                Сохранить доступ
              </button>
            </div>
          )}

          {/* Text preview */}
          <div className="glass-card rounded-xl overflow-hidden">
            <button
              onClick={() => setShowText(!showText)}
              className="w-full flex items-center justify-between p-5 text-left"
            >
              <h3 className="font-display text-sm font-semibold text-foreground">Переписанный текст</h3>
              {showText ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
            </button>
            <AnimatePresence>
              {showText && (
                <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }} className="overflow-hidden">
                  <div className="px-5 pb-5">
                    <textarea
                      readOnly={isAdmin}
                      defaultValue={selectedBook.paraphrased_text}
                      className="w-full h-[420px] px-4 py-3 rounded-lg border border-input bg-muted text-foreground text-sm font-mono resize-none focus:outline-none"
                    />
                    {!isAdmin && (
                      <button className="mt-3 flex items-center gap-1.5 px-4 py-2 rounded-lg bg-accent text-accent-foreground text-sm font-medium hover:opacity-90 transition-opacity">
                        <Save size={14} />
                        Сохранить правки
                      </button>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Version history */}
          <div className="glass-card rounded-xl overflow-hidden">
            <button
              onClick={() => setShowVersions(!showVersions)}
              className="w-full flex items-center justify-between p-5 text-left"
            >
              <h3 className="font-display text-sm font-semibold text-foreground flex items-center gap-2">
                <History size={16} className="text-accent" />
                История версий ({versions.length})
              </h3>
              {showVersions ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
            </button>
            <AnimatePresence>
              {showVersions && (
                <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }} className="overflow-hidden">
                  <div className="px-5 pb-5 space-y-3">
                    {versions.map((v) => (
                      <div key={v.id} className="p-3 rounded-lg bg-muted">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-foreground">
                            Версия {v.version_number} — {v.change_note}
                          </span>
                          <button className="flex items-center gap-1 text-xs text-accent hover:underline">
                            <RotateCcw size={12} />
                            Восстановить
                          </button>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {new Date(v.created_at).toLocaleString("ru")} · {v.created_by}
                        </p>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Comments */}
          <div className="glass-card rounded-xl overflow-hidden">
            <button
              onClick={() => setShowComments(!showComments)}
              className="w-full flex items-center justify-between p-5 text-left"
            >
              <h3 className="font-display text-sm font-semibold text-foreground flex items-center gap-2">
                <MessageSquare size={16} className="text-accent" />
                Комментарии ({comments.length})
              </h3>
              {showComments ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
            </button>
            <AnimatePresence>
              {showComments && (
                <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }} className="overflow-hidden">
                  <div className="px-5 pb-5 space-y-3">
                    {comments.map((c) => (
                      <div key={c.id} className="p-3 rounded-lg bg-muted">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium text-foreground">{c.author}</span>
                          {c.paragraph_index != null && (
                            <span className="text-xs bg-accent/20 text-accent-foreground px-1.5 py-0.5 rounded">
                              §{c.paragraph_index}
                            </span>
                          )}
                          <span className="text-xs text-muted-foreground ml-auto">
                            {new Date(c.created_at).toLocaleString("ru")}
                          </span>
                        </div>
                        <p className="text-sm text-foreground">{c.comment_text}</p>
                      </div>
                    ))}
                    <div className="flex gap-2 mt-2">
                      <input
                        value={newComment}
                        onChange={(e) => setNewComment(e.target.value)}
                        placeholder="Написать комментарий..."
                        className="flex-1 px-3 py-2 rounded-lg border border-input bg-background text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                      />
                      <button className="px-3 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition-opacity">
                        Отправить
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      )}

      {!selectedBook && books.length === 0 && (
        <div className="text-center py-16 text-muted-foreground">
          <BookOpen size={48} className="mx-auto mb-3 opacity-30" />
          <p>Нет доступных книг</p>
        </div>
      )}
    </div>
  );
};

export default BooksPage;
