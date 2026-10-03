import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

/**
 * Email service tests.
 *
 * Regression coverage for the failure path that used to crash: the catch block
 * loaded the logger with `const { logger } = await import(...)` while
 * utils/logger.js only had a default export, so `logger` was undefined and
 * every SMTP failure threw a TypeError instead of resolving
 * `{ sent: false, error }`.
 */

const mockSendMail = jest.fn();
const mockClose = jest.fn();
const mockCreateTransport = jest.fn();
const mockSystemConfigGet = jest.fn();
const mockLogger = { info: jest.fn(), warn: jest.fn(), error: jest.fn(), debug: jest.fn(), http: jest.fn() };

// Mutable DB-backed SMTP config returned by the (mocked) systemConfig service.
let smtpConfig = null;

jest.unstable_mockModule('nodemailer', () => ({
  default: { createTransport: mockCreateTransport },
}));

jest.unstable_mockModule('../../services/systemConfig.service.js', () => ({
  default: { get: mockSystemConfigGet },
}));

jest.unstable_mockModule('../../utils/logger.js', () => ({
  default: mockLogger,
  logger: mockLogger,
  withRequestId: () => mockLogger,
}));

const emailService = await import('../../services/email.service.js');
const { logger } = await import('../../utils/logger.js');

function configureEnvSmtp(overrides = {}) {
  process.env.SMTP_HOST = 'smtp.example.com';
  process.env.SMTP_USER = 'mailer@example.com';
  process.env.SMTP_PASS = 'super-secret';
  process.env.SMTP_PORT = '587';
  Object.assign(process.env, overrides);
}

function clearSmtpEnv() {
  delete process.env.SMTP_HOST;
  delete process.env.SMTP_USER;
  delete process.env.SMTP_PASS;
  delete process.env.SMTP_PORT;
}

