import { describe, it, expect } from '@jest/globals';
import Order from '../../models/Order.js';
import Product from '../../models/Product.js';
import Cart from '../../models/Cart.js';
import Payment from '../../models/Payment.js';
import Review from '../../models/Review.js';
import Doctor from '../../models/Doctor.js';
import AuditLog from '../../models/AuditLog.js';
import User from '../../models/User.js';
import Organization from '../../models/Organization.js';

/**
 * PostgreSQL does not support MySQL-style unsigned integers. Foreign keys must
 * use the same concrete type as the referenced primary key, otherwise
 * migrations/constraints can fail or silently coerce values.
 */
const CASES = [
  { name: 'Order', model: Order, field: 'org_id', parentName: 'Organization', parent: Organization, parentField: 'id' },
  { name: 'Product', model: Product, field: 'org_id', parentName: 'Organization', parent: Organization, parentField: 'id' },
  { name: 'Cart', model: Cart, field: 'org_id', parentName: 'Organization', parent: Organization, parentField: 'id' },
  { name: 'Payment', model: Payment, field: 'org_id', parentName: 'Organization', parent: Organization, parentField: 'id' },
  { name: 'Review', model: Review, field: 'org_id', parentName: 'Organization', parent: Organization, parentField: 'id' },
  { name: 'Doctor', model: Doctor, field: 'org_id', parentName: 'Organization', parent: Organization, parentField: 'id' },
  { name: 'User', model: User, field: 'current_org_id', parentName: 'Organization', parent: Organization, parentField: 'id' },
  { name: 'Organization', model: Organization, field: 'owner_id', parentName: 'User', parent: User, parentField: 'id' },
  { name: 'AuditLog', model: AuditLog, field: 'user_id', parentName: 'User', parent: User, parentField: 'id' },
];

describe('Postgres foreign-key types', () => {
  it.each(CASES)('$name / $field matches $parentName / $parentField', ({ model, field, parent, parentField }) => {
    const childType = model.rawAttributes[field].type.key;
    const parentType = parent.rawAttributes[parentField].type.key;

    expect(childType).toBe('INTEGER');
    expect(childType).toBe(parentType);
  });

  it.each([
    { name: 'Order', model: Order, field: 'org_id' },
    { name: 'Product', model: Product, field: 'org_id' },
    { name: 'Cart', model: Cart, field: 'org_id' },
    { name: 'Payment', model: Payment, field: 'org_id' },
    { name: 'Review', model: Review, field: 'org_id' },
    { name: 'Doctor', model: Doctor, field: 'org_id' },
  ])('$name / $field has a database-level organization constraint and index', ({ model, field }) => {
    const attribute = model.rawAttributes[field];

    expect(attribute.references).toEqual({ model: 'organizations', key: 'id' });
    expect(attribute.onDelete).toBe('SET NULL');
    expect(attribute.onUpdate).toBe('CASCADE');
    const indexedFields = (model.options.indexes || []).flatMap((index) => index.fields || []);
    expect(indexedFields).toContain(field);
  });
});
