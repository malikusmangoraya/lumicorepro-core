import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import ClassSchedule from '../../templates/fitness/ClassSchedule/ClassSchedule';
import GymLanding from '../../templates/fitness/GymLanding/GymLanding';
import MembershipPlans from '../../templates/fitness/MembershipPlans/MembershipPlans';
import NutritionPlans from '../../templates/fitness/NutritionPlans/NutritionPlans';
import TrainerProfiles from '../../templates/fitness/TrainerProfiles/TrainerProfiles';

/**
 * Fitness showcase templates: local mock data, no network. The router is only
 * needed for the TemplateShell "Templates" back link.
 */
function renderTemplate(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe('Fitness ClassSchedule template', () => {
  it('renders the shell header, timetable action, and perks strip', () => {
    renderTemplate(<ClassSchedule />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Weekly Class Schedule' })
    ).toBeInTheDocument();
    expect(screen.getByText(/Book your seat in live classes/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Download Timetable' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Templates' })).toBeInTheDocument();

    for (const perk of [
      'Free first class',
      'No joining fee on monthly',
      'Towel & lockers included',
      'Cancel anytime',
    ]) {
      expect(screen.getByText(perk)).toBeInTheDocument();
    }
    expect(screen.getByRole('button', { name: 'Add to Calendar' })).toBeInTheDocument();
  });

  it('renders every class card with coach, capacity, and availability', () => {
    renderTemplate(<ClassSchedule />);

    for (const name of [
      'HIIT Burn',
      'Power Yoga',
      'Spin & Sculpt',
      'Lunch-Break Pump',
      'Box Fit',
      'Evening Recovery',
    ]) {
      expect(screen.getByRole('heading', { name })).toBeInTheDocument();
    }

    expect(screen.getByText('Sara Ali · All Levels')).toBeInTheDocument();
    expect(screen.getByText('6 spots left of 20')).toBeInTheDocument();
    expect(screen.getAllByText('Open')).toHaveLength(5);
    expect(screen.getByText('FULL')).toBeInTheDocument();
    expect(screen.getAllByText('Book Class')).toHaveLength(6);
  });

  it('moves the selected day and blocks booking for full classes', () => {
    renderTemplate(<ClassSchedule />);

    const monday = screen.getByRole('button', { name: 'Mon' });
    const saturday = screen.getByRole('button', { name: 'Sat' });
    expect(monday).toHaveClass('bg-primary');

    fireEvent.click(saturday);

    expect(saturday).toHaveClass('bg-primary');
    expect(monday).not.toHaveClass('bg-primary');

    const spinCard = screen.getByRole('heading', { name: 'Spin & Sculpt' }).parentElement;
    expect(within(spinCard).getByRole('button', { name: 'Book Class' })).toBeDisabled();

    const availableButtons = screen
      .getAllByRole('button', { name: 'Book Class' })
      .filter((button) => !button.disabled);
    expect(availableButtons).toHaveLength(5);
  });
});