describe('EmailService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCreateTransport.mockImplementation(() => ({ sendMail: mockSendMail, close: mockClose }));
    mockSystemConfigGet.mockImplementation(async (key) => (key === 'smtp' ? smtpConfig : {}));
    mockSendMail.mockResolvedValue({ messageId: 'test-123' });
    clearSmtpEnv();
    smtpConfig = null;
    emailService.closeTransporter();
  });

  afterEach(() => {
    clearSmtpEnv();
    emailService.closeTransporter();
  });

  describe('sendEmail without SMTP configured', () => {
    it('resolves { sent:false, dryRun:true } and logs the message instead of throwing', async () => {
      const result = await emailService.sendEmail({
        to: 'user@example.com',
        subject: 'Welcome',
        html: '<p>hi</p>',
      });

      expect(result).toEqual({ sent: false, dryRun: true });
      expect(mockSendMail).not.toHaveBeenCalled();
      expect(logger.info).toHaveBeenCalledWith(expect.stringContaining('[mail:dry-run]'));
    });

    it('treats placeholder credentials (your_*) as "not configured"', async () => {
      configureEnvSmtp({ SMTP_HOST: 'smtp.your_provider.com' });

      const result = await emailService.sendEmail({ to: 'u@example.com', subject: 's', html: 'h' });

      expect(result).toEqual({ sent: false, dryRun: true });
    });
  });

  describe('sendEmail with SMTP configured', () => {
    it('sends through the pooled transporter and reports sent=true', async () => {
      configureEnvSmtp();

      const result = await emailService.sendEmail({
        to: 'user@example.com',
        subject: 'Welcome',
        html: '<p>hi</p>',
      });

      expect(result).toEqual({ sent: true });
      expect(mockSendMail).toHaveBeenCalledTimes(1);
      const message = mockSendMail.mock.calls[0][0];
      expect(message.to).toBe('user@example.com');
      expect(message.subject).toBe('Welcome');
      expect(message.html).toBe('<p>hi</p>');
      expect(message.from).toMatch(/<.+@.+>/);
    });

    it('never throws and reports the failure when the transport rejects', async () => {
      configureEnvSmtp();
      mockSendMail.mockRejectedValue(new Error('smtp down'));

      const result = await emailService.sendEmail({ to: 'u@example.com', subject: 's', html: 'h' });

      expect(result.sent).toBe(false);
      expect(result.error).toBe('smtp down');
      expect(result.code).toBe('EMAIL_SEND_FAILED');
      // This assertion is the regression guard: the old code crashed here.
      expect(logger.warn).toHaveBeenCalledWith(expect.stringContaining('smtp down'));
    });
  });

  describe('getTransporter', () => {
    it('returns null when SMTP is not configured', async () => {
      await expect(emailService.getTransporter()).resolves.toBeNull();
      expect(mockCreateTransport).not.toHaveBeenCalled();
    });

    it('creates a pooled transporter from env credentials', async () => {
      configureEnvSmtp();

      const transporter = await emailService.getTransporter();

      expect(transporter).toBeDefined();
      expect(mockCreateTransport).toHaveBeenCalledTimes(1);
      expect(mockCreateTransport.mock.calls[0][0]).toMatchObject({
        host: 'smtp.example.com',
        port: 587,
        pool: true,
        auth: { user: 'mailer@example.com', pass: 'super-secret' },
      });
    });

    it('reuses the cached transporter while the config is unchanged', async () => {
      configureEnvSmtp();

      const first = await emailService.getTransporter();
      const second = await emailService.getTransporter();

      expect(second).toBe(first);
      expect(mockCreateTransport).toHaveBeenCalledTimes(1);
    });

    it('rebuilds the transporter when credentials rotate (stale-pool regression)', async () => {
      configureEnvSmtp();
      await emailService.getTransporter();

      process.env.SMTP_PASS = 'rotated-secret';
      await emailService.getTransporter();

      expect(mockCreateTransport).toHaveBeenCalledTimes(2);
      expect(mockClose).toHaveBeenCalledTimes(1);
    });

    it('does not collide credential values containing delimiters', async () => {
      configureEnvSmtp({ SMTP_HOST: 'smtp-a', SMTP_USER: 'user|b' });
      await emailService.getTransporter();

      configureEnvSmtp({ SMTP_HOST: 'smtp-a|user', SMTP_USER: 'b' });
      await emailService.getTransporter();

      expect(mockCreateTransport).toHaveBeenCalledTimes(2);
    });

    it('prefers DB-backed settings over environment variables', async () => {
      configureEnvSmtp();
      smtpConfig = {
        enabled: true,
        host: 'smtp.db-config.example',
        port: '465',
        user: 'db-user',
        pass: 'db-pass',
      };

      await emailService.getTransporter();

      expect(mockCreateTransport.mock.calls[0][0]).toMatchObject({
        host: 'smtp.db-config.example',
        port: 465,
        secure: true,
        auth: { user: 'db-user', pass: 'db-pass' },
      });
    });
  });

  describe('templates', () => {
    beforeEach(() => {
      configureEnvSmtp();
    });

    async function lastHtml() {
      return mockSendMail.mock.calls.at(-1)[0].html;
    }

    it('welcome email greets the user by name', async () => {
      await emailService.sendWelcomeEmail('user@example.com', 'Ayesha');
      expect(await lastHtml()).toContain('Ayesha');
    });

    it('password reset email contains a tokenised reset URL', async () => {
      await emailService.sendPasswordResetEmail('user@example.com', 'tok-123', 'https://app.example.com');
      const html = await lastHtml();
      expect(html).toContain('https://app.example.com/reset-password/tok-123');
      expect(html).toContain('15 minutes');
    });

    it('verification email contains a tokenised verify URL and the user name', async () => {
      await emailService.sendVerificationEmail('user@example.com', 'Bilal', 'verify-abc', 'https://app.example.com');
      const html = await lastHtml();
      expect(html).toContain('https://app.example.com/verify-email/verify-abc');
      expect(html).toContain('Bilal');
      expect(html).toContain('24 hours');
    });

    it('order confirmation email renders the order number, item count and total', async () => {
      await emailService.sendOrderConfirmationEmail('user@example.com', {
        orderNumber: 'ORD-1001',
        totalPrice: 129.5,
        itemsCount: 3,
      });
      const html = await lastHtml();
      expect(html).toContain('ORD-1001');
      expect(html).toContain('129.50');
      expect(html).toContain('3');
    });

    it('OTP email carries the code and the 5-minute validity note', async () => {
      await emailService.sendOTPEmail('user@example.com', '428913');
      const html = await lastHtml();
      expect(html).toContain('428913');
      expect(html).toContain('5 minutes');
    });

    it('sanitizes display names before building the From header', async () => {
      configureEnvSmtp();
      smtpConfig = {
        enabled: true,
        host: 'smtp.db-config.example',
        port: 587,
        user: 'db-user',
        pass: 'db-pass',
        fromName: 'Evil"\r\nBcc: victim@example.com',
        fromEmail: 'sender@example.com',
      };

      await emailService.sendWelcomeEmail('user@example.com', 'Ayesha');
      const message = mockSendMail.mock.calls.at(-1)[0];

      expect(message.from).toBe('"Evil Bcc: victim@example.com" <sender@example.com>');
    });
  });
});
