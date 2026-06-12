import { createContext, useContext, useEffect, useState } from 'react';
import { AUTH_CHANGED_EVENT, getToken } from './auth.js';

const STORAGE_KEY = 'notes_lang';
export const LANGS = ['en', 'ru'];

const MESSAGES = {
  en: {
    brand: 'Notes',
    nav: { notes: 'Notes', calendar: 'Calendar', settings: 'Settings', logout: 'Log out' },
    theme: { light: 'Light', dark: 'Dark', system: 'System' },
    lang: { label: { en: 'EN', ru: 'RU' } },
    auth: {
      loginTitle: 'Welcome back',
      loginSubtitle: 'Log in to your notes.',
      registerTitle: 'Create an account',
      registerSubtitle: 'Your notes stay private to you.',
      username: 'Username',
      password: 'Password',
      login: 'Log in',
      create: 'Create account',
      noAccount: 'No account?',
      createOne: 'Create one',
      haveAccount: 'Already have an account?',
      loginLink: 'Log in',
      loginFailed: 'Login failed',
      registerFailed: 'Registration failed',
    },
    notes: {
      search: 'Search notes...',
      new: '+ New',
      allTag: 'all',
      noMatch: 'No notes match.',
      nothingSelected: 'Nothing selected',
      pickOrCreate: 'Pick a note from the list or create a new one.',
      viewActive: 'Active',
      viewArchived: 'Archived',
      selectMode: 'Select',
      cancelSelect: 'Cancel',
      selectAll: 'Select all',
      deleteSelected: 'Delete ({count})',
      confirmBulkDelete: 'Delete {count} note(s)?',
      loadMore: 'Load more',
      of: 'of',
      pinned: 'Pinned',
      archived: 'Archived',
    },
    editor: {
      untitled: 'Untitled note',
      date: 'Date',
      tags: 'Tags',
      tagsPlaceholder: 'work, ideas',
      writeHere: 'Write markdown here...',
      previewEmpty: '_Start typing to see the preview._',
      save: 'Save',
      cancel: 'Cancel',
      delete: 'Delete',
      pin: 'Pin',
      unpin: 'Unpin',
      archive: 'Archive',
      unarchive: 'Unarchive',
      confirmDelete: 'Delete this note?',
      toolbarBold: 'Bold',
      toolbarItalic: 'Italic',
      toolbarLink: 'Link',
      toolbarCode: 'Code',
      toolbarHeading: 'Heading',
      toolbarList: 'List',
      toolbarQuote: 'Quote',
    },
    calendar: {
      today: 'Today',
      notesOn: 'Notes on',
      noNotes: 'No notes on this day.',
      prev: 'Previous month',
      next: 'Next month',
      months: ['January','February','March','April','May','June','July','August','September','October','November','December'],
      weekdaysShort: ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],
    },
    settings: {
      title: 'Settings',
      changePasswordTitle: 'Change password',
      currentPassword: 'Current password',
      newPassword: 'New password',
      submit: 'Update password',
      passwordChanged: 'Password updated.',
      telegramTitle: 'Telegram reminders',
      telegramConnected: 'Telegram is connected.',
      telegramDisconnected: 'Connect Telegram to receive reminders when a note date arrives.',
      telegramBotNotConfigured: 'Telegram bot is not configured for this environment.',
      connectTelegram: 'Open Telegram',
      prepareTelegramLink: 'Connect',
      enableTelegramNotifications: 'Enable Telegram reminders',
      timezone: 'Timezone',
      reminderTime: 'Notification time',
      saveNotificationSettings: 'Save',
      notificationSettingsSaved: 'Notification settings saved.',
      dangerZone: 'Danger zone',
      deleteAccountTitle: 'Delete account',
      deleteAccountHint: 'This permanently removes your account and all your notes.',
      confirmPassword: 'Enter your password to confirm',
      deleteAccount: 'Delete account',
      confirmDelete: 'This action cannot be undone. Proceed?',
    },
    shortcuts: {
      title: 'Keyboard shortcuts',
      newNote: 'New note',
      focusSearch: 'Focus search',
      saveNote: 'Save note',
      closeModal: 'Close this dialog',
      showHelp: 'Show this help',
      close: 'Close',
    },
  },
  ru: {
    brand: 'Заметки',
    nav: { notes: 'Заметки', calendar: 'Календарь', settings: 'Настройки', logout: 'Выйти' },
    theme: { light: 'Светлая', dark: 'Тёмная', system: 'Системная' },
    lang: { label: { en: 'EN', ru: 'RU' } },
    auth: {
      loginTitle: 'С возвращением',
      loginSubtitle: 'Войдите в свои заметки.',
      registerTitle: 'Создать аккаунт',
      registerSubtitle: 'Ваши заметки видны только вам.',
      username: 'Имя пользователя',
      password: 'Пароль',
      login: 'Войти',
      create: 'Создать аккаунт',
      noAccount: 'Нет аккаунта?',
      createOne: 'Создать',
      haveAccount: 'Уже есть аккаунт?',
      loginLink: 'Войти',
      loginFailed: 'Не удалось войти',
      registerFailed: 'Не удалось зарегистрироваться',
    },
    notes: {
      search: 'Поиск...',
      new: '+ Новая',
      allTag: 'все',
      noMatch: 'Ничего не найдено.',
      nothingSelected: 'Ничего не выбрано',
      pickOrCreate: 'Выберите заметку из списка или создайте новую.',
      viewActive: 'Активные',
      viewArchived: 'Архив',
      selectMode: 'Выбрать',
      cancelSelect: 'Отмена',
      selectAll: 'Выбрать все',
      deleteSelected: 'Удалить ({count})',
      confirmBulkDelete: 'Удалить {count} заметок?',
      loadMore: 'Загрузить ещё',
      of: 'из',
      pinned: 'Закреплено',
      archived: 'В архиве',
    },
    editor: {
      untitled: 'Без названия',
      date: 'Дата',
      tags: 'Теги',
      tagsPlaceholder: 'работа, идеи',
      writeHere: 'Пишите markdown здесь...',
      previewEmpty: '_Начните печатать, чтобы увидеть превью._',
      save: 'Сохранить',
      cancel: 'Отмена',
      delete: 'Удалить',
      pin: 'Закрепить',
      unpin: 'Открепить',
      archive: 'В архив',
      unarchive: 'Из архива',
      confirmDelete: 'Удалить эту заметку?',
      toolbarBold: 'Жирный',
      toolbarItalic: 'Курсив',
      toolbarLink: 'Ссылка',
      toolbarCode: 'Код',
      toolbarHeading: 'Заголовок',
      toolbarList: 'Список',
      toolbarQuote: 'Цитата',
    },
    calendar: {
      today: 'Сегодня',
      notesOn: 'Заметки на',
      noNotes: 'На этот день заметок нет.',
      prev: 'Предыдущий месяц',
      next: 'Следующий месяц',
      months: ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'],
      weekdaysShort: ['Пн','Вт','Ср','Чт','Пт','Сб','Вс'],
    },
    settings: {
      title: 'Настройки',
      changePasswordTitle: 'Смена пароля',
      currentPassword: 'Текущий пароль',
      newPassword: 'Новый пароль',
      submit: 'Обновить пароль',
      passwordChanged: 'Пароль обновлён.',
      telegramTitle: 'Telegram-напоминания',
      telegramConnected: 'Telegram подключён.',
      telegramDisconnected: 'Подключите Telegram, чтобы получать напоминания при наступлении даты заметки.',
      telegramBotNotConfigured: 'Telegram-бот не настроен для этого окружения.',
      connectTelegram: 'Открыть Telegram',
      prepareTelegramLink: 'Подключить',
      enableTelegramNotifications: 'Включить Telegram-напоминания',
      timezone: 'Часовой пояс',
      reminderTime: 'Время уведомления',
      saveNotificationSettings: 'Сохранить',
      notificationSettingsSaved: 'Настройки уведомлений сохранены.',
      dangerZone: 'Опасная зона',
      deleteAccountTitle: 'Удалить аккаунт',
      deleteAccountHint: 'Это безвозвратно удалит ваш аккаунт и все ваши заметки.',
      confirmPassword: 'Введите пароль для подтверждения',
      deleteAccount: 'Удалить аккаунт',
      confirmDelete: 'Это действие необратимо. Продолжить?',
    },
    shortcuts: {
      title: 'Горячие клавиши',
      newNote: 'Новая заметка',
      focusSearch: 'Поиск',
      saveNote: 'Сохранить заметку',
      closeModal: 'Закрыть диалог',
      showHelp: 'Показать эту справку',
      close: 'Закрыть',
    },
  },
};

