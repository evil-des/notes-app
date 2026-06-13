import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { useParams } from 'react-router-dom';
import { api } from '../api.js';
import { useLang } from '../i18n.jsx';

export default function SharedNote() {
  const { token } = useParams();
  const { t } = useLang();
  const [note, setNote] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    api
      .getSharedNote(token)
      .then((data) => {
        if (alive) setNote(data);
      })
      .catch(() => {
        if (alive) setError(t('shared.notFound'));
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [token, t]);

  if (loading) {
    return (
      <div className="shared-page">
        <div className="shared-note">
          <p className="shared-muted">{t('shared.loading')}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="shared-page">
        <div className="shared-note">
          <h1>{t('shared.unavailableTitle')}</h1>
          <p className="shared-muted">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="shared-page">
      <article className="shared-note">
        <header className="shared-note-head">
          <h1>{note.title}</h1>
          <div className="shared-meta">
            {note.note_date && <span>{t('shared.date')}: {note.note_date}</span>}
            <span>{t('shared.updated')}: {new Date(note.updated_at).toLocaleString()}</span>
          </div>
          {note.tags.length > 0 && (
            <div className="shared-tags">
              {note.tags.map((tag) => <span key={tag}>{tag}</span>)}
            </div>
          )}
        </header>
        <div className="preview shared-content">
          <ReactMarkdown>{note.content || t('shared.empty')}</ReactMarkdown>
        </div>
      </article>
    </div>
  );
}
