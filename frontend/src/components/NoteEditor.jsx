import { useEffect, useImperativeHandle, useRef, useState, forwardRef } from 'react';
import ReactMarkdown from 'react-markdown';
import MarkdownToolbar from './MarkdownToolbar.jsx';
import { useLang } from '../i18n.jsx';

function emptyNote() {
  return { title: '', content: '', tags: [], note_date: null, pinned_at: null, archived_at: null };
}

const NoteEditor = forwardRef(function NoteEditor(
  { note, onSave, onCancel, onDelete, onPin, onArchive, onShare, onUnshare },
  ref,
) {
  const { t } = useLang();
  const [draft, setDraft] = useState(emptyNote());
  const [tagsInput, setTagsInput] = useState('');
  const [copyStatus, setCopyStatus] = useState('');
  const formRef = useRef(null);
  const contentRef = useRef(null);

  useEffect(() => {
    if (note) {
      setDraft({ ...note });
      setTagsInput((note.tags || []).join(', '));
    } else {
      setDraft(emptyNote());
      setTagsInput('');
    }
    setCopyStatus('');
  }, [note]);

  useImperativeHandle(ref, () => ({
    submit: () => formRef.current?.requestSubmit(),
  }));

  const submit = (e) => {
    e.preventDefault();
    const tags = tagsInput
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
    onSave({
      title: draft.title,
      content: draft.content,
      tags,
      note_date: draft.note_date || null,
    });
  };

  const isPersisted = Boolean(note);
  const isPinned = Boolean(draft.pinned_at);
  const isArchived = Boolean(draft.archived_at);
  const shareUrl = note?.share_token
    ? `${window.location.origin}/shared/${note.share_token}`
    : '';

  const copyShareUrl = async () => {
    if (!shareUrl) return;
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopyStatus(t('editor.shareCopied'));
    } catch {
      setCopyStatus(t('editor.shareCopyFailed'));
    }
  };

  return (
    <form ref={formRef} className="editor" onSubmit={submit}>
      <div className="editor-head">
        <input
          className="title"
          placeholder={t('editor.untitled')}
          value={draft.title}
          onChange={(e) => setDraft({ ...draft, title: e.target.value })}
          required
        />
        {isPersisted && (
          <div className="editor-flags">
            <button
              type="button"
              className={`flag-btn ${isPinned ? 'on' : ''}`}
              title={isPinned ? t('editor.unpin') : t('editor.pin')}
              onClick={() => onPin?.(note, !isPinned)}
            >
              {isPinned ? '📌' : '📍'}
            </button>
            <button
              type="button"
              className={`flag-btn ${isArchived ? 'on' : ''}`}
              title={isArchived ? t('editor.unarchive') : t('editor.archive')}
              onClick={() => onArchive?.(note, !isArchived)}
            >
              🗄
            </button>
          </div>
        )}
      </div>
      <div className="meta">
        <label>
          📅 {t('editor.date')}
          <input
            type="date"
            value={draft.note_date || ''}
            onChange={(e) => setDraft({ ...draft, note_date: e.target.value || null })}
          />
        </label>
        <label>
          🏷 {t('editor.tags')}
          <input
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
            placeholder={t('editor.tagsPlaceholder')}
          />
        </label>
      </div>
      {isPersisted && (
        <div className="share-panel">
          <div>
            <strong>{t('editor.shareTitle')}</strong>
            <p>{note.share_token ? t('editor.shareEnabled') : t('editor.shareDisabled')}</p>
          </div>
          {note.share_token ? (
            <>
              <input readOnly value={shareUrl} aria-label={t('editor.shareUrl')} />
              <button type="button" className="btn btn-ghost" onClick={copyShareUrl}>
                {t('editor.shareCopy')}
              </button>
              <button type="button" className="btn btn-danger" onClick={() => onUnshare?.(note)}>
                {t('editor.shareRevoke')}
              </button>
            </>
          ) : (
            <button type="button" className="btn btn-ghost" onClick={() => onShare?.(note)}>
              {t('editor.shareEnable')}
            </button>
          )}
          {copyStatus && <span className="share-status">{copyStatus}</span>}
        </div>
      )}
      <MarkdownToolbar textareaRef={contentRef} />
      <div className="split">
        <textarea
          ref={contentRef}
          className="content"
          placeholder={t('editor.writeHere')}
          value={draft.content}
          onChange={(e) => setDraft({ ...draft, content: e.target.value })}
        />
        <div className="preview">
          <ReactMarkdown>{draft.content || t('editor.previewEmpty')}</ReactMarkdown>
        </div>
      </div>
      <div className="actions">
        <button type="submit" className="btn btn-primary">{t('editor.save')}</button>
        {onCancel && <button type="button" className="btn btn-ghost" onClick={onCancel}>{t('editor.cancel')}</button>}
        <div className="spacer" />
        {note && onDelete && (
          <button
            type="button"
            className="btn btn-danger"
            onClick={() => {
              if (window.confirm(t('editor.confirmDelete'))) onDelete(note.id);
            }}
          >
            {t('editor.delete')}
          </button>
        )}
      </div>
    </form>
  );
});

export default NoteEditor;
