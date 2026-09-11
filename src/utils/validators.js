/**
 * Validation utilities
 * Form and data validation functions
 */

export const isEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
};

export const isPhone = (phone) => {
  const re = /^\+?[\d\s\-()]{10,}$/;
  return re.test(phone);
};

export const isURL = (url) => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

export const isStrongPassword = (password) => {
  return (
    password.length >= 8 &&
    /[A-Z]/.test(password) &&
    /[a-z]/.test(password) &&
    /[0-9]/.test(password)
  );
};

export const isAlphanumeric = (str) => {
  return /^[a-zA-Z0-9]+$/.test(str);
};

export const minLength = (value, min) => {
  return value.length >= min;
};

export const maxLength = (value, max) => {
  return value.length <= max;
};

export const isRequired = (value) => {
  if (typeof value === 'boolean') return true;
  if (typeof value === 'number') return true;
  return value != null && value.toString().trim() !== '';
};

export const validateRequired = (value, fieldName) => {
  if (!isRequired(value)) {
    return `${fieldName} is required`;
  }
  return '';
};

export const validateEmail = (email) => {
  if (!isRequired(email)) return 'Email is required';
  if (!isEmail(email)) return 'Invalid email format';
  return '';
};

export const validatePassword = (password) => {
  if (!isRequired(password)) return 'Password is required';
  if (!minLength(password, 8)) return 'Password must be at least 8 characters';
  if (!isStrongPassword(password)) return 'Password must contain uppercase, lowercase, and numbers';
  return '';
};

export const validatePhone = (phone) => {
  if (!isRequired(phone)) return 'Phone is required';
  if (!isPhone(phone)) return 'Invalid phone number';
  return '';
};

export const validateForm = (values, rules) => {
  const errors = {};
  for (const [field, fieldRules] of Object.entries(rules)) {
    for (const rule of fieldRules) {
      const error = rule(values[field], values);
      if (error) {
        errors[field] = error;
        break;
      }
    }
  }
  return errors;
};
