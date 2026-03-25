import React, { useState } from "react";
import { MOCK_MODERATORS, MOCK_BOOKS, MOCK_MODERATOR_ACCESS } from "@/data/mockData";
import { UserPlus, Trash2, Save, ChevronDown, ChevronRight, Lock } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const ModeratorsPage: React.FC = () => {
  const [expandedMod, setExpandedMod] = useState<string | null>(null);
  const [newName, setNewName] = useState("");
  const [newLogin, setNewLogin] = useState("");
  const [newPass, setNewPass] = useState("");
  const [newPassConfirm, setNewPassConfirm] = useState("");
  const [createError, setCreateError] = useState("");

  const handleCreate = () => {
    setCreateError("");
    if (newLogin.length < 3 || newLogin.length > 32) { setCreateError("Логин: 3–32 символа"); return; }
    if (!/^[a-zA-Z0-9._-]+$/.test(newLogin)) { setCreateError("Только латиница, цифры, . _ -"); return; }
    if (newLogin === "admin") { setCreateError("Логин admin зарезервирован"); return; }
    if (newPass.length < 6) { setCreateError("Пароль: минимум 6 символов"); return; }
    if (newPass !== newPassConfirm) { setCreateError("Пароли не совпадают"); return; }
    // Mock create
    setNewName(""); setNewLogin(""); setNewPass(""); setNewPassConfirm("");
  };

  return (
    <div>
      <h1 className="font-display text-2xl font-bold text-foreground mb-6">Модераторы</h1>

      <div className="max-w-3xl space-y-6">
        {/* Create moderator */}
        <div className="glass-card rounded-xl p-5">
          <h2 className="font-display text-base font-semibold text-foreground mb-4 flex items-center gap-2">
            <UserPlus size={18} className="text-accent" />
            Создать модератора
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Имя</label>
              <input value={newName} onChange={(e) => setNewName(e.target.value)} className="w-full px-3 py-2 rounded-lg border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Логин</label>
              <input value={newLogin} onChange={(e) => setNewLogin(e.target.value)} placeholder="3–32, латиница" className="w-full px-3 py-2 rounded-lg border border-input bg-background text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Пароль</label>
              <input type="password" value={newPass} onChange={(e) => setNewPass(e.target.value)} className="w-full px-3 py-2 rounded-lg border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Повторите пароль</label>
              <input type="password" value={newPassConfirm} onChange={(e) => setNewPassConfirm(e.target.value)} className="w-full px-3 py-2 rounded-lg border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
            </div>
          </div>
          {createError && (
            <p className="text-sm text-destructive mt-2">{createError}</p>
          )}
          <button onClick={handleCreate} className="mt-4 flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition-opacity">
            <UserPlus size={16} />
            Создать
          </button>
        </div>

        {/* Moderator list */}
        <div>
          <h2 className="font-display text-base font-semibold text-foreground mb-3">Список модераторов</h2>
          <div className="space-y-3">
            {MOCK_MODERATORS.map((mod) => (
              <div key={mod.username} className="glass-card rounded-xl overflow-hidden">
                <button
                  onClick={() => setExpandedMod(expandedMod === mod.username ? null : mod.username)}
                  className="w-full flex items-center justify-between p-4 text-left"
                >
                  <div>
                    <span className="text-sm font-medium text-foreground">{mod.name || mod.username}</span>
                    <span className="text-xs text-muted-foreground ml-2">@{mod.username}</span>
                    <span className="text-xs text-muted-foreground ml-2">
                      · {new Date(mod.created_at).toLocaleDateString("ru")}
                    </span>
                  </div>
                  {expandedMod === mod.username ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                </button>
                <AnimatePresence>
                  {expandedMod === mod.username && (
                    <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }} className="overflow-hidden">
                      <div className="px-4 pb-4 space-y-4">
                        {/* Change password */}
                        <div className="p-3 rounded-lg bg-muted">
                          <h4 className="text-xs font-medium text-foreground mb-2 flex items-center gap-1">
                            <Lock size={12} />
                            Сменить пароль
                          </h4>
                          <div className="flex gap-2">
                            <input type="password" placeholder="Новый пароль" className="flex-1 px-3 py-1.5 rounded-lg border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
                            <input type="password" placeholder="Повторить" className="flex-1 px-3 py-1.5 rounded-lg border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
                            <button className="px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-xs font-medium hover:opacity-90 transition-opacity">
                              <Save size={12} />
                            </button>
                          </div>
                        </div>

                        {/* Book access */}
                        <div className="p-3 rounded-lg bg-muted">
                          <h4 className="text-xs font-medium text-foreground mb-2">Доступ к книгам</h4>
                          <div className="space-y-1.5">
                            {MOCK_BOOKS.map((b) => (
                              <label key={b.id} className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                                <input
                                  type="checkbox"
                                  defaultChecked={MOCK_MODERATOR_ACCESS[b.id]?.includes(mod.username)}
                                  className="rounded border-input text-accent focus:ring-ring"
                                />
                                #{b.id} — {b.title}
                              </label>
                            ))}
                          </div>
                          <button className="mt-2 px-3 py-1.5 rounded-lg bg-accent text-accent-foreground text-xs font-medium hover:opacity-90 transition-opacity">
                            Сохранить доступ
                          </button>
                        </div>

                        <button className="flex items-center gap-1.5 text-sm text-destructive hover:underline">
                          <Trash2 size={14} />
                          Удалить модератора
                        </button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModeratorsPage;
