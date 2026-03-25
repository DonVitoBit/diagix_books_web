export interface Book {
  id: number;
  title: string;
  source_filename: string | null;
  theme: string | null;
  temperature: number | null;
  include_research: boolean;
  original_text: string | null;
  paraphrased_text: string;
  created_at: string;
  created_by: string;
}

export interface BookVersion {
  id: number;
  book_id: number;
  version_number: number;
  paraphrased_text: string;
  change_note: string | null;
  created_at: string;
  created_by: string;
}

export interface Comment {
  id: number;
  book_id: number;
  author: string;
  comment_text: string;
  paragraph_index: number | null;
  created_at: string;
}

export interface Moderator {
  username: string;
  name: string | null;
  created_at: string;
}
