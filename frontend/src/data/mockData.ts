import { Book, BookVersion, Comment, Moderator } from "@/types/models";

export const MOCK_BOOKS: Book[] = [
  {
    id: 1,
    title: "Основы нейрохирургии",
    source_filename: "neurosurgery_basics.pdf",
    theme: "Нейрохирургия",
    temperature: 0.4,
    include_research: true,
    original_text: "Нейрохирургия — раздел хирургии, занимающийся вопросами оперативного лечения заболеваний нервной системы. Нейрохирургия как медицинская специальность возникла в начале XX века...",
    paraphrased_text: "Нейрохирургическая дисциплина представляет собой специализированную область хирургической медицины, ориентированную на оперативные вмешательства при патологиях нервной системы. Становление нейрохирургии как самостоятельного медицинского направления произошло в начале двадцатого столетия...",
    created_at: "2025-03-01T10:30:00Z",
    created_by: "admin",
  },
  {
    id: 2,
    title: "Патологическая анатомия",
    source_filename: "pathological_anatomy.docx",
    theme: "Патанатомия",
    temperature: 0.3,
    include_research: false,
    original_text: "Патологическая анатомия — научно-прикладная дисциплина, изучающая патологические процессы и болезни с помощью научного, главным образом микроскопического, исследования изменений...",
    paraphrased_text: "Патологическая анатомия является научно-практической дисциплиной, предметом изучения которой выступают патологические процессы и заболевания посредством научного исследования...",
    created_at: "2025-02-15T14:20:00Z",
    created_by: "admin",
  },
  {
    id: 3,
    title: "Клиническая фармакология",
    source_filename: "clinical_pharma.pdf",
    theme: "Фармакология",
    temperature: 0.5,
    include_research: true,
    original_text: null,
    paraphrased_text: "Клиническая фармакология изучает воздействие лекарственных средств на организм больного человека...",
    created_at: "2025-01-20T09:00:00Z",
    created_by: "moderator",
  },
];

export const MOCK_VERSIONS: BookVersion[] = [
  { id: 1, book_id: 1, version_number: 1, paraphrased_text: "Первая версия...", change_note: "Начальная версия", created_at: "2025-03-01T10:30:00Z", created_by: "admin" },
  { id: 2, book_id: 1, version_number: 2, paraphrased_text: "Вторая версия с правками...", change_note: "Правки модератора", created_at: "2025-03-05T15:00:00Z", created_by: "moderator" },
];

export const MOCK_COMMENTS: Comment[] = [
  { id: 1, book_id: 1, author: "moderator", comment_text: "Нужно уточнить терминологию в 3-м абзаце", paragraph_index: 3, created_at: "2025-03-02T11:00:00Z" },
  { id: 2, book_id: 1, author: "admin", comment_text: "Согласен, поправлю", paragraph_index: 3, created_at: "2025-03-02T14:00:00Z" },
];

export const MOCK_MODERATORS: Moderator[] = [
  { username: "moderator", name: "Иван Петров", created_at: "2025-01-10T09:00:00Z" },
  { username: "editor1", name: "Мария Сидорова", created_at: "2025-02-20T10:00:00Z" },
];

export const MOCK_MODERATOR_ACCESS: Record<number, string[]> = {
  1: ["moderator"],
  2: ["moderator", "editor1"],
  3: ["editor1"],
};