describe('Fitness GymLanding template', () => {
  it('renders the hero copy, member badge, and both hero calls to action', () => {
    renderTemplate(<GymLanding />);

    expect(screen.getByRole('heading', { level: 1, name: 'Gym & Fitness' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Push Your Limits Daily/ })).toBeInTheDocument();
    expect(screen.getByText(/3,200\+ Active Members/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Join Now' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Start Free Trial' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'View Plans' })).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'Gym' })).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'Gym interior' })).toBeInTheDocument();
  });

  it('renders the stats and all six scheduled classes with intensity', () => {
    renderTemplate(<GymLanding />);

    expect(screen.getByText('Active Members')).toBeInTheDocument();
    expect(screen.getByText('3,200+')).toBeInTheDocument();
    expect(screen.getByText('Classes / Week')).toBeInTheDocument();
    expect(screen.getByText('84')).toBeInTheDocument();
    expect(screen.getByText('Locations')).toBeInTheDocument();

    expect(screen.getByRole('heading', { name: 'Class Schedule' })).toBeInTheDocument();
    for (const name of [
      'HIIT Burn',
      'Yoga Flow',
      'Spin Cycle',
      'Kickboxing',
      'Pilates Core',
      'Strength 101',
    ]) {
      expect(screen.getByRole('heading', { name })).toBeInTheDocument();
    }
    expect(screen.getAllByText('Book Class')).toHaveLength(6);
    expect(screen.getAllByText('High')).toHaveLength(3);
    expect(screen.getAllByText('Medium')).toHaveLength(2);
    expect(screen.getByText('Low')).toBeInTheDocument();
  });

  it('switches the active day tab and lists membership plans', () => {
    renderTemplate(<GymLanding />);

    const today = screen.getByRole('button', { name: 'Today' });
    const tomorrow = screen.getByRole('button', { name: 'Tomorrow' });
    expect(today).toHaveClass('bg-primary');

    fireEvent.click(tomorrow);

    expect(tomorrow).toHaveClass('bg-primary');
    expect(today).not.toHaveClass('bg-primary');

    expect(screen.getByRole('heading', { name: 'Membership Plans' })).toBeInTheDocument();
    for (const plan of ['Starter', 'Pro', 'Elite']) {
      expect(screen.getByRole('heading', { name: plan })).toBeInTheDocument();
    }
    expect(screen.getByText('PKR 2,500')).toBeInTheDocument();
    expect(screen.getByText('PKR 5,000')).toBeInTheDocument();
    expect(screen.getByText('PKR 9,500')).toBeInTheDocument();
    expect(screen.getByText('Most Popular')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Choose Pro' })).toBeInTheDocument();
  });

  it('renders the four expert trainers with specialty and experience', () => {
    renderTemplate(<GymLanding />);

    expect(screen.getByRole('heading', { name: 'Expert Trainers' })).toBeInTheDocument();
    for (const [name, specialty] of [
      ['Coach Bilal', 'HIIT & Cardio'],
      ['Coach Maria', 'Yoga & Mindfulness'],
      ['Coach Asad', 'Cycling & Endurance'],
      ['Coach Hina', 'Kickboxing & Defense'],
    ]) {
      expect(screen.getByRole('heading', { name })).toBeInTheDocument();
      expect(screen.getByText(specialty)).toBeInTheDocument();
    }
    expect(screen.getAllByRole('img', { name: /^Coach / })).toHaveLength(4);
  });
});

describe('Fitness MembershipPlans template', () => {
  it('renders the header and every membership guarantee', () => {
    renderTemplate(<MembershipPlans />);

    expect(screen.getByRole('heading', { level: 1, name: 'Membership Plans' })).toBeInTheDocument();
    expect(screen.getByText(/No contracts, no hidden fees/)).toBeInTheDocument();
    expect(screen.getByText('First class is free')).toBeInTheDocument();
    for (const guarantee of [
      'No hidden charges',
      '7-day money-back',
      'Student & family discounts',
      'Assessments included',
    ]) {
      expect(screen.getByText(guarantee)).toBeInTheDocument();
    }
    expect(screen.getByRole('button', { name: 'Payment Secure' })).toBeInTheDocument();
  });

  it('renders the three plans with normalized prices and billing periods', () => {
    renderTemplate(<MembershipPlans />);

    expect(screen.getByText('Day Pass')).toBeInTheDocument();
    expect(screen.getByText('Monthly')).toBeInTheDocument();
    expect(screen.getByText('Annual')).toBeInTheDocument();

    expect(screen.getByText('Rs 800')).toBeInTheDocument();
    expect(screen.getByText('Rs 6500')).toBeInTheDocument();
    expect(screen.getByText('Rs 65000')).toBeInTheDocument();
    expect(screen.getByText('/day')).toBeInTheDocument();
    expect(screen.getByText('/month')).toBeInTheDocument();
    expect(screen.getByText('/year')).toBeInTheDocument();

    for (const name of ['Day Pass', 'Monthly', 'Annual']) {
      expect(screen.getByRole('button', { name: `Choose ${name}` })).toBeInTheDocument();
    }
  });

  it('marks the popular plan and locks features only on the entry tier', () => {
    renderTemplate(<MembershipPlans />);

    expect(screen.getByText(/Most Popular/)).toBeInTheDocument();
    expect(screen.getByText('Try before you commit')).toBeInTheDocument();
    expect(screen.getAllByText('Locked feature in higher plans')).toHaveLength(2);
    expect(screen.getByText(/Prices in PKR, inclusive of all taxes/)).toBeInTheDocument();
  });
});

