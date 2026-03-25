import React, { useState } from "react";
import { FileText, Upload, Play, Download, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";

const ParaphrasingPage: React.FC = () => {
  const [theme, setTheme] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [temperature, setTemperature] = useState(0.4);
  const [includeResearch, setIncludeResearch] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState("");

  const handleStart = () => {
    if (!theme || !file) return;
    setIsRunning(true);
    setProgress(0);
    setStage("Извлечение текста...");
    // Mock progress
    const stages = ["Извлечение текста...", "Перефразирование блоков...", "Финализация..."];
    let i = 0;
    const timer = setInterval(() => {
      i++;
      setProgress(Math.min(i * 12, 100));
      setStage(stages[Math.min(Math.floor(i / 3), stages.length - 1)]);
      if (i >= 9) {
        clearInterval(timer);
        setIsRunning(false);
        setProgress(100);
        setStage("Готово!");
      }
    }, 800);
  };

  return (
    <div>
      <h1 className="font-display text-2xl font-bold text-foreground mb-6">Перефразирование текста</h1>

      {/* Parameters */}
      <div className="glass-card rounded-xl p-6 mb-6">
        <h2 className="font-display text-base font-semibold text-foreground mb-4">Параметры</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">
              Тема текста <span className="text-destructive">*</span>
            </label>
            <input
              type="text"
              value={theme}
              onChange={(e) => setTheme(e.target.value)}
              placeholder="Например: Нейрохирургия"
              className="w-full px-4 py-2.5 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">
              Загрузка файла (PDF, TXT, MD, DOCX, до 10 МБ)
            </label>
            <label className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-dashed border-input bg-muted/50 cursor-pointer hover:bg-muted transition-colors">
              <Upload size={16} className="text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                {file ? file.name : "Выберите файл..."}
              </span>
              <input
                type="file"
                accept=".pdf,.txt,.md,.docx"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="hidden"
              />
            </label>
          </div>
          <div>
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
              className="w-full accent-accent"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>0.0 — точнее</span>
              <span>1.0 — креативнее</span>
            </div>
          </div>
          <div className="flex items-center">
            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
              <input
                type="checkbox"
                checked={includeResearch}
                onChange={(e) => setIncludeResearch(e.target.checked)}
                className="rounded border-input text-accent focus:ring-ring"
              />
              Включить исследование
            </label>
          </div>
        </div>
        <button
          onClick={handleStart}
          disabled={isRunning || !theme || !file}
          className="mt-5 flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-primary-foreground font-medium hover:opacity-90 transition-opacity disabled:opacity-40"
        >
          <Play size={18} />
          Начать перефразирование
        </button>
      </div>

      {/* Progress */}
      {(isRunning || progress === 100) && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <div className="glass-card rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-foreground">{stage}</span>
              <span className="text-sm font-semibold text-accent">{progress}%</span>
            </div>
            <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-accent rounded-full"
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.4 }}
              />
            </div>
          </div>

          {/* Two columns */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="glass-card rounded-xl p-5">
              <h3 className="font-display text-sm font-semibold text-foreground mb-3">Сейчас в работе (оригинал)</h3>
              <div className="h-48 overflow-y-auto rounded-lg bg-muted p-3 text-sm text-foreground font-mono">
                {isRunning
                  ? "Нейрохирургия — раздел хирургии, занимающийся вопросами оперативного лечения заболеваний нервной системы..."
                  : "Обработка завершена."}
              </div>
            </div>
            <div className="glass-card rounded-xl p-5">
              <h3 className="font-display text-sm font-semibold text-foreground mb-3">Накапливаемый результат</h3>
              <div className="h-48 overflow-y-auto rounded-lg bg-muted p-3 text-sm text-foreground font-mono">
                Нейрохирургическая дисциплина представляет собой специализированную область хирургической медицины...
              </div>
            </div>
          </div>

          {progress === 100 && (
            <div className="flex gap-3">
              <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition-opacity">
                <Download size={16} />
                Скачать .md
              </button>
              <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-secondary text-secondary-foreground text-sm font-medium hover:opacity-90 transition-opacity">
                <Download size={16} />
                Скачать .pdf
              </button>
              <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent text-accent-foreground text-sm font-medium hover:opacity-90 transition-opacity">
                <ArrowRight size={16} />
                Перейти к результатам
              </button>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
};

export default ParaphrasingPage;
