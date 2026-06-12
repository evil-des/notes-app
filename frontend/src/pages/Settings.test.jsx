import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import Settings from './Settings.jsx';
import { setToken } from '../auth.js';
import { LangProvider } from '../i18n.jsx';

function renderSettings() {
  return render(
    <MemoryRouter>
      <LangProvider>
        <Settings />
      </LangProvider>
    </MemoryRouter>,
  );
}

describe('Settings Telegram reminders', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders Telegram connection state and saves changed notification settings', async () => {
    const user = userEvent.setup();
    setToken('token');
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((url, options = {}) => {
      if (url === '/api/account/settings' && options.method === 'GET') {
        return Promise.resolve(new Response(JSON.stringify({
          telegram_connected: true,
          telegram_notifications_enabled: false,
          timezone: 'UTC',
          reminder_time: '09:00',
          telegram_bot_configured: true,
          telegram_connect_url: 'https://t.me/notes_bot?start=abc',
        }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
      }
      if (url === '/api/account/settings' && options.method === 'PATCH') {
        return Promise.resolve(new Response(JSON.stringify({
          telegram_connected: true,
          telegram_notifications_enabled: true,
          timezone: 'Europe/Moscow',
          reminder_time: '10:30',
          telegram_bot_configured: true,
          telegram_connect_url: 'https://t.me/notes_bot?start=abc',
        }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });

    renderSettings();

    expect(await screen.findByText('Telegram is connected.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Open Telegram' })).toHaveAttribute(
      'href',
      'https://t.me/notes_bot?start=abc',
    );
    expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();

    const timezone = screen.getByLabelText('Timezone');
    await user.selectOptions(timezone, 'Europe/Moscow');
    await user.clear(screen.getByLabelText('Notification time'));
    await user.type(screen.getByLabelText('Notification time'), '10:30');
    await user.click(screen.getByLabelText('Enable Telegram reminders'));
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/account/settings',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({
            reminder_time: '10:30',
            telegram_notifications_enabled: true,
            timezone: 'Europe/Moscow',
          }),
        }),
      );
    });
    expect(await screen.findByText('Notification settings saved.')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();
  });

  it('shows Save when Telegram reminders toggle changes', async () => {
    const user = userEvent.setup();
    setToken('token');
    vi.spyOn(globalThis, 'fetch').mockImplementation((url, options = {}) => {
      if (url === '/api/account/settings' && options.method === 'GET') {
        return Promise.resolve(new Response(JSON.stringify({
          telegram_connected: true,
          telegram_notifications_enabled: false,
          timezone: 'UTC',
          reminder_time: '09:00',
          telegram_bot_configured: true,
          telegram_connect_url: 'https://t.me/notes_bot?start=abc',
        }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });

    renderSettings();

    expect(await screen.findByText('Telegram is connected.')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();

    await user.click(screen.getByLabelText('Enable Telegram reminders'));

    expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument();
  });

  it('shows Save when reminder time changes', async () => {
    const user = userEvent.setup();
    setToken('token');
    vi.spyOn(globalThis, 'fetch').mockImplementation((url, options = {}) => {
      if (url === '/api/account/settings' && options.method === 'GET') {
        return Promise.resolve(new Response(JSON.stringify({
          telegram_connected: true,
          telegram_notifications_enabled: false,
          timezone: 'UTC',
          reminder_time: '09:00',
          telegram_bot_configured: true,
          telegram_connect_url: 'https://t.me/notes_bot?start=abc',
        }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });

    renderSettings();

    expect(await screen.findByText('Telegram is connected.')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();

    await user.clear(screen.getByLabelText('Notification time'));
    await user.type(screen.getByLabelText('Notification time'), '10:30');

    expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument();
  });

  it('disables connect button when Telegram bot is not configured', async () => {
    setToken('token');
    vi.spyOn(globalThis, 'fetch').mockImplementation((url, options = {}) => {
      if (url === '/api/account/settings' && options.method === 'GET') {
        return Promise.resolve(new Response(JSON.stringify({
          telegram_connected: false,
          telegram_notifications_enabled: false,
          timezone: 'UTC',
          reminder_time: '09:00',
          telegram_bot_configured: false,
          telegram_connect_url: null,
        }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
      }
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    });

    renderSettings();

    expect(await screen.findByRole('button', { name: 'Connect' })).toBeDisabled();
  });
});
