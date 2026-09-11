import React from 'react';
import { cn } from '../../utils';
import Grid from '../common/Grid';
import PricingCard from './PricingCard';

const delaySteps = [0, 100, 200, 300];

const PricingGrid = ({ plans = [], columns = 3, onPlanSelect, className = '', ...props }) => {
  return (
    <Grid cols={columns} gap="lg" className={cn(className)} {...props}>
      {plans.map((plan, index) => (
        <PricingCard
          key={plan.id ?? plan.name ?? index}
          {...plan}
          animationDelay={delaySteps[index % delaySteps.length]}
          onSelect={(data, e) => {
            plan.onSelect?.(data, e);
            onPlanSelect?.(plan, index, e);
          }}
        />
      ))}
    </Grid>
  );
};

export default PricingGrid;
