import React, { useState } from "react";
import { Upload, Image as ImageIcon, ChevronLeft, ChevronRight, Wand2, Search } from "lucide-react";
import { motion } from "framer-motion";

const MOCK_IMAGES = Array.from({ length: 6 }, (_, i) => ({
  id: i + 1,
  label: `Изображение ${i + 1}`,
  category: i % 2 === 0 ? "clinical" : "encyclopedia",
}));

const ImagesPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [extracted, setExtracted] = useState(false);
  const [currentImage, setCurrentImage] = useState(0);
  const [prompt, setPrompt] = useState("");
  const [enhancePrompt, setEnhancePrompt] = useState(false);

  const handleExtract = () => {
    if (!file) return;
    setExtracted(true);
    setCurrentImage(0);
  };

  return (
    <div>
      <h1 className="font-display text-2xl font-bold text-foreground mb-6">Автоматическая иллюстрация книги</h1>

      {/* Upload */}
      <div className="glass-card rounded-xl p-6 mb-6">
        <label className="flex flex-col items-center justify-center w-full h-32 rounded-lg border-2 border-dashed border-input bg-muted/30 cursor-pointer hover:bg-muted/60 transition-colors">
          <Upload size={24} className="text-muted-foreground mb-2" />
          <span className="text-sm text-muted-foreground">
            {file ? `${file.name} (${(file.size / 1024 / 1024).toFixed(1)} МБ)` : "Загрузите PDF файл"}
          </span>
          <input type="file" accept=".pdf" onChange={(e) => { setFile(e.target.files?.[0] || null); setExtracted(false); }} className="hidden" />
        </label>
        <div className="flex items-center gap-4 mt-4">
          <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
            <input type="checkbox" defaultChecked className="rounded border-input text-accent focus:ring-ring" />
            Извлечь изображения из загруженной книги
          </label>
          <button
            onClick={handleExtract}
            disabled={!file}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-40"
          >
            <Search size={16} />
            Извлечь изображения
          </button>
        </div>
      </div>

      {/* Extracted images */}
      {extracted && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
          {/* Summary */}
          <div className="glass-card rounded-xl p-5">
            <h2 className="font-display text-base font-semibold text-foreground mb-2">Сводка</h2>
            <div className="flex gap-6 text-sm text-muted-foreground">
              <span>Всего: <strong className="text-foreground">{MOCK_IMAGES.length}</strong></span>
              <span>Clinical: <strong className="text-foreground">{MOCK_IMAGES.filter(i => i.category === "clinical").length}</strong></span>
              <span>Encyclopedia: <strong className="text-foreground">{MOCK_IMAGES.filter(i => i.category === "encyclopedia").length}</strong></span>
            </div>
          </div>

          {/* Image viewer */}
          <div className="glass-card rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display text-base font-semibold text-foreground">Просмотр изображений</h2>
              <span className="text-sm text-muted-foreground">{currentImage + 1} из {MOCK_IMAGES.length}</span>
            </div>
            <div className="flex items-center gap-4">
              <button onClick={() => setCurrentImage(Math.max(0, currentImage - 1))} disabled={currentImage === 0} className="p-2 rounded-lg bg-muted hover:bg-secondary transition-colors disabled:opacity-30">
                <ChevronLeft size={20} />
              </button>
              <div className="flex-1 aspect-video rounded-lg bg-muted flex items-center justify-center">
                <div className="text-center text-muted-foreground">
                  <ImageIcon size={48} className="mx-auto mb-2 opacity-30" />
                  <p className="text-sm">{MOCK_IMAGES[currentImage].label}</p>
                  <p className="text-xs">Категория: {MOCK_IMAGES[currentImage].category}</p>
                </div>
              </div>
              <button onClick={() => setCurrentImage(Math.min(MOCK_IMAGES.length - 1, currentImage + 1))} disabled={currentImage === MOCK_IMAGES.length - 1} className="p-2 rounded-lg bg-muted hover:bg-secondary transition-colors disabled:opacity-30">
                <ChevronRight size={20} />
              </button>
            </div>
          </div>

          {/* Redraw */}
          <div className="glass-card rounded-xl p-5">
            <h2 className="font-display text-base font-semibold text-foreground mb-3">Перерисовка</h2>
            <label className="flex items-center gap-2 text-sm text-foreground mb-3 cursor-pointer">
              <input type="checkbox" checked={enhancePrompt} onChange={(e) => setEnhancePrompt(e.target.checked)} className="rounded border-input text-accent focus:ring-ring" />
              Улучшить промпт с помощью AI
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Опишите, как перерисовать изображение..."
              className="w-full h-24 px-3 py-2.5 rounded-lg border border-input bg-background text-foreground text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none mb-3"
            />
            <div className="flex gap-2">
              <button className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition-opacity">
                <Wand2 size={14} />
                Перерисовать заново
              </button>
              <button className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-accent text-accent-foreground text-sm font-medium hover:opacity-90 transition-opacity">
                Улучшить через NanoBanana Pro
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default ImagesPage;
