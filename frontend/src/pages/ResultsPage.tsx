import React, { useState } from "react";
import { MOCK_BOOKS } from "@/data/mockData";
import { ChevronDown, ChevronRight, Download, Plus, AlertTriangle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const ResultsPage: React.FC = () => {
  const [expandedBook, setExpandedBook] = useState<number | null>(null);

  return (
    <div>
      <h1 className="font-display text-2xl font-bold text-foreground mb-6">Результаты перефразирования</h1>

      {/* Latest file result */}
      <div className="glass-card rounded-xl p-5 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="font-display text-base font-semibold text-foreground">Результат из файла</h2>
            <p className="text-xs text-muted-foreground mt-0.5">Последний результат перефразирования</p>
          </div>
          <button className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-accent text-accent-foreground text-sm font-medium hover:opacity-90 transition-opacity">
            <Plus size={14} />
            Добавить в книги
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h3 className="text-xs font-medium text-muted-foreground mb-2">Оригинальный текст</h3>
            <textarea
              readOnly
              value="Нейрохирургия — раздел хирургии, занимающийся вопросами оперативного лечения заболеваний нервной системы..."
              className="w-full h-[200px] px-3 py-2.5 rounded-lg border border-input bg-muted text-foreground text-sm font-mono resize-none"
            />
          </div>
          <div>
            <h3 className="text-xs font-medium text-muted-foreground mb-2">Перефразированный текст</h3>
            <textarea
              readOnly
              value="Нейрохирургическая дисциплина представляет собой специализированную область хирургической медицины..."
              className="w-full h-[200px] px-3 py-2.5 rounded-lg border border-input bg-muted text-foreground text-sm font-mono resize-none"
            />
          </div>
        </div>
      </div>

      {/* All books */}
      <h2 className="font-display text-base font-semibold text-foreground mb-3">Все переписанные книги</h2>
      <div className="space-y-3">
        {MOCK_BOOKS.map((book) => (
          <div key={book.id} className="glass-card rounded-xl overflow-hidden">
            <button
              onClick={() => setExpandedBook(expandedBook === book.id ? null : book.id)}
              className="w-full flex items-center justify-between p-4 text-left"
            >
              <div className="flex items-center gap-3">
                {expandedBook === book.id ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                <span className="text-sm font-medium text-foreground">
                  {book.title} — {new Date(book.created_at).toLocaleDateString("ru")} ({book.created_by})
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button className="p-1.5 rounded-lg hover:bg-muted transition-colors" title="Скачать">
                  <Download size={14} className="text-muted-foreground" />
                </button>
              </div>
            </button>
            <AnimatePresence>
              {expandedBook === book.id && (
                <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }} className="overflow-hidden">
                  <div className="px-4 pb-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div>
                        <h4 className="text-xs font-medium text-muted-foreground mb-1.5">Оригинал</h4>
                        <textarea
                          readOnly
                          value={book.original_text || "Оригинал недоступен"}
                          className="w-full h-[180px] px-3 py-2 rounded-lg border border-input bg-muted text-foreground text-xs font-mono resize-none"
                        />
                      </div>
                      <div>
                        <h4 className="text-xs font-medium text-muted-foreground mb-1.5">Перефразированный</h4>
                        <textarea
                          readOnly
                          value={book.paraphrased_text}
                          className="w-full h-[180px] px-3 py-2 rounded-lg border border-input bg-muted text-foreground text-xs font-mono resize-none"
                        />
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ResultsPage;