describe('Fitness NutritionPlans template', () => {
  it('renders the goal summary and macro targets', () => {
    renderTemplate(<NutritionPlans />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Personalized Nutrition Plan' })
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Edit My Plan' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Your Fat-Loss Plan' })).toBeInTheDocument();
    expect(screen.getByText(/Day 12 of 60/)).toBeInTheDocument();
    expect(screen.getByText(/2100 kcal daily target/)).toBeInTheDocument();

    expect(screen.getByText('Protein')).toBeInTheDocument();
    expect(screen.getByText('Carbs')).toBeInTheDocument();
    expect(screen.getByText('Fat')).toBeInTheDocument();
    expect(screen.getByText('/140g')).toBeInTheDocument();
    expect(screen.getByText('/220g')).toBeInTheDocument();
    expect(screen.getByText('/60g')).toBeInTheDocument();
  });

  it('renders all four meals with type, calories, and prep time', () => {
    renderTemplate(<NutritionPlans />);

    for (const [type, name, calories] of [
      ['Breakfast', 'Oats + Whey + Banana', '420'],
      ['Lunch', 'Chicken Biryani Rice', '620'],
      ['Snack', 'Greek Yogurt + Almonds', '250'],
      ['Dinner', 'Grilled Fish + Salad', '480'],
    ]) {
      expect(screen.getByText(type)).toBeInTheDocument();
      expect(screen.getByRole('heading', { name })).toBeInTheDocument();
      expect(screen.getByText(calories)).toBeInTheDocument();
    }
    expect(screen.getByText(/Prep 5 min/)).toBeInTheDocument();
  });

  it('renders the daily rules, hydration progress, and swap tips', () => {
    renderTemplate(<NutritionPlans />);

    expect(
      screen.getByRole('heading', { name: 'Daily Non-Negotiables' })
    ).toBeInTheDocument();
    for (const rule of [
      'Drink 3L water daily',
      'Protein within 30 min post-workout',
      'No sugary drinks after 6 PM',
      'Walk 8,000 steps on rest days',
    ]) {
      expect(screen.getByText(rule)).toBeInTheDocument();
    }

    expect(screen.getByRole('heading', { name: 'Hydration Today' })).toBeInTheDocument();
    expect(screen.getByText('1.4 / 3.0 L')).toBeInTheDocument();
    expect(screen.getAllByText(/Pro tip:/)).toHaveLength(3);
    expect(screen.getByText(/Swap: Biryani/)).toBeInTheDocument();
  });
});

describe('Fitness TrainerProfiles template', () => {
  it('renders the header, intro action, and aggregate stats', () => {
    renderTemplate(<TrainerProfiles />);

    expect(screen.getByRole('heading', { level: 1, name: 'Meet Your Coaches' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Book Free Intro' })).toBeInTheDocument();

    for (const [label, value] of [
      ['Combined Experience', '38 yrs'],
      ['Students Trained', '4,400+'],
      ['Avg. Rating', '4.85'],
      ['Free Starter Session', 'Yes'],
    ]) {
      expect(screen.getByText(label)).toBeInTheDocument();
      expect(screen.getByText(value)).toBeInTheDocument();
    }
  });

  it('renders every trainer card with role, certification, and rating', () => {
    renderTemplate(<TrainerProfiles />);

    for (const [name, role, cert, rating] of [
      ['Sara Ali', 'HIIT & Conditioning', 'ACE Certified', '4.9'],
      ['Bilal Raza', 'Strength & Powerlifting', 'NASM · S&C L2', '4.8'],
      ['Areej Khan', 'Yoga & Mobility', 'RYT-500', '5'],
      ['Faisal Mehmood', 'Fat-Loss Coaching', 'ISSA Nutrition', '4.7'],
    ]) {
      expect(screen.getByText(name)).toBeInTheDocument();
      expect(screen.getByText(role)).toBeInTheDocument();
      expect(screen.getByText(cert)).toBeInTheDocument();
      expect(screen.getByText(rating)).toBeInTheDocument();
    }

    expect(screen.getAllByRole('img', { name: /^Sara Ali$|^Bilal Raza$|^Areej Khan$|^Faisal/ })).toHaveLength(
      4
    );
  });

  it('gives each trainer a profile action and shows experience plus student counts', () => {
    renderTemplate(<TrainerProfiles />);

    expect(screen.getByText('9 yrs')).toBeInTheDocument();
    expect(screen.getByText('1200+')).toBeInTheDocument();
    expect(screen.getByText('900+')).toBeInTheDocument();
    expect(screen.getByText('1500+')).toBeInTheDocument();
    expect(screen.getByText('800+')).toBeInTheDocument();

    const viewButtons = screen.getAllByRole('button', { name: 'View Profile' });
    expect(viewButtons).toHaveLength(4);
    for (const button of viewButtons) {
      expect(button).toBeEnabled();
    }
  });
});
