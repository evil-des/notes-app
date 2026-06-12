import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api.js';
import { clearToken } from '../auth.js';
import { useLang } from '../i18n.jsx';

function browserTimezone() {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
}

function timezoneOptions(selected) {
  const fallback = ['UTC', 'Europe/Moscow', 'Europe/London', 'America/New_York', 'Asia/Tokyo'];
  const supported = typeof Intl.supportedValuesOf === 'function'
    ? Intl.supportedValuesOf('timeZone')
    : fallback;
  return Array.from(new Set([selected, 'UTC', ...supported].filter(Boolean))).sort();
}

export default function Settings() {
  const { t } = useLang();
  const navigate = useNavigate();

  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [pwError, setPwError] = useState(null);
  const [pwOk, setPwOk] = useState(false);

  const [deletePw, setDeletePw] = useState('');
  const [deleteError, setDeleteError] = useState(null);
  const [settings, setSettings] = useState(null);
  const [settingsError, setSettingsError] = useState(null);
  const [settingsOk, setSettingsOk] = useState(false);
  const [timezone, setTimezone] = useState(browserTimezone);
  const [reminderTime, setReminderTime] = useState('09:00');
  const [telegramNotificationsEnabled, setTelegramNotificationsEnabled] = useState(false);
  const timezones = timezoneOptions(timezone);
  const settingsChanged = Boolean(
    settings
      && (
        timezone !== settings.timezone
        || reminderTime !== settings.reminder_time
        || telegramNotificationsEnabled !== settings.telegram_notifications_enabled
      ),
  );

  useEffect(() => {
    let alive = true;
    api.getAccountSettings()
      .then((data) => {
        if (!alive) return;
        setSettings(data);
        setTimezone(data.timezone || browserTimezone());
        setReminderTime(data.reminder_time || '09:00');
        setTelegramNotificationsEnabled(data.telegram_notifications_enabled);
      })
      .catch((err) => {
        if (alive) setSettingsError(err.message);
      });
    return () => {
      alive = false;
    };
  }, []);

  const changePassword = async (e) => {
    e.preventDefault();
    setPwError(null);
    setPwOk(false);
    try {
      await api.changePassword(currentPw, newPw);
      setPwOk(true);
      setCurrentPw('');
      setNewPw('');
    } catch (err) {
      setPwError(err.message);
    }
  };

  const saveNotificationSettings = async (next) => {
    setSettingsError(null);
    setSettingsOk(false);
    try {
      const updated = await api.updateAccountSettings(next);
      setSettings(updated);
      setTimezone(updated.timezone);
      setReminderTime(updated.reminder_time);
      setTelegramNotificationsEnabled(updated.telegram_notifications_enabled);
      setSettingsOk(true);
    } catch (err) {
      setSettingsError(err.message);
    }
  };

  const createTelegramLink = async () => {
    setSettingsError(null);
    setSettingsOk(false);
    try {
      const link = await api.createTelegramLink();
      setSettings((current) => ({
        ...current,
        telegram_connect_url: link.telegram_connect_url,
        telegram_bot_configured: link.telegram_bot_configured,
      }));
    } catch (err) {
      setSettingsError(err.message);
    }
  };

  const deleteAccount = async (e) => {
    e.preventDefault();
    setDeleteError(null);
    if (!window.confirm(t('settings.confirmDelete'))) return;
    try {
      await api.deleteAccount(deletePw);
      clearToken();
      navigate('/login', { replace: true });
    } catch (err) {
      setDeleteError(err.message);
    }
  };

  return (
    <div className="settings-page">
      <h1>{t('settings.title')}</h1>

      <section className="settings-card">
        <h2>{t('settings.telegramTitle')}</h2>
        <p className="settings-hint">
          {settings?.telegram_connected
            ? t('settings.telegramConnected')
            : t('settings.telegramDisconnected')}
        </p>
        {settings?.telegram_connect_url ? (
          <a
            className="btn btn-primary settings-link-btn"
            href={settings.telegram_connect_url}
            target="_blank"
            rel="noreferrer"
          >
            {t('settings.connectTelegram')}
          </a>
        ) : (
          <button
            type="button"
            className="btn btn-primary"
            onClick={createTelegramLink}
            disabled={!settings?.telegram_bot_configured}
          >
            {t('settings.prepareTelegramLink')}
          </button>
        )}
        {settings && !settings.telegram_bot_configured && (
          <div className="settings-note">{t('settings.telegramBotNotConfigured')}</div>
        )}
        <div className="settings-row">
          <label className="settings-checkbox">
            <input
              type="checkbox"
              checked={telegramNotificationsEnabled}
              disabled={!settings?.telegram_connected}
              onChange={(e) => {
                setTelegramNotificationsEnabled(e.target.checked);
                setSettingsOk(false);
              }}
            />
            {t('settings.enableTelegramNotifications')}
          </label>
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            saveNotificationSettings({
              reminder_time: reminderTime,
              telegram_notifications_enabled: telegramNotificationsEnabled,
              timezone,
            });
          }}
        >
          <label>
            {t('settings.timezone')}
            <select
              value={timezone}
              onChange={(e) => {
                setTimezone(e.target.value);
                setSettingsOk(false);
              }}
              required
            >
              {timezones.map((zone) => (
                <option key={zone} value={zone}>{zone}</option>
              ))}
            </select>
          </label>
          <label>
            {t('settings.reminderTime')}
            <input
              type="time"
              value={reminderTime}
              onChange={(e) => {
                setReminderTime(e.target.value);
                setSettingsOk(false);
              }}
              required
            />
          </label>
          {settingsChanged && (
            <button type="submit" className="btn">{t('settings.saveNotificationSettings')}</button>
          )}
        </form>
        {settingsError && <div className="error">{settingsError}</div>}
        {settingsOk && <div className="success">{t('settings.notificationSettingsSaved')}</div>}
      </section>

      <section className="settings-card">
        <h2>{t('settings.changePasswordTitle')}</h2>
        <form onSubmit={changePassword}>
          <label>
            {t('settings.currentPassword')}
            <input
              type="password"
              value={currentPw}
              onChange={(e) => setCurrentPw(e.target.value)}
              required
              autoComplete="current-password"
            />
          </label>
          <label>
            {t('settings.newPassword')}
            <input
              type="password"
              value={newPw}
              onChange={(e) => setNewPw(e.target.value)}
              required
              minLength={6}
              autoComplete="new-password"
            />
          </label>
          {pwError && <div className="error">{pwError}</div>}
          {pwOk && <div className="success">{t('settings.passwordChanged')}</div>}
          <button type="submit" className="btn btn-primary">{t('settings.submit')}</button>
        </form>
      </section>

      <section className="settings-card danger">
        <h2>{t('settings.dangerZone')}</h2>
        <h3>{t('settings.deleteAccountTitle')}</h3>
        <p className="settings-hint">{t('settings.deleteAccountHint')}</p>
        <form onSubmit={deleteAccount}>
          <label>
            {t('settings.confirmPassword')}
            <input
              type="password"
              value={deletePw}
              onChange={(e) => setDeletePw(e.target.value)}
              required
              autoComplete="current-password"
            />
          </label>
          {deleteError && <div className="error">{deleteError}</div>}
          <button type="submit" className="btn btn-danger">{t('settings.deleteAccount')}</button>
        </form>
      </section>
    </div>
  );
}
