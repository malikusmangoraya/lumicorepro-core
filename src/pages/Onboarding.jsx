import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../components/common/ThemeProvider';
import {
  ChevronLeft,
  ChevronRight,
  Check,
  Loader2,
} from 'lucide-react';

const STEPS = 3;

const ROLES = ['Admin', 'Developer', 'Designer', 'Other'];
const THEME_OPTIONS = ['Light', 'Dark', 'System'];

export default function Onboarding() {
  const { t } = useTranslation();
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [step, setStep] = useState(1);
  const [role, setRole] = useState('');
  const [customRole, setCustomRole] = useState('');
  const [teamName, setTeamName] = useState('');
  const [emails, setEmails] = useState('');
  const [themePref, setThemePref] = useState('System');
  const [emailNotifs, setEmailNotifs] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const progress = ((step - 1) / (STEPS - 1)) * 100;

  function handleComplete() {
    setIsSubmitting(true);
    localStorage.setItem('onboarding_complete', 'true');
    setTimeout(() => {
      window.location.href = '/dashboard';
    }, 500);
  }

  const inputClass = `w-full bg-background border border-border rounded-lg px-3 py-2 text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary transition-colors`;
  const labelClass = 'text-sm font-medium text-muted-foreground mb-1 block';

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="h-1 bg-muted rounded-full overflow-hidden mb-6">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        <div className="bg-card rounded-xl border border-border shadow-sm p-6">
          {step === 1 && (
            <div>
              <h2 className="text-lg font-semibold text-foreground mb-1">
                {t('onboarding.welcome', 'Welcome!')}
              </h2>
              <p className="text-sm text-muted-foreground mb-6">
                {t('onboarding.selectRole', 'Select your role to get started.')}
              </p>

              <div className="space-y-3">
                {ROLES.map((r) => (
                  <label
                    key={r}
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg border cursor-pointer transition-colors ${
                      role === r
                        ? 'border-primary bg-primary/10'
                        : 'border-border hover:bg-muted'
                    }`}
                  >
                    <input
                      type="radio"
                      name="role"
                      value={r}
                      checked={role === r}
                      onChange={() => setRole(r)}
                      className="accent-primary"
                    />
                    <span className="text-sm text-foreground">{r}</span>
                  </label>
                ))}
              </div>

              {role === 'Other' && (
                <div className="mt-4">
                  <label className={labelClass}>
                    {t('onboarding.customRole', 'Specify your role')}
                  </label>
                  <input
                    type="text"
                    value={customRole}
                    onChange={(e) => setCustomRole(e.target.value)}
                    placeholder={t('onboarding.customRolePlaceholder', 'e.g. Product Manager')}
                    className={inputClass}
                  />
                </div>
              )}
            </div>
          )}

          {step === 2 && (
            <div>
              <h2 className="text-lg font-semibold text-foreground mb-1">
                {t('onboarding.teamSetup', 'Team Setup')}
              </h2>
              <p className="text-sm text-muted-foreground mb-6">
                {t('onboarding.teamSetupDesc', 'Set up your team and invite collaborators.')}
              </p>

              <div className="space-y-4">
                <div>
                  <label className={labelClass}>
                    {t('onboarding.teamName', 'Team Name')}
                  </label>
                  <input
                    type="text"
                    value={teamName}
                    onChange={(e) => setTeamName(e.target.value)}
                    placeholder={t('onboarding.teamNamePlaceholder', 'My Team')}
                    className={inputClass}
                  />
                </div>

                <div>
                  <label className={labelClass}>
                    {t('onboarding.inviteEmails', 'Invite Emails')}
                  </label>
                  <textarea
                    value={emails}
                    onChange={(e) => setEmails(e.target.value)}
                    placeholder={t('onboarding.inviteEmailsPlaceholder', 'email1@example.com, email2@example.com')}
                    rows={4}
                    className={`${inputClass} resize-none`}
                  />
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div>
              <h2 className="text-lg font-semibold text-foreground mb-1">
                {t('onboarding.preferences', 'Preferences')}
              </h2>
              <p className="text-sm text-muted-foreground mb-6">
                {t('onboarding.preferencesDesc', 'Customize your experience.')}
              </p>

              <div className="space-y-5">
                <div>
                  <label className={labelClass}>
                    {t('onboarding.theme', 'Theme')}
                  </label>
                  <div className="flex gap-2">
                    {THEME_OPTIONS.map((opt) => (
                      <button
                        key={opt}
                        onClick={() => setThemePref(opt)}
                        className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium border transition-colors ${
                          themePref === opt
                            ? 'border-primary bg-primary text-white'
                            : 'border-border bg-background text-foreground hover:bg-muted'
                        }`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="flex items-center justify-between cursor-pointer">
                    <span className={labelClass}>
                      {t('onboarding.emailNotifications', 'Email Notifications')}
                    </span>
                    <button
                      type="button"
                      role="switch"
                      aria-checked={emailNotifs}
                      onClick={() => setEmailNotifs((prev) => !prev)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        emailNotifs ? 'bg-primary' : 'bg-muted'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 rounded-full bg-white transition-transform ${
                          emailNotifs ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </label>
                </div>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between mt-8 pt-4 border-t border-border">
            {step > 1 ? (
              <button
                onClick={() => setStep((s) => s - 1)}
                className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <ChevronLeft className="h-4 w-4" aria-hidden="true" />
                {t('common.back', 'Back')}
              </button>
            ) : (
              <div />
            )}

            {step < STEPS ? (
              <button
                onClick={() => setStep((s) => s + 1)}
                className="flex items-center gap-1 px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
              >
                {t('common.next', 'Next')}
                <ChevronRight className="h-4 w-4" aria-hidden="true" />
              </button>
            ) : (
              <button
                onClick={handleComplete}
                disabled={isSubmitting}
                className="flex items-center gap-1 px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {isSubmitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                ) : (
                  <Check className="h-4 w-4" aria-hidden="true" />
                )}
                {t('onboarding.complete', 'Complete')}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
