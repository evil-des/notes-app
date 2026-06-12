import { describe, expect, it } from 'vitest';
import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { LangProvider, useLang } from './i18n.jsx';

function Probe() {
  const { lang, setLang, t } = useLang();
  return (
    <div>
      <span data-testid="lang">{lang}</span>
      <span data-testid="title">{t('auth.loginTitle')}</span>
      <span data-testid="count">{t('notes.deleteSelected', { count: 3 })}</span>
      <span data-testid="telegram">{t('settings.telegramTitle')}</span>
      <button onClick={() => setLang('ru')}>switch</button>
    </div>
  );
}

describe('i18n', () => {
  it('resolves English strings by default', () => {
    render(
      <LangProvider>
        <Probe />
      </LangProvider>
    );
    expect(screen.getByTestId('lang')).toHaveTextContent('en');
    expect(screen.getByTestId('title')).toHaveTextContent('Welcome back');
    expect(screen.getByTestId('telegram')).toHaveTextContent('Telegram reminders');
  });

  it('interpolates {count} placeholders', () => {
    render(
      <LangProvider>
        <Probe />
      </LangProvider>
    );
    expect(screen.getByTestId('count')).toHaveTextContent('Delete (3)');
  });

  it('switches language and persists to localStorage', async () => {
    const user = userEvent.setup();
    render(
      <LangProvider>
        <Probe />
      </LangProvider>
    );
    await act(() => user.click(screen.getByText('switch')));
    expect(screen.getByTestId('lang')).toHaveTextContent('ru');
    expect(screen.getByTestId('title')).toHaveTextContent('С возвращением');
    expect(screen.getByTestId('telegram')).toHaveTextContent('Telegram-напоминания');
    expect(localStorage.getItem('notes_lang')).toBe('ru');
  });
});
