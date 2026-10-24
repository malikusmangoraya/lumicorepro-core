/**
 * Reservation — table booking with date/time picker and party size.
 */
import React, { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, Link } from 'react-router-dom';
import { Calendar, Clock, Users, CheckCircle2, Phone, MapPin } from 'lucide-react';
import { useCart } from '@/store/cartStore';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import api from '@/services/api';

export default function Reservation() {
  const { t } = useTranslation();
  const { count } = useCart();
  const navigate = useNavigate();
  const [date, setDate] = useState('');
  const [time, setTime] = useState('19:00');
  const [partySize, setPartySize] = useState('2');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  const today = new Date().toISOString().split('T')[0];
  const times = ['12:00', '12:30', '13:00', '13:30', '14:00', '18:00', '18:30', '19:00', '19:30', '20:00', '20:30', '21:00'];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.post('/restaurant/reservations', {
        date,
        time,
        partySize: parseInt(partySize, 10),
        name: name || undefined,
        phone: phone || undefined,
        notes: notes || undefined,
      });
      setSuccess(true);
    } catch (err) {
      setError(err.message || 'Failed to book table. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <section className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <div className="text-center space-y-6">
          <div className="mx-auto w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
            <CheckCircle2 className="h-8 w-8 text-green-600 dark:text-green-400" />
          </div>
          <h2 className="text-2xl font-display font-bold">{t('restaurant.reservation.success', 'Table Reserved!')}</h2>
          <p className="text-muted-foreground">
            {t('restaurant.reservation.successDesc', 'Your table is booked. We look forward to serving you.')}
          </p>
          <Card className="mt-8 p-6 max-w-md mx-auto border border-border">
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">{t('restaurant.reservation.date', 'Date')}</span>
                <span className="font-medium">{date}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">{t('restaurant.reservation.time', 'Time')}</span>
                <span className="font-medium">{time}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">{t('restaurant.reservation.party', 'Party size')}</span>
                <span className="font-medium">{partySize}</span>
              </div>
            </div>
          </Card>
          <Button variant="outline" onClick={() => navigate('/restaurant/menu')} className="mt-6">
            {t('restaurant.menu.viewMenu', 'Browse Menu')}
          </Button>
        </div>
      </section>
    );
  }

  return (
    <section className="min-h-screen bg-background text-foreground">
      <nav className="container mx-auto px-4 py-4">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/restaurant/menu">
            <span>&larr;</span> {t('common.back', 'Back to menu')}
          </Link>
        </Button>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          {error && (
            <div className="mb-6 p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
              {error}
            </div>
          )}

          <div className="flex flex-col md:flex-row justify-between items-end gap-4 mb-10">
            <div>
              <h1 className="text-3xl font-display font-bold tracking-tight">{t('restaurant.reservation.heading', 'Reserve a Table')}</h1>
              <p className="text-muted-foreground">{t('restaurant.reservation.subhead', 'Pick a date, time and party size. We’ll confirm your booking.')}</p>
            </div>
            <Link to="/restaurant/cart" className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-border text-sm">
              <Users className="h-4 w-4" /> {count} item{count !== 1 ? 's' : ''}
            </Link>
          </div>

          <Card className="p-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">{t('restaurant.reservation.date', 'Date')}</label>
                  <input
                    type="date"
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                    min={today}
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">{t('restaurant.reservation.time', 'Time')}</label>
                  <select
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                    value={time}
                    onChange={(e) => setTime(e.target.value)}
                  >
                    {times.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">{t('restaurant.reservation.party', 'Party Size')}</label>
                  <select
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                    value={partySize}
                    onChange={(e) => setPartySize(e.target.value)}
                  >
                    {[1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20].map((n) => (
                      <option key={n} value={String(n)}>{n}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">{t('restaurant.reservation.name', 'Your Name')}</label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder={t('restaurant.reservation.namePlaceholder', 'John Doe')}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">{t('restaurant.reservation.phone', 'Phone')}</label>
                <input
                  type="tel"
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder={t('restaurant.reservation.phonePlaceholder', '+1 (555) 000-0000')}
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">{t('restaurant.reservation.notes', 'Special Requests')}</label>
                <textarea
                  rows={3}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder={t('restaurant.reservation.notesPlaceholder', 'Window seat, high chair, allergies…')}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </div>
              <div className="flex items-center gap-4 pt-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Phone className="h-4 w-4" />
                  <span>+1 (555) 123-4567</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground ml-auto">
                  <MapPin className="h-4 w-4" />
                  <span>123 Taste Street, Flavor City</span>
                </div>
              </div>
              <Button
                type="submit"
                variant="primary"
                fullWidth
                loading={submitting}
                className="mt-6 text-lg"
                leftIcon={Calendar}
              >
                {submitting ? t('common.submitting', 'Booking…') : t('restaurant.reservation.book', 'Book Table')}
              </Button>
            </form>
          </Card>
        </div>
      </div>
    </section>
  );
}