function getInitialLang() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (LANGS.includes(saved)) return saved;
  } catch {
    // localStorage may be unavailable (private mode); fall through to defaults.
  }
  const browser = (navigator.language || 'en').slice(0, 2);
  return LANGS.includes(browser) ? browser : 'en';
}

function resolve(dict, path) {
  const parts = path.split('.');
  let node = dict;
  for (const p of parts) {
    if (node == null) return undefined;
    node = node[p];
  }
  return node;
}

function interpolate(str, vars) {
  if (typeof str !== 'string' || !vars) return str;
  return str.replace(/\{(\w+)\}/g, (_, k) => (k in vars ? String(vars[k]) : `{${k}}`));
}

const LangContext = createContext({ lang: 'en', setLang: () => {}, t: (k) => k });

export function LangProvider({ children }) {
  const [lang, setLangState] = useState(getInitialLang);

  useEffect(() => {
    document.documentElement.setAttribute('lang', lang);
  }, [lang]);

  useEffect(() => {
    let alive = true;
    const syncLanguageFromServer = () => {
      const token = getToken();
      if (!token) return;
      fetch('/api/account/settings', {
        method: 'GET',
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (!alive || !LANGS.includes(data?.language)) return;
          setLangState(data.language);
          try {
            localStorage.setItem(STORAGE_KEY, data.language);
          } catch {
            // localStorage may be unavailable; continue in-memory.
          }
        })
        .catch(() => {});
    };
    syncLanguageFromServer();
    window.addEventListener(AUTH_CHANGED_EVENT, syncLanguageFromServer);
    return () => {
      alive = false;
      window.removeEventListener(AUTH_CHANGED_EVENT, syncLanguageFromServer);
    };
  }, []);

  const setLang = (next, { sync = true } = {}) => {
    if (!LANGS.includes(next)) return;
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // localStorage may be unavailable; continue in-memory.
    }
    setLangState(next);
    const token = getToken();
    if (sync && token) {
      fetch('/api/account/settings', {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ language: next }),
      }).catch(() => {});
    }
  };

  const t = (key, vars) => {
    const value = resolve(MESSAGES[lang], key);
    if (value === undefined) {
      const fallback = resolve(MESSAGES.en, key);
      return interpolate(fallback ?? key, vars);
    }
    return interpolate(value, vars);
  };

  return (
    <LangContext.Provider value={{ lang, setLang, t }}>{children}</LangContext.Provider>
  );
}

export function useLang() {
  return useContext(LangContext);
}
