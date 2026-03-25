import React, { useState } from "react";
import { Key, Save, X, Check, AlertCircle, ChevronDown, ChevronRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface ApiKeyBlockProps {
  label: string;
  saved: boolean;
  masked?: string;
}

const ApiKeyBlock: React.FC<ApiKeyBlockProps> = ({ label, saved, masked }) => {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState("");

  return (
    <div className="p-4 rounded-lg bg-muted/50 border border-border">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Key size={16} className="text-accent" />
          <span className="text-sm font-medium text-foreground">{label}</span>
        </div>
        {saved ? (
          <span className="flex items-center gap-1 text-xs text-success">
            <Check size={12} />
            Сохранён
          </span>
        ) : (
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <AlertCircle size={12} />
            Не установлен
          </span>
        )}
      </div>
      {saved && !editing && (
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground font-mono">{masked || "sk-...xxxx"}</span>
          <div className="flex gap-1.5">
            <button onClick={() => setEditing(true)} className="text-xs text-accent hover:underline">Изменить</button>
            <button className="text-xs text-destructive hover:underline">Удалить</button>
          </div>
        </div>
      )}
      {(!saved || editing) && (
        <div className="flex gap-2 mt-2">
          <input
            type="password"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Введите API ключ"
            className="flex-1 px-3 py-2 rounded-lg border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <button className="px-3 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition-opacity">
            <Save size={14} />
          </button>
          {editing && (
            <button onClick={() => setEditing(false)} className="px-3 py-2 rounded-lg bg-muted text-muted-foreground text-sm hover:bg-secondary transition-colors">
              <X size={14} />
            </button>
          )}
        </div>
      )}
    </div>
  );
};

const SettingsPage: React.FC = () => {
  const [provider, setProvider] = useState<"openai" | "deepseek">("openai");
  const [temperature, setTemperature] = useState(0.4);
  const [showHelp, setShowHelp] = useState(false);
  const [showErrors, setShowErrors] = useState(false);

  return (
    <div>
      <h1 className="font-display text-2xl font-bold text-foreground mb-6">Настройки и информация</h1>

      <div className="space-y-6 max-w-3xl">
        {/* LLM Provider */}
        <div className="glass-card rounded-xl p-5">
          <h2 className="font-display text-base font-semibold text-foreground mb-3">Провайдер LLM</h2>
          <div className="flex gap-4">
            {(["openai", "deepseek"] as const).map((p) => (
              <label key={p} className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                <input
                  type="radio"
                  name="provider"
                  checked={provider === p}
                  onChange={() => setProvider(p)}
                  className="text-accent focus:ring-ring"
                />
                {p === "openai" ? "OpenAI (ChatGPT)" : "DeepSeek"}
              </label>
            ))}
          </div>
        </div>

        {/* API Keys */}
        <div className="glass-card rounded-xl p-5">
          <h2 className="font-display text-base font-semibold text-foreground mb-4">API ключи</h2>
          <div className="space-y-3">
            <ApiKeyBlock label="OpenAI API" saved={true} masked="sk-...9f3x" />
            <ApiKeyBlock label="DeepSeek API" saved={false} />
            <ApiKeyBlock label="DALL-E 2" saved={true} masked="sk-...2d1a" />
            <ApiKeyBlock label="NanoBanana" saved={false} />
            <ApiKeyBlock label="Tavily Search" saved={false} />
            <ApiKeyBlock label="Google Custom Search" saved={true} masked="AIza...8xQ2" />
          </div>
        </div>

        {/* Temperature */}
        <div className="glass-card rounded-xl p-5">
          <h2 className="font-display text-base font-semibold text-foreground mb-3">Параметры обработки</h2>
          <label className="block text-sm font-medium text-foreground mb-1.5">
            Temperature: {temperature.toFixed(1)}
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={temperature}
            onChange={(e) => setTemperature(Number(e.target.value))}
            className="w-full max-w-sm accent-accent"
          />
          <p className="text-xs text-muted-foreground mt-1">
            0.0–0.3 — точный перевод · 0.4–0.6 — баланс · 0.7–1.0 — творческий подход
          </p>
        </div>

        {/* Help */}
        <div className="glass-card rounded-xl overflow-hidden">
          <button onClick={() => setShowHelp(!showHelp)} className="w-full flex items-center justify-between p-5 text-left">
            <h2 className="font-display text-base font-semibold text-foreground">Инструкции по использованию</h2>
            {showHelp ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
          </button>
          <AnimatePresence>
            {showHelp && (
              <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }} className="overflow-hidden">
                <div className="px-5 pb-5 text-sm text-foreground space-y-2">
                  <p>1. Загрузите файл (PDF, TXT, MD, DOCX) в разделе «Перефразирование».</p>
                  <p>2. Укажите тему текста и настройте temperature.</p>
                  <p>3. Нажмите «Начать перефразирование» и дождитесь завершения.</p>
                  <p>4. Результат доступен на вкладке «Результаты» и может быть сохранён как книга.</p>
                  <p>5. Модераторы могут редактировать и комментировать доступные им книги.</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Common errors */}
        <div className="glass-card rounded-xl overflow-hidden">
          <button onClick={() => setShowErrors(!showErrors)} className="w-full flex items-center justify-between p-5 text-left">
            <h2 className="font-display text-base font-semibold text-foreground">Возможные проблемы</h2>
            {showErrors ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
          </button>
          <AnimatePresence>
            {showErrors && (
              <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }} className="overflow-hidden">
                <div className="px-5 pb-5 text-sm text-foreground space-y-2">
                  <p><strong>Ошибка API:</strong> Проверьте корректность ключа и лимиты.</p>
                  <p><strong>Файл не загружается:</strong> Максимальный размер — 10 МБ. Поддерживаются PDF, TXT, MD, DOCX.</p>
                  <p><strong>Обработка прервана:</strong> Частичный результат автоматически сохраняется.</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
